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

"""Wo die Aufnahmen liegen und wie sie heissen.

Der Ordner ist frei waehlbar, die Benennung stellt naming.py zusammen:
Unterordner je Tag, Woche, Monat oder Jahr und ein Dateiname aus frei
angeordneten Bausteinen. Dieses Modul kuemmert sich nur noch darum, wo das
Ergebnis landet.

Die sessions.json bleibt dabei immer an ihrem Platz in den Programmdaten:
eine Liste, die mit den WAV-Dateien auf eine externe Platte wandert, ist
beim naechsten Start verschwunden, sobald die Platte nicht steckt.

Deshalb steht in "file" ein Name *relativ* zum Aufnahmeordner, mit
Schraegstrich als Trenner — auch unter Windows, wo Path den akzeptiert. So
bleibt die Liste zwischen den Systemen austauschbar.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import naming
import paths
import settings

DEFAULT_ROOT = paths.SESSION_DIR

STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
MONTH_FORMAT = "%Y-%m"

# Unterordner, die dieses Programm selbst anlegt. Nur die werden beim
# Aufraeumen wieder entfernt, wenn sie leer sind — ein fremder leerer
# Ordner im Aufnahmeverzeichnis geht niemanden etwas an.
AUTO_DIR = re.compile(r"^(?:\d{4}(?:-\d{2}(?:-\d{2})?)?|\d{4}-KW\d{2}|unsorted)$")


# ------------------------------------------------------------------ Ordner

def root() -> Path:
    """Aktueller Aufnahmeordner."""
    custom = settings.get_session_dir()
    return Path(custom).expanduser() if custom else DEFAULT_ROOT


def is_default() -> bool:
    return settings.get_session_dir() is None


def writable(folder: Path) -> str:
    """Leerer String, wenn sich dort schreiben laesst, sonst der Grund.

    Erst beim Schreiben zu scheitern hiesse: Aufnahme gemacht, Aufnahme
    weg. Also einmal vorher ausprobieren.
    """
    try:
        folder = Path(folder).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".writetest"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return str(exc)
    return ""


def ensure_root() -> Path:
    folder = root()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ------------------------------------------------------------------ Zaehler

def peek_counter(scheme: dict, stamp: datetime) -> int:
    """Welche Nummer die naechste Aufnahme bekaeme — ohne sie zu verbrauchen.

    Getrennt von take_counter(), damit die Vorschau im Optionen-Reiter
    mitzaehlen kann, ohne den Zaehler bei jedem Tastendruck weiterzudrehen.
    """
    period = naming.period_key(naming.normalize(scheme)["counter_reset"], stamp)
    state = settings.get_name_counter()
    return 1 if state["period"] != period else state["value"] + 1


def take_counter(scheme: dict, stamp: datetime) -> int:
    """Die naechste Nummer holen und vermerken."""
    period = naming.period_key(naming.normalize(scheme)["counter_reset"], stamp)
    number = peek_counter(scheme, stamp)
    settings.set_name_counter(period, number)
    return number


# ------------------------------------------------------------------ Namen

def month_of(stamp: datetime) -> str:
    return stamp.strftime(MONTH_FORMAT)


def relative_name(stamp: datetime, type_key: str | None = None,
                  stem: str | None = None, suffix: str = ".wav",
                  month: bool | None = None, typed: bool | None = None,
                  scheme: dict | None = None,
                  counter: int | None = None) -> str:
    """Name einer Aufnahme, relativ zum Aufnahmeordner.

    Ohne scheme gilt das eingestellte. month und typed uebergehen es —
    damit rechnet der Umzug ein anderes Schema durch, ohne es zu speichern.

    Der Zaehler wird hier nur gelesen, nie weitergedreht. Wer wirklich
    speichert, nimmt next_name().
    """
    scheme = naming.with_legacy(scheme or settings.get_naming(), month, typed)
    if counter is None:
        counter = peek_counter(scheme, stamp)
    return naming.relative(scheme, stamp, type_key, counter, suffix, stem)


def next_name(stamp: datetime, type_key: str | None = None,
              suffix: str = ".wav") -> str:
    """Name fuer eine Aufnahme, die gleich geschrieben wird.

    Verbraucht die Nummer des fortlaufenden Zaehlers, sofern der Baustein
    ueberhaupt eingeschaltet ist. Sonst zaehlte er auch dann hoch, wenn ihn
    niemand haben will, und stuende beim Einschalten schon bei 400.
    """
    scheme = settings.get_naming()
    counter = (take_counter(scheme, stamp) if naming.uses_counter(scheme)
               else peek_counter(scheme, stamp))
    return naming.relative(scheme, stamp, type_key, counter, suffix)


def path_for(name: str) -> Path:
    """Vollstaendiger Pfad zu einer Aufnahme.

    Wer den Ordner umstellt, aber die alten Dateien stehen laesst, soll sie
    trotzdem noch abspielen koennen. Deshalb der Blick in den Standardort,
    bevor ein nicht vorhandener Pfad zurueckkommt.
    """
    name = str(name or "")
    if not name:
        return root()

    candidate = root() / name
    if candidate.exists():
        return candidate
    for fallback in (DEFAULT_ROOT / name, DEFAULT_ROOT / Path(name).name,
                     root() / Path(name).name):
        if fallback.exists():
            return fallback
    return candidate


def free_path(path: Path) -> Path:
    """Freien Namen finden, statt eine vorhandene Datei zu ueberschreiben."""
    if not path.exists():
        return path
    for number in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
        if not candidate.exists():
            return candidate
    stamp = datetime.now().strftime("%H%M%S")
    return path.with_name(f"{path.stem}-{stamp}{path.suffix}")


def folder_part(name: str) -> str:
    """Der Unterordner eines Eintrags, mit Schraegstrich am Ende."""
    parent = Path(str(name or "")).parent
    return "" if str(parent) in (".", "") else parent.as_posix() + "/"


# ------------------------------------------------------------------ Umzug

def _stamp_of(entry: dict) -> datetime:
    """Zeitpunkt einer Aufnahme, notfalls aus dem Dateinamen.

    Ein Eintrag ohne brauchbaren Zeitstempel darf nicht dazu fuehren, dass
    der ganze Umzug abbricht — er landet dann eben im Ordner "unsorted".
    """
    raw = str(entry.get("timestamp", ""))
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass

    # Aelteste Rettung: der Zeitstempel steht vorn im Dateinamen.
    stem = Path(str(entry.get("file", ""))).stem
    head = stem.split(naming.SEPARATOR)
    for size in (2, 1):
        try:
            return datetime.strptime(naming.SEPARATOR.join(head[:size]),
                                     STAMP_FORMAT)
        except ValueError:
            continue
    return datetime.min


def target_name(entry: dict, scheme: dict | None = None, *,
                month: bool | None = None, typed: bool | None = None,
                counter: int = 1) -> str:
    """Wohin ein vorhandener Eintrag nach dem gewaehlten Schema gehoert.

    Selbst vergebene Namen behalten ihren Stamm und wandern nur in den
    passenden Unterordner. Erkannt wird das an den Bausteinen: was sich
    restlos in Datum, Uhrzeit, Typ und Zaehler zerlegen laesst, stammt vom
    Programm — alles andere hat sich jemand ueberlegt.
    """
    old = str(entry.get("file", ""))
    if not old:
        return ""

    scheme = naming.with_legacy(scheme or settings.get_naming(), month, typed)
    base = Path(old).name
    stem = Path(base).stem
    suffix = Path(base).suffix or ".wav"
    stamp = _stamp_of(entry)

    keep = None if naming.looks_generated(stem, scheme) else stem
    if stamp == datetime.min:
        # Ohne Zeitstempel laesst sich kein Name bauen und kein Zeitraum
        # bestimmen. Der Eintrag bleibt, wie er heisst, und wird eingesammelt.
        folder = naming.build_folder(scheme, datetime.now())
        return f"unsorted/{stem}{suffix}" if folder else f"{stem}{suffix}"

    return naming.relative(scheme, stamp, entry.get("type"), counter, suffix,
                           stem=keep)


def _numbered(entries: list[dict], scheme: dict) -> dict[int, int]:
    """Fortlaufende Nummern fuer einen Umzug, je Zeitraum von vorn.

    Der gespeicherte Zaehler taugt hier nicht: er kennt nur den aktuellen
    Zeitraum, und ein Umzug bringt Aufnahmen aus Monaten mit, die laengst
    vorbei sind. Also wird fuer die Liste einmal durchgezaehlt — nach
    Aufnahmezeitpunkt, damit die Nummern der Reihenfolge folgen.
    """
    if not naming.uses_counter(scheme):
        return {}

    reset = naming.normalize(scheme)["counter_reset"]
    order = sorted(range(len(entries)), key=lambda i: _stamp_of(entries[i]))
    seen: dict[str, int] = {}
    numbers: dict[int, int] = {}
    for index in order:
        stamp = _stamp_of(entries[index])
        period = naming.period_key(reset, stamp)
        seen[period] = seen.get(period, 0) + 1
        numbers[index] = seen[period]
    return numbers


def _find(name: str, roots: list[Path]) -> Path | None:
    """Die Datei eines Eintrags in einem der bekannten Ordner suchen."""
    plain = Path(str(name or "")).name
    for base in roots:
        for candidate in (base / name, base / plain):
            if candidate.is_file():
                return candidate
    return None


def move_all(entries: list[dict], sources: list[Path], target: Path,
             scheme: dict | None = None, *, month: bool | None = None,
             typed: bool | None = None) -> dict:
    """Vorhandene Aufnahmen in den neuen Ordner und das neue Schema bringen.

    Aendert entry["file"] auf den neuen Namen. Die Liste zu speichern ist
    Sache des Aufrufers — der weiss, wann er das Fenster ohnehin neu
    zeichnet.
    """
    scheme = naming.with_legacy(scheme or settings.get_naming(), month, typed)
    numbers = _numbered(entries, scheme)
    target = Path(target).expanduser()
    # Das Ziel steht bewusst hinten: liegt dort schon eine fremde Datei
    # gleichen Namens, soll die echte Quelle gefunden und daneben abgelegt
    # werden, statt die fremde faelschlich fuer den Eintrag zu halten. Nach
    # einem bereits erledigten Umzug ist das Ziel der einzige Fund, und
    # Quelle und Ziel sind derselbe Pfad — dann passiert nichts.
    roots: list[Path] = []
    for base in [*sources, DEFAULT_ROOT, target]:
        base = Path(base).expanduser()
        if base not in roots:
            roots.append(base)

    result = {"moved": 0, "kept": 0, "missing": 0, "errors": []}
    for index, entry in enumerate(entries):
        old = str(entry.get("file", ""))
        if not old:
            continue

        source = _find(old, roots)
        if source is None:
            result["missing"] += 1
            continue

        wanted = target_name(entry, scheme, counter=numbers.get(index, 1))
        destination = target / wanted
        if source == destination:
            if old != wanted:
                entry["file"] = wanted
            result["kept"] += 1
            continue

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = free_path(destination)
            shutil.move(str(source), str(destination))
        except OSError as exc:
            result["errors"].append(f"{old}: {exc}")
            continue

        entry["file"] = destination.relative_to(target).as_posix()
        result["moved"] += 1

    for base in roots:
        if base != target:
            prune_empty(base)
    return result


def prune_empty(folder: Path) -> None:
    """Leere selbst angelegte Unterordner wegraeumen, den Ordner selbst nicht.

    Nach einem Wechsel von "pro Monat" auf "pro Tag" bleiben sonst die
    leeren Monatsordner stehen und der Aufnahmeordner sieht aus wie ein
    Dachboden.
    """
    try:
        if not folder.is_dir():
            return
        for item in folder.iterdir():
            if item.is_dir() and AUTO_DIR.match(item.name):
                try:
                    item.rmdir()
                except OSError:
                    pass
    except OSError:
        pass


def elsewhere(entries: list[dict], target: Path, scheme: dict | None = None,
              *, month: bool | None = None, typed: bool | None = None) -> int:
    """Wie viele Aufnahmen noch nicht dort liegen, wo sie hin sollen."""
    scheme = naming.with_legacy(scheme or settings.get_naming(), month, typed)
    numbers = _numbered(entries, scheme)
    target = Path(target).expanduser()
    count = 0
    for index, entry in enumerate(entries):
        old = str(entry.get("file", ""))
        if not old:
            continue
        wanted = target / target_name(entry, scheme,
                                      counter=numbers.get(index, 1))
        if wanted.is_file():
            continue
        if _find(old, [target, root(), DEFAULT_ROOT]) is not None:
            count += 1
    return count
