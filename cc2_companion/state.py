from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompanionState:
    connected: bool = False
    host_ok: bool = False
    error: str = ""
    health: dict[str, Any] = field(default_factory=dict)
    version: dict[str, Any] = field(default_factory=dict)
    printers: list[dict[str, Any]] = field(default_factory=list)
    status: dict[str, Any] = field(default_factory=dict)
    ai_monitor: dict[str, Any] = field(default_factory=dict)
    camera_status: dict[str, Any] = field(default_factory=dict)
    selected_printer_id: str = ""
    last_snapshot_bytes: bytes | None = None
    camera_stream_url: str = ""

    def printer_name(self) -> str:
        pid = self.selected_printer_id
        for printer in self.printers:
            if printer.get("id") == pid:
                return printer.get("name") or printer.get("serial") or pid
        return pid or "Default printer"

    def print_state(self) -> str:
        status = self.status or {}
        for key in ("state", "status", "print_state", "print_status", "task_state"):
            val = status.get(key)
            if val not in (None, ""):
                return str(val)
        snap = status.get("snapshot") or status.get("raw") or {}
        if isinstance(snap, dict):
            for key in ("state", "status", "print_state", "print_status", "task_state"):
                val = snap.get(key)
                if val not in (None, ""):
                    return str(val)
        return "Unknown"

    def progress_percent(self) -> int:
        status = self.status or {}
        candidates = [
            status.get("progress"), status.get("progress_percent"), status.get("percent"),
            (status.get("print") or {}).get("progress") if isinstance(status.get("print"), dict) else None,
            (status.get("job") or {}).get("progress") if isinstance(status.get("job"), dict) else None,
        ]
        for raw in candidates:
            try:
                if raw is None:
                    continue
                val = float(raw)
                if val <= 1.0:
                    val *= 100.0
                return max(0, min(100, int(round(val))))
            except Exception:
                continue
        return 0

    def filename(self) -> str:
        status = self.status or {}
        for key in ("filename", "file", "file_name", "current_file", "task_name"):
            val = status.get(key)
            if val:
                return str(val)
        for parent in ("print", "job", "task"):
            obj = status.get(parent)
            if isinstance(obj, dict):
                for key in ("filename", "file", "file_name", "name", "task_name"):
                    val = obj.get(key)
                    if val:
                        return str(val)
        return "—"

    def ai_summary(self) -> tuple[str, str]:
        status = self.status or {}
        ai = status.get("portal_ai") or status.get("vision_ai") or {}
        if not isinstance(ai, dict):
            ai = {}
        label = ai.get("label") or ai.get("state") or ai.get("status") or ai.get("message") or "Unknown"
        severity = ai.get("severity") or ai.get("level") or "info"
        return str(label), str(severity)

    def tray_level(self) -> str:
        if not self.connected:
            return "offline"
        ai_label, ai_sev = self.ai_summary()
        sev = ai_sev.lower()
        state = self.print_state().lower()
        if sev in {"error", "critical", "high", "danger"} or any(x in ai_label.lower() for x in ("fail", "spaghetti", "error")):
            return "alert"
        if sev in {"warning", "warn", "medium", "uncertain"}:
            return "warn"
        if any(x in state for x in ("print", "running", "busy")):
            return "printing"
        return "idle"
