from __future__ import annotations

import httpx
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .config import CompanionConfig
from .state import CompanionState


class PollResult(QObject):
    done = Signal(object)


class PollWorker(QRunnable):
    def __init__(self, cfg: CompanionConfig):
        super().__init__()
        self.cfg = cfg
        self.signals = PollResult()

    @Slot()
    def run(self) -> None:
        state = CompanionState(selected_printer_id=self.cfg.selected_printer_id)
        base = self.cfg.normalized_host_url
        try:
            with httpx.Client(base_url=base, timeout=4.0, follow_redirects=True) as client:
                health = _get_json(client, "/health") or _get_json(client, "/api/health")
                version = _get_json(client, "/api/version")
                printers_payload = _get_json(client, "/api/printers") or {}
                printers = printers_payload.get("configured") or printers_payload.get("printers") or []
                if not isinstance(printers, list):
                    printers = []

                selected = self.cfg.selected_printer_id
                if not selected and printers:
                    selected = str(printers[0].get("id") or "")
                state.selected_printer_id = selected

                status_path = f"/api/status/{selected}" if selected else "/api/status"
                status = _get_json(client, status_path) or _get_json(client, "/api/status") or {}
                ai = _get_json(client, "/api/ai/monitor") or {}
                cam = _get_json(client, f"/api/printers/{selected}/camera/status") if selected else {}
                if selected:
                    state.camera_stream_url = f"{base}/api/printers/{selected}/camera/stream"

                snap_bytes = None
                if selected:
                    for path in (
                        f"/api/printers/{selected}/camera/latest.jpg",
                        f"/api/printers/{selected}/camera/snapshot.jpg",
                        f"/api/printers/{selected}/vision/latest.jpg",
                    ):
                        try:
                            r = client.get(path)
                            if r.status_code == 200 and r.headers.get("content-type", "").lower().startswith("image/"):
                                snap_bytes = r.content
                                break
                        except Exception:
                            continue

                state.connected = True
                state.host_ok = bool(health and health.get("ok", True))
                state.health = health or {}
                state.version = version or {}
                state.printers = printers
                state.status = status or {}
                state.ai_monitor = ai or {}
                state.camera_status = cam or {}
                state.last_snapshot_bytes = snap_bytes
        except Exception as exc:
            state.connected = False
            state.error = str(exc)
        self.signals.done.emit(state)


def _get_json(client: httpx.Client, path: str) -> dict | None:
    try:
        r = client.get(path)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


class ApiPoller(QObject):
    polled = Signal(object)

    def __init__(self, cfg: CompanionConfig):
        super().__init__()
        self.cfg = cfg
        self.pool = QThreadPool.globalInstance()
        self._busy = False

    def poll(self) -> None:
        if self._busy:
            return
        self._busy = True
        worker = PollWorker(self.cfg)
        worker.signals.done.connect(self._done)
        self.pool.start(worker)

    def _done(self, state: CompanionState) -> None:
        self._busy = False
        self.polled.emit(state)

    def post_feedback(self, printer_id: str, label: str, note: str = "") -> tuple[bool, str]:
        try:
            with httpx.Client(base_url=self.cfg.normalized_host_url, timeout=5.0) as client:
                r = client.post(f"/api/printers/{printer_id}/ai/feedback", json={"label": label, "note": note})
                if r.status_code >= 400:
                    return False, r.text[:300]
                return True, "Feedback saved"
        except Exception as exc:
            return False, str(exc)
