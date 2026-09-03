"""Einstellungen, Vorlagen und Persistenz."""

import importlib
import json

import pytest

import settings


def test_grenzen_werden_eingehalten():
    clamped = settings.Settings(pitch_floor=9999.0, voicing_threshold=5.0,
                                min_voiced_ratio=-3.0).clamped()
    for param in settings.PARAMS:
        value = getattr(clamped, param.attr)
        assert param.lo <= value <= param.hi, param.attr


def test_widerspruechliche_grenzen_werden_korrigiert():
    clamped = settings.Settings(pitch_floor=200.0, pitch_ceiling=150.0,
                                zone_low=250.0, zone_high=100.0).clamped()
    assert clamped.pitch_ceiling > clamped.pitch_floor
    assert clamped.zone_high > clamped.zone_low


def test_apply_wirkt_auf_die_singleton_instanz():
    settings.apply(settings.Settings(pitch_floor=88.0))
    assert settings.CFG.pitch_floor == 88.0
    from settings import CFG
    assert CFG.pitch_floor == 88.0


def test_eingebaute_vorlagen_sind_gueltig():
    for name, template in settings.BUILTIN_TEMPLATES.items():
        assert template.clamped() == template, name


def test_eigene_vorlage_speichern_und_loeschen():
    settings.save_template("Testziel", settings.Settings(pitch_floor=90.0))
    assert "Testziel" in settings.all_templates()
    assert not settings.is_builtin("Testziel")
    assert settings.delete_template("Testziel") is True
    assert "Testziel" not in settings.all_templates()


def test_eingebaute_vorlage_ist_nicht_loeschbar():
    assert settings.delete_template(settings.DEFAULT_TEMPLATE) is False


def test_persistenz_ueber_einen_neustart(tmp_path, monkeypatch):
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "home"))
    import paths
    importlib.reload(paths)
    importlib.reload(settings)

    paths.ensure_dirs()
    settings.apply(settings.Settings(pitch_floor=77.0, voicing_threshold=0.8))
    settings.set_language("de")
    settings.set_device("mein-mikro")
    settings.save_template("Meins", settings.snapshot())

    stored = json.loads(paths.CONFIG_PATH.read_text(encoding="utf-8"))
    assert stored["language"] == "de"
    assert stored["device"] == "mein-mikro"

    settings.apply(settings.Settings())
    settings._state["user_templates"] = {}
    settings.load()
    assert settings.CFG.pitch_floor == 77.0
    assert settings.get_language() == "de"
    assert "Meins" in settings.all_templates()

    monkeypatch.delenv("DREAM_VOICETRAINING_HOME")
    importlib.reload(paths)
    importlib.reload(settings)


def test_defekte_konfiguration_kippt_das_programm_nicht(tmp_path, monkeypatch):
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "kaputt"))
    import paths
    importlib.reload(paths)
    importlib.reload(settings)
    paths.ensure_dirs()
    paths.CONFIG_PATH.write_text("{kein json", encoding="utf-8")
    settings.load()
    assert settings.CFG.pitch_floor == settings.Settings().pitch_floor

    monkeypatch.delenv("DREAM_VOICETRAINING_HOME")
    importlib.reload(paths)
    importlib.reload(settings)
