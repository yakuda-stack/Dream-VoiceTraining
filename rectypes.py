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

"""Aufnahmetypen.

Ein fester Typ je Aufnahme statt freier Namen. Nur so lassen sich spaeter
Werte vergleichen, die dasselbe messen — ein Lesetext und ein gehaltenes
/a/ ergeben voellig verschiedene Formanten, ohne dass sich die Stimme
geaendert haette.
"""

from __future__ import annotations

from dataclasses import dataclass

import i18n


@dataclass(frozen=True)
class RecordingType:
    key: str
    seconds: float | None = None      # empfohlene Laenge fuer gehaltene Laute
    sustained: bool = False           # gehaltener Laut, Mitte ausschneidbar

    @property
    def label(self) -> str:
        return i18n.t(f"type_{self.key}")

    @property
    def hint(self) -> str:
        return i18n.t(f"type_{self.key}_hint")


TYPES = [
    RecordingType("reading"),
    RecordingType("hum", seconds=4.0, sustained=True),
    RecordingType("vowel_a", seconds=3.0, sustained=True),
    RecordingType("vowel_i", seconds=3.0, sustained=True),
    RecordingType("vowel_u", seconds=3.0, sustained=True),
    RecordingType("free"),
]

BY_KEY = {t.key: t for t in TYPES}
DEFAULT = "reading"

# Empfohlene Reihenfolge fuer die erste Runde: Tonhoehentest, dann die drei
# Vokale. Alle vier sind gehaltene Laute und damit die Aufnahmen, aus denen
# ueber Wochen vergleichbare Formant- und Stabilitaetswerte entstehen.
RECOMMENDED = ["hum", "vowel_a", "vowel_i", "vowel_u"]


def get(key: str | None) -> RecordingType:
    return BY_KEY.get(key or DEFAULT, BY_KEY[DEFAULT])


def label(key: str | None) -> str:
    return get(key).label
