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

"""Goldene Marke (Wegweiser) fuer die Einfuehrung."""

from __future__ import annotations

import math

from PySide6 import QtCore, QtGui, QtWidgets


# -------------------------------------------------------------- Wegweiser

# Bewusst kein Themenwert: die Marke soll in jedem Farbschema als dasselbe
# goldene ⓘ erkennbar sein, sonst sucht man beim Themenwechsel neu.
GOLD = "#f0c14e"
GOLD_TEXT = "#2b2b2b"


class Spotlight(QtWidgets.QWidget):
    """Pulsierendes goldenes ⓘ, das auf ein Bedienelement zeigt.

    Eine Anleitung, die nur beschreibt, wo etwas liegt, laesst einen suchen.
    Diese Marke haengt entweder am echten Knopf im Hauptfenster oder an einer
    Stelle in einem Bildschirmfoto und pulst, solange der Schritt laeuft.

    Sie nimmt keine Mausklicks an — sonst waere ausgerechnet der Knopf
    blockiert, auf den sie zeigt.
    """

    SIZE = 22                      # Durchmesser des Kerns
    HALO = 10                      # zusaetzlicher Rand fuer den Schein
    STEP_MS = 40                   # 25 Bilder je Sekunde reichen dafuer
    PERIOD_MS = 1500

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(self.SIZE + 2 * self.HALO, self.SIZE + 2 * self.HALO)
        self._phase = 0.0
        self._target = None
        self._anchor = None
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self.STEP_MS)
        self._timer.timeout.connect(self._step)
        self.hide()

    # -- Anhaengen -------------------------------------------------------

    def attach(self, target: QtWidgets.QWidget, anchor=None) -> None:
        """An ein echtes Bedienelement haengen.

        `anchor` liefert den Punkt im Koordinatensystem des Ziels, auf den
        die Marke zeigen soll; ohne Angabe der linke Rand, damit sie das
        Element selbst nicht verdeckt.
        """
        self._target = target
        self._anchor = anchor
        self._follow()
        self._timer.start()

    def place(self, centre: QtCore.QPoint) -> None:
        """Feste Stelle, etwa auf einem Bildschirmfoto."""
        self._target = None
        self.move(centre.x() - self.width() // 2,
                  centre.y() - self.height() // 2)
        self.show()
        self.raise_()

    def detach(self) -> None:
        self._timer.stop()
        self._target = None
        self.hide()

    # -- Ablauf ----------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _step(self) -> None:
        self._phase = (self._phase + self.STEP_MS / self.PERIOD_MS) % 1.0
        if self._target is not None:
            self._follow()
        self.update()

    def _follow(self) -> None:
        parent = self.parentWidget()
        target = self._target
        if parent is None or target is None:
            return
        try:
            if not target.isVisible():
                self.hide()
                return
            point = (self._anchor(target) if self._anchor is not None
                     else QtCore.QPoint(-10, target.height() // 2))
            # Ueber den Bildschirm rechnen: dann muss das Ziel kein
            # Nachfahre der Marke sein und ein Reiterwechsel stoert nicht.
            centre = parent.mapFromGlobal(target.mapToGlobal(point))
        except RuntimeError:
            # Das Ziel wurde beim Neuaufbau der Oberflaeche geloescht.
            self.detach()
            return
        self.move(centre.x() - self.width() // 2,
                  centre.y() - self.height() // 2)
        if not self.isVisible():
            self.show()
        self.raise_()

    def paintEvent(self, event):
        pulse = 0.5 - 0.5 * math.cos(2 * math.pi * self._phase)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        centre = QtCore.QPointF(self.width() / 2, self.height() / 2)
        core = self.SIZE / 2

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        glow = QtGui.QColor(GOLD)
        glow.setAlpha(int(120 * (1.0 - pulse)))
        painter.setBrush(glow)
        radius = core + self.HALO * pulse
        painter.drawEllipse(centre, radius, radius)

        painter.setBrush(QtGui.QColor(GOLD))
        painter.drawEllipse(centre, core, core)

        painter.setPen(QtGui.QColor(GOLD_TEXT))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(max(8, self.SIZE // 2))
        painter.setFont(font)
        painter.drawText(self.rect(),
                         QtCore.Qt.AlignmentFlag.AlignCenter, "i")
