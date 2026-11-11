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

"""Auswertungen ueber mehrere Aufnahmen: Verlauf, Serie, Vergleich, Ziel-Anteil.

Ohne Qt, damit sich alles direkt testen laesst. Die Fenster dazu liegen in
ui/progress_dialog.py und ui/compare_dialog.py.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np

from core import columns


def parse_stamp(entry: dict) -> datetime | None:
    raw = entry.get("timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def series(entries: list[dict], key: str,
           type_key: str | None = None) -> list[tuple[datetime, float]]:
    """(Zeitpunkt, Wert) je Aufnahme, nach Zeit sortiert.

    Aufnahmen ohne Sprache fallen heraus: ihre Werte waeren Rauschen und
    wuerden die Kurve verziehen.
    """
    column = columns.BY_KEY.get(key)
    if column is None or not column.numeric:
        return []
    points = []
    for entry in entries:
        if entry.get("quality", "ok") == "kein_signal":
            continue
        if type_key and entry.get("type") != type_key:
            continue
        stamp = parse_stamp(entry)
        value = columns.value(entry, column)
        if stamp is None or value is None:
            continue
        points.append((stamp, float(value)))
    points.sort(key=lambda p: p[0])
    return points


def moving_average(values: list[float], window: int = 5) -> list[float]:
    """Gleitender Mittelwert ueber die letzten `window` Werte."""
    out = []
    for i in range(len(values)):
        part = values[max(0, i - window + 1):i + 1]
        out.append(float(np.mean(part)))
    return out


def practice_days(entries: list[dict]) -> set[date]:
    days = set()
    for entry in entries:
        stamp = parse_stamp(entry)
        if stamp is not None:
            days.add(stamp.date())
    return days


def streak(entries: list[dict], today: date | None = None) -> int:
    """Tage in Folge mit mindestens einer Aufnahme.

    Heute zaehlt mit, muss aber noch nicht dabei sein: wer gestern geuebt
    hat, verliert die Serie nicht schon morgens um acht.
    """
    today = today or date.today()
    days = practice_days(entries)
    day = today if today in days else today - timedelta(days=1)
    count = 0
    while day in days:
        count += 1
        day -= timedelta(days=1)
    return count


def week_count(entries: list[dict], today: date | None = None) -> int:
    """Aufnahmen in den letzten sieben Tagen (heute eingeschlossen)."""
    today = today or date.today()
    start = today - timedelta(days=6)
    count = 0
    for entry in entries:
        stamp = parse_stamp(entry)
        if stamp is not None and start <= stamp.date() <= today:
            count += 1
    return count


def target_share(f0_values, rng) -> float | None:
    """Anteil stimmhafter Werte im Zielbereich, in Prozent.

    None, wenn es keinen Bereich gibt oder nichts Stimmhaftes da ist.
    """
    if rng is None:
        return None
    lo, hi = rng
    if lo is None and hi is None:
        return None
    values = np.asarray([v for v in f0_values
                         if v is not None and np.isfinite(v) and v > 0],
                        dtype=float)
    if values.size == 0:
        return None
    inside = np.ones(values.size, dtype=bool)
    if lo is not None:
        inside &= values >= lo
    if hi is not None:
        inside &= values <= hi
    return float(inside.mean() * 100.0)


MAX_COMPARE = 4


def compare(*entries: dict) -> list[tuple]:
    """(Spalte, [Werte je Aufnahme], Differenz letzte−erste) fuer Zahlenspalten.

    Die Aufnahmen kommen in der uebergebenen Reihenfolge. Spalten ohne Wert
    in allen Aufnahmen fallen weg; die Differenz ist None, wenn der erste
    oder der letzte Wert fehlt.
    """
    rows = []
    for column in columns.COLUMNS:
        if not column.numeric or column.field is None:
            continue
        values = [columns.value(entry, column) for entry in entries]
        if all(v is None for v in values):
            continue
        first, last = values[0], values[-1]
        diff = last - first if first is not None and last is not None else None
        rows.append((column, values, diff))
    return rows
