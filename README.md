# cc2-dash Companion v0.1.4

A lightweight Windows tray companion for **cc2-dash-lite**.

It runs in the system tray, polls your cc2-dash-lite host over LAN, shows printer/AI/camera status, and opens a compact mini dashboard when clicked.

## Current v0.1 features

- Windows system tray app
- PySide6 / Qt UI
- Configurable cc2-dash-lite host URL
- Polls cc2-dash-lite health/version/printer/status/AI/camera endpoints
- Mini dashboard window with:
  - cc2-dash-lite-inspired themed UI
  - Overview / Camera-AI / Console / Settings tabs
  - printer state
  - progress bar
  - current file when available
  - automatic live camera preview via the cc2-dash-lite relay, with snapshot fallback
  - Portal AI status
  - AI feedback buttons
  - host version/build info
- Tray icon changes color by status:
  - gray: offline
  - blue: idle/connected
  - green: printing
  - yellow: warning/uncertain
  - red: alert/error
- Right-click tray menu:
  - Open Mini Dashboard
  - Open Full cc2-dash-lite
  - Open Portal
  - Refresh Now
  - Pause Monitoring
  - Quit
- Windows notifications for host disconnects and AI warning/alert changes
- Settings popup from the tray menu
- Theme picker using cc2-dash-lite style themes
- Debug/status console tab with polling, state, config, stream, and feedback messages
- Compact default window size
- Uses a compact fixed-size mini dashboard and remembers its last screen position

## Tested target

- Windows 10/11
- Python 3.11+
- cc2-dash-lite on LAN

## Install for development

```powershell
cd cc2-companion-v0.1.4
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

On first run, open **Settings** and set your cc2-dash-lite host URL, for example:

```text
http://192.168.1.50:8080
```

## Build a Windows EXE

```powershell
scripts\build_windows.bat
```

The EXE will be created under:

```text
dist\cc2-dash-companion.exe
```

## cc2-dash-lite endpoints used

The companion currently uses endpoints already present in the uploaded cc2-dash-lite source:

```text
/health
/api/health
/api/version
/api/printers
/api/status
/api/status/{printer_id}
/api/ai/monitor
/api/printers/{printer_id}/ai/feedback
/api/printers/{printer_id}/camera/status
/api/printers/{printer_id}/camera/stream
/api/printers/{printer_id}/camera/latest.jpg
/api/printers/{printer_id}/camera/snapshot.jpg
/api/printers/{printer_id}/vision/latest.jpg
```

## Notes

This is a v0.1 starter build. It is intentionally read-mostly, except for AI feedback submission. It does not pause, resume, cancel, heat, move, or otherwise control printer jobs.

Future ideas:

- auto-discovery of cc2-dash-lite hosts
- multi-printer overview
- auto-discovery of camera relay capabilities
- startup-on-login toggle
- event history
- cc2-style theme picker with the built-in cc2-dash-lite theme palette
- dedicated Windows installer
- optional service + tray split for hardened background monitoring
