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

"""Editor fuer Zielprofile."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from core import i18n
from core import settings
from voice import targets
from ui.theming import COLORS as NORD


# ------------------------------------------------------- Zielprofil-Editor

class ProfileEditor(QtWidgets.QWidget):
    """Zielprofile ansehen, anpassen und speichern.

    Die eingebauten Profile lassen sich ebenfalls aendern; die Werte aus der
    Literatur stehen im Code und kommen ueber "Zurücksetzen" jederzeit
    zurueck. Gespeichert wird erst auf Knopfdruck, damit ein verrutschtes
    Feld nicht sofort das Profil veraendert.
    """

    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False
        self._dirty = False
        self.rows: dict[str, tuple] = {}

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(12)

        hint = QtWidgets.QLabel(i18n.t("profiles_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        root.addWidget(hint)

        chooser = QtWidgets.QGroupBox(i18n.t("target_voice"))
        chooser_lay = QtWidgets.QHBoxLayout(chooser)
        self.profile_box = QtWidgets.QComboBox()
        self.profile_box.currentIndexChanged.connect(self._profile_chosen)
        chooser_lay.addWidget(self.profile_box, 1)
        root.addWidget(chooser)

        box = QtWidgets.QGroupBox(i18n.t("col_target"))
        box_lay = QtWidgets.QVBoxLayout(box)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(inner)
        grid.setContentsMargins(0, 0, 8, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(1, 1)
        scroll.setWidget(inner)
        box_lay.addWidget(scroll)

        for row, key in enumerate(targets.profile_keys_all()):
            metric = targets.METRIC_BY_KEY[key]

            enabled = QtWidgets.QCheckBox(metric.label)
            enabled.setToolTip(metric.hint)
            enabled.toggled.connect(self._value_changed)
            grid.addWidget(enabled, row, 0)

            low = QtWidgets.QDoubleSpinBox()
            high = QtWidgets.QDoubleSpinBox()
            for spin in (low, high):
                spin.setDecimals(metric.decimals)
                spin.setRange(-200.0, 9000.0)
                spin.setSingleStep(1.0 if metric.decimals == 0 else 0.1)
                if metric.unit:
                    spin.setSuffix(f" {metric.unit}")
                spin.setMinimumWidth(120)
                spin.valueChanged.connect(self._value_changed)

            grid.addWidget(QtWidgets.QLabel(i18n.t("profile_low")), row, 1,
                           QtCore.Qt.AlignmentFlag.AlignRight)
            grid.addWidget(low, row, 2)
            grid.addWidget(QtWidgets.QLabel(i18n.t("profile_high")), row, 3,
                           QtCore.Qt.AlignmentFlag.AlignRight)
            grid.addWidget(high, row, 4)
            if metric.vowel_only:
                enabled.setText(
                    f"{metric.label}   ({i18n.t('vowel_only_marker')})")
            self.rows[key] = (enabled, low, high)
        root.addWidget(box, 1)

        self.note = QtWidgets.QLabel("")
        self.note.setWordWrap(True)
        self.note.setStyleSheet(f"color: {NORD['yellow']}; font-size: 11px;")
        root.addWidget(self.note)

        actions = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton(i18n.t("profile_save"))
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self._save)
        self.btn_save_as = QtWidgets.QPushButton(i18n.t("save_as"))
        self.btn_save_as.clicked.connect(self._save_as)
        self.btn_reset = QtWidgets.QPushButton(i18n.t("profile_reset"))
        self.btn_reset.clicked.connect(self._reset)
        self.btn_delete = QtWidgets.QPushButton(i18n.t("delete"))
        self.btn_delete.setObjectName("danger")
        self.btn_delete.clicked.connect(self._delete)
        actions.addWidget(self.btn_save)
        actions.addWidget(self.btn_save_as)
        actions.addWidget(self.btn_reset)
        actions.addStretch(1)
        actions.addWidget(self.btn_delete)
        root.addLayout(actions)

        self.refresh(settings.get_profile())

    # -- Zustand ---------------------------------------------------------

    def refresh(self, select: str | None = None) -> None:
        self._loading = True
        self.profile_box.clear()
        for key in targets.profile_keys():
            if key == "none":
                continue
            self.profile_box.addItem(targets.profile_label(key), key)
        index = self.profile_box.findData(select or settings.get_profile())
        self.profile_box.setCurrentIndex(max(0, index))
        self._loading = False
        self._profile_chosen()

    def current_key(self) -> str:
        return self.profile_box.currentData() or "feminin"

    def _profile_chosen(self) -> None:
        if self._loading:
            return
        key = self.current_key()
        ranges = targets.profile_ranges(key)

        self._loading = True
        for metric_key, (enabled, low, high) in self.rows.items():
            span = ranges.get(metric_key)
            enabled.setChecked(span is not None)
            if span is not None:
                low.setValue(float(span[0]))
                high.setValue(float(span[1]))
            low.setEnabled(span is not None)
            high.setEnabled(span is not None)
        self._loading = False

        self._dirty = False
        self._update_buttons()
        # Der Editor bearbeitet Profile, er waehlt keins aus. Das machen die
        # Dropdowns im Live-Reiter und in der Detailansicht.
        self.changed.emit()

    def _update_buttons(self) -> None:
        key = self.current_key()
        user = targets.is_user_profile(key)
        self.btn_delete.setEnabled(user)
        self.btn_reset.setEnabled(not user and targets.is_overridden(key))

        if self._dirty:
            self.note.setText(i18n.t("profile_modified"))
        elif targets.is_overridden(key):
            self.note.setText(i18n.t("profile_overridden"))
        else:
            self.note.setText("")

    def _value_changed(self) -> None:
        if self._loading:
            return
        for enabled, low, high in self.rows.values():
            active = enabled.isChecked()
            low.setEnabled(active)
            high.setEnabled(active)
        self._dirty = True
        self._update_buttons()

    def _collect(self) -> dict:
        ranges = {}
        for key, (enabled, low, high) in self.rows.items():
            if not enabled.isChecked():
                continue
            lower, upper = low.value(), high.value()
            if upper < lower:
                lower, upper = upper, lower
            if upper == lower:
                upper = lower + targets.CUSTOM_MIN_MARGIN
            ranges[key] = [round(lower, 3), round(upper, 3)]
        return ranges

    # -- Aktionen --------------------------------------------------------

    def _save(self) -> None:
        ranges = self._collect()
        if not ranges:
            QtWidgets.QMessageBox.information(
                self, i18n.t("profile_save_title"), i18n.t("profile_needs_values"))
            return

        key = self.current_key()
        if targets.is_user_profile(key):
            settings.save_user_profile(targets.profile_name(key), ranges)
        else:
            settings.save_builtin_override(key, ranges)

        self._dirty = False
        self._update_buttons()
        self.changed.emit()

    def _save_as(self) -> None:
        ranges = self._collect()
        if not ranges:
            QtWidgets.QMessageBox.information(
                self, i18n.t("profile_save_title"), i18n.t("profile_needs_values"))
            return

        current = self.current_key()
        suggestion = (targets.profile_name(current)
                      if targets.is_user_profile(current)
                      else targets.profile_label(current))
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("profile_save_title"), i18n.t("name"), text=suggestion)
        name = name.strip()
        if not ok or not name:
            return

        settings.save_user_profile(name, ranges)
        self.refresh(select=targets.USER_PREFIX + name)
        self.changed.emit()

    def _reset(self) -> None:
        key = self.current_key()
        if targets.is_user_profile(key):
            return
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("profile_reset_title"),
            i18n.t("profile_reset_body", name=targets.profile_label(key)))
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        settings.reset_builtin(key)
        self._profile_chosen()
        self.changed.emit()

    def _delete(self) -> None:
        key = self.current_key()
        if not targets.is_user_profile(key):
            return
        name = targets.profile_name(key)
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("profile_delete_title"),
            i18n.t("profile_delete_body", name=name))
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            settings.delete_user_profile(name)
            self.refresh(select="feminin")
            self.changed.emit()
