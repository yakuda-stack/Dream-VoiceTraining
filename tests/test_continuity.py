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

"""Was ueber einen Wechsel hinweg stehenbleiben soll.

Zwei Dinge, die sich nur im laufenden Betrieb zeigen und deshalb leicht
wieder kaputtgehen: die Markierung im Detailfenster und der Verlauf ueber
eine Pause hinweg.
"""

import numpy as np
import pytest


# ------------------------------------------------- Detailfenster: ganz

def test_full_button_locked_until_loaded(detail):
    """Ohne geladene Wellenform gibt es kein "ganz"."""
    assert not detail.btn_full.isEnabled()


def test_full_button_marks_everything(detail):
    detail.btn_advanced.setChecked(True)
    detail._toggle_advanced(True)
    assert detail.btn_full.isEnabled()

    # Voreinstellung ist das mittlere Drittel — nicht die ganze Aufnahme.
    low, high = detail.region.getRegion()
    assert high - low < detail._duration

    detail._show_full()
    low, high = detail.region.getRegion()
    assert low == pytest.approx(0.0, abs=1e-6)
    assert high == pytest.approx(detail._duration, abs=1e-6)


def test_full_button_stays_locked_without_file(qt_app, tmp_path, monkeypatch):
    """Fehlt die Datei, bleibt der Knopf gesperrt statt ins Leere zu greifen."""
    import storage
    import dialogs

    monkeypatch.setattr(storage, "root", lambda: tmp_path)
    entry = {"timestamp": "2026-09-01T10:00:00", "file": "weg.wav",
             "quality": "ok"}
    dlg = dialogs.SessionDetailDialog(entry, [entry], tmp_path)
    try:
        dlg._toggle_advanced(True)
        assert not dlg.btn_full.isEnabled()
        dlg._show_full()            # darf nicht knallen
    finally:
        dlg.close()


# --------------------------------------------------- Verlauf ueber Pause

def test_clock_ignores_the_pause(intro_window):
    """Die Uhr des Verlaufs steht still, solange der Stream steht."""
    window = intro_window

    window.run_seconds = 12.0
    window.elapsed.restart()
    first = window._clock()
    assert first == pytest.approx(12.0, abs=0.5)

    # Pause: run_seconds bekommt den bisherigen Lauf, elapsed faengt beim
    # naechsten Start von vorn an. Der Sprung darf nicht groesser werden
    # als das, was tatsaechlich gelaufen ist.
    window.run_seconds += window.elapsed.elapsed() / 1000.0
    window.elapsed.restart()
    assert window._clock() >= first
    assert window._clock() - first < 1.0


def test_history_survives_a_stop(intro_window, monkeypatch):
    """Stoppen und wieder starten leert weder Verlauf noch Spektrogramm."""
    window = intro_window

    # Stream ohne Audiohardware vortaeuschen: engine.running haengt allein
    # am gesetzten Stream, und engine.stop() faengt alles ab, was ein
    # Attrappenobjekt nicht kann.
    window.engine._stream = object()
    monkeypatch.setattr(
        window.engine, "start",
        lambda source=None: (setattr(window.engine, "_stream", object()), True)[1])

    # Ein Geraet, das nicht gesperrt ist — sonst kommt statt des Starts
    # ein modaler Hinweis.
    window.device_box.clear()
    window.device_box.addItem("Attrappe", 0)

    window.history.append((1.0, 180.0))
    window.spec[:] = -40.0

    window._toggle_stream()             # Stopp
    assert not window.engine.running
    window._toggle_stream()             # Start
    assert window.engine.running

    assert list(window.history) == [(1.0, 180.0)]
    assert float(window.spec.max()) == pytest.approx(-40.0)

    window.timer.stop()
    window.engine._stream = None


# ------------------------------------------- Fadenkreuz und Leeren

def _scene_pos(window, hz):
    """Die Bildschirmposition, an der im Verlauf diese Tonhoehe steht."""
    from PySide6 import QtCore

    view = window.pitch_plot.getPlotItem().vb
    left = view.viewRange()[0][0]
    return view.mapViewToScene(QtCore.QPointF(left, hz))


def test_cursor_shows_pitch_under_the_mouse(intro_window):
    window = intro_window
    assert not window.pitch_cursor.isVisible()

    window._pitch_hover(_scene_pos(window, 180.0))
    assert window.pitch_cursor.isVisible()
    assert window.pitch_cursor.value() == pytest.approx(180.0, abs=1.0)
    # Die Beschriftung bringt sich nur sichtbar auf Stand. Stuende hier
    # "0 Hz", waere sie vor dem Einblenden gesetzt worden.
    assert window.pitch_cursor.label.textItem.toPlainText().endswith("Hz")
    assert "180" in window.pitch_cursor.label.textItem.toPlainText()

    window._pitch_hover(_scene_pos(window, 250.0))
    assert window.pitch_cursor.value() == pytest.approx(250.0, abs=1.0)
    assert "250" in window.pitch_cursor.label.textItem.toPlainText()


def test_cursor_hides_beside_the_plot(intro_window):
    from PySide6 import QtCore

    window = intro_window
    window._pitch_hover(_scene_pos(window, 180.0))
    assert window.pitch_cursor.isVisible()

    # Weit ausserhalb der Zeichenflaeche — dort gibt es keinen Messwert.
    window._pitch_hover(QtCore.QPointF(-500.0, -500.0))
    assert not window.pitch_cursor.isVisible()


def test_clear_history_empties_the_curve(intro_window):
    window = intro_window
    window.history.extend([(1.0, 180.0), (2.0, 190.0)])
    window.pitch_curve.setData([1.0, 2.0], [180.0, 190.0])

    window._clear_history()

    assert not window.history
    xs, ys = window.pitch_curve.getData()
    assert xs is None or len(xs) == 0


def test_clear_spectrogram_empties_the_image(intro_window):
    window = intro_window
    window.spec[:] = -40.0

    window._clear_spectrogram()

    assert float(window.spec.max()) == pytest.approx(-100.0)
