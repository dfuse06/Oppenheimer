#!/usr/bin/env python3

from PySide6.QtWidgets import QApplication

from ui.main_window import Oppenheimer
from ui.fonts import application_font, load_application_fonts


if __name__ == "__main__":
    app = QApplication([])

    font_family = load_application_fonts()
    app.setFont(application_font(font_family, 13))

    window = Oppenheimer()
    window.show()

    app.exec()
