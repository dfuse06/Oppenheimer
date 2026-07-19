from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class Sidebar(QFrame):
    page_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 18, 14, 18)
        root.setSpacing(6)

        brand = QLabel("OPPENHEIMER")
        brand.setObjectName("sidebarBrand")
        root.addWidget(brand)

        subtitle = QLabel("KERNEL FORGE")
        subtitle.setObjectName("sidebarSubtitle")
        root.addWidget(subtitle)

        session = QFrame()
        session.setObjectName("modeCard")

        session_layout = QVBoxLayout(session)
        session_layout.setContentsMargins(12, 10, 12, 10)
        session_layout.setSpacing(3)

        session_title = QLabel("BUILD SESSION")
        session_title.setObjectName("modeTitle")

        self.session_status = QLabel("READY")
        self.session_status.setObjectName("modeText")

        self.session_details = QLabel("Kernel environment initialized")
        self.session_details.setObjectName("sessionDetails")
        self.session_details.setWordWrap(True)

        session_layout.addWidget(session_title)
        session_layout.addWidget(self.session_status)
        session_layout.addWidget(self.session_details)

        root.addWidget(session)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons: dict[str, QPushButton] = {}

        sections = [
            (
                "BUILD",
                [
                    ("configure", "⚛  Build Kernel"),
                ],
            ),
            (
                "PATCHING",
                [
                    ("patches", "◈  Patch Library"),
                ],
            ),
            (
                "KERNELS",
                [
                    ("kernels", "▦  Installed Kernels"),
                    ("boot", "♙  Boot Manager"),
                ],
            ),
            (
                "SYSTEM",
                [
                    ("tweaks", "☷  Tweaks"),
                    ("drivers", "⌘  Drivers"),
                    ("services", "⌬  Services"),
                ],
            ),
            (
                "TOOLS",
                [
                    ("terminal", ">_  Terminal"),
                    ("ai", "⚡ Oppenheimer AI"),
                ],
            ),
            (
                "SETTINGS",
                [
                    ("settings", "⚙  Settings"),
                    ("about", "ⓘ  About"),
                ],
            ),
        ]

        for section_name, pages in sections:
            heading = QLabel(section_name)
            heading.setObjectName("navHeading")
            root.addWidget(heading)

            for page_id, text in pages:
                button = QPushButton(text)
                button.setObjectName("navButton")
                button.setCheckable(True)

                button.clicked.connect(
                    lambda _checked=False, key=page_id:
                    self.page_requested.emit(key)
                )

                self.group.addButton(button)
                self.buttons[page_id] = button

                root.addWidget(button)

        root.addStretch(1)

        footer = QLabel(
            "OPPENHEIMER\n"
            "Kernel Forge v2.0"
        )
        footer.setObjectName("sidebarFooter")
        root.addWidget(footer)

        self.set_active("configure")

    def set_active(self, page_id: str) -> None:
        button = self.buttons.get(page_id)

        if button is not None:
            button.setChecked(True)

    def set_session_status(
        self,
        status: str,
        details: str = "",
    ) -> None:
        self.session_status.setText(status.upper())

        if details:
            self.session_details.setText(details)
