# Dream-VoiceTraining — voice analysis for training your speaking voice
# Copyright (C) 2026  Yakuda
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Farbschema und Stylesheet.

COLORS ist ein Dictionary, das zur Laufzeit an Ort und Stelle geaendert
wird. Alle Module halten eine Referenz darauf, ein Themenwechsel wirkt
dadurch ohne Neuimport.
"""

from __future__ import annotations

from dataclasses import dataclass

import i18n
import paths


@dataclass(frozen=True)
class Role:
    key: str
    label_key: str

    @property
    def label(self) -> str:
        return i18n.t(self.label_key)


# Reihenfolge wie im Einstellungsdialog, drei Spalten.
ROLES = [
    Role("accent", "role_accent"),
    Role("bg", "role_window"),
    Role("sidebar", "role_sidebar"),
    Role("bg2", "role_cards"),
    Role("bg3", "role_inner"),
    Role("border", "role_border"),
    Role("fg", "role_text"),
    Role("dim", "role_dim"),
    Role("red", "role_danger"),
    Role("green", "role_ok"),
    Role("yellow", "role_warn"),
    Role("purple", "role_highlight"),
]

ROLE_KEYS = [role.key for role in ROLES]

PRESETS: dict[str, dict[str, str]] = {
    "default": {
        "bg": "#2e3440", "sidebar": "#333a47", "bg2": "#3b4252",
        "bg3": "#434c5e", "border": "#4c566a",
        "fg": "#eceff4", "dim": "#8896ab", "accent": "#88c0d0",
        "red": "#bf616a", "green": "#a3be8c", "yellow": "#ebcb8b",
        "purple": "#b48ead",
    },
    "carbon": {
        "bg": "#161616", "sidebar": "#1c1c1c", "bg2": "#212121",
        "bg3": "#2b2b2b", "border": "#3a3a3a",
        "fg": "#e8e8e8", "dim": "#8a8a8a", "accent": "#c9c9c9",
        "red": "#d05f5f", "green": "#8fb573", "yellow": "#d6b25e",
        "purple": "#a98fc2",
    },
    "nebula": {
        "bg": "#17151f", "sidebar": "#1e1b2a", "bg2": "#252036",
        "bg3": "#302a45", "border": "#3d3559",
        "fg": "#ece8f7", "dim": "#8f86ab", "accent": "#a98bff",
        "red": "#e0607e", "green": "#7fd6a4", "yellow": "#e6c07b",
        "purple": "#c9a6ff",
    },
    "embers": {
        "bg": "#1c1512", "sidebar": "#241b16", "bg2": "#2c211a",
        "bg3": "#3a2b21", "border": "#4d392c",
        "fg": "#f5e8dd", "dim": "#a89083", "accent": "#e08a45",
        "red": "#d4614a", "green": "#9bb06a", "yellow": "#e3b25c",
        "purple": "#c08a9e",
    },
    "grass": {
        "bg": "#141a15", "sidebar": "#19211a", "bg2": "#1f2921",
        "bg3": "#2a362c", "border": "#38483a",
        "fg": "#e6efe6", "dim": "#8aa08d", "accent": "#7cc47f",
        "red": "#cf6b62", "green": "#9ad48f", "yellow": "#ddc06d",
        "purple": "#a99ad0",
    },
    "ocean": {
        "bg": "#101a20", "sidebar": "#142229", "bg2": "#182a33",
        "bg3": "#213945", "border": "#2c4b5a",
        "fg": "#e4f1f6", "dim": "#7e9aa6", "accent": "#42b6d6",
        "red": "#e06c6c", "green": "#5fc9a3", "yellow": "#e0c173",
        "purple": "#8fa8e0",
    },
    "rose": {
        "bg": "#1d1418", "sidebar": "#251920", "bg2": "#2e1f27",
        "bg3": "#3c2a33", "border": "#4f3743",
        "fg": "#f7e6ee", "dim": "#ab8b99", "accent": "#f070a8",
        "red": "#e05f77", "green": "#8fc79f", "yellow": "#e6bd77",
        "purple": "#cf8fd6",
    },
    "mono": {
        "bg": "#0d0d0d", "sidebar": "#141414", "bg2": "#1a1a1a",
        "bg3": "#262626", "border": "#383838",
        "fg": "#f2f2f2", "dim": "#909090", "accent": "#f2f2f2",
        "red": "#c96a6a", "green": "#9aab8f", "yellow": "#c9b98a",
        "purple": "#a99ab5",
    },
}

DEFAULT_PRESET = "default"

# Lebende Farbtabelle. Andere Module halten eine Referenz hierauf.
COLORS: dict[str, str] = dict(PRESETS[DEFAULT_PRESET])

_state = {"preset": DEFAULT_PRESET, "background": None, "card_opacity": 100}


# --------------------------------------------------------------- Helfer

def _clamp(value: int) -> int:
    return max(0, min(255, value))


def _rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    try:
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    except (ValueError, IndexError):
        return (0, 0, 0)


def mix(color: str, other: str, amount: float) -> str:
    """Zwei Farben mischen; amount 0 = color, 1 = other."""
    a, b = _rgb(color), _rgb(other)
    return "#%02x%02x%02x" % tuple(
        _clamp(round(a[i] + (b[i] - a[i]) * amount)) for i in range(3))


def lighten(color: str, amount: float = 0.35) -> str:
    return mix(color, "#ffffff", amount)


def darken(color: str, amount: float = 0.35) -> str:
    return mix(color, "#000000", amount)


def is_light(color: str) -> bool:
    r, g, b = _rgb(color)
    return (0.299 * r + 0.587 * g + 0.114 * b) > 140


def contrast_text(color: str) -> str:
    """Lesbare Schriftfarbe auf einem gegebenen Hintergrund."""
    return "#101010" if is_light(color) else COLORS["fg"]


def rgba(color: str, alpha: float) -> str:
    r, g, b = _rgb(color)
    return f"rgba({r}, {g}, {b}, {alpha:.3f})"


# ---------------------------------------------------------------- Zustand

def preset_name() -> str:
    return _state["preset"]


def background() -> str | None:
    return _state["background"]


def card_opacity() -> int:
    return int(_state["card_opacity"])


def apply(colors: dict | None = None, preset: str | None = None,
          bg_image: str | None = ..., opacity: int | None = None) -> None:
    """Zustand uebernehmen. bg_image=... bedeutet unveraendert."""
    if preset is not None:
        _state["preset"] = preset
        COLORS.update(PRESETS.get(preset, PRESETS[DEFAULT_PRESET]))
    if colors:
        COLORS.update({k: v for k, v in colors.items() if k in ROLE_KEYS})
    if bg_image is not ...:
        _state["background"] = bg_image
    if opacity is not None:
        _state["card_opacity"] = max(20, min(100, int(opacity)))


def use_preset(name: str) -> None:
    apply(preset=name)


def reset_colors() -> None:
    """Zurueck auf die Farben der gewaehlten Vorlage, Bild und Deckkraft
    bleiben."""
    COLORS.update(PRESETS.get(_state["preset"], PRESETS[DEFAULT_PRESET]))


def snapshot() -> dict:
    return {
        "preset": _state["preset"],
        "colors": {k: COLORS[k] for k in ROLE_KEYS if k in COLORS},
        "background": _state["background"],
        "card_opacity": _state["card_opacity"],
    }


def restore(data: dict) -> None:
    if not isinstance(data, dict):
        return
    apply(preset=data.get("preset", DEFAULT_PRESET))
    colors = data.get("colors")
    if isinstance(colors, dict):
        apply(colors=colors)
    apply(bg_image=data.get("background"),
          opacity=data.get("card_opacity", 100))


def deviates_from_preset() -> bool:
    base = PRESETS.get(_state["preset"], {})
    return any(COLORS.get(k) != base.get(k) for k in ROLE_KEYS)


# ------------------------------------------------------------ Pfeilbilder

ARROWS = {
    "up": "3,7.5 6,4.5 9,7.5",
    "down": "3,4.5 6,7.5 9,4.5",
}


def _arrow_files() -> dict[str, str]:
    """Pfeile als SVG in der aktuellen Textfarbe ablegen.

    Qt zeichnet die Pfeile einer QSpinBox nicht mehr selbst, sobald das
    Widget per Stylesheet angefasst wird, und der aus CSS bekannte
    Dreieck-Trick ueber border funktioniert dort nicht. Es braucht also
    ein Bild — und weil die Farbe vom Thema abhaengt, wird es erzeugt.
    """
    try:
        target = paths.CACHE_DIR
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {}

    out = {}
    for name, points in ARROWS.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12">'
            f'<polyline points="{points}" fill="none" stroke="{COLORS["fg"]}"'
            ' stroke-width="1.6" stroke-linecap="round"'
            ' stroke-linejoin="round"/></svg>'
        )
        path = target / f"arrow-{name}.svg"
        try:
            if not path.exists() or path.read_text(encoding="utf-8") != svg:
                path.write_text(svg, encoding="utf-8")
        except OSError:
            return {}
        out[name] = str(path).replace("\\", "/")
    return out


# ------------------------------------------------------------ Stylesheet

def stylesheet() -> str:
    c = COLORS
    alpha = card_opacity() / 100.0
    # Ohne Hintergrundbild bleiben die Flaechen deckend; die Deckkraft
    # ergibt sonst nur ein flaues Grau statt Durchblick.
    card = c["bg2"] if background() is None else rgba(c["bg2"], alpha)
    inner = c["bg3"] if background() is None else rgba(c["bg3"], alpha)
    sidebar = c["sidebar"] if background() is None else rgba(c["sidebar"], alpha)

    arrows = _arrow_files()
    if arrows:
        arrow_rules = (
            "QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QDateEdit::up-arrow"
            ' { image: url("%s"); width: 12px; height: 12px; }\n'
            "QSpinBox::down-arrow, QDoubleSpinBox::down-arrow,"
            " QDateEdit::down-arrow, QComboBox::down-arrow"
            ' { image: url("%s"); width: 12px; height: 12px; }'
        ) % (arrows["up"], arrows["down"])
    else:
        arrow_rules = ""

    accent_text = contrast_text(c["accent"])
    accent_light = lighten(c["accent"], 0.35)
    hover = lighten(c["bg3"], 0.10)

    return f"""
QWidget {{ background: transparent; color: {c['fg']};
           font-family: "Noto Sans", "Segoe UI", sans-serif; font-size: 13px; }}
QMainWindow, QDialog {{ background: {c['bg']}; }}
QGroupBox {{ background: {card}; border: 1px solid {c['border']};
             border-radius: 8px; margin-top: 14px; padding: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px;
                    color: {c['dim']}; font-size: 11px;
                    text-transform: uppercase; letter-spacing: 1px; }}
QPushButton {{ background: {inner}; border: none; border-radius: 6px;
               padding: 8px 16px; font-weight: 600; color: {c['fg']}; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:disabled {{ color: {c['dim']}; background: {card}; }}
QPushButton#primary {{ background: {c['accent']}; color: {accent_text}; }}
QPushButton#record {{ background: {c['red']}; color: {c['fg']}; }}
QPushButton#help {{ font-size: 16px; padding: 6px 0; color: {c['accent']}; }}
QPushButton#rowaction, QPushButton#danger {{ padding: 5px 12px; font-weight: 500; }}
QPushButton#danger {{ background: {inner}; color: {c['red']}; }}
QPushButton#danger:hover {{ background: {c['red']}; color: {c['fg']}; }}
QPushButton#guided:checked {{ background: {accent_light}; color: {accent_text};
    font-weight: 700; border: 1px solid {c['accent']}; }}
QPushButton#guided:checked:hover {{ background: {lighten(c['accent'], 0.5)}; }}
QPushButton#langleft, QPushButton#langright {{ padding: 8px 0; font-size: 11px;
    background: {card}; color: {c['dim']}; border-radius: 0; }}
QPushButton#langleft {{ border-top-left-radius: 6px; border-bottom-left-radius: 6px; }}
QPushButton#langright {{ border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
QPushButton#langleft:checked, QPushButton#langright:checked {{
    background: {c['accent']}; color: {accent_text}; font-weight: 700; }}
QComboBox {{ background: {inner}; border: none; border-radius: 6px;
             padding: 7px 26px 7px 10px; min-width: 180px; color: {c['fg']}; }}
QComboBox QAbstractItemView {{ background: {c['bg2']}; color: {c['fg']};
                               selection-background-color: {c['bg3']}; }}
QLineEdit {{ background: {inner}; border: 1px solid {c['border']};
    border-radius: 5px; padding: 4px 6px; color: {c['fg']}; }}

/* Sobald eine QSpinBox per Stylesheet angefasst wird, zeichnet Qt die
   Pfeilfelder nicht mehr selbst an die richtige Stelle. Ohne die folgenden
   Regeln liegen sie ueber der Zahl — unter Linux faellt das je nach Stil
   nicht auf, unter Windows schon. */
QSpinBox, QDoubleSpinBox, QDateEdit {{ background: {inner};
    border: 1px solid {c['border']}; border-radius: 5px;
    padding: 4px 24px 4px 6px; color: {c['fg']}; min-height: 20px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 18px; height: 14px; margin: 1px 1px 0 0;
    background: {c['bg3']}; border: none;
    border-top-right-radius: 4px; }}
QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 18px; height: 14px; margin: 0 1px 1px 0;
    background: {c['bg3']}; border: none;
    border-bottom-right-radius: 4px; }}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover,
QDateEdit::up-button:hover, QDateEdit::down-button:hover {{
    background: {c['accent']}; }}
{arrow_rules}

/* Dasselbe gilt fuer das Aufklappfeld der Auswahllisten. */
QComboBox::drop-down {{ subcontrol-origin: padding;
    subcontrol-position: center right; width: 20px; border: none;
    border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
QComboBox::drop-down:hover {{ background: {c['bg3']}; }}
QTextEdit, QPlainTextEdit, QTableWidget {{ background: {card};
    border: 1px solid {c['border']}; border-radius: 8px; color: {c['fg']}; }}
QHeaderView::section {{ background: {c['bg3']}; border: none; padding: 6px;
                        color: {c['fg']}; }}
QTableWidget {{ gridline-color: {c['border']}; }}
QTableWidget::item:selected {{ background: {c['accent']}; color: {accent_text}; }}
QTabBar::tab {{ background: {sidebar}; padding: 9px 20px; color: {c['dim']};
                border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {c['bg3']}; color: {c['accent']}; }}
QTabWidget::pane {{ border: none; }}
QStatusBar {{ color: {c['dim']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px;
                               min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; }}
QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 5px; }}
QMenu {{ background: {c['bg2']}; color: {c['fg']};
         border: 1px solid {c['border']}; }}
QMenu::item:selected {{ background: {c['bg3']}; }}
QCheckBox, QLabel, QRadioButton {{ color: {c['fg']}; }}
QToolTip {{ background: {c['bg2']}; color: {c['fg']};
            border: 1px solid {c['border']}; padding: 4px; }}
QProgressBar {{ background: {c['bg']}; border: none; border-radius: 5px; }}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 5px; }}
QSlider::groove:horizontal {{ background: {c['bg3']}; height: 4px;
                              border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {c['accent']}; width: 14px;
                              margin: -5px 0; border-radius: 7px; }}
"""


def window_background_style() -> str:
    """Eigener Block fuers Hintergrundbild, sonst erbt es jedes Kindwidget."""
    path = background()
    if not path:
        return f"QMainWindow {{ background: {COLORS['bg']}; }}"
    escaped = str(path).replace("\\", "/")
    return (f'QMainWindow {{ background-color: {COLORS["bg"]};'
            f' background-image: url("{escaped}");'
            " background-position: center; background-repeat: no-repeat; }")
