from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget
)

from .config import CONFIG_PATH, CompanionConfig, save_config
from .themes import qss, theme_choices


class SettingsDialog(QDialog):
    config_changed = Signal(object)

    def __init__(self, cfg: CompanionConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("cc2-dash Companion Settings")
        self.setMinimumWidth(520)
        self.setStyleSheet(qss(self.cfg.theme))

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Companion Settings")
        title.setObjectName("title")
        root.addWidget(title)

        hint = QLabel("Configure the cc2-dash-lite host, tray behavior, and cc2-style theme.")
        hint.setObjectName("muted")
        root.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)

        self.host_edit = QLineEdit(self.cfg.host_url)
        self.host_edit.setPlaceholderText("http://192.168.1.50:8080")

        self.poll_spin = QSpinBox()
        self.poll_spin.setRange(2, 300)
        self.poll_spin.setSuffix(" sec")
        self.poll_spin.setValue(int(self.cfg.poll_interval_seconds))

        self.theme_combo = QComboBox()
        for tid, name in theme_choices():
            self.theme_combo.addItem(name, tid)
        idx = self.theme_combo.findData(self.cfg.theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)

        self.start_minimized_check = QCheckBox("Start minimized to tray")
        self.start_minimized_check.setChecked(bool(self.cfg.start_minimized))

        self.notify_check = QCheckBox("Show Windows tray notifications")
        self.notify_check.setChecked(bool(self.cfg.show_notifications))

        self.remember_geom_check = QCheckBox("Remember mini dashboard position")
        self.remember_geom_check.setChecked(bool(self.cfg.remember_window_geometry))

        self.dashboard_path = QLineEdit(self.cfg.open_full_dashboard_path)
        self.dashboard_path.setPlaceholderText("/")

        self.portal_path = QLineEdit(self.cfg.open_portal_path)
        self.portal_path.setPlaceholderText("/portal")

        form.addRow("cc2-dash host URL", self.host_edit)
        form.addRow("Polling interval", self.poll_spin)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Dashboard path", self.dashboard_path)
        form.addRow("Portal path", self.portal_path)
        form.addRow("Startup", self.start_minimized_check)
        form.addRow("Notifications", self.notify_check)
        form.addRow("Window", self.remember_geom_check)
        root.addLayout(form)

        path_row = QHBoxLayout()
        path_label = QLabel(f"Config file: {CONFIG_PATH}")
        path_label.setObjectName("muted")
        path_label.setWordWrap(True)
        path_row.addWidget(path_label, 1)
        open_cfg = QPushButton("Open Folder")
        open_cfg.clicked.connect(self._open_config_folder)
        path_row.addWidget(open_cfg)
        root.addLayout(path_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _preview_theme(self) -> None:
        self.setStyleSheet(qss(self.theme_combo.currentData()))

    def _clean_path(self, value: str, fallback: str) -> str:
        value = (value or "").strip()
        if not value:
            return fallback
        if not value.startswith("/"):
            value = "/" + value
        return value

    def _save(self) -> None:
        self.cfg.host_url = self.host_edit.text().strip()
        self.cfg.poll_interval_seconds = int(self.poll_spin.value())
        self.cfg.theme = self.theme_combo.currentData() or "octo_dark_blue"
        self.cfg.start_minimized = self.start_minimized_check.isChecked()
        self.cfg.show_notifications = self.notify_check.isChecked()
        self.cfg.remember_window_geometry = self.remember_geom_check.isChecked()
        self.cfg.open_full_dashboard_path = self._clean_path(self.dashboard_path.text(), "/")
        self.cfg.open_portal_path = self._clean_path(self.portal_path.text(), "/portal")
        save_config(self.cfg)
        self.config_changed.emit(self.cfg)
        self.accept()

    def _open_config_folder(self) -> None:
        import os
        os.startfile(str(CONFIG_PATH.parent))  # type: ignore[attr-defined]
