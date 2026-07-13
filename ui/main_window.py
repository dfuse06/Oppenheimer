import shlex, shutil
from pathlib import Path
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStatusBar, QVBoxLayout
from engine.builder import build_commands, compile_commands, download_commands, prepare_commands
from engine.installer import install_commands
from engine.verifier import verification_commands
from engine.worker import Worker
from ui.background import BackgroundWidget
from ui.build_log import BuildLogPanel
from ui.left_panel import LeftPanel
from ui.status_panel import StatusPanel
from ui.styles import APP_STYLE

PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"
ASSET_DIR = PROJECT_DIR / "assets"
RAZER_APPLY = PROJECT_DIR / "patches/hid-razer/apply.py"

KERNEL_SOURCES = {
    "Linux Stable": {"url": "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git", "directory": "linux-stable", "config_directory": None},
    "Linux Zen": {"url": "https://github.com/zen-kernel/zen-kernel.git", "directory": "linux-zen", "config_directory": "zen"},
}
ARCH_DEPENDENCIES = ["base-devel", "git", "bc", "flex", "bison", "openssl", "elfutils", "pahole", "cpio", "perl", "python", "rsync", "kmod", "zstd"]
REQUIRED_TOOLS = ["git", "make", "gcc", "bc", "flex", "bison", "openssl", "pahole", "cpio", "perl", "python3", "rsync", "depmod", "zstd"]

def quote(value: object) -> str:
    return shlex.quote(str(value))

class Oppenheimer(BackgroundWidget):
    def __init__(self) -> None:
        super().__init__(ASSET_DIR / "oppenheimer-background.png")

        self.worker: Worker | None = None
        self.build_succeeded = False

        for path in (WORKSPACE_DIR, OUTPUT_DIR, LOG_DIR):
            path.mkdir(parents=True, exist_ok=True)

        self.setWindowTitle("Oppenheimer")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(APP_STYLE)

        root = QVBoxLayout(self)

        self.title = QLabel("OPPENHEIMER")
        self.title.setObjectName("appTitle")
        root.addWidget(self.title)

        body = QHBoxLayout()
        root.addLayout(body, 1)

        self.left = LeftPanel(list(KERNEL_SOURCES.keys()))
        self.log_panel = BuildLogPanel()
        self.status_panel = StatusPanel()

        center = QVBoxLayout()
        center.addStretch(5)
        center.addWidget(self.log_panel, 4)

        body.addWidget(self.left, 3)
        body.addLayout(center, 7)
        body.addWidget(self.status_panel, 3)

        self.status_bar = QStatusBar()
        root.addWidget(self.status_bar)
        self.status_bar.showMessage(
            "STATUS: IDLE | OPPENHEIMER READY"
        )

        self.connect_signals()
        self.kernel_source_changed("")

    @property
    def output(self): return self.log_panel.output
    def append_output(self, text: str) -> None: self.log_panel.append_output(text)
    def selected_kernel(self): return KERNEL_SOURCES[self.left.kernel_source.currentText()]
    def source_dir(self) -> Path: return WORKSPACE_DIR / str(self.selected_kernel()["directory"])
    def kernel_repository(self) -> str: return str(self.selected_kernel()["url"])
    def build_jobs(self) -> int: return self.left.jobs.value()
    def build_mode(self) -> str: return self.left.build_preparation.currentText()

    def config_file(self) -> Path:
        names = {"DFUSE 7.2": "config.dfuse-7.2", "Manjaro 7.2 (Golden)": "config.manjaro-7.2", "DFUSE Legacy": "config.dfuse", "DFUSE Slim": "config.dfuse-slim"}
        filename = names[self.left.config_choice.currentText()]
        config_dir = self.selected_kernel()["config_directory"]
        return PROJECT_DIR / "configs" / (str(config_dir) if config_dir else "") / filename

    def connect_signals(self) -> None:
        self.left.kernel_source.currentTextChanged.connect(self.kernel_source_changed)
        self.left.config_choice.currentTextChanged.connect(self.kernel_source_changed)
        self.left.btn_check.clicked.connect(self.check_environment)
        self.left.btn_install_deps.clicked.connect(self.install_dependencies)
        self.left.btn_download.clicked.connect(self.download_kernel)
        self.left.btn_prepare.clicked.connect(self.prepare_kernel)
        self.left.btn_verify.clicked.connect(self.verify_kernel)
        self.left.btn_build.clicked.connect(self.build_kernel)
        self.left.btn_install.clicked.connect(self.install_kernel)
        self.left.btn_all.clicked.connect(self.prepare_and_build)

    def kernel_source_changed(self, _name: str) -> None:
        self.build_succeeded = False
        self.left.btn_install.setEnabled(False)
        self.left.workspace_label.setText(f"Workspace: {self.source_dir()}")
        self.status_panel.set_state("idle", "configuration changed", self.build_jobs(), False)

    def set_buttons_enabled(self, enabled: bool) -> None:
        for button in self.left.buttons():
            if button is not self.left.btn_install: button.setEnabled(enabled)
        self.left.btn_install.setEnabled(enabled and self.build_succeeded)

    def run_commands(self, commands: list[str], action: str) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.output.append("\nAnother operation is already running.\n"); return
        self.set_buttons_enabled(False)
        self.status_panel.set_state("running", action, self.build_jobs(), self.build_succeeded)
        self.status_bar.showMessage(f"STATUS: {action.upper()} | JOBS: {self.build_jobs()}")
        self.worker = Worker(commands, action)
        self.worker.log.connect(self.append_output)
        self.worker.completed.connect(self.operation_finished)
        self.worker.start()

    def operation_finished(self, success: bool, action: str) -> None:
        if action == "build": self.build_succeeded = success
        messages = {
            ("build", True): "\n✓ BUILD COMPLETE\nThe kernel is ready for installation.\n",
            ("build", False): "\n✗ BUILD FAILED\nInstallation remains disabled.\n",
            ("verify", True): "\n✓ CONFIGURATION VERIFIED\n",
            ("verify", False): "\n✗ CONFIGURATION CHECK FAILED\n",
            ("prepare", True): "\n✓ CONFIGURATION AND PATCHES APPLIED\n",
            ("prepare", False): "\n✗ PREPARATION FAILED\n",
            ("download", True): "\n✓ KERNEL SOURCE READY\n",
            ("install", True): "\n✓ INSTALLATION COMPLETE\n",
            ("install", False): "\n✗ INSTALLATION FAILED\n",
        }
        if (action, success) in messages: self.output.append(messages[(action, success)])
        self.status_panel.set_state("complete" if success else "failed", action, self.build_jobs(), self.build_succeeded)
        self.status_bar.showMessage(f"STATUS: {'COMPLETE' if success else 'FAILED'} | STEP: {action.upper()}")
        self.set_buttons_enabled(True)

    def check_environment(self) -> None:
        self.output.append("\n== OPPENHEIMER SYSTEM CHECK ==\n")
        missing = []
        for tool in REQUIRED_TOOLS:
            location = shutil.which(tool)
            self.output.append(f"{'✓' if location else '✗'} {tool}: {location or 'missing'}\n")
            if not location: missing.append(tool)
        self.output.append(f"\nProject: {PROJECT_DIR}\nWorkspace: {self.source_dir()}\nSelected config: {self.config_file()}\nJobs: {self.build_jobs()}\n")
        self.output.append("\nMissing tools found.\n" if missing else "\nEnvironment check complete. ⚛️\n")

    def install_dependencies(self) -> None:
        packages = " ".join(quote(x) for x in ARCH_DEPENDENCIES)
        self.run_commands([f"pkexec /usr/bin/pacman -S --needed {packages}"], "dependencies")
    def download_kernel(self) -> None:
        self.run_commands(download_commands(WORKSPACE_DIR, self.source_dir(), self.kernel_repository()), "download")
    def prepare_kernel(self) -> None:
        self.build_succeeded = False
        self.run_commands(prepare_commands(self.source_dir(), self.config_file(), self.left.local_version.text().strip() or "-DFUSE", self.left.apply_razer.isChecked(), RAZER_APPLY), "prepare")
    def verify_kernel(self) -> None:
        self.run_commands(verification_commands(self.source_dir(), self.left.apply_razer.isChecked()), "verify")
    def build_kernel(self) -> None:
        self.build_succeeded = False
        self.run_commands(build_commands(self.source_dir(), self.build_mode(), self.build_jobs(), self.config_file(), self.left.local_version.text().strip() or "-DFUSE", self.left.apply_razer.isChecked(), RAZER_APPLY), "build")
    def install_kernel(self) -> None:
        if not self.build_succeeded:
            self.output.append("\nERROR: Build the kernel successfully before installing.\n"); return
        self.run_commands(install_commands(self.source_dir()), "install")

    def prepare_and_build(self) -> None:
        self.build_succeeded = False
        source = self.source_dir(); mode = self.build_mode()
        commands = download_commands(WORKSPACE_DIR, source, self.kernel_repository())
        if mode == "Deep Clean (mrproper)": commands.append(f"if [ -f {quote(source / 'Makefile')} ]; then cd {quote(source)} && make mrproper; fi")
        commands += prepare_commands(source, self.config_file(), self.left.local_version.text().strip() or "-DFUSE", self.left.apply_razer.isChecked(), RAZER_APPLY)
        commands += verification_commands(source, self.left.apply_razer.isChecked())
        if mode == "Clean Build": commands.append(f"cd {quote(source)} && make clean")
        commands += compile_commands(source, self.build_jobs())
        self.run_commands(commands, "build")
