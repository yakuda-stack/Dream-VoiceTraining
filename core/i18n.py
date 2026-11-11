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

"""Sprachumschaltung ueber Sprachdateien im Ordner ``locales/``.

Jede Datei ``<code>.json`` ist eine Sprache. Aufbau::

    {
      "lang": "DE",              Kuerzel, wird kleingeschrieben zum Code
      "name": "Deutsch",         steht so im Sprach-Dropdown
      "strings": {...},          Texte der Oberflaeche, Schluessel -> Text
      "help_sections": {...},    Ueberschriften der Hilfe
      "help_topics": {...}       Hilfethemen: title, body, keywords
    }

Jede Datei im Ordner landet automatisch im Dropdown. Fehlt in einer Sprache
ein Text, wird der englische genommen. Zusaetzlich wird
``~/.config/dream-voicetraining/locales/`` gelesen: dort abgelegte Dateien
ergaenzen oder ueberschreiben die mitgelieferten, ohne neu zu bauen.

Neue Texte in ``locales/en.json`` (und den anderen) eintragen und im UI
ueber t("key") verwenden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT = "en"
LANG = DEFAULT
LANGUAGES: tuple[str, ...] = ()

# Schluessel -> {Code -> Text}. Gleiche Form wie frueher, damit bestehender
# Code (und die Tests) unveraendert darauf zugreifen koennen.
STRINGS: dict[str, dict[str, str]] = {}
HELP_SECTIONS: dict[str, dict[str, str]] = {}
HELP_TOPICS: dict[str, dict[str, dict[str, str]]] = {}
NAMES: dict[str, str] = {}

FOLDER = "locales"


def locale_dirs() -> list[Path]:
    """Alle Ordner mit Sprachdateien, spaetere ueberschreiben fruehere."""
    folders = []
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        folders.append(Path(bundle) / FOLDER)
    folders.append(Path(__file__).resolve().parents[1] / FOLDER)
    try:
        from core.paths import CONFIG_DIR
        folders.append(CONFIG_DIR / FOLDER)
    except Exception:
        pass
    seen, unique = set(), []
    for folder in folders:
        if folder not in seen:
            seen.add(folder)
            unique.append(folder)
    return unique


def _note(message: str) -> None:
    try:
        from core import debuglog
        debuglog.record_note("i18n", message)
    except Exception:
        pass


def _read(path: Path) -> tuple[str, dict] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _note(f"{path.name} nicht lesbar: {exc}")
        return None
    if not isinstance(data, dict):
        _note(f"{path.name}: kein JSON-Objekt")
        return None
    code = str(data.get("lang") or path.stem).strip().lower()
    return (code, data) if code else None


def load(folders: list[Path] | None = None) -> None:
    """Alle Sprachdateien (neu) einlesen."""
    global LANGUAGES
    STRINGS.clear()
    HELP_SECTIONS.clear()
    HELP_TOPICS.clear()
    NAMES.clear()

    for folder in folders if folders is not None else locale_dirs():
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            found = _read(path)
            if found is None:
                continue
            code, data = found
            NAMES[code] = str(data.get("name") or NAMES.get(code)
                              or code.upper())
            for key, text in (data.get("strings") or {}).items():
                STRINGS.setdefault(key, {})[code] = str(text)
            for key, text in (data.get("help_sections") or {}).items():
                HELP_SECTIONS.setdefault(key, {})[code] = str(text)
            for key, topic in (data.get("help_topics") or {}).items():
                if isinstance(topic, dict):
                    entry = HELP_TOPICS.setdefault(key, {})
                    for part, text in topic.items():
                        entry.setdefault(part, {})[code] = str(text)

    # Englisch zuerst, der Rest nach Anzeigename.
    codes = sorted(NAMES, key=lambda c: (c != DEFAULT, NAMES[c].lower()))
    LANGUAGES = tuple(codes)


def available() -> list[tuple[str, str]]:
    """(Code, Anzeigename) fuer das Dropdown."""
    return [(code, NAMES[code]) for code in LANGUAGES]


def language_name(code: str) -> str:
    return NAMES.get(code, code.upper())


def set_language(code: str) -> None:
    global LANG
    if code in LANGUAGES:
        LANG = code


def pick(entry: dict | None, fallback: str = "") -> str:
    """Text in der aktuellen Sprache aus {Code -> Text}, sonst Englisch."""
    if not entry:
        return fallback
    return entry.get(LANG) or entry.get(DEFAULT) or fallback


def t(key: str, **kwargs) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = pick(entry, key)
    return text.format(**kwargs) if kwargs else text


load()
