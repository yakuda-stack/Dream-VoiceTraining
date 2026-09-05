"""Spaltendefinitionen der Sessionliste.

Welche Spalten sichtbar sind, laesst sich im Filterdialog einstellen; hier
steht, welche es ueberhaupt gibt und wie sie formatiert und sortiert werden.
"""

from __future__ import annotations

from dataclasses import dataclass

import i18n
import rectypes


@dataclass(frozen=True)
class Column:
    key: str
    label_key: str
    field: str | None = None
    unit: str = ""
    decimals: int = 0
    numeric: bool = True

    @property
    def label(self) -> str:
        return i18n.t(self.label_key)


COLUMNS = [
    Column("date", "col_date", numeric=False),
    Column("label", "col_name", numeric=False),
    Column("type", "col_type", numeric=False),
    Column("duration", "col_duration", "duration", "s", 1),
    Column("peak_db", "col_level", "peak_db", "dB", 0),
    Column("f0_median", "m_f0_median", "f0_median", "Hz", 0),
    Column("f0_spread", "col_f0_spread"),
    Column("f0_p10", "m_f0_p10", "f0_p10", "Hz", 0),
    Column("f0_p90", "m_f0_p90", "f0_p90", "Hz", 0),
    Column("f0_sd_st", "m_f0_sd_st", "f0_sd_st", "ST", 2),
    Column("f0_range_st", "m_f0_range_st", "f0_range_st", "ST", 1),
    Column("f1_median", "m_f1_median", "f1_median", "Hz", 0),
    Column("f2_median", "m_f2_median", "f2_median", "Hz", 0),
    Column("f3_median", "m_f3_median", "f3_median", "Hz", 0),
    Column("h1_db", "m_h1_db", "h1_db", "dB", 1),
    Column("h2_db", "m_h2_db", "h2_db", "dB", 1),
    Column("h1_h2", "m_h1_h2", "h1_h2", "dB", 1),
    Column("hnr", "m_hnr", "hnr", "dB", 1),
    Column("jitter_local", "m_jitter_local", "jitter_local", "%", 2),
    Column("shimmer_local", "m_shimmer_local", "shimmer_local", "%", 2),
    Column("voice_breaks_pct", "m_voice_breaks_pct", "voice_breaks_pct", "%", 1),
    Column("voice_break_count", "m_voice_break_count", "voice_break_count", "", 0),
    Column("voiced_ratio_pct", "m_voiced_ratio_pct"),
    Column("file", "col_file", numeric=False),
]

BY_KEY = {c.key: c for c in COLUMNS}

# Startauswahl: die Groessen, an denen sich beim Stimmtraining tatsaechlich
# etwas ablesen laesst — Tonhoehe und ihre Spanne, die Melodiefuehrung, die
# Resonanz ueber F2 und F3, die beiden Harmonischen einzeln sowie Jitter und
# Shimmer. Alles Weitere laesst sich jederzeit ueber die Kopfzeile oder den
# Ansichtsdialog dazuholen.
DEFAULT_VISIBLE = ["date", "label", "type", "f0_median", "f0_spread",
                   "f0_sd_st", "f2_median", "f3_median", "h1_db", "h2_db",
                   "jitter_local", "shimmer_local"]

QUIET_DB = -40.0


def display_name(entry: dict) -> str:
    label = entry.get("label")
    if label:
        return str(label)
    # Nur der Dateiname: der Monatsunterordner steht schon in der
    # Datumsspalte und wuerde die Namensspalte doppelt so breit machen.
    name = str(entry.get("file", "")).rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return name[:-4] if name.lower().endswith(".wav") else name


def value(entry: dict, column: Column):
    """Rohwert fuer Sortierung und Export."""
    if column.key == "date":
        return entry.get("timestamp", "")
    if column.key == "label":
        return display_name(entry)
    if column.key == "type":
        return rectypes.label(entry.get("type")).lower()
    if column.key == "type":
        return rectypes.label(entry.get("type"))
    if column.key == "file":
        return entry.get("file", "")
    if column.key == "f0_spread":
        return entry.get("f0_p10")
    if column.key == "voiced_ratio_pct":
        raw = entry.get("voiced_ratio")
        return raw * 100.0 if isinstance(raw, (int, float)) else None
    raw = entry.get(column.field) if column.field else None
    return raw if isinstance(raw, (int, float)) else None


def text(entry: dict, column: Column) -> str:
    """Was in der Zelle steht."""
    no_signal = entry.get("quality", "ok") == "kein_signal"

    if column.key == "date":
        return entry.get("timestamp", "").replace("T", "  ")
    if column.key == "label":
        return display_name(entry)
    if column.key == "type":
        return rectypes.label(entry.get("type"))
    if column.key == "file":
        return entry.get("file", "")

    if column.key == "duration":
        seconds = entry.get("duration")
        return f"{seconds:.1f} s" if isinstance(seconds, (int, float)) else "--"

    if column.key == "peak_db":
        peak = entry.get("peak_db")
        if not isinstance(peak, (int, float)):
            return "--"
        suffix = "  " + i18n.t("quiet") if peak < QUIET_DB else ""
        return f"{peak:.0f} dB{suffix}"

    if column.key == "f0_median" and no_signal:
        return i18n.t("no_speech")
    if no_signal:
        return "--"

    if column.key == "f0_spread":
        low, high = entry.get("f0_p10"), entry.get("f0_p90")
        if isinstance(low, (int, float)) and isinstance(high, (int, float)):
            return f"{low:.0f}–{high:.0f} Hz"
        return "--"

    raw = value(entry, column)
    if raw is None:
        return "--"
    return f"{raw:.{column.decimals}f} {column.unit}".strip()


def sort_key(entry: dict, column: Column, descending: bool):
    """Sortierschluessel; fehlende Werte landen immer am Ende."""
    raw = value(entry, column)
    if raw is None or raw == "":
        return (1, 0.0 if column.numeric else "")
    return (0, raw)
