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

"""Das Spektrogramm einer fertigen Aufnahme — Rechnung und Anzeige."""

import numpy as np
import pytest

import audio


def _ton(seconds=2.0, rate=16000, freq=400.0):
    n = int(seconds * rate)
    return (0.3 * np.sin(2 * np.pi * freq * np.arange(n) / rate)).astype(
        np.float32)


# --------------------------------------------------------- die Rechnung

def test_bild_ist_nach_spalten_und_baendern_geordnet():
    image, first, last, top = audio.spectrogram(_ton(2.0, 16000), 16000)
    assert image.ndim == 2
    assert top == 5000.0
    # Zweite Achse sind die Frequenzbaender bis top.
    assert image.shape[1] == int(5000.0 / (16000 / 1024)) + 1
    # Der abgedeckte Zeitraum liegt innerhalb der Aufnahme und faengt eine
    # halbe Fensterlaenge hinter dem Anfang an.
    assert 0.0 < first < 0.05
    assert last == pytest.approx(2.0, abs=0.05)


def test_zeitraum_passt_zur_wellenform():
    """Ohne die Randkorrektur saesse das Bild um ein Fenster daneben."""
    rate = 16000
    _, first, last, _ = audio.spectrogram(_ton(2.0, rate), rate)
    halbes_fenster = 512 / rate
    assert first == pytest.approx(halbes_fenster, abs=halbes_fenster)
    assert last <= 2.0 + 1e-6


def test_lange_aufnahme_bekommt_nicht_mehr_spalten_als_noetig():
    """Eine Stunde Ton ergaebe bei festem Vorschub Millionen Spalten."""
    kurz, _, _, _ = audio.spectrogram(_ton(5.0, 16000), 16000, max_columns=200)
    lang, _, _, _ = audio.spectrogram(_ton(300.0, 16000), 16000,
                                      max_columns=200)
    assert kurz.shape[0] <= 201
    assert lang.shape[0] <= 201
    assert lang.shape[1] == kurz.shape[1]


def test_der_ton_liegt_im_richtigen_band():
    rate = 16000
    image, _, _, top = audio.spectrogram(_ton(2.0, rate, freq=1000.0), rate)
    schritt = rate / 1024
    band = int(round(1000.0 / schritt))
    mitte = image[image.shape[0] // 2]
    assert int(np.argmax(mitte)) == pytest.approx(band, abs=1)


def test_zu_kurzes_signal_ergibt_ein_leeres_bild():
    image, first, last, top = audio.spectrogram(
        np.zeros(100, dtype=np.float32), 16000)
    assert image.shape[0] == 1
    assert (first, top) == (0.0, 5000.0)
    assert last == pytest.approx(100 / 16000)


def test_obere_frequenz_folgt_der_abtastrate():
    """Ueber die halbe Abtastrate hinaus gibt es nichts zu zeigen."""
    _, _, _, top = audio.spectrogram(_ton(1.0, 8000), 8000)
    assert top == 4000.0


# --------------------------------------------------------- die Anzeige

def test_spektrogramm_kommt_mit_der_wellenform(detail):
    # isHidden statt isVisible: das Fenster selbst wird hier nie gezeigt.
    detail._toggle_advanced(True)
    assert detail._spectrogram_done
    assert not detail.spec_plot.isHidden()
    assert detail.spec_img.image is not None


def test_haken_blendet_es_aus_und_wieder_ein(detail):
    detail._toggle_advanced(True)
    detail.chk_spec.setChecked(False)
    assert detail.spec_plot.isHidden()
    detail.chk_spec.setChecked(True)
    assert not detail.spec_plot.isHidden()


def test_beide_diagramme_haengen_an_derselben_zeitachse(detail):
    detail._toggle_advanced(True)
    assert detail.spec_plot.getPlotItem().vb.linkedView(0) is \
        detail.wave_plot.getPlotItem().vb


def test_auswahl_gilt_in_beiden_richtungen(detail):
    detail._toggle_advanced(True)

    detail.region.setRegion((0.4, 1.1))
    assert tuple(round(v, 3) for v in detail.spec_region.getRegion()) == \
        (0.4, 1.1)

    # Und andersherum: ziehen laesst sich die Auswahl auch unten.
    detail.spec_region.setRegion((1.2, 1.6))
    assert tuple(round(v, 3) for v in detail.region.getRegion()) == (1.2, 1.6)
    assert "1.20" in detail.range_label.text()


def test_ganze_aufnahme_zieht_beide_auf(detail):
    detail._toggle_advanced(True)
    detail.region.setRegion((0.4, 1.1))

    detail._show_full()

    assert tuple(round(v, 2) for v in detail.spec_region.getRegion()) == \
        (0.0, round(detail._duration, 2))


def test_ohne_datei_gibt_es_kein_bild(qt_app, tmp_path, monkeypatch):
    import dialogs
    import storage

    monkeypatch.setattr(storage, "root", lambda: tmp_path)
    entry = {"timestamp": "2026-09-01T10:00:00", "file": "weg.wav",
             "quality": "ok"}
    dlg = dialogs.SessionDetailDialog(entry, [entry], tmp_path)
    try:
        dlg._toggle_advanced(True)          # darf nicht knallen
        assert not dlg._spectrogram_done
    finally:
        dlg.close()


def test_zoomen_rechnet_feiner_nach(detail):
    """Sonst zieht man beim Hineinzoomen nur ein paar Spalten auseinander."""
    detail._toggle_advanced(True)
    voll = detail.spec_img.image.shape[0]
    voll_span = detail._spec_span[1] - detail._spec_span[0]

    detail.spec_plot.getPlotItem().vb.setXRange(0.5, 0.9, padding=0)
    detail._render_spectrogram(force=True)

    span = detail._spec_span[1] - detail._spec_span[0]
    assert span < voll_span / 2
    # Ueber ein Zehntel der Zeit stehen wieder ungefaehr so viele Spalten
    # zur Verfuegung wie vorher ueber die ganze Aufnahme.
    assert detail.spec_img.image.shape[0] > voll / 2


def test_helligkeit_bleibt_beim_zoomen_stehen(detail):
    """Sonst saehe eine leise Stelle aus wie eine laute."""
    detail._toggle_advanced(True)
    vorher = detail._spec_levels
    detail.spec_plot.getPlotItem().vb.setXRange(0.4, 0.6, padding=0)
    detail._render_spectrogram(force=True)
    assert detail._spec_levels == vorher


def test_fenster_faellt_mit_dem_ausschnitt(detail):
    """Ein 64-ms-Fenster kann in 25 ms nichts unterscheiden."""
    rate = 16000
    assert detail._window_for(3.0, rate) == 1024
    assert detail._window_for(0.5, rate) < 1024
    assert detail._window_for(0.025, rate) == 128
    # Nie kleiner: darunter bliebe von der Frequenzachse nichts uebrig.
    assert detail._window_for(0.001, rate) == 128


def test_tiefer_zoom_liefert_zeitstruktur(detail):
    detail._toggle_advanced(True)
    view = detail.spec_plot.getPlotItem().vb

    view.setXRange(0.5, 1.5, padding=0)
    detail._render_spectrogram(force=True)
    weit = detail.spec_img.image.shape[1]

    view.setXRange(0.90, 0.93, padding=0)
    detail._render_spectrogram(force=True)
    nah = detail.spec_img.image.shape[1]

    # Kuerzeres Fenster heisst weniger Frequenzbaender — das ist der
    # Tausch, den man beim Hineinzoomen will.
    assert nah < weit
    assert detail.spec_img.image.shape[0] > 100


def test_wellenform_zeigt_im_zoom_die_abtastwerte(detail):
    """Die Huellkurve ueber die ganze Aufnahme waere hier eine Treppe."""
    detail._toggle_advanced(True)
    view = detail.wave_plot.getPlotItem().vb

    view.setXRange(0.0, detail._duration, padding=0)
    detail._render_waveform()
    xs, _ = detail.wave_curve.getData()
    weit = len(xs)

    view.setXRange(0.90, 0.93, padding=0)
    detail._render_waveform()
    xs, ys = detail.wave_curve.getData()

    # Im engen Ausschnitt steht je Abtastwert ein Punkt.
    assert len(xs) == pytest.approx(0.03 * detail._rate, rel=0.2)
    assert len(xs) < weit
    assert float(xs[0]) >= 0.89
