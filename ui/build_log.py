from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

class BuildLogPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("glassPanel")
        layout = QVBoxLayout(self)
        title = QLabel("BUILD LOG")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def append_output(self, text: str) -> None:
        self.output.insertPlainText(text)
        bar = self.output.verticalScrollBar()
        bar.setValue(bar.maximum())
