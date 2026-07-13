#!/usr/bin/env python3
from PySide6.QtWidgets import QApplication
from ui.main_window import Oppenheimer

if __name__ == "__main__":
    app = QApplication([])
    window = Oppenheimer()
    window.show()
    app.exec()
