import platform
import shlex
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from engine.builder import (
    build_commands,
    compile_commands,
    download_commands,
    prepare_commands,
)
from engine.installer import install_commands
from engine.tweaks import TweakValidationError
from engine.tweaks import permanent_commands as tweak_permanent_commands
from engine.tweaks import session_commands as tweak_session_commands
from engine.uninstaller import uninstall_kernel_commands
from engine.verifier import verification_commands
from engine.worker import Worker
from ui.background import BackgroundWidget
from ui.build_page import BuildPage
from ui.installed_kernels import InstalledKernelsPanel
from ui.patches_page import PatchesPage
from ui.placeholder_page import PlaceholderPage
from ui.sidebar import Sidebar
from ui.styles import APP_STYLE
from ui.terminal_page import TerminalPage
from ui.tweaks_page import TweaksPage


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"
ASSET_DIR = PROJECT_DIR / "assets"
RAZER_APPLY = PROJECT_DIR / "patches/hid-razer/apply.py"

KERNEL_SOURCES = {
    "Linux Stable": {
        "directory": "linux-stable",
        "config_directory": None,
        "source_type": "tarball",
        "archive_url_template": "https://cdn.kernel.org/pub/linux/kernel/v{major}.x/linux-{version}.tar.xz",
    },
    "Linux Zen": {
        "url": "https://github.com/zen-kernel/zen-kernel.git",
        "directory": "linux-zen",
        "config_directory": None,
        "source_type": "git",
    },
}

CONFIG_FILES = {
    "DFUSE 7.2": "config.dfuse-7.2",
    "Zen 7.1.3": "config.zen-7.1.3",
    "Manjaro 7.2 (Golden)": "config.manjaro-7.2",
    "DFUSE Legacy": "config.dfuse",
    "DFUSE Slim": "config.dfuse-slim",
}

ARCH_DEPENDENCIES = [
    "base-devel",
    "git",
    "curl",
    "bc",
    "flex",
    "bison",
    "openssl",
    "elfutils",
    "pahole",
    "cpio",
    "perl",
    "python",
    "rsync",
    "kmod",
    "zstd",
    "rust",
    "rust-bindgen",
    "rust-src",

    # Embedded xterm.js terminal
    "qt6-webengine",
    "nodejs",
    "npm",
]

REQUIRED_TOOLS = [
    "git",
    "curl",
    "make",
    "gcc",
    "bc",
    "flex",
    "bison",
    "openssl",
    "pahole",
    "cpio",
    "perl",
    "python3",
    "rsync",
    "depmod",
    "zstd",
    "rustc",
    "bindgen",

    # Embedded terminal
    "node",
    "npm",
]


def quote(value: object) -> str:
    return shlex.quote(str(value))


class Oppenheimer(BackgroundWidget):
    def __init__(self) -> None:
        super().__init__(ASSET_DIR / "oppenheimer-background.png")

        self.worker: Worker | None = None
        self.build_succeeded = False

        for path in (WORKSPACE_DIR, OUTPUT_DIR, LOG_DIR):
            path.mkdir(parents=True, exist_ok=True)

        self.setWindowTitle("Oppenheimer Kernel Forge")
        self.resize(1540, 960)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 0)
        root.setSpacing(0)

        shell = QHBoxLayout()
        shell.setSpacing(10)
        root.addLayout(shell, 1)

        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(240)
        shell.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        shell.addWidget(self.pages, 1)

        self.build_page = BuildPage(list(KERNEL_SOURCES.keys()))
        self.left = self.build_page
        self.log_panel = self.build_page.log_panel
        self.status_panel = self.build_page.status_panel

        self.patches_page = PatchesPage(PROJECT_DIR / "patches")
        self.installed_kernels = InstalledKernelsPanel()
        self.terminal_page = TerminalPage(self.source_dir())
        self.tweaks_page = TweaksPage()
        self.kernels_page = self._wrap_page(
            "INSTALLED KERNELS",
            "MANAGE. VERIFY. REMOVE.",
            self.installed_kernels,
        )
        
        self.ai_page = PlaceholderPage(
            "OPPENHEIMER AI",
            "AI-assisted kernel configuration and build guidance will live here.",
        )

        self.page_map: dict[str, QWidget] = {
            "configure": self.build_page,
            "download": self.build_page,
            "build": self.build_page,
            "install": self.build_page,
            "patches": self.patches_page,
            "kernels": self.kernels_page,
            "boot": PlaceholderPage(
                "BOOT MANAGER",
                "Boot-entry management is staged for the next engine pass.",
            ),
            "tweaks": self.tweaks_page,
            "drivers": PlaceholderPage(
                "DRIVERS",
                "Kernel, DKMS, GPU, DisplayLink, Razer, and controller drivers will live here.",
            ),
            "services": PlaceholderPage(
                "SERVICES",
                "Service detection and enable/disable controls will live here.",
            ),
            "log": self.build_page,
            "terminal": self.terminal_page,
            "ai": self.ai_page,
            "settings": PlaceholderPage(
                "SETTINGS",
                "Workspace, output, theme, and build defaults will live here.",
            ),
            "about": PlaceholderPage(
                "ABOUT OPPENHEIMER",
                "DFUSE Kernel Forge\nUI 2.0 architecture",
            ),
        }

        added: set[int] = set()
        for page in self.page_map.values():
            if id(page) not in added:
                self.pages.addWidget(page)
                added.add(id(page))

        self.status_bar = QStatusBar()
        root.addWidget(self.status_bar)
        self.status_bar.showMessage("STATUS: IDLE | OPPENHEIMER READY")

        self.connect_signals()
        self.show_page("configure")
        self.kernel_source_changed("")

    @staticmethod
    def _wrap_page(title: str, subtitle: str, widget: QWidget) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        subheading = QLabel(subtitle)
        subheading.setObjectName("pageSubtitle")
        layout.addWidget(heading)
        layout.addWidget(subheading)
        layout.addWidget(widget, 1)
        return page

    @property
    def output(self):
        return self.log_panel.output

    def append_output(self, text: str) -> None:
        self.log_panel.append_output(text)

    def show_page(self, page_id: str) -> None:
        page = self.page_map.get(page_id)
        if page is None:
            return
        self.pages.setCurrentWidget(page)
        self.sidebar.set_active(page_id)

    def selected_kernel(self) -> dict:
        selected_name = self.left.kernel_source.currentText()
        return KERNEL_SOURCES[selected_name]

    def source_dir(self) -> Path:
        directory = self.selected_kernel().get("directory", "kernel")
        directory_name = str(directory)
        if self.kernel_source_type() == "tarball":
            version = self.kernel_version()
            if version:
                safe_version = version.replace(".", "-").replace("+", "-")
                directory_name = f"{directory_name}-{safe_version}"
        return WORKSPACE_DIR / directory_name

    def kernel_repository(self) -> str:
        return str(self.selected_kernel().get("url", ""))

    def kernel_source_type(self) -> str:
        source_type = self.selected_kernel().get("source_type")
        if source_type:
            return str(source_type).lower()
        return str(self.left.source_type.currentText()).lower()

    def kernel_version(self) -> str:
        return self.left.kernel_version.currentText().strip()

    def kernel_archive_url(self) -> str | None:
        if self.kernel_source_type() != "tarball":
            return None

        version = self.kernel_version()
        if not version:
            return None

        template = self.selected_kernel().get("archive_url_template")
        if not template:
            return None

        major = version.split(".", 1)[0]
        return template.format(version=version, major=major)

    def recommended_config_name(self) -> str:
        kernel_name = self.left.kernel_source.currentText().lower()
        if "zen" in kernel_name:
            return "Zen 7.1.3"

        version = self.kernel_version()
        if version.startswith("7.") or version.startswith("7"):
            return "DFUSE 7.2"
        if version.startswith("6.") or version.startswith("6"):
            return "DFUSE Legacy"
        if version.startswith("5.") or version.startswith("5"):
            return "DFUSE Slim"
        if version.startswith("next") or version.startswith("rc"):
            return "DFUSE 7.2"
        return "DFUSE 7.2"

    def build_jobs(self) -> int:
        return self.left.jobs.value()

    def build_mode(self) -> str:
        return self.left.build_preparation.currentText()

    def config_file(self) -> Path:
        selected_config = self.left.config_choice.currentText()
        if selected_config == "Auto (recommended)":
            selected_config = self.recommended_config_name()
        if selected_config not in CONFIG_FILES:
            raise ValueError(f"Unknown kernel configuration: {selected_config}")
        filename = CONFIG_FILES[selected_config]
        config_directory = self.selected_kernel().get("config_directory")
        path = PROJECT_DIR / "configs"
        if config_directory:
            path /= str(config_directory)
        return path / filename

    def apply_razer(self) -> bool:
        return self.patches_page.apply_razer.isChecked()

    def apply_xbox(self) -> bool:
        return self.patches_page.apply_xbox.isChecked()

    def apply_dualsense(self) -> bool:
        return self.patches_page.apply_dualsense.isChecked()

    def connect_signals(self) -> None:
        self.sidebar.page_requested.connect(self.show_page)
        self.left.kernel_source.currentTextChanged.connect(self.kernel_source_changed)
        self.left.config_choice.currentTextChanged.connect(self.kernel_source_changed)
        self.left.jobs.valueChanged.connect(lambda _value: self.kernel_source_changed(""))
        self.patches_page.selection_changed.connect(self.patch_selection_changed)
        self.left.btn_check.clicked.connect(self.check_environment)
        self.left.btn_install_deps.clicked.connect(self.install_dependencies)
        self.left.btn_download.clicked.connect(self.download_kernel)
        self.left.btn_prepare.clicked.connect(self.prepare_kernel)
        self.left.btn_verify.clicked.connect(self.verify_kernel)
        self.left.btn_build.clicked.connect(self.build_kernel)
        self.left.btn_install.clicked.connect(self.install_kernel)
        self.left.btn_all.clicked.connect(self.prepare_and_build)
        self.installed_kernels.remove_requested.connect(self.uninstall_kernel)
        self.tweaks_page.apply_requested.connect(self.apply_tweaks)

    def patch_selection_changed(self) -> None:
        names = self.patches_page.enabled_names()
        self.build_succeeded = False
        self.left.btn_install.setEnabled(False)
        self.append_output(
            "\nSelected patches: " + (", ".join(names) if names else "none") + "\n"
        )

    def apply_tweaks(self, state: dict, permanent: bool) -> None:
        if permanent:
            answer = QMessageBox.question(
                self,
                "Apply Tweaks Permanently",
                (
                    "This installs a systemd unit that re-applies these tweaks "
                    "on every boot.\n\nContinue?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self.tweaks_page.on_apply_result(False, permanent)
                return

        try:
            commands = (
                tweak_permanent_commands(state)
                if permanent
                else tweak_session_commands(state)
            )
        except TweakValidationError as error:
            QMessageBox.critical(self, "Invalid Tweak Settings", str(error))
            self.tweaks_page.on_apply_result(False, permanent)
            return

        action = "tweaks-permanent" if permanent else "tweaks-session"
        self.run_commands(commands, action)

    def uninstall_kernel(self, kernel_version: str) -> None:
        if kernel_version == platform.release():
            QMessageBox.warning(self, "Running Kernel", "You cannot uninstall the kernel currently in use.")
            return

        answer = QMessageBox.question(
            self,
            "Uninstall Kernel",
            (
                "Uninstall this kernel?\n\n"
                f"{kernel_version}\n\n"
                "Package-managed kernels will be removed through pacman. "
                "Manually installed kernels will have their matching modules "
                "and boot files removed.\n\nThis action cannot be undone."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            commands = uninstall_kernel_commands(kernel_version)
        except ValueError as error:
            QMessageBox.critical(self, "Invalid Kernel", str(error))
            return
        self.run_commands(commands, "uninstall")

    def kernel_source_changed(self, _name: str) -> None:
        self.build_succeeded = False
        self.left.btn_install.setEnabled(False)
        source = self.source_dir()
        self.left.workspace_label.setText(str(source))
        self.left.quick_kernel.setText(f"KERNEL  {self.left.kernel_source.currentText()}")
        self.left.quick_jobs.setText(f"CPU  {self.build_jobs()} threads")
        if self.left.config_choice.currentText() == "Auto (recommended)":
            self.left.config_choice.setCurrentText(self.recommended_config_name())
        source_type = self.selected_kernel().get("source_type", "git")
        self.left.source_type.blockSignals(True)
        self.left.source_type.setCurrentText("Tarball" if source_type == "tarball" else "Git")
        self.left.source_type.blockSignals(False)
        self.left.source_type.setEnabled(False)
        if hasattr(self, "terminal_page"):
            self.terminal_page.set_working_directory(source)
        self.status_panel.set_state("idle", "configuration changed", self.build_jobs(), False)

    def set_buttons_enabled(self, enabled: bool) -> None:
        for button in self.left.buttons():
            if button is not self.left.btn_install:
                button.setEnabled(enabled)
        self.left.btn_install.setEnabled(enabled and self.build_succeeded)

    def run_commands(self, commands: list[str], action: str) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.output.append("\nAnother operation is already running.\n")
            return
        self.show_page("build")
        self.set_buttons_enabled(False)
        self.status_panel.set_state("running", action, self.build_jobs(), self.build_succeeded)
        self.status_bar.showMessage(f"STATUS: {action.upper()} | JOBS: {self.build_jobs()}")
        self.worker = Worker(commands, action)
        self.worker.log.connect(self.append_output)
        self.worker.completed.connect(self.operation_finished)
        self.worker.start()

    def operation_finished(self, success: bool, action: str) -> None:
        if action == "build":
            self.build_succeeded = success
        messages = {
            ("build", True): "\n✓ BUILD COMPLETE\nThe kernel is ready for installation.\n",
            ("build", False): "\n✗ BUILD FAILED\nInstallation remains disabled.\n",
            ("verify", True): "\n✓ CONFIGURATION VERIFIED\n",
            ("verify", False): "\n✗ CONFIGURATION CHECK FAILED\n",
            ("prepare", True): "\n✓ CONFIGURATION AND PATCHES APPLIED\n",
            ("prepare", False): "\n✗ PREPARATION FAILED\n",
            ("download", True): "\n✓ KERNEL SOURCE READY\n",
            ("download", False): "\n✗ KERNEL DOWNLOAD FAILED\n",
            ("dependencies", True): "\n✓ DEPENDENCIES READY\n",
            ("dependencies", False): "\n✗ DEPENDENCY INSTALLATION FAILED\n",
            ("install", True): "\n✓ INSTALLATION COMPLETE\n",
            ("install", False): "\n✗ INSTALLATION FAILED\n",
            ("uninstall", True): "\n✓ KERNEL UNINSTALLED\n",
            ("uninstall", False): "\n✗ KERNEL UNINSTALL FAILED\n",
            ("tweaks-session", True): "\n✓ TWEAKS APPLIED FOR THIS SESSION\n",
            ("tweaks-session", False): "\n✗ FAILED TO APPLY SESSION TWEAKS\n",
            ("tweaks-permanent", True): "\n✓ TWEAKS APPLIED AND PERSISTED ACROSS REBOOTS\n",
            ("tweaks-permanent", False): "\n✗ FAILED TO APPLY PERMANENT TWEAKS\n",
        }
        message = messages.get((action, success))
        if message:
            self.output.append(message)
        if action == "uninstall":
            self.installed_kernels.refresh()
        if action in ("tweaks-session", "tweaks-permanent"):
            self.tweaks_page.on_apply_result(success, action == "tweaks-permanent")
        state = "complete" if success else "failed"
        self.status_panel.set_state(state, action, self.build_jobs(), self.build_succeeded)
        self.status_bar.showMessage(
            f"STATUS: {'COMPLETE' if success else 'FAILED'} | STEP: {action.upper()}"
        )
        self.set_buttons_enabled(True)

    def check_environment(self) -> None:
        self.show_page("log")
        self.output.append("\n== OPPENHEIMER SYSTEM CHECK ==\n")
        missing: list[str] = []
        for tool in REQUIRED_TOOLS:
            location = shutil.which(tool)
            symbol = "✓" if location else "✗"
            self.output.append(f"{symbol} {tool}: {location or 'missing'}\n")
            if not location:
                missing.append(tool)
        selected_config = self.config_file()
        self.output.append(
            f"\nProject: {PROJECT_DIR}\nWorkspace: {self.source_dir()}\n"
            f"Kernel source: {self.left.kernel_source.currentText()}\n"
            f"Selected config: {selected_config}\nJobs: {self.build_jobs()}\n"
            f"Patches: {', '.join(self.patches_page.enabled_names()) or 'none'}\n"
        )
        if not selected_config.is_file():
            self.output.append(f"\n✗ Configuration file not found: {selected_config}\n")
        self.output.append("\nMissing tools found.\n" if missing else "\nEnvironment check complete. ⚛\n")

    def install_dependencies(self) -> None:
        packages = " ".join(quote(package) for package in ARCH_DEPENDENCIES)
        self.run_commands([f"pkexec /usr/bin/pacman -S --needed --noconfirm {packages}"], "dependencies")

    def download_kernel(self) -> None:
        self.run_commands(
            download_commands(
                WORKSPACE_DIR,
                self.source_dir(),
                self.kernel_repository(),
                source_type=self.kernel_source_type(),
                archive_url=self.kernel_archive_url(),
            ),
            "download",
        )

    def prepare_kernel(self) -> None:
        self.build_succeeded = False
        commands = prepare_commands(
            self.source_dir(),
            self.config_file(),
            self.left.local_version.text().strip() or "-DFUSE",
            self.apply_razer(),
            RAZER_APPLY,
            apply_xbox=self.apply_xbox(),
            xbox_apply=None,
            apply_dualsense=self.apply_dualsense(),
        )
        self.run_commands(commands, "prepare")

    def verify_kernel(self) -> None:
        commands = verification_commands(self.source_dir(), self.apply_razer())
        self.run_commands(commands, "verify")

    def build_kernel(self) -> None:
        self.build_succeeded = False
        commands = build_commands(
            self.source_dir(),
            self.build_mode(),
            self.build_jobs(),
            self.config_file(),
            self.left.local_version.text().strip() or "-DFUSE",
            self.apply_razer(),
            RAZER_APPLY,
            apply_xbox=self.apply_xbox(),
            xbox_apply=None,
            apply_dualsense=self.apply_dualsense(),
        )
        self.run_commands(commands, "build")

    def install_kernel(self) -> None:
        if not self.build_succeeded:
            self.output.append("\nERROR: Build the kernel successfully before installing.\n")
            return
        self.run_commands(install_commands(self.source_dir()), "install")

    def prepare_and_build(self) -> None:
        self.build_succeeded = False
        source = self.source_dir()
        mode = self.build_mode()
        commands = download_commands(
            WORKSPACE_DIR,
            source,
            self.kernel_repository(),
            source_type=self.kernel_source_type(),
            archive_url=self.kernel_archive_url(),
        )
        if mode == "Deep Clean (mrproper)":
            commands.append(
                f"if [ -f {quote(source / 'Makefile')} ]; then cd {quote(source)} && make mrproper; fi"
            )
        commands += prepare_commands(
            source,
            self.config_file(),
            self.left.local_version.text().strip() or "-DFUSE",
            self.apply_razer(),
            RAZER_APPLY,
            apply_xbox=self.apply_xbox(),
            xbox_apply=None,
            apply_dualsense=self.apply_dualsense(),
        )
        commands += verification_commands(source, self.apply_razer())
        if mode == "Clean Build":
            commands.append(f"cd {quote(source)} && make clean")
        commands += compile_commands(
            source,
            self.build_jobs(),
            apply_xbox=self.apply_xbox(),
            apply_dualsense=self.apply_dualsense(),
        )
        self.run_commands(commands, "build")
