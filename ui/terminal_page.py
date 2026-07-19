from __future__ import annotations

import errno
import fcntl
import json
import os
import pty
import signal
import struct
import subprocess
import termios
from pathlib import Path

from PySide6.QtCore import QObject, QSocketNotifier, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class TerminalBridge(QObject):
    output_ready = Signal(str)
    title_changed = Signal(str)
    process_exited = Signal(int)

    def __init__(self, working_directory: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.working_directory = working_directory
        self.master_fd: int | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.notifier: QSocketNotifier | None = None
        self.start_shell()

    def start_shell(self) -> None:
        self.close_shell()
        self.working_directory.mkdir(parents=True, exist_ok=True)

        master_fd, slave_fd = pty.openpty()
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        env = os.environ.copy()
        env.update({
            "TERM": "xterm-256color",
            "COLORTERM": "truecolor",
            "OPPENHEIMER_TERMINAL": "1",
        })

        shell = env.get("SHELL") or "/bin/bash"
        self.process = subprocess.Popen(
            [shell, "--login"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self.working_directory,
            env=env,
            start_new_session=True,
            close_fds=True,
        )
        os.close(slave_fd)

        self.master_fd = master_fd
        self.notifier = QSocketNotifier(master_fd, QSocketNotifier.Read, self)
        self.notifier.activated.connect(self._read_from_pty)
        self.title_changed.emit(self.working_directory.name or "Terminal")

    @Slot(str)
    def write(self, data: str) -> None:
        if self.master_fd is None:
            return
        try:
            os.write(self.master_fd, data.encode("utf-8", errors="replace"))
        except OSError:
            self.output_ready.emit("\r\n[terminal input failed]\r\n")

    @Slot(int, int)
    def resize(self, columns: int, rows: int) -> None:
        if self.master_fd is None or columns < 1 or rows < 1:
            return
        size = struct.pack("HHHH", rows, columns, 0, 0)
        try:
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)
            if self.process is not None:
                os.killpg(self.process.pid, signal.SIGWINCH)
        except (OSError, ProcessLookupError):
            pass

    @Slot(str)
    def change_directory(self, path: str) -> None:
        directory = Path(path).expanduser().resolve()
        if not directory.is_dir():
            self.output_ready.emit(f"\r\nDirectory does not exist: {directory}\r\n")
            return
        self.working_directory = directory
        self.write(f"cd {self._shell_quote(str(directory))}\n")
        self.title_changed.emit(directory.name or "Terminal")

    @Slot()
    def restart(self) -> None:
        self.start_shell()
        self.output_ready.emit("\r\n\x1b[33m[terminal restarted]\x1b[0m\r\n")

    @Slot()
    def interrupt(self) -> None:
        self.write("\x03")

    def _read_from_pty(self) -> None:
        if self.master_fd is None:
            return
        chunks: list[bytes] = []
        while True:
            try:
                chunk = os.read(self.master_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            except BlockingIOError:
                break
            except OSError as error:
                if error.errno == errno.EIO:
                    code = self.process.poll() if self.process else 0
                    self.process_exited.emit(code or 0)
                    break
                raise
        if chunks:
            self.output_ready.emit(b"".join(chunks).decode("utf-8", errors="replace"))

    def close_shell(self) -> None:
        if self.notifier is not None:
            self.notifier.setEnabled(False)
            self.notifier.deleteLater()
            self.notifier = None

        if self.process is not None and self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGHUP)
                self.process.wait(timeout=1)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                self.process.kill()
        self.process = None

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

    @staticmethod
    def _shell_quote(value: str) -> str:
        return "'" + value.replace("'", "'\\''") + "'"


class TerminalWidget(QWidget):
    title_changed = Signal(str)

    def __init__(self, working_directory: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.assets_dir = Path(__file__).resolve().parent / "assets" / "terminal"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        self.web_view.setAttribute(Qt.WA_TranslucentBackground, True)
        self.web_view.setAutoFillBackground(False)
        self.web_view.setStyleSheet("background: transparent; border: none;")
        self.web_view.page().setBackgroundColor(QColor(0, 0, 0, 0))
        self._pending_js: list[str] = []
        self._page_ready = False
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view)

        self.bridge = TerminalBridge(working_directory, self)
        self.channel = QWebChannel(self.web_view.page())
        self.channel.registerObject("terminalBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        self.bridge.output_ready.connect(self._write_to_terminal)
        self.bridge.title_changed.connect(self.title_changed)
        self.bridge.process_exited.connect(self._process_exited)
        self.web_view.load(QUrl.fromLocalFile(str(self.assets_dir / "terminal.html")))

    def set_working_directory(self, directory: Path) -> None:
        self.bridge.change_directory(str(directory))

    def restart(self) -> None:
        self.bridge.restart()

    def interrupt(self) -> None:
        self.bridge.interrupt()

    def clear(self) -> None:
        self._run_terminal_js("window.oppenheimerClear();")

    def copy(self) -> None:
        self._run_terminal_js("window.oppenheimerCopy();")

    def paste(self) -> None:
        self._run_terminal_js("window.oppenheimerPaste();")

    def focus_terminal(self) -> None:
        self.web_view.setFocus(Qt.OtherFocusReason)
        self._run_terminal_js("window.oppenheimerFocus();")

    @Slot(str)
    def _write_to_terminal(self, text: str) -> None:
        self._run_terminal_js("window.oppenheimerWrite(" + json.dumps(text) + ");")

    def _run_terminal_js(self, script: str) -> None:
        if self.web_view.page() is None:
            return
        if not self._page_ready:
            self._pending_js.append(script)
            return
        self.web_view.page().runJavaScript(script)

    @Slot(bool)
    def _on_load_finished(self, ok: bool) -> None:
        self._page_ready = ok
        if not ok:
            return
        pending_scripts = self._pending_js
        self._pending_js = []
        for script in pending_scripts:
            self._run_terminal_js(script)

    @Slot(int)
    def _process_exited(self, code: int) -> None:
        self._write_to_terminal(
            f"\r\n\x1b[90m[process exited with code {code}; press Restart]\x1b[0m\r\n"
        )

    def close_terminal(self) -> None:
        self.bridge.close_shell()


class TerminalPage(QWidget):
    def __init__(self, working_directory: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.working_directory = working_directory
        self._terminal_number = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("terminalToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 6, 8, 6)
        toolbar_layout.setSpacing(6)

        title = QLabel("TERMINAL")
        title.setObjectName("terminalToolbarTitle")
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch(1)

        self.cwd_label = QLabel(str(self.working_directory))
        self.cwd_label.setObjectName("terminalCwd")
        toolbar_layout.addWidget(self.cwd_label)

        self.new_button = self._tool_button("＋", "New Terminal")
        self.restart_button = self._tool_button("↻", "Restart Terminal")
        self.interrupt_button = self._tool_button("■", "Stop Current Command")
        self.clear_button = self._tool_button("⌫", "Clear Terminal")
        self.copy_button = self._tool_button("⧉", "Copy Selection")
        self.paste_button = self._tool_button("▣", "Paste")
        self.close_button = self._tool_button("×", "Close Terminal")

        for button in (
            self.new_button,
            self.restart_button,
            self.interrupt_button,
            self.clear_button,
            self.copy_button,
            self.paste_button,
            self.close_button,
        ):
            toolbar_layout.addWidget(button)

        root.addWidget(toolbar)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("terminalTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_terminal)
        self.tabs.currentChanged.connect(self._focus_current)
        root.addWidget(self.tabs, 1)

        self.new_button.clicked.connect(self.new_terminal)
        self.restart_button.clicked.connect(lambda: self._with_current("restart"))
        self.interrupt_button.clicked.connect(lambda: self._with_current("interrupt"))
        self.clear_button.clicked.connect(lambda: self._with_current("clear"))
        self.copy_button.clicked.connect(lambda: self._with_current("copy"))
        self.paste_button.clicked.connect(lambda: self._with_current("paste"))
        self.close_button.clicked.connect(lambda: self.close_terminal(self.tabs.currentIndex()))

        QShortcut(QKeySequence("Ctrl+Shift+`"), self, activated=self.new_terminal)
        QShortcut(QKeySequence("Ctrl+Shift+W"), self, activated=lambda: self.close_terminal(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, activated=lambda: self._with_current("copy"))
        QShortcut(QKeySequence("Ctrl+Shift+V"), self, activated=lambda: self._with_current("paste"))
        QShortcut(QKeySequence("Ctrl+L"), self, activated=lambda: self._with_current("clear"))

        self.new_terminal()

    @staticmethod
    def _tool_button(text: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setObjectName("terminalToolButton")
        button.setAutoRaise(True)
        return button

    def current_terminal(self) -> TerminalWidget | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, TerminalWidget) else None

    def new_terminal(self) -> None:
        self._terminal_number += 1
        terminal = TerminalWidget(self.working_directory, self)
        label = f"bash {self._terminal_number}"
        index = self.tabs.addTab(terminal, label)
        terminal.title_changed.connect(lambda title, item=terminal: self._rename_tab(item, title))
        self.tabs.setCurrentIndex(index)
        terminal.focus_terminal()

    def close_terminal(self, index: int) -> None:
        if index < 0:
            return
        widget = self.tabs.widget(index)
        if isinstance(widget, TerminalWidget):
            widget.close_terminal()
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.new_terminal()

    def set_working_directory(self, directory: Path) -> None:
        self.working_directory = directory
        self.cwd_label.setText(str(directory))
        terminal = self.current_terminal()
        if terminal is not None:
            terminal.set_working_directory(directory)

    def _rename_tab(self, terminal: TerminalWidget, title: str) -> None:
        index = self.tabs.indexOf(terminal)
        if index >= 0:
            self.tabs.setTabText(index, title)

    def _with_current(self, method_name: str) -> None:
        terminal = self.current_terminal()
        if terminal is not None:
            getattr(terminal, method_name)()

    def _focus_current(self, _index: int) -> None:
        terminal = self.current_terminal()
        if terminal is not None:
            terminal.focus_terminal()

    def closeEvent(self, event) -> None:
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if isinstance(widget, TerminalWidget):
                widget.close_terminal()
        super().closeEvent(event)
