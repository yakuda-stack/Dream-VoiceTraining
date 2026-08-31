"""Zielbereiche und Vollstaendigkeit der Uebersetzungen."""

import re
from pathlib import Path

import pytest

import i18n
import settings
import targets

ROOT = Path(__file__).resolve().parents[1]


def test_jeder_text_hat_beide_sprachen():
    for key, entry in i18n.STRINGS.items():
        assert set(entry) == {"en", "de"}, key
        assert entry["en"].strip() and entry["de"].strip(), key


def test_alle_verwendeten_schluessel_existieren():
    used = set()
    for path in ROOT.glob("*.py"):
        used |= set(re.findall(r'i18n\.t\(\s*"([a-z0-9_]+)"', path.read_text(encoding="utf-8")))
    missing = sorted(used - set(i18n.STRINGS))
    assert not missing, f"fehlende Texte: {missing}"


def test_jeder_parameter_und_kennwert_ist_uebersetzt():
    for param in settings.PARAMS:
        assert f"param_{param.attr}" in i18n.STRINGS, param.attr
        assert f"param_{param.attr}_hint" in i18n.STRINGS, param.attr
    for metric in targets.METRICS:
        assert f"m_{metric.key}" in i18n.STRINGS, metric.key
        assert f"m_{metric.key}_hint" in i18n.STRINGS, metric.key


def test_platzhalter_stimmen_zwischen_den_sprachen():
    pattern = re.compile(r"\{(\w+)")
    for key, entry in i18n.STRINGS.items():
        assert set(pattern.findall(entry["en"])) == set(pattern.findall(entry["de"])), key


def test_sprachumschaltung():
    i18n.set_language("de")
    assert i18n.t("delete") == "Löschen"
    i18n.set_language("en")
    assert i18n.t("delete") == "Delete"
    i18n.set_language("klingonisch")
    assert i18n.LANG == "en"


def test_bewertung():
    i18n.set_language("en")
    assert targets.verdict(100.0, (150.0, 250.0)) == i18n.t("verdict_below")
    assert targets.verdict(200.0, (150.0, 250.0)) == i18n.t("verdict_within")
    assert targets.verdict(300.0, (150.0, 250.0)) == i18n.t("verdict_above")
    assert targets.verdict(None, (150.0, 250.0)) == ""
    assert targets.verdict(200.0, None) == ""


def test_is_within():
    assert targets.is_within(20.0, (15.0, None)) is True
    assert targets.is_within(10.0, (15.0, None)) is False
    assert targets.is_within(None, (15.0, None)) is None


def test_bereichsformat_bleibt_bei_negativen_werten_lesbar():
    i18n.set_language("en")
    text = targets.format_range((-30.0, -8.0), "dBFS", 0)
    assert "to" in text and "--" not in text
    assert targets.format_range((15.0, None), "dB", 1) == "≥ 15.0 dB"
    assert targets.format_range(None, "Hz", 0) == "—"


def test_alle_profile_haben_dieselben_kennwerte():
    keys = [set(v) for v in targets.PROFILES.values()]
    assert all(k == keys[0] for k in keys)
    for key in keys[0]:
        assert key in {m.key for m in targets.METRICS}


def test_profile_sind_aufsteigend_geordnet():
    """maskulin < androgyn < feminin bei den tonhoehenbezogenen Groessen."""
    for key in ("f0_median", "f2_median", "f3_median"):
        low = targets.PROFILES["maskulin"][key]
        mid = targets.PROFILES["androgyn"][key]
        high = targets.PROFILES["feminin"][key]
        assert low[0] < mid[0] < high[0], key
        assert low[1] < mid[1] < high[1], key


def test_spalten_haben_uebersetzte_beschriftungen():
    import columns
    for column in columns.COLUMNS:
        assert column.label_key in i18n.STRINGS, column.key
    assert set(columns.DEFAULT_VISIBLE) <= set(columns.BY_KEY)
