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

import csv
import io
import json
import sys
import wave
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import sounddevice as sd
from PySide6 import QtCore, QtGui, QtWidgets

import analysis
import columns
import debuglog
import i18n
import paths
import rectypes
import settings
import targets
import audio as audio_mod
from audio import DEFAULT_KEY, AudioEngine, write_wav
from dialogs import (FilterDialog, GuidedPanel, SessionDetailDialog,
                     SettingsDialog, ask_export_language, export_language)
from settings import CFG

APP_DIR = Path(__file__).resolve().parent
SESSION_DIR = paths.SESSION_DIR
SESSION_INDEX = paths.SESSION_INDEX

TICK_MS = 50                # UI-Takt
ANALYSIS_EVERY = 2          # Analyse nur bei jedem n-ten Tick (-> 10 Hz)
WINDOW_SECONDS = 0.40       # Analysefenster
NFFT = 2048
HOP = 1024
SPEC_COLS = 320
KEY_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
MAX_FREQ = 5000.0
SPEC_FLOOR_DB = -95.0
LOW_LEVEL_DB = -40.0
SPEC_CEIL_DB = -25.0
HISTORY_SECONDS = 30.0

NORD = {
    "bg": "#2e3440", "bg2": "#3b4252", "bg3": "#434c5e",
    "fg": "#eceff4", "dim": "#8896ab",
    "accent": "#88c0d0", "light": "#b8e2ee", "green": "#a3be8c", "yellow": "#ebcb8b",
    "red": "#bf616a", "purple": "#b48ead",
}

STYLESHEET = f"""
QWidget {{ background: {NORD['bg']}; color: {NORD['fg']};
           font-family: "Noto Sans", sans-serif; font-size: 13px; }}
QGroupBox {{ background: {NORD['bg2']}; border: 1px solid {NORD['bg3']};
             border-radius: 8px; margin-top: 14px; padding: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px;
                    color: {NORD['dim']}; font-size: 11px;
                    text-transform: uppercase; letter-spacing: 1px; }}
QPushButton {{ background: {NORD['bg3']}; border: none; border-radius: 6px;
               padding: 8px 16px; font-weight: 600; }}
QPushButton:hover {{ background: #4c566a; }}
QPushButton:disabled {{ color: {NORD['dim']}; background: {NORD['bg2']}; }}
QPushButton#primary {{ background: {NORD['accent']}; color: {NORD['bg']}; }}
QPushButton#record {{ background: {NORD['red']}; color: {NORD['fg']}; }}
QPushButton#rowaction, QPushButton#danger {{ padding: 5px 12px; font-weight: 500; }}
QPushButton#guided:checked {{ background: {NORD['light']}; color: {NORD['bg']};
    font-weight: 700; border: 1px solid {NORD['accent']}; }}
QPushButton#guided:checked:hover {{ background: #cfe9f1; }}
QPushButton#langleft, QPushButton#langright {{ padding: 8px 0; font-size: 11px;
    background: {NORD['bg2']}; color: {NORD['dim']}; border-radius: 0; }}
QPushButton#langleft {{ border-top-left-radius: 6px; border-bottom-left-radius: 6px; }}
QPushButton#langright {{ border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
QPushButton#langleft:checked, QPushButton#langright:checked {{
    background: {NORD['accent']}; color: {NORD['bg']}; font-weight: 700; }}
QPushButton#danger {{ background: {NORD['bg3']}; color: {NORD['red']}; }}
QPushButton#danger:hover {{ background: {NORD['red']}; color: {NORD['fg']}; }}
QComboBox {{ background: {NORD['bg3']}; border: none; border-radius: 6px;
             padding: 7px 10px; min-width: 220px; }}
QComboBox QAbstractItemView {{ background: {NORD['bg2']};
                               selection-background-color: {NORD['bg3']}; }}
QTextEdit, QTableWidget {{ background: {NORD['bg2']}; border: 1px solid {NORD['bg3']};
                           border-radius: 8px; }}
QHeaderView::section {{ background: {NORD['bg3']}; border: none; padding: 6px; }}
QTableWidget {{ gridline-color: {NORD['bg3']}; }}
QTabBar::tab {{ background: {NORD['bg2']}; padding: 9px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {NORD['bg3']}; color: {NORD['accent']}; }}
QTabWidget::pane {{ border: none; }}
QStatusBar {{ color: {NORD['dim']}; }}
"""


# ---------------------------------------------------------------- Widgets

class StatCard(QtWidgets.QFrame):
    """Grosse Zahl mit Beschriftung."""

    def __init__(self, title: str, unit: str = "", color: str = NORD["fg"]):
        super().__init__()
        self.setStyleSheet(
            f"QFrame {{ background: {NORD['bg2']}; border-radius: 8px; }}")
        self._unit = unit

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        cap = QtWidgets.QLabel(title.upper())
        cap.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 10px; letter-spacing: 1px;")

        self.value = QtWidgets.QLabel("--")
        f = self.value.font()
        f.setPointSize(26)
        f.setWeight(QtGui.QFont.Weight.DemiBold)
        self.value.setFont(f)
        self.value.setStyleSheet(f"color: {color};")

        lay.addWidget(cap)
        lay.addWidget(self.value)
        self._base_color = color

    def set_color(self, color: str | None = None) -> None:
        self.value.setStyleSheet(f"color: {color or self._base_color};")

    def set(self, text: str) -> None:
        self.value.setText(f"{text}{self._unit}" if text != "--" else "--")


class ZoneBar(QtWidgets.QWidget):
    """Horizontaler Balken 60-350 Hz mit Zonenfaerbung und Marker."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(58)
        self.f0: float | None = None
        self.recent: deque[float] = deque(maxlen=120)

    def update_value(self, f0: float | None) -> None:
        self.f0 = f0
        if f0 is not None:
            self.recent.append(f0)
        self.update()

    @property
    def LO(self) -> float:
        return max(40.0, CFG.pitch_floor)

    @property
    def HI(self) -> float:
        return min(CFG.pitch_ceiling, max(CFG.zone_high + 140.0, self.LO + 120.0))

    def _ticks(self) -> list[int]:
        span = self.HI - self.LO
        step = next((s for s in (10, 20, 25, 50, 100) if span / s <= 8), 100)
        first = int(np.ceil(self.LO / step) * step)
        return list(range(first, int(self.HI) + 1, step))

    def _x(self, hz: float, w: int) -> float:
        frac = (hz - self.LO) / (self.HI - self.LO)
        return max(0.0, min(1.0, frac)) * w

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_top, bar_h = 16, 22

        zones = [
            (self.LO, CFG.zone_low, QtGui.QColor(94, 129, 172, 160)),
            (CFG.zone_low, CFG.zone_high, QtGui.QColor(180, 142, 173, 160)),
            (CFG.zone_high, self.HI, QtGui.QColor(163, 190, 140, 160)),
        ]
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for lo, hi, col in zones:
            x0, x1 = self._x(lo, w), self._x(hi, w)
            p.setBrush(col)
            p.drawRoundedRect(QtCore.QRectF(x0, bar_top, x1 - x0, bar_h), 3, 3)

        # Streubereich der letzten Sekunden
        if len(self.recent) >= 5:
            arr = np.fromiter(self.recent, dtype=float)
            lo, hi = np.percentile(arr, 10), np.percentile(arr, 90)
            x0, x1 = self._x(lo, w), self._x(hi, w)
            p.setBrush(QtGui.QColor(236, 239, 244, 55))
            p.drawRect(QtCore.QRectF(x0, bar_top, max(2.0, x1 - x0), bar_h))

        # Skala
        p.setPen(QtGui.QColor(NORD["dim"]))
        font = p.font()
        font.setPointSize(8)
        p.setFont(font)
        for hz in self._ticks():
            x = self._x(hz, w)
            p.drawText(QtCore.QRectF(x - 20, bar_top + bar_h + 2, 40, 14),
                       QtCore.Qt.AlignmentFlag.AlignHCenter, str(hz))

        # Zonengrenzen hervorheben
        p.setPen(QtGui.QColor(NORD["fg"]))
        for hz in (CFG.zone_low, CFG.zone_high):
            x = self._x(hz, w)
            p.drawText(QtCore.QRectF(x - 24, 0, 48, 13),
                       QtCore.Qt.AlignmentFlag.AlignHCenter, f"{hz:.0f}")

        # Marker
        if self.f0 is not None:
            x = self._x(self.f0, w)
            p.setPen(QtGui.QPen(QtGui.QColor(NORD["fg"]), 2))
            p.drawLine(QtCore.QPointF(x, bar_top - 6),
                       QtCore.QPointF(x, bar_top + bar_h + 1))
            p.setBrush(QtGui.QColor(NORD["fg"]))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawPolygon(QtGui.QPolygonF([
                QtCore.QPointF(x, bar_top - 2),
                QtCore.QPointF(x - 5, bar_top - 10),
                QtCore.QPointF(x + 5, bar_top - 10),
            ]))
        p.end()


# ------------------------------------------------------------ Hauptfenster

class DetachedWindow(QtWidgets.QWidget):
    """Ein ausgehaengter Reiter als eigenstaendiges Fenster."""

    closed = QtCore.Signal()

    def __init__(self, page: QtWidgets.QWidget, title: str, parent=None):
        super().__init__(parent, QtCore.Qt.WindowType.Window)
        self.setWindowTitle(title)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(page)
        # removeTab() versteckt die Seite. Ohne das hier bleibt das
        # ausgehaengte Fenster leer, obwohl alles darin haengt.
        page.setVisible(True)
        self.resize(1150, 720)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(paths.APP_NAME)
        self.resize(1160, 820)

        self.engine = AudioEngine()
        self.sr = self.engine.samplerate
        self.tick_count = 0

        self.spec_cursor = 0
        self.spec_written = 0
        self.debug_spec = "--debug-spec" in sys.argv
        self.spec = np.full((SPEC_COLS, self._n_bins()), -100.0, dtype=np.float32)
        self.window_fn = np.hanning(NFFT).astype(np.float32)

        self.history: deque[tuple[float, float]] = deque(maxlen=1200)
        self.elapsed = QtCore.QElapsedTimer()
        self.elapsed.start()
        self.f0_smooth: deque[float] = deque(maxlen=3)

        paths.ensure_dirs()
        self.sessions = self._load_sessions()
        self.view = settings.get_view()
        self._rows: list[dict] = []
        self._reordering = False
        self._record_peak = 0.0
        self._action_rows: set[int] = set()
        self._action_column = None
        self._detached: dict[str, tuple] = {}
        self._dialogs: list[QtWidgets.QDialog] = []

        self.ui_language = i18n.LANG
        self._build_ui()
        self._refresh_devices()
        self._fill_session_table()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.setInterval(TICK_MS)

    def _n_bins(self) -> int:
        return int(MAX_FREQ / (self.sr / NFFT)) + 1

    # -- UI-Aufbau -------------------------------------------------------

    def _build_ui(self) -> None:
        # Beim Neuaufbau (etwa Sprachwechsel) zuerst alles zurueckholen,
        # sonst haengen die Fenster an verworfenen Widgets.
        self._reattach_all()

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_live_tab(), i18n.t("tab_live"))
        tabs.addTab(self._build_session_tab(), i18n.t("tab_sessions"))
        tabs.tabBar().setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        tabs.tabBar().customContextMenuRequested.connect(self._tab_menu)
        tabs.tabBarDoubleClicked.connect(self._detach_tab)
        self.tabs = tabs
        self.setCentralWidget(tabs)
        if self.statusBar() is not None:
            self.status = self.statusBar()
            self.status.showMessage(i18n.t("pick_device"))

    def _build_live_tab(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(page)
        root.setContentsMargins(14, 14, 14, 10)
        root.setSpacing(12)

        # Steuerleiste
        bar = QtWidgets.QHBoxLayout()

        self.lang_group = QtWidgets.QWidget()
        lang_lay = QtWidgets.QHBoxLayout(self.lang_group)
        lang_lay.setContentsMargins(0, 0, 0, 0)
        lang_lay.setSpacing(0)
        self.lang_buttons = {}
        for code, text in (("en", "EN"), ("de", "DE")):
            button = QtWidgets.QPushButton(text)
            button.setObjectName("langleft" if code == "en" else "langright")
            button.setCheckable(True)
            button.setChecked(i18n.LANG == code)
            button.setFixedWidth(42)
            button.clicked.connect(lambda _=False, c=code: self._set_language(c))
            self.lang_buttons[code] = button
            lang_lay.addWidget(button)

        self.device_box = QtWidgets.QComboBox()
        self.btn_refresh = QtWidgets.QPushButton()
        self.btn_refresh.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        self.btn_refresh.setToolTip(i18n.t("refresh_tip"))
        self.btn_refresh.setFixedWidth(40)
        self.btn_refresh.clicked.connect(self._refresh_devices)
        self.btn_start = QtWidgets.QPushButton(i18n.t("start"))
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self._toggle_stream)
        self.btn_record = QtWidgets.QPushButton(i18n.t("record"))
        self.btn_record.setObjectName("record")
        self.btn_record.setEnabled(False)
        self.btn_record.clicked.connect(self._toggle_record)
        self.type_box = QtWidgets.QComboBox()
        for kind in rectypes.TYPES:
            self.type_box.addItem(kind.label, kind.key)
            self.type_box.setItemData(self.type_box.count() - 1, kind.hint,
                                      QtCore.Qt.ItemDataRole.ToolTipRole)
        index = self.type_box.findData(settings.get_recording_type())
        self.type_box.setCurrentIndex(max(0, index))
        self.type_box.currentIndexChanged.connect(
            lambda: settings.set_recording_type(self.type_box.currentData()))

        self.profile_box = QtWidgets.QComboBox()
        self._fill_profiles()
        self.profile_box.currentIndexChanged.connect(self._profile_chosen)

        self.btn_guided = QtWidgets.QPushButton(i18n.t("guided"))
        self.btn_guided.setObjectName("guided")
        self.btn_guided.setCheckable(True)
        self.btn_guided.toggled.connect(self._toggle_guided)

        self.btn_settings = QtWidgets.QPushButton("⚙  " + i18n.t("settings"))
        self.btn_settings.clicked.connect(self._open_settings)

        bar.addWidget(self.lang_group)
        bar.addSpacing(14)
        bar.addWidget(QtWidgets.QLabel(i18n.t("microphone")))
        bar.addWidget(self.device_box, 1)
        bar.addWidget(self.btn_refresh)
        bar.addSpacing(10)
        bar.addWidget(self.btn_start)
        bar.addWidget(self.btn_record)
        bar.addSpacing(10)
        bar.addWidget(QtWidgets.QLabel(i18n.t("recording_type")))
        bar.addWidget(self.type_box)
        bar.addSpacing(10)
        bar.addWidget(QtWidgets.QLabel(i18n.t("target_voice")))
        bar.addWidget(self.profile_box)
        bar.addWidget(self.btn_guided)
        bar.addSpacing(10)
        bar.addWidget(self.btn_settings)
        root.addLayout(bar)

        # Kennzahlen
        cards = QtWidgets.QHBoxLayout()
        cards.setSpacing(10)
        self.card_f0 = StatCard(i18n.t("card_f0"), " Hz", NORD["accent"])
        self.card_zone = StatCard(i18n.t("card_zone"), "", NORD["purple"])
        self.card_f1 = StatCard("F1", " Hz", NORD["yellow"])
        self.card_f2 = StatCard("F2", " Hz", NORD["green"])
        self.card_h1h2 = StatCard(i18n.t("m_h1_h2"), " dB", NORD["purple"])
        self.card_level = StatCard(i18n.t("card_level"), " dB", NORD["dim"])
        for c in (self.card_f0, self.card_zone, self.card_f1, self.card_f2,
                  self.card_h1h2, self.card_level):
            cards.addWidget(c)
        root.addLayout(cards)

        self.zone_bar = ZoneBar()
        root.addWidget(self.zone_bar)

        # Spektrogramm
        pg.setConfigOptions(antialias=True)
        self.spec_plot = pg.PlotWidget()
        self.spec_plot.setBackground(NORD["bg2"])
        self.spec_plot.setMouseEnabled(x=False, y=False)
        self.spec_plot.hideButtons()
        self.spec_plot.setLabel("left", i18n.t("frequency"), units="Hz")
        self.spec_plot.getAxis("bottom").setStyle(showValues=False)
        self.spec_plot.setYRange(0, MAX_FREQ, padding=0)
        self.spec_plot.setXRange(0, SPEC_COLS, padding=0)

        self.spec_img = pg.ImageItem()
        try:
            self.spec_img.setColorMap(pg.colormap.get("inferno"))
        except Exception:
            pass
        self.spec_img.setLevels((SPEC_FLOOR_DB, SPEC_CEIL_DB))
        self.spec_plot.addItem(self.spec_img)

        self.line_f1 = pg.InfiniteLine(angle=0, movable=False,
                                       pen=pg.mkPen(NORD["yellow"], width=1,
                                                    style=QtCore.Qt.PenStyle.DashLine))
        self.line_f2 = pg.InfiniteLine(angle=0, movable=False,
                                       pen=pg.mkPen(NORD["green"], width=1,
                                                    style=QtCore.Qt.PenStyle.DashLine))
        for ln in (self.line_f1, self.line_f2):
            ln.setVisible(False)
            self.spec_plot.addItem(ln)

        spec_group = QtWidgets.QGroupBox(i18n.t("spectrogram"))
        sg = QtWidgets.QVBoxLayout(spec_group)
        sg.addWidget(self.spec_plot)
        root.addWidget(spec_group, 3)

        # Pitchverlauf
        self.pitch_plot = pg.PlotWidget()
        self.pitch_plot.setBackground(NORD["bg2"])
        self.pitch_plot.setMouseEnabled(x=False, y=False)
        self.pitch_plot.hideButtons()
        self.pitch_plot.setLabel("left", "F0", units="Hz")
        self.pitch_plot.getAxis("bottom").setStyle(showValues=False)
        self.pitch_plot.setYRange(60, 320, padding=0)
        self.pitch_plot.showGrid(y=True, alpha=0.15)

        self.zone_region = pg.LinearRegionItem(
            values=(CFG.zone_low, CFG.zone_high),
            orientation="horizontal", movable=False,
            brush=pg.mkBrush(180, 142, 173, 45))
        self.zone_region.setZValue(-10)
        self.pitch_plot.addItem(self.zone_region)
        self.pitch_curve = self.pitch_plot.plot(
            pen=pg.mkPen(NORD["accent"], width=2), connect="finite")

        pitch_group = QtWidgets.QGroupBox(i18n.t("history"))
        pgl = QtWidgets.QVBoxLayout(pitch_group)
        pgl.addWidget(self.pitch_plot)
        root.addWidget(pitch_group, 2)

        self.guided_panel = GuidedPanel(self.engine, self.store_recording, page)
        self.guided_panel.setVisible(False)
        self.guided_panel.finished.connect(self._guided_finished)
        root.addWidget(self.guided_panel)

        # Uebungstext
        text_group = QtWidgets.QGroupBox(i18n.t("practice_text"))
        tg = QtWidgets.QVBoxLayout(text_group)
        txt = QtWidgets.QTextEdit(i18n.t("practice_body"))
        txt.setMaximumHeight(78)
        tg.addWidget(txt)
        root.addWidget(text_group)

        return page

    def _build_session_tab(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)

        bar = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel("")
        self.count_label.setStyleSheet(f"color: {NORD['dim']};")
        btn_filter = QtWidgets.QPushButton(i18n.t("filter"))
        btn_filter.clicked.connect(self._open_filter)
        btn_export = QtWidgets.QPushButton(i18n.t("export_list"))
        btn_export.clicked.connect(self._export_list)
        bar.addWidget(self.count_label, 1)
        bar.addWidget(btn_filter)
        bar.addWidget(btn_export)
        lay.addLayout(bar)

        self.table = QtWidgets.QTableWidget(0, 0)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._row_menu)
        self.table.doubleClicked.connect(
            lambda index: self._open_details(self._entry_at(index.row())))

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._header_clicked)
        header.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._header_menu)
        header.setSectionsMovable(True)
        header.sectionMoved.connect(self._section_moved)
        self.table.verticalScrollBar().valueChanged.connect(self._populate_actions)
        lay.addWidget(self.table)

        row = QtWidgets.QHBoxLayout()
        btn_play = QtWidgets.QPushButton(i18n.t("play"))
        btn_play.clicked.connect(self._play_selected)
        btn_stop = QtWidgets.QPushButton(i18n.t("stop"))
        btn_stop.clicked.connect(lambda: sd.stop())
        btn_dir = QtWidgets.QPushButton(i18n.t("open_folder"))
        btn_dir.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(str(SESSION_DIR))))
        row.addWidget(btn_play)
        row.addWidget(btn_stop)
        row.addStretch(1)
        row.addWidget(btn_dir)
        lay.addLayout(row)

        hint = QtWidgets.QLabel(i18n.t("formant_hint"))
        hint.setStyleSheet(f"color: {NORD['dim']};")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        return page

    # -- Ansicht der Liste -----------------------------------------------

    def _visible_columns(self) -> list:
        keys = self.view.get("columns") or columns.DEFAULT_VISIBLE
        chosen = [columns.BY_KEY[k] for k in keys if k in columns.BY_KEY]
        return chosen or [columns.BY_KEY[k] for k in columns.DEFAULT_VISIBLE]

    def _filtered_sessions(self) -> list[dict]:
        entries = list(self.sessions)

        if self.view.get("period_on"):
            start = self.view.get("period_from") or ""
            end = self.view.get("period_to") or ""
            entries = [e for e in entries
                       if (not start or e.get("timestamp", "")[:10] >= start)
                       and (not end or e.get("timestamp", "")[:10] <= end)]

        column = columns.BY_KEY.get(self.view.get("sort", "date"),
                                    columns.BY_KEY["date"])
        descending = bool(self.view.get("descending", True))
        entries.sort(key=lambda e: columns.sort_key(e, column, descending),
                     reverse=descending)
        # Fehlende Werte bleiben unten, auch wenn absteigend sortiert wird.
        present = [e for e in entries if columns.value(e, column) not in (None, "")]
        missing = [e for e in entries if columns.value(e, column) in (None, "")]
        return present + missing

    def _entry_at(self, row: int) -> dict | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def _header_clicked(self, index: int) -> None:
        visible = self._visible_columns()
        if not 0 <= index < len(visible):
            return
        key = visible[index].key
        if self.view.get("sort") == key:
            self.view["descending"] = not self.view.get("descending", True)
        else:
            self.view["sort"] = key
            self.view["descending"] = True
        settings.set_view(self.view)
        self._fill_session_table()

    def _header_menu(self, position) -> None:
        header = self.table.horizontalHeader()
        menu = self.build_header_menu(header.logicalIndexAt(position))
        menu.exec(header.mapToGlobal(position))

    def build_header_menu(self, index: int) -> QtWidgets.QMenu:
        """Rechtsklick auf eine Ueberschrift: ausblenden oder verwalten.

        Aufbau und Anzeige sind getrennt, damit sich der Inhalt ohne
        blockierendes exec() pruefen laesst.
        """
        visible = self._visible_columns()
        clicked = visible[index] if 0 <= index < len(visible) else None

        menu = QtWidgets.QMenu(self)

        if clicked is not None:
            action = menu.addAction(i18n.t("sort_by_this"))
            action.triggered.connect(
                lambda _=False, i=index: self._header_clicked(i))

            left = menu.addAction(i18n.t("move_left"))
            left.setEnabled(index > 0)
            left.triggered.connect(
                lambda _=False, key=clicked.key: self._move_column(key, -1))
            right = menu.addAction(i18n.t("move_right"))
            right.setEnabled(index < len(visible) - 1)
            right.triggered.connect(
                lambda _=False, key=clicked.key: self._move_column(key, 1))
            menu.addSeparator()

            hide = menu.addAction(i18n.t("hide_column", name=clicked.label))
            hide.triggered.connect(
                lambda _=False, key=clicked.key: self._hide_column(key))
            if len(visible) <= 1:
                hide.setEnabled(False)
                hide.setToolTip(i18n.t("last_column"))
            menu.addSeparator()

        keys = {c.key for c in visible}
        submenu = menu.addMenu(i18n.t("columns_menu"))
        for column in columns.COLUMNS:
            entry = submenu.addAction(column.label)
            entry.setCheckable(True)
            entry.setChecked(column.key in keys)
            entry.triggered.connect(
                lambda checked, key=column.key: self._toggle_column(key, checked))

        menu.addSeparator()
        menu.addAction(i18n.t("manage_columns"), self._open_filter)
        return menu

    def _section_moved(self, _logical: int, _old: int, _new: int) -> None:
        """Reihenfolge nach dem Ziehen einer Ueberschrift uebernehmen."""
        if self._reordering:
            return
        header = self.table.horizontalHeader()
        count = self.table.columnCount()
        if count < 2:
            return

        self._reordering = True
        try:
            # Die Aktionsspalte bleibt immer ganz rechts.
            action_visual = header.visualIndex(count - 1)
            if action_visual != count - 1:
                header.moveSection(action_visual, count - 1)

            visible = self._visible_columns()
            order = []
            for visual in range(count - 1):
                logical = header.logicalIndex(visual)
                if 0 <= logical < len(visible):
                    order.append(visible[logical].key)
        finally:
            self._reordering = False

        if order and order != [c.key for c in self._visible_columns()]:
            self._set_columns(order)

    def _move_column(self, key: str, offset: int) -> None:
        keys = [c.key for c in self._visible_columns()]
        if key not in keys:
            return
        index = keys.index(key)
        target = index + offset
        if not 0 <= target < len(keys):
            return
        keys[index], keys[target] = keys[target], keys[index]
        self._set_columns(keys)

    def _set_columns(self, keys: list[str]) -> None:
        if not keys:
            return
        self.view["columns"] = keys
        settings.set_view(self.view)
        self._fill_session_table()

    def _hide_column(self, key: str) -> None:
        keys = [c.key for c in self._visible_columns() if c.key != key]
        self._set_columns(keys)

    def _toggle_column(self, key: str, wanted: bool) -> None:
        keys = [c.key for c in self._visible_columns()]
        if wanted and key not in keys:
            # An der Stelle einfuegen, an der die Spalte laut Definition
            # hingehoert — relativ zu den bereits sichtbaren Nachbarn.
            order = [c.key for c in columns.COLUMNS]
            position = len(keys)
            for i, existing in enumerate(keys):
                if order.index(existing) > order.index(key):
                    position = i
                    break
            keys = keys[:position] + [key] + keys[position:]
        elif not wanted and key in keys:
            if len(keys) <= 1:
                return
            keys.remove(key)
        self._set_columns(keys)

    def _open_filter(self) -> None:
        dialog = FilterDialog(self.view, self)
        dialog.applied.connect(self._apply_view)
        self.open_dialog(dialog)

    def _apply_view(self, view: dict) -> None:
        self.view = view
        settings.set_view(self.view)
        self._fill_session_table()

    def _row_menu(self, position) -> None:
        row = self.table.rowAt(position.y())
        entry = self._entry_at(row)
        if entry is None:
            return
        self.table.selectRow(row)

        menu = QtWidgets.QMenu(self)
        menu.addAction(i18n.t("details"), lambda: self._open_details(entry))
        menu.addAction(i18n.t("play"), lambda: self._play_entry(entry))
        menu.addSeparator()
        submenu = menu.addMenu(i18n.t("change_type"))
        current = entry.get("type")
        for kind in rectypes.TYPES:
            action = submenu.addAction(kind.label)
            action.setCheckable(True)
            action.setChecked(kind.key == rectypes.get(current).key)
            action.triggered.connect(
                lambda _=False, e=entry, k=kind.key: self._set_type(e, k))

        menu.addAction(i18n.t("rename"), lambda: self._rename_session(entry))
        menu.addAction(i18n.t("delete"), lambda: self._delete_session(entry))
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _set_type(self, entry: dict, key: str) -> None:
        if entry.get("type") == key:
            return
        entry["type"] = key
        self._save_sessions()
        self._fill_session_table()

    def _rename_session(self, entry: dict) -> None:
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("rename_title"), i18n.t("rename_prompt"),
            text=columns.display_name(entry))
        if not ok:
            return
        name = name.strip()
        if name:
            entry["label"] = name
        else:
            entry.pop("label", None)      # leer heisst zurueck zum Dateinamen
        self._save_sessions()
        self._fill_session_table()

    def _fill_session_table(self) -> None:
        visible = self._visible_columns()
        self._rows = self._filtered_sessions()

        # setColumnCount raeumt vorhandene Cell-Widgets nicht ab. Ohne das
        # Leeren blieben die Aktionsknoepfe in der Spalte stehen, in der die
        # Aktionsspalte vor einer Aenderung der Auswahl lag.
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setColumnCount(len(visible) + 1)
        sort_key = self.view.get("sort")
        arrow = " ▼" if self.view.get("descending", True) else " ▲"
        self.table.setHorizontalHeaderLabels(
            [c.label + (arrow if c.key == sort_key else "") for c in visible] + [""])
        self.table.setRowCount(len(self._rows))

        for r, entry in enumerate(self._rows):
            no_signal = entry.get("quality", "ok") == "kein_signal"
            peak = entry.get("peak_db")
            quiet = isinstance(peak, (int, float)) and peak < columns.QUIET_DB

            for c, column in enumerate(visible):
                item = QtWidgets.QTableWidgetItem(columns.text(entry, column))
                if no_signal:
                    item.setForeground(QtGui.QColor(NORD["dim"]))
                elif quiet and column.key == "peak_db":
                    item.setForeground(QtGui.QColor(NORD["yellow"]))
                self.table.setItem(r, c, item)

        # Die Aktionsknoepfe entstehen erst, wenn eine Zeile sichtbar wird.
        # Sie im Voraus fuer alle Zeilen zu bauen kostete bei 500 Sessions
        # eine knappe halbe Sekunde.
        self._action_rows.clear()
        self._action_column = len(visible)
        self.table.resizeColumnsToContents()
        self._populate_actions()
        self._fit_action_column()
        self.count_label.setText(i18n.t("shown_count", shown=len(self._rows),
                                        total=len(self.sessions)))

    def _populate_actions(self) -> None:
        """Knoepfe fuer den sichtbaren Ausschnitt nachziehen."""
        column = self._action_column
        if column is None or not self._rows:
            return

        first = self.table.rowAt(0)
        last = self.table.rowAt(self.table.viewport().height() - 1)
        first = 0 if first < 0 else first
        last = self.table.rowCount() - 1 if last < 0 else last
        first = max(0, first - 4)
        last = min(self.table.rowCount() - 1, last + 4)

        for row in range(first, last + 1):
            if row in self._action_rows:
                continue
            entry = self._entry_at(row)
            if entry is None:
                continue
            self.table.setCellWidget(row, column, self._row_actions(entry))
            self._action_rows.add(row)

    def _fit_action_column(self) -> None:
        last = self.table.columnCount() - 1
        widest = 0
        for row in self._action_rows:
            widget = self.table.cellWidget(row, last)
            if widget is not None:
                widest = max(widest, widget.sizeHint().width())
        self.table.setColumnWidth(last, max(widest + 12, 190))

    def _row_actions(self, entry: dict) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        details = QtWidgets.QPushButton(i18n.t("details"))
        details.setObjectName("rowaction")
        details.clicked.connect(lambda _=False, e=entry: self._open_details(e))

        remove = QtWidgets.QPushButton(i18n.t("delete"))
        remove.setObjectName("danger")
        remove.clicked.connect(lambda _=False, e=entry: self._delete_session(e))

        # Keine feste Breite: sonst schneidet Qt bei längeren Beschriftungen ab.
        for button in (details, remove):
            button.setMinimumWidth(button.sizeHint().width())
        lay.addWidget(details)
        lay.addWidget(remove)
        lay.addStretch(1)
        return box

    def _open_details(self, entry) -> None:
        if entry is None:
            return
        # Alte Eintraege kennen die neueren Kennwerte noch nicht.
        if "hnr" not in entry and entry.get("quality", "ok") == "ok":
            path = SESSION_DIR / entry.get("file", "")
            if path.exists():
                self.status.showMessage(i18n.t("recalculating"))
                QtWidgets.QApplication.processEvents()
                try:
                    entry.update(analysis.analyse_file(path))
                    self._save_sessions()
                    self._fill_session_table()
                except Exception as exc:
                    debuglog.record_exception("main.open_details", exc)
                self.status.clearMessage()

        dialog = SessionDetailDialog(entry, list(self._rows), SESSION_DIR, self)
        dialog.changed.connect(self._session_changed)
        self.open_dialog(dialog)

    def _session_changed(self) -> None:
        self._save_sessions()
        self._fill_session_table()

    def _delete_session(self, entry: dict) -> None:
        name = entry.get("file", "")
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("delete_title"), i18n.t("delete_question", name=name),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        path = SESSION_DIR / name
        try:
            if name and path.exists():
                path.unlink()
        except OSError as exc:
            debuglog.record_exception("main.delete_session", exc)
            QtWidgets.QMessageBox.warning(self, i18n.t("delete"), str(exc))
            return

        if entry in self.sessions:
            self.sessions.remove(entry)

        # Dialoge sind nicht-modal und koennten den geloeschten Eintrag
        # noch anzeigen.
        for dialog in list(self._dialogs):
            if getattr(dialog, "entry", None) is entry:
                dialog.close()

        self._save_sessions()
        self._fill_session_table()
        self.status.showMessage(i18n.t("deleted", name=name))

    # -- Listenexport ------------------------------------------------------

    def _list_report(self) -> str:
        visible = self._visible_columns()
        head = [c.label for c in visible]
        table = [[columns.text(e, c) for c in visible] for e in self._rows]
        widths = [max(len(head[i]), *(len(row[i]) for row in table)) if table
                  else len(head[i]) for i in range(len(head))]

        out = [i18n.t("report_list_title"),
               "=" * len(i18n.t("report_list_title")),
               f"{i18n.t('report_generated')}: "
               f"{datetime.now().isoformat(timespec='seconds')}",
               i18n.t("shown_count", shown=len(self._rows),
                      total=len(self.sessions))]
        if self.view.get("period_on"):
            out.append(f"{i18n.t('filter_period')}: "
                       f"{self.view.get('period_from')} – {self.view.get('period_to')}")
        out += ["", "  ".join(h.ljust(widths[i]) for i, h in enumerate(head)).rstrip(),
                "  ".join("-" * w for w in widths)]
        for row in table:
            out.append("  ".join(v.ljust(widths[i])
                                 for i, v in enumerate(row)).rstrip())
        return "\n".join(out) + "\n"

    def _list_csv(self) -> str:
        visible = self._visible_columns()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([c.key for c in visible])
        for entry in self._rows:
            row = []
            for column in visible:
                raw = columns.value(entry, column)
                row.append("" if raw is None else
                           (f"{raw:.4f}" if isinstance(raw, float) else str(raw)))
            writer.writerow(row)
        return buffer.getvalue()

    def _export_list(self) -> None:
        language = ask_export_language(self)
        if language is None:
            return
        suggestion = str(SESSION_DIR / "sessions.txt")
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(
            self, i18n.t("export_list_title"), suggestion, i18n.t("export_filter"))
        if not path:
            return
        if not Path(path).suffix:
            path += ".csv" if "csv" in (chosen or "").lower() else ".txt"

        try:
            with export_language(language):
                text = (self._list_csv() if path.lower().endswith(".csv")
                        else self._list_report())
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            debuglog.record_exception("main.export_list", exc)
            QtWidgets.QMessageBox.warning(self, i18n.t("export_failed"), str(exc))
            return
        QtWidgets.QMessageBox.information(
            self, i18n.t("export_list_title"), i18n.t("exported", path=path))

    def _play_entry(self, entry: dict) -> None:
        path = SESSION_DIR / entry.get("file", "")
        if not path.exists():
            self.status.showMessage(i18n.t("file_missing"))
            return
        try:
            data, rate = audio_mod.read_wav(path)
            sd.play(data, rate)
        except Exception as exc:
            debuglog.record_exception("main.play", exc)
            self.status.showMessage(str(exc))

    def _play_selected(self) -> None:
        entry = self._entry_at(self.table.currentRow())
        if entry is not None:
            self._play_entry(entry)

    # -- Dialoge ----------------------------------------------------------

    def open_dialog(self, dialog: QtWidgets.QDialog) -> QtWidgets.QDialog:
        """Dialog nicht-modal oeffnen und mitfuehren.

        Mit exec() waere der Dialog anwendungsmodal. Qt verwirft die
        Schliessanfrage des Fenstermanagers an ein blockiertes Fenster, bevor
        sie im Programm ankommt — "Schliessen" aus der Taskleiste bliebe also
        wirkungslos, solange ein Dialog offen ist.
        """
        dialog.setModal(False)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self._dialogs.append(dialog)
        dialog.destroyed.connect(
            lambda _=None, d=dialog: self._forget_dialog(d))
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def _forget_dialog(self, dialog) -> None:
        try:
            self._dialogs.remove(dialog)
        except ValueError:
            pass

    def _close_dialogs(self) -> None:
        for dialog in list(self._dialogs):
            try:
                dialog.close()
            except RuntimeError:      # bereits abgeraeumt
                pass
        self._dialogs.clear()

    # -- Reiter aus- und einhaengen ---------------------------------------

    def _tab_menu(self, position) -> None:
        index = self.tabs.tabBar().tabAt(position)
        menu = QtWidgets.QMenu(self)

        if index >= 0:
            action = menu.addAction(i18n.t("detach_tab"))
            action.triggered.connect(lambda _=False, i=index: self._detach_tab(i))
            # Der letzte verbliebene Reiter bleibt, sonst waere das Fenster leer.
            action.setEnabled(self.tabs.count() > 1)

        for name in list(self._detached):
            entry = menu.addAction(f"{i18n.t('reattach_tab')}: {name}")
            entry.triggered.connect(lambda _=False, n=name: self._reattach(n))

        if menu.actions():
            menu.exec(self.tabs.tabBar().mapToGlobal(position))

    def _detach_tab(self, index: int) -> None:
        if index < 0 or self.tabs.count() <= 1:
            return
        page = self.tabs.widget(index)
        title = self.tabs.tabText(index)
        self.tabs.removeTab(index)

        window = DetachedWindow(
            page, i18n.t("detached_title", name=title, app=paths.APP_NAME), self)
        icon = paths.icon_file()
        if icon is not None:
            window.setWindowIcon(QtGui.QIcon(str(icon)))
        window.closed.connect(lambda n=title: self._reattach(n))
        self._detached[title] = (window, page, index)
        window.show()

    def _reattach(self, title: str) -> None:
        entry = self._detached.pop(title, None)
        if entry is None:
            return
        window, page, index = entry
        page.setParent(None)
        self.tabs.insertTab(min(index, self.tabs.count()), page, title)
        window.closed.disconnect()
        window.close()
        window.deleteLater()

    def _reattach_all(self) -> None:
        for title in list(self._detached):
            self._reattach(title)

    # -- Sprache ----------------------------------------------------------

    def _set_language(self, code: str) -> None:
        for key, button in self.lang_buttons.items():
            button.setChecked(key == code)
        # Gegen die Sprache pruefen, in der die Oberflaeche gebaut wurde, nicht
        # gegen die globale — sonst bleibt ein Wechsel wirkungslos, wenn beide
        # auseinanderlaufen.
        if code == self.ui_language:
            return

        was_running = self.engine.running
        was_recording = self.engine.is_recording
        i18n.set_language(code)
        settings.set_language(code)

        # Der Audiostrom lebt unabhaengig vom UI, deshalb laesst sich die
        # Oberflaeche gefahrlos neu aufbauen.
        self._build_ui()
        self.ui_language = code
        self._refresh_devices()
        self._fill_session_table()
        self.spec_img.setImage(self.spec, autoLevels=False,
                               levels=(SPEC_FLOOR_DB, SPEC_CEIL_DB))
        self.spec_img.setRect(QtCore.QRectF(0, 0, SPEC_COLS, MAX_FREQ))
        if was_running:
            self.btn_start.setText(i18n.t("stop"))
            self.btn_record.setEnabled(True)
            self.status.showMessage(i18n.t("running", rate=self.sr))
        if was_recording:
            self.btn_record.setText(i18n.t("stop"))

    # -- Einstellungen ----------------------------------------------------

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.applied.connect(self._apply_settings)
        self.open_dialog(dialog)

    def _apply_settings(self) -> None:
        self._fill_profiles()
        self.zone_region.setRegion((CFG.zone_low, CFG.zone_high))
        lo = min(60.0, CFG.pitch_floor)
        hi = min(CFG.pitch_ceiling, max(320.0, CFG.zone_high + 120.0))
        self.pitch_plot.setYRange(lo, hi, padding=0)
        self.zone_bar.update()
        self.f0_smooth.clear()
        name = settings.active_template()
        self.status.showMessage(i18n.t("settings_applied", name=name))

    # -- Geraete / Stream -------------------------------------------------

    def _refresh_devices(self) -> None:
        remembered = settings.get_device()
        model = QtGui.QStandardItemModel()

        def add_header(text: str) -> None:
            item = QtGui.QStandardItem(text)
            item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
            item.setForeground(QtGui.QColor(NORD["dim"]))
            font = item.font()
            font.setPointSize(max(8, font.pointSize() - 1))
            item.setFont(font)
            model.appendRow(item)

        def add_entry(label: str, index, key: str, enabled: bool = True) -> None:
            item = QtGui.QStandardItem(label)
            item.setData(index, QtCore.Qt.ItemDataRole.UserRole)
            item.setData(key, KEY_ROLE)
            if not enabled:
                item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)
                item.setForeground(QtGui.QColor(NORD["dim"]))
            model.appendRow(item)

        add_entry(i18n.t("system_default"), None, DEFAULT_KEY)
        for title, items in audio_mod.grouped_sources(remembered):
            add_header(title)
            for src in items:
                label = ("●  " if src.is_default else "     ") + src.label
                if not src.available:
                    label += "   " + i18n.t("not_available")
                add_entry(label, src, src.name, src.available)

        self.device_box.setModel(model)
        target = 0
        if remembered:
            for row in range(model.rowCount()):
                if model.item(row).data(KEY_ROLE) == remembered:
                    target = row
                    break
        self.device_box.setCurrentIndex(target)

    def _current_device_key(self):
        model = self.device_box.model()
        idx = self.device_box.currentIndex()
        if idx < 0 or idx >= model.rowCount():
            return None
        return model.item(idx).data(KEY_ROLE)

    def _toggle_stream(self) -> None:
        if self.engine.running:
            if self.engine.is_recording:
                self._toggle_record()
            self.engine.stop()
            self.timer.stop()
            self.btn_start.setText(i18n.t("start"))
            self.btn_record.setEnabled(False)
            self.status.showMessage(i18n.t("stopped"))
            return

        model = self.device_box.model()
        item = model.item(self.device_box.currentIndex())
        if item is not None and not (item.flags() & QtCore.Qt.ItemFlag.ItemIsEnabled):
            QtWidgets.QMessageBox.information(
                self, i18n.t("microphone"), i18n.t("source_unavailable"))
            return

        if not self.engine.start(self.device_box.currentData()):
            QtWidgets.QMessageBox.critical(
                self, i18n.t("microphone"),
                i18n.t("mic_open_failed") + f"\n\n{self.engine.last_error}")
            return

        self.spec_cursor = self.engine.total_samples
        self.spec[:] = -100.0
        self.history.clear()
        self.elapsed.restart()
        self.timer.start()
        self.btn_start.setText(i18n.t("stop"))
        self.btn_record.setEnabled(True)
        settings.set_device(self._current_device_key())
        self.status.showMessage(i18n.t("running", rate=self.sr))

    # -- Haupttakt --------------------------------------------------------

    def _tick(self) -> None:
        if not self.engine.running:
            return
        self.engine.pump()
        self._update_spectrogram()

        self.tick_count += 1
        if self.tick_count % ANALYSIS_EVERY == 0:
            self._update_analysis()

        if self.engine.is_recording:
            self.btn_record.setText(
                f"{i18n.t('stop')}  ·  {self.engine.recorded_seconds():.0f} s")
            self._watch_level()

        if self.debug_spec and self.tick_count % 20 == 0:
            spread = float(self.spec.max() - self.spec.min())
            self.status.showMessage(
                "Spektrogramm: %.1f … %.1f dB  ·  Spannweite %.1f dB  ·  "
                "Spalten geschrieben: %d"
                % (self.spec.min(), self.spec.max(), spread, self.spec_written))

    def _update_spectrogram(self) -> None:
        n_bins = self.spec.shape[1]
        cols = []
        guard = 0
        while self.spec_cursor + NFFT <= self.engine.total_samples and guard < 12:
            chunk = self.engine.slice_abs(self.spec_cursor, NFFT)
            if chunk is None:
                # Puffer ueberholt, neu aufsetzen
                self.spec_cursor = max(self.engine.buffer_start,
                                       self.engine.total_samples - NFFT)
                break
            spectrum = np.fft.rfft(chunk * self.window_fn)
            mag = np.abs(spectrum[:n_bins]) / (NFFT / 2)
            cols.append(20.0 * np.log10(np.maximum(mag, 1e-6)))
            self.spec_cursor += HOP
            guard += 1

        if cols:
            block = np.asarray(cols, dtype=np.float32)
            k = block.shape[0]
            if k >= SPEC_COLS:
                self.spec[:] = block[-SPEC_COLS:]
            else:
                self.spec[:-k] = self.spec[k:]
                self.spec[-k:] = block
            self.spec_written += k
            self.spec_img.setImage(self.spec, autoLevels=False,
                                   levels=(SPEC_FLOOR_DB, SPEC_CEIL_DB))
            # Muss NACH setImage kommen: ohne vorhandenes Bild kann pyqtgraph
            # die Skalierung nicht bilden und streckt die Grafik ins Nichts.
            self.spec_img.setRect(QtCore.QRectF(0, 0, SPEC_COLS, MAX_FREQ))

    def _update_analysis(self) -> None:
        samples = self.engine.latest(WINDOW_SECONDS)
        result = analysis.analyse_window(samples, self.sr)

        level = result["rms"]
        self.card_level.set(f"{20 * np.log10(max(level, 1e-6)):.0f}"
                            if level > 0 else "--")
        # Signal da, aber unter der Schwelle -> Pegel oder Schwellwert stimmt nicht.
        too_quiet = 1e-5 < level < CFG.silence_rms
        self.card_level.set_color(NORD["red"] if too_quiet else None)

        t = self.elapsed.elapsed() / 1000.0
        f0 = result["f0"]

        if f0 is not None:
            self.f0_smooth.append(f0)
            shown = float(np.median(self.f0_smooth))
            self.card_f0.set(f"{shown:.0f}")
            self.card_zone.set(analysis.zone_label(shown))
            self.zone_bar.update_value(shown)
            self.history.append((t, shown))
        else:
            self.f0_smooth.clear()
            self.card_f0.set("--")
            self.card_zone.set("--")
            self.zone_bar.update_value(None)
            self.history.append((t, float("nan")))

        f1, f2 = result["f1"], result["f2"]
        self.card_f1.set(f"{f1:.0f}" if f1 else "--")
        self.card_f2.set(f"{f2:.0f}" if f2 else "--")
        weight = result["h1_h2"]
        self.card_h1h2.set(f"{weight:.1f}" if weight is not None else "--")

        profile = settings.get_live_profile()
        self._mark(self.card_f0, "f0_median", self.f0_smooth and shown or None,
                   profile)
        self._mark(self.card_f1, "f1_median", f1, profile)
        self._mark(self.card_f2, "f2_median", f2, profile)
        self._mark(self.card_h1h2, "h1_h2", weight, profile)
        self.line_f1.setVisible(bool(f1))
        self.line_f2.setVisible(bool(f2))
        if f1:
            self.line_f1.setPos(f1)
        if f2:
            self.line_f2.setPos(f2)

        cutoff = t - HISTORY_SECONDS
        pts = [(tt, ff) for tt, ff in self.history if tt >= cutoff]
        if len(pts) >= 2:
            xs = np.array([p[0] for p in pts])
            ys = np.array([p[1] for p in pts])
            self.pitch_curve.setData(xs, ys)
            self.pitch_plot.setXRange(cutoff, t, padding=0)

    # -- Aufnahme ---------------------------------------------------------

    def _fill_profiles(self, select: str | None = None) -> None:
        """Zielauswahl neu aufbauen; eigene Profile koennen dazugekommen sein."""
        blocked = self.profile_box.blockSignals(True)
        self.profile_box.clear()
        for key in targets.profile_keys():
            self.profile_box.addItem(targets.profile_label(key), key)
        index = self.profile_box.findData(select or settings.get_live_profile())
        self.profile_box.setCurrentIndex(max(0, index))
        self.profile_box.blockSignals(blocked)

    def _profile_chosen(self) -> None:
        key = self.profile_box.currentData()
        if key:
            settings.set_live_profile(key)

    def _mark(self, card: StatCard, key: str, value, profile: str) -> None:
        """Kachel einfaerben, sobald ein Zielbereich hinterlegt ist."""
        inside = targets.is_within(value, targets.range_for(key, profile))
        if inside is None:
            card.set_color()
        else:
            card.set_color(NORD["green"] if inside else NORD["yellow"])

    def _toggle_record(self) -> None:
        if not self.engine.is_recording:
            self._record_peak = 0.0
            self.engine.start_recording()
            self.btn_record.setText(i18n.t("stop"))
            self.status.showMessage(i18n.t("recording"))
            return

        samples = self.engine.stop_recording()
        self.btn_record.setText(i18n.t("record"))
        if samples.size < int(0.5 * self.sr):
            self.status.showMessage(i18n.t("too_short"))
            return

        self.status.showMessage(i18n.t("analysing"))
        QtWidgets.QApplication.processEvents()
        entry = self.store_recording(samples, self.type_box.currentData())

        stats = entry
        name = entry["file"]
        pct = stats["voiced_ratio"] * 100.0
        if stats["quality"] == "kein_signal":
            self.status.showMessage(i18n.t("saved_nosignal", name=name, pct=pct))
        elif stats["f0_median"]:
            self.status.showMessage(
                i18n.t("saved_ok", name=name, f0=stats["f0_median"], pct=pct))
        else:
            self.status.showMessage(i18n.t("saved_plain", name=name))

    def _watch_level(self) -> None:
        """Waehrend der Aufnahme auf zu leises Signal hinweisen.

        Eine Pruefung beim Druck auf Aufnahme waere sinnlos: da ist
        naturgemaess Stille, weil noch niemand gesprochen hat.
        """
        seconds = self.engine.recorded_seconds()
        level = analysis.rms(self.engine.latest(1.0))
        self._record_peak = max(self._record_peak, level)

        if seconds < 3.0 or not settings.get_warn_low_level():
            return
        if self._record_peak <= 0.0:
            return
        decibel = 20.0 * np.log10(self._record_peak)
        if decibel < LOW_LEVEL_DB:
            self.status.showMessage(i18n.t("level_live_warning", level=decibel))

    def store_recording(self, samples: np.ndarray, type_key: str,
                        span: tuple[float, float] | None = None) -> dict:
        """WAV schreiben, auswerten und in die Historie aufnehmen."""
        stamp = datetime.now()
        name = stamp.strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
        path = SESSION_DIR / name
        write_wav(path, samples, self.sr)

        # Die vollstaendige Auswertung braucht rund 0,13 s je Sekunde Audio
        # und laeuft im UI-Thread. Wenigstens sichtbar machen, dass gerechnet
        # wird, statt das Fenster stumm einfrieren zu lassen.
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            stats = analysis.analyse_recording(samples, self.sr)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        entry = {"timestamp": stamp.isoformat(timespec="seconds"),
                 "file": name, "type": type_key, **stats}
        if span is not None:
            entry["selection"] = [round(span[0], 3), round(span[1], 3)]

        self.sessions.append(entry)
        self._save_sessions()
        self._fill_session_table()
        return entry

    def _toggle_guided(self, active: bool) -> None:
        """Standardmaessig aus. Eingeschaltet erscheint eine Leiste im
        Live-Reiter statt eines Fensters vor der Nase."""
        if not active:
            self.guided_panel.stop()
            self.guided_panel.setVisible(False)
            self.status.clearMessage()
            return

        if not self.engine.running:
            QtWidgets.QMessageBox.information(
                self, i18n.t("guided_title"), i18n.t("guided_needs_stream"))
            self.btn_guided.setChecked(False)
            return
        if self.engine.is_recording:
            self._toggle_record()

        self.guided_panel.reset()
        self.guided_panel.setVisible(True)

    def _guided_finished(self) -> None:
        # Die Leiste bleibt mit dem Ergebnis stehen, bis abgeschaltet wird.
        self.btn_record.setEnabled(True)

    def _load_sessions(self) -> list[dict]:
        if not SESSION_INDEX.exists():
            return []
        try:
            return json.loads(SESSION_INDEX.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_sessions(self) -> None:
        tmp = SESSION_INDEX.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.sessions, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(SESSION_INDEX)

    def closeEvent(self, event):
        self._close_dialogs()
        self._reattach_all()
        self.timer.stop()
        self.engine.stop()
        try:
            sd.stop()
        except Exception:
            pass
        super().closeEvent(event)


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
    app.setStyleSheet(STYLESHEET)
    debuglog.install()
    paths.ensure_dirs()
    moved = paths.migrate_from(APP_DIR)
    settings.load()
    i18n.set_language(settings.get_language())
    if not paths.CONFIG_PATH.exists():
        settings.save()      # beim ersten Start eine Datei anlegen
    win = MainWindow()
    if moved:
        win.status.showMessage(
            f"{len(moved)} file(s) moved to {paths.CONFIG_DIR}")
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
