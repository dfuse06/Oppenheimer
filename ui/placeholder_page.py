from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        root.addWidget(heading)

        card = QFrame()
        card.setObjectName("glassPanel")
        layout = QVBoxLayout(card)
        message = QLabel(subtitle)
        message.setObjectName("placeholderMessage")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message, 1)
        root.addWidget(card, 1)
