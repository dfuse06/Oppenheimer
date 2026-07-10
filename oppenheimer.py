#!/usr/bin/env python3

import os
import shlex
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


PROJECT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

RAZER_APPLY = PROJECT_DIR / "patches/hid-razer/apply.py"

KERNEL_SOURCES = {
    "Linux Stable": {
        "url": "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git",
        "directory": "linux-stable",
        "config_directory": None,
    },
    "Linux Zen": {
        "url": "https://github.com/zen-kernel/zen-kernel.git",
        "directory": "linux-zen",
        "config_directory": "zen",
    },
}

CPU_THREADS = os.cpu_count() or 1

ARCH_DEPENDENCIES = [
    "base-devel",
    "git",
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
]

REQUIRED_TOOLS = [
    "git",
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
]

BOOT_CRITICAL_OPTIONS = {
    "CONFIG_BLK_DEV_INITRD": "y",
    "CONFIG_DEVTMPFS": "y",
    "CONFIG_DEVTMPFS_MOUNT": "y",
    "CONFIG_EFI": "y",
    "CONFIG_EFI_PARTITION": "y",
    "CONFIG_EFIVAR_FS": "y",
    "CONFIG_EXT4_FS": "y",
    "CONFIG_FAT_FS": "y",
    "CONFIG_VFAT_FS": "y",
}

FILESYSTEM_OPTIONS = [
    "FAT_FS",
    "VFAT_FS",
    "MSDOS_FS",
    "NLS",
    "NLS_CODEPAGE_437",
    "NLS_ISO8859_1",
]


def quote(value: object) -> str:
    return shlex.quote(str(value))


class Worker(QThread):
    log = Signal(str)
    completed = Signal(bool, str)

    def __init__(self, commands: list[str], action: str):
        super().__init__()
        self.commands = commands
        self.action = action

    def run(self) -> None:
        for command in self.commands:
            self.log.emit(f"\n$ {command}\n")

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                executable="/bin/bash",
                bufsize=1,
            )

            if process.stdout is not None:
                for line in process.stdout:
                    self.log.emit(line)

            return_code = process.wait()

            if return_code != 0:
                self.log.emit(
                    f"\nERROR: command failed with exit code "
                    f"{return_code}\n"
                )
                self.completed.emit(False, self.action)
                return

        self.log.emit("\nDONE.\n")
        self.completed.emit(True, self.action)


class Oppenheimer(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.worker: Worker | None = None
        self.build_succeeded = False

        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        self.setWindowTitle("Oppenheimer")
        self.resize(950, 760)

        layout = QVBoxLayout(self)

        self.title = QLabel("OPPENHEIMER ⚛️")
        layout.addWidget(self.title)

        layout.addWidget(QLabel("Kernel source:"))

        self.kernel_source = QComboBox()
        self.kernel_source.addItems(KERNEL_SOURCES.keys())
        layout.addWidget(self.kernel_source)

        self.workspace_label = QLabel()
        layout.addWidget(self.workspace_label)

        layout.addWidget(QLabel("Kernel LOCALVERSION:"))

        self.local_version = QLineEdit("-DFUSE")
        layout.addWidget(self.local_version)

        layout.addWidget(
            QLabel(f"Build Jobs / Threads: detected {CPU_THREADS}")
        )

        self.jobs = QSpinBox()
        self.jobs.setMinimum(1)
        self.jobs.setMaximum(CPU_THREADS)
        self.jobs.setValue(CPU_THREADS)
        layout.addWidget(self.jobs)

        layout.addWidget(QLabel("Configuration:"))

        self.use_slim = QCheckBox("Use DFUSE slim config")
        self.use_slim.setChecked(True)
        layout.addWidget(self.use_slim)

        self.apply_razer = QCheckBox(
            "Apply DFUSE Razer HID driver"
        )
        self.apply_razer.setChecked(True)
        layout.addWidget(self.apply_razer)

        layout.addWidget(QLabel("Build preparation:"))

        self.build_preparation = QComboBox()
        self.build_preparation.addItems([
            "None",
            "Clean Build",
            "Deep Clean (mrproper)",
        ])
        layout.addWidget(self.build_preparation)

        self.btn_check = QPushButton("0. Check Environment")
        self.btn_install_deps = QPushButton(
            "Install Missing Dependencies"
        )
        self.btn_download = QPushButton(
            "1. Download Linux Kernel"
        )
        self.btn_prepare = QPushButton(
            "2. Apply Config + Patches"
        )
        self.btn_verify = QPushButton(
            "3. Verify Configuration"
        )
        self.btn_build = QPushButton("4. Build Kernel")
        self.btn_install = QPushButton("5. Install Kernel")
        self.btn_all = QPushButton("Prepare + Build")

        self.btn_install.setEnabled(False)

        for button in [
            self.btn_check,
            self.btn_install_deps,
            self.btn_download,
            self.btn_prepare,
            self.btn_verify,
            self.btn_build,
            self.btn_install,
            self.btn_all,
        ]:
            layout.addWidget(button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.kernel_source.currentTextChanged.connect(
            self.kernel_source_changed
        )

        self.btn_check.clicked.connect(self.check_environment)
        self.btn_install_deps.clicked.connect(
            self.install_dependencies
        )
        self.btn_download.clicked.connect(self.download_kernel)
        self.btn_prepare.clicked.connect(self.prepare_kernel)
        self.btn_verify.clicked.connect(self.verify_kernel)
        self.btn_build.clicked.connect(self.build_kernel)
        self.btn_install.clicked.connect(self.install_kernel)
        self.btn_all.clicked.connect(self.prepare_and_build)

        self.kernel_source_changed(
            self.kernel_source.currentText()
        )

    def append_output(self, text: str) -> None:
        self.output.insertPlainText(text)

        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_buttons_enabled(self, enabled: bool) -> None:
        for button in [
            self.btn_check,
            self.btn_install_deps,
            self.btn_download,
            self.btn_prepare,
            self.btn_verify,
            self.btn_build,
            self.btn_all,
        ]:
            button.setEnabled(enabled)

        self.btn_install.setEnabled(
            enabled and self.build_succeeded
        )

    def run_commands(
        self,
        commands: list[str],
        action: str,
    ) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.output.append(
                "\nAnother operation is already running.\n"
            )
            return

        self.set_buttons_enabled(False)

        self.worker = Worker(commands, action)
        self.worker.log.connect(self.append_output)
        self.worker.completed.connect(self.operation_finished)
        self.worker.start()

    def operation_finished(
        self,
        success: bool,
        action: str,
    ) -> None:
        if action == "build":
            self.build_succeeded = success

            if success:
                self.output.append(
                    "\n✓ BUILD COMPLETE\n"
                    "The kernel is ready for installation.\n"
                )
            else:
                self.output.append(
                    "\n✗ BUILD FAILED\n"
                    "Installation remains disabled.\n"
                )

        elif action == "verify":
            if success:
                self.output.append(
                    "\n✓ CONFIGURATION VERIFIED\n"
                    "The selected kernel is ready to build.\n"
                )
            else:
                self.output.append(
                    "\n✗ CONFIGURATION CHECK FAILED\n"
                    "Fix the reported option before building.\n"
                )

        elif action == "prepare":
            self.build_succeeded = False

            if success:
                self.output.append(
                    "\n✓ CONFIGURATION AND PATCHES APPLIED\n"
                )
            else:
                self.output.append(
                    "\n✗ PREPARATION FAILED\n"
                )

        elif action == "download":
            self.build_succeeded = False

            if success:
                self.output.append(
                    "\n✓ KERNEL SOURCE READY\n"
                )

        elif action == "install":
            if success:
                self.output.append(
                    "\n✓ INSTALLATION COMPLETE\n"
                    "Review the GRUB entry before rebooting.\n"
                )
            else:
                self.output.append(
                    "\n✗ INSTALLATION FAILED\n"
                )

        self.set_buttons_enabled(True)

    def selected_kernel(self) -> dict[str, str | None]:
        return KERNEL_SOURCES[
            self.kernel_source.currentText()
        ]

    def source_dir(self) -> Path:
        directory = self.selected_kernel()["directory"]
        return WORKSPACE_DIR / str(directory)

    def kernel_repository(self) -> str:
        return str(self.selected_kernel()["url"])

    def kernel_source_changed(self, _name: str) -> None:
        self.build_succeeded = False

        if hasattr(self, "btn_install"):
            self.btn_install.setEnabled(False)

        if hasattr(self, "workspace_label"):
            self.workspace_label.setText(
                f"Workspace: {self.source_dir()}"
            )

    def config_file(self) -> Path:
        selected = self.selected_kernel()
        config_directory = selected["config_directory"]

        filename = (
            "config.dfuse-slim"
            if self.use_slim.isChecked()
            else "config.dfuse"
        )

        if config_directory:
            return (
                PROJECT_DIR
                / "configs"
                / str(config_directory)
                / filename
            )

        return PROJECT_DIR / "configs" / filename

    def build_jobs(self) -> int:
        return self.jobs.value()

    def build_mode(self) -> str:
        return self.build_preparation.currentText()

    def python_executable(self) -> str:
        return shutil.which("python3") or "python3"

    def check_environment(self) -> None:
        self.output.append(
            "\n== OPPENHEIMER SYSTEM CHECK ==\n"
        )

        missing_tools: list[str] = []

        for tool in REQUIRED_TOOLS:
            location = shutil.which(tool)

            if location:
                self.output.append(f"✓ {tool}: {location}")
            else:
                self.output.append(f"✗ {tool}: missing")
                missing_tools.append(tool)

        selected_config = self.config_file()

        self.output.append(f"\nProject: {PROJECT_DIR}")
        self.output.append(f"Workspace: {self.source_dir()}")
        self.output.append(
            f"Selected kernel: "
            f"{self.kernel_source.currentText()}"
        )
        self.output.append(
            f"Selected config: {selected_config}"
        )
        self.output.append(
            f"Build preparation: {self.build_mode()}"
        )
        self.output.append(
            f"CPU threads detected: {CPU_THREADS}"
        )
        self.output.append(
            f"Selected build jobs: {self.build_jobs()}"
        )

        checks = [
            ("Selected config", selected_config),
            ("Razer apply script", RAZER_APPLY),
            (
                "Razer driver Kconfig",
                PROJECT_DIR
                / "patches/hid-razer/driver/Kconfig",
            ),
            (
                "Razer driver Makefile",
                PROJECT_DIR
                / "patches/hid-razer/driver/Makefile",
            ),
        ]

        missing_files = []

        for name, path in checks:
            exists = path.exists()
            symbol = "✓" if exists else "✗"
            self.output.append(f"{symbol} {name}: {path}")

            if not exists:
                missing_files.append(str(path))

        free_bytes = shutil.disk_usage(PROJECT_DIR).free
        free_gib = free_bytes / (1024 ** 3)

        self.output.append(
            f"Free disk space: {free_gib:.1f} GiB"
        )

        if free_gib < 20:
            self.output.append(
                "⚠ Less than 20 GiB is available. "
                "A kernel build may run out of space."
            )

        if missing_tools:
            self.output.append(
                "\nMissing tools found. "
                "Click Install Missing Dependencies."
            )
        elif missing_files:
            self.output.append(
                "\nOne or more selected project files are missing."
            )
        else:
            self.output.append(
                "\nEnvironment check complete. ⚛️"
            )

    def install_dependencies(self) -> None:
        packages = " ".join(
            quote(package)
            for package in ARCH_DEPENDENCIES
        )

        commands = [
            "if command -v pacman >/dev/null 2>&1; then "
            f"pkexec /usr/bin/pacman -S --needed {packages}; "
            "else "
            "echo 'Automatic dependency installation currently "
            "supports Arch-based distributions only.'; "
            "exit 1; "
            "fi"
        ]

        self.run_commands(commands, "dependencies")

    def download_commands(self) -> list[str]:
        source_dir = self.source_dir()
        repository = self.kernel_repository()

        return [
            f"mkdir -p {quote(WORKSPACE_DIR)}",

            f"if [ -d {quote(source_dir / '.git')} ]; then "
            "echo 'Selected kernel workspace already exists. "
            "No files were deleted.'; "
            f"git -C {quote(source_dir)} status --short; "
            "else "
            f"git clone --depth=1 {quote(repository)} "
            f"{quote(source_dir)}; "
            "fi",
        ]

    def download_kernel(self) -> None:
        self.run_commands(
            self.download_commands(),
            "download",
        )

    def prepare_commands(self) -> list[str]:
        source_dir = self.source_dir()
        config = self.config_file()
        version = (
            self.local_version.text().strip()
            or "-DFUSE"
        )

        commands = [
            f"test -d {quote(source_dir / '.git')} || "
            "(echo 'Kernel workspace is missing. "
            "Download it first.'; exit 1)",

            f"test -f {quote(config)} || "
            f"(echo 'Selected config is missing: "
            f"{quote(config)}'; exit 1)",

            f"cp {quote(config)} "
            f"{quote(source_dir / '.config')}",

            f"cd {quote(source_dir)} && "
            f"scripts/config --set-str LOCALVERSION "
            f"{quote(version)}",

            f"cd {quote(source_dir)} && "
            "scripts/config --disable LOCALVERSION_AUTO",

            f"cd {quote(source_dir)} && "
            "scripts/config --set-str DEFAULT_HOSTNAME dfuse",
        ]

        for option in FILESYSTEM_OPTIONS:
            commands.append(
                f"cd {quote(source_dir)} && "
                f"scripts/config --enable {quote(option)}"
            )

        if self.apply_razer.isChecked():
            commands.extend([
                f"test -x {quote(RAZER_APPLY)} || "
                f"(echo 'Missing Razer apply script: "
                f"{quote(RAZER_APPLY)}'; exit 1)",

                f"{quote(self.python_executable())} "
                f"{quote(RAZER_APPLY)} "
                f"--kernel-src {quote(source_dir)}",
            ])
        else:
            commands.append(
                f"cd {quote(source_dir)} && "
                "scripts/config --disable HID_RAZER_DFUSE"
            )

        commands.extend([
            f"cd {quote(source_dir)} && "
            "scripts/config --disable LOCALVERSION_AUTO",

            f"cd {quote(source_dir)} && make olddefconfig",

            f"cd {quote(source_dir)} && "
            "echo 'Kernel release:' && "
            "make -s kernelrelease",

            f"cd {quote(source_dir)} && "
            "grep -E "
            "'HID_RAZER|LOCALVERSION|DEFAULT_HOSTNAME|"
            "FAT_FS|VFAT_FS|EXT4_FS|EFI' "
            ".config || true",
        ])

        return commands

    def prepare_kernel(self) -> None:
        self.build_succeeded = False
        self.run_commands(
            self.prepare_commands(),
            "prepare",
        )

    def verification_commands(self) -> list[str]:
        source_dir = self.source_dir()

        commands = [
            f"test -f {quote(source_dir / '.config')} || "
            "(echo 'Kernel has not been configured.'; exit 1)",
        ]

        for option, expected_value in (
            BOOT_CRITICAL_OPTIONS.items()
        ):
            expected_line = f"{option}={expected_value}"

            commands.append(
                f"grep -qx {quote(expected_line)} "
                f"{quote(source_dir / '.config')} || "
                f"(echo 'Missing boot-critical option: "
                f"{expected_line}'; exit 1)"
            )

        if self.apply_razer.isChecked():
            commands.extend([
                f"grep -qx "
                f"'CONFIG_HID_RAZER_DFUSE=m' "
                f"{quote(source_dir / '.config')} || "
                "(echo 'DFUSE Razer driver is not enabled.'; "
                "exit 1)",

                f"grep -qx "
                f"'# CONFIG_HID_RAZER is not set' "
                f"{quote(source_dir / '.config')} || "
                "(echo 'Stock Razer driver is still enabled.'; "
                "exit 1)",

                f"test -f "
                f"{quote(source_dir / 'drivers/hid/hid-razer/Kconfig')} "
                "|| "
                "(echo 'Razer Kconfig is missing from workspace.'; "
                "exit 1)",

                f"test -f "
                f"{quote(source_dir / 'drivers/hid/hid-razer/Makefile')} "
                "|| "
                "(echo 'Razer Makefile is missing from workspace.'; "
                "exit 1)",
            ])

        commands.extend([
            f"cd {quote(source_dir)} && "
            "echo 'Configuration verification passed.'",

            f"cd {quote(source_dir)} && "
            "make -s kernelrelease",
        ])

        return commands

    def verify_kernel(self) -> None:
        self.run_commands(
            self.verification_commands(),
            "verify",
        )

    def compile_commands(self) -> list[str]:
        source_dir = self.source_dir()
        jobs = self.build_jobs()

        return [
            f"cd {quote(source_dir)} && make -j{jobs}",

            f"test -s "
            f"{quote(source_dir / 'arch/x86/boot/bzImage')} "
            "|| "
            "(echo 'ERROR: bzImage was not created.'; exit 1)",

            f"test -s "
            f"{quote(source_dir / 'System.map')} || "
            "(echo 'ERROR: System.map was not created.'; exit 1)",

            f"test -s "
            f"{quote(source_dir / 'Module.symvers')} || "
            "(echo 'ERROR: Module.symvers was not created.'; "
            "exit 1)",

            f"cd {quote(source_dir)} && "
            "echo 'Built kernel release:' && "
            "make -s kernelrelease",
        ]

    def build_commands(self) -> list[str]:
        source_dir = self.source_dir()
        mode = self.build_mode()

        commands: list[str] = []

        if mode == "Deep Clean (mrproper)":
            commands.append(
                f"cd {quote(source_dir)} && make mrproper"
            )

            # mrproper removes .config, so restore configuration
            # and reapply selected patches before verification.
            commands.extend(self.prepare_commands())

        else:
            commands.extend(self.verification_commands())

            if mode == "Clean Build":
                commands.append(
                    f"cd {quote(source_dir)} && make clean"
                )

        # Deep Clean still needs verification after configuration
        # and patch restoration.
        if mode == "Deep Clean (mrproper)":
            commands.extend(self.verification_commands())

        commands.extend(self.compile_commands())

        return commands

    def build_kernel(self) -> None:
        self.build_succeeded = False
        self.run_commands(
            self.build_commands(),
            "build",
        )

    def install_kernel(self) -> None:
        if not self.build_succeeded:
            self.output.append(
                "\nERROR: Build the kernel successfully "
                "before installing.\n"
            )
            return

        source_dir = self.source_dir()

        commands = [
            f"test -s "
            f"{quote(source_dir / 'arch/x86/boot/bzImage')} "
            "|| "
            "(echo 'Kernel image missing.'; exit 1)",

            f"release=$(cd {quote(source_dir)} && "
            "make -s kernelrelease) && "
            "echo \"Installing kernel release: $release\"",

            f"pkexec /usr/bin/make "
            f"-C {quote(source_dir)} modules_install",

            f"pkexec /usr/bin/make "
            f"-C {quote(source_dir)} install",

            "if command -v grub-mkconfig "
            ">/dev/null 2>&1; then "
            "pkexec /usr/bin/grub-mkconfig "
            "-o /boot/grub/grub.cfg; "
            "else "
            "echo 'grub-mkconfig was not found. "
            "Update your bootloader manually.'; "
            "fi",

            f"release=$(cd {quote(source_dir)} && "
            "make -s kernelrelease) && "
            "test -d \"/lib/modules/$release\" || "
            "(echo \"Module directory missing: "
            "/lib/modules/$release\"; exit 1)",

            f"cd {quote(source_dir)} && "
            "echo 'Installed release:' && "
            "make -s kernelrelease",
        ]

        self.run_commands(commands, "install")

    def prepare_and_build(self) -> None:
        self.build_succeeded = False

        source_dir = self.source_dir()
        mode = self.build_mode()

        commands = self.download_commands()

        if mode == "Deep Clean (mrproper)":
            commands.append(
                f"if [ -f {quote(source_dir / 'Makefile')} ]; then "
                f"cd {quote(source_dir)} && make mrproper; "
                "fi"
            )

        commands.extend(self.prepare_commands())
        commands.extend(self.verification_commands())

        if mode == "Clean Build":
            commands.append(
                f"cd {quote(source_dir)} && make clean"
            )

        commands.extend(self.compile_commands())

        self.run_commands(commands, "build")


if __name__ == "__main__":
    app = QApplication([])
    window = Oppenheimer()
    window.show()
    app.exec()
