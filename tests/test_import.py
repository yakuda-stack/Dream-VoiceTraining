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

"""Import vorhandener Dateien in die Sessionliste."""

import os
import wave
from datetime import datetime

import numpy as np
import pytest

import audio
import storage


@pytest.fixture
def ordner(tmp_path, monkeypatch):
    """Aufnahmeordner und Quellordner, beide unter tmp_path."""
    target = tmp_path / "sessions"
    target.mkdir()
    monkeypatch.setattr(storage, "root", lambda: target)
    source = tmp_path / "quelle"
    source.mkdir()
    return target, source


def _write(path, seconds=1.0, rate=16000, f0=150.0, width=2, channels=1):
    """Eine WAV-Datei mit gewaehlter Bittiefe und Kanalzahl."""
    n = int(seconds * rate)
    tone = 0.3 * np.sin(2 * np.pi * f0 * np.arange(n) / rate)
    scale = {1: 127, 2: 32767, 3: (1 << 23) - 1, 4: (1 << 31) - 1}[width]
    ints = (tone * scale).astype(np.int64)
    if channels > 1:
        ints = np.repeat(ints, channels)
    if width == 1:
        raw = (ints + 128).astype(np.uint8).tobytes()
    elif width == 3:
        raw = np.stack([(ints >> shift) & 255 for shift in (0, 8, 16)],
                       axis=1).astype(np.uint8).tobytes()
    else:
        raw = ints.astype(f"<i{width}").tobytes()
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(raw)
    return path


# ------------------------------------------------------------ read_wav

@pytest.mark.parametrize("width", [1, 2, 3, 4])
def test_alle_bittiefen_werden_gelesen(tmp_path, width):
    path = _write(tmp_path / f"w{width}.wav", seconds=0.5, width=width)
    data, rate = audio.read_wav(path)
    assert rate == 16000
    assert data.size == 8000
    # 8 Bit ist grob, der Rest genau — der Pegel muss trotzdem stimmen.
    assert float(np.abs(data).max()) == pytest.approx(0.3, abs=0.02)


def test_stereo_wird_gemittelt(tmp_path):
    path = _write(tmp_path / "st.wav", seconds=0.5, channels=2)
    data, _ = audio.read_wav(path)
    assert data.size == 8000


def test_gleitkomma_wav_wirft_eine_wave_error(tmp_path):
    """Nicht lesbar — aber mit einem Fehler, den der Import abfangen kann."""
    path = tmp_path / "float.wav"
    # WAVE_FORMAT_IEEE_FLOAT (3) von Hand zusammengesetzt.
    import struct
    data = np.zeros(100, dtype="<f4").tobytes()
    header = (b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
              + struct.pack("<IHHIIHH", 16, 3, 1, 16000, 64000, 4, 32)
              + b"data" + struct.pack("<I", len(data)))
    path.write_bytes(header + data)
    with pytest.raises(wave.Error):
        audio.read_wav(path)


# -------------------------------------------------------- Importablauf

def test_import_legt_eintrag_und_kopie_an(intro_window, ordner):
    target, source = ordner
    window = intro_window
    quelle = _write(source / "probe.wav", seconds=1.0, rate=16000)
    # Aenderungsdatum als Aufnahmezeitpunkt.
    wann = datetime(2026, 3, 14, 9, 5, 0)
    os.utime(quelle, (wann.timestamp(), wann.timestamp()))

    vorher = len(window.sessions)
    added, failed = window._import_all([str(quelle)], "reading")

    assert (added, failed) == (1, [])
    assert len(window.sessions) == vorher + 1
    entry = window.sessions[-1]
    assert entry["type"] == "reading"
    assert entry["timestamp"].startswith("2026-03-14T09:05")
    # Das Original bleibt liegen, im Aufnahmeordner steht eine Kopie.
    assert quelle.exists()
    assert storage.path_for(entry["file"]).exists()


def test_import_behaelt_die_abtastrate_der_datei(intro_window, ordner):
    """Mit der falschen Rate laegen Tonhoehe und Formanten daneben."""
    target, source = ordner
    window = intro_window
    quelle = _write(source / "acht.wav", seconds=1.5, rate=8000, f0=150.0)

    window._import_all([str(quelle)], "reading")
    entry = window.sessions[-1]

    kopie, rate = audio.read_wav(storage.path_for(entry["file"]))
    assert rate == 8000
    assert entry["duration"] == pytest.approx(1.5, abs=0.05)
    assert entry["f0_median"] == pytest.approx(150.0, rel=0.05)


def test_kaputte_datei_stoppt_den_durchgang_nicht(intro_window, ordner):
    target, source = ordner
    window = intro_window
    gut1 = _write(source / "a.wav", seconds=0.6)
    kaputt = source / "b.wav"
    kaputt.write_bytes(b"das ist kein WAV")
    gut2 = _write(source / "c.wav", seconds=0.6)

    vorher = len(window.sessions)
    added, failed = window._import_all(
        [str(gut1), str(kaputt), str(gut2)], "reading")

    assert added == 2
    assert len(failed) == 1 and "b.wav" in failed[0]
    assert len(window.sessions) == vorher + 2


def test_zu_kurze_datei_wird_abgewiesen(intro_window, ordner):
    target, source = ordner
    window = intro_window
    winzig = _write(source / "kurz.wav", seconds=0.05)

    added, failed = window._import_all([str(winzig)], "reading")

    assert added == 0
    assert len(failed) == 1


def test_import_behaelt_den_dateinamen(intro_window, ordner):
    """In der Liste soll stehen, wie die Datei vorher hiess."""
    import columns

    target, source = ordner
    window = intro_window
    quelle = _write(source / "Morgen Übung 1.wav", seconds=0.6)

    window._import_all([str(quelle)], "reading")
    entry = window.sessions[-1]

    assert entry["file"] == "Morgen Übung 1.wav"
    assert columns.display_name(entry) == "Morgen Übung 1"
    assert storage.path_for(entry["file"]).exists()


def test_gleicher_name_zweimal_bekommt_eine_nummer(intro_window, ordner):
    target, source = ordner
    window = intro_window
    unter = source / "unter"
    unter.mkdir()
    erste = _write(source / "probe.wav", seconds=0.6)
    zweite = _write(unter / "probe.wav", seconds=0.6)

    window._import_all([str(erste), str(zweite)], "reading")
    namen = [e["file"] for e in window.sessions[-2:]]

    assert namen == ["probe.wav", "probe-2.wav"]
    # Beide Dateien liegen wirklich da, keine hat die andere ueberschrieben.
    assert all(storage.path_for(name).exists() for name in namen)


def test_unbrauchbarer_name_faellt_auf_das_schema_zurueck(intro_window, ordner):
    target, source = ordner
    window = intro_window
    quelle = _write(source / "....wav", seconds=0.6)

    window._import_all([str(quelle)], "reading")
    entry = window.sessions[-1]

    # Kein Name aus lauter Punkten, sondern der erzeugte.
    assert entry["file"].endswith(".wav")
    assert entry["file"].strip(". ") == entry["file"]
    assert storage.path_for(entry["file"]).exists()


def test_uebernommener_name_ueberlebt_einen_umzug(intro_window, ordner):
    """Ein Umzug soll ihn in den Ordner schieben, nicht umbenennen."""
    target, source = ordner
    window = intro_window
    quelle = _write(source / "Morgen Übung 1.wav", seconds=0.6)
    window._import_all([str(quelle)], "reading")
    entry = window.sessions[-1]

    ziel = storage.target_name(entry, {"subfolders": "month",
                                       "enabled": {"date": True}})
    assert ziel.endswith("Morgen Übung 1.wav")


def test_clean_stem_laesst_lesbares_stehen():
    import naming

    assert naming.clean_stem("Morgen Übung 1") == "Morgen Übung 1"
    assert naming.clean_stem("abend_lesetext") == "abend_lesetext"
    # Verboten oder ordnereroeffnend: raus.
    assert "/" not in naming.clean_stem("a/b")
    assert ":" not in naming.clean_stem("10:30 Probe")
    assert naming.clean_stem("...") == ""
    assert len(naming.clean_stem("x" * 300)) == naming.MAX_STEM


def test_import_nimmt_eigene_typen(intro_window, ordner):
    import rectypes
    import settings

    target, source = ordner
    window = intro_window
    settings.save_user_type("aufwaermen", "Aufwärmen")
    quelle = _write(source / "probe.wav", seconds=0.6)

    window._import_all([str(quelle)], "user:aufwaermen")
    entry = window.sessions[-1]

    assert entry["type"] == "user:aufwaermen"
    assert rectypes.label(entry["type"]) == "Aufwärmen"


def test_typabfrage_liefert_den_schluessel(intro_window, monkeypatch):
    from PySide6 import QtWidgets

    import i18n
    import rectypes

    window = intro_window
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getItem",
        staticmethod(lambda *a, **k: (i18n.t("type_hum"), True)))
    assert window._ask_import_type(3) == "hum"

    monkeypatch.setattr(QtWidgets.QInputDialog, "getItem",
                        staticmethod(lambda *a, **k: ("", False)))
    assert window._ask_import_type(3) is None
    assert rectypes.exists("hum")


def test_abbruch_im_dateidialog_importiert_nichts(intro_window, monkeypatch):
    from PySide6 import QtWidgets

    window = intro_window
    monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileNames",
                        staticmethod(lambda *a, **k: ([], "")))
    gefragt = []
    monkeypatch.setattr(window, "_ask_import_type",
                        lambda count: gefragt.append(1))

    vorher = len(window.sessions)
    window._import_files()

    assert not gefragt, "Es wurde trotz Abbruch nach dem Typ gefragt"
    assert len(window.sessions) == vorher


def test_ganzer_ablauf_landet_in_der_tabelle(intro_window, ordner, monkeypatch):
    from PySide6 import QtWidgets

    import i18n
    import main

    target, source = ordner
    window = intro_window
    quelle = _write(source / "probe.wav", seconds=0.8)

    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getOpenFileNames",
        staticmethod(lambda *a, **k: ([str(quelle)], "")))
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getItem",
        staticmethod(lambda *a, **k: (i18n.t("type_free"), True)))

    zeilen = window.table.rowCount()
    window._import_files()

    assert window.table.rowCount() == zeilen + 1
    entry = window.sessions[-1]
    assert entry["type"] == "free"
    # Und die Liste liegt auf der Platte, nicht nur im Speicher.
    assert entry["file"] in main.SESSION_INDEX.read_text(encoding="utf-8")
