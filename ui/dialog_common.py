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

"""Gemeinsame Helfer der Dialoge: Exportsprache, Formant-Hilfslinien, Messwerte."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from core import i18n
from voice import targets
from ui.theming import COLORS as NORD


# ----------------------------------------------------- Sprache beim Export

def ask_export_language(parent) -> str | None:
    """Bei anderer Oberflaechensprache nachfragen, bei Englisch direkt Englisch.

    Gibt den Sprachcode zurueck oder None, wenn abgebrochen wurde.
    """
    if i18n.LANG == i18n.DEFAULT:
        return i18n.DEFAULT

    box = QtWidgets.QMessageBox(parent)
    box.setWindowTitle(i18n.t("export_language_title"))
    box.setText(i18n.t("export_language_body"))
    current = box.addButton(i18n.language_name(i18n.LANG),
                            QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    english = box.addButton(i18n.t("language_en"),
                            QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    box.addButton(i18n.t("cancel"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(current)
    box.exec()

    clicked = box.clickedButton()
    if clicked is current:
        return i18n.LANG
    if clicked is english:
        return i18n.DEFAULT
    return None


class export_language:
    """Kontextmanager, der die Sprache nur waehrend des Schreibens umstellt."""

    def __init__(self, code: str):
        self.code = code
        self.previous = i18n.LANG

    def __enter__(self):
        i18n.set_language(self.code)
        return self

    def __exit__(self, *exc):
        i18n.set_language(self.previous)
        return False


def CUSTOM_LABEL() -> str:
    return i18n.t("custom_values")


# --------------------------------------------------------- Detailansicht

# Farbrolle je Linie. Dieselben Rollen wie die Kennwertkarten im
# Livebereich: die blasse Linie im Bild und die Zahl darueber gehoeren
# sichtbar zusammen.
GUIDE_ROLES = {"F1": "yellow", "F2": "green", "F3": "purple"}

# Ueber dem Bild (0), unter der Auswahl (10) und unter den gemessenen
# Formantlinien des Livebereichs (MEASURED_Z). Was gemessen wurde,
# verdeckt die Orientierung, nicht umgekehrt.
GUIDE_Z = 5
MEASURED_Z = 15


def add_formant_guides(plot, top: float, visible: bool = True) -> list:
    """Waagerechte Orientierungslinien fuer F1, F2 und F3.

    Gepunktet, duenn und blass, damit sie sich von den gemessenen Linien
    unterscheiden — vier gestrichelte Linien im selben Bild waeren nicht
    auseinanderzuhalten.

    `top` ist die obere Frequenz des Bildes. Eine Linie darueber wird
    weggelassen statt am Rand zu kleben: bei 8 kHz Abtastrate endet das
    Bild bei 4000 Hz, und die 2800 der F3 sind dann noch drin, bei einer
    aelteren Aufnahme mit weniger aber nicht mehr.

    ignoreBounds ist Pflicht. Ohne das zaehlt eine InfiniteLine als Inhalt,
    und der sichtbare Bereich richtet sich beim naechsten Zurechtruecken
    nach ihr statt nach dem Bild.
    """
    lines = []
    for name, hertz in targets.FORMANT_GUIDES:
        if hertz > top:
            continue
        colour = QtGui.QColor(NORD[GUIDE_ROLES.get(name, "dim")])
        colour.setAlpha(130)
        fill = QtGui.QColor(NORD["bg2"])
        fill.setAlpha(190)
        line = pg.InfiniteLine(
            pos=hertz, angle=0, movable=False,
            pen=pg.mkPen(colour, width=1, style=QtCore.Qt.PenStyle.DotLine),
            label=f"{name}  {hertz:.0f} Hz",
            # anchors: ohne das zentriert pyqtgraph die Beschriftung auf der
            # Stelle, und bei position 0.02 haengt die Haelfte davon links
            # aus dem Diagramm heraus. (0, …) setzt die linke Textkante auf
            # den Punkt.
            labelOpts={"position": 0.02, "color": NORD["dim"],
                       "anchors": [(0, 1), (0, 0)],
                       "fill": pg.mkBrush(fill), "border": pg.mkPen(colour)})
        line.setZValue(GUIDE_Z)
        line.setVisible(visible)
        plot.addItem(line, ignoreBounds=True)
        lines.append(line)
    return lines


def metric_value(entry: dict, key: str) -> float | None:
    """Kennwert aus einem Session-Eintrag, None wenn nicht vorhanden."""
    if key == "voiced_ratio_pct":
        raw = entry.get("voiced_ratio")
        return float(raw) * 100.0 if isinstance(raw, (int, float)) else None
    raw = entry.get(key)
    return float(raw) if isinstance(raw, (int, float)) else None
