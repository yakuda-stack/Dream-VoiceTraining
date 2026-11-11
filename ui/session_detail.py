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

"""Detailfenster einer Aufnahme: Kennzahlen, Verlauf, Spektrogramm, Bereichsauswahl."""

from __future__ import annotations

import csv
import io
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import sounddevice as sd
from PySide6 import QtCore, QtGui, QtWidgets

from voice import analysis
from voice import audio as audio_mod
from core import i18n
from core import rectypes
from core import settings
from core import storage
from voice import targets
from ui.theming import COLORS as NORD

from ui.dialog_common import (add_formant_guides, ask_export_language,
                              export_language, metric_value)


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
        self._duration = 0.0
        self._spectrogram_done = False
        self.wave_curve = None
        self._spec_levels = None
        self._spec_auto_levels = None
        self._guides: list = []
        self._spec_span = None
        self._syncing = False
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
        self.selection_note.setStyleSheet(f"color: {NORD['yellow']}; font-size: 11px;")
        self.selection_note.setVisible(False)
        root.addWidget(self.selection_note)

        self.btn_advanced = QtWidgets.QToolButton()
        self.btn_advanced.setText("▸  " + i18n.t("advanced"))
        self.btn_advanced.setAutoRaise(True)
        self.btn_advanced.setCheckable(True)
        self.btn_advanced.setStyleSheet(
            f"QToolButton {{ color: {NORD['accent']}; font-weight: 600;"
            " border: none; }")
        self.btn_advanced.toggled.connect(self._toggle_advanced)
        root.addWidget(self.btn_advanced, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.advanced = self._build_advanced()
        self.advanced.setVisible(False)
        root.addWidget(self.advanced)

        for key in ("targets_note", "vowel_only_note"):
            note = QtWidgets.QLabel(i18n.t(key))
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
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
            warn.setStyleSheet(f"color: {NORD['yellow']};")
            warn.setWordWrap(True)
            lay.addWidget(warn)
        floor = self.entry.get("pitch_floor")
        ceiling = self.entry.get("pitch_ceiling")
        if floor and ceiling:
            meta = QtWidgets.QLabel(i18n.t(
                "measured_with", floor=floor, ceiling=ceiling,
                formant=self.entry.get("formant_ceiling", 0.0)))
            meta.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
            lay.addWidget(meta)
        return box

    def _build_selectors(self) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)

        self.type_box = QtWidgets.QComboBox()
        for kind in rectypes.all_types():
            self.type_box.addItem(kind.label, kind.key)
        stored = self.entry.get("type")
        if stored and not rectypes.exists(stored):
            # Der Typ wurde geloescht. Ihn trotzdem anzubieten ist besser,
            # als die Aufnahme beim naechsten Speichern stumm zum Lesetext
            # zu machen.
            self.type_box.addItem(rectypes.label(stored), stored)
        index = self.type_box.findData(stored or rectypes.DEFAULT)
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
                        NORD["green"] if inside else NORD["yellow"]))
                if c == 6 and text not in ("—", ""):
                    item.setForeground(QtGui.QColor(NORD["accent"]))
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
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        lay.addWidget(hint)

        self.wave_plot = pg.PlotWidget()
        self.wave_plot.setBackground(NORD["bg2"])
        self.wave_plot.setMinimumHeight(140)
        self.wave_plot.setMenuEnabled(False)
        self.wave_plot.hideButtons()
        # Die Sekundenachse steht unter dem Spektrogramm, nicht zweimal.
        self.wave_plot.getAxis("bottom").setStyle(showValues=False)
        self.wave_plot.getAxis("left").setStyle(showValues=False)
        self.wave_plot.setMouseEnabled(x=True, y=False)
        # Feste Streckungsfaktoren fuer beide Diagramme. Ohne sie teilt Qt
        # den Platz nach Groessenhinweisen auf, und der faellt nach einem
        # Aus- und Wiedereinschalten anders aus als vorher — das
        # Spektrogramm kam in einer anderen Hoehe zurueck, als es ging.
        lay.addWidget(self.wave_plot, 2)

        accent = QtGui.QColor(NORD["accent"])
        self.region = pg.LinearRegionItem(
            brush=pg.mkBrush(accent.red(), accent.green(), accent.blue(), 50),
            hoverBrush=pg.mkBrush(accent.red(), accent.green(), accent.blue(), 80))
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self._region_moved)

        lay.addWidget(self._build_spectrogram(), 3)

        info = QtWidgets.QHBoxLayout()
        self.range_label = QtWidgets.QLabel("")
        self.range_label.setStyleSheet(f"color: {NORD['fg']};")
        self.chk_spec = QtWidgets.QCheckBox(i18n.t("adv_spectrogram"))
        self.chk_spec.setChecked(True)
        self.chk_spec.setToolTip(i18n.t("adv_spectrogram_hint"))
        self.chk_spec.toggled.connect(self._toggle_spectrogram)
        # Der Schalter merkt sich seinen Zustand ueber Fenster hinweg: wer
        # zwei Aufnahmen vergleicht, oeffnet zwei Detailfenster und muesste
        # sonst in jedem einzeln umlegen — und genau dann faellt es auf,
        # wenn eines davon vergessen wurde.
        self.chk_fixed_scale = QtWidgets.QCheckBox(i18n.t("adv_fixed_scale"))
        self.chk_fixed_scale.setChecked(settings.get_fixed_spec_scale())
        self.chk_fixed_scale.setToolTip(i18n.t("adv_fixed_scale_hint"))
        self.chk_fixed_scale.toggled.connect(self._toggle_fixed_scale)
        info.addWidget(self.range_label, 1)
        info.addWidget(self.chk_fixed_scale)
        info.addWidget(self.chk_spec)
        lay.addLayout(info)

        row = QtWidgets.QHBoxLayout()
        self.btn_sel_analyse = QtWidgets.QPushButton(i18n.t("analyse_selection"))
        self.btn_sel_analyse.setObjectName("primary")
        self.btn_sel_analyse.clicked.connect(self._analyse_selection)
        btn_sel_play = QtWidgets.QPushButton(i18n.t("play_selection"))
        btn_sel_play.clicked.connect(self._play_selection)
        # Bis die Wellenform geladen ist, gibt es keine Aufnahme, auf die
        # sich "ganz" beziehen koennte. Fehlt die Datei, bleibt der Knopf
        # gesperrt — das ist ehrlicher als ein Druck, der nichts bewirkt.
        self.btn_full = QtWidgets.QPushButton(i18n.t("full_recording"))
        self.btn_full.setEnabled(False)
        self.btn_full.clicked.connect(self._show_full)
        self.btn_sel_save = QtWidgets.QPushButton(i18n.t("save_selection"))
        self.btn_sel_save.setEnabled(False)
        self.btn_sel_save.clicked.connect(self._save_selection)
        for widget in (self.btn_sel_analyse, btn_sel_play, self.btn_full):
            row.addWidget(widget)
        row.addStretch(1)
        row.addWidget(self.btn_sel_save)
        lay.addLayout(row)
        return box

    def _build_spectrogram(self) -> QtWidgets.QWidget:
        """Das Spektrogramm unter der Wellenform, auf derselben Zeitachse.

        Nicht daneben: beide zeigen denselben Zeitraum, und untereinander
        liegt jeder Augenblick in beiden an derselben Stelle. Die
        Sekundenachse steht deshalb nur einmal, hier unten.
        """
        self.spec_plot = pg.PlotWidget()
        self.spec_plot.setBackground(NORD["bg2"])
        self.spec_plot.setMinimumHeight(150)
        self.spec_plot.setMenuEnabled(False)
        self.spec_plot.hideButtons()
        self.spec_plot.setLabel("bottom", i18n.t("seconds"))
        self.spec_plot.setLabel("left", i18n.t("frequency"), units="Hz")
        self.spec_plot.setMouseEnabled(x=True, y=False)
        self.spec_plot.setXLink(self.wave_plot)

        self.spec_img = pg.ImageItem()
        try:
            self.spec_img.setColorMap(pg.colormap.get("inferno"))
        except Exception:
            pass
        # ignoreBounds: das Bild soll den sichtbaren Bereich nicht
        # mitbestimmen. Sonst zoege ein neu gesetztes Bild die Achse nach,
        # die Achse loeste das naechste Neuzeichnen aus, und so fort.
        self.spec_plot.addItem(self.spec_img, ignoreBounds=True)

        # Beim Zoomen neu rechnen, aber nicht bei jedem Rad-Klick einzeln.
        self._spec_timer = QtCore.QTimer(self)
        self._spec_timer.setSingleShot(True)
        self._spec_timer.setInterval(120)
        self._spec_timer.timeout.connect(self._render_zoom)
        self.spec_plot.getPlotItem().vb.sigXRangeChanged.connect(
            lambda *_: self._spec_timer.start())

        # Dieselbe Auswahl noch einmal. Sie laesst sich auch hier ziehen —
        # wer eine Stelle an den Formanten erkennt, will sie nicht erst in
        # der Wellenform darueber suchen muessen.
        accent = QtGui.QColor(NORD["accent"])
        self.spec_region = pg.LinearRegionItem(
            brush=pg.mkBrush(accent.red(), accent.green(), accent.blue(), 55),
            hoverBrush=pg.mkBrush(accent.red(), accent.green(), accent.blue(), 85))
        self.spec_region.setZValue(10)
        self.spec_region.sigRegionChanged.connect(self._spec_region_moved)
        return self.spec_plot

    def _mirror(self, source, target) -> None:
        """Auswahl von einem Diagramm ins andere uebernehmen.

        Die Sperre verhindert, dass die beiden sich gegenseitig immer
        weiter anstossen: setRegion meldet sofort zurueck.
        """
        if self._syncing:
            return
        self._syncing = True
        try:
            target.setRegion(source.getRegion())
        finally:
            self._syncing = False

    def _spec_region_moved(self) -> None:
        self._mirror(self.spec_region, self.region)

    def _levels(self) -> tuple[float, float]:
        """Die Grenzen, mit denen das Bild gerade eingefaerbt wird.

        Bei fester Skala dieselben Werte wie im Livebereich, damit zwei
        Detailfenster nebeneinander dieselbe Helligkeit fuer denselben
        Pegel zeigen. Sonst die einmal ueber die Aufnahme gerechnete
        Aussteuerung.
        """
        if settings.get_fixed_spec_scale():
            return (audio_mod.SPEC_FLOOR_DB, audio_mod.SPEC_CEIL_DB)
        return self._spec_auto_levels or (audio_mod.SPEC_FLOOR_DB,
                                          audio_mod.SPEC_CEIL_DB)

    def _toggle_fixed_scale(self, on: bool) -> None:
        settings.set_fixed_spec_scale(on)
        if not self._spectrogram_done:
            return
        self._spec_levels = self._levels()
        # Nur einfaerben, nicht neu rechnen: das Bild selbst aendert sich
        # nicht, und _render_spectrogram wuerde bei unveraendertem
        # Ausschnitt ohnehin abbrechen.
        self.spec_img.setLevels(self._spec_levels)

    def _toggle_spectrogram(self, on: bool) -> None:
        self.spec_plot.setVisible(on)
        if on:
            self._load_spectrogram()
            self._render_spectrogram(force=True)

    def _load_spectrogram(self) -> None:
        """Einmalige Vorbereitung: Helligkeit, Achse, Auswahlbereich."""
        if self._samples is None or self._spectrogram_done:
            return
        image, _, _, top = audio_mod.spectrogram(self._samples, self._rate)
        if image.size == 0:
            return

        # Der obere Wert kommt aus dem Bild selbst, der untere 70 dB
        # darunter. Berechnet wird er einmal ueber die ganze Aufnahme, damit
        # die Helligkeit beim Zoomen stehenbleibt — sonst wuerde jeder
        # Ausschnitt neu ausgesteuert und eine leise Stelle saehe aus wie
        # eine laute.
        #
        # Fuer eine einzelne Aufnahme ist das richtig; fuer zwei
        # nebeneinander nicht, denn dann steuert sich jede fuer sich aus und
        # der Helligkeitsunterschied zwischen ihnen verschwindet. Deshalb
        # bleibt die gerechnete Aussteuerung hier stehen und die Anzeige
        # entscheidet sich in _levels() erneut.
        ceiling = float(np.percentile(image, 99.5))
        self._spec_auto_levels = (ceiling - 70.0, ceiling)
        self._spec_levels = self._levels()
        self._spec_top = top

        self.spec_plot.setYRange(0, top, padding=0)
        # Erst hier und nicht in _build_spectrogram: welche der drei Linien
        # ueberhaupt ins Bild passen, haengt an der oberen Frequenz, und die
        # steht erst fest, wenn die Aufnahme gelesen ist.
        self._guides = add_formant_guides(self.spec_plot, top,
                                          settings.get_formant_guides())
        self.spec_plot.addItem(self.spec_region)
        self.spec_region.setBounds((0.0, self._duration))
        self._mirror(self.region, self.spec_region)
        self._spectrogram_done = True
        self._render_spectrogram(force=True)

    def _render_zoom(self) -> None:
        """Beide Diagramme auf den sichtbaren Ausschnitt bringen."""
        self._render_waveform()
        self._render_spectrogram()

    def _render_waveform(self) -> None:
        """Die Wellenform aus den echten Abtastwerten des Ausschnitts.

        Die Huellkurve ueber die ganze Aufnahme hat 2400 Stuetzstellen. Bei
        sechs Sekunden ist das jede 2,5 Millisekunden — beim Hineinzoomen
        auf ein paar Hundertstel bleibt davon eine Treppe uebrig, die mit
        dem Signal nichts mehr zu tun hat. Also wird auch sie fuer den
        sichtbaren Bereich neu gebildet, und ist der klein genug, stehen
        dort die Abtastwerte selbst.
        """
        if self._samples is None or self.wave_curve is None:
            return
        view = self.wave_plot.getPlotItem().vb
        low, high = view.viewRange()[0]
        start = max(0, int(max(0.0, low) * self._rate))
        stop = min(self._samples.size,
                   int(min(self._duration, high) * self._rate) + 1)
        if stop - start < 2:
            return

        piece = self._samples[start:stop]
        if piece.size <= 4000:
            xs = np.arange(start, stop, dtype=np.float64)
            ys = piece
        else:
            xs, ys = audio_mod.envelope(piece, 2400)
            xs = np.asarray(xs, dtype=np.float64) + start
        self.wave_curve.setData(xs / float(self._rate), ys)

    @staticmethod
    def _window_for(span: float, rate: int) -> int:
        """Fensterlaenge, die zum sichtbaren Zeitraum passt.

        Das Fenster bestimmt, wie fein das Spektrogramm in der Zeit
        aufloest. 1024 Abtastwerte sind bei 16 kHz 64 ms lang — wer auf
        25 ms hineinzoomt, sieht in jeder Spalte fast dasselbe Stueck Ton
        und bekommt waagerechte Streifen statt Struktur. Also faellt das
        Fenster mit dem Ausschnitt, bis hinunter zu 128.

        Der Preis ist Frequenzaufloesung: ein kurzes Fenster unterscheidet
        benachbarte Obertoene schlechter. Genau der Tausch ist beim
        Hineinzoomen aber gewollt.
        """
        nfft = 1024
        while nfft > 128 and nfft / rate > span / 8.0:
            nfft //= 2
        return nfft

    def _render_spectrogram(self, force: bool = False) -> None:
        """Das Bild fuer den gerade sichtbaren Zeitraum rechnen.

        Ein einmal fuer die ganze Aufnahme gerechnetes Bild hat so viele
        Spalten, wie das Diagramm breit ist. Wer hineinzoomt, zieht ein
        paar davon auseinander und sieht Kloetzchen. Also wird derselbe
        Aufwand auf den kleineren Ausschnitt verwendet: gleich viele
        Spalten, weniger Zeit, mehr zu erkennen.
        """
        if not self._spectrogram_done or self.spec_plot.isHidden():
            return
        view = self.spec_plot.getPlotItem().vb
        low, high = view.viewRange()[0]
        low = max(0.0, float(low))
        high = min(float(self._duration), float(high))
        if high - low < 1e-3:
            return
        if not force and self._spec_span is not None:
            vorher_low, vorher_high = self._spec_span
            # Ein Nachrechnen lohnt erst, wenn sich der Ausschnitt spuerbar
            # geaendert hat; sonst rechnete jedes Verschieben um ein Pixel.
            breite = vorher_high - vorher_low
            if (abs(low - vorher_low) < breite * 0.02
                    and abs(high - vorher_high) < breite * 0.02):
                return

        rate = self._rate
        nfft = self._window_for(high - low, rate)
        # Etwas Vorlauf auf beiden Seiten: das erste Fenster beginnt eine
        # halbe Fensterlaenge vor der ersten Spalte, sonst bliebe am Rand
        # ein leerer Streifen stehen.
        start = max(0, int(low * rate) - nfft)
        stop = min(self._samples.size, int(high * rate) + nfft)
        piece = self._samples[start:stop]
        if piece.size < nfft:
            return

        image, first, last, top = audio_mod.spectrogram(piece, rate, nfft=nfft)
        if image.size == 0:
            return
        offset = start / float(rate)
        self._spec_levels = self._levels()
        self.spec_img.setImage(image, autoLevels=False,
                               levels=self._spec_levels)
        # Muss NACH setImage kommen, sonst kann pyqtgraph nicht skalieren.
        self.spec_img.setRect(QtCore.QRectF(offset + first, 0.0,
                                            max(last - first, 1e-6), top))
        self._spec_span = (low, high)

    def _toggle_advanced(self, on: bool) -> None:
        self.btn_advanced.setText(("▾  " if on else "▸  ") + i18n.t("advanced"))
        self.advanced.setVisible(on)
        if on and self._samples is None:
            self._load_waveform()
        if on:
            # Zwei Diagramme brauchen mehr Platz als eines — aber nicht
            # mehr, als der Bildschirm hergibt, sonst steht die Knopfreihe
            # unter dem unteren Rand.
            screen = self.screen()
            room = screen.availableGeometry().height() - 80 if screen else 1020
            self.resize(self.width(), max(self.height(), min(1020, room)))

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
        self.wave_curve = self.wave_plot.plot(
            pen=pg.mkPen(NORD["accent"], width=1))
        duration = data.size / float(rate)
        self._duration = duration
        self.btn_full.setEnabled(True)
        self.wave_plot.setXRange(0, duration, padding=0)
        self.wave_plot.addItem(self.region)
        # Voreinstellung: mittleres Drittel, damit sofort sichtbar ist,
        # dass sich der Bereich ziehen laesst.
        self.region.setRegion((duration / 3.0, duration * 2.0 / 3.0))
        self.region.setBounds((0.0, duration))
        self._render_waveform()
        if self.chk_spec.isChecked():
            self._load_spectrogram()
        self._region_moved()

    def _span(self) -> tuple[float, float]:
        low, high = self.region.getRegion()
        return float(min(low, high)), float(max(low, high))

    def _region_moved(self) -> None:
        start, end = self._span()
        self.range_label.setText(
            i18n.t("selection_label", start=start, end=end, length=end - start))
        self._mirror(self.region, self.spec_region)

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
        """Zurueck auf die gespeicherten Werte — und die Markierung mit.

        Nur die Werte zurueckzusetzen reicht nicht: liegt gerade keine
        ausgewertete Auswahl vor, aendert sich dabei nichts Sichtbares und
        der Knopf wirkt kaputt. Die Region geht deshalb immer auf die
        ganze Aufnahme auf, damit zu sehen ist, worauf sich die Tabelle
        gerade bezieht.
        """
        self._selection_stats = None
        self._selection_span = None
        self.btn_sel_save.setEnabled(False)
        if self._samples is not None and self._duration > 0.0:
            # Loest _region_moved aus und schreibt damit das Bereichslabel
            # neu — genau das soll passieren.
            self.region.setRegion((0.0, self._duration))
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
            f"QToolButton {{ color: {NORD['dim']}; border: none;"
            " font-size: 14px; }"
            f"QToolButton:hover {{ color: {NORD['accent']}; }}")
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
        suggestion = str(Path(self.session_dir) / f"{stem}-report.txt")
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
        return storage.path_for(self.entry.get("file", ""))

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
