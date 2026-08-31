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

"""Laufzeit-Einstellungen mit JSON-Persistenz und Vorlagen.

`CFG` ist eine Singleton-Instanz, die von analysis.py zur Laufzeit gelesen
wird. Aenderungen werden per apply() an Ort und Stelle uebernommen, damit
alle Module ohne Neustart die neuen Werte sehen.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from typing import NamedTuple

import i18n
from paths import CONFIG_PATH

LEGACY_PROFILE_NAME = "My target"


@dataclass
class Settings:
    silence_rms: float = 0.0015
    pitch_floor: float = 60.0
    pitch_ceiling: float = 500.0
    formant_ceiling: float = 5000.0
    zone_low: float = 145.0
    zone_high: float = 185.0
    voicing_threshold: float = 0.65
    min_voiced_ratio: float = 0.15

    def clamped(self) -> "Settings":
        """Grenzen einhalten und widerspruechliche Werte korrigieren."""
        out = Settings(**asdict(self))
        for param in PARAMS:
            value = getattr(out, param.attr)
            setattr(out, param.attr, float(min(max(value, param.lo), param.hi)))
        if out.pitch_ceiling <= out.pitch_floor + 20.0:
            out.pitch_ceiling = out.pitch_floor + 20.0
        if out.zone_high <= out.zone_low + 5.0:
            out.zone_high = out.zone_low + 5.0
        return out


class Param(NamedTuple):
    attr: str
    unit: str
    lo: float
    hi: float
    step: float
    decimals: int

    @property
    def label(self) -> str:
        return i18n.t(f"param_{self.attr}")

    @property
    def hint(self) -> str:
        return i18n.t(f"param_{self.attr}_hint")


PARAMS = [
    Param("silence_rms", "RMS", 0.0002, 0.0500, 0.0005, 4),
    Param("pitch_floor", "Hz", 30.0, 300.0, 5.0, 0),
    Param("pitch_ceiling", "Hz", 120.0, 900.0, 10.0, 0),
    Param("formant_ceiling", "Hz", 3500.0, 7000.0, 100.0, 0),
    Param("zone_low", "Hz", 80.0, 300.0, 5.0, 0),
    Param("zone_high", "Hz", 100.0, 400.0, 5.0, 0),
    Param("voicing_threshold", "", 0.30, 0.95, 0.05, 2),
    Param("min_voiced_ratio", "", 0.00, 0.60, 0.05, 2),
]

BUILTIN_TEMPLATES: dict[str, Settings] = {
    "Standard": Settings(),
    "Leises Mikrofon": Settings(
        silence_rms=0.0006, pitch_floor=60.0, pitch_ceiling=500.0,
        formant_ceiling=5000.0),
    "Tiefe Stimme / Baseline": Settings(
        silence_rms=0.0015, pitch_floor=50.0, pitch_ceiling=350.0,
        formant_ceiling=5000.0),
    "Hohe Stimme": Settings(
        silence_rms=0.0020, pitch_floor=100.0, pitch_ceiling=600.0,
        formant_ceiling=5500.0),
    "Formantmessung (Vokal halten)": Settings(
        silence_rms=0.0040, pitch_floor=60.0, pitch_ceiling=400.0,
        formant_ceiling=5000.0, voicing_threshold=0.70),
    "Lautes Umfeld / strenger": Settings(
        silence_rms=0.0030, pitch_floor=70.0, pitch_ceiling=500.0,
        formant_ceiling=5000.0, voicing_threshold=0.80, min_voiced_ratio=0.25),
}

# Aktive Konfiguration. analysis.py liest hier zur Laufzeit.
CFG = Settings()

_state = {"active_template": "Standard", "user_templates": {}, "device": None, "language": "en", "profile": "feminin", "live_profile": "none",
          "view": {}, "user_profiles": {},
          "builtin_overrides": {},
          "warn_low_level": True, "recording_type": "reading"}


def apply(new: Settings) -> None:
    """Werte in die Singleton-Instanz uebernehmen (in place)."""
    valid = new.clamped()
    for f in fields(Settings):
        setattr(CFG, f.name, getattr(valid, f.name))


def snapshot() -> Settings:
    return Settings(**asdict(CFG))


def get_device() -> str | None:
    return _state["device"]


def set_device(key: str | None) -> None:
    if _state["device"] != key:
        _state["device"] = key
        save()


def get_language() -> str:
    return _state["language"]


def set_language(code: str) -> None:
    if _state["language"] != code:
        _state["language"] = code
        save()


def get_profile() -> str:
    """Ziel der Detailansicht und der Auswertung."""
    return _state["profile"]


def get_live_profile() -> str:
    """Ziel der Live-Ansicht.

    Absichtlich getrennt und standardmaessig aus: eine mitlaufende
    Zielanzeige lenkt beim Sprechen ab, und Ablenkung ist beim Training
    das Gegenteil von hilfreich.
    """
    return _state["live_profile"]


def set_live_profile(key: str) -> None:
    if _state["live_profile"] != key:
        _state["live_profile"] = key
        save()


def set_profile(key: str) -> None:
    if _state["profile"] != key:
        _state["profile"] = key
        save()


DEFAULT_VIEW = {
    "columns": None,          # None = Standardauswahl aus columns.py
    "sort": "date",
    "descending": True,
    "period_on": False,
    "period_from": "",
    "period_to": "",
}


def get_user_profiles() -> dict[str, dict]:
    return {name: dict(ranges)
            for name, ranges in _state["user_profiles"].items()}


def get_builtin_overrides() -> dict[str, dict]:
    return {name: dict(ranges)
            for name, ranges in _state["builtin_overrides"].items()}


def save_builtin_override(name: str, ranges: dict) -> None:
    _state["builtin_overrides"][name] = dict(ranges)
    save()


def reset_builtin(name: str) -> bool:
    if name in _state["builtin_overrides"]:
        del _state["builtin_overrides"][name]
        save()
        return True
    return False


def save_user_profile(name: str, ranges: dict) -> None:
    _state["user_profiles"][name] = dict(ranges)
    save()


def delete_user_profile(name: str) -> bool:
    if name in _state["user_profiles"]:
        del _state["user_profiles"][name]
        save()
        return True
    return False


def get_warn_low_level() -> bool:
    return bool(_state["warn_low_level"])


def set_warn_low_level(enabled: bool) -> None:
    _state["warn_low_level"] = bool(enabled)
    save()


def get_recording_type() -> str:
    return _state["recording_type"]


def set_recording_type(key: str) -> None:
    if _state["recording_type"] != key:
        _state["recording_type"] = key
        save()


def get_view() -> dict:
    return {**DEFAULT_VIEW, **_state["view"]}


def set_view(view: dict) -> None:
    _state["view"] = {k: v for k, v in view.items() if k in DEFAULT_VIEW}
    save()


def all_templates() -> dict[str, Settings]:
    merged = dict(BUILTIN_TEMPLATES)
    merged.update(_state["user_templates"])
    return merged


def is_builtin(name: str) -> bool:
    return name in BUILTIN_TEMPLATES


def active_template() -> str:
    return _state["active_template"]


def set_active_template(name: str) -> None:
    _state["active_template"] = name


def save_template(name: str, values: Settings) -> None:
    _state["user_templates"][name] = values.clamped()
    _state["active_template"] = name
    save()


def delete_template(name: str) -> bool:
    if name in _state["user_templates"]:
        del _state["user_templates"][name]
        if _state["active_template"] == name:
            _state["active_template"] = "Standard"
        save()
        return True
    return False


def load() -> None:
    if not CONFIG_PATH.exists():
        return
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return

    known = {f.name for f in fields(Settings)}
    values = {k: float(v) for k, v in raw.get("values", {}).items() if k in known}
    if values:
        apply(Settings(**{**asdict(Settings()), **values}))

    templates = {}
    for name, data in raw.get("user_templates", {}).items():
        clean = {k: float(v) for k, v in data.items() if k in known}
        templates[name] = Settings(**{**asdict(Settings()), **clean}).clamped()
    _state["user_templates"] = templates
    _state["active_template"] = raw.get("active_template", "Standard")
    _state["device"] = raw.get("device")
    _state["language"] = raw.get("language", "en")
    _state["profile"] = raw.get("profile", "feminin")
    _state["live_profile"] = raw.get("live_profile", "none")
    stored = raw.get("view")
    _state["view"] = stored if isinstance(stored, dict) else {}
    profiles = raw.get("user_profiles")
    _state["user_profiles"] = profiles if isinstance(profiles, dict) else {}
    overrides = raw.get("builtin_overrides")
    _state["builtin_overrides"] = overrides if isinstance(overrides, dict) else {}
    # Uebernahme aus der Fassung mit nur einem festen Ziel.
    legacy = raw.get("custom_target")
    if isinstance(legacy, dict) and legacy and not _state["user_profiles"]:
        _state["user_profiles"] = {LEGACY_PROFILE_NAME: legacy}
        if _state.get("profile") == "custom":
            _state["profile"] = "user:" + LEGACY_PROFILE_NAME
    _state["warn_low_level"] = bool(raw.get("warn_low_level", True))
    _state["recording_type"] = raw.get("recording_type", "reading")
    i18n.set_language(_state["language"])


def save() -> None:
    payload = {
        "active_template": _state["active_template"],
        "device": _state["device"],
        "language": _state["language"],
        "profile": _state["profile"],
        "live_profile": _state["live_profile"],
        "view": _state["view"],
        "user_profiles": _state["user_profiles"],
        "builtin_overrides": _state["builtin_overrides"],
        "warn_low_level": _state["warn_low_level"],
        "recording_type": _state["recording_type"],
        "values": asdict(CFG),
        "user_templates": {n: asdict(s) for n, s in _state["user_templates"].items()},
    }
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CONFIG_PATH)
