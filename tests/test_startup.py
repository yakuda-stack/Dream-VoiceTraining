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

"""Der Startablauf — vor allem seine Reihenfolge.

Ein eingestelltes Design ueberlebte den Neustart nicht: theming.restore()
lief vor settings.load() und bekam deshalb den leeren Vorgabewert zu
sehen, mit dem es jedes Mal die Vorlagenfarben setzte.
"""

import pytest

import settings
import theming


@pytest.fixture(autouse=True)
def frisches_design():
    """Das Design ist Modulzustand — nach dem Test wieder herstellen."""
    vorher = theming.snapshot()
    yield
    theming.restore(vorher)


def test_design_ueberlebt_den_neustart():
    theming.apply(colors={"accent": "#ff00aa", "bg": "#101820"},
                  bg_image="/tmp/bild.png", opacity=70)
    settings.set_theme(theming.snapshot())

    # Neustart: nichts mehr im Speicher, alles nur noch in der Datei.
    theming.reset_colors()
    theming.apply(bg_image=None, opacity=100)
    settings._state["theme"] = {}
    assert theming.COLORS["accent"] != "#ff00aa"

    settings.load()
    theming.restore(settings.get_theme())

    assert theming.COLORS["accent"] == "#ff00aa"
    assert theming.COLORS["bg"] == "#101820"
    assert theming.background() == "/tmp/bild.png"
    assert theming.card_opacity() == 70


def test_leeres_design_raeumt_nichts_ab():
    """restore({}) heisst "nichts gespeichert", nicht "zuruecksetzen"."""
    theming.apply(colors={"accent": "#ff00aa"})
    theming.restore({})
    assert theming.COLORS["accent"] == "#ff00aa"
    theming.restore(None)
    assert theming.COLORS["accent"] == "#ff00aa"


def test_design_wird_erst_nach_der_konfiguration_gesetzt(monkeypatch):
    """Die Reihenfolge in load_state(), gegen einen Rueckfall abgesichert."""
    import i18n
    import main
    import paths

    schritte = []
    monkeypatch.setattr(paths, "ensure_dirs", lambda: None)
    monkeypatch.setattr(paths, "migrate_from", lambda _: [])
    monkeypatch.setattr(settings, "load",
                        lambda: schritte.append("konfiguration"))
    monkeypatch.setattr(theming, "restore",
                        lambda data: schritte.append("design"))
    monkeypatch.setattr(i18n, "set_language",
                        lambda code: schritte.append("sprache"))

    main.load_state()

    assert schritte == ["konfiguration", "design", "sprache"]
