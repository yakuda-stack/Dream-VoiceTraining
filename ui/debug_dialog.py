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

"""Debugfenster mit Fehlerprotokoll."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from ui.theming import COLORS as NORD


# ------------------------------------------------------------ Debugfenster

class DebugDialog(QtWidgets.QDialog):
    """Zeigt, was das Programm abgefangen hat, statt abzustuerzen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("debug_title"))
        self.setMinimumSize(860, 560)

        root = QtWidgets.QVBoxLayout(self)
        hint = QtWidgets.QLabel(i18n.t("debug_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        root.addWidget(hint)

        self.summary = QtWidgets.QLabel("")
        root.addWidget(self.summary)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            i18n.t("col_time"), i18n.t("col_level_dbg"),
            i18n.t("col_source"), i18n.t("col_message")])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._show_traceback)
        splitter.addWidget(self.table)

        self.trace = QtWidgets.QPlainTextEdit()
        self.trace.setReadOnly(True)
        self.trace.setFont(QtGui.QFontDatabase.systemFont(
            QtGui.QFontDatabase.SystemFont.FixedFont))
        splitter.addWidget(self.trace)
        splitter.setSizes([340, 200])
        root.addWidget(splitter, 1)

        row = QtWidgets.QHBoxLayout()
        for text, slot in ((i18n.t("debug_refresh"), self._reload),
                           (i18n.t("debug_clear"), self._clear),
                           (i18n.t("export"), self._export)):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        close = QtWidgets.QPushButton(i18n.t("close"))
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        root.addLayout(row)

        self._reload()

    def _reload(self) -> None:
        records = list(debuglog.RECORDS)
        self.summary.setText(i18n.t("debug_count", count=len(records),
                                    errors=sum(1 for r in records
                                               if r[1] in ("ERROR", "CRITICAL"))))
        self.table.setRowCount(len(records))
        for r, (stamp, level, source, message, tb) in enumerate(records):
            for c, text in enumerate((stamp, level, source, message)):
                item = QtWidgets.QTableWidgetItem(text)
                if c == 1 and level in ("ERROR", "CRITICAL"):
                    item.setForeground(QtGui.QColor(NORD["red"]))
                elif c == 1 and level == "WARNING":
                    item.setForeground(QtGui.QColor(NORD["yellow"]))
                if c == 0:
                    item.setData(QtCore.Qt.ItemDataRole.UserRole, tb)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.trace.setPlainText("" if records else i18n.t("debug_empty"))

    def _show_traceback(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        tb = item.data(QtCore.Qt.ItemDataRole.UserRole) if item else ""
        self.trace.setPlainText(tb or i18n.t("debug_empty"))

    def _clear(self) -> None:
        debuglog.clear()
        self._reload()

    def _export(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, i18n.t("export_title"), "dream-voicetraining-debug.txt",
            "Text (*.txt)")
        if not path:
            return
        if not Path(path).suffix:
            path += ".txt"
        try:
            Path(path).write_text(debuglog.as_text(), encoding="utf-8")
        except OSError as exc:
            QtWidgets.QMessageBox.warning(self, i18n.t("export_failed"), str(exc))
            return
        QtWidgets.QMessageBox.information(
            self, i18n.t("export_title"), i18n.t("exported", path=path))
