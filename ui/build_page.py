from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from engine.kernel_releases import auto_version_labels
from ui.build_log import BuildLogPanel
from ui.status_panel import StatusPanel


CPU_THREADS = os.cpu_count() or 1


class BuildPage(QWidget):
    def __init__(self, kernel_sources: list[str]) -> None:
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("BUILD KERNEL")
        title.setObjectName("pageTitle")

        subtitle = QLabel("COMPILE. CREATE. DETONATE.")
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch(1)

        self.quick_kernel = QLabel("KERNEL  waiting")
        self.quick_kernel.setObjectName("headerMetric")

        self.quick_jobs = QLabel(
            f"CPU  {CPU_THREADS} threads"
        )
        self.quick_jobs.setObjectName("headerMetric")

        header.addWidget(self.quick_jobs)
        header.addWidget(self.quick_kernel)

        root.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(12)

        root.addLayout(content, 1)

        main_column = QVBoxLayout()
        main_column.setSpacing(12)

        content.addLayout(main_column, 4)

        config_card = QFrame()
        config_card.setObjectName("glassPanel")

        config_layout = QVBoxLayout(config_card)

        config_layout.addWidget(
            self._section_title("BUILD CONFIGURATION")
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        self.kernel_source = QComboBox()
        self.kernel_source.addItems(kernel_sources)

        self.source_type = QComboBox()
        self.source_type.addItems(["Git", "Tarball"])
        self.source_type.setToolTip("Selected automatically for official vs custom kernels")

        self.kernel_version = QComboBox()
        self.kernel_version.setEditable(True)
        self.kernel_version.addItems([
            *auto_version_labels(),
            "7.2-rc4",
            "7.1.4",
            "7.0.14",
            "6.18.39",
            "6.12.96",
            "6.6.144",
            "6.1.177",
            "5.15.211",
            "5.10.260",
            "next-20260717",
        ])
        self.kernel_version.setCurrentText("6.6.144")
        if self.kernel_version.lineEdit() is not None:
            self.kernel_version.lineEdit().setPlaceholderText("Enter kernel release")

        self.workspace_label = QLabel()
        self.workspace_label.setWordWrap(True)
        self.workspace_label.setObjectName("mutedLabel")

        self.local_version = QLineEdit("-DFUSE")

        self.jobs = QSpinBox()
        self.jobs.setRange(1, CPU_THREADS)
        self.jobs.setValue(CPU_THREADS)

        self.config_choice = QComboBox()
        self.config_choice.addItems(
            [
                "Auto (recommended)",
                "DFUSE 7.2",
                "Zen 7.1.3",
                "Manjaro 7.2 (Golden)",
                "DFUSE Legacy",
                "DFUSE Slim",
            ]
        )

        self.build_preparation = QComboBox()
        self.build_preparation.addItems(
            [
                "None",
                "Clean Build",
                "Deep Clean (mrproper)",
            ]
        )

        grid.addWidget(QLabel("Kernel Source"), 0, 0)
        grid.addWidget(QLabel("Configuration"), 0, 1)
        grid.addWidget(QLabel("Local Version"), 0, 2)

        grid.addWidget(self.kernel_source, 1, 0)
        grid.addWidget(self.config_choice, 1, 1)
        grid.addWidget(self.local_version, 1, 2)

        grid.addWidget(QLabel("Source Type"), 2, 0)
        grid.addWidget(
            QLabel("Build Preparation"),
            2,
            1,
        )
        grid.addWidget(
            QLabel("Source Directory"),
            2,
            2,
        )

        grid.addWidget(self.source_type, 3, 0)
        grid.addWidget(
            self.build_preparation,
            3,
            1,
        )
        grid.addWidget(
            self.workspace_label,
            3,
            2,
        )

        grid.addWidget(QLabel("Kernel Version"), 4, 0)
        grid.addWidget(QLabel(""), 4, 1)
        grid.addWidget(QLabel(""), 4, 2)
        grid.addWidget(self.kernel_version, 5, 0)

        grid.addWidget(QLabel("Build Jobs"), 6, 0)
        grid.addWidget(QLabel(""), 6, 1)
        grid.addWidget(QLabel(""), 6, 2)
        grid.addWidget(self.jobs, 7, 0)

        config_layout.addLayout(grid)

        self.tailor_hardware = QCheckBox(
            "Tailor config to this PC's hardware (additive, safe)"
        )
        self.tailor_hardware.setToolTip(
            "Detects CPU vendor, GPU, network chipset, storage and "
            "Bluetooth, then enables the matching drivers on top of the "
            "selected base config. Never disables anything."
        )
        config_layout.addWidget(self.tailor_hardware)

        self.trim_unused_modules = QCheckBox(
            "Aggressively trim unused modules (make localmodconfig)"
        )
        self.trim_unused_modules.setToolTip(
            "Disables module support for anything not currently loaded. "
            "Produces a smaller/faster-building kernel, but can omit "
            "drivers for hardware that is not active right now (unplugged "
            "USB devices, a second GPU, etc.)."
        )
        config_layout.addWidget(self.trim_unused_modules)

        main_column.addWidget(config_card)

        self.log_panel = BuildLogPanel()

        # The build log now takes all remaining vertical space.
        main_column.addWidget(self.log_panel, 1)

        side_column = QVBoxLayout()
        side_column.setSpacing(12)

        content.addLayout(side_column, 1)

        actions = QFrame()
        actions.setObjectName("glassPanel")

        action_layout = QVBoxLayout(actions)

        action_layout.addWidget(
            self._section_title("BUILD ACTIONS")
        )

        self.btn_check = QPushButton(
            "0. CHECK ENVIRONMENT"
        )
        self.btn_install_deps = QPushButton(
            "INSTALL DEPENDENCIES"
        )
        self.btn_detect_hw = QPushButton(
            "DETECT HARDWARE"
        )
        self.btn_download = QPushButton(
            "1. DOWNLOAD SOURCE"
        )
        self.btn_prepare = QPushButton(
            "2. APPLY CONFIG + PATCHES"
        )
        self.btn_verify = QPushButton(
            "3. VERIFY CONFIGURATION"
        )
        self.btn_build = QPushButton(
            "4. START BUILD"
        )
        self.btn_install = QPushButton(
            "5. INSTALL KERNEL"
        )
        self.btn_all = QPushButton(
            "PREPARE + BUILD"
        )

        self.btn_all.setObjectName("primaryButton")
        self.btn_build.setObjectName("primaryButton")
        self.btn_install.setEnabled(False)

        for button in self.buttons():
            action_layout.addWidget(button)

        side_column.addWidget(actions)

        self.status_panel = StatusPanel()
        side_column.addWidget(self.status_panel)

        side_column.addStretch(1)

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    @property
    def output(self):
        return self.log_panel.output

    def buttons(self) -> list[QPushButton]:
        return [
            self.btn_check,
            self.btn_install_deps,
            self.btn_detect_hw,
            self.btn_download,
            self.btn_prepare,
            self.btn_verify,
            self.btn_build,
            self.btn_install,
            self.btn_all,
        ]
