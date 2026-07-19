from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


CPU_THREADS = os.cpu_count() or 2


class TweaksPage(QWidget):
    apply_requested = Signal(dict, bool)

    PROFILES = {
        "1. BALANCED": {
            "governor": "schedutil",
            "turbo": "ENABLED",
            "energy": "balance_perf.",
            "swappiness": 10,
            "zram": "ENABLED",
            "compression": "zstd",
            "scheduler": "mq-deadline",
            "read_ahead": "256 KB",
        },
        "2. PERFORMANCE": {
            "governor": "performance",
            "turbo": "ENABLED",
            "energy": "performance",
            "swappiness": 10,
            "zram": "ENABLED",
            "compression": "lz4",
            "scheduler": "none",
            "read_ahead": "512 KB",
        },
        "3. GAMING": {
            "governor": "performance",
            "turbo": "ENABLED",
            "energy": "performance",
            "swappiness": 10,
            "zram": "ENABLED",
            "compression": "zstd",
            "scheduler": "kyber",
            "read_ahead": "1024 KB",
        },
        "4. POWER SAVER": {
            "governor": "powersave",
            "turbo": "DISABLED",
            "energy": "power",
            "swappiness": 60,
            "zram": "ENABLED",
            "compression": "zstd",
            "scheduler": "mq-deadline",
            "read_ahead": "128 KB",
        },
    }

    def __init__(self) -> None:
        super().__init__()

        self.current_profile = "CUSTOM"
        self.saved_state: dict[str, any] = {}
        self.profile_buttons: dict[str, QPushButton] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()

        title = QLabel("TWEAKS")
        title.setObjectName("pageTitle")

        subtitle = QLabel("SYSTEM PERFORMANCE. CONTROL. OPTIMIZE.")
        subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        self.quick_jobs = QLabel(f"CPU  {CPU_THREADS} threads")
        self.quick_jobs.setObjectName("headerMetric")

        self.quick_status = QLabel("STATUS  ACTIVE")
        self.quick_status.setObjectName("headerMetric")

        header.addWidget(self.quick_jobs)
        header.addWidget(self.quick_status)
        root.addLayout(header)

        # Main Content Layout
        content = QHBoxLayout()
        content.setSpacing(16)
        root.addLayout(content, 1)

        main_column = QVBoxLayout()
        main_column.setSpacing(12)
        content.addLayout(main_column, 3)

        # --- Left Column: Configuration Cards ---
        # 1. CPU CONFIGURATION
        cpu_card, cpu_layout = self._create_card("CPU CONFIGURATION")
        cpu_grid = QGridLayout()
        cpu_grid.setHorizontalSpacing(16)
        cpu_grid.setVerticalSpacing(10)

        self.lbl_cpu_driver_val = QLabel(self._detect_cpu_driver())
        self.lbl_cpu_driver_val.setObjectName("mutedLabel")

        self.combo_governor = QComboBox()
        self.combo_governor.addItems(["schedutil", "performance", "powersave", "ondemand", "conservative"])

        self.combo_turbo = QComboBox()
        self.combo_turbo.addItems(["ENABLED", "DISABLED"])

        self.combo_energy = QComboBox()
        self.combo_energy.addItems(["balance_perf.", "performance", "balance_power", "power"])

        cpu_grid.addWidget(QLabel("Driver"), 0, 0)
        cpu_grid.addWidget(self.lbl_cpu_driver_val, 0, 1)
        cpu_grid.addWidget(QLabel("Governor"), 1, 0)
        cpu_grid.addWidget(self.combo_governor, 1, 1)
        cpu_grid.addWidget(QLabel("Turbo Boost"), 2, 0)
        cpu_grid.addWidget(self.combo_turbo, 2, 1)
        cpu_grid.addWidget(QLabel("Energy Pref."), 3, 0)
        cpu_grid.addWidget(self.combo_energy, 3, 1)
        cpu_layout.addLayout(cpu_grid)
        main_column.addWidget(cpu_card)

        # 2. MEMORY CONFIGURATION
        mem_card, mem_layout = self._create_card("MEMORY CONFIGURATION")
        mem_grid = QGridLayout()
        mem_grid.setHorizontalSpacing(16)
        mem_grid.setVerticalSpacing(10)

        self.spin_swappiness = QSpinBox()
        self.spin_swappiness.setRange(0, 100)
        self.spin_swappiness.setValue(10)

        self.combo_zram = QComboBox()
        self.combo_zram.addItems(["ENABLED", "DISABLED"])

        self.combo_compression = QComboBox()
        self.combo_compression.addItems(["zstd", "lz4", "lzo", "lz4hc"])

        mem_grid.addWidget(QLabel("Swappiness"), 0, 0)
        mem_grid.addWidget(self.spin_swappiness, 0, 1)
        mem_grid.addWidget(QLabel("ZRAM"), 1, 0)
        mem_grid.addWidget(self.combo_zram, 1, 1)
        mem_grid.addWidget(QLabel("Compression"), 2, 0)
        mem_grid.addWidget(self.combo_compression, 2, 1)
        mem_layout.addLayout(mem_grid)
        main_column.addWidget(mem_card)

        # 3. STORAGE CONFIGURATION
        storage_card, storage_layout = self._create_card("STORAGE CONFIGURATION")
        storage_grid = QGridLayout()
        storage_grid.setHorizontalSpacing(16)
        storage_grid.setVerticalSpacing(10)

        self.lbl_storage_dev_val = QLabel(self._detect_storage_device())
        self.lbl_storage_dev_val.setObjectName("mutedLabel")

        self.combo_scheduler = QComboBox()
        self.combo_scheduler.addItems(["mq-deadline", "none", "kyber", "bfq"])

        self.combo_read_ahead = QComboBox()
        self.combo_read_ahead.addItems(["256 KB", "128 KB", "512 KB", "1024 KB", "2048 KB"])

        storage_grid.addWidget(QLabel("Device"), 0, 0)
        storage_grid.addWidget(self.lbl_storage_dev_val, 0, 1)
        storage_grid.addWidget(QLabel("Scheduler"), 1, 0)
        storage_grid.addWidget(self.combo_scheduler, 1, 1)
        storage_grid.addWidget(QLabel("Read Ahead"), 2, 0)
        storage_grid.addWidget(self.combo_read_ahead, 2, 1)
        storage_layout.addLayout(storage_grid)
        main_column.addWidget(storage_card)
        main_column.addStretch(1)

        # --- Right Column: Profiles, Status & Actions ---
        side_column = QVBoxLayout()
        side_column.setSpacing(12)
        content.addLayout(side_column, 2)

        # 1. TWEAK PROFILES
        prof_card, prof_layout = self._create_card("TWEAK PROFILES")
        for prof_name in [
            "1. BALANCED",
            "2. PERFORMANCE",
            "3. GAMING",
            "4. POWER SAVER",
            "5. CUSTOM",
        ]:
            btn = QPushButton(prof_name)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=prof_name: self._on_profile_clicked(name))
            self.profile_buttons[prof_name] = btn
            prof_layout.addWidget(btn)
        side_column.addWidget(prof_card)

        # 2. TWEAK STATUS
        status_card, status_layout = self._create_card("TWEAK STATUS")
        self.lbl_profile_status = QLabel("PROFILE: CUSTOM")
        self.lbl_profile_status.setObjectName("stepName")
        self.lbl_pending_changes = QLabel("Pending changes: 0")
        self.lbl_pending_changes.setObjectName("mutedLabel")
        status_layout.addWidget(self.lbl_profile_status)
        status_layout.addWidget(self.lbl_pending_changes)
        side_column.addWidget(status_card)

        # 3. ACTIONS
        actions_card, actions_layout = self._create_card("ACTIONS")
        self.btn_apply_session = QPushButton("APPLY FOR SESSION")
        self.btn_apply_session.setObjectName("primaryButton")
        self.btn_apply_session.clicked.connect(lambda: self._apply_changes(permanent=False))

        self.btn_apply_perm = QPushButton("APPLY PERMANENTLY")
        self.btn_apply_perm.setObjectName("primaryButton")
        self.btn_apply_perm.clicked.connect(lambda: self._apply_changes(permanent=True))

        self.btn_restore = QPushButton("RESTORE PREVIOUS")
        self.btn_restore.clicked.connect(self._restore_previous)

        self.btn_reset = QPushButton("RESET DEFAULTS")
        self.btn_reset.clicked.connect(self._reset_defaults)

        actions_layout.addWidget(self.btn_apply_session)
        actions_layout.addWidget(self.btn_apply_perm)
        actions_layout.addWidget(self.btn_restore)
        actions_layout.addWidget(self.btn_reset)
        side_column.addWidget(actions_card)
        side_column.addStretch(1)

        # Connect change listeners
        self.combo_governor.currentTextChanged.connect(self._on_setting_changed)
        self.combo_turbo.currentTextChanged.connect(self._on_setting_changed)
        self.combo_energy.currentTextChanged.connect(self._on_setting_changed)
        self.spin_swappiness.valueChanged.connect(self._on_setting_changed)
        self.combo_zram.currentTextChanged.connect(self._on_setting_changed)
        self.combo_compression.currentTextChanged.connect(self._on_setting_changed)
        self.combo_scheduler.currentTextChanged.connect(self._on_setting_changed)
        self.combo_read_ahead.currentTextChanged.connect(self._on_setting_changed)

        # Initialize defaults and load state
        self._load_from_profile_json()
        self._save_checkpoint_state()
        self._on_profile_clicked("1. BALANCED", initial=True)

    @staticmethod
    def _section_title(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _create_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("glassPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self._section_title(title))
        return card, layout

    def _detect_cpu_driver(self) -> str:
        driver_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
        if driver_path.exists():
            try:
                return driver_path.read_text().strip()
            except Exception:
                pass
        return "intel_cpufreq"

    def _detect_storage_device(self) -> str:
        if Path("/dev/nvme0n1").exists():
            return "/dev/nvme0n1"
        return "/dev/sda"

    def _get_current_state(self) -> dict[str, any]:
        return {
            "governor": self.combo_governor.currentText(),
            "turbo": self.combo_turbo.currentText(),
            "energy": self.combo_energy.currentText(),
            "swappiness": self.spin_swappiness.value(),
            "zram": self.combo_zram.currentText(),
            "compression": self.combo_compression.currentText(),
            "scheduler": self.combo_scheduler.currentText(),
            "read_ahead": self.combo_read_ahead.currentText(),
            "device": self.lbl_storage_dev_val.text(),
        }

    def _set_state(self, state: dict[str, any]) -> None:
        self.combo_governor.setCurrentText(str(state.get("governor", "schedutil")))
        self.combo_turbo.setCurrentText(str(state.get("turbo", "ENABLED")))
        self.combo_energy.setCurrentText(str(state.get("energy", "balance_perf.")))
        self.spin_swappiness.setValue(int(state.get("swappiness", 10)))
        self.combo_zram.setCurrentText(str(state.get("zram", "ENABLED")))
        self.combo_compression.setCurrentText(str(state.get("compression", "zstd")))
        self.combo_scheduler.setCurrentText(str(state.get("scheduler", "mq-deadline")))
        self.combo_read_ahead.setCurrentText(str(state.get("read_ahead", "256 KB")))

    def _save_checkpoint_state(self) -> None:
        self.saved_state = self._get_current_state()
        self._update_pending_count()

    def _update_pending_count(self) -> None:
        curr = self._get_current_state()
        pending = sum(1 for k, v in curr.items() if self.saved_state.get(k) != v)
        self.lbl_pending_changes.setText(f"Pending changes: {pending}")

    def _on_setting_changed(self) -> None:
        # Check if current state matches any predefined profile (device is
        # hardware-specific, not part of a profile, so it's excluded).
        curr = self._get_current_state()
        profile_fields = {key: value for key, value in curr.items() if key != "device"}
        matched_profile = "5. CUSTOM"
        for prof_name, settings in self.PROFILES.items():
            if profile_fields == settings:
                matched_profile = prof_name
                break

        self.current_profile = matched_profile.split(". ")[-1]
        self.lbl_profile_status.setText(f"PROFILE: {self.current_profile}")
        self._update_profile_buttons(matched_profile)
        self._update_pending_count()

    def _update_profile_buttons(self, active_name: str) -> None:
        for name, btn in self.profile_buttons.items():
            btn.setChecked(name == active_name)

    def _on_profile_clicked(self, prof_name: str, initial: bool = False) -> None:
        if prof_name in self.PROFILES:
            self._set_state(self.PROFILES[prof_name])

        self._on_setting_changed()

        if prof_name not in self.PROFILES:
            # Explicit "CUSTOM" selection overrides the auto-detected match.
            self.current_profile = "CUSTOM"
            self.lbl_profile_status.setText("PROFILE: CUSTOM")
            self._update_profile_buttons(prof_name)

        if initial:
            self._save_checkpoint_state()

    def _apply_changes(self, permanent: bool = False) -> None:
        self.quick_status.setText("STATUS  APPLYING...")
        self.apply_requested.emit(self._get_current_state(), permanent)

    def on_apply_result(self, success: bool, permanent: bool) -> None:
        """Called by the main window once the privileged apply command finishes."""
        if success:
            self._save_checkpoint_state()
            self._save_to_profile_json()
            self.quick_status.setText("STATUS  PERMANENT" if permanent else "STATUS  ACTIVE")
        else:
            self._update_pending_count()
            self.quick_status.setText("STATUS  APPLY FAILED")

    def _restore_previous(self) -> None:
        if self.saved_state:
            self._set_state(self.saved_state)
            self._on_setting_changed()

    def _reset_defaults(self) -> None:
        self._on_profile_clicked("1. BALANCED")
        self._apply_changes(permanent=False)

    def _load_from_profile_json(self) -> None:
        profile_path = Path("output/tweaks-profile.json")
        if not profile_path.exists():
            return
        try:
            data = json.loads(profile_path.read_text())
            if "cpu_governor" in data:
                self.combo_governor.setCurrentText(data["cpu_governor"])
            if "scheduler" in data:
                self.combo_scheduler.setCurrentText(data["scheduler"])
            if "zram_enabled" in data:
                self.combo_zram.setCurrentText("ENABLED" if data["zram_enabled"] else "DISABLED")
            if "turbo_enabled" in data:
                self.combo_turbo.setCurrentText("ENABLED" if data["turbo_enabled"] else "DISABLED")
        except Exception:
            pass

    def _save_to_profile_json(self) -> None:
        try:
            out_dir = Path("output")
            out_dir.mkdir(parents=True, exist_ok=True)
            profile_path = out_dir / "tweaks-profile.json"
            curr = self._get_current_state()
            data = {
                "preset": self.current_profile,
                "cpu_governor": curr["governor"],
                "turbo_enabled": curr["turbo"] == "ENABLED",
                "energy_preference": curr["energy"],
                "memory_swappiness": curr["swappiness"],
                "zram_enabled": curr["zram"] == "ENABLED",
                "compression_algorithm": curr["compression"],
                "storage_scheduler": curr["scheduler"],
                "read_ahead_kb": curr["read_ahead"],
            }
            profile_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
