#!/usr/bin/env python3
"""Bildschirmfotos fuer die Einfuehrung erzeugen — je Sprache eines.

Von Hand aufgenommene Fotos veralten und stehen immer in einer Sprache. Die
hier entstehen aus der echten Oberflaeche mit erfundenen Daten, einmal auf
Englisch und einmal auf Deutsch, und die Stellen der goldenen Marken fallen
als Nebenprodukt ab: sie werden aus der tatsaechlichen Lage der Bedienelemente
berechnet und landen in assets/intro/shots.json.

    python packaging/make-intro-shots.py

Danach liegen in assets/intro:
    sessions.en.png  sessions.de.png
    detail.en.png    detail.de.png
    advanced.en.png  advanced.de.png
    shots.json
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import wave
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORK = Path(tempfile.mkdtemp(prefix="dvt-shots-"))
os.environ["DREAM_VOICETRAINING_HOME"] = str(WORK)

import numpy as np                                        # noqa: E402
from PySide6 import QtCore, QtGui, QtWidgets              # noqa: E402

import dialogs                                            # noqa: E402
import i18n                                               # noqa: E402
import main as app_main                                   # noqa: E402
import paths                                              # noqa: E402
import settings                                           # noqa: E402
import theming                                            # noqa: E402

OUT = ROOT / "assets" / "intro"
SR = 48000
SHOT_WIDTH = 860          # Breite, in der die Fotos in der Einfuehrung stehen


# ------------------------------------------------------------ Beispieldaten

def vowel(f0: float, seconds: float, formants=(700.0, 1200.0, 2500.0)):
    """Impulsfolge durch drei Formantresonatoren — klingt wie ein Vokal."""
    n = int(seconds * SR)
    source = np.zeros(n)
    source[:: max(1, int(SR / f0))] = 1.0
    out = np.zeros(n)
    for freq, bw in zip(formants, (80.0, 90.0, 120.0)):
        r = np.exp(-np.pi * bw / SR)
        theta = 2.0 * np.pi * freq / SR
        a1, a2 = -2.0 * r * np.cos(theta), r * r
        y = np.zeros(n)
        for i in range(2, n):
            y[i] = source[i] - a1 * y[i - 1] - a2 * y[i - 2]
        out += y
    peak = np.max(np.abs(out))
    return out / peak * 0.3 if peak else out


def syllables(rng, seconds: float) -> np.ndarray:
    """Sprachaehnliche Folge kurzer Silben mit Pausen dazwischen."""
    parts = []
    total = 0.0
    while total < seconds:
        length = float(rng.uniform(0.12, 0.28))
        gap = float(rng.uniform(0.05, 0.22))
        f0 = float(rng.uniform(130.0, 175.0))
        formants = (float(rng.uniform(420.0, 780.0)),
                    float(rng.uniform(1100.0, 2100.0)), 2500.0)
        burst = vowel(f0, length, formants) * float(rng.uniform(0.45, 1.0))
        # Ein- und Ausschwingen, sonst klackt jede Silbe.
        ramp = min(len(burst) // 4, int(0.02 * SR))
        if ramp:
            burst[:ramp] *= np.linspace(0.0, 1.0, ramp)
            burst[-ramp:] *= np.linspace(1.0, 0.0, ramp)
        parts += [burst, np.zeros(int(gap * SR))]
        total += length + gap
    return np.concatenate(parts)


def write_take(name: str) -> None:
    """Sprechen, ein gehaltener Vokal in der Mitte, wieder sprechen.

    Genau der Fall, den der erweiterte Modus erklaert: die ruhige Mitte
    herausschneiden.
    """
    rng = np.random.default_rng(7)
    held = vowel(151.0, 3.0)
    fade = int(0.25 * SR)
    held[:fade] *= np.linspace(0.0, 1.0, fade)
    held[-fade:] *= np.linspace(1.0, 0.0, fade)

    signal = np.concatenate([
        np.zeros(int(0.3 * SR)),
        syllables(rng, 2.6),
        np.zeros(int(0.35 * SR)),
        held * 1.05,
        np.zeros(int(0.35 * SR)),
        syllables(rng, 2.4),
        np.zeros(int(0.3 * SR)),
    ])
    data = (np.clip(signal, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(paths.SESSION_DIR / name), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(data.tobytes())


ENTRIES = [
    {"timestamp": "2026-09-02T20:31:27", "file": "2026-09-02_20-31-27.wav",
     "type": "vowel_a", "quality": "ok", "duration": 8.5, "peak_db": -19.0,
     "f0_median": 152.0, "f0_p10": 147.0, "f0_p90": 158.0, "f0_sd_st": 0.9,
     "f0_range_st": 2.1, "f1_median": 702.0, "f2_median": 1204.0,
     "f3_median": 2498.0, "h1_db": -27.8, "h2_db": -33.9, "h1_h2": 6.1,
     "hnr": 18.7, "jitter_local": 0.71, "shimmer_local": 3.4,
     "voice_breaks": 2.0, "n_breaks": 1, "voiced_ratio": 0.82},
    {"timestamp": "2026-09-02T18:42:08", "file": "2026-09-02_18-42-08.wav", "type": "reading",
     "quality": "ok", "duration": 24.1, "peak_db": -21.5, "f0_median": 143.0,
     "f0_p10": 121.0, "f0_p90": 168.0, "f0_sd_st": 3.1, "f1_median": 512.0,
     "f2_median": 1476.0, "f3_median": 2475.0, "h1_db": -35.4,
     "h2_db": -39.3, "h1_h2": 3.9, "hnr": 14.2, "jitter_local": 2.1,
     "shimmer_local": 11.4, "voiced_ratio": 0.61},
    {"timestamp": "2026-09-02T18:35:52", "file": "2026-09-02_18-35-52.wav", "type": "hum",
     "quality": "ok", "duration": 4.0, "peak_db": -20.2, "f0_median": 149.0,
     "f0_p10": 146.0, "f0_p90": 152.0, "f0_sd_st": 0.6, "f1_median": 480.0,
     "f2_median": 1462.0, "f3_median": 2403.0, "h1_db": -35.2,
     "h2_db": -39.2, "h1_h2": 4.0, "hnr": 19.8, "jitter_local": 0.6,
     "shimmer_local": 4.1, "voiced_ratio": 0.94},
    {"timestamp": "2026-09-02T18:35:38", "file": "2026-09-02_18-35-38.wav", "type": "vowel_i",
     "quality": "ok", "duration": 3.2, "peak_db": -22.8, "f0_median": 151.0,
     "f0_p10": 147.0, "f0_p90": 155.0, "f0_sd_st": 0.8, "f1_median": 320.0,
     "f2_median": 2362.0, "f3_median": 2977.0, "h1_db": -31.8,
     "h2_db": -37.2, "h1_h2": 5.4, "hnr": 17.1, "jitter_local": 0.9,
     "shimmer_local": 5.2, "voiced_ratio": 0.88},
]


# ---------------------------------------------------------------- Werkzeuge

def spot(rect: QtCore.QRect, region: QtCore.QRect, scale: float):
    """Mittelpunkt eines Bedienelements als Anteil des Ausschnitts."""
    x = (rect.center().x() - region.x()) * scale
    y = (rect.center().y() - region.y()) * scale
    return [round(x / (region.width() * scale), 4),
            round(y / (region.height() * scale), 4)]


def grab(widget: QtWidgets.QWidget, region: QtCore.QRect, name: str,
         lang: str) -> float:
    """Ausschnitt aufnehmen, auf Zielbreite bringen, speichern."""
    pixmap = widget.grab(region)
    scale = SHOT_WIDTH / pixmap.width()
    pixmap = pixmap.scaledToWidth(
        SHOT_WIDTH, QtCore.Qt.TransformationMode.SmoothTransformation)
    OUT.mkdir(parents=True, exist_ok=True)
    pixmap.save(str(OUT / f"{name}.{lang}.png"), "PNG")
    print(f"  {name}.{lang}.png  {pixmap.width()}x{pixmap.height()}")
    return scale


def rect_in(widget: QtWidgets.QWidget, host: QtWidgets.QWidget) -> QtCore.QRect:
    top_left = widget.mapTo(host, QtCore.QPoint(0, 0))
    return QtCore.QRect(top_left, widget.size())


# ------------------------------------------------------------------ Aufnahmen

def shoot_sessions(app, lang: str, out: dict) -> None:
    window = app_main.MainWindow()
    window.resize(1280, 820)
    window.sessions = list(ENTRIES)
    window._fill_session_table()
    window.tabs.setCurrentIndex(1)
    window.show()
    app.processEvents()

    table = window.table
    rows = min(4, table.rowCount())
    bottom = (table.mapTo(window, QtCore.QPoint(0, 0)).y()
              + table.horizontalHeader().height()
              + rows * table.rowHeight(0) + 12)
    region = QtCore.QRect(0, 0, window.width(), bottom)

    tab_rect = window.tabs.tabBar().tabRect(1)
    tab_rect.moveTopLeft(window.tabs.tabBar().mapTo(window, tab_rect.topLeft()))
    marks = [QtCore.QRect(tab_rect.right() + 8, tab_rect.top() + 8, 1, 1)]

    button = table.cellWidget(0, window._action_column)
    if button is not None:
        details = rect_in(button, window)
        marks.append(QtCore.QRect(details.left() - 16, details.center().y(),
                                  1, 1))

    scale = grab(window, region, "sessions", lang)
    out.setdefault("sessions", {})[lang] = [spot(m, region, scale)
                                            for m in marks]
    window.close()


def _detail(window) -> dialogs.SessionDetailDialog:
    dialog = dialogs.SessionDetailDialog(
        ENTRIES[0], list(ENTRIES), paths.SESSION_DIR, window)
    dialog.resize(1000, 900)
    dialog.show()
    return dialog


def shoot_detail(app, lang: str, out: dict, window) -> None:
    dialog = _detail(window)
    app.processEvents()

    table = dialog.table
    top = table.mapTo(dialog, QtCore.QPoint(0, 0)).y() - 46
    rows = min(11, table.rowCount())
    bottom = (table.mapTo(dialog, QtCore.QPoint(0, 0)).y()
              + table.horizontalHeader().height()
              + rows * table.rowHeight(0))
    region = QtCore.QRect(10, top, dialog.width() - 20, bottom - top)

    info = table.cellWidget(0, 0)
    mark = rect_in(info, dialog) if info is not None else QtCore.QRect(
        30, top + 90, 1, 1)

    scale = grab(dialog, region, "detail", lang)
    out.setdefault("detail", {})[lang] = [spot(mark, region, scale)]
    dialog.close()


def shoot_advanced(app, lang: str, out: dict, window) -> None:
    dialog = _detail(window)
    dialog.btn_advanced.setChecked(True)
    app.processEvents()

    toggle = rect_in(dialog.btn_advanced, dialog)
    buttons = rect_in(dialog.btn_sel_analyse, dialog)
    # Volle Breite, nicht ab 10: sonst wird die Marke links neben dem
    # Auswertungsknopf am Bildrand abgeschnitten.
    region = QtCore.QRect(0, toggle.top() - 10, dialog.width(),
                          buttons.bottom() + 12 - (toggle.top() - 10))

    # Linker Rand des markierten Bereichs: die Auswahl steht auf dem
    # mittleren Drittel, der Rand liegt also bei einem guten Drittel der
    # Zeichenflaeche.
    wave_rect = rect_in(dialog.wave_plot, dialog)
    edge = QtCore.QRect(wave_rect.left() + int(wave_rect.width() * 0.335),
                        wave_rect.top() + int(wave_rect.height() * 0.26), 1, 1)
    marks = [QtCore.QRect(toggle.right() + 10, toggle.center().y(), 1, 1),
             edge,
             QtCore.QRect(buttons.left() - 14, buttons.center().y(), 1, 1)]

    scale = grab(dialog, region, "advanced", lang)
    out.setdefault("advanced", {})[lang] = [spot(m, region, scale)
                                            for m in marks]
    dialog.close()


def run() -> None:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    paths.ensure_dirs()
    write_take(ENTRIES[0]["file"])

    spots: dict = {}
    for lang in ("en", "de"):
        print(f"{lang}:")
        i18n.set_language(lang)
        settings.set_language(lang)
        app.setStyleSheet(theming.stylesheet())

        window = app_main.MainWindow()
        window.resize(1280, 820)
        window.show()
        app.processEvents()

        shoot_sessions(app, lang, spots)
        shoot_detail(app, lang, spots, window)
        shoot_advanced(app, lang, spots, window)
        window.close()

    (OUT / "shots.json").write_text(
        json.dumps(spots, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"\n{OUT / 'shots.json'} geschrieben")


if __name__ == "__main__":
    run()
