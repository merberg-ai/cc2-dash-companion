from __future__ import annotations

import sys
import webbrowser

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .api_client import ApiPoller
from .config import CompanionConfig, load_config
from .dashboard import Dashboard
from .icons import make_icon
from .settings_dialog import SettingsDialog
from .state import CompanionState


class CompanionApp:
    def __init__(self) -> None:
        self.qt = QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        self.cfg: CompanionConfig = load_config()
        self.dashboard = Dashboard(self.cfg)
        self.settings_dialog: SettingsDialog | None = None
        self.poller = ApiPoller(self.cfg)
        self.timer = QTimer()
        self.last_level = "offline"
        self.last_connected = False

        self.tray = QSystemTrayIcon(make_icon("offline"), self.qt)
        self.tray.setToolTip("cc2-dash Companion")
        self.menu = QMenu()
        self.action_open = self.menu.addAction("Open Mini Dashboard")
        self.action_open.triggered.connect(self.show_dashboard)
        self.action_full = self.menu.addAction("Open Full cc2-dash-lite")
        self.action_full.triggered.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_full_dashboard_path))
        self.action_portal = self.menu.addAction("Open Portal")
        self.action_portal.triggered.connect(lambda: webbrowser.open(self.cfg.normalized_host_url + self.cfg.open_portal_path))
        self.menu.addSeparator()
        self.action_settings = self.menu.addAction("Settings…")
        self.action_settings.triggered.connect(self.show_settings)
        self.menu.addSeparator()
        self.action_refresh = self.menu.addAction("Refresh Now")
        self.action_refresh.triggered.connect(self.poller.poll)
        self.action_pause = self.menu.addAction("Pause Monitoring")
        self.action_pause.setCheckable(True)
        self.action_pause.toggled.connect(self._toggle_pause)
        self.menu.addSeparator()
        self.action_quit = self.menu.addAction("Quit")
        self.action_quit.triggered.connect(self.qt.quit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

        self.poller.polled.connect(self._state_updated)
        self.dashboard.refresh_requested.connect(self.poller.poll)
        self.dashboard.feedback_requested.connect(self._send_feedback)
        self.dashboard.config_changed.connect(self._config_changed)
        self.timer.timeout.connect(self.poller.poll)
        self._restart_timer()
        self._log("POLL", f"Polling {self.cfg.normalized_host_url}")
        self.poller.poll()
        if not self.cfg.start_minimized:
            self.show_dashboard()

    def _restart_timer(self) -> None:
        self.timer.start(max(2, int(self.cfg.poll_interval_seconds)) * 1000)

    def _toggle_pause(self, paused: bool) -> None:
        if paused:
            self.timer.stop()
            self.action_pause.setText("Resume Monitoring")
        else:
            self.action_pause.setText("Pause Monitoring")
            self._restart_timer()
            self._log("POLL", "Monitoring resumed")
            self.poller.poll()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_dashboard()

    def show_dashboard(self) -> None:
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def show_settings(self) -> None:
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog(self.cfg, self.dashboard)
            self.settings_dialog.config_changed.connect(self._config_changed)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def _config_changed(self, cfg: CompanionConfig) -> None:
        self.cfg = cfg
        self.poller.cfg = cfg
        self._restart_timer()
        self.dashboard.apply_theme()
        self._log("CONFIG", f"Settings saved. Theme={cfg.theme}, interval={cfg.poll_interval_seconds}s")
        self.poller.poll()
        self.tray.showMessage("cc2-dash Companion", "Settings saved", QSystemTrayIcon.MessageIcon.Information, 2500)

    def _state_updated(self, state: CompanionState) -> None:
        self.dashboard.update_state(state)
        level = state.tray_level()
        if state.connected:
            self._log("STATE", f"{state.printer_name()} | {state.print_state()} | {state.progress_percent()}% | {level}")
        else:
            self._log("ERROR", state.error or "cc2-dash host offline")
        self.tray.setIcon(make_icon(level))
        self.tray.setToolTip(f"cc2-dash Companion — {state.printer_name()} — {state.print_state()}")
        if self.cfg.show_notifications:
            if self.last_connected and not state.connected:
                self.tray.showMessage("cc2-dash host offline", state.error or "Could not reach cc2-dash-lite", QSystemTrayIcon.MessageIcon.Warning, 5000)
            elif state.connected and level in {"warn", "alert"} and level != self.last_level:
                ai_label, ai_sev = state.ai_summary()
                self.tray.showMessage("Portal AI status", f"{ai_label} / {ai_sev}", QSystemTrayIcon.MessageIcon.Warning, 5000)
        self.last_connected = state.connected
        self.last_level = level

    def _send_feedback(self, label: str) -> None:
        pid = self.dashboard.state.selected_printer_id or self.cfg.selected_printer_id
        if not pid:
            QMessageBox.warning(self.dashboard, "No printer", "No printer is selected yet.")
            return
        ok, msg = self.poller.post_feedback(pid, label, "Sent from Windows companion v0.1")
        if ok:
            self._log("FEEDBACK", f"{label}: {msg}")
            self.tray.showMessage("cc2-dash Companion", msg, QSystemTrayIcon.MessageIcon.Information, 2500)
            self.poller.poll()
        else:
            self._log("ERROR", f"Feedback failed: {msg}")
            QMessageBox.warning(self.dashboard, "Feedback failed", msg)

    def _log(self, level: str, message: str) -> None:
        try:
            self.dashboard.add_console_line(level, message)
        except Exception:
            pass

    def run(self) -> int:
        return self.qt.exec()


def main() -> int:
    app = CompanionApp()
    return app.run()
