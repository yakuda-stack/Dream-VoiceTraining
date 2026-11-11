"""Sprachdateien unter locales/ und ihr Einlesen."""

import json
from pathlib import Path

import pytest

from core import i18n

LOCALES = Path(__file__).resolve().parents[1] / "locales"


@pytest.fixture
def restore_languages():
    yield
    i18n.load()
    i18n.set_language("en")


def test_jede_datei_hat_lang_und_name():
    for path in LOCALES.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert list(data)[0] == "lang", path.name
        assert data["lang"].lower() == path.stem, path.name
        assert data["name"].strip(), path.name


def test_englisch_ist_vollstaendig_und_zuerst():
    assert i18n.LANGUAGES[0] == "en"
    english = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    for path in LOCALES.glob("*.json"):
        other = json.loads(path.read_text(encoding="utf-8"))
        assert set(other["strings"]) <= set(english["strings"]), path.name


def test_neue_datei_landet_im_dropdown(tmp_path, restore_languages):
    for path in LOCALES.glob("*.json"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"),
                                          encoding="utf-8")
    (tmp_path / "fr.json").write_text(json.dumps({
        "lang": "FR", "name": "Français",
        "strings": {"start": "Démarrer"}}), encoding="utf-8")

    i18n.load([tmp_path])
    assert ("fr", "Français") in i18n.available()

    i18n.set_language("fr")
    assert i18n.t("start") == "Démarrer"
    # Fehlende Texte fallen auf Englisch zurueck.
    assert i18n.t("stop") == "Stop"


def test_spaetere_ordner_ueberschreiben(tmp_path, restore_languages):
    user = tmp_path / "user"
    user.mkdir()
    (user / "de.json").write_text(json.dumps({
        "lang": "DE", "strings": {"start": "Los"}}), encoding="utf-8")

    i18n.load([LOCALES, user])
    i18n.set_language("de")
    assert i18n.t("start") == "Los"
    assert i18n.t("stop") == "Stopp"
    assert i18n.language_name("de") == "Deutsch"


def test_kaputte_datei_wird_uebersprungen(tmp_path, restore_languages):
    (tmp_path / "xx.json").write_text("{ kein json", encoding="utf-8")
    i18n.load([LOCALES, tmp_path])
    assert "xx" not in i18n.LANGUAGES
    assert "de" in i18n.LANGUAGES


def test_hauptfenster_hat_sprach_dropdown(qt_app):
    from main import MainWindow

    window = MainWindow()
    try:
        codes = [window.lang_box.itemData(i)
                 for i in range(window.lang_box.count())]
        assert codes == list(i18n.LANGUAGES)
    finally:
        window.close()
