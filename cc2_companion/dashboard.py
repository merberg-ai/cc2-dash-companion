from __future__ import annotations

from datetime import datetime
import threading
import webbrowser

import httpx

from PySide6.QtCore import Qt, Signal, QObject
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
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_overview_tab(), "Overview")
        self.tabs.addTab(self._build_camera_ai_tab(), "Camera / AI")
        self.tabs.addTab(self._build_console_tab(), "Console")
        self.tabs.addTab(self._build_settings_tab(), "Settings")
        self.setCentralWidget(self.tabs)
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
        root.setObjectName("page")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        return root, layout

    def _card(self, object_name: str = "card") -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName(object_name)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)
        return frame, layout

    def _header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title = QLabel("cc2-dash Companion")
        self.title.setObjectName("title")
        self.subtitle = QLabel("LAN printer cockpit • tray monitor • Portal AI status")
        self.subtitle.setObjectName("muted")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        self.connection_pill = QLabel("Offline")
        self.connection_pill.setObjectName("pill")
        header.addLayout(title_box, 1)
        header.addWidget(self.connection_pill)
        return header

    def _build_overview_tab(self) -> QWidget:
        root, layout = self._page()
        layout.addLayout(self._header())

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        printer_card, c = self._card()
        c.addWidget(self._section("Printer"))
        self.printer_name = QLabel("Printer: —")
        self.printer_state = QLabel("State: —")
        self.file_label = QLabel("File: —")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        c.addWidget(self.printer_name)
        c.addWidget(self.printer_state)
        c.addWidget(self.file_label)
        c.addWidget(self.progress)
        grid.addWidget(printer_card, 0, 0)

        ai_card, ai = self._card()
        ai.addWidget(self._section("Portal AI"))
        self.ai_status = QLabel("Portal AI: —")
        self.ai_monitor = QLabel("Monitor: —")
        self.ai_last = QLabel("Last check: —")
        self.ai_last.setObjectName("muted")
        ai.addWidget(self.ai_status)
        ai.addWidget(self.ai_monitor)
        ai.addWidget(self.ai_last)
        grid.addWidget(ai_card, 0, 1)

        host_card, host = self._card()
        host.addWidget(self._section("Host"))
        self.host_info = QLabel("Host: —")
        self.host_info.setWordWrap(True)
        self.version_info = QLabel("Version: —")
        host.addWidget(self.host_info)
        host.addWidget(self.version_info)
        row2 = QHBoxLayout()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_requested.emit)
        open_dash = QPushButton("Open Dashboard")
        open_dash.clicked.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_full_dashboard_path))
        open_portal = QPushButton("Open Portal")
        open_portal.clicked.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_portal_path))
        row2.addWidget(refresh)
        row2.addWidget(open_dash)
        row2.addWidget(open_portal)
        host.addLayout(row2)
        grid.addWidget(host_card, 1, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch(1)
        return root

    def _build_camera_ai_tab(self) -> QWidget:
        root, layout = self._page()
        cam_card, cam = self._card()
        cam.addWidget(self._section("Camera Snapshot"))
        self.snapshot = QLabel("No snapshot yet")
        self.snapshot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.snapshot.setMinimumHeight(260)
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
        # A fixed card-friendly footprint: compact, predictable, and large enough for the console/camera.
        self.setFixedSize(560, 680)

    def _save_window_geometry(self) -> None:
        if not self.cfg.remember_window_geometry:
            return
        geo = self.geometry()
        self.cfg.window_x = int(geo.x())
        self.cfg.window_y = int(geo.y())
        # Size is fixed by the card layout; only remember screen position.
        save_config(self.cfg)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_window_geometry()
        self.streamer.stop()
        self.hide()
        event.ignore()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._camera_stream_url:
            self.streamer.start(self._camera_stream_url)

    def hideEvent(self, event) -> None:  # type: ignore[override]
        self._save_window_geometry()
        self.streamer.stop()
        super().hideEvent(event)

    def _update_snapshot(self, data: bytes | None) -> None:
        if not data:
            return
        pix = QPixmap()
        if pix.loadFromData(data):
            self.snapshot.setPixmap(pix.scaled(self.snapshot.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

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
