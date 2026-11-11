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

"""Vorher/Nachher: zwei bis vier Aufnahmen Kennwert fuer Kennwert nebeneinander."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from core import columns
from core import i18n
from core import progress
from ui.theming import COLORS as NORD


def _fmt(value, column, signed: bool = False) -> str:
    if value is None:
        return "--"
    sign = "+" if signed else ""
    unit = f" {column.unit}" if column.unit else ""
    return f"{value:{sign}.{column.decimals}f}{unit}"


class CompareDialog(QtWidgets.QDialog):
    """Nach Datum sortiert: die aelteste links, die neueste rechts.

    Die letzte Spalte ist neueste minus aelteste.
    """

    play_requested = QtCore.Signal(dict)

    def __init__(self, entries: list[dict], parent=None):
        super().__init__(parent)
        self.entries = sorted(entries[:progress.MAX_COMPARE],
                              key=lambda e: e.get("timestamp") or "")
        self.setWindowTitle(i18n.t("compare_title"))
        self.resize(520 + 130 * len(self.entries), 620)

        root = QtWidgets.QVBoxLayout(self)
        rows = progress.compare(*self.entries)
        count = len(self.entries)

        heads = [i18n.t("compare_value")]
        for entry in self.entries:
            date = str(entry.get("timestamp", "")).replace("T", "  ")
            heads.append(f"{columns.display_name(entry)}\n{date}")
        heads.append(i18n.t("compare_diff"))

        self.table = QtWidgets.QTableWidget(len(rows), count + 2)
        self.table.setHorizontalHeaderLabels(heads)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for col in range(1, count + 2):
            header.setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        right = (QtCore.Qt.AlignmentFlag.AlignRight
                 | QtCore.Qt.AlignmentFlag.AlignVCenter)
        for r, (column, values, diff) in enumerate(rows):
            cells = ([column.label] + [_fmt(v, column) for v in values]
                     + [_fmt(diff, column, signed=True)])
            for c, text in enumerate(cells):
                item = QtWidgets.QTableWidgetItem(text)
                if c:
                    item.setTextAlignment(right)
                if c == count + 1 and diff:
                    item.setForeground(QtGui.QColor(NORD["accent"]))
                self.table.setItem(r, c, item)
        root.addWidget(self.table, 1)

        buttons = QtWidgets.QHBoxLayout()
        for entry in self.entries:
            button = QtWidgets.QPushButton(
                i18n.t("compare_play", name=columns.display_name(entry)))
            button.clicked.connect(
                lambda _=False, e=entry: self.play_requested.emit(e))
            buttons.addWidget(button)
        buttons.addStretch(1)
        close = QtWidgets.QPushButton(i18n.t("close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        root.addLayout(buttons)
