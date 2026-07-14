import platform
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


MODULES_DIR = Path("/usr/lib/modules")


class KernelCard(QFrame):
    remove_requested = Signal(str)

    def __init__(
        self,
        kernel_version: str,
        running_kernel: str,
    ) -> None:
        super().__init__()

        self.kernel_version = kernel_version
        self.is_running = kernel_version == running_kernel

        self.setObjectName(
            "runningKernelCard"
            if self.is_running
            else "kernelCard"
        )
        self.setAttribute(Qt.WA_StyledBackground, True)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        details = QVBoxLayout()
        details.setSpacing(4)

        title = QLabel(kernel_version)
        title.setObjectName(
            "runningKernelName"
            if self.is_running
            else "kernelName"
        )

        state = QLabel(
            "Running now"
            if self.is_running
            else "Installed"
        )
        state.setObjectName(
            "runningKernelState"
            if self.is_running
            else "kernelState"
        )

        path = QLabel(
            str(MODULES_DIR / kernel_version)
        )
        path.setWordWrap(True)
        path.setObjectName("kernelPath")

        details.addWidget(title)
        details.addWidget(state)
        details.addWidget(path)

        root.addLayout(details, 1)

        if self.is_running:
            badge = QLabel("RUNNING")
            badge.setObjectName("runningBadge")
            badge.setAlignment(Qt.AlignCenter)
            root.addWidget(badge)
        else:
            remove_button = QPushButton("🗑")
            remove_button.setObjectName(
                "kernelRemoveButton"
            )
            remove_button.setToolTip(
                f"Uninstall {kernel_version}"
            )
            remove_button.setFixedSize(34, 34)
            remove_button.clicked.connect(
                lambda: self.remove_requested.emit(
                    self.kernel_version
                )
            )
            root.addWidget(remove_button)

class InstalledKernelsPanel(QFrame):
    remove_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("glassPanel")
        self.setAttribute(
            Qt.WA_StyledBackground,
            True,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        header = QHBoxLayout()

        self.title = QLabel("INSTALLED KERNELS")
        self.title.setObjectName("sectionTitle")

        self.refresh_button = QPushButton(
            "↻ Refresh"
        )
        self.refresh_button.setObjectName(
            "refreshButton"
        )
        self.refresh_button.clicked.connect(
            self.refresh
        )

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.refresh_button)

        root.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.scroll.setStyleSheet(
            """
            QScrollArea,
            QScrollArea::viewport,
            QScrollArea > QWidget,
            QScrollArea > QWidget > QWidget {
                background: transparent;
                border: none;
            }
            """
        )

        self.container = QWidget()
        self.container.setAttribute(
            Qt.WA_StyledBackground,
            True,
        )
        self.container.setStyleSheet(
            "background: transparent;"
        )

        self.kernel_layout = QVBoxLayout(
            self.container
        )
        self.kernel_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.kernel_layout.setSpacing(8)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        self.refresh()

    def installed_kernels(self) -> list[str]:
        if not MODULES_DIR.is_dir():
            return []

        return sorted(
            path.name
            for path in MODULES_DIR.iterdir()
            if path.is_dir()
        )

    def clear_cards(self) -> None:
        while self.kernel_layout.count():
            item = self.kernel_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def refresh(self) -> None:
        self.clear_cards()

        running_kernel = platform.release()
        kernels = self.installed_kernels()

        self.title.setText(
            f"INSTALLED KERNELS ({len(kernels)})"
        )

        if not kernels:
            empty_label = QLabel(
                "No installed kernels were found."
            )
            empty_label.setObjectName(
                "kernelEmpty"
            )
            empty_label.setAlignment(
                Qt.AlignCenter
            )

            self.kernel_layout.addWidget(
                empty_label
            )
            self.kernel_layout.addStretch()
            return

        for kernel_version in kernels:
            card = KernelCard(
                kernel_version,
                running_kernel,
            )

            card.remove_requested.connect(
                self.remove_requested.emit
            )

            self.kernel_layout.addWidget(card)

        self.kernel_layout.addStretch()

