from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

APP_NAME = "cc2-dash Companion"
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "cc2-dash-companion"
CONFIG_PATH = APP_DIR / "config.json"


@dataclass
class CompanionConfig:
    host_url: str = "http://127.0.0.1:8080"
    poll_interval_seconds: int = 5
    start_minimized: bool = True
    show_notifications: bool = True
    selected_printer_id: str = ""
    open_full_dashboard_path: str = "/"
    open_portal_path: str = "/portal"
    theme: str = "octo_dark_blue"
    # Compact fixed window defaults. Size is controlled by the UI; position can be remembered.
    window_x: int = -1
    window_y: int = -1
    window_w: int = 380
    window_h: int = 540
    remember_window_geometry: bool = True
    enable_camera_stream: bool = True  # legacy config key; streaming is automatic when available

    @property
    def normalized_host_url(self) -> str:
        url = (self.host_url or "").strip().rstrip("/")
        if url and not url.startswith(("http://", "https://")):
            url = "http://" + url
        return url or "http://127.0.0.1:8080"


def load_config() -> CompanionConfig:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        cfg = CompanionConfig()
        save_config(cfg)
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        base = asdict(CompanionConfig())
        base.update({k: v for k, v in data.items() if k in base})
        return CompanionConfig(**base)
    except Exception:
        broken = CONFIG_PATH.with_suffix(".broken.json")
        try:
            CONFIG_PATH.replace(broken)
        except Exception:
            pass
        cfg = CompanionConfig()
        save_config(cfg)
        return cfg


def save_config(cfg: CompanionConfig) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
