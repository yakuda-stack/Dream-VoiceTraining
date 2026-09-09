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

"""Das Namensschema: woraus ein Dateiname besteht und in welcher Reihenfolge.

Ein Schema ist ein einfaches dict, damit es unveraendert in der config.json
landen kann. Es besteht aus drei Teilen:

    subfolders   Unterordner je Tag, Kalenderwoche, Monat, Jahr — oder keiner
    order        alle Bausteine in ihrer Reihenfolge, auch die abgeschalteten
    enabled      welche Bausteine davon tatsaechlich im Namen stehen

"order" fuehrt bewusst auch die abgeschalteten Bausteine mit. Sonst
verloere ein Baustein seinen Platz, sobald er einmal aus war, und landete
beim Wiedereinschalten am Ende statt dort, wo er hingehoert.

Alle erzeugten Bestandteile sind sprachunabhaengig — auch "KW" fuer die
Kalenderwoche. Uebersetzte Bestandteile hiessen nach einem Sprachwechsel
anders als die bereits gespeicherten Dateien, und dann zeigte die
Sessionliste auf Namen, die es so nicht mehr gibt.

Der Trenner ist fest der Unterstrich, und in den Bausteinen selbst kommt er
nicht vor: Datum und Uhrzeit trennen mit Bindestrich. Dadurch laesst sich
ein fertiger Name spaeter wieder in seine Bausteine zerlegen — das braucht
der Umzug in storage.py, um selbst vergebene Namen zu erkennen und in Ruhe
zu lassen.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import rectypes

SEPARATOR = "_"

# Reihenfolge hier ist die Vorgabe, nicht die einzig moegliche.
BLOCKS = ("prefix", "year", "month", "day", "week", "date", "time", "type",
          "counter", "suffix")

# Freitext-Bausteine. Sie liefern nur etwas, wenn auch etwas eingetippt ist.
TEXT_BLOCKS = ("prefix", "suffix")

SUBFOLDERS = ("none", "day", "week", "month", "year")

# Bausteine fuer den Ordnernamen. Eine eigene Liste, weil ein Ordner
# andere Sachen braucht als eine Datei: keinen Zaehler, keinen Aufnahmetyp,
# dafuer die Spanne einer Kalenderwoche ("07.09-13.09").
FOLDER_BLOCKS = ("year", "month", "day", "date", "week", "weekrange", "text")
FOLDER_MODES = ("period", "blocks")

# Ordner duerfen Leerzeichen tragen, Dateinamen in diesem Programm nicht.
# Deshalb hier ein anderer Trenner als SEPARATOR.
FOLDER_SEPARATOR = " "
RESETS = ("never", "day", "week", "month", "year")

MIN_DIGITS, MAX_DIGITS = 1, 6
MAX_TEXT = 40

# Was ohne Zutun herauskommt: 2026-03-14_09-05-00.wav, also genau das
# Schema der Fassungen bis 1.1.1. Wer nie in die Optionen schaut, merkt
# vom ganzen Umbau nichts.
DEFAULT: dict = {
    "subfolders": "none",
    "folder": {"mode": "period",
               "order": list(FOLDER_BLOCKS),
               # Nur wirksam, wenn mode "blocks" ist. Die Vorbelegung
               # ergibt "KW37 07.09-13.09" — die Form, in der Wochenordner
               # ueblicherweise von Hand angelegt werden.
               "enabled": {"week": True, "weekrange": True},
               "text": ""},
    "order": list(BLOCKS),
    "enabled": {"date": True, "time": True},
    "prefix": "",
    "suffix": "",
    "seconds": True,
    "counter_digits": 3,
    "counter_reset": "never",
}


# --------------------------------------------------------------- Freitext

# Alles, was unter Windows im Dateinamen verboten ist, dazu der Trenner
# selbst und der Schraegstrich: ein Freitext darf keinen Unterordner
# aufmachen und das Zerlegen in Bausteine nicht kaputtmachen.
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f_]+')
_SPACES = re.compile(r"\s+")


def clean_text(raw: str) -> str:
    """Freitext auf das eindampfen, was als Dateiname unbedenklich ist."""
    text = _SPACES.sub("-", str(raw or "").strip())
    text = _FORBIDDEN.sub("-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-. ")
    return text[:MAX_TEXT]


# Fuer Namen, die von aussen kommen — beim Import. Anders als oben bleiben
# Leerzeichen und Unterstriche stehen: ein uebernommener Name soll
# aussehen wie vorher und nicht wie ein erzeugter. Entfernt wird nur, was
# als Dateiname verboten ist oder einen Unterordner aufmachen wuerde.
_FORBIDDEN_STEM = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
MAX_STEM = 80


def clean_stem(raw: str) -> str:
    """Einen uebernommenen Dateinamen auf das Unbedenkliche eindampfen.

    Kommt nichts Brauchbares heraus — ein Name nur aus Punkten etwa —,
    ist das Ergebnis leer, und der Aufrufer vergibt einen eigenen Namen.
    """
    text = _FORBIDDEN_STEM.sub("-", str(raw or ""))
    text = _SPACES.sub(" ", text).strip(". ")
    return text[:MAX_STEM].strip(". ")


# ----------------------------------------------------------- Zeitbausteine

def _week(stamp: datetime) -> tuple[int, int]:
    """ISO-Jahr und Kalenderwoche.

    Das ISO-Jahr statt stamp.year, weil der 1. Januar noch zur letzten
    Woche des Vorjahres gehoeren kann. Sonst lagen zwei verschiedene Wochen
    im selben Ordner.
    """
    iso = stamp.isocalendar()
    return iso[0], iso[1]


def _time_part(stamp: datetime, seconds: bool) -> str:
    return stamp.strftime("%H-%M-%S" if seconds else "%H-%M")


def week_range(stamp: datetime) -> str:
    """Montag bis Sonntag der Woche, als "07.09-13.09"."""
    monday = stamp - timedelta(days=stamp.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday:%d.%m}-{sunday:%d.%m}"


def folder_block_value(key: str, scheme: dict, stamp: datetime) -> str:
    """Was ein einzelner Ordnerbaustein beitraegt."""
    if key == "text":
        return clean_stem(scheme.get("folder", {}).get("text", ""))[:MAX_TEXT]
    if key == "year":
        return stamp.strftime("%Y")
    if key == "month":
        return stamp.strftime("%m")
    if key == "day":
        return stamp.strftime("%d")
    if key == "date":
        return stamp.strftime("%Y-%m-%d")
    if key == "week":
        return f"KW{_week(stamp)[1]:02d}"
    if key == "weekrange":
        return week_range(stamp)
    return ""


def period_key(kind: str, stamp: datetime) -> str:
    """Bezeichner des Zeitraums — fuer Unterordner und Zaehler dasselbe."""
    if kind == "day":
        return stamp.strftime("%Y-%m-%d")
    if kind == "week":
        year, week = _week(stamp)
        return f"{year}-KW{week:02d}"
    if kind == "month":
        return stamp.strftime("%Y-%m")
    if kind == "year":
        return stamp.strftime("%Y")
    return ""


# ----------------------------------------------------------------- Schema

def normalize(raw: dict | None) -> dict:
    """Ein Schema aus der Konfiguration auf gueltige Werte bringen.

    Die config.json ist eine Textdatei, die jeder aufmachen kann. Ein
    Tippfehler darin darf nicht dazu fuehren, dass keine Aufnahme mehr
    einen Namen bekommt.
    """
    raw = raw if isinstance(raw, dict) else {}
    scheme = dict(DEFAULT)

    folders = raw.get("subfolders")
    scheme["subfolders"] = folders if folders in SUBFOLDERS else "none"

    raw_folder = raw.get("folder")
    raw_folder = raw_folder if isinstance(raw_folder, dict) else {}
    mode = raw_folder.get("mode")
    folder_order = [key for key in raw_folder.get("order", [])
                    if key in FOLDER_BLOCKS]
    gesehen: list[str] = []
    for key in folder_order:
        if key not in gesehen:
            gesehen.append(key)
    folder_enabled = raw_folder.get("enabled")
    folder_enabled = folder_enabled if isinstance(folder_enabled, dict) else {}
    scheme["folder"] = {
        "mode": mode if mode in FOLDER_MODES else "period",
        "order": gesehen + [key for key in FOLDER_BLOCKS if key not in gesehen],
        "enabled": {key: bool(folder_enabled.get(
            key, DEFAULT["folder"]["enabled"].get(key, False)))
            for key in FOLDER_BLOCKS},
        "text": clean_stem(raw_folder.get("text", ""))[:MAX_TEXT],
    }

    reset = raw.get("counter_reset")
    scheme["counter_reset"] = reset if reset in RESETS else "never"

    order = [key for key in raw.get("order", []) if key in BLOCKS]
    # Doppelte raus, Fehlende hinten dran: die Liste muss jeden Baustein
    # genau einmal enthalten, sonst verschwindet einer aus der Oberflaeche.
    seen: list[str] = []
    for key in order:
        if key not in seen:
            seen.append(key)
    scheme["order"] = seen + [key for key in BLOCKS if key not in seen]

    enabled = raw.get("enabled")
    enabled = enabled if isinstance(enabled, dict) else {}
    scheme["enabled"] = {key: bool(enabled.get(key, DEFAULT["enabled"].get(key, False)))
                         for key in BLOCKS}

    scheme["prefix"] = clean_text(raw.get("prefix", ""))
    scheme["suffix"] = clean_text(raw.get("suffix", ""))
    scheme["seconds"] = bool(raw.get("seconds", True))

    try:
        digits = int(raw.get("counter_digits", 3))
    except (TypeError, ValueError):
        digits = 3
    scheme["counter_digits"] = min(max(digits, MIN_DIGITS), MAX_DIGITS)
    return scheme


def from_legacy(month_folders: bool, type_in_name: bool) -> dict:
    """Schema aus den zwei Schaltern der Fassungen bis 1.1.1."""
    scheme = normalize(None)
    if month_folders:
        scheme["subfolders"] = "month"
    if type_in_name:
        scheme["enabled"]["type"] = True
    return scheme


def with_legacy(scheme: dict, month: bool | None = None,
                typed: bool | None = None) -> dict:
    """Schema mit den alten Schaltern uebersteuern.

    Nur fuer Aufrufer, die bewusst ein anderes Schema durchrechnen wollen
    als das eingestellte — die Vorschau tut das, und die Tests tun es auch.
    """
    if month is None and typed is None:
        return scheme
    out = normalize(scheme)
    if month is not None:
        out["subfolders"] = "month" if month else "none"
    if typed is not None:
        out["enabled"] = {**out["enabled"], "type": bool(typed)}
    return out


# ------------------------------------------------------------- Zusammenbau

def block_value(key: str, scheme: dict, stamp: datetime,
                type_key: str | None, counter: int) -> str:
    """Was ein einzelner Baustein beitraegt. Leer heisst: faellt weg."""
    if key == "prefix":
        return scheme.get("prefix", "")
    if key == "suffix":
        return scheme.get("suffix", "")
    if key == "year":
        return stamp.strftime("%Y")
    if key == "month":
        # Nur die Monatszahl. Das Jahr hat einen eigenen Baustein — beides
        # hier hineinzupacken hiesse, dass "Jahr" und "Monat" zusammen
        # 2026_2026-03 ergaeben.
        return stamp.strftime("%m")
    if key == "day":
        # Aus demselben Grund nur der Tag: Jahr, Monat und Tag zusammen
        # ergeben, was sonst "Datum" liefert, aber einzeln abwaehlbar.
        return stamp.strftime("%d")
    if key == "week":
        return f"KW{_week(stamp)[1]:02d}"
    if key == "date":
        return stamp.strftime("%Y-%m-%d")
    if key == "time":
        return _time_part(stamp, bool(scheme.get("seconds", True)))
    if key == "type":
        return rectypes.slug(type_key)
    if key == "counter":
        return str(int(counter)).zfill(int(scheme.get("counter_digits", 3)))
    return ""


def build_stem(scheme: dict, stamp: datetime, type_key: str | None = None,
               counter: int = 1) -> str:
    """Der Dateiname ohne Endung und ohne Unterordner."""
    scheme = normalize(scheme)
    parts = []
    for key in scheme["order"]:
        if not scheme["enabled"].get(key):
            continue
        value = block_value(key, scheme, stamp, type_key, counter)
        if value:
            parts.append(value)
    # Wer alle Bausteine abschaltet, bekaeme sonst eine Datei, die nur
    # ".wav" heisst — und die zweite hiesse genauso.
    return SEPARATOR.join(parts) or stamp.strftime("%Y-%m-%d_%H-%M-%S")


def build_folder(scheme: dict, stamp: datetime) -> str:
    """Der Unterordner, oder leer.

    Zwei Betriebsarten: entweder ein fertiger Zeitraum wie bisher, oder ein
    Name aus Bausteinen — dieselbe Idee wie beim Dateinamen, nur mit
    Leerzeichen als Trenner, weil Ordner welche tragen duerfen.
    """
    scheme = normalize(scheme)
    folder = scheme["folder"]
    if folder["mode"] != "blocks":
        return period_key(scheme["subfolders"], stamp)
    parts = [folder_block_value(key, scheme, stamp)
             for key in folder["order"] if folder["enabled"].get(key)]
    return FOLDER_SEPARATOR.join(part for part in parts if part).strip()


def relative(scheme: dict, stamp: datetime, type_key: str | None = None,
             counter: int = 1, suffix: str = ".wav",
             stem: str | None = None) -> str:
    """Vollstaendiger Name relativ zum Aufnahmeordner.

    Ein uebergebener stem gewinnt: so behaelt eine selbst umbenannte
    Aufnahme ihren Namen und wandert trotzdem in den richtigen Ordner.
    """
    name = (stem if stem is not None
            else build_stem(scheme, stamp, type_key, counter)) + suffix
    folder = build_folder(scheme, stamp)
    return f"{folder}/{name}" if folder else name


def uses_counter(scheme: dict) -> bool:
    return bool(normalize(scheme)["enabled"].get("counter"))


# ------------------------------------------------------ Erzeugte erkennen

# Muster der Bausteine, sprachunabhaengig und ohne Unterstrich. Fuer den
# Umzug: nur was hierdurch vollstaendig beschrieben wird, gilt als selbst
# erzeugt und darf umbenannt werden.
_TOKEN_TIME = (
    r"\d{4}-\d{2}-\d{2}",     # Datum
    r"\d{4}-\d{2}",           # Monat der Fassungen bis 1.1.2
    r"\d{4}",                 # Jahr
    r"(?:0[1-9]|[12]\d|3[01])",  # Monat oder Tag — nur 01 bis 31, damit
                                 # eine selbst "42" genannte Datei nicht
                                 # als erzeugt gilt
    r"KW\d{2}",               # Kalenderwoche
    r"\d{2}-\d{2}(?:-\d{2})?",  # Uhrzeit
)
_TIMEISH = re.compile("(?:" + "|".join(_TOKEN_TIME) + r")\Z")
_COUNTER = re.compile(r"\d{1,6}\Z")


def _known_token(token: str, texts: set[str]) -> bool:
    if token in texts or token in rectypes.all_slugs():
        return True
    return bool(_TIMEISH.match(token) or _COUNTER.match(token))


def looks_generated(stem: str, scheme: dict | None = None) -> bool:
    """Ob dieser Name von der Aufnahme selbst vergeben wurde.

    Geprueft wird gegen die Bausteine allgemein, nicht gegen das gerade
    eingestellte Schema: die vorhandenen Dateien entstanden unter dem
    Schema von damals, und das steht nirgends geschrieben.

    Verlangt wird mindestens ein Zeit-Baustein. Sonst gaelte eine selbst
    "hum" genannte Aufnahme als erzeugt und wuerde umbenannt.
    """
    stem = str(stem or "")
    if not stem:
        return False

    texts = set()
    for candidate in (scheme or {}, DEFAULT):
        for key in TEXT_BLOCKS:
            value = clean_text(candidate.get(key, ""))
            if value:
                texts.add(value)

    tokens = stem.split(SEPARATOR)
    if not all(_known_token(token, texts) for token in tokens):
        return False
    return any(_TIMEISH.match(token) for token in tokens)
