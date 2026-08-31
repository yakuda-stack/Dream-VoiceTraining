"""Gemeinsame Testvorbereitung.

sounddevice braucht PortAudio und damit echte Audiohardware. Fuer die
Analyse- und Einstellungstests ist das unnoetig, also wird das Modul durch
eine Attrappe ersetzt, bevor irgendetwas es importiert.
"""

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if "sounddevice" not in sys.modules:
    try:
        import sounddevice  # noqa: F401
    except Exception:
        sys.modules["sounddevice"] = types.SimpleNamespace(
            query_devices=lambda: [],
            query_hostapis=lambda: [],
            default=types.SimpleNamespace(device=(0, 0)),
            InputStream=object,
            play=lambda *args, **kwargs: None,
            stop=lambda: None,
        )

import numpy as np
import pytest


@pytest.fixture
def sr():
    return 48000


@pytest.fixture
def vowel(sr):
    """Synthetischer Vokal: Impulsfolge durch drei Formantresonatoren."""

    def build(f0=120.0, formants=(700.0, 1200.0, 2500.0), seconds=1.5,
              bandwidths=(80.0, 90.0, 120.0), amplitude=0.3):
        n = int(seconds * sr)
        source = np.zeros(n)
        source[:: max(1, int(sr / f0))] = 1.0
        out = np.zeros(n)
        for freq, bw in zip(formants, bandwidths):
            r = np.exp(-np.pi * bw / sr)
            theta = 2.0 * np.pi * freq / sr
            a1, a2 = -2.0 * r * np.cos(theta), r * r
            y = np.zeros(n)
            for i in range(2, n):
                y[i] = source[i] - a1 * y[i - 1] - a2 * y[i - 2]
            out += y
        peak = np.max(np.abs(out))
        return out / peak * amplitude if peak else out

    return build


@pytest.fixture
def noise(sr):
    def build(seconds=2.0, level=0.002):
        rng = np.random.default_rng(1234)
        return rng.standard_normal(int(seconds * sr)) * level

    return build


@pytest.fixture(autouse=True)
def fresh_settings(tmp_path, monkeypatch):
    """Jeder Test bekommt eigene Pfade und Standardeinstellungen."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    import settings
    settings.apply(settings.Settings())
    settings._state["user_profiles"] = {}
    settings._state["builtin_overrides"] = {}
    settings._state["profile"] = "feminin"
    settings._state["live_profile"] = "none"
    yield


@pytest.fixture
def qt_table(monkeypatch):
    """Eine echte Sessionliste ohne den Rest des Hauptfensters."""
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    from PySide6 import QtCore, QtGui
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    import columns

    table = QtWidgets.QTableWidget(0, 0)
    entries = [
        {"timestamp": "2026-08-30T14:46:58", "file": "a.wav", "quality": "ok",
         "duration": 26.9, "peak_db": -25.2, "f0_median": 111.1,
         "f0_p10": 93.8, "f0_p90": 157.7, "f1_median": 414.1,
         "f2_median": 1602.0, "f3_median": 2589.0, "h1_db": -40.1,
         "h2_db": -40.2},
        {"timestamp": "2026-08-28T14:06:23", "file": "b.wav", "quality": "ok",
         "duration": 17.5, "peak_db": -46.9, "f0_median": 122.6},
    ]

    def fill(keys, reset=True):
        """Spiegelt MainWindow._fill_session_table.

        reset=False laesst den Schritt weg, der eine Spaltenverschiebung
        verwirft — dafuer gibt es einen eigenen Test.
        """
        visible = [columns.BY_KEY[k] for k in keys]
        table.clearContents()
        table.setRowCount(0)
        if reset:
            table.setColumnCount(0)
        table.setColumnCount(len(visible) + 1)
        table.setRowCount(len(entries))
        for r, entry in enumerate(entries):
            for c, column in enumerate(visible):
                table.setItem(r, c, QtWidgets.QTableWidgetItem(
                    columns.text(entry, column)))
            table.setCellWidget(r, len(visible), QtWidgets.QPushButton("x"))

    yield table, fill
    table.deleteLater()
