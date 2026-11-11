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

"""Kleine Bausteine des Live-Reiters: Kennzahl-Kachel und Zonenbalken."""

from __future__ import annotations

from collections import deque

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from ui.theming import COLORS as NORD
from core.settings import CFG


class StatCard(QtWidgets.QFrame):
    """Grosse Zahl mit Beschriftung."""

    def __init__(self, title: str, unit: str = "", color: str = NORD["fg"]):
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background: {NORD['bg2']}; border-radius: 8px; }}")
        self._unit = unit

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        cap = QtWidgets.QLabel(title.upper())
        cap.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 10px; letter-spacing: 1px;")

        self.value = QtWidgets.QLabel("--")
        f = self.value.font()
        f.setPointSize(26)
        f.setWeight(QtGui.QFont.Weight.DemiBold)
        self.value.setFont(f)
        self.value.setStyleSheet(f"color: {color};")

        lay.addWidget(cap)
        lay.addWidget(self.value)
        self._base_color = color

    def set_color(self, color: str | None = None) -> None:
        self.value.setStyleSheet(f"color: {color or self._base_color};")

    def set(self, text: str) -> None:
        self.value.setText(f"{text}{self._unit}" if text != "--" else "--")


class ZoneBar(QtWidgets.QWidget):
    """Horizontaler Balken 60-350 Hz mit Zonenfaerbung und Marker."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(58)
        self.f0: float | None = None
        self.recent: deque[float] = deque(maxlen=120)

    def update_value(self, f0: float | None) -> None:
        self.f0 = f0
        if f0 is not None:
            self.recent.append(f0)
        self.update()

    @property
    def LO(self) -> float:
        return max(40.0, CFG.pitch_floor)

    @property
    def HI(self) -> float:
        return min(CFG.pitch_ceiling, max(CFG.zone_high + 140.0, self.LO + 120.0))

    def _ticks(self) -> list[int]:
        span = self.HI - self.LO
        step = next((s for s in (10, 20, 25, 50, 100) if span / s <= 8), 100)
        first = int(np.ceil(self.LO / step) * step)
        return list(range(first, int(self.HI) + 1, step))

    def _x(self, hz: float, w: int) -> float:
        frac = (hz - self.LO) / (self.HI - self.LO)
        return max(0.0, min(1.0, frac)) * w

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_top, bar_h = 16, 22

        zones = [
            (self.LO, CFG.zone_low, QtGui.QColor(94, 129, 172, 160)),
            (CFG.zone_low, CFG.zone_high, QtGui.QColor(180, 142, 173, 160)),
            (CFG.zone_high, self.HI, QtGui.QColor(163, 190, 140, 160)),
        ]
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for lo, hi, col in zones:
            x0, x1 = self._x(lo, w), self._x(hi, w)
            p.setBrush(col)
            p.drawRoundedRect(QtCore.QRectF(x0, bar_top, x1 - x0, bar_h), 3, 3)

        # Streubereich der letzten Sekunden
        if len(self.recent) >= 5:
            arr = np.fromiter(self.recent, dtype=float)
            lo, hi = np.percentile(arr, 10), np.percentile(arr, 90)
            x0, x1 = self._x(lo, w), self._x(hi, w)
            p.setBrush(QtGui.QColor(236, 239, 244, 55))
            p.drawRect(QtCore.QRectF(x0, bar_top, max(2.0, x1 - x0), bar_h))

        # Skala
        p.setPen(QtGui.QColor(NORD["dim"]))
        font = p.font()
        font.setPointSize(8)
        p.setFont(font)
        for hz in self._ticks():
            x = self._x(hz, w)
            p.drawText(QtCore.QRectF(x - 20, bar_top + bar_h + 2, 40, 14),
                       QtCore.Qt.AlignmentFlag.AlignHCenter, str(hz))

        # Zonengrenzen hervorheben
        p.setPen(QtGui.QColor(NORD["fg"]))
        for hz in (CFG.zone_low, CFG.zone_high):
            x = self._x(hz, w)
            p.drawText(QtCore.QRectF(x - 24, 0, 48, 13),
                       QtCore.Qt.AlignmentFlag.AlignHCenter, f"{hz:.0f}")

        # Marker
        if self.f0 is not None:
            x = self._x(self.f0, w)
            p.setPen(QtGui.QPen(QtGui.QColor(NORD["fg"]), 2))
            p.drawLine(QtCore.QPointF(x, bar_top - 6),
                       QtCore.QPointF(x, bar_top + bar_h + 1))
            p.setBrush(QtGui.QColor(NORD["fg"]))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawPolygon(QtGui.QPolygonF([
                QtCore.QPointF(x, bar_top - 2),
                QtCore.QPointF(x - 5, bar_top - 10),
                QtCore.QPointF(x + 5, bar_top - 10),
            ]))
        p.end()
