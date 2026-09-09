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

"""Uebungstexte: das Modul und die Auswahl im Livebereich."""

import pytest

import i18n
import practice
import settings


# ------------------------------------------------------------ das Modul

def test_ohne_eigene_gibt_es_nur_den_eingebauten():
    assert practice.keys() == [practice.BUILTIN]
    assert practice.body(practice.BUILTIN) == i18n.t("practice_body")


def test_eigene_stehen_nach_namen_sortiert_dahinter():
    settings.save_practice_text("Zweiter", "zwei")
    settings.save_practice_text("Erster", "eins")
    assert practice.keys() == [practice.BUILTIN, "user:Erster", "user:Zweiter"]
    assert practice.label("user:Erster") == "Erster"
    assert practice.body("user:Zweiter") == "zwei"


def test_eingebauter_text_wechselt_die_sprache_mit_eigene_nicht():
    settings.save_practice_text("Meiner", "Mein eigener Text.")
    i18n.set_language("en")
    englisch = practice.body(practice.BUILTIN)
    assert practice.label(practice.BUILTIN) == "Built-in text"
    i18n.set_language("de")
    assert practice.body(practice.BUILTIN) != englisch
    assert practice.body("user:Meiner") == "Mein eigener Text."
    i18n.set_language("en")


def test_geloeschter_text_faellt_auf_den_eingebauten_zurueck():
    """Der Schluessel in der Konfiguration kann ins Leere zeigen."""
    settings.save_practice_text("Weg", "verschwindet")
    assert practice.resolve("user:Weg") == "user:Weg"
    settings.delete_practice_text("Weg")
    assert practice.resolve("user:Weg") == practice.BUILTIN
    assert practice.body("user:Weg") == i18n.t("practice_body")


def test_name_wird_auf_eine_zeile_gebracht():
    assert practice.clean_name("  Mein\nText  ") == "Mein Text"
    assert len(practice.clean_name("x" * 200)) == practice.MAX_NAME


def test_auswahl_ueberlebt_den_neustart(tmp_path):
    settings.save_practice_text("Bleibt", "bleibt stehen")
    settings.set_practice_choice("user:Bleibt")
    settings._state["practice_texts"] = {}
    settings._state["practice_choice"] = "builtin"
    settings.load()
    assert settings.get_practice_choice() == "user:Bleibt"
    assert practice.body("user:Bleibt") == "bleibt stehen"


# ------------------------------------------------------- die Oberflaeche

def _keys_in_box(window):
    box = window.practice_box
    return [box.itemData(i) for i in range(box.count())]


def test_liste_zeigt_den_eingebauten_text(intro_window):
    window = intro_window
    assert _keys_in_box(window) == [practice.BUILTIN]
    assert window.practice_edit.toPlainText() == i18n.t("practice_body")
    assert not window.btn_practice_delete.isEnabled()


def test_speichern_legt_einen_eigenen_text_an(intro_window, monkeypatch):
    from PySide6 import QtWidgets

    window = intro_window
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText",
                        staticmethod(lambda *a, **k: ("Aufwärmen", True)))
    window.practice_edit.setPlainText("Mein Aufwärmtext.")
    window._save_practice()

    assert settings.get_practice_texts() == {"Aufwärmen": "Mein Aufwärmtext."}
    assert _keys_in_box(window) == [practice.BUILTIN, "user:Aufwärmen"]
    assert window.practice_box.currentData() == "user:Aufwärmen"
    assert settings.get_practice_choice() == "user:Aufwärmen"
    assert window.btn_practice_delete.isEnabled()


def test_wechsel_setzt_den_text_und_merkt_sich_die_wahl(intro_window):
    window = intro_window
    settings.save_practice_text("Anderer", "Ein anderer Text.")
    window._fill_practice(select="user:Anderer")
    assert window.practice_edit.toPlainText() == "Ein anderer Text."

    window.practice_box.setCurrentIndex(
        window.practice_box.findData(practice.BUILTIN))
    assert window.practice_edit.toPlainText() == i18n.t("practice_body")
    assert settings.get_practice_choice() == practice.BUILTIN


def test_ungespeichertes_wird_nicht_stillschweigend_verworfen(intro_window,
                                                              monkeypatch):
    from PySide6 import QtWidgets

    window = intro_window
    settings.save_practice_text("Anderer", "Ein anderer Text.")
    window._fill_practice(select="user:Anderer")
    window.practice_edit.setPlainText("gerade erst getippt")

    asked = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: asked.append(1)
                     or QtWidgets.QMessageBox.StandardButton.No))

    window.practice_box.setCurrentIndex(
        window.practice_box.findData(practice.BUILTIN))

    assert asked, "Es wurde nicht nachgefragt"
    # Nachgefragt und abgelehnt: Auswahl und Text bleiben, wo sie waren.
    assert window.practice_box.currentData() == "user:Anderer"
    assert window.practice_edit.toPlainText() == "gerade erst getippt"


def test_loeschen_faellt_auf_den_eingebauten_zurueck(intro_window, monkeypatch):
    from PySide6 import QtWidgets

    window = intro_window
    settings.save_practice_text("Weg", "verschwindet")
    window._fill_practice(select="user:Weg")
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes))

    window._delete_practice()

    assert settings.get_practice_texts() == {}
    assert _keys_in_box(window) == [practice.BUILTIN]
    assert window.practice_edit.toPlainText() == i18n.t("practice_body")
    assert settings.get_practice_choice() == practice.BUILTIN


def test_leeres_feld_wird_nicht_gespeichert(intro_window, monkeypatch):
    from PySide6 import QtWidgets

    window = intro_window
    monkeypatch.setattr(QtWidgets.QMessageBox, "information",
                        staticmethod(lambda *a, **k: None))
    called = []
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getText",
        staticmethod(lambda *a, **k: called.append(1) or ("x", True)))

    window.practice_edit.setPlainText("   ")
    window._save_practice()

    assert not called, "Es wurde trotz leerem Feld nach einem Namen gefragt"
    assert settings.get_practice_texts() == {}
