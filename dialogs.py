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

"""Einstellungsdialog. Die Felder werden aus settings.PARAMS erzeugt,
neue Parameter dort eintragen reicht also aus."""

from __future__ import annotations

from dataclasses import asdict

import csv
import io
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import sounddevice as sd
from PySide6 import QtCore, QtGui, QtWidgets

import analysis
import audio as audio_mod
import columns
import debuglog
import i18n
import paths
import rectypes
import settings
import targets
from settings import PARAMS, Settings

# ----------------------------------------------------- Sprache beim Export

def ask_export_language(parent) -> str | None:
    """Bei deutscher Oberflaeche nachfragen, bei englischer direkt Englisch.

    Gibt den Sprachcode zurueck oder None, wenn abgebrochen wurde.
    """
    if i18n.LANG == "en":
        return "en"

    box = QtWidgets.QMessageBox(parent)
    box.setWindowTitle(i18n.t("export_language_title"))
    box.setText(i18n.t("export_language_body"))
    german = box.addButton(i18n.t("language_de"),
                           QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    english = box.addButton(i18n.t("language_en"),
                            QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    box.addButton(i18n.t("cancel"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(german)
    box.exec()

    clicked = box.clickedButton()
    if clicked is german:
        return "de"
    if clicked is english:
        return "en"
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


class SettingsDialog(QtWidgets.QDialog):
    """Aenderungen werden per applied-Signal sofort weitergereicht."""

    applied = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("dlg_settings"))
        self.setMinimumSize(660, 660)
        self.resize(720, 820)

        self._spins: dict[str, QtWidgets.QDoubleSpinBox] = {}
        self._loading = False

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(14)

        analysis_page = QtWidgets.QWidget()
        analysis_lay = QtWidgets.QVBoxLayout(analysis_page)
        analysis_lay.setContentsMargins(0, 8, 0, 0)
        analysis_lay.addWidget(self._build_template_row())

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._build_params_group())
        analysis_lay.addWidget(scroll, 1)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(analysis_page, i18n.t("tab_analysis"))
        self.profiles = ProfileEditor()
        self.tabs.addTab(self.profiles, i18n.t("tab_profiles"))
        root.addWidget(self.tabs, 1)

        note = QtWidgets.QLabel(i18n.t("settings_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color: #8896ab;")
        root.addWidget(note)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        SB = QtWidgets.QDialogButtonBox.StandardButton
        buttons.button(SB.Ok).setText(i18n.t("ok"))
        buttons.button(SB.Cancel).setText(i18n.t("cancel"))
        buttons.button(SB.Apply).setText(i18n.t("apply"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self._reject)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply
                       ).clicked.connect(self._apply)

        self.btn_about = QtWidgets.QPushButton("ⓘ  " + i18n.t("about"))
        self.btn_about.clicked.connect(self._open_about)
        buttons.addButton(self.btn_about,
                          QtWidgets.QDialogButtonBox.ButtonRole.HelpRole)

        self.btn_debug = QtWidgets.QPushButton("🐞  " + i18n.t("debug"))
        self.btn_debug.clicked.connect(self._open_debug)
        buttons.addButton(self.btn_debug,
                          QtWidgets.QDialogButtonBox.ButtonRole.HelpRole)
        self._update_debug_badge()
        root.addWidget(buttons)

        self._before = settings.snapshot()
        self._before_template = settings.active_template()
        self._refresh_templates()
        self._load_values(self._before)

    # -- Aufbau ----------------------------------------------------------

    def _build_template_row(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("template"))
        lay = QtWidgets.QHBoxLayout(box)

        self.template_box = QtWidgets.QComboBox()
        self.template_box.currentIndexChanged.connect(self._template_chosen)

        self.btn_save = QtWidgets.QPushButton(i18n.t("save_as"))
        self.btn_save.clicked.connect(self._save_template)
        self.btn_delete = QtWidgets.QPushButton(i18n.t("delete"))
        self.btn_delete.clicked.connect(self._delete_template)

        lay.addWidget(self.template_box, 1)
        lay.addWidget(self.btn_save)
        lay.addWidget(self.btn_delete)
        return box

    def _build_params_group(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("parameters"))
        # Direktes Grid statt verschachtelter Widgets: nur so berechnet Qt
        # die Hoehe umbrechender Hinweistexte richtig.
        grid = QtWidgets.QGridLayout(box)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(1, 150)

        row = 0
        for param in PARAMS:
            attr, unit = param.attr, param.unit
            lo, hi, step, decimals = param.lo, param.hi, param.step, param.decimals
            label, tip = param.label, param.hint
            if row:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                line.setStyleSheet("color: #434c5e;")
                grid.addWidget(line, row, 0, 1, 2)
                row += 1

            caption = QtWidgets.QLabel(label)
            caption.setStyleSheet("font-weight: 600;")
            grid.addWidget(caption, row, 0,
                           QtCore.Qt.AlignmentFlag.AlignLeft
                           | QtCore.Qt.AlignmentFlag.AlignVCenter)

            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setSingleStep(step)
            spin.setDecimals(decimals)
            if unit:
                spin.setSuffix(f" {unit}")
            spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight
                              | QtCore.Qt.AlignmentFlag.AlignVCenter)
            spin.valueChanged.connect(self._value_changed)
            self._spins[attr] = spin
            grid.addWidget(spin, row, 1)
            row += 1

            hint = QtWidgets.QLabel(tip)
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #8896ab; font-size: 11px;")
            hint.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                               QtWidgets.QSizePolicy.Policy.Minimum)
            grid.addWidget(hint, row, 0, 1, 2)
            grid.setRowMinimumHeight(row, 20)
            row += 1
            grid.setRowMinimumHeight(row, 8)
            row += 1
        return box

    def _open_about(self) -> None:
        self._show(AboutDialog(self))

    def _open_debug(self) -> None:
        dialog = self._show(DebugDialog(self))
        dialog.finished.connect(self._update_debug_badge)

    @staticmethod
    def _show(dialog: QtWidgets.QDialog) -> QtWidgets.QDialog:
        """Nicht-modal, damit das Hauptfenster schliessbar bleibt."""
        dialog.setModal(False)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.show()
        dialog.raise_()
        return dialog

    def _update_debug_badge(self) -> None:
        errors = sum(1 for record in debuglog.RECORDS
                     if record[1] in ("ERROR", "CRITICAL"))
        self.btn_debug.setText("🐞  " + i18n.t("debug")
                               + (f"  ({errors})" if errors else ""))
        self.btn_debug.setStyleSheet("color: #bf616a;" if errors else "")

    # -- Vorlagen --------------------------------------------------------

    def _refresh_templates(self, select: str | None = None) -> None:
        self._loading = True
        self.template_box.clear()
        self.template_box.addItem(CUSTOM_LABEL())
        for name in settings.all_templates():
            self.template_box.addItem(name)
        target = select or settings.active_template()
        idx = self.template_box.findText(target)
        self.template_box.setCurrentIndex(idx if idx >= 0 else 0)
        self._loading = False
        self._update_delete_state()

    def _update_delete_state(self) -> None:
        name = self.template_box.currentText()
        self.btn_delete.setEnabled(
            name != CUSTOM_LABEL() and not settings.is_builtin(name))

    def _template_chosen(self) -> None:
        self._update_delete_state()
        if self._loading:
            return
        name = self.template_box.currentText()
        template = settings.all_templates().get(name)
        if template is not None:
            self._load_values(template)

    def _save_template(self) -> None:
        current = self.template_box.currentText()
        suggestion = "" if current == CUSTOM_LABEL() or settings.is_builtin(current) else current
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("template_save_title"), i18n.t("name"), text=suggestion)
        name = name.strip()
        if not ok or not name:
            return
        if settings.is_builtin(name):
            QtWidgets.QMessageBox.warning(
                self, i18n.t("name_taken"), i18n.t("name_taken_body"))
            return
        settings.save_template(name, self._collect())
        self._refresh_templates(select=name)

    def _delete_template(self) -> None:
        name = self.template_box.currentText()
        if settings.is_builtin(name) or name == CUSTOM_LABEL():
            return
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("template_delete_title"),
            i18n.t("template_delete_body", name=name))
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            settings.delete_template(name)
            self._refresh_templates(select="Standard")

    # -- Werte -----------------------------------------------------------

    def _load_values(self, values: Settings) -> None:
        self._loading = True
        data = asdict(values)
        for attr, spin in self._spins.items():
            spin.setValue(data[attr])
        self._loading = False

    def _collect(self) -> Settings:
        return Settings(**{a: s.value() for a, s in self._spins.items()}).clamped()

    def _value_changed(self) -> None:
        if self._loading:
            return
        # Handbearbeitung loest die Vorlagenbindung.
        name = self.template_box.currentText()
        template = settings.all_templates().get(name)
        if template is not None and asdict(template) != asdict(self._collect()):
            self._loading = True
            self.template_box.setCurrentIndex(0)
            self._loading = False
            self._update_delete_state()

    # -- Aktionen --------------------------------------------------------

    def _apply(self) -> None:
        values = self._collect()
        settings.apply(values)
        settings.set_active_template(self.template_box.currentText())
        settings.save()
        self._load_values(settings.snapshot())
        self.applied.emit()

    def _accept(self) -> None:
        self._apply()
        self.accept()

    def _reject(self) -> None:
        # Auch ein zwischenzeitliches "Anwenden" wird zurueckgerollt,
        # inklusive der bereits geschriebenen config.json.
        settings.apply(self._before)
        settings.set_active_template(self._before_template)
        settings.save()
        self.applied.emit()
        self.reject()



# --------------------------------------------------------- Detailansicht

def metric_value(entry: dict, key: str) -> float | None:
    """Kennwert aus einem Session-Eintrag, None wenn nicht vorhanden."""
    if key == "voiced_ratio_pct":
        raw = entry.get("voiced_ratio")
        return float(raw) * 100.0 if isinstance(raw, (int, float)) else None
    raw = entry.get(key)
    return float(raw) if isinstance(raw, (int, float)) else None


class SessionDetailDialog(QtWidgets.QDialog):
    """Alle Kennwerte einer Aufnahme, wahlweise gegen ein Ziel und
    gegen eine zweite Aufnahme."""

    changed = QtCore.Signal()

    COLUMN_KEYS = [None, "col_metric", "col_value", "col_target", "col_verdict",
                   "comparison", "delta"]

    @property
    def COLUMNS(self) -> list[str]:
        out = []
        for key in self.COLUMN_KEYS:
            if key is None:
                out.append("")          # Spalte mit den Info-Knöpfen
            elif key == "delta":
                out.append("Δ")
            else:
                out.append(i18n.t(key))
        return out

    def __init__(self, entry: dict, entries: list[dict], session_dir, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.entries = entries
        self.session_dir = session_dir
        self._columns_sized = False
        self._samples = None
        self._rate = 0
        self._selection_stats = None
        self._selection_span = None

        self.setWindowTitle(i18n.t("dlg_detail"))
        self.setMinimumSize(880, 640)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)
        root.addWidget(self._build_header())
        root.addWidget(self._build_selectors())

        self.table = QtWidgets.QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        head = self.table.horizontalHeader()
        # Alle Spalten von Hand verschiebbar; nur die Info-Spalte bleibt schmal.
        head.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        head.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        head.setStretchLastSection(True)
        self.table.setColumnWidth(0, 30)
        self.table.verticalHeader().setDefaultSectionSize(30)
        root.addWidget(self.table, 1)

        self.selection_note = QtWidgets.QLabel("")
        self.selection_note.setStyleSheet("color: #ebcb8b; font-size: 11px;")
        self.selection_note.setVisible(False)
        root.addWidget(self.selection_note)

        self.btn_advanced = QtWidgets.QToolButton()
        self.btn_advanced.setText("▸  " + i18n.t("advanced"))
        self.btn_advanced.setAutoRaise(True)
        self.btn_advanced.setCheckable(True)
        self.btn_advanced.setStyleSheet(
            "QToolButton { color: #88c0d0; font-weight: 600; border: none; }")
        self.btn_advanced.toggled.connect(self._toggle_advanced)
        root.addWidget(self.btn_advanced, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.advanced = self._build_advanced()
        self.advanced.setVisible(False)
        root.addWidget(self.advanced)

        for key in ("targets_note", "vowel_only_note"):
            note = QtWidgets.QLabel(i18n.t(key))
            note.setWordWrap(True)
            note.setStyleSheet("color: #8896ab; font-size: 11px;")
            root.addWidget(note)

        row = QtWidgets.QHBoxLayout()
        btn_play = QtWidgets.QPushButton(i18n.t("play"))
        btn_play.clicked.connect(self._play)
        btn_stop = QtWidgets.QPushButton(i18n.t("stop"))
        btn_stop.clicked.connect(lambda: sd.stop())
        btn_again = QtWidgets.QPushButton(i18n.t("reanalyse"))
        btn_again.clicked.connect(self._reanalyse)
        btn_export = QtWidgets.QPushButton(i18n.t("export"))
        btn_export.clicked.connect(self._export)
        btn_target = QtWidgets.QPushButton(i18n.t("set_custom_target"))
        btn_target.clicked.connect(self._set_custom_target)
        btn_close = QtWidgets.QPushButton(i18n.t("close"))
        btn_close.setObjectName("primary")
        btn_close.clicked.connect(self.accept)
        row.addWidget(btn_play)
        row.addWidget(btn_stop)
        row.addWidget(btn_again)
        row.addWidget(btn_export)
        row.addWidget(btn_target)
        row.addStretch(1)
        row.addWidget(btn_close)
        root.addLayout(row)

        self._fill()

    def _build_header(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("recording_head"))
        lay = QtWidgets.QVBoxLayout(box)
        stamp = self.entry.get("timestamp", "").replace("T", "  ")
        duration = self.entry.get("duration", 0.0)
        quality = self.entry.get("quality", "ok")
        title = QtWidgets.QLabel(
            f"{stamp}   ·   {duration:.1f} s   ·   {self.entry.get('file', '')}")
        title.setStyleSheet("font-weight: 600;")
        lay.addWidget(title)
        if quality != "ok":
            warn = QtWidgets.QLabel(i18n.t("no_signal_note"))
            warn.setStyleSheet("color: #ebcb8b;")
            warn.setWordWrap(True)
            lay.addWidget(warn)
        floor = self.entry.get("pitch_floor")
        ceiling = self.entry.get("pitch_ceiling")
        if floor and ceiling:
            meta = QtWidgets.QLabel(i18n.t(
                "measured_with", floor=floor, ceiling=ceiling,
                formant=self.entry.get("formant_ceiling", 0.0)))
            meta.setStyleSheet("color: #8896ab; font-size: 11px;")
            lay.addWidget(meta)
        return box

    def _build_selectors(self) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)

        self.type_box = QtWidgets.QComboBox()
        for kind in rectypes.TYPES:
            self.type_box.addItem(kind.label, kind.key)
        index = self.type_box.findData(rectypes.get(self.entry.get("type")).key)
        self.type_box.setCurrentIndex(max(0, index))
        self.type_box.currentIndexChanged.connect(self._type_changed)

        self.profile_box = QtWidgets.QComboBox()
        keys = targets.profile_keys()
        for key in keys:
            self.profile_box.addItem(targets.profile_label(key), key)
        index = self.profile_box.findData(settings.get_profile())
        self.profile_box.setCurrentIndex(max(0, index))
        self.profile_box.currentIndexChanged.connect(self._fill)

        self.compare_box = QtWidgets.QComboBox()
        self.compare_box.addItem(i18n.t("no_comparison"), None)
        for other in self.entries:
            if other is self.entry:
                continue
            label = other.get("timestamp", "").replace("T", "  ")
            median = other.get("f0_median")
            if isinstance(median, (int, float)):
                label += f"   ({median:.0f} Hz)"
            elif other.get("quality") != "ok":
                label += "   (" + i18n.t("no_speech") + ")"
            self.compare_box.addItem(label, other)
        self.compare_box.currentIndexChanged.connect(self._fill)

        lay.addWidget(QtWidgets.QLabel(i18n.t("recording_type")))
        lay.addWidget(self.type_box)
        lay.addSpacing(20)
        lay.addWidget(QtWidgets.QLabel(i18n.t("target")))
        lay.addWidget(self.profile_box)
        lay.addSpacing(20)
        lay.addWidget(QtWidgets.QLabel(i18n.t("comparison")))
        lay.addWidget(self.compare_box, 1)
        return box

    def _fill(self) -> None:
        profile = self.profile_box.currentData() or "none"
        settings.set_profile(profile)
        source = self._selection_stats or self.entry

        if self._selection_stats is not None and self._selection_span:
            start, end = self._selection_span
            self.selection_note.setText(
                i18n.t("showing_selection", start=start, end=end))
            self.selection_note.setVisible(True)
        else:
            self.selection_note.setVisible(False)
        other = self.compare_box.currentData()

        self.table.setRowCount(len(targets.METRICS))
        for r, metric in enumerate(targets.METRICS):
            value = metric_value(source, metric.key)
            rng = targets.range_for(metric.key, profile)
            note = targets.verdict(value, rng)
            fmt = f"{{:.{metric.decimals}f}}"

            label = metric.label
            if metric.vowel_only:
                label += f"   ({i18n.t('vowel_only_marker')})"
            cells = [
                None,      # Platzhalter fuer den Info-Knopf
                label,
                f"{fmt.format(value)} {metric.unit}".strip() if value is not None else "—",
                targets.format_range(rng, metric.unit, metric.decimals),
                note or "—",
            ]

            if other is None:
                cells += ["—", "—"]
            else:
                ref = metric_value(other, metric.key)
                cells.append(f"{fmt.format(ref)} {metric.unit}".strip()
                             if ref is not None else "—")
                if value is not None and ref is not None:
                    delta = value - ref
                    cells.append(f"{delta:+.{metric.decimals}f} {metric.unit}".strip())
                else:
                    cells.append("—")

            for c, text in enumerate(cells):
                if text is None:
                    self.table.setCellWidget(r, c, self._info_button(metric))
                    continue
                item = QtWidgets.QTableWidgetItem(text)
                if c == 1:
                    item.setToolTip(metric.hint)
                if c == 4 and note:
                    inside = targets.is_within(value, rng)
                    item.setForeground(QtGui.QColor(
                        "#a3be8c" if inside else "#ebcb8b"))
                if c == 6 and text not in ("—", ""):
                    item.setForeground(QtGui.QColor("#88c0d0"))
                self.table.setItem(r, c, item)
        if not self._columns_sized:
            self.table.resizeColumnsToContents()
            self.table.setColumnWidth(0, 30)
            self.table.setColumnWidth(1, max(200, self.table.columnWidth(1)))
            self._columns_sized = True

    # -- Erweiterter Bereich ---------------------------------------------

    def _build_advanced(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("waveform"))
        lay = QtWidgets.QVBoxLayout(box)

        hint = QtWidgets.QLabel(i18n.t("advanced_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8896ab; font-size: 11px;")
        lay.addWidget(hint)

        self.wave_plot = pg.PlotWidget()
        self.wave_plot.setBackground("#3b4252")
        self.wave_plot.setMinimumHeight(170)
        self.wave_plot.setMenuEnabled(False)
        self.wave_plot.hideButtons()
        self.wave_plot.setLabel("bottom", i18n.t("seconds"))
        self.wave_plot.getAxis("left").setStyle(showValues=False)
        self.wave_plot.setMouseEnabled(x=True, y=False)
        lay.addWidget(self.wave_plot)

        self.region = pg.LinearRegionItem(brush=pg.mkBrush(136, 192, 208, 50),
                                          hoverBrush=pg.mkBrush(136, 192, 208, 80))
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self._region_moved)

        self.range_label = QtWidgets.QLabel("")
        self.range_label.setStyleSheet("color: #eceff4;")
        lay.addWidget(self.range_label)

        row = QtWidgets.QHBoxLayout()
        self.btn_sel_analyse = QtWidgets.QPushButton(i18n.t("analyse_selection"))
        self.btn_sel_analyse.setObjectName("primary")
        self.btn_sel_analyse.clicked.connect(self._analyse_selection)
        btn_sel_play = QtWidgets.QPushButton(i18n.t("play_selection"))
        btn_sel_play.clicked.connect(self._play_selection)
        btn_full = QtWidgets.QPushButton(i18n.t("full_recording"))
        btn_full.clicked.connect(self._show_full)
        self.btn_sel_save = QtWidgets.QPushButton(i18n.t("save_selection"))
        self.btn_sel_save.setEnabled(False)
        self.btn_sel_save.clicked.connect(self._save_selection)
        for widget in (self.btn_sel_analyse, btn_sel_play, btn_full):
            row.addWidget(widget)
        row.addStretch(1)
        row.addWidget(self.btn_sel_save)
        lay.addLayout(row)
        return box

    def _toggle_advanced(self, on: bool) -> None:
        self.btn_advanced.setText(("▾  " if on else "▸  ") + i18n.t("advanced"))
        self.advanced.setVisible(on)
        if on and self._samples is None:
            self._load_waveform()
        if on:
            self.resize(self.width(), max(self.height(), 900))

    def _load_waveform(self) -> None:
        path = self._path()
        if not path.exists():
            self.wave_plot.setTitle(i18n.t("file_missing"))
            return
        try:
            data, rate = audio_mod.read_wav(path)
        except Exception as exc:
            self.wave_plot.setTitle(str(exc))
            return

        self._samples, self._rate = data, rate
        xs, ys = audio_mod.envelope(data, 2400)
        seconds = xs / float(rate)
        self.wave_plot.plot(seconds, ys, pen=pg.mkPen("#88c0d0", width=1))
        duration = data.size / float(rate)
        self.wave_plot.setXRange(0, duration, padding=0)
        self.wave_plot.addItem(self.region)
        # Voreinstellung: mittleres Drittel, damit sofort sichtbar ist,
        # dass sich der Bereich ziehen laesst.
        self.region.setRegion((duration / 3.0, duration * 2.0 / 3.0))
        self.region.setBounds((0.0, duration))
        self._region_moved()

    def _span(self) -> tuple[float, float]:
        low, high = self.region.getRegion()
        return float(min(low, high)), float(max(low, high))

    def _region_moved(self) -> None:
        start, end = self._span()
        self.range_label.setText(
            i18n.t("selection_label", start=start, end=end, length=end - start))

    def _selected_samples(self) -> np.ndarray | None:
        if self._samples is None:
            return None
        start, end = self._span()
        a, b = int(start * self._rate), int(end * self._rate)
        a, b = max(0, a), min(self._samples.size, b)
        return self._samples[a:b] if b > a else None

    def _play_selection(self) -> None:
        chunk = self._selected_samples()
        if chunk is None or chunk.size == 0:
            return
        try:
            sd.play(chunk, self._rate)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, i18n.t("play"), str(exc))

    def _analyse_selection(self) -> None:
        chunk = self._selected_samples()
        if chunk is None or chunk.size < int(0.3 * self._rate):
            QtWidgets.QMessageBox.information(
                self, i18n.t("advanced"), i18n.t("selection_too_short"))
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            stats = analysis.analyse_recording(chunk.astype(np.float64), self._rate)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        self._selection_stats = stats
        self._selection_span = self._span()
        self.btn_sel_save.setEnabled(True)
        self._fill()

    def _show_full(self) -> None:
        self._selection_stats = None
        self._selection_span = None
        self.btn_sel_save.setEnabled(False)
        self._fill()

    def _save_selection(self) -> None:
        if self._selection_stats is None:
            return
        self.entry.update(self._selection_stats)
        start, end = self._selection_span
        self.entry["selection"] = [round(start, 3), round(end, 3)]
        self.changed.emit()
        self._show_full()
        QtWidgets.QMessageBox.information(
            self, i18n.t("advanced"), i18n.t("selection_saved"))

    def _info_button(self, metric) -> QtWidgets.QWidget:
        """Kleines (i) mit Erklaerung — als Tooltip und auf Klick als Popup."""
        button = QtWidgets.QToolButton()
        button.setText("ⓘ")
        button.setCursor(QtCore.Qt.CursorShape.WhatsThisCursor)
        button.setAutoRaise(True)
        button.setToolTip(f"<b>{metric.label}</b><br>{metric.hint}")
        button.setAccessibleName(i18n.t("info_tip"))
        button.setStyleSheet(
            "QToolButton { color: #8896ab; border: none; font-size: 14px; }"
            "QToolButton:hover { color: #88c0d0; }")
        button.clicked.connect(
            lambda _=False, m=metric, b=button: QtWidgets.QToolTip.showText(
                b.mapToGlobal(QtCore.QPoint(0, b.height())),
                f"<div style='max-width:380px'><b>{m.label}</b><br>{m.hint}</div>",
                b))

        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(button, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        return box

    def _type_changed(self) -> None:
        key = self.type_box.currentData()
        if self.entry.get("type") == key:
            return
        self.entry["type"] = key
        self.changed.emit()

    def _set_custom_target(self) -> None:
        """Die angezeigten Werte als eigenen Zielbereich sichern."""
        source = self._selection_stats or self.entry
        ranges = targets.build_custom(source)
        if not ranges:
            QtWidgets.QMessageBox.information(
                self, i18n.t("set_custom_target"), i18n.t("custom_target_missing"))
            return
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("set_custom_target"), i18n.t("name"),
            text=i18n.t("profile_custom"))
        name = name.strip()
        if not ok or not name:
            return

        settings.save_user_profile(name, ranges)
        key = targets.USER_PREFIX + name
        settings.set_profile(key)

        blocked = self.profile_box.blockSignals(True)
        self.profile_box.clear()
        for entry in targets.profile_keys():
            self.profile_box.addItem(targets.profile_label(entry), entry)
        self.profile_box.setCurrentIndex(max(0, self.profile_box.findData(key)))
        self.profile_box.blockSignals(blocked)

        self._fill()
        QtWidgets.QMessageBox.information(
            self, i18n.t("set_custom_target"),
            i18n.t("custom_target_set",
                   percent=targets.CUSTOM_TOLERANCE * 100.0))

    # -- Export ----------------------------------------------------------

    def _report_rows(self) -> list[dict]:
        """Die aktuell angezeigten Werte in maschinenlesbarer Form."""
        profile = self.profile_box.currentData() or "none"
        other = self.compare_box.currentData()
        source = self._selection_stats or self.entry

        rows = []
        for metric in targets.METRICS:
            value = metric_value(source, metric.key)
            rng = targets.range_for(metric.key, profile)
            low, high = rng if rng else (None, None)
            reference = metric_value(other, metric.key) if other else None
            rows.append({
                "key": metric.key,
                "label": metric.label,
                "unit": metric.unit,
                "decimals": metric.decimals,
                "vowel_only": metric.vowel_only,
                "value": value,
                "target_low": low,
                "target_high": high,
                "target": targets.format_range(rng, metric.unit, metric.decimals),
                "verdict": targets.verdict(value, rng),
                "comparison": reference,
                "delta": (value - reference
                          if value is not None and reference is not None else None),
                "hint": metric.hint,
            })
        return rows

    def _report_header(self) -> list[str]:
        source = self._selection_stats or self.entry
        lines = [
            i18n.t("report_title"),
            "=" * len(i18n.t("report_title")),
            f"{i18n.t('report_generated')}: "
            f"{datetime.now().isoformat(timespec='seconds')}",
            f"{i18n.t('report_recording')}: {self.entry.get('file', '')}  "
            f"({self.entry.get('timestamp', '')}, "
            f"{source.get('duration', 0.0):.1f} s)",
        ]
        floor = source.get("pitch_floor")
        ceiling = source.get("pitch_ceiling")
        if floor and ceiling:
            lines.append(i18n.t("measured_with", floor=floor, ceiling=ceiling,
                                formant=source.get("formant_ceiling", 0.0)))
        if self._selection_stats is not None and self._selection_span:
            start, end = self._selection_span
            lines.append(f"{i18n.t('report_selection')}: "
                         f"{start:.2f} – {end:.2f} s")
        lines.append(f"{i18n.t('target')}: {self.profile_box.currentText()}")
        other = self.compare_box.currentData()
        if other is not None:
            lines.append(f"{i18n.t('comparison')}: {other.get('timestamp', '')} "
                         f"({other.get('file', '')})")
        return lines

    def _report_text(self) -> str:
        rows = self._report_rows()

        def cell(value, decimals, unit):
            if value is None:
                return "—"
            return f"{value:.{decimals}f} {unit}".strip()

        table = [[
            r["label"] + ("  (" + i18n.t("vowel_only_marker") + ")"
                          if r["vowel_only"] else ""),
            cell(r["value"], r["decimals"], r["unit"]),
            r["target"],
            r["verdict"] or "—",
            cell(r["comparison"], r["decimals"], r["unit"]),
            (f"{r['delta']:+.{r['decimals']}f} {r['unit']}".strip()
             if r["delta"] is not None else "—"),
        ] for r in rows]

        head = [i18n.t("col_metric"), i18n.t("col_value"), i18n.t("col_target"),
                i18n.t("col_verdict"), i18n.t("comparison"), "Delta"]
        widths = [max(len(head[c]), *(len(row[c]) for row in table))
                  for c in range(len(head))]

        out = self._report_header()
        out += ["", "  ".join(h.ljust(widths[c]) for c, h in enumerate(head)).rstrip(),
                "  ".join("-" * w for w in widths)]
        for row in table:
            out.append("  ".join(v.ljust(widths[c]) for c, v in enumerate(row)).rstrip())

        out += ["", i18n.t("report_notes") + ":", "  " + i18n.t("targets_note"),
                "  " + i18n.t("vowel_only_note"),
                "", i18n.t("report_explanations") + ":"]
        for r in rows:
            out.append(f"  {r['label']}: {r['hint']}")
        return "\n".join(out) + "\n"

    def _report_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["metric", "key", "value", "unit", "target_low",
                         "target_high", "verdict", "comparison", "delta",
                         "vowel_only"])
        for r in self._report_rows():
            writer.writerow([
                r["label"], r["key"],
                "" if r["value"] is None else f"{r['value']:.4f}",
                r["unit"],
                "" if r["target_low"] is None else f"{r['target_low']:.4f}",
                "" if r["target_high"] is None else f"{r['target_high']:.4f}",
                r["verdict"],
                "" if r["comparison"] is None else f"{r['comparison']:.4f}",
                "" if r["delta"] is None else f"{r['delta']:.4f}",
                "yes" if r["vowel_only"] else "no",
            ])
        return buffer.getvalue()

    def _export(self) -> None:
        language = ask_export_language(self)
        if language is None:
            return
        stem = Path(self.entry.get("file", "session")).stem
        suggestion = str(self.session_dir / f"{stem}-report.txt")
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(
            self, i18n.t("export_title"), suggestion, i18n.t("export_filter"))
        if not path:
            return
        if not Path(path).suffix:
            path += ".csv" if "csv" in (chosen or "").lower() else ".txt"

        try:
            with export_language(language):
                text = (self._report_csv() if path.lower().endswith(".csv")
                        else self._report_text())
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            QtWidgets.QMessageBox.warning(self, i18n.t("export_failed"), str(exc))
            return
        QtWidgets.QMessageBox.information(
            self, i18n.t("export_title"), i18n.t("exported", path=path))

    def _path(self):
        return self.session_dir / self.entry.get("file", "")

    def _play(self) -> None:
        path = self._path()
        if not path.exists():
            QtWidgets.QMessageBox.information(self, i18n.t("play"), i18n.t("file_missing"))
            return
        try:
            with wave.open(str(path), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
                rate = wf.getframerate()
            data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            sd.play(data, rate)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, i18n.t("play"), str(exc))

    def _reanalyse(self) -> None:
        path = self._path()
        if not path.exists():
            QtWidgets.QMessageBox.information(
                self, i18n.t("reanalyse"), i18n.t("no_wav"))
            return
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            stats = analysis.analyse_file(path)
        except Exception as exc:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.warning(self, i18n.t("reanalyse"), str(exc))
            return
        QtWidgets.QApplication.restoreOverrideCursor()
        self.entry.update(stats)
        self.changed.emit()
        self._fill()


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
        hint.setStyleSheet("color: #8896ab; font-size: 11px;")
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
                    item.setForeground(QtGui.QColor("#bf616a"))
                elif c == 1 and level == "WARNING":
                    item.setForeground(QtGui.QColor("#ebcb8b"))
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
        hint.setStyleSheet("color: #8896ab; font-size: 11px;")
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


# ------------------------------------------------------------- Infofenster

class AboutDialog(QtWidgets.QDialog):
    """Version, Lizenz, Links und der gesundheitliche Hinweis.

    Bewusst ohne Aktualisierungsprüfung: das Programm baut keine
    Netzwerkverbindungen auf, und dabei soll es bleiben.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("about_title"))
        self.setMinimumWidth(560)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(14)
        root.addLayout(self._build_head())

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._build_body())
        root.addWidget(scroll, 1)

        row = QtWidgets.QHBoxLayout()
        copy = QtWidgets.QPushButton(i18n.t("copy_env"))
        copy.clicked.connect(self._copy_environment)
        folder = QtWidgets.QPushButton(i18n.t("open_folder"))
        folder.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(str(paths.CONFIG_DIR))))
        close = QtWidgets.QPushButton(i18n.t("close"))
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        row.addWidget(copy)
        row.addWidget(folder)
        row.addStretch(1)
        row.addWidget(close)
        root.addLayout(row)

    def _build_head(self) -> QtWidgets.QHBoxLayout:
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(16)

        icon_path = paths.icon_file()
        if icon_path is not None:
            label = QtWidgets.QLabel()
            label.setPixmap(QtGui.QIcon(str(icon_path)).pixmap(84, 84))
            row.addWidget(label, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        text = QtWidgets.QVBoxLayout()
        text.setSpacing(4)
        name = QtWidgets.QLabel(paths.APP_NAME)
        font = name.font()
        font.setPointSize(font.pointSize() + 7)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        name.setFont(font)
        version = QtWidgets.QLabel(f"v{paths.APP_VERSION}")
        version.setStyleSheet("color: #8896ab;")
        tagline = QtWidgets.QLabel(i18n.t("about_tagline"))
        tagline.setWordWrap(True)
        text.addWidget(name)
        text.addWidget(version)
        text.addWidget(tagline)
        row.addLayout(text, 1)
        return row

    def _build_body(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        links = QtWidgets.QGroupBox(i18n.t("about_links"))
        links_lay = QtWidgets.QVBoxLayout(links)
        for label, url in ((i18n.t("about_source"), paths.APP_URL),
                           (i18n.t("about_discord"), paths.DISCORD_URL),
                           (i18n.t("about_kofi"), paths.KOFI_URL)):
            item = QtWidgets.QLabel(
                f'<a href="{url}" style="color:#88c0d0; '
                f'text-decoration:none;">{label}</a>'
                f'<br><span style="color:#5a6478; font-size:11px;">{url}</span>')
            item.setOpenExternalLinks(True)
            item.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
            links_lay.addWidget(item)
        lay.addWidget(links)

        lay.addWidget(self._section(i18n.t("about_license_head"),
                                    i18n.t("about_license")))
        lay.addWidget(self._section(i18n.t("about_privacy_head"),
                                    i18n.t("about_privacy")))
        lay.addWidget(self._section(
            i18n.t("about_paths"),
            f"{paths.CONFIG_PATH}\n{paths.SESSION_DIR}", mono=True))

        note = QtWidgets.QLabel(i18n.t("about_health"))
        note.setWordWrap(True)
        note.setStyleSheet(
            "color: #ebcb8b; border: 1px solid #4c566a; border-radius: 8px;"
            "padding: 10px;")
        lay.addWidget(note)

        citation = QtWidgets.QLabel(i18n.t("about_citation"))
        citation.setWordWrap(True)
        citation.setStyleSheet("color: #8896ab; font-size: 11px;")
        lay.addWidget(citation)
        lay.addStretch(1)
        return page

    @staticmethod
    def _section(title: str, body: str, mono: bool = False) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(title)
        lay = QtWidgets.QVBoxLayout(box)
        label = QtWidgets.QLabel(body)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        if mono:
            label.setFont(QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.SystemFont.FixedFont))
            label.setStyleSheet("color: #8896ab;")
        lay.addWidget(label)
        return box

    def _copy_environment(self) -> None:
        QtWidgets.QApplication.clipboard().setText(
            "\n".join(debuglog.environment()))
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), i18n.t("copied"), self)


# --------------------------------------------------------- Gefuehrter Ablauf

class GuidedPanel(QtWidgets.QWidget):
    """Fuehrt durch Summen, /a/, /i/ und /u/ — als schmale Leiste im
    Live-Reiter statt als Fenster.

    Ein Popup mitten im Blickfeld reisst einen beim Halten eines Lautes
    heraus. Deshalb bleibt hier alles an einer Stelle sichtbar, die
    Kennzahlen und das Spektrogramm daneben laufen weiter.

    Jede Aufnahme wird auf ihre stabile Mitte gekuerzt — der Schritt, den man
    sonst von Hand im erweiterten Modus macht und deshalb meistens sein laesst.
    """

    finished = QtCore.Signal()

    COUNTDOWN = 3

    def __init__(self, engine, store, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.store = store
        self.steps = [rectypes.get(key) for key in rectypes.GUIDED]
        self.index = 0
        self.saved = 0
        self.phase = "idle"
        self.remaining = 0.0

        # Wie die anderen Bereiche ein Kasten mit Ueberschrift, damit die
        # Leiste nicht zwischen Diagramm und Uebungstext eingequetscht wirkt.
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QtWidgets.QGroupBox(i18n.t("guided_title"))
        outer.addWidget(box)

        inner = QtWidgets.QVBoxLayout(box)
        inner.setContentsMargins(14, 10, 14, 12)
        inner.setSpacing(10)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(16)

        self.step_label = QtWidgets.QLabel("")
        self.step_label.setStyleSheet(
            "color: #8896ab; font-size: 10px; letter-spacing: 1px;")

        self.title = QtWidgets.QLabel("")
        font = self.title.font()
        font.setPointSize(font.pointSize() + 6)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        self.title.setFont(font)
        self.title.setStyleSheet("color: #88c0d0;")

        heading = QtWidgets.QVBoxLayout()
        heading.setSpacing(1)
        heading.addWidget(self.step_label)
        heading.addWidget(self.title)
        row.addLayout(heading)

        self.state = QtWidgets.QLabel("")
        font = self.state.font()
        font.setPointSize(font.pointSize() + 1)
        self.state.setFont(font)
        self.state.setStyleSheet("color: #a3be8c;")
        row.addSpacing(8)
        row.addWidget(self.state, 1)

        self.bar = QtWidgets.QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        self.bar.setMinimumWidth(200)
        self.bar.setStyleSheet(
            "QProgressBar { background: #2e3440; border: none; border-radius: 5px; }"
            "QProgressBar::chunk { background: #88c0d0; border-radius: 5px; }")
        row.addWidget(self.bar)

        self.btn_go = QtWidgets.QPushButton(i18n.t("guided_next"))
        self.btn_go.setObjectName("primary")
        self.btn_go.setMinimumWidth(110)
        self.btn_go.clicked.connect(self._start_step)
        self.btn_skip = QtWidgets.QPushButton(i18n.t("guided_skip"))
        self.btn_skip.clicked.connect(self._next_step)
        row.addSpacing(8)
        row.addWidget(self.btn_go)
        row.addWidget(self.btn_skip)
        inner.addLayout(row)

        self.hint = QtWidgets.QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #8896ab; font-size: 11px;")
        inner.addWidget(self.hint)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._tick)
        self.reset()

    # -- Ablauf ----------------------------------------------------------

    def reset(self) -> None:
        self.timer.stop()
        if self.engine.is_recording:
            self.engine.stop_recording()
        self.phase = "idle"
        self.index = 0
        self.saved = 0
        self.btn_go.setEnabled(True)
        self.btn_skip.setEnabled(True)
        self._show_step()

    def _show_step(self) -> None:
        if self.index >= len(self.steps):
            self.step_label.setText("")
            self.title.setText("")
            self.hint.setText(i18n.t("guided_intro"))
            self.state.setText(i18n.t("guided_done", count=self.saved))
            self.bar.setValue(0)
            self.btn_go.setEnabled(False)
            self.btn_skip.setEnabled(False)
            return

        step = self.steps[self.index]
        self.step_label.setText(i18n.t("guided_step", step=self.index + 1,
                                       total=len(self.steps)))
        self.title.setText(step.label)
        self.hint.setText(f"{step.hint}  {i18n.t('guided_ready')}")
        self.state.setText("")
        self.bar.setValue(0)

    def _start_step(self) -> None:
        if self.index >= len(self.steps):
            return
        self.btn_go.setEnabled(False)
        self.btn_skip.setEnabled(False)
        self.phase = "countdown"
        self.remaining = float(self.COUNTDOWN)
        self.bar.setRange(0, int(self.COUNTDOWN * 10))
        self.timer.start()

    def _tick(self) -> None:
        self.remaining -= 0.1

        if self.phase == "countdown":
            self.state.setText(i18n.t("guided_get_ready",
                                      seconds=max(0, int(self.remaining) + 1)))
            self.bar.setValue(int((self.COUNTDOWN - self.remaining) * 10))
            if self.remaining <= 0.0:
                self._begin_recording()
            return

        if self.phase == "recording":
            self.engine.pump()
            step = self.steps[self.index]
            total = step.seconds or 3.0
            self.state.setText(i18n.t("guided_recording",
                                      seconds=max(0, int(self.remaining) + 1)))
            self.bar.setValue(int((total - self.remaining) * 10))
            if self.remaining <= 0.0:
                self._finish_recording()

    def _begin_recording(self) -> None:
        step = self.steps[self.index]
        self.phase = "recording"
        self.remaining = step.seconds or 3.0
        self.bar.setRange(0, int(self.remaining * 10))
        self.engine.pump()
        self.engine.start_recording()

    def _finish_recording(self) -> None:
        self.timer.stop()
        self.phase = "idle"
        self.engine.pump()
        samples = self.engine.stop_recording()
        step = self.steps[self.index]

        rate = self.engine.samplerate
        if samples.size < int(0.5 * rate):
            self.state.setText(i18n.t("too_short"))
            self.btn_go.setEnabled(True)
            self.btn_skip.setEnabled(True)
            return

        span = None
        if step.sustained:
            target = max(1.5, (step.seconds or 3.0) - 1.2)
            begin, end = analysis.stable_span(samples.astype(np.float64),
                                              rate, target)
            if end > begin:
                span = (begin / rate, end / rate)
                samples = samples[begin:end]

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            self.store(samples, step.key, span)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        self.saved += 1
        self.state.setText(i18n.t("guided_saved", length=samples.size / rate))
        QtCore.QTimer.singleShot(900, self._next_step)

    def _next_step(self) -> None:
        self.timer.stop()
        if self.engine.is_recording:
            self.engine.stop_recording()
        self.phase = "idle"
        self.index += 1
        self.btn_go.setEnabled(True)
        self.btn_skip.setEnabled(True)
        self._show_step()
        if self.index >= len(self.steps):
            self.finished.emit()

    def stop(self) -> None:
        self.timer.stop()
        if self.engine.is_recording:
            self.engine.stop_recording()
        self.phase = "idle"


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
        hint.setStyleSheet("color: #8896ab; font-size: 11px;")
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
        self.note.setStyleSheet("color: #ebcb8b; font-size: 11px;")
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
