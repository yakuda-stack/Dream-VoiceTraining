#!/usr/bin/env python3
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

"""Diagnose fuer das Spektrogramm.

Nimmt 3 Sekunden ueber genau denselben Weg auf wie das Programm und
zeigt, was beim FFT-Schritt tatsaechlich ankommt.

    python diag.py            # Systemstandard
    python diag.py --list     # Quellen anzeigen
    python diag.py --device 3 # bestimmte Quelle (Nummer aus --list)
"""

import argparse
import sys
import time

import numpy as np

import audio
import settings
from audio import BLOCKSIZE, AudioEngine

NFFT = 2048
HOP = 1024
MAX_FREQ = 5000.0


def show_sources() -> None:
    for title, items in audio.grouped_sources():
        print(f"\n{title}")
        for src in items:
            route = ("ALSA-Index %s" % src.pa_index if src.pa_index is not None
                     else "PULSE_SOURCE=%s" % src.pulse_source if src.pulse_source
                     else "nicht verfügbar")
            print("  [%2d] %-46s %s"
                  % (SOURCES.index(src), src.label[:46], route))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--device", type=int, default=None)
    ap.add_argument("--seconds", type=float, default=3.0)
    args = ap.parse_args()

    settings.load()

    global SOURCES
    SOURCES = [s for _title, items in audio.grouped_sources() for s in items]

    if args.list:
        show_sources()
        return 0

    target = SOURCES[args.device] if args.device is not None else None
    engine = AudioEngine()
    print("Öffne:", target.label if target else "Systemstandard")
    if not engine.start(target):
        print("FEHLER beim Öffnen:", engine.last_error)
        return 1

    print(f"Nehme {args.seconds:.0f} s auf, bitte normal sprechen …")
    engine.start_recording()
    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        engine.pump()
        time.sleep(0.02)
    engine.pump()
    data = engine.stop_recording()
    engine.stop()

    print("\n=== Rohdaten ===")
    print("Samples:            ", data.size, "(%.2f s)" % (data.size / engine.samplerate))
    print("dtype:              ", data.dtype)
    if data.size == 0:
        print("Es kam nichts an — die Quelle liefert keine Daten.")
        return 1
    print("min / max:           %.6f / %.6f" % (data.min(), data.max()))
    print("RMS:                 %.6f  (%.1f dBFS)"
          % (np.sqrt((data.astype(np.float64) ** 2).mean()),
             20 * np.log10(np.sqrt((data.astype(np.float64) ** 2).mean()) + 1e-12)))
    print("Anteil exakt 0:      %.1f %%" % (100 * np.mean(data == 0.0)))
    print("verschiedene Werte:  ", len(np.unique(data)))
    print("erste 12 Samples:    ", np.array2string(data[:12], precision=5))

    print("\n=== FFT-Spalten (wie im Spektrogramm) ===")
    n_bins = int(MAX_FREQ / (engine.samplerate / NFFT)) + 1
    window = np.hanning(NFFT).astype(np.float32)
    cols = []
    pos = 0
    while pos + NFFT <= data.size:
        mag = np.abs(np.fft.rfft(data[pos:pos + NFFT] * window)[:n_bins]) / (NFFT / 2)
        cols.append(20.0 * np.log10(np.maximum(mag, 1e-6)))
        pos += HOP
    spec = np.asarray(cols)
    print("Form:               ", spec.shape, "(Spalten x Bins)")
    print("min / max:           %.1f / %.1f dB" % (spec.min(), spec.max()))
    print("Streuung je Spalte:  %.1f dB (Mittel über Bins)"
          % np.mean(spec.max(axis=1) - spec.min(axis=1)))
    print("Streuung je Bin:     %.1f dB (Mittel über Zeit)"
          % np.mean(spec.max(axis=0) - spec.min(axis=0)))
    flat = np.allclose(spec, spec.flat[0])
    print("komplett konstant:  ", flat)

    print("\nBeispielspalte (Mitte), alle 400 Hz:")
    mid = spec[spec.shape[0] // 2]
    step = int(400 / (engine.samplerate / NFFT))
    for b in range(0, n_bins, step):
        hz = b * engine.samplerate / NFFT
        bar = "#" * max(0, int((mid[b] + 100) / 3))
        print("  %5.0f Hz  %7.1f dB  %s" % (hz, mid[b], bar))
    return 0


if __name__ == "__main__":
    sys.exit(main())
