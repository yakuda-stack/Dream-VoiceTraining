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

"""Fortschritts-Fenster: ein Kennwert ueber alle Aufnahmen als Kurve."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from core import columns
from core import i18n
from core import progress
from core import rectypes
from core import settings
from ui.theming import COLORS as NORD
from voice import targets

DEFAULT_METRIC = "f0_median"


class ProgressDialog(QtWidgets.QDialog):
    """Nicht modal: man kann daneben weiter in der Liste blaettern."""

    def __init__(self, entries: list[dict], parent=None):
        super().__init__(parent)
        self.entries = entries
        self.setWindowTitle(i18n.t("progress_title"))
        self.resize(860, 520)

        root = QtWidgets.QVBoxLayout(self)

        bar = QtWidgets.QHBoxLayout()
        self.metric_box = QtWidgets.QComboBox()
        for column in columns.COLUMNS:
            if column.numeric and column.field is not None:
                self.metric_box.addItem(column.label, column.key)
        self.metric_box.setCurrentIndex(
            max(0, self.metric_box.findData(DEFAULT_METRIC)))

        self.type_box = QtWidgets.QComboBox()
        self.type_box.addItem(i18n.t("progress_all_types"), None)
        for kind in rectypes.all_types():
            self.type_box.addItem(kind.label, kind.key)

        bar.addWidget(QtWidgets.QLabel(i18n.t("progress_metric")))
        bar.addWidget(self.metric_box, 1)
        bar.addSpacing(12)
        bar.addWidget(QtWidgets.QLabel(i18n.t("progress_type")))
        bar.addWidget(self.type_box, 1)
        bar.addSpacing(12)

        self.profile_box = QtWidgets.QComboBox()
        for key in targets.profile_keys():
            self.profile_box.addItem(targets.profile_label(key), key)
        self.profile_box.setCurrentIndex(
            max(0, self.profile_box.findData(settings.get_profile())))
        bar.addWidget(QtWidgets.QLabel(i18n.t("target_voice")))
        bar.addWidget(self.profile_box, 1)
        root.addLayout(bar)

        self.plot = pg.PlotWidget(axisItems={"bottom": pg.DateAxisItem()})
        self.plot.setBackground(NORD["bg2"])
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.addLegend(offset=(10, 10))
        root.addWidget(self.plot, 1)

        self.summary = QtWidgets.QLabel("")
        self.summary.setStyleSheet(f"color: {NORD['dim']};")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Close
                       ).setText(i18n.t("close"))
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.metric_box.currentIndexChanged.connect(self.redraw)
        self.type_box.currentIndexChanged.connect(self.redraw)
        self.profile_box.currentIndexChanged.connect(self.redraw)
        self.redraw()

    def redraw(self) -> None:
        key = self.metric_box.currentData()
        column = columns.BY_KEY[key]
        points = progress.series(self.entries, key,
                                 self.type_box.currentData())

        self.plot.clear()
        self.plot.setLabel("left", column.label, units=column.unit or None)
        if not points:
            self.summary.setText(i18n.t("progress_empty"))
            return

        xs = [stamp.timestamp() for stamp, _ in points]
        ys = [value for _, value in points]

        span = targets.range_for(key, self.profile_box.currentData())
        if span is not None and None not in span:
            fill = QtGui.QColor(NORD["green"])
            fill.setAlpha(45)
            band = pg.LinearRegionItem(
                values=span, orientation="horizontal", movable=False,
                brush=pg.mkBrush(fill),
                pen=pg.mkPen(None))
            band.setZValue(-10)
            self.plot.addItem(band)
            # Fuer die Legende: ein unsichtbares Stueck Kurve in Bandfarbe.
            self.plot.plot([], [], pen=pg.mkPen(NORD["green"], width=6),
                           name=i18n.t("progress_target"))

        self.plot.plot(xs, ys, pen=pg.mkPen(NORD["dim"], width=1),
                       symbol="o", symbolSize=7,
                       symbolBrush=NORD["accent"], symbolPen=None,
                       name=column.label)
        if len(ys) >= 3:
            self.plot.plot(xs, progress.moving_average(ys),
                           pen=pg.mkPen(NORD["yellow"], width=2),
                           name=i18n.t("progress_trend"))

        decimals = column.decimals
        unit = f" {column.unit}" if column.unit else ""
        diff = ys[-1] - ys[0]
        self.summary.setText(i18n.t(
            "progress_summary", count=len(ys),
            first=f"{ys[0]:.{decimals}f}{unit}",
            last=f"{ys[-1]:.{decimals}f}{unit}",
            diff=f"{diff:+.{decimals}f}{unit}"))
        self.plot.enableAutoRange()

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(860, 520)
