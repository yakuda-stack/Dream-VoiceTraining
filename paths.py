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

"""Ablageorte.

Linux, nach XDG Base Directory Specification:
    Konfiguration   $XDG_CONFIG_HOME/dream-voicetraining/config.json
    Aufnahmen       $XDG_DATA_HOME/dream-voicetraining/sessions/
Fallbacks sind ~/.config und ~/.local/share.

Windows:
    Konfiguration   %APPDATA%\\Dream-VoiceTraining\\config.json
    Aufnahmen       %LOCALAPPDATA%\\Dream-VoiceTraining\\sessions\\

Die Aufnahmen liegen dort bewusst im lokalen Zweig: bei einem
servergespeicherten Profil wanderten sonst hunderte WAV-Dateien bei jeder
An- und Abmeldung durchs Netz.

DREAM_VOICETRAINING_HOME ueberschreibt beides mit einem gemeinsamen Ordner,
praktisch fuer Tests und portable Varianten.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

WINDOWS = sys.platform.startswith("win")
# PyInstaller entpackt die Beigaben in einen temporaeren Ordner.
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else None

APP_ID = "dream-voicetraining"
APP_NAME = "Dream-VoiceTraining"
APP_VERSION = "1.0.3"

APP_URL = "https://github.com/yakuda-stack/Dream-VoiceTraining"
ISSUES_URL = APP_URL + "/issues"
DISCORD_URL = "https://discord.gg/UkhJSz3Ctf"
KOFI_URL = "https://ko-fi.com/yakuda_"


def set_process_name(name: str = APP_ID) -> None:
    """Damit im Systemmonitor nicht "python3" steht.

    setproctitle aendert die vollstaendige Kommandozeile. Fehlt das Paket,
    setzt prctl wenigstens den Kurznamen (comm), der auf 15 Zeichen begrenzt
    ist und den die meisten Monitore anzeigen.
    """
    if WINDOWS:
        # Dort traegt die EXE den Namen, im Taskmanager steht er ohnehin.
        return

    try:
        import setproctitle
        setproctitle.setproctitle(name)
        return
    except Exception:
        pass

    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        PR_SET_NAME = 15
        libc.prctl(PR_SET_NAME, ctypes.c_char_p(name[:15].encode()), 0, 0, 0)
    except Exception:
        pass


def icon_file() -> Path | None:
    """Programmsymbol suchen, egal ob aus dem Quellordner oder installiert."""
    candidates = []
    if BUNDLE_DIR is not None:
        candidates += [BUNDLE_DIR / f"{APP_ID}.ico",
                       BUNDLE_DIR / f"{APP_ID}.svg"]
    candidates += [
        Path(__file__).resolve().parent / "packaging" / f"{APP_ID}.ico",
        Path(__file__).resolve().parent / "packaging" / f"{APP_ID}.svg",
        Path(f"/usr/share/icons/hicolor/scalable/apps/{APP_ID}.svg"),
        Path.home() / ".local/share/icons/hicolor/scalable/apps" / f"{APP_ID}.svg",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None

ENV_OVERRIDE = "DREAM_VOICETRAINING_HOME"

# Frueher benutzte Orte, aus denen beim Start uebernommen wird.
LEGACY_APP_IDS = ("voicetfy",)


def _xdg(var: str, default: str) -> Path:
    base = os.environ.get(var)
    return (Path(base) if base else Path.home() / default).expanduser()


def _windows_dir(variable: str, fallback: str) -> Path:
    base = os.environ.get(variable)
    return Path(base) if base else Path.home() / "AppData" / fallback


def _roots() -> tuple[Path, Path]:
    override = os.environ.get(ENV_OVERRIDE)
    if override:
        root = Path(override).expanduser()
        return root, root
    if WINDOWS:
        return (_windows_dir("APPDATA", "Roaming") / APP_NAME,
                _windows_dir("LOCALAPPDATA", "Local") / APP_NAME)
    return (_xdg("XDG_CONFIG_HOME", ".config") / APP_ID,
            _xdg("XDG_DATA_HOME", ".local/share") / APP_ID)


CONFIG_DIR, DATA_DIR = _roots()
SESSION_DIR = DATA_DIR / "sessions"
BACKGROUND_DIR = DATA_DIR / "backgrounds"
CONFIG_PATH = CONFIG_DIR / "config.json"
SESSION_INDEX = SESSION_DIR / "sessions.json"


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)


def _adopt_file(source: Path, target: Path, moved: list[str]) -> None:
    if source.is_file() and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        moved.append(target.name)


def _adopt_dir(source: Path, target: Path, moved: list[str]) -> None:
    if not source.is_dir():
        return
    target.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if item.is_file():
            _adopt_file(item, target / item.name, moved)
    try:
        source.rmdir()
    except OSError:
        pass


def migrate_from(app_dir: Path) -> list[str]:
    """Altbestand einsammeln: neben dem Programm und aus frueheren App-IDs.

    Vorhandene Dateien am Ziel werden nie ueberschrieben.
    """
    moved: list[str] = []
    ensure_dirs()

    # 1) Direkt neben dem Programm (frueheste Variante)
    _adopt_file(app_dir / "config.json", CONFIG_PATH, moved)
    _adopt_dir(app_dir / "sessions", SESSION_DIR, moved)

    # 2) Frueher benutzte App-IDs unter XDG
    for legacy in LEGACY_APP_IDS:
        for base in (_xdg("XDG_CONFIG_HOME", ".config"),
                     _xdg("XDG_DATA_HOME", ".local/share")):
            old = base / legacy
            if not old.is_dir() or old in (CONFIG_DIR, DATA_DIR):
                continue
            _adopt_file(old / "config.json", CONFIG_PATH, moved)
            _adopt_dir(old / "sessions", SESSION_DIR, moved)
            try:
                old.rmdir()
            except OSError:
                pass
    return moved
