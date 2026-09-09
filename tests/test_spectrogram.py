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
    image, duration, top = audio.spectrogram(_ton(2.0, 16000), 16000)
    assert image.ndim == 2
    assert duration == pytest.approx(2.0)
    assert top == 5000.0
    # Zweite Achse sind die Frequenzbaender bis top.
    assert image.shape[1] == int(5000.0 / (16000 / 1024)) + 1


def test_lange_aufnahme_bekommt_nicht_mehr_spalten_als_noetig():
    """Eine Stunde Ton ergaebe bei festem Vorschub Millionen Spalten."""
    kurz, _, _ = audio.spectrogram(_ton(5.0, 16000), 16000, max_columns=200)
    lang, _, _ = audio.spectrogram(_ton(300.0, 16000), 16000, max_columns=200)
    assert kurz.shape[0] <= 201
    assert lang.shape[0] <= 201
    assert lang.shape[1] == kurz.shape[1]


def test_der_ton_liegt_im_richtigen_band():
    rate = 16000
    image, _, top = audio.spectrogram(_ton(2.0, rate, freq=1000.0), rate)
    schritt = rate / 1024
    band = int(round(1000.0 / schritt))
    mitte = image[image.shape[0] // 2]
    assert int(np.argmax(mitte)) == pytest.approx(band, abs=1)


def test_zu_kurzes_signal_ergibt_ein_leeres_bild():
    image, duration, top = audio.spectrogram(np.zeros(100, dtype=np.float32),
                                             16000)
    assert image.shape[0] == 1
    assert duration == 0.0
    assert top == 5000.0


def test_obere_frequenz_folgt_der_abtastrate():
    """Ueber die halbe Abtastrate hinaus gibt es nichts zu zeigen."""
    _, _, top = audio.spectrogram(_ton(1.0, 8000), 8000)
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
