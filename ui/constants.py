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

"""Gemeinsame Konstanten des Hauptfensters (Takt, Analysefenster, Spektrogramm)."""

from __future__ import annotations

from PySide6 import QtCore

TICK_MS = 50                # UI-Takt
ANALYSIS_EVERY = 2          # Analyse nur bei jedem n-ten Tick (-> 10 Hz)
WINDOW_SECONDS = 0.40       # Analysefenster
NFFT = 2048
HOP = 1024
SPEC_COLS = 320
KEY_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
MAX_FREQ = 5000.0
LOW_LEVEL_DB = -40.0
HISTORY_SECONDS = 30.0
# SPEC_FLOOR_DB und SPEC_CEIL_DB stehen in audio.py, damit die
# Detailansicht dieselbe Skala verwenden kann. Hier unter denselben Namen.
from voice.audio import SPEC_CEIL_DB, SPEC_FLOOR_DB  # noqa: E402
