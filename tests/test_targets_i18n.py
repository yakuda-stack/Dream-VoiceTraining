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


def test_eingebaute_vorlagen_heissen_in_beiden_sprachen_richtig():
    """Die Namen standen frueher deutsch im Code und blieben es auch im EN."""
    for name in settings.BUILTIN_TEMPLATES:
        assert f"tpl_{name}" in i18n.STRINGS, name
    i18n.set_language("en")
    assert settings.template_label("quiet_mic") == "Quiet microphone"
    i18n.set_language("de")
    assert settings.template_label("quiet_mic") == "Leises Mikrofon"
    # Eigene Vorlagen heissen so, wie der Benutzer sie genannt hat.
    assert settings.template_label("Meins") == "Meins"
    i18n.set_language("en")


def test_alte_vorlagennamen_werden_uebernommen():
    """Wer von 1.0.5 kommt, hat den deutschen Namen in der Konfiguration."""
    import json
    import paths
    paths.ensure_dirs()
    paths.CONFIG_PATH.write_text(
        json.dumps({"active_template": "Leises Mikrofon"}), encoding="utf-8")
    settings.load()
    assert settings.active_template() == "quiet_mic"
    assert settings.active_template() in settings.BUILTIN_TEMPLATES
    paths.CONFIG_PATH.unlink()


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
    for key in ("f0_median", "f0_p10", "f0_p90", "f0_sd_st", "f0_range_st"):
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


def test_profile_beschreiben_nur_die_tonhoehe():
    """Formanten bleiben absichtlich offen — im Lesetext wären sie ohne Aussage."""
    for name, ranges in targets.PROFILES.items():
        for key in ("f1_median", "f2_median", "f3_median", "h1_h2"):
            assert key not in ranges, f"{name}: {key}"
        assert targets.range_for("f2_median", name) is None, name


def test_qualitaetsgrenzen_gelten_weiterhin():
    """Abgeschaltete Ziele heißen nicht, dass Warnungen verschwinden."""
    for name in targets.PROFILES:
        assert targets.range_for("peak_db", name) == (-30.0, -8.0)
        assert targets.range_for("hnr", name) == (15.0, None)
