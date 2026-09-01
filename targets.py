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

"""Orientierungsbereiche fuer die Detailansicht.

Wichtig: das sind Populationsmittelwerte aus der Literatur zur Sprechstimme,
keine Vorgaben. Zwei Menschen mit identischen Werten koennen voellig
unterschiedlich wahrgenommen werden, und die Wahrnehmung haengt an mehr
Faktoren als hier messbar sind. Die Bereiche taugen zur Orientierung und
zum Vergleich mit sich selbst ueber die Zeit, nicht als Zielvorgabe.
"""

from __future__ import annotations

from dataclasses import dataclass

import i18n
import settings


@dataclass(frozen=True)
class Metric:
    key: str
    unit: str
    decimals: int = 0
    vowel_only: bool = False

    @property
    def label(self) -> str:
        return i18n.t(f"m_{self.key}")

    @property
    def hint(self) -> str:
        return i18n.t(f"m_{self.key}_hint")


# Kennwerte in der Reihenfolge, in der sie angezeigt werden.
METRICS = [
    Metric("f0_median", "Hz", 0),
    Metric("f0_p10", "Hz", 0),
    Metric("f0_p90", "Hz", 0),
    Metric("f0_sd_st", "ST", 2),
    Metric("f0_range_st", "ST", 1),
    Metric("f1_median", "Hz", 0),
    Metric("f2_median", "Hz", 0),
    Metric("f3_median", "Hz", 0),
    Metric("h1_db", "dB", 1),
    Metric("h2_db", "dB", 1),
    Metric("h1_h2", "dB", 1),
    Metric("hnr", "dB", 1),
    Metric("jitter_local", "%", 2, vowel_only=True),
    Metric("shimmer_local", "%", 2, vowel_only=True),
    Metric("voice_breaks_pct", "%", 1, vowel_only=True),
    Metric("voice_break_count", "", 0, vowel_only=True),
    Metric("voiced_ratio_pct", "%", 0),
    Metric("peak_db", "dBFS", 0),
]

METRIC_BY_KEY = {m.key: m for m in METRICS}

# Profilabhaengige Bereiche: key -> (untere Grenze, obere Grenze), None = offen
# Bewusst nur die Groessen rund um die Tonhoehe. Formanten stehen zwar in
# der Literatur, dort aber fuer gehaltene Vokale — verglichen wuerde hier ein
# Median ueber fliessenden Lesetext. Das sind zwei verschiedene Dinge, und
# eine Bewertung daraus waere bedeutungslos. Wer Formantziele will, schaltet
# sie im Einstellungsdialog ein oder leitet ein eigenes Profil aus einer
# Aufnahme ab.
#
# Die Qualitaetsgrenzen weiter unten (Pegel, HNR, Jitter, Shimmer,
# Stimmabbrueche, stimmhafter Anteil) gelten unabhaengig davon weiter.
PROFILES: dict[str, dict[str, tuple[float | None, float | None]]] = {
    "maskulin": {
        "f0_median": (85.0, 130.0),
        "f0_p10": (70.0, 110.0),
        "f0_p90": (120.0, 200.0),
        "f0_sd_st": (2.0, 4.5),
        "f0_range_st": (4.0, 11.0),
    },
    "androgyn": {
        "f0_median": (145.0, 175.0),
        "f0_p10": (115.0, 150.0),
        "f0_p90": (180.0, 250.0),
        "f0_sd_st": (2.5, 5.0),
        "f0_range_st": (5.0, 13.0),
    },
    "feminin": {
        "f0_median": (180.0, 250.0),
        "f0_p10": (145.0, 200.0),
        "f0_p90": (210.0, 300.0),
        "f0_sd_st": (3.0, 5.5),
        "f0_range_st": (7.0, 16.0),
    },
}

# Interne Schluessel; die Beschriftung kommt aus i18n.
# Kennwerte, aus denen "Diese Werte als mein Ziel" ein Profil ableitet.
# Absichtlich nur die, die eine Zielstimme beschreiben — der Aufnahmepegel
# etwa ist Aufnahmequalitaet und kein Ziel.
CUSTOM_KEYS = ["f0_median", "f0_sd_st", "f1_median", "f2_median", "f3_median",
               "h1_h2"]
CUSTOM_TOLERANCE = 0.08      # +/- 8 % um den Referenzwert
CUSTOM_MIN_MARGIN = 0.05     # verhindert einen null breiten Bereich


def build_custom(source: dict) -> dict:
    """Aus einer Aufnahme einen Zielbereich je Kennwert ableiten."""
    ranges = {}
    for key in CUSTOM_KEYS:
        value = source.get(key)
        if not isinstance(value, (int, float)):
            continue
        margin = max(abs(value) * CUSTOM_TOLERANCE, CUSTOM_MIN_MARGIN)
        ranges[key] = [round(value - margin, 3), round(value + margin, 3)]
    return ranges


BUILTIN_ORDER = ["none", "maskulin", "androgyn", "feminin"]
PROFILE_LABEL_KEYS = {"none": "profile_none", "maskulin": "profile_masc",
                      "androgyn": "profile_andro", "feminin": "profile_fem"}

USER_PREFIX = "user:"


def profile_keys() -> list[str]:
    """Eingebaute Profile, danach die selbst angelegten."""
    return BUILTIN_ORDER + [USER_PREFIX + name
                            for name in sorted(settings.get_user_profiles())]


def is_user_profile(key: str) -> bool:
    return key.startswith(USER_PREFIX)


def profile_name(key: str) -> str:
    return key[len(USER_PREFIX):] if is_user_profile(key) else key


def profile_label(key: str) -> str:
    if is_user_profile(key):
        return profile_name(key)
    return i18n.t(PROFILE_LABEL_KEYS.get(key, "profile_none"))


def _clean(stored: dict) -> dict:
    return {k: (float(v[0]), float(v[1]))
            for k, v in stored.items()
            if isinstance(v, (list, tuple)) and len(v) == 2}


def is_overridden(key: str) -> bool:
    """Wurde ein eingebautes Profil vom Benutzer angepasst?"""
    return not is_user_profile(key) and key in settings.get_builtin_overrides()


def profile_ranges(key: str) -> dict:
    """Alle hinterlegten Bereiche eines Profils, egal woher.

    Reihenfolge: eigenes Profil, sonst eine Anpassung des eingebauten,
    sonst der Literaturwert.
    """
    if is_user_profile(key):
        return _clean(settings.get_user_profiles().get(profile_name(key), {}))
    override = settings.get_builtin_overrides().get(key)
    if isinstance(override, dict) and override:
        return _clean(override)
    return dict(PROFILES.get(key, {}))


# Bereiche, die unabhaengig vom Ziel gelten (Aufnahmequalitaet).
QUALITY_RANGES: dict[str, tuple[float | None, float | None]] = {
    "peak_db": (-30.0, -8.0),
    "hnr": (15.0, None),
    "voiced_ratio_pct": (30.0, None),
    # Diese Grenzen gelten fuer gehaltene Vokale. In fliessender Sprache
    # liegen die Werte systematisch hoeher, ohne dass etwas nicht stimmt.
    "jitter_local": (None, 1.04),
    "shimmer_local": (None, 3.81),
    "voice_breaks_pct": (None, 5.0),
}


def profile_keys_all() -> list[str]:
    """Jeder Kennwert laesst sich in einem Profil festlegen."""
    return [metric.key for metric in METRICS]


def range_for(key: str, profile: str) -> tuple[float | None, float | None] | None:
    """Das Profil hat Vorrang; ohne Eintrag greifen die Qualitaetsgrenzen.

    Damit kann ein eigenes Profil auch HNR, Jitter oder den Pegel festlegen,
    ohne dass die eingebauten Vorgaben dazwischenfunken.
    """
    span = profile_ranges(profile).get(key)
    if span is not None:
        return span
    return QUALITY_RANGES.get(key)


def format_range(rng: tuple[float | None, float | None] | None, unit: str,
                 decimals: int) -> str:
    if rng is None:
        return "—"
    lo, hi = rng
    fmt = f"{{:.{decimals}f}}"
    if lo is not None and hi is not None:
        # Bei negativen Werten wuerde ein Gedankenstrich mit dem Minus verschmelzen.
        joiner = f" {i18n.t('range_join')} " if lo < 0 or hi < 0 else "–"
        return f"{fmt.format(lo)}{joiner}{fmt.format(hi)} {unit}".strip()
    if lo is not None:
        return f"≥ {fmt.format(lo)} {unit}".strip()
    if hi is not None:
        return f"≤ {fmt.format(hi)} {unit}".strip()
    return "—"


def verdict(value: float | None,
            rng: tuple[float | None, float | None] | None) -> str:
    """'' oder der uebersetzte Text fuer darunter / im Bereich / darueber."""
    if value is None or rng is None:
        return ""
    lo, hi = rng
    if lo is not None and value < lo:
        return i18n.t("verdict_below")
    if hi is not None and value > hi:
        return i18n.t("verdict_above")
    return i18n.t("verdict_within")


def is_within(value: float | None,
              rng: tuple[float | None, float | None] | None) -> bool | None:
    if value is None or rng is None:
        return None
    lo, hi = rng
    if lo is not None and value < lo:
        return False
    if hi is not None and value > hi:
        return False
    return True
