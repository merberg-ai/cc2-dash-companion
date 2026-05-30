from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    id: str
    name: str
    colors: dict[str, str]
    fonts: dict[str, str]
    radius: int = 14
    scanlines: bool = False

THEMES: dict[str, Theme] = {
    "octo_dark_blue": Theme("octo_dark_blue", "Octo Dark Blue", {"bg":"#343941","bg2":"#252932","card":"#292b31","card_soft":"#30333b","border":"rgba(255,255,255,0.09)","text":"#f4f4f5","muted":"#b8bdc8","primary":"#49669c","primary_hover":"#5878b5","success":"#22c55e","warning":"#eab308","danger":"#ef4444"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 14),
    "amber_terminal": Theme("amber_terminal", "Amber Terminal", {"bg":"#12100b","bg2":"#20180e","card":"rgba(29, 22, 14, 0.94)","card_soft":"rgba(45, 33, 18, 0.92)","border":"rgba(255,180,72,0.18)","text":"#ffe7b3","muted":"#c9a96f","primary":"#b46b1d","primary_hover":"#d18228","success":"#55e17a","warning":"#f6be3b","danger":"#ff5a4d"}, {"base":"Consolas","mono":"Consolas"}, 12, True),
    "mainsail_dark": Theme("mainsail_dark", "Mainsail-ish Dark", {"bg":"#1f2937","bg2":"#111827","card":"#263244","card_soft":"#2e3b4f","border":"rgba(255,255,255,0.08)","text":"#f9fafb","muted":"#cbd5e1","primary":"#2563eb","primary_hover":"#3b82f6","success":"#10b981","warning":"#f59e0b","danger":"#ef4444"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 16),
    "carbon_glass": Theme("carbon_glass", "Carbon Glass", {"bg":"#0f172a","bg2":"#1e293b","card":"rgba(15,23,42,0.82)","card_soft":"rgba(30,41,59,0.82)","border":"rgba(148,163,184,0.18)","text":"#f8fafc","muted":"#cbd5e1","primary":"#475569","primary_hover":"#64748b","success":"#22c55e","warning":"#eab308","danger":"#ef4444"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 18),
    "toxic_green": Theme("toxic_green", "Toxic Green Lab", {"bg":"#041007","bg2":"#061b0c","card":"rgba(5, 21, 10, 0.94)","card_soft":"rgba(9, 34, 15, 0.94)","border":"rgba(87,255,117,0.2)","text":"#e8ffe8","muted":"#9fd3a5","primary":"#20c45a","primary_hover":"#42f57b","success":"#5cff89","warning":"#e6f75c","danger":"#ff4971"}, {"base":"Consolas","mono":"Consolas"}, 12, True),
    "blood_terminal": Theme("blood_terminal", "Blood Red Terminal", {"bg":"#100405","bg2":"#24070a","card":"rgba(30, 7, 9, 0.94)","card_soft":"rgba(50, 12, 15, 0.94)","border":"rgba(255,86,86,0.2)","text":"#ffe8e8","muted":"#d69b9b","primary":"#b71f2e","primary_hover":"#e33b4b","success":"#65e08b","warning":"#f5b944","danger":"#ff4d4d"}, {"base":"Consolas","mono":"Consolas"}, 13, True),
    "elegoo_dark": Theme("elegoo_dark", "Elegoo Dark", {"bg":"#171718","bg2":"#202123","card":"#242526","card_soft":"#303133","border":"rgba(255,255,255,0.1)","text":"#f7f7f8","muted":"#b8b8bd","primary":"#ff7a1a","primary_hover":"#ff9440","success":"#38d878","warning":"#ffcc4d","danger":"#ff5c5c"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 12),
    "klipper_blue": Theme("klipper_blue", "Klipper Blue", {"bg":"#07111f","bg2":"#0d1b2e","card":"rgba(13, 27, 46, 0.94)","card_soft":"rgba(20, 38, 62, 0.94)","border":"rgba(106,164,255,0.18)","text":"#eaf3ff","muted":"#a8bed8","primary":"#2f81f7","primary_hover":"#58a6ff","success":"#3ddc84","warning":"#f5c451","danger":"#ff5f72"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 16),
    "oled_mono": Theme("oled_mono", "OLED Mono", {"bg":"#000000","bg2":"#050505","card":"#080808","card_soft":"#121212","border":"rgba(255,255,255,0.16)","text":"#f7f7f7","muted":"#a8a8a8","primary":"#4b5563","primary_hover":"#6b7280","success":"#ffffff","warning":"#d8d8d8","danger":"#ff7474"}, {"base":"Consolas","mono":"Consolas"}, 8),
    "cyberpunk_magenta": Theme("cyberpunk_magenta", "Cyberpunk Magenta", {"bg":"#0d0615","bg2":"#160b2c","card":"rgba(23, 10, 43, 0.94)","card_soft":"rgba(38, 16, 66, 0.94)","border":"rgba(255,75,216,0.18)","text":"#fff0ff","muted":"#d4a8df","primary":"#d946ef","primary_hover":"#f472b6","success":"#34f5c5","warning":"#facc15","danger":"#ff4f8b"}, {"base":"Segoe UI","mono":"Cascadia Mono"}, 18, True),
    "retro_crt_blue": Theme("retro_crt_blue", "Retro CRT Blue-Gray", {"bg":"#05080d","bg2":"#101720","card":"rgba(12, 19, 28, 0.94)","card_soft":"rgba(22, 31, 44, 0.94)","border":"rgba(133, 163, 196, 0.18)","text":"#d7e4ee","muted":"#93a8bb","primary":"#5f7f9a","primary_hover":"#7f9cb5","success":"#7fdcaa","warning":"#d5be73","danger":"#e68181"}, {"base":"Courier New","mono":"Courier New"}, 10, True),
    "green_phosphor_crt": Theme("green_phosphor_crt", "Green Phosphor CRT", {"bg":"#020403","bg2":"#07100a","card":"rgba(4, 12, 7, 0.94)","card_soft":"rgba(8, 22, 12, 0.94)","border":"rgba(103, 255, 156, 0.20)","text":"#bcffd0","muted":"#76b389","primary":"#33d16f","primary_hover":"#5af592","success":"#7dffb0","warning":"#d7c76e","danger":"#ff6f6f"}, {"base":"Courier New","mono":"Courier New"}, 10, True),
    "high_contrast": Theme("high_contrast", "High Contrast", {"bg":"#000000","bg2":"#111111","card":"#161616","card_soft":"#202020","border":"rgba(255,255,255,0.22)","text":"#ffffff","muted":"#e5e5e5","primary":"#1d4ed8","primary_hover":"#2563eb","success":"#22c55e","warning":"#facc15","danger":"#f87171"}, {"base":"Segoe UI","mono":"Consolas"}, 10),
}


def hex_to_rgba(color_str: str, alpha: float) -> str:
    color_str = color_str.strip()
    if color_str.startswith("rgba"):
        return color_str
    if color_str.startswith("#"):
        hex_val = color_str.lstrip("#")
        if len(hex_val) == 3:
            hex_val = "".join(c * 2 for c in hex_val)
        if len(hex_val) == 6:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
    return color_str


def get_theme(theme_id: str | None) -> Theme:
    return THEMES.get(theme_id or "octo_dark_blue", THEMES["octo_dark_blue"])


def theme_choices() -> list[tuple[str, str]]:
    return [(theme.id, theme.name) for theme in THEMES.values()]


def qss(theme_id: str | None) -> str:
    t = get_theme(theme_id)
    c = t.colors
    r = t.radius
    base_font = t.fonts.get("base", "Segoe UI")
    mono_font = t.fonts.get("mono", "Consolas")
    
    # Border with alpha for nice border glow
    border_color = hex_to_rgba(c['border'], 0.4) if c['border'].startswith('rgba') else c['border']
    
    return f"""
QMainWindow, QDialog {{ background: transparent; }}
QWidget#page {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {hex_to_rgba(c['bg'], 0.88)}, stop:1 {hex_to_rgba(c['bg2'], 0.88)});
    border: 1px solid {border_color};
    border-radius: {r}px;
}}
QWidget#tabPage {{ background: transparent; }}
QFrame#card {{ background: {hex_to_rgba(c['card'], 0.85)}; border: 1px solid {c['border']}; border-radius: {r}px; }}
QFrame#softCard {{ background: {hex_to_rgba(c['card_soft'], 0.85)}; border: 1px solid {c['border']}; border-radius: {max(8, r - 2)}px; }}
QLabel {{ background: transparent; color: {c['text']}; font-family: {base_font}, Arial; font-size: 10pt; }}
QLabel#title {{ font-size: 20px; font-weight: 900; color: {c['text']}; }}
QLabel#sectionTitle {{ font-size: 14px; font-weight: 800; color: {c['text']}; margin-bottom: 2px; }}
QLabel#muted {{ color: {c['muted']}; }}
QLabel#smallMuted {{ color: {c['muted']}; font-size: 8.5pt; }}
QLabel#pill {{ background: {c['card_soft']}; border: 1px solid {c['primary']}; border-radius: 12px; padding: 3px 8px; color: {c['text']}; font-weight: 800; font-size: 9pt; }}

/* Title Bar Styles */
QWidget#titleBar {{ background: transparent; }}
QLabel#titleBarText {{ font-weight: 800; font-size: 10pt; color: {c['text']}; }}
QPushButton#titleBarBtn, QPushButton#titleBarBtnClose {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: {c['muted']};
    font-weight: bold;
    font-size: 10pt;
    min-width: 28px;
    min-height: 28px;
    max-width: 28px;
    max-height: 28px;
    padding: 0;
}}
QPushButton#titleBarBtn:hover {{
    background: {hex_to_rgba(c['primary'], 0.25)};
    color: {c['text']};
}}
QPushButton#titleBarBtnClose:hover {{
    background: #ef4444;
    color: white;
}}

QPushButton {{ background: {c['primary']}; border: 1px solid {c['primary_hover']}; border-radius: 8px; padding: 6px 10px; color: {c['text']}; font-weight: 800; font-size: 9.5pt; }}
QPushButton:hover {{ background: {c['primary_hover']}; }}
QPushButton:pressed {{ background: {c['card_soft']}; }}
QLineEdit, QSpinBox, QComboBox {{ background: {hex_to_rgba(c['bg2'], 0.9)}; border: 1px solid {c['border']}; border-radius: 8px; padding: 6px; color: {c['text']}; selection-background-color: {c['primary']}; }}
QComboBox QAbstractItemView {{ background: {c['bg2']}; border: 1px solid {c['border']}; selection-background-color: {c['primary']}; color: {c['text']}; }}
QCheckBox {{ spacing: 8px; color: {c['text']}; }}
QProgressBar {{ border: 1px solid {c['border']}; border-radius: 8px; text-align: center; background: {hex_to_rgba(c['bg2'], 0.9)}; color: {c['text']}; font-weight: 700; font-size: 9pt; }}
QProgressBar::chunk {{ background: {c['success']}; border-radius: 8px; }}

QTabWidget {{ background: transparent; }}
QTabWidget::pane {{ border: 0; background: transparent; }}
QTabBar::tab {{ background: {hex_to_rgba(c['bg2'], 0.6)}; color: {c['muted']}; padding: 8px 12px; margin-right: 3px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: 700; font-size: 9.5pt; }}
QTabBar::tab:selected {{ background: {hex_to_rgba(c['card'], 0.85)}; color: {c['text']}; border: 1px solid {c['border']}; border-bottom: 0; }}

QTextEdit#console {{ background: #000000; border: 1px solid {c['border']}; border-radius: {max(8, r - 3)}px; color: {c['success']}; font-family: {mono_font}, Consolas, monospace; font-size: 9.5pt; }}
QScrollBar:vertical {{ background: {c['bg2']}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {c['primary']}; border-radius: 5px; min-height: 20px; }}
"""

