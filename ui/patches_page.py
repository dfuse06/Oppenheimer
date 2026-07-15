from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PatchCard(QFrame):
    toggled = Signal()
    validate_requested = Signal()

    def __init__(
        self,
        name: str,
        description: str,
        path: Path,
        checked: bool,
    ) -> None:
        super().__init__()

        self.patch_name = name
        self.patch_path = path

        self.setObjectName("patchCard")
        self.setMinimumHeight(150)
        self.setMaximumHeight(175)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 12)
        root.setSpacing(7)

        header = QHBoxLayout()
        header.setSpacing(8)

        self.checkbox = QCheckBox(name)
        self.checkbox.setChecked(checked)
        self.checkbox.setProperty("patchPath", str(path))
        self.checkbox.setProperty("description", description)

        self.status = QLabel()
        self.status.setObjectName("patchStatus")
        self.status.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        header.addWidget(self.checkbox, 1)
        header.addWidget(self.status)

        detail = QLabel(description)
        detail.setObjectName("mutedLabel")
        detail.setWordWrap(True)
        detail.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        path_label = QLabel(str(path))
        path_label.setObjectName("pathLabel")
        path_label.setWordWrap(False)
        path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        footer = QHBoxLayout()
        footer.setSpacing(8)

        self.btn_validate = QPushButton("VALIDATE")
        self.btn_validate.setObjectName("patchValidateButton")
        self.btn_validate.setMaximumWidth(100)

        self.selection_label = QLabel()
        self.selection_label.setObjectName("patchSelectionState")
        self.selection_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        footer.addWidget(self.btn_validate)
        footer.addStretch(1)
        footer.addWidget(self.selection_label)

        root.addLayout(header)
        root.addWidget(detail)
        root.addStretch(1)
        root.addWidget(path_label)
        root.addLayout(footer)

        self.checkbox.toggled.connect(self._state_changed)
        self.btn_validate.clicked.connect(
            self.validate_requested.emit
        )

        self.refresh_state()

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)

    def refresh_state(self) -> None:
        exists = self.patch_path.exists()

        self.status.setText(
            "READY" if exists else "MISSING"
        )
        self.status.setProperty(
            "ready",
            exists,
        )

        self.selection_label.setText(
            "ENABLED" if self.is_checked() else "NOT SELECTED"
        )
        self.selection_label.setProperty(
            "enabled",
            self.is_checked(),
        )

        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

        self.selection_label.style().unpolish(
            self.selection_label
        )
        self.selection_label.style().polish(
            self.selection_label
        )

    def _state_changed(self) -> None:
        self.refresh_state()
        self.toggled.emit()


class PatchesPage(QWidget):
    selection_changed = Signal()

    def __init__(self, patches_root: Path) -> None:
        super().__init__()

        self.patches_root = patches_root
        self.patches_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.state_file = (
            self.patches_root / "patch-selections.json"
        )

        self.cards: list[PatchCard] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        title = QLabel("PATCH LIBRARY")
        title.setObjectName("pageTitle")

        subtitle = QLabel("SELECT. VALIDATE. APPLY.")
        subtitle.setObjectName("pageSubtitle")

        root.addWidget(title)
        root.addWidget(subtitle)

        library = QFrame()
        library.setObjectName("glassPanel")

        library_layout = QVBoxLayout(library)
        library_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )
        library_layout.setSpacing(10)

        toolbar = QHBoxLayout()

        toolbar.addWidget(
            self._title("AVAILABLE PATCH SETS")
        )
        toolbar.addStretch(1)

        self.summary = QLabel()
        self.summary.setObjectName("patchLibrarySummary")
        self.summary.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )
        toolbar.addWidget(self.summary)

        library_layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setObjectName("patchScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        grid_widget = QWidget()
        grid_widget.setObjectName("patchGridWidget")

        self.grid = QGridLayout(grid_widget)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setAlignment(Qt.AlignTop)

        scroll.setWidget(grid_widget)
        library_layout.addWidget(scroll, 1)

        root.addWidget(library, 1)

        self.apply_razer = self._add_patch_card(
            "Razer HID Driver",
            "In-tree DFUSE Razer keyboard and mouse driver.",
            self.patches_root / "hid-razer",
            True,
        )
        self.apply_xbox = self._add_patch_card(
            "Xbox Controller Support",
            "Kernel controller options and future Xbox driver patches.",
            self.patches_root / "xbox",
            True,
        )
        self.cachyos_base = self._add_patch_card(
            "CachyOS Base Patch Set",
            "CachyOS performance and desktop-oriented kernel patches.",
            self.patches_root / "cachyos",
            False,
        )
        self.bore = self._add_patch_card(
            "BORE Scheduler",
            "Burst-Oriented Response Enhancer scheduler patch set.",
            self.patches_root / "cachyos-bore",
            False,
        )

        self._load_state()
        self._refresh()

    @staticmethod
    def _title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _add_patch_card(
        self,
        name: str,
        description: str,
        path: Path,
        checked: bool,
    ) -> QCheckBox:
        card = PatchCard(
            name,
            description,
            path,
            checked,
        )

        card.toggled.connect(
            self._selection_updated
        )
        card.validate_requested.connect(
            lambda current=card:
            self.validate_card(current)
        )

        index = len(self.cards)
        row = index // 2
        column = index % 2

        self.grid.addWidget(card, row, column)
        self.cards.append(card)

        return card.checkbox

    def checkboxes(self) -> list[QCheckBox]:
        return [
            card.checkbox
            for card in self.cards
        ]

    def enabled_names(self) -> list[str]:
        return [
            card.patch_name
            for card in self.cards
            if card.is_checked()
        ]

    def _selection_updated(self) -> None:
        self._refresh()
        self._save_state()
        self.selection_changed.emit()

    def _refresh(self) -> None:
        selected = self.enabled_names()

        for card in self.cards:
            card.refresh_state()

        if selected:
            self.summary.setText(
                f"{len(selected)} ENABLED"
            )
        else:
            self.summary.setText(
                "NO PATCHES ENABLED"
            )

    def validate_card(
        self,
        card: PatchCard,
    ) -> None:
        card.refresh_state()

        if card.patch_path.exists():
            card.status.setText("VALID")
        else:
            card.status.setText("MISSING")

        card.status.style().unpolish(card.status)
        card.status.style().polish(card.status)

    def validate(self) -> None:
        for card in self.cards:
            if card.is_checked():
                self.validate_card(card)

        self._refresh()

    def _save_state(self) -> None:
        data = {
            "enabled": {
                card.patch_name: card.is_checked()
                for card in self.cards
            },
        }

        self.state_file.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def _load_state(self) -> None:
        if not self.state_file.is_file():
            return

        try:
            data = json.loads(
                self.state_file.read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, ValueError):
            return

        enabled = data.get("enabled", {})

        for card in self.cards:
            if card.patch_name in enabled:
                card.set_checked(
                    bool(enabled[card.patch_name])
                )
