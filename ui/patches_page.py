from __future__ import annotations

import json
import subprocess
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class PatchCard(QFrame):
    toggled = Signal()
    validate_requested = Signal()
    update_requested = Signal()
    remove_requested = Signal()

    def __init__(
        self,
        name: str,
        description: str,
        path: Path,
        checked: bool,
        managed: bool = False,
        features: list[str] | None = None,
        sub_options: list[str] | None = None,
        full_width: bool = False,
        disabled_options: set[str] | None = None,
    ) -> None:
        super().__init__()

        self.patch_name = name
        self.patch_path = path
        self.managed = managed
        self.sub_checkboxes: dict[str, QCheckBox] = {}
        self.disabled_options = disabled_options or set()

        sub_option_columns = len(sub_options) if full_width and sub_options else 2
        sub_option_rows = (
            (len(sub_options) + sub_option_columns - 1) // sub_option_columns
            if sub_options
            else 0
        )
        extra_height = max(0, sub_option_rows - 1) * 30

        self.setObjectName("patchCard")
        self.setMinimumHeight(200 + extra_height)
        self.setMaximumHeight(230 + extra_height)
        self.setMinimumWidth(340)
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 12)
        root.setSpacing(7)

        header = QHBoxLayout()

        self.checkbox = QCheckBox(name)
        self.checkbox.setChecked(checked)

        self.status = QLabel()
        self.status.setObjectName("patchStatus")
        self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header.addWidget(self.checkbox, 1)
        header.addWidget(self.status)

        detail = QLabel(description)
        detail.setObjectName("mutedLabel")
        detail.setWordWrap(True)

        feature_label: QLabel | None = None
        if features:
            feature_label = QLabel("  \u2022  ".join(f"\u2713 {feature}" for feature in features))
            feature_label.setObjectName("patchFeatureList")
            feature_label.setWordWrap(True)

        sub_options_layout: QGridLayout | None = None
        if sub_options:
            sub_options_layout = QGridLayout()
            sub_options_layout.setHorizontalSpacing(16)
            sub_options_layout.setVerticalSpacing(6)

            for index, option_name in enumerate(sub_options):
                option_checkbox = QCheckBox(option_name)
                option_checkbox.setObjectName("patchSubOption")

                if option_name in self.disabled_options:
                    option_checkbox.setChecked(False)
                    option_checkbox.setEnabled(False)
                    option_checkbox.setToolTip("Not implemented yet - coming soon")
                else:
                    option_checkbox.setChecked(True)
                    option_checkbox.toggled.connect(self._state_changed)

                self.sub_checkboxes[option_name] = option_checkbox
                sub_options_layout.addWidget(
                    option_checkbox,
                    index // sub_option_columns,
                    index % sub_option_columns,
                )

            sub_options_layout.setColumnStretch(sub_option_columns, 1)

        path_label = QLabel(str(path))
        path_label.setObjectName("pathLabel")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        buttons = QHBoxLayout()

        self.btn_validate = QPushButton("VALIDATE")
        self.btn_validate.setObjectName("patchValidateButton")
        buttons.addWidget(self.btn_validate)

        self.btn_update: QPushButton | None = None
        self.btn_remove: QPushButton | None = None

        if managed:
            self.btn_update = QPushButton("UPDATE")
            self.btn_update.setObjectName("patchValidateButton")
            self.btn_remove = QPushButton("REMOVE FILES")
            self.btn_remove.setObjectName("patchValidateButton")

            buttons.addWidget(self.btn_update)
            buttons.addWidget(self.btn_remove)

        buttons.addStretch(1)

        self.selection_label = QLabel()
        self.selection_label.setObjectName("patchSelectionState")
        self.selection_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        buttons.addWidget(self.selection_label)

        root.addLayout(header)
        root.addWidget(detail)
        if feature_label is not None:
            root.addWidget(feature_label)
        if sub_options_layout is not None:
            root.addLayout(sub_options_layout)
        root.addStretch(1)
        root.addWidget(path_label)
        root.addLayout(buttons)

        self.checkbox.toggled.connect(self._state_changed)
        self.checkbox.toggled.connect(self._update_sub_option_state)
        self.btn_validate.clicked.connect(self.validate_requested.emit)

        if self.btn_update is not None:
            self.btn_update.clicked.connect(self.update_requested.emit)

        if self.btn_remove is not None:
            self.btn_remove.clicked.connect(self.remove_requested.emit)

        self._update_sub_option_state()
        self.refresh_state()

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)

    def _update_sub_option_state(self) -> None:
        for option_name, option_checkbox in self.sub_checkboxes.items():
            if option_name in self.disabled_options:
                continue

            option_checkbox.setEnabled(self.is_checked())

    def set_status(self, text: str, ready: bool = False) -> None:
        self.status.setText(text)
        self.status.setProperty("ready", ready)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def refresh_state(self) -> None:
        exists = self.patch_path.exists()

        self.set_status(
            "READY" if exists else "MISSING",
            ready=exists,
        )

        self.selection_label.setText(
            "ENABLED" if self.is_checked() else "NOT SELECTED"
        )
        self.selection_label.setProperty(
            "enabled",
            self.is_checked(),
        )
        self.selection_label.style().unpolish(self.selection_label)
        self.selection_label.style().polish(self.selection_label)

    def _state_changed(self) -> None:
        self.refresh_state()
        self.toggled.emit()


CARD_MIN_WIDTH = 420
MAX_GRID_COLUMNS = 2


class PatchesPage(QWidget):
    selection_changed = Signal()

    def __init__(self, patches_root: Path) -> None:
        super().__init__()

        self.patches_root = patches_root
        self.patches_root.mkdir(parents=True, exist_ok=True)

        self.state_file = self.patches_root / "patch-selections.json"
        self.cards: list[PatchCard] = []
        self._card_entries: list[tuple[PatchCard, bool]] = []
        self._grid_columns = MAX_GRID_COLUMNS

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
        library_layout.setContentsMargins(10, 10, 10, 10)
        library_layout.setSpacing(10)

        toolbar = QHBoxLayout()

        section_title = QLabel("AVAILABLE PATCH SETS")
        section_title.setObjectName("sectionTitle")
        toolbar.addWidget(section_title)
        toolbar.addStretch(1)

        self.summary = QLabel()
        self.summary.setObjectName("patchLibrarySummary")
        toolbar.addWidget(self.summary)

        library_layout.addLayout(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("patchScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        grid_widget = QWidget()
        grid_widget.setObjectName("patchGridWidget")

        self.grid = QGridLayout(grid_widget)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.grid.setAlignment(Qt.AlignTop)
        self._apply_column_stretch(self._grid_columns)

        self.scroll.setWidget(grid_widget)
        library_layout.addWidget(self.scroll, 1)

        root.addWidget(library, 1)

        self.razer_card = self._add_patch_card(
            name="Razer HID Driver",
            description="In-tree DFUSE Razer keyboard and mouse driver.",
            path=self.patches_root / "hid-razer",
            checked=True,
            managed=True,
        )
        self.apply_razer = self.razer_card.checkbox

        self.xbox_card = self._add_patch_card(
            name="Xbox Controller Support",
            description="Native Xbox controller drivers for Linux.",
            path=self.patches_root / "xbox",
            checked=True,
            managed=True,
            sub_options=["XPAD (USB)", "XPADNEO (Bluetooth)"],
        )
        self.apply_xbox = self.xbox_card.checkbox
        self.apply_xpad = self.xbox_card.sub_checkboxes["XPAD (USB)"]
        self.apply_xpadneo = self.xbox_card.sub_checkboxes["XPADNEO (Bluetooth)"]
        self.xbox_card.update_requested.connect(self._update_xbox)
        self.xbox_card.validate_requested.connect(self._validate_xbox)
        self.xbox_card.remove_requested.connect(self._remove_xbox_files)

        self.dualsense_card = self._add_patch_card(
            name="DualSense Controller Support",
            description=(
                "Native Sony DualSense & DualSense Edge support using the "
                "Linux hid-playstation driver."
            ),
            path=self.patches_root / "dualsense",
            checked=True,
            features=[
                "Base Driver",
                "Bluetooth",
                "Gyroscope",
                "Touchpad",
                "LED Control",
                "Haptics",
                "Adaptive Triggers",
            ],
        )
        self.apply_dualsense = self.dualsense_card.checkbox

        self.cachyos_card = self._add_patch_card(
            name="CachyOS Patch Set",
            description=(
                "Curated patches from CachyOS "
                "(github.com/CachyOS/linux-cachyos): performance tuning, "
                "schedulers, sync primitives, filesystem, and networking."
            ),
            path=self.patches_root / "cachyos-bore",
            checked=False,
            managed=True,
            sub_options=[
                "Cachy Sauce",
                "BORE Scheduler",
                "scx_lavd / scx_rustland",
                "Deckify Handheld",
                "NTSync / Fastsync / Winesync",
                "EXT4 / Btrfs / XFS",
                "Networking Low-Latency",
            ],
            full_width=True,
            disabled_options={
                "Cachy Sauce",
                "scx_lavd / scx_rustland",
                "Deckify Handheld",
                "NTSync / Fastsync / Winesync",
                "EXT4 / Btrfs / XFS",
                "Networking Low-Latency",
            },
        )
        self.apply_bore_checkbox = self.cachyos_card.sub_checkboxes["BORE Scheduler"]
        self.cachyos_card.update_requested.connect(self._update_bore)
        self.cachyos_card.validate_requested.connect(self._validate_bore)
        self.cachyos_card.remove_requested.connect(self._remove_bore_files)

        self.razer_card.update_requested.connect(self._update_razer)
        self.razer_card.validate_requested.connect(self._validate_razer)
        self.razer_card.remove_requested.connect(self._remove_razer_files)

        self._load_state()
        self._refresh()

    def _add_patch_card(
        self,
        name: str,
        description: str,
        path: Path,
        checked: bool,
        managed: bool = False,
        features: list[str] | None = None,
        sub_options: list[str] | None = None,
        full_width: bool = False,
        disabled_options: set[str] | None = None,
    ) -> PatchCard:
        card = PatchCard(
            name=name,
            description=description,
            path=path,
            checked=checked,
            managed=managed,
            features=features,
            sub_options=sub_options,
            full_width=full_width,
            disabled_options=disabled_options,
        )

        card.toggled.connect(self._selection_updated)

        if not managed:
            card.validate_requested.connect(
                lambda current=card: self._validate_basic_card(current)
            )

        self.cards.append(card)
        self._card_entries.append((card, full_width))
        self._reflow_grid()

        return card

    def _apply_column_stretch(self, columns: int) -> None:
        for column in range(MAX_GRID_COLUMNS):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)

    def _reflow_grid(self, columns: int | None = None) -> None:
        if columns is None:
            columns = self._grid_columns
        else:
            self._grid_columns = columns

        while self.grid.count():
            self.grid.takeAt(0)

        row = 0
        col = 0
        for card, full_width in self._card_entries:
            if full_width or columns == 1:
                if col != 0:
                    row += 1
                    col = 0
                self.grid.addWidget(card, row, 0, 1, columns)
                row += 1
                col = 0
            else:
                self.grid.addWidget(card, row, col)
                col += 1
                if col >= columns:
                    col = 0
                    row += 1

        self._apply_column_stretch(columns)

    def _columns_for_width(self, width: int) -> int:
        if width <= 0:
            return self._grid_columns
        columns = max(1, width // CARD_MIN_WIDTH)
        return min(columns, MAX_GRID_COLUMNS)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._update_columns)

    def _update_columns(self) -> None:
        columns = self._columns_for_width(self.scroll.viewport().width())
        if columns != self._grid_columns:
            self._reflow_grid(columns)

    def checkboxes(self) -> list[QCheckBox]:
        return [card.checkbox for card in self.cards]

    def enabled_names(self) -> list[str]:
        return [
            card.patch_name
            for card in self.cards
            if card.is_checked()
        ]

    def enabled_patch_ids(self) -> list[str]:
        mapping = {
            "Razer HID Driver": "hid-razer",
            "Xbox Controller Support": "xbox",
            "DualSense Controller Support": "dualsense",
        }

        ids = [
            mapping[card.patch_name]
            for card in self.cards
            if card.is_checked() and card.patch_name in mapping
        ]

        if self.cachyos_card.is_checked():
            sub_mapping = {
                "Cachy Sauce": "cachyos",
                "BORE Scheduler": "cachyos-bore",
                "scx_lavd / scx_rustland": "cachyos-scx",
                "Deckify Handheld": "cachyos-deckify",
                "NTSync / Fastsync / Winesync": "cachyos-ntsync",
                "EXT4 / Btrfs / XFS": "cachyos-fs",
                "Networking Low-Latency": "cachyos-net",
            }

            for option_name, patch_id in sub_mapping.items():
                checkbox = self.cachyos_card.sub_checkboxes.get(option_name)

                if checkbox is not None and checkbox.isChecked():
                    ids.append(patch_id)

        return ids

    def validate(self) -> None:
        for card in self.cards:
            if not card.is_checked():
                continue

            if card is self.razer_card:
                self._validate_razer(show_message=False)
            elif card is self.xbox_card:
                self._validate_xbox(show_message=False)
            else:
                self._validate_basic_card(card, show_message=False)

        self._refresh()

    def _selection_updated(self) -> None:
        self._save_state()
        self._refresh()
        self.selection_changed.emit()

    def _refresh(self) -> None:
        selected = self.enabled_names()

        for card in self.cards:
            if card is not self.razer_card:
                card.refresh_state()

        self._refresh_razer_status()

        self.summary.setText(
            f"{len(selected)} ENABLED"
            if selected
            else "NO PATCHES ENABLED"
        )

    def _validate_basic_card(
        self,
        card: PatchCard,
        show_message: bool = True,
    ) -> bool:
        exists = card.patch_path.exists()

        card.set_status(
            "READY" if exists else "MISSING",
            ready=exists,
        )

        if show_message:
            if exists:
                QMessageBox.information(
                    self,
                    "Patch Validation",
                    f"{card.patch_name} is ready.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Patch Validation",
                    f"Patch path is missing:\n{card.patch_path}",
                )

        return exists

    def _razer_paths(self) -> tuple[Path, Path, Path]:
        patch_dir = self.patches_root / "hid-razer"

        return (
            patch_dir / "metadata.json",
            patch_dir / "driver",
            patch_dir / "sync_upstream.py",
        )

    def _load_razer_metadata(self) -> dict:
        metadata_file, _, _ = self._razer_paths()

        if not metadata_file.is_file():
            raise FileNotFoundError(
                f"Razer metadata is missing:\n{metadata_file}"
            )

        return json.loads(
            metadata_file.read_text(encoding="utf-8")
        )

    def _razer_validation(self) -> tuple[bool, list[str]]:
        try:
            metadata = self._load_razer_metadata()
        except (OSError, ValueError, TypeError) as error:
            return False, [str(error)]

        _, driver_dir, sync_script = self._razer_paths()
        missing: list[str] = []

        for filename in metadata.get("preserve_files", []):
            if not (driver_dir / filename).is_file():
                missing.append(f"preserved: {filename}")

        for filename in metadata.get("managed_files", []):
            if not (driver_dir / filename).is_file():
                missing.append(f"managed: {filename}")

        if not sync_script.is_file():
            missing.append("sync_upstream.py")

        return not missing, missing

    def _xbox_paths(self) -> tuple[Path, Path, Path]:
        patch_dir = self.patches_root / "xbox"

        return (
            patch_dir / "metadata.json",
            patch_dir / "driver",
            patch_dir / "sync_upstream.py",
        )

    def _load_xbox_metadata(self) -> dict:
        metadata_file, _, _ = self._xbox_paths()

        if not metadata_file.is_file():
            raise FileNotFoundError(
                f"Xbox metadata is missing:\n{metadata_file}"
            )

        return json.loads(
            metadata_file.read_text(encoding="utf-8")
        )

    def _xbox_validation(self) -> tuple[bool, list[str]]:
        try:
            metadata = self._load_xbox_metadata()
        except (OSError, ValueError, TypeError) as error:
            return False, [str(error)]

        _, driver_dir, sync_script = self._xbox_paths()
        missing: list[str] = []

        for filename in metadata.get("preserve_files", []):
            if not (driver_dir / filename).is_file():
                missing.append(f"preserved: {filename}")

        for filename in metadata.get("managed_files", []):
            if not (driver_dir / filename).is_file():
                missing.append(f"managed: {filename}")

        if not sync_script.is_file():
            missing.append("sync_upstream.py")

        return not missing, missing

    def _refresh_xbox_status(self) -> None:
        valid, _missing = self._xbox_validation()

        self.xbox_card.set_status(
            "READY" if valid else "MISSING",
            ready=valid,
        )

        self.xbox_card.selection_label.setText(
            "ENABLED"
            if self.xbox_card.is_checked()
            else "NOT SELECTED"
        )
        self.xbox_card.selection_label.setProperty(
            "enabled",
            self.xbox_card.is_checked(),
        )
        self.xbox_card.selection_label.style().unpolish(
            self.xbox_card.selection_label
        )
        self.xbox_card.selection_label.style().polish(
            self.xbox_card.selection_label
        )

    def _update_xbox(self) -> None:
        _, _, sync_script = self._xbox_paths()

        if not sync_script.is_file():
            QMessageBox.critical(
                self,
                "Xbox Update",
                f"Sync script is missing:\n{sync_script}",
            )
            return

        if self.xbox_card.btn_update is not None:
            self.xbox_card.btn_update.setEnabled(False)

        self.xbox_card.set_status("UPDATING", ready=False)

        try:
            result = subprocess.run(
                ["python3", str(sync_script)],
                cwd=str(sync_script.parent),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Xbox Update Failed",
                str(error),
            )
            result = None
        finally:
            if self.xbox_card.btn_update is not None:
                self.xbox_card.btn_update.setEnabled(True)

        if result is None:
            self._refresh_xbox_status()
            return

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()

            QMessageBox.critical(
                self,
                "Xbox Update Failed",
                details or "The updater returned an error.",
            )
        else:
            QMessageBox.information(
                self,
                "Xbox Updated",
                result.stdout.strip()
                or "Xbox controller driver files updated.",
            )

        self._refresh_xbox_status()

    def _validate_xbox(
        self,
        show_message: bool = True,
    ) -> bool:
        valid, missing = self._xbox_validation()

        self._refresh_xbox_status()

        if show_message:
            if valid:
                metadata = self._load_xbox_metadata()

                QMessageBox.information(
                    self,
                    "Xbox Validation",
                    (
                        "Xbox controller support is ready.\n\n"
                        f"Managed files: "
                        f"{len(metadata.get('managed_files', []))}\n"
                        f"Preserved integration files: "
                        f"{len(metadata.get('preserve_files', []))}"
                    ),
                )
            else:
                QMessageBox.warning(
                    self,
                    "Xbox Validation",
                    "Missing files:\n\n"
                    + "\n".join(f"• {item}" for item in missing),
                )

        return valid

    def _remove_xbox_files(self) -> None:
        try:
            metadata = self._load_xbox_metadata()
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Remove Xbox Files",
                str(error),
            )
            return

        answer = QMessageBox.question(
            self,
            "Remove Downloaded Xbox Files",
            (
                "Remove the downloaded XPAD and XPADNEO files?\n\n"
                "Kconfig and Makefile integration files will be preserved."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        _, driver_dir, _ = self._xbox_paths()
        removed = 0

        for source in metadata.get("sources", []):
            local_dir = source.get("local_dir")
            managed_paths = source.get("managed_files", [])

            if not local_dir:
                continue

            source_dir = driver_dir / local_dir

            for path_name in managed_paths:
                path = source_dir / path_name

                if path.is_dir():
                    shutil.rmtree(path)
                    removed += 1
                elif path.is_file():
                    path.unlink()
                    removed += 1

        self._refresh_xbox_status()

        QMessageBox.information(
            self,
            "Xbox Files Removed",
            (
                f"Removed {removed} downloaded items.\n\n"
                "Oppenheimer integration files were preserved."
            ),
        )

    def _refresh_razer_status(self) -> None:
        valid, _missing = self._razer_validation()

        self.razer_card.set_status(
            "READY" if valid else "MISSING",
            ready=valid,
        )

        self.razer_card.selection_label.setText(
            "ENABLED"
            if self.razer_card.is_checked()
            else "NOT SELECTED"
        )
        self.razer_card.selection_label.setProperty(
            "enabled",
            self.razer_card.is_checked(),
        )
        self.razer_card.selection_label.style().unpolish(
            self.razer_card.selection_label
        )
        self.razer_card.selection_label.style().polish(
            self.razer_card.selection_label
        )

    def _update_razer(self) -> None:
        _, _, sync_script = self._razer_paths()

        if not sync_script.is_file():
            QMessageBox.critical(
                self,
                "Razer Update",
                f"Sync script is missing:\n{sync_script}",
            )
            return

        if self.razer_card.btn_update is not None:
            self.razer_card.btn_update.setEnabled(False)

        self.razer_card.set_status("UPDATING", ready=False)

        try:
            result = subprocess.run(
                ["python3", str(sync_script)],
                cwd=str(sync_script.parent),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "Razer Update Failed",
                str(error),
            )
            result = None
        finally:
            if self.razer_card.btn_update is not None:
                self.razer_card.btn_update.setEnabled(True)

        if result is None:
            self._refresh_razer_status()
            return

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()

            QMessageBox.critical(
                self,
                "Razer Update Failed",
                details or "The updater returned an error.",
            )
        else:
            QMessageBox.information(
                self,
                "Razer Updated",
                result.stdout.strip() or "Razer driver files updated.",
            )

        self._refresh_razer_status()

    def _validate_razer(
        self,
        show_message: bool = True,
    ) -> bool:
        valid, missing = self._razer_validation()

        self._refresh_razer_status()

        if show_message:
            if valid:
                metadata = self._load_razer_metadata()

                QMessageBox.information(
                    self,
                    "Razer Validation",
                    (
                        "DFUSE Razer HID is ready.\n\n"
                        f"Managed files: "
                        f"{len(metadata.get('managed_files', []))}\n"
                        f"Preserved DFUSE files: "
                        f"{len(metadata.get('preserve_files', []))}"
                    ),
                )
            else:
                QMessageBox.warning(
                    self,
                    "Razer Validation",
                    "Missing files:\n\n"
                    + "\n".join(f"• {item}" for item in missing),
                )

        return valid

    def _remove_razer_files(self) -> None:
        try:
            metadata = self._load_razer_metadata()
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Remove Razer Files",
                str(error),
            )
            return

        answer = QMessageBox.question(
            self,
            "Remove Downloaded Razer Files",
            (
                "Remove the downloaded OpenRazer driver files?\n\n"
                "Kconfig, Makefile, and razer-dfuse-main.c "
                "will be preserved."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        _, driver_dir, _ = self._razer_paths()
        removed = 0

        for filename in metadata.get("managed_files", []):
            path = driver_dir / filename

            if path.is_file():
                path.unlink()
                removed += 1

        self._refresh_razer_status()

        QMessageBox.information(
            self,
            "Razer Files Removed",
            (
                f"Removed {removed} managed files.\n\n"
                "DFUSE integration files were preserved."
            ),
        )

    def apply_bore(self) -> bool:
        return (
            self.cachyos_card.is_checked()
            and self.apply_bore_checkbox.isChecked()
        )

    def _bore_paths(self) -> tuple[Path, Path, Path, Path]:
        patch_dir = self.patches_root / "cachyos-bore"

        return (
            patch_dir / "metadata.json",
            patch_dir / "upstream",
            patch_dir / "sync_upstream.py",
            patch_dir / "apply.py",
        )

    def _load_bore_metadata(self) -> dict:
        metadata_file, _, _, _ = self._bore_paths()

        if not metadata_file.is_file():
            raise FileNotFoundError(
                f"BORE metadata is missing:\n{metadata_file}"
            )

        return json.loads(
            metadata_file.read_text(encoding="utf-8")
        )

    def _bore_validation(self) -> tuple[bool, list[str]]:
        try:
            self._load_bore_metadata()
        except (OSError, ValueError, TypeError) as error:
            return False, [str(error)]

        _, upstream_dir, sync_script, apply_script = self._bore_paths()
        missing: list[str] = []

        if not sync_script.is_file():
            missing.append("sync_upstream.py")

        if not apply_script.is_file():
            missing.append("apply.py")

        if not upstream_dir.is_dir() or not any(upstream_dir.rglob("*.patch")):
            missing.append("upstream/stable/*.patch (run Update to sync)")

        return not missing, missing

    def _refresh_bore_status(self) -> None:
        valid, _missing = self._bore_validation()

        self.cachyos_card.set_status(
            "READY" if valid else "MISSING",
            ready=valid,
        )

        self.cachyos_card.selection_label.setText(
            "ENABLED" if self.apply_bore() else "NOT SELECTED"
        )
        self.cachyos_card.selection_label.setProperty(
            "enabled",
            self.apply_bore(),
        )
        self.cachyos_card.selection_label.style().unpolish(
            self.cachyos_card.selection_label
        )
        self.cachyos_card.selection_label.style().polish(
            self.cachyos_card.selection_label
        )

    def _update_bore(self) -> None:
        _, _, sync_script, _ = self._bore_paths()

        if not sync_script.is_file():
            QMessageBox.critical(
                self,
                "BORE Update",
                f"Sync script is missing:\n{sync_script}",
            )
            return

        if self.cachyos_card.btn_update is not None:
            self.cachyos_card.btn_update.setEnabled(False)

        self.cachyos_card.set_status("UPDATING", ready=False)

        try:
            result = subprocess.run(
                ["python3", str(sync_script)],
                cwd=str(sync_script.parent),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                "BORE Update Failed",
                str(error),
            )
            result = None
        finally:
            if self.cachyos_card.btn_update is not None:
                self.cachyos_card.btn_update.setEnabled(True)

        if result is None:
            self._refresh_bore_status()
            return

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()

            QMessageBox.critical(
                self,
                "BORE Update Failed",
                details or "The updater returned an error.",
            )
        else:
            QMessageBox.information(
                self,
                "BORE Updated",
                result.stdout.strip()
                or "BORE scheduler patch files updated.",
            )

        self._refresh_bore_status()

    def _validate_bore(
        self,
        show_message: bool = True,
    ) -> bool:
        valid, missing = self._bore_validation()

        self._refresh_bore_status()

        if show_message:
            if valid:
                _, upstream_dir, _, _ = self._bore_paths()
                patch_count = len(list(upstream_dir.rglob("*.patch")))

                QMessageBox.information(
                    self,
                    "BORE Validation",
                    (
                        "BORE scheduler patch set is ready.\n\n"
                        f"Vendored patch files: {patch_count}"
                    ),
                )
            else:
                QMessageBox.warning(
                    self,
                    "BORE Validation",
                    "Missing files:\n\n"
                    + "\n".join(f"• {item}" for item in missing),
                )

        return valid

    def _remove_bore_files(self) -> None:
        _, upstream_dir, _, _ = self._bore_paths()

        answer = QMessageBox.question(
            self,
            "Remove Downloaded BORE Files",
            (
                "Remove the downloaded BORE scheduler patch files?\n\n"
                f"{upstream_dir}"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        removed = upstream_dir.is_dir()

        if removed:
            shutil.rmtree(upstream_dir)

        self._refresh_bore_status()

        QMessageBox.information(
            self,
            "BORE Files Removed",
            (
                "Removed vendored BORE patch files."
                if removed
                else "No vendored BORE patch files were present."
            ),
        )

    def _save_state(self) -> None:
        data = {
            "enabled": {
                card.patch_name: card.is_checked()
                for card in self.cards
            },
            "sub_options": {
                card.patch_name: {
                    option_name: option_checkbox.isChecked()
                    for option_name, option_checkbox in card.sub_checkboxes.items()
                }
                for card in self.cards
                if card.sub_checkboxes
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
                self.state_file.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return

        enabled = data.get("enabled", {})
        sub_options = data.get("sub_options", {})

        for card in self.cards:
            if card.patch_name in enabled:
                card.set_checked(
                    bool(enabled[card.patch_name])
                )

            saved_options = sub_options.get(card.patch_name, {})

            for option_name, option_checkbox in card.sub_checkboxes.items():
                if option_name in card.disabled_options:
                    continue

                if option_name in saved_options:
                    option_checkbox.setChecked(bool(saved_options[option_name]))
