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

Der Ordner ist frei waehlbar, wahlweise mit einem Unterordner je Monat und
mit dem Aufnahmetyp im Dateinamen. Die sessions.json bleibt dabei immer an
ihrem Platz in den Programmdaten: eine Liste, die mit den WAV-Dateien auf
eine externe Platte wandert, ist beim naechsten Start verschwunden, sobald
die Platte nicht steckt.

Deshalb steht in "file" ein Name *relativ* zum Aufnahmeordner, mit
Schraegstrich als Trenner — auch unter Windows, wo Path den akzeptiert. So
bleibt die Liste zwischen den Systemen austauschbar.

Der Typ steht als fester englischer Kuerzel im Namen, nicht als uebersetzte
Beschriftung. Sonst hiessen dieselben Aufnahmen nach einem Sprachwechsel
anders als die Eintraege in der Liste.
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import paths
import rectypes
import settings

DEFAULT_ROOT = paths.SESSION_DIR

STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
MONTH_FORMAT = "%Y-%m"

# Von der Aufnahme selbst vergebene Namen. Nur diese werden beim Umziehen
# umbenannt — an einem selbst vergebenen Namen fasst niemand ungefragt an.
AUTO_STEM = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
AUTO_TYPED = re.compile(r"^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([a-z-]+)$")
MONTH_DIR = re.compile(r"^\d{4}-\d{2}$")


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


# ------------------------------------------------------------------ Namen

def month_of(stamp: datetime) -> str:
    return stamp.strftime(MONTH_FORMAT)


def relative_name(stamp: datetime, type_key: str | None = None,
                  stem: str | None = None, suffix: str = ".wav",
                  month: bool | None = None, typed: bool | None = None) -> str:
    """Name einer Aufnahme, relativ zum Aufnahmeordner.

    month und typed uebergehen die Einstellung — der Dialog zeigt damit
    eine Vorschau, ohne schon etwas zu speichern.
    """
    month = settings.get_month_folders() if month is None else month
    typed = settings.get_type_in_name() if typed is None else typed

    base = stem or stamp.strftime(STAMP_FORMAT)
    if typed and stem is None:
        base = f"{base}_{rectypes.slug(type_key)}"
    name = base + suffix
    return f"{month_of(stamp)}/{name}" if month else name


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
    der ganze Umzug abbricht — er landet dann eben im Ordner "unsortiert".
    """
    raw = str(entry.get("timestamp", ""))
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        pass
    stem = Path(str(entry.get("file", ""))).stem
    match = AUTO_TYPED.match(stem)
    head = match.group(1) if match else stem
    try:
        return datetime.strptime(head, STAMP_FORMAT)
    except ValueError:
        return datetime.min


def target_name(entry: dict, month: bool, typed: bool) -> str:
    """Wohin ein vorhandener Eintrag nach dem gewaehlten Schema gehoert."""
    old = str(entry.get("file", ""))
    if not old:
        return ""

    base = Path(old).name
    stem = Path(base).stem
    suffix = Path(base).suffix or ".wav"
    stamp = _stamp_of(entry)

    known = set(rectypes.SLUGS.values())
    match = AUTO_TYPED.match(stem)
    if match and match.group(2) in known:
        stem = match.group(1) if not typed else \
            f"{match.group(1)}_{rectypes.slug(entry.get('type'))}"
    elif typed and AUTO_STEM.match(stem):
        stem = f"{stem}_{rectypes.slug(entry.get('type'))}"

    name = stem + suffix
    if not month:
        return name
    folder = "unsorted" if stamp == datetime.min else month_of(stamp)
    return f"{folder}/{name}"


def _find(name: str, roots: list[Path]) -> Path | None:
    """Die Datei eines Eintrags in einem der bekannten Ordner suchen."""
    plain = Path(str(name or "")).name
    for base in roots:
        for candidate in (base / name, base / plain):
            if candidate.is_file():
                return candidate
    return None


def move_all(entries: list[dict], sources: list[Path], target: Path,
             month: bool, typed: bool) -> dict:
    """Vorhandene Aufnahmen in den neuen Ordner und das neue Schema bringen.

    Aendert entry["file"] auf den neuen Namen. Die Liste zu speichern ist
    Sache des Aufrufers — der weiss, wann er das Fenster ohnehin neu
    zeichnet.
    """
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
    for entry in entries:
        old = str(entry.get("file", ""))
        if not old:
            continue

        source = _find(old, roots)
        if source is None:
            result["missing"] += 1
            continue

        wanted = target_name(entry, month, typed)
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
    """Leere Monatsordner wegraeumen, den Ordner selbst stehen lassen."""
    try:
        if not folder.is_dir():
            return
        for item in folder.iterdir():
            if item.is_dir() and (MONTH_DIR.match(item.name)
                                  or item.name == "unsorted"):
                try:
                    item.rmdir()
                except OSError:
                    pass
    except OSError:
        pass


def elsewhere(entries: list[dict], target: Path, month: bool,
              typed: bool) -> int:
    """Wie viele Aufnahmen noch nicht dort liegen, wo sie hin sollen."""
    target = Path(target).expanduser()
    count = 0
    for entry in entries:
        old = str(entry.get("file", ""))
        if not old:
            continue
        wanted = target / target_name(entry, month, typed)
        if wanted.is_file():
            continue
        if _find(old, [target, root(), DEFAULT_ROOT]) is not None:
            count += 1
    return count
