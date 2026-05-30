from __future__ import annotations

from PySide6.QtCore import Signal, Qt, QPropertyAnimation
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

        # Transparent background and frameless flags
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        # Outer container styled as #page for gradient/border
        page = QWidget(self)
        page.setObjectName("page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(14, 12, 14, 12)
        page_layout.setSpacing(10)

        # Custom Title Bar for Settings Dialog
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar_layout.setSpacing(8)

        # Status Dot
        status_dot = QLabel()
        status_dot.setObjectName("statusDot")
        status_dot.setFixedSize(10, 10)
        status_dot.setStyleSheet("background-color: #00b2ff; border-radius: 5px;")
        title_bar_layout.addWidget(status_dot)

        title_text = QLabel("cc2-dash Companion Settings")
        title_text.setObjectName("titleBarText")
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch(1)

        close_btn = QPushButton("×")
        close_btn.setObjectName("titleBarBtnClose")
        close_btn.clicked.connect(self.reject)
        title_bar_layout.addWidget(close_btn)

        page_layout.addWidget(title_bar)

        # Settings content
        title = QLabel("Companion Settings")
        title.setObjectName("title")
        page_layout.addWidget(title)

        hint = QLabel("Configure the cc2-dash-lite host, tray behavior, and cc2-style theme.")
        hint.setObjectName("muted")
        page_layout.addWidget(hint)

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
        page_layout.addLayout(form)

        path_row = QHBoxLayout()
        path_label = QLabel(f"Config file: {CONFIG_PATH}")
        path_label.setObjectName("muted")
        path_label.setWordWrap(True)
        path_row.addWidget(path_label, 1)
        open_cfg = QPushButton("Open Folder")
        open_cfg.clicked.connect(self._open_config_folder)
        path_row.addWidget(open_cfg)
        page_layout.addLayout(path_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        page_layout.addWidget(buttons)

        # Layout on self containing the page card
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(page)

    def _preview_theme(self) -> None:
        self.setStyleSheet(qss(self.theme_combo.currentData()))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() < 40:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self._dragging = True
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if getattr(self, "_dragging", False):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False
        event.accept()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._fading_out = False
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(0.96)
        self._fade_anim.start()

    def hide_animated(self, accept_or_reject: str = "reject") -> None:
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(lambda: self._on_fade_out_finished(accept_or_reject))
        self._fade_anim.start()

    def _on_fade_out_finished(self, action: str) -> None:
        self.hide()
        self.setWindowOpacity(0.96)
        if action == "accept":
            super().accept()
        else:
            super().reject()

    def accept(self) -> None:
        if getattr(self, "_fading_out", False):
            super().accept()
        else:
            self._fading_out = True
            self.hide_animated("accept")

    def reject(self) -> None:
        if getattr(self, "_fading_out", False):
            super().reject()
        else:
            self._fading_out = True
            self.hide_animated("reject")

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
