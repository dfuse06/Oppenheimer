from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

class BackgroundWidget(QWidget):
    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self.background = QPixmap(str(image_path))
        self.overlay = QColor(0, 0, 0, 135)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if not self.background.isNull():
            scaled = self.background.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        painter.fillRect(self.rect(), self.overlay)
        super().paintEvent(event)
