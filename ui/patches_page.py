from __future__ import annotations

import json
import subprocess
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, Signal
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
    ) -> None:
        super().__init__()

        self.patch_name = name
        self.patch_path = path
        self.managed = managed

        self.setObjectName("patchCard")
        self.setMinimumHeight(160 if not features else 200)
        self.setMaximumHeight(190 if not features else 230)
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
        root.addStretch(1)
        root.addWidget(path_label)
        root.addLayout(buttons)

        self.checkbox.toggled.connect(self._state_changed)
        self.btn_validate.clicked.connect(self.validate_requested.emit)

        if self.btn_update is not None:
            self.btn_update.clicked.connect(self.update_requested.emit)

        if self.btn_remove is not None:
            self.btn_remove.clicked.connect(self.remove_requested.emit)

        self.refresh_state()

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, checked: bool) -> None:
        self.checkbox.setChecked(checked)

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


class PatchesPage(QWidget):
    selection_changed = Signal()

    def __init__(self, patches_root: Path) -> None:
        super().__init__()

        self.patches_root = patches_root
        self.patches_root.mkdir(parents=True, exist_ok=True)

        self.state_file = self.patches_root / "patch-selections.json"
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

        scroll = QScrollArea()
        scroll.setObjectName("patchScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
            description=(
                "Native Xbox controller drivers for Linux. "
                "Includes XPAD for USB and XPADNEO for Bluetooth."
            ),
            path=self.patches_root / "xbox",
            checked=True,
            managed=True,
        )
        self.apply_xbox = self.xbox_card.checkbox
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
            name="CachyOS Base Patch Set",
            description="CachyOS performance and desktop-oriented kernel patches.",
            path=self.patches_root / "cachyos",
            checked=False,
        )

        self.bore_card = self._add_patch_card(
            name="BORE Scheduler",
            description="Burst-Oriented Response Enhancer scheduler patch set.",
            path=self.patches_root / "cachyos-bore",
            checked=False,
        )

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
    ) -> PatchCard:
        card = PatchCard(
            name=name,
            description=description,
            path=path,
            checked=checked,
            managed=managed,
            features=features,
        )

        card.toggled.connect(self._selection_updated)

        if not managed:
            card.validate_requested.connect(
                lambda current=card: self._validate_basic_card(current)
            )

        index = len(self.cards)
        row = index // 2
        column = index % 2

        self.grid.addWidget(card, row, column)
        self.cards.append(card)

        return card

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
            "CachyOS Base Patch Set": "cachyos",
            "BORE Scheduler": "cachyos-bore",
        }

        return [
            mapping[card.patch_name]
            for card in self.cards
            if card.is_checked() and card.patch_name in mapping
        ]

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
                self.state_file.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return

        enabled = data.get("enabled", {})

        for card in self.cards:
            if card.patch_name in enabled:
                card.set_checked(
                    bool(enabled[card.patch_name])
                )
