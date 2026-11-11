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

"""Grosse Mikrofonauswahl."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from voice import audio as audio_mod
from core import i18n
from ui.theming import COLORS as NORD


# ------------------------------------------------------- Mikrofonauswahl

class MicrophonePicker(QtWidgets.QDialog):
    """Grosse Auswahl der Eingangsquelle.

    Im Klappmenue der Leiste bleibt von einem Namen wie "USB Advanced Audio
    Device Analoges Stereo" je nach Fensterbreite die Haelfte uebrig — unter
    Windows melden sich Geraete besonders geschwaetzig. Hier ist Platz fuer
    den ganzen Namen, darunter steht der technische, und der erklaerende
    Satz am Fuss beantwortet die Frage, warum dasselbe Mikrofon zweimal in
    der Liste steht.
    """

    KEY = QtCore.Qt.ItemDataRole.UserRole + 1
    DETAIL = QtCore.Qt.ItemDataRole.UserRole + 2

    def __init__(self, current: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("mic_pick_title"))
        self.setMinimumSize(760, 520)
        self._current = current

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(10)

        top = QtWidgets.QHBoxLayout()
        heading = QtWidgets.QLabel(i18n.t("mic_pick_intro"))
        heading.setWordWrap(True)
        top.addWidget(heading, 1)
        self.btn_refresh = QtWidgets.QPushButton(i18n.t("refresh_tip"))
        self.btn_refresh.clicked.connect(self.reload)
        top.addWidget(self.btn_refresh)
        root.addLayout(top)

        self.list = QtWidgets.QListWidget()
        self.list.setAlternatingRowColors(False)
        self.list.itemSelectionChanged.connect(self._selection_changed)
        self.list.itemDoubleClicked.connect(self._double_clicked)
        root.addWidget(self.list, 1)

        self.detail = QtWidgets.QLabel(" ")
        self.detail.setWordWrap(True)
        self.detail.setStyleSheet(f"color: {NORD['dim']};")
        self.detail.setMinimumHeight(34)
        root.addWidget(self.detail)

        note = QtWidgets.QLabel(i18n.t("mic_pick_note"))
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        root.addWidget(note)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.ok_button = buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText(i18n.t("mic_pick_use"))
        # Ohne das steht auf dem zweiten Knopf das englische "Cancel", weil
        # die Qt-Uebersetzungen nicht mitgeladen werden.
        buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText(
                i18n.t("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.reload()

    # -- Inhalt ----------------------------------------------------------

    def reload(self) -> None:
        selected = self.selected_key() or self._current
        self.list.clear()
        self._add_entry(i18n.t("system_default"), audio_mod.DEFAULT_KEY,
                        i18n.t("mic_pick_default_detail"), True)

        for title, items in audio_mod.grouped_sources(self._current):
            header = QtWidgets.QListWidgetItem(title)
            header.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
            header.setForeground(QtGui.QColor(NORD["dim"]))
            font = header.font()
            font.setPointSize(max(8, font.pointSize() - 1))
            header.setFont(font)
            self.list.addItem(header)
            for src in items:
                label = ("●  " if src.is_default else "     ") + src.label
                if not src.available:
                    label += "   " + i18n.t("not_available")
                self._add_entry(label, src.name, src.detail or src.name,
                                src.available)

        self._select(selected)

    def _add_entry(self, label: str, key: str, detail: str,
                   enabled: bool) -> None:
        item = QtWidgets.QListWidgetItem(label)
        item.setData(self.KEY, key)
        item.setData(self.DETAIL, detail)
        item.setToolTip(detail)
        if not enabled:
            item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
            item.setForeground(QtGui.QColor(NORD["dim"]))
        self.list.addItem(item)

    def _select(self, key: str | None) -> None:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(self.KEY) == key:
                self.list.setCurrentItem(item)
                return
        if self.list.count():
            self.list.setCurrentRow(0)

    # -- Auswahl ---------------------------------------------------------

    def selected_key(self) -> str | None:
        item = self.list.currentItem()
        return item.data(self.KEY) if item is not None else None

    def _selection_changed(self) -> None:
        item = self.list.currentItem()
        detail = item.data(self.DETAIL) if item is not None else ""
        self.detail.setText(detail or " ")
        self.ok_button.setEnabled(
            item is not None and item.data(self.KEY) is not None)

    def _double_clicked(self, item) -> None:
        if item.data(self.KEY) is not None:
            self.accept()
