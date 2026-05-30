from __future__ import annotations

from datetime import datetime
import threading
import webbrowser

import httpx

from PySide6.QtCore import Qt, Signal, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QProgressBar, QSpinBox, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget
)

from .config import CompanionConfig, save_config
from .state import CompanionState
from .themes import qss, theme_choices


class MjpegStream(QObject):
    frame = Signal(bytes)
    status = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._url = ""

    def start(self, url: str) -> None:
        url = (url or "").strip()
        if not url:
            self.stop()
            return
        if self._thread and self._thread.is_alive() and self._url == url:
            return
        self.stop()
        self._url = url
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, args=(url,), daemon=True)
        self._thread.start()
        self.status.emit("STREAM", f"Camera stream starting: {url}")

    def stop(self) -> None:
        self._stop.set()
        self._url = ""

    def _run(self, url: str) -> None:
        buf = bytearray()
        try:
            with httpx.stream("GET", url, timeout=httpx.Timeout(8.0, read=20.0), follow_redirects=True) as response:
                if response.status_code >= 400:
                    self.status.emit("ERROR", f"Camera stream HTTP {response.status_code}")
                    return
                self.status.emit("STREAM", "Camera stream connected")
                for chunk in response.iter_bytes():
                    if self._stop.is_set():
                        break
                    if not chunk:
                        continue
                    buf.extend(chunk)
                    while True:
                        start = buf.find(b"\xff\xd8")
                        end = buf.find(b"\xff\xd9", start + 2) if start >= 0 else -1
                        if start >= 0 and end >= 0:
                            jpg = bytes(buf[start:end + 2])
                            del buf[:end + 2]
                            self.frame.emit(jpg)
                        else:
                            if len(buf) > 2_000_000:
                                del buf[:-4096]
                            break
        except Exception as exc:
            if not self._stop.is_set():
                self.status.emit("ERROR", f"Camera stream failed: {exc}")
        finally:
            if not self._stop.is_set():
                self.status.emit("STREAM", "Camera stream ended")


class Dashboard(QMainWindow):
    refresh_requested = Signal()
    feedback_requested = Signal(str)
    config_changed = Signal(object)

    def __init__(self, cfg: CompanionConfig):
        super().__init__()
        self.cfg = cfg
        self.state = CompanionState()
        self._camera_stream_url = ""
        self.streamer = MjpegStream()
        self.streamer.frame.connect(self._update_snapshot)
        self.streamer.status.connect(self.add_console_line)
        self.setWindowTitle("cc2-dash Companion")
        
        # Transparent background and frameless flags
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        
        # Outer container styled as #page for gradient/border
        main_widget = QWidget(self)
        main_widget.setObjectName("page")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        
        # Custom Title Bar
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(12, 6, 12, 6)
        title_bar_layout.setSpacing(8)
        
        self.status_dot = QLabel()
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setStyleSheet("background-color: #5f646e; border-radius: 5px;")
        title_bar_layout.addWidget(self.status_dot)
        
        title_text = QLabel("cc2-dash Companion")
        title_text.setObjectName("titleBarText")
        title_bar_layout.addWidget(title_text)
        title_bar_layout.addStretch(1)
        
        min_btn = QPushButton("—")
        min_btn.setObjectName("titleBarBtn")
        min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(min_btn)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("titleBarBtnClose")
        close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_overview_tab(), "Overview")
        self.tabs.addTab(self._build_camera_ai_tab(), "Camera / AI")
        self.tabs.addTab(self._build_console_tab(), "Console")
        self.tabs.addTab(self._build_settings_tab(), "Settings")
        main_layout.addWidget(self.tabs)
        
        self.setCentralWidget(main_widget)
        
        self.apply_theme()
        self._lock_compact_size()
        
        if self.cfg.remember_window_geometry and self.cfg.window_x >= 0 and self.cfg.window_y >= 0:
            self.move(int(self.cfg.window_x), int(self.cfg.window_y))
        self.add_console_line("BOOT", "cc2-dash Companion UI initialized")

    def apply_theme(self) -> None:
        self.setStyleSheet(qss(self.cfg.theme))
        self._style_snapshot()

    def _page(self) -> tuple[QWidget, QVBoxLayout]:
        root = QWidget()
        root.setObjectName("tabPage")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        return root, layout

    def _card(self, object_name: str = "card") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName(object_name)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        return frame, layout

    def _header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        self.overview_label = QLabel("Overview")
        self.overview_label.setObjectName("sectionTitle")
        self.connection_pill = QLabel("Offline")
        self.connection_pill.setObjectName("pill")
        header.addWidget(self.overview_label, 1)
        header.addWidget(self.connection_pill)
        return header

    def _build_overview_tab(self) -> QWidget:
        root, layout = self._page()
        layout.addLayout(self._header())

        printer_card, c = self._card()
        c.addWidget(self._section("Printer"))
        self.printer_name = QLabel("Printer: —")
        self.printer_state = QLabel("State: —")
        self.file_label = QLabel("File: —")
        self.file_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        c.addWidget(self.printer_name)
        c.addWidget(self.printer_state)
        c.addWidget(self.file_label)
        c.addWidget(self.progress)
        layout.addWidget(printer_card)

        ai_card, ai = self._card()
        ai.addWidget(self._section("Portal AI"))
        self.ai_status = QLabel("Portal AI: —")
        self.ai_monitor = QLabel("Monitor: —")
        self.ai_last = QLabel("Last check: —")
        self.ai_last.setObjectName("muted")
        ai.addWidget(self.ai_status)
        ai.addWidget(self.ai_monitor)
        ai.addWidget(self.ai_last)
        layout.addWidget(ai_card)

        host_card, host = self._card()
        host.addWidget(self._section("Host"))
        self.host_info = QLabel("Host: —")
        self.host_info.setWordWrap(True)
        self.version_info = QLabel("Version: —")
        host.addWidget(self.host_info)
        host.addWidget(self.version_info)
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_requested.emit)
        open_dash = QPushButton("Dashboard")
        open_dash.clicked.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_full_dashboard_path))
        open_portal = QPushButton("Portal")
        open_portal.clicked.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_portal_path))
        row2.addWidget(refresh)
        row2.addWidget(open_dash)
        row2.addWidget(open_portal)
        host.addLayout(row2)
        layout.addWidget(host_card)

        layout.addStretch(1)
        return root

    def _build_camera_ai_tab(self) -> QWidget:
        root, layout = self._page()
        cam_card, cam = self._card()
        cam.addWidget(self._section("Camera Snapshot"))
        self.snapshot = QLabel("No snapshot yet")
        self.snapshot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.snapshot.setFixedHeight(210)
        cam.addWidget(self.snapshot)
        self.stream_status = QLabel("Camera: waiting for printer relay")
        self.stream_status.setObjectName("muted")
        cam.addWidget(self.stream_status)
        layout.addWidget(cam_card)

        feedback_card, fb = self._card()
        fb.addWidget(self._section("Feedback"))
        hint = QLabel("Send quick feedback to cc2-dash-lite so Portal AI can learn from false alarms and real issues.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        fb.addWidget(hint)
        row = QHBoxLayout()
        for label, text in (("looks_good", "Looks good"), ("false_alarm", "False alarm"), ("bad", "Bad / real issue")):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, x=label: self.feedback_requested.emit(x))
            row.addWidget(b)
        fb.addLayout(row)
        layout.addWidget(feedback_card)
        layout.addStretch(1)
        return root

    def _build_console_tab(self) -> QWidget:
        root, layout = self._page()
        header = QHBoxLayout()
        title = self._section("Debug Console")
        header.addWidget(title, 1)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self.console.clear())
        header.addWidget(clear)
        layout.addLayout(header)
        self.console = QTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(420)
        layout.addWidget(self.console, 1)
        return root

    def _build_settings_tab(self) -> QWidget:
        root, layout = self._page()
        card, formbox = self._card()
        formbox.addWidget(self._section("Companion Settings"))
        form = QFormLayout()
        self.host_edit = QLineEdit(self.cfg.host_url)
        self.poll_spin = QSpinBox()
        self.poll_spin.setRange(2, 300)
        self.poll_spin.setSuffix(" sec")
        self.poll_spin.setValue(int(self.cfg.poll_interval_seconds))
        self.notify_check = QCheckBox("Show Windows tray notifications")
        self.notify_check.setChecked(bool(self.cfg.show_notifications))
        self.remember_geom_check = QCheckBox("Remember window position")
        self.remember_geom_check.setChecked(bool(self.cfg.remember_window_geometry))
        self.theme_combo = QComboBox()
        for tid, name in theme_choices():
            self.theme_combo.addItem(name, tid)
        idx = self.theme_combo.findData(self.cfg.theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.printer_combo = QComboBox()
        form.addRow("cc2-dash host URL", self.host_edit)
        form.addRow("Poll interval", self.poll_spin)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Selected printer", self.printer_combo)
        form.addRow("Notifications", self.notify_check)
        form.addRow("Window", self.remember_geom_check)
        formbox.addLayout(form)
        save = QPushButton("Save Settings")
        save.clicked.connect(self._save_settings)
        formbox.addWidget(save)
        layout.addWidget(card)
        layout.addStretch(1)
        return root

    def _section(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _save_settings(self) -> None:
        self.cfg.host_url = self.host_edit.text().strip()
        self.cfg.poll_interval_seconds = int(self.poll_spin.value())
        self.cfg.show_notifications = self.notify_check.isChecked()
        self.cfg.remember_window_geometry = self.remember_geom_check.isChecked()
        self.cfg.selected_printer_id = self.printer_combo.currentData() or ""
        self.cfg.theme = self.theme_combo.currentData() or "octo_dark_blue"
        save_config(self.cfg)
        self.apply_theme()
        self.add_console_line("CONFIG", f"Settings saved. Theme={self.cfg.theme}, host={self.cfg.normalized_host_url}")
        self.config_changed.emit(self.cfg)

    def update_state(self, state: CompanionState) -> None:
        self.state = state
        if state.selected_printer_id and self.cfg.selected_printer_id != state.selected_printer_id:
            self.cfg.selected_printer_id = state.selected_printer_id
            save_config(self.cfg)
        if hasattr(self, "status_dot"):
            level = state.tray_level()
            dot_color = {
                "offline": "#5f646e",
                "idle": "#00b2ff",
                "printing": "#00ff8c",
                "warn": "#ffbf40",
                "alert": "#ff4556"
            }.get(level, "#00b2ff")
            self.status_dot.setStyleSheet(f"background-color: {dot_color}; border-radius: 5px;")
        self.connection_pill.setText("Connected" if state.connected else "Offline")
        self.host_info.setText(f"Host: {self.cfg.normalized_host_url}" + (f" — {state.error}" if state.error else ""))
        build = (state.version.get("build") or state.health.get("build") or {}) if isinstance(state.version, dict) else {}
        version = build.get("version") or state.health.get("version") or "unknown"
        commit = build.get("git_commit") or build.get("commit") or ""
        self.version_info.setText(f"Version: {version}" + (f" / {commit[:8]}" if commit else ""))
        self.printer_name.setText(f"Printer: {state.printer_name()}")
        self.printer_state.setText(f"State: {state.print_state()}")
        self.file_label.setText(f"File: {state.filename()}")
        self.progress.setValue(state.progress_percent())
        ai_label, ai_sev = state.ai_summary()
        self.ai_status.setText(f"Portal AI: {ai_label} / {ai_sev}")
        mon = state.ai_monitor or {}
        running = mon.get("running") or mon.get("enabled") or mon.get("active")
        self.ai_monitor.setText(f"Monitor: {'running' if running else 'stopped/unknown'}")
        last = mon.get("last_check") or mon.get("last_checked") or mon.get("updated_at") or "—"
        self.ai_last.setText(f"Last check: {last}")
        self._update_printer_combo(state)
        self._camera_stream_url = state.camera_stream_url or ""
        if self._camera_stream_url:
            self.stream_status.setText("Camera: live relay stream")
        else:
            self.stream_status.setText("Camera: no relay stream; using snapshots when available")
        if self.isVisible() and self._camera_stream_url:
            self.streamer.start(self._camera_stream_url)
        else:
            self.streamer.stop()
            self._update_snapshot(state.last_snapshot_bytes)

    def _update_printer_combo(self, state: CompanionState) -> None:
        current = self.printer_combo.currentData() or self.cfg.selected_printer_id
        self.printer_combo.blockSignals(True)
        self.printer_combo.clear()
        for p in state.printers:
            pid = str(p.get("id") or "")
            if not pid:
                continue
            name = p.get("name") or p.get("serial") or pid
            self.printer_combo.addItem(str(name), pid)
        idx = self.printer_combo.findData(current or state.selected_printer_id)
        if idx >= 0:
            self.printer_combo.setCurrentIndex(idx)
        self.printer_combo.blockSignals(False)

    def _lock_compact_size(self) -> None:
        """Make the mini dashboard behave like a compact tray widget, not a resizable app window."""
        self.adjustSize()
        self.setFixedSize(380, 540)

    def _save_window_geometry(self) -> None:
        if not self.cfg.remember_window_geometry:
            return
        geo = self.geometry()
        self.cfg.window_x = int(geo.x())
        self.cfg.window_y = int(geo.y())
        save_config(self.cfg)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() < 45:
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
        if getattr(self, "_dragging", False):
            self._dragging = False
            self._save_window_geometry()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if self.cfg.remember_window_geometry:
            pos = event.pos()
            self.cfg.window_x = pos.x()
            self.cfg.window_y = pos.y()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_window_geometry()
        self.streamer.stop()
        if getattr(self, "_fading_out", False):
            event.accept()
        else:
            self._fading_out = True
            event.ignore()
            self._fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
            self._fade_out_anim.setDuration(200)
            self._fade_out_anim.setStartValue(self.windowOpacity())
            self._fade_out_anim.setEndValue(0.0)
            self._fade_out_anim.finished.connect(self._on_fade_out_finished)
            self._fade_out_anim.start()

    def _on_fade_out_finished(self) -> None:
        self.hide()
        self._fading_out = False

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._fading_out = False
        if self._camera_stream_url:
            self.streamer.start(self._camera_stream_url)
        else:
            self._update_snapshot(self.state.last_snapshot_bytes)
        
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(0.96)
        self._fade_anim.start()

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self._save_window_geometry()
        self.streamer.stop()
        super().hideEvent(event)

    def _update_snapshot(self, data: bytes | None) -> None:
        if not self.isVisible() or not data:
            return
        pix = QPixmap()
        if pix.loadFromData(data):
            self.snapshot.setPixmap(pix.scaled(self.snapshot.width(), self.snapshot.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _style_snapshot(self) -> None:
        if hasattr(self, "snapshot"):
            self.snapshot.setStyleSheet("background:#000000; border:1px solid rgba(255,255,255,0.12); border-radius:12px; color:#888; padding:8px;")

    def add_console_line(self, level: str, message: str) -> None:
        if not hasattr(self, "console"):
            return
        ts = datetime.now().strftime("%H:%M:%S")
        safe = str(message).replace("<", "&lt;").replace(">", "&gt;")
        self.console.append(f"[{ts}] [{level}] {safe}")
        self.console.moveCursor(self.console.textCursor().MoveOperation.End)
