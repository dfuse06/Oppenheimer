import os
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

CPU_THREADS = os.cpu_count() or 1

class LeftPanel(QWidget):
    def __init__(self, kernel_sources: list[str]) -> None:
        super().__init__()
        self.setObjectName("glassPanel")
        layout = QVBoxLayout(self)
        title = QLabel("CONFIGURATION")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        layout.addWidget(QLabel("Kernel source"))
        self.kernel_source = QComboBox(); self.kernel_source.addItems(kernel_sources); layout.addWidget(self.kernel_source)
        self.workspace_label = QLabel(); self.workspace_label.setWordWrap(True); layout.addWidget(self.workspace_label)
        layout.addWidget(QLabel("Kernel LOCALVERSION"))
        self.local_version = QLineEdit("-DFUSE"); layout.addWidget(self.local_version)
        layout.addWidget(QLabel(f"Build jobs / threads: detected {CPU_THREADS}"))
        self.jobs = QSpinBox(); self.jobs.setRange(1, CPU_THREADS); self.jobs.setValue(CPU_THREADS); layout.addWidget(self.jobs)
        layout.addWidget(QLabel("Configuration"))
        self.config_choice = QComboBox(); self.config_choice.addItems(["DFUSE 7.2", "Manjaro 7.2 (Golden)", "DFUSE Legacy", "DFUSE Slim"]); layout.addWidget(self.config_choice)
        self.apply_razer = QCheckBox("Apply DFUSE Razer HID driver"); self.apply_razer.setChecked(True); layout.addWidget(self.apply_razer)
        layout.addWidget(QLabel("Build preparation"))
        self.build_preparation = QComboBox(); self.build_preparation.addItems(["None", "Clean Build", "Deep Clean (mrproper)"]); layout.addWidget(self.build_preparation)
        self.btn_check = QPushButton("0. Check Environment")
        self.btn_install_deps = QPushButton("Install Missing Dependencies")
        self.btn_download = QPushButton("1. Download Linux Kernel")
        self.btn_prepare = QPushButton("2. Apply Config + Patches")
        self.btn_verify = QPushButton("3. Verify Configuration")
        self.btn_build = QPushButton("4. Build Kernel")
        self.btn_install = QPushButton("5. Install Kernel")
        self.btn_all = QPushButton("Prepare + Build")
        self.btn_install.setEnabled(False)
        for button in self.buttons(): layout.addWidget(button)
        layout.addStretch()

    def buttons(self) -> list[QPushButton]:
        return [self.btn_check, self.btn_install_deps, self.btn_download, self.btn_prepare, self.btn_verify, self.btn_build, self.btn_install, self.btn_all]
