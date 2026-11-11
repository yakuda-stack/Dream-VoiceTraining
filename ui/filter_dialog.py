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

"""Filterdialog des Sessions-Reiters."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from core import columns
from core import i18n
from ui.theming import COLORS as NORD


# ------------------------------------------------------------ Filterdialog

class FilterDialog(QtWidgets.QDialog):
    """Spaltenauswahl, Sortierung und Zeitraum der Sessionliste.

    "Übernehmen" schickt die Auswahl sofort an die Liste, ohne den Dialog
    zu schliessen — praktisch beim Ausprobieren von Spaltenkombinationen.
    """

    applied = QtCore.Signal(dict)

    def __init__(self, view: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("filter_title"))
        self.setMinimumSize(620, 680)
        self.view = dict(view)
        self._original = dict(view)

        root = QtWidgets.QVBoxLayout(self)
        root.addWidget(self._build_columns())
        root.addWidget(self._build_sort())
        root.addWidget(self._build_period())

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Apply
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        SB = QtWidgets.QDialogButtonBox.StandardButton
        buttons.button(SB.Ok).setText(i18n.t("ok"))
        buttons.button(SB.Apply).setText(i18n.t("apply"))
        buttons.button(SB.Cancel).setText(i18n.t("cancel"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self._reject)
        buttons.button(SB.Apply).clicked.connect(self.apply_now)
        root.addWidget(buttons)

        self._load()

    def _build_columns(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("filter_columns"))
        lay = QtWidgets.QVBoxLayout(box)

        hint = QtWidgets.QLabel(i18n.t("filter_columns_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        lay.addWidget(hint)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        inner = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 0, 0)

        self.checks: dict[str, QtWidgets.QCheckBox] = {}
        for i, column in enumerate(columns.COLUMNS):
            check = QtWidgets.QCheckBox(column.label)
            self.checks[column.key] = check
            grid.addWidget(check, i // 2, i % 2)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)

        row = QtWidgets.QHBoxLayout()
        for text, keys in (
                (i18n.t("select_all"), [c.key for c in columns.COLUMNS]),
                (i18n.t("select_none"), []),
                (i18n.t("select_default"), columns.DEFAULT_VISIBLE)):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(
                lambda _=False, k=keys: self._set_checked(k))
            row.addWidget(button)
        row.addStretch(1)
        lay.addLayout(row)
        return box

    def _build_sort(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("filter_sort"))
        lay = QtWidgets.QHBoxLayout(box)
        self.sort_box = QtWidgets.QComboBox()
        for column in columns.COLUMNS:
            self.sort_box.addItem(column.label, column.key)
        self.descending = QtWidgets.QCheckBox(i18n.t("filter_descending"))
        lay.addWidget(QtWidgets.QLabel(i18n.t("filter_sort_by")))
        lay.addWidget(self.sort_box, 1)
        lay.addWidget(self.descending)
        return box

    def _build_period(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("filter_period"))
        lay = QtWidgets.QVBoxLayout(box)
        self.period_on = QtWidgets.QCheckBox(i18n.t("filter_period_on"))
        lay.addWidget(self.period_on)

        row = QtWidgets.QHBoxLayout()
        self.date_from = QtWidgets.QDateEdit()
        self.date_to = QtWidgets.QDateEdit()
        for edit in (self.date_from, self.date_to):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")
        row.addWidget(QtWidgets.QLabel(i18n.t("filter_from")))
        row.addWidget(self.date_from)
        row.addSpacing(16)
        row.addWidget(QtWidgets.QLabel(i18n.t("filter_to")))
        row.addWidget(self.date_to)
        row.addStretch(1)
        lay.addLayout(row)

        self.period_on.toggled.connect(self.date_from.setEnabled)
        self.period_on.toggled.connect(self.date_to.setEnabled)
        return box

    def _set_checked(self, keys) -> None:
        wanted = set(keys)
        for key, check in self.checks.items():
            check.setChecked(key in wanted)

    def _load(self) -> None:
        visible = self.view.get("columns") or columns.DEFAULT_VISIBLE
        self._set_checked(visible)

        index = self.sort_box.findData(self.view.get("sort", "date"))
        self.sort_box.setCurrentIndex(max(0, index))
        self.descending.setChecked(bool(self.view.get("descending", True)))

        today = QtCore.QDate.currentDate()
        start = QtCore.QDate.fromString(self.view.get("period_from") or "",
                                        "yyyy-MM-dd")
        end = QtCore.QDate.fromString(self.view.get("period_to") or "",
                                      "yyyy-MM-dd")
        self.date_from.setDate(start if start.isValid() else today.addDays(-30))
        self.date_to.setDate(end if end.isValid() else today)
        self.period_on.setChecked(bool(self.view.get("period_on")))
        self.date_from.setEnabled(self.period_on.isChecked())
        self.date_to.setEnabled(self.period_on.isChecked())

    def apply_now(self) -> None:
        self.applied.emit(self.result_view())

    def _accept(self) -> None:
        self.apply_now()
        self.accept()

    def _reject(self) -> None:
        # Ein zwischenzeitliches "Übernehmen" wird zurueckgerollt.
        self.applied.emit(dict(self._original))
        self.reject()

    def result_view(self) -> dict:
        chosen = [c.key for c in columns.COLUMNS if self.checks[c.key].isChecked()]
        return {
            "columns": chosen or list(columns.DEFAULT_VISIBLE),
            "sort": self.sort_box.currentData(),
            "descending": self.descending.isChecked(),
            "period_on": self.period_on.isChecked(),
            "period_from": self.date_from.date().toString("yyyy-MM-dd"),
            "period_to": self.date_to.date().toString("yyyy-MM-dd"),
        }
