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

"""Uebungstexte zur Auswahl.

Der eingebaute Text steht in i18n und wechselt mit der Sprache mit.
Eigene Texte tun das nicht: sie liegen so in der Konfiguration, wie sie
eingetippt wurden, und eine Umschaltung auf Englisch soll den deutschen
Text nicht verschwinden lassen.

Aufbau wie bei den Zielprofilen in targets.py — ein Schluessel je Eintrag,
eigene mit dem Praefix "user:" davor. Der Name allein taugte nicht als
Schluessel: jemand koennte seinen Text "builtin" nennen.
"""

from __future__ import annotations

import i18n
import settings

BUILTIN = "builtin"
USER_PREFIX = "user:"

# Genug fuer eine Beschreibung, zu wenig, um die Auswahlliste zu sprengen.
MAX_NAME = 60


def keys() -> list[str]:
    """Erst der eingebaute Text, dann die eigenen in Namensfolge."""
    return [BUILTIN] + [USER_PREFIX + name
                        for name in sorted(settings.get_practice_texts())]


def is_user(key: str | None) -> bool:
    return str(key or "").startswith(USER_PREFIX)


def name_of(key: str | None) -> str:
    """Der Name eines eigenen Textes. Beim eingebauten leer."""
    return str(key)[len(USER_PREFIX):] if is_user(key) else ""


def label(key: str | None) -> str:
    return name_of(key) if is_user(key) else i18n.t("practice_builtin")


def body(key: str | None) -> str:
    """Der Text selbst.

    Ein Schluessel aus der Konfiguration kann auf etwas zeigen, das es
    nicht mehr gibt — geloescht, oder von Hand aus der config.json
    entfernt. Dann ist der eingebaute Text die richtige Antwort, nicht
    ein leeres Feld.
    """
    if is_user(key):
        stored = settings.get_practice_texts().get(name_of(key))
        if stored is not None:
            return stored
    return i18n.t("practice_body")


def resolve(key: str | None) -> str:
    """Den Schluessel auf einen zurechtruecken, den es wirklich gibt."""
    return key if key in keys() else BUILTIN


def clean_name(raw: str) -> str:
    """Zeilenumbrueche und doppelte Leerzeichen raus, dann kuerzen.

    Der Name landet in einer Auswahlliste; ein Zeilenumbruch darin
    zerrisse die Zeile.
    """
    return " ".join(str(raw or "").split())[:MAX_NAME]
