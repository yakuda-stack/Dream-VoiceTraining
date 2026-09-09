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

"""Eigene Aufnahmetypen: Kuerzel, Dateinamen und die Verwaltung."""

from datetime import datetime

import pytest

import i18n
import naming
import rectypes
import settings


# ----------------------------------------------------------- Kuerzel

def test_kuerzel_enthaelt_nur_erlaubte_zeichen():
    code = rectypes.make_slug("Mein Übungs_Typ!")
    assert naming.SEPARATOR not in code
    assert code == code.lower()
    assert all(c.isalnum() or c == "-" for c in code)


def test_kuerzel_weicht_einem_vergebenen_aus():
    assert rectypes.make_slug("Reading") == "reading-2"
    settings.save_user_type("mein-typ", "Mein Typ")
    # Anderer Name, gleiches Kuerzel — im Ordner waeren beide dasselbe.
    assert rectypes.make_slug("mein typ") == "mein-typ-2"


def test_kuerzel_ist_nie_leer():
    assert rectypes.make_slug("!!!") == "typ"
    assert rectypes.make_slug("") == "typ"


# ------------------------------------------------------------ Zugriff

def test_eigene_typen_stehen_hinter_den_eingebauten():
    settings.save_user_type("zischen", "Zischlaute")
    settings.save_user_type("aufwaermen", "Aufwärmen")
    keys = [kind.key for kind in rectypes.all_types()]
    assert keys[:len(rectypes.TYPES)] == [k.key for k in rectypes.TYPES]
    # Eigene nach Namen sortiert.
    assert keys[len(rectypes.TYPES):] == ["user:aufwaermen", "user:zischen"]


def test_eigener_typ_heisst_in_jeder_sprache_gleich():
    settings.save_user_type("aufwaermen", "Aufwärmen")
    for lang in ("en", "de"):
        i18n.set_language(lang)
        assert rectypes.label("user:aufwaermen") == "Aufwärmen"
        assert rectypes.get("user:aufwaermen").hint.strip()
    i18n.set_language("en")


def test_geloeschter_typ_zeigt_sein_kuerzel_statt_lesetext():
    """Sonst behauptete die Liste, die Aufnahme sei ein Lesetext."""
    settings.save_user_type("zischen", "Zischlaute")
    assert rectypes.label("user:zischen") == "Zischlaute"

    settings.delete_user_type("zischen")
    assert rectypes.exists("user:zischen") is False
    assert rectypes.label("user:zischen") == "zischen"
    # Fuers Verhalten bleibt es der Standardtyp.
    assert rectypes.get("user:zischen").key == rectypes.DEFAULT
    # Das Kuerzel bleibt, damit die alten Dateien zuzuordnen sind.
    assert rectypes.slug("user:zischen") == "zischen"


def test_unbekannter_typ_faellt_weiter_zurueck():
    assert rectypes.get(None).key == rectypes.DEFAULT
    assert rectypes.get("gibt-es-nicht").key == rectypes.DEFAULT


def test_typen_ueberleben_den_neustart():
    settings.save_user_type("aufwaermen", "Aufwärmen")
    settings._state["user_types"] = {}
    settings.load()
    assert settings.get_user_types() == {"aufwaermen": "Aufwärmen"}


# ------------------------------------------------------- im Dateinamen

def test_eigenes_kuerzel_landet_im_dateinamen():
    settings.save_user_type("aufwaermen", "Aufwärmen")
    scheme = naming.normalize({"enabled": {"date": True, "type": True}})
    stem = naming.build_stem(scheme, datetime(2026, 3, 14, 9, 5),
                             "user:aufwaermen")
    assert stem == "2026-03-14_09-05-00_aufwaermen"


def test_eigenes_kuerzel_gilt_als_selbst_vergeben():
    """Sonst liesse der Umzug die betroffenen Dateien liegen."""
    settings.save_user_type("aufwaermen", "Aufwärmen")
    assert naming.looks_generated("2026-03-14_aufwaermen") is True
    # Ohne den Typ in der Konfiguration ist es ein fremder Name.
    settings.delete_user_type("aufwaermen")
    assert naming.looks_generated("2026-03-14_aufwaermen") is False


# ------------------------------------------------------- die Verwaltung

@pytest.fixture
def options(qt_app):
    import dialogs
    entries = [{"timestamp": "2026-09-01T10:00:00", "file": "a.wav",
                "type": "user:zischen", "quality": "ok"},
               {"timestamp": "2026-09-02T10:00:00", "file": "b.wav",
                "type": "reading", "quality": "ok"}]
    page = dialogs.OptionsPage(entries)
    yield page
    page.deleteLater()


def _listed(page):
    return [page.type_list.item(i).data(0x0100)      # UserRole
            for i in range(page.type_list.count())]


def test_liste_zeigt_alle_typen(options):
    assert _listed(options) == [kind.key for kind in rectypes.all_types()]
    # Eingebaute lassen sich nicht loeschen.
    options.type_list.setCurrentRow(0)
    assert not options.btn_type_delete.isEnabled()


def test_anlegen_erzeugt_typ_und_meldet_das(options, monkeypatch):
    from PySide6 import QtWidgets

    monkeypatch.setattr(QtWidgets.QInputDialog, "getText",
                        staticmethod(lambda *a, **k: ("Zischlaute", True)))
    seen = []
    options.types_changed.connect(lambda: seen.append(1))

    options._add_type()

    assert settings.get_user_types() == {"zischlaute": "Zischlaute"}
    assert "user:zischlaute" in _listed(options)
    assert options.btn_type_delete.isEnabled()
    assert seen, "types_changed wurde nicht gemeldet"


def test_doppelter_name_wird_abgewiesen(options, monkeypatch):
    from PySide6 import QtWidgets

    warned = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning",
                        staticmethod(lambda *a, **k: warned.append(1)))
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getText",
        staticmethod(lambda *a, **k: (i18n.t("type_reading"), True)))

    options._add_type()

    assert warned, "Der doppelte Name ging durch"
    assert settings.get_user_types() == {}


def test_loeschen_warnt_vor_betroffenen_aufnahmen(options, monkeypatch):
    from PySide6 import QtWidgets

    settings.save_user_type("zischen", "Zischlaute")
    options._fill_types(select="user:zischen")

    gezeigt = []

    def frage(parent, title, body, *a, **k):
        gezeigt.append(body)
        return QtWidgets.QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QtWidgets.QMessageBox, "question", staticmethod(frage))
    options._delete_type()

    assert gezeigt, "Es wurde nicht nachgefragt"
    # Die eine betroffene Aufnahme aus der Vorrichtung wird benannt.
    assert "1" in gezeigt[0] and "zischen" in gezeigt[0]
    assert settings.get_user_types() == {}


def test_abgelehntes_loeschen_laesst_den_typ_stehen(options, monkeypatch):
    from PySide6 import QtWidgets

    settings.save_user_type("zischen", "Zischlaute")
    options._fill_types(select="user:zischen")
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.No))

    options._delete_type()

    assert settings.get_user_types() == {"zischen": "Zischlaute"}


# ------------------------------------------------------ im Hauptfenster

def test_auswahl_im_livebereich_kennt_eigene_typen(intro_window):
    window = intro_window
    settings.save_user_type("aufwaermen", "Aufwärmen")
    window._fill_types()

    keys = [window.type_box.itemData(i)
            for i in range(window.type_box.count())]
    assert keys[-1] == "user:aufwaermen"
    assert window.type_box.itemText(len(keys) - 1) == "Aufwärmen"


def test_geloeschter_typ_raeumt_die_einstellung_auf(intro_window):
    """Sonst bekaeme die naechste Aufnahme ein Kuerzel ohne Typ dahinter."""
    window = intro_window
    settings.save_user_type("aufwaermen", "Aufwärmen")
    window._fill_types()
    window.type_box.setCurrentIndex(window.type_box.count() - 1)
    assert settings.get_recording_type() == "user:aufwaermen"

    settings.delete_user_type("aufwaermen")
    window._fill_types()
    assert settings.get_recording_type() == rectypes.DEFAULT
