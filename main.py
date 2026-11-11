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

"""Voice Training - Live-Analyse von Tonhoehe und Resonanz.

Zeigt waehrend des Sprechens die Grundfrequenz (F0), die ersten beiden
Formanten (F1/F2) und ein Spektrogramm. Aufnahmen werden mit Kennzahlen
in einer Session-Historie abgelegt.
"""

from __future__ import annotations

import os

# pyqtgraph sucht sich sein Qt-Binding beim Import selbst und probiert
# PyQt5, PySide2, PyQt6, PySide6 in dieser Reihenfolge. Ist auf dem System
# python-pyqt6 installiert, nimmt es PyQt6 — und mischt sich dann mit den
# PySide6-Objekten dieses Programms, was in einem TypeError und einem
# Segfault endet. Deshalb VOR dem Import festlegen, welches Binding gilt.
os.environ.setdefault("PYQTGRAPH_QT_LIB", "PySide6")

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from core import paths
from core import settings
from core import wininstall
from ui import theming
from ui.constants import SPEC_CEIL_DB, SPEC_FLOOR_DB  # noqa: F401  (Tests greifen darauf zu)
from ui.main_window import MainWindow, SESSION_DIR, SESSION_INDEX  # noqa: F401

APP_DIR = Path(__file__).resolve().parent


def load_state() -> list[str]:
    """Konfiguration lesen und den gespeicherten Zustand anwenden.

    Die Reihenfolge ist der ganze Sinn dieser Funktion, deshalb steht sie
    beisammen: erst kann der Umzug die config.json ueberhaupt an ihren
    Platz legen, dann wird sie gelesen, und erst danach duerfen Design und
    Sprache daraus gesetzt werden. Wer restore() davorzieht, bekommt den
    leeren Vorgabewert und damit nach jedem Start wieder die Vorlagenfarben.

    Zurueck kommt, was der Umzug bewegt hat.
    """
    paths.ensure_dirs()
    moved = paths.migrate_from(APP_DIR)
    settings.load()
    theming.restore(settings.get_theme())
    i18n.set_language(settings.get_language())
    return moved


def main() -> int:
    paths.set_process_name()

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(paths.APP_NAME)
    app.setApplicationDisplayName(paths.APP_NAME)
    app.setApplicationVersion(paths.APP_VERSION)
    app.setOrganizationName("yakuda")
    # Ohne den Desktop-Dateinamen ordnet Wayland Fenster und Symbol nicht zu.
    QtGui.QGuiApplication.setDesktopFileName(paths.APP_ID)

    icon_path = paths.icon_file()
    if icon_path is not None:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    debuglog.install()
    moved = load_state()
    app.setStyleSheet(theming.stylesheet())
    if not paths.CONFIG_PATH.exists():
        settings.save()      # beim ersten Start eine Datei anlegen
    win = MainWindow()
    first_run = not settings.get_intro_done()
    if moved:
        win.status.showMessage(
            f"{len(moved)} file(s) moved to {paths.CONFIG_DIR}")
    win.show()
    # Etwas spaeter, damit der Start nicht auf das Netz wartet.
    QtCore.QTimer.singleShot(2000, win.check_for_updates)

    # Die vom alten Ort zurueckgelassene EXE entfernen, falls sich das
    # Programm gerade selbst eingerichtet hat.
    leftover = wininstall.handover_path()
    if leftover is not None:
        QtCore.QTimer.singleShot(
            1200, lambda: wininstall.delete_leftover(leftover))

    offer = wininstall.should_offer()
    if first_run or offer:
        # Erst nach show(), sonst steht der Assistent hinter dem Fenster.
        QtCore.QTimer.singleShot(
            0, lambda: win.start_first_run(offer, first_run))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
