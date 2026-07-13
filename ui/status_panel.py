from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

class StatusPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("glassPanel")
        layout = QVBoxLayout(self)
        title = QLabel("BUILD STATUS")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.status = QLabel("IDLE")
        self.status.setObjectName("statusValue")
        layout.addWidget(self.status)
        self.kernel = QLabel("Kernel: waiting")
        self.jobs = QLabel("Jobs: waiting")
        self.current_step = QLabel("Current step: none")
        self.ready = QLabel("Ready: no")
        for widget in (self.kernel, self.jobs, self.current_step, self.ready):
            widget.setWordWrap(True)
            layout.addWidget(widget)
        layout.addStretch()

    def set_state(self, status: str, step: str, jobs: int, ready: bool, kernel: str = "waiting") -> None:
        self.status.setText(status.upper())
        self.current_step.setText(f"Current step: {step}")
        self.jobs.setText(f"Jobs: {jobs}")
        self.ready.setText(f"Ready: {'yes' if ready else 'no'}")
        self.kernel.setText(f"Kernel: {kernel}")
