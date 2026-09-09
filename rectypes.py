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

import re
from dataclasses import dataclass

import i18n

# Schluessel eigener Typen. Der Teil dahinter ist das Kuerzel, das auch im
# Dateinamen steht — es wird einmal beim Anlegen aus dem Namen gebildet und
# aendert sich danach nicht mehr. Nur so bleibt eine vor Wochen
# aufgenommene Datei ihrem Typ zugeordnet, auch wenn der Name laengst ein
# anderer ist.
USER_PREFIX = "user:"

MAX_NAME = 40
MAX_SLUG = 24


@dataclass(frozen=True)
class RecordingType:
    key: str
    seconds: float | None = None      # empfohlene Laenge fuer gehaltene Laute
    sustained: bool = False           # gehaltener Laut, Mitte ausschneidbar
    name: str = ""                    # nur bei eigenen: der eingetippte Name

    @property
    def label(self) -> str:
        # Eigene Typen heissen so, wie sie genannt wurden, und zwar in
        # jeder Sprache — uebersetzt ist an ihnen nichts.
        return self.name or i18n.t(f"type_{self.key}")

    @property
    def hint(self) -> str:
        if self.name:
            return i18n.t("type_user_hint")
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

# Kuerzel fuer den Dateinamen. Bewusst fest und englisch: die uebersetzte
# Beschriftung waere nach einem Sprachwechsel eine andere, und dann hiessen
# gleichartige Aufnahmen im Ordner unterschiedlich.
SLUGS = {
    "reading": "reading",
    "hum": "hum",
    "vowel_a": "vowel-a",
    "vowel_i": "vowel-i",
    "vowel_u": "vowel-u",
    "free": "free",
}

# Empfohlene Reihenfolge fuer die erste Runde: Tonhoehentest, dann die drei
# Vokale. Alle vier sind gehaltene Laute und damit die Aufnahmen, aus denen
# ueber Wochen vergleichbare Formant- und Stabilitaetswerte entstehen.
RECOMMENDED = ["hum", "vowel_a", "vowel_i", "vowel_u"]


def _stored() -> dict[str, str]:
    """Die eigenen Typen aus der Konfiguration: Kuerzel -> Name.

    Der Import steht absichtlich hier drin und nicht oben: settings holt
    sich naming, und naming holt sich dieses Modul. Ein Import auf
    Modulebene machte daraus einen Ring, der davon abhinge, wer zuerst
    geladen wird.
    """
    import settings
    return settings.get_user_types()


# ------------------------------------------------------------ Namen, Kuerzel

_NOT_SLUG = re.compile(r"[^a-z0-9]+")


def clean_name(raw: str) -> str:
    """Zeilenumbrueche und doppelte Leerzeichen raus, dann kuerzen."""
    return " ".join(str(raw or "").split())[:MAX_NAME]


def make_slug(name: str, taken: set[str] | None = None) -> str:
    """Das feste Kuerzel zu einem Namen, einmalig beim Anlegen.

    Nur Kleinbuchstaben, Ziffern und Bindestriche: das Kuerzel landet im
    Dateinamen, und der Unterstrich trennt dort die Bausteine — ein
    Kuerzel mit Unterstrich zerlegte sich spaeter in zwei.

    Ist es schon vergeben, haengt eine Nummer dran. Zwei verschiedene
    Namen koennen zum selben Kuerzel fuehren ("Mein Typ" und "mein-typ"),
    und zwei Typen mit demselben Kuerzel waeren im Ordner nicht mehr
    auseinanderzuhalten.
    """
    base = _NOT_SLUG.sub("-", clean_name(name).lower()).strip("-")
    base = base[:MAX_SLUG].strip("-") or "typ"
    used = set(taken) if taken is not None else all_slugs()
    slug_out, number = base, 2
    while slug_out in used:
        slug_out = f"{base}-{number}"
        number += 1
    return slug_out


# --------------------------------------------------------------- Zugriff

def is_user(key: str | None) -> bool:
    return str(key or "").startswith(USER_PREFIX)


def slug_of(key: str | None) -> str:
    """Der Kuerzel-Teil eines eigenen Schluessels."""
    return str(key)[len(USER_PREFIX):] if is_user(key) else ""


def user_types() -> list[RecordingType]:
    """Die eigenen Typen, nach Namen sortiert."""
    return [RecordingType(USER_PREFIX + code, name=name)
            for code, name in sorted(_stored().items(),
                                     key=lambda item: item[1].lower())]


def all_types() -> list[RecordingType]:
    """Eingebaute Typen, danach die eigenen.

    Statt der Konstanten TYPES ueberall dort zu verwenden, wo eine Liste
    zur Auswahl gestellt wird: die eigenen koennen sich zwischen zwei
    Aufrufen geaendert haben.
    """
    return TYPES + user_types()


def all_slugs() -> set[str]:
    """Jedes Kuerzel, das im Dateinamen vorkommen kann."""
    return set(SLUGS.values()) | set(_stored())


def get(key: str | None) -> RecordingType:
    """Der Typ zu einem Schluessel, notfalls der Standardtyp.

    Ein Schluessel aus einer alten Aufnahme kann auf einen geloeschten
    eigenen Typ zeigen. Fuers Verhalten ist der Standardtyp dann die
    richtige Antwort — fuer die Beschriftung nicht, siehe label().
    """
    if is_user(key):
        for kind in user_types():
            if kind.key == key:
                return kind
        return BY_KEY[DEFAULT]
    return BY_KEY.get(key or DEFAULT, BY_KEY[DEFAULT])


def exists(key: str | None) -> bool:
    return any(kind.key == key for kind in all_types())


def label(key: str | None) -> str:
    """Beschriftung eines Typs.

    Bei einem geloeschten eigenen Typ steht hier sein Kuerzel. Es ist das,
    was im Dateinamen der betroffenen Aufnahmen steht — und ehrlicher, als
    sie in der Liste stumm als Lesetext zu fuehren.
    """
    if is_user(key) and not exists(key):
        return slug_of(key)
    return get(key).label


def slug(key: str | None) -> str:
    """Kuerzel fuer den Dateinamen."""
    if is_user(key):
        return slug_of(key)
    return SLUGS.get(get(key).key, SLUGS[DEFAULT])
