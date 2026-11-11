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

"""Live-Reiter: Aufbau, Geraete, Audiostrom, Uebungstexte, Diagramme und Aufnahme."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets

from voice import analysis
from core import i18n
from voice import practice
from core import rectypes
from core import progress
from core import settings
from core import storage
from voice import targets
from ui.theming import COLORS as NORD
from voice import audio as audio_mod
from voice.audio import (DEFAULT_KEY, SPEC_CEIL_DB, SPEC_FLOOR_DB)
from ui.dialogs import (MEASURED_Z, MicrophonePicker, add_formant_guides)
from core.settings import CFG
from ui.constants import (ANALYSIS_EVERY, WINDOW_SECONDS, NFFT, HOP, SPEC_COLS,
                          KEY_ROLE, MAX_FREQ, LOW_LEVEL_DB, HISTORY_SECONDS)
from ui.widgets import StatCard, ZoneBar


class LiveTabMixin:
    """Alles, was zum Live-Reiter gehoert. Wird in MainWindow eingemischt."""

    def _build_live_tab(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(page)
        root.setContentsMargins(14, 14, 14, 10)
        root.setSpacing(12)

        # Steuerleiste
        bar = QtWidgets.QHBoxLayout()

        self.lang_box = QtWidgets.QComboBox()
        self.lang_box.setObjectName("language")
        self.lang_box.setToolTip(i18n.t("language_tip"))
        for code, name in i18n.available():
            self.lang_box.addItem(name, code)
        self.lang_box.setCurrentIndex(max(0, self.lang_box.findData(i18n.LANG)))
        self.lang_box.currentIndexChanged.connect(
            lambda _i: self._set_language(self.lang_box.currentData()))

        self.device_box = QtWidgets.QComboBox()
        self.device_box.setObjectName("device")
        # Der Text im Klappmenue wird beschnitten, sobald der Name lang ist —
        # unter Windows der Normalfall. Der ganze Name steht im Tooltip und
        # in der grossen Auswahl daneben.
        self.device_box.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.device_box.setMinimumContentsLength(18)
        self.device_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed)
        self.device_box.currentIndexChanged.connect(self._device_tooltip)

        self.btn_pick = QtWidgets.QPushButton()
        self.btn_pick.setIcon(self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.btn_pick.setToolTip(i18n.t("mic_pick_tip"))
        self.btn_pick.setFixedWidth(40)
        self.btn_pick.clicked.connect(self._pick_device)

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
        self.btn_reference = QtWidgets.QPushButton("▶  " + i18n.t("reference_play"))
        self.btn_reference.clicked.connect(self._play_reference)
        self._update_reference_button()
        self.type_box = QtWidgets.QComboBox()
        # "Tonhoehentest (Summen)" ist das laengste Wort und zieht das Feld
        # sonst auf eine Breite, die "Lesetext" nicht braucht. Der volle Text
        # steht im Tooltip, der Platz gehoert dem Mikrofonnamen.
        self.type_box.setMaximumWidth(150)
        self.type_box.currentIndexChanged.connect(
            lambda: settings.set_recording_type(self.type_box.currentData()))
        self._fill_types()

        self.profile_box = QtWidgets.QComboBox()
        self.profile_box.setMaximumWidth(140)
        self._fill_profiles()
        self.profile_box.currentIndexChanged.connect(self._profile_chosen)

        self.btn_settings = QtWidgets.QPushButton("⚙  " + i18n.t("settings"))
        self.btn_settings.clicked.connect(self._open_settings)

        self.btn_help = QtWidgets.QPushButton("ⓘ")
        self.btn_help.setObjectName("help")
        self.btn_help.setFixedWidth(40)
        self.btn_help.setToolTip(i18n.t("help_tip"))
        self.btn_help.clicked.connect(self._open_help)

        bar.addWidget(self.lang_box)
        bar.addSpacing(14)
        bar.addWidget(QtWidgets.QLabel(i18n.t("microphone")))
        bar.addWidget(self.device_box, 1)
        bar.addWidget(self.btn_pick)
        bar.addWidget(self.btn_refresh)
        bar.addSpacing(10)
        bar.addWidget(self.btn_start)
        bar.addWidget(self.btn_record)
        bar.addWidget(self.btn_reference)
        bar.addSpacing(10)
        bar.addWidget(QtWidgets.QLabel(i18n.t("recording_type")))
        bar.addWidget(self.type_box)
        bar.addSpacing(10)
        bar.addWidget(QtWidgets.QLabel(i18n.t("target_voice")))
        bar.addWidget(self.profile_box)
        bar.addSpacing(10)
        bar.addWidget(self.btn_settings)
        bar.addWidget(self.btn_help)
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
        self.card_target = StatCard(i18n.t("card_target"), " %", NORD["green"])
        self.card_target.setToolTip(i18n.t("card_target_tip"))
        for c in (self.card_f0, self.card_zone, self.card_f1, self.card_f2,
                  self.card_h1h2, self.card_level, self.card_target):
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
            # Ueber den Orientierungslinien: der gemessene Wert ist das,
            # was zaehlt, und darf von einem Anhaltspunkt nicht verdeckt
            # werden, wenn beide zufaellig aufeinandertreffen.
            ln.setZValue(MEASURED_Z)
            self.spec_plot.addItem(ln, ignoreBounds=True)

        # Die drei blassen, gepunkteten Linien darunter. MAX_FREQ begrenzt
        # das Bild nach oben, die halbe Abtastrate ebenso — die kleinere
        # von beiden entscheidet, welche Linie noch hineinpasst.
        self.spec_guides = add_formant_guides(
            self.spec_plot, min(MAX_FREQ, self.sr / 2.0),
            settings.get_formant_guides())

        spec_group = QtWidgets.QGroupBox(i18n.t("spectrogram"))
        sg = QtWidgets.QVBoxLayout(spec_group)
        sg.addWidget(self.spec_plot)
        root.addWidget(spec_group, 3)
        self._plot_menu(self.spec_plot, self._spec_menu)

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

        # Fadenkreuz: zeigt beim Ueberfahren, welche Tonhoehe unter dem
        # Zeiger liegt. Die Beschriftung haengt an der Linie selbst statt
        # an einer festen Stelle — so wandert sie mit, wenn sich der
        # Zeitausschnitt unter ihr weiterschiebt.
        self.pitch_cursor = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen(NORD["fg"], width=1,
                         style=QtCore.Qt.PenStyle.DashLine),
            label="{value:0.0f} Hz",
            labelOpts={"position": 0.02, "color": NORD["fg"],
                       "fill": pg.mkBrush(QtGui.QColor(NORD["bg3"])),
                       "border": pg.mkPen(NORD["border"])})
        self.pitch_cursor.setZValue(20)
        self.pitch_cursor.setVisible(False)
        self.pitch_plot.addItem(self.pitch_cursor, ignoreBounds=True)
        self.pitch_plot.scene().sigMouseMoved.connect(self._pitch_hover)
        # Fuer den Fall, dass der Zeiger das Fenster verlaesst, ohne noch
        # ein Bewegungssignal ueber dem Diagramm auszuloesen.
        self.pitch_plot.installEventFilter(self)

        self._plot_menu(self.pitch_plot, self._pitch_menu)

        pitch_group = QtWidgets.QGroupBox(i18n.t("history"))
        pgl = QtWidgets.QVBoxLayout(pitch_group)
        pgl.addWidget(self.pitch_plot)
        root.addWidget(pitch_group, 2)

        # Uebungstext
        text_group = QtWidgets.QGroupBox(i18n.t("practice_text"))
        tg = QtWidgets.QVBoxLayout(text_group)

        picker = QtWidgets.QHBoxLayout()
        self.practice_box = QtWidgets.QComboBox()
        # Namen sind kurz; ueber die ganze Breite gezogen sieht das Feld
        # leer aus. Der Rest der Zeile gehoert dem Abstand.
        self.practice_box.setMaximumWidth(360)
        self.practice_box.currentIndexChanged.connect(self._practice_picked)
        self.btn_practice_save = QtWidgets.QPushButton(i18n.t("save_as"))
        self.btn_practice_save.clicked.connect(self._save_practice)
        self.btn_practice_delete = QtWidgets.QPushButton(i18n.t("delete"))
        self.btn_practice_delete.clicked.connect(self._delete_practice)
        picker.addWidget(self.practice_box, 1)
        picker.addStretch(1)
        picker.addWidget(self.btn_practice_save)
        picker.addWidget(self.btn_practice_delete)
        tg.addLayout(picker)

        self.practice_edit = QtWidgets.QTextEdit()
        self.practice_edit.setMaximumHeight(78)
        tg.addWidget(self.practice_edit)
        root.addWidget(text_group)

        self._fill_practice()

        return page

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
        self._device_tooltip()

    def _device_tooltip(self) -> None:
        """Ganzer Name als Tooltip, weil das Feld ihn beschneidet."""
        text = self.device_box.currentText().strip()
        self.device_box.setToolTip(text)

    def _pick_device(self) -> None:
        """Grosse Auswahl oeffnen und die Entscheidung uebernehmen."""
        dialog = MicrophonePicker(self._current_device_key(), self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        key = dialog.selected_key()
        if key is None:
            return

        # Die Liste kann sich im Dialog geaendert haben (Aktualisieren), also
        # neu aufbauen und danach die Wahl setzen.
        settings.set_device(key)
        self._refresh_devices()
        self._device_tooltip()

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
            # Die bisherige Laufzeit festhalten, bevor der Zeitgeber beim
            # naechsten Start wieder bei null anfaengt. Ohne das entstuende
            # in der Zeitachse eine Luecke so gross wie die Pause, und der
            # Verlauf davor faende sich schlagartig ausserhalb der letzten
            # 30 Sekunden wieder — sichtbar waere dasselbe wie geloescht.
            self.run_seconds += self.elapsed.elapsed() / 1000.0
            self.engine.stop()
            self.timer.stop()
            self.btn_start.setText(i18n.t("start"))
            self.btn_record.setEnabled(False)
            self.status.showMessage(i18n.t("stopped"))
            self._break_shown = False
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

        # Weder Spektrogramm noch Verlauf werden geleert: beides soll da
        # weitergehen, wo der letzte Lauf aufgehoert hat. Der Zaehler
        # engine.total_samples laeuft ueber das Stoppen hinweg weiter und
        # steht waehrend der Pause still, also passt spec_cursor noch.
        self.elapsed.restart()
        self.timer.start()
        self.btn_start.setText(i18n.t("stop"))
        self.btn_record.setEnabled(True)
        settings.set_device(self._current_device_key())
        self.status.showMessage(i18n.t("running", rate=self.sr))

    # -- Uebungstexte ------------------------------------------------------

    def _fill_practice(self, select: str | None = None) -> None:
        """Auswahlliste neu aufbauen und den zugehoerigen Text einsetzen."""
        key = practice.resolve(select or settings.get_practice_choice())
        blocked = self.practice_box.blockSignals(True)
        self.practice_box.clear()
        for entry in practice.keys():
            self.practice_box.addItem(practice.label(entry), entry)
        self.practice_box.setCurrentIndex(
            max(0, self.practice_box.findData(key)))
        self.practice_box.blockSignals(blocked)
        settings.set_practice_choice(key)
        self._show_practice(key)

    def _show_practice(self, key: str) -> None:
        self._practice_key = key
        self.practice_edit.setPlainText(practice.body(key))
        # Der eingebaute Text laesst sich nicht loeschen. Er bleibt als
        # Rueckfallebene stehen, auch wenn alle eigenen weg sind.
        self.btn_practice_delete.setEnabled(practice.is_user(key))

    def _practice_picked(self) -> None:
        key = self.practice_box.currentData()
        if key is None or key == self._practice_key:
            return
        if not self._practice_may_leave():
            # Zurueck auf den alten Eintrag, ohne dieses Signal erneut
            # auszuloesen.
            blocked = self.practice_box.blockSignals(True)
            self.practice_box.setCurrentIndex(
                self.practice_box.findData(self._practice_key))
            self.practice_box.blockSignals(blocked)
            return
        settings.set_practice_choice(key)
        self._show_practice(key)

    def _practice_may_leave(self) -> bool:
        """Nachfragen, wenn im Feld etwas Ungespeichertes steht.

        Ein Wechsel in der Liste ueberschreibt das Feld. Wer gerade einen
        Text getippt und noch nicht gespeichert hat, waere ihn sonst mit
        einem Klick los.
        """
        typed = self.practice_edit.toPlainText().strip()
        if typed == practice.body(self._practice_key).strip():
            return True
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("practice_discard_title"),
            i18n.t("practice_discard_body"))
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def _save_practice(self) -> None:
        """Den Text im Feld unter einem Namen ablegen.

        Vorgeschlagen wird der Name des gerade gewaehlten eigenen Textes:
        wer einen bestehenden ueberarbeitet, bestaetigt einmal und ist
        fertig. Beim eingebauten bleibt das Feld leer — der bekommt auf
        diesem Weg eine Kopie unter eigenem Namen und bleibt selbst, wie
        er ist.
        """
        text = self.practice_edit.toPlainText().strip()
        if not text:
            QtWidgets.QMessageBox.information(
                self, i18n.t("practice_save_title"), i18n.t("practice_empty"))
            return

        current = self.practice_box.currentData()
        suggestion = (practice.name_of(current)
                      if practice.is_user(current) else "")
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("practice_save_title"), i18n.t("name"),
            text=suggestion)
        name = practice.clean_name(name)
        if not ok or not name:
            return

        settings.save_practice_text(name, text)
        self._fill_practice(select=practice.USER_PREFIX + name)
        self.status.showMessage(i18n.t("practice_saved", name=name))

    def _delete_practice(self) -> None:
        key = self.practice_box.currentData()
        if not practice.is_user(key):
            return
        name = practice.name_of(key)
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("practice_delete_title"),
            i18n.t("practice_delete_body", name=name))
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            settings.delete_practice_text(name)
            self._fill_practice(select=practice.BUILTIN)

    # -- Diagramme: Zeiger und Kontextmenue --------------------------------

    @staticmethod
    def _plot_menu(plot, handler) -> None:
        """Eigenes Kontextmenue statt des eingebauten von pyqtgraph.

        Dessen Menue bietet Zoom und Achsenbereiche an — beides ist hier
        abgeschaltet, es waere also ein Menue voller Eintraege ohne Wirkung.
        """
        plot.setMenuEnabled(False)
        plot.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        plot.customContextMenuRequested.connect(handler)

    def _pitch_menu(self, pos) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction(i18n.t("clear_history"), self._clear_history)
        menu.exec(self.pitch_plot.mapToGlobal(pos))

    def _spec_menu(self, pos) -> None:
        menu = QtWidgets.QMenu(self)
        menu.addAction(i18n.t("clear_spectrogram"), self._clear_spectrogram)
        menu.exec(self.spec_plot.mapToGlobal(pos))

    def _clear_history(self) -> None:
        """Verlauf verwerfen.

        Seit Start und Stopp ihn stehenlassen, braucht es einen Weg, ihn
        von Hand loszuwerden — sonst haengt nach der dritten Uebung noch
        der Anfang der ersten mit im Bild.
        """
        self.history.clear()
        self.f0_smooth.clear()
        self.pitch_curve.setData([], [])

    def _clear_spectrogram(self) -> None:
        # Derselbe Wert wie beim Aufbau in __init__: knapp unter dem
        # Anzeigeboden, damit ein leeres Bild ueberall gleich aussieht.
        self.spec[:] = -100.0
        self.spec_img.setImage(self.spec, autoLevels=False,
                               levels=(SPEC_FLOOR_DB, SPEC_CEIL_DB))
        self.spec_img.setRect(QtCore.QRectF(0, 0, SPEC_COLS, MAX_FREQ))

    def _pitch_hover(self, pos) -> None:
        """Fadenkreuz auf die Tonhoehe unter dem Mauszeiger setzen."""
        view = self.pitch_plot.getPlotItem().vb
        # Das Signal kommt fuer die ganze Szene, also auch fuer die Achsen
        # und den Rand daneben. Dort gibt es keinen sinnvollen Messwert.
        if not view.sceneBoundingRect().contains(pos):
            self.pitch_cursor.setVisible(False)
            return
        # Reihenfolge zaehlt: die Beschriftung einer InfiniteLine bringt
        # sich nur auf Stand, solange sie sichtbar ist. Erst setzen und
        # dann einblenden hiesse, sie zeigte dauerhaft 0 Hz.
        self.pitch_cursor.setVisible(True)
        self.pitch_cursor.setPos(view.mapSceneToView(pos).y())

    def eventFilter(self, obj, event) -> bool:
        if (getattr(self, "pitch_plot", None) is obj
                and event.type() == QtCore.QEvent.Type.Leave):
            self.pitch_cursor.setVisible(False)
        return super().eventFilter(obj, event)

    # -- Haupttakt --------------------------------------------------------

    def _clock(self) -> float:
        """Laufzeit in Sekunden, ohne die Pausen zwischen den Durchgaengen.

        Die Zeitachse des Verlaufs haengt daran. Wuerde hier die Wanduhr
        stehen, risse jede Pause ein Loch hinein, das breiter ist als das
        gezeigte Fenster.
        """
        return self.run_seconds + self.elapsed.elapsed() / 1000.0

    def _tick(self) -> None:
        if not self.engine.running:
            return
        self.engine.pump()
        self._update_spectrogram()

        self.tick_count += 1
        if self.tick_count % ANALYSIS_EVERY == 0:
            self._update_analysis()

        self._check_break()

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

        t = self._clock()
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
        share = progress.target_share(
            [ff for _, ff in pts], targets.range_for("f0_median", profile))
        self.card_target.set(f"{share:.0f}" if share is not None else "--")
        if len(pts) >= 2:
            xs = np.array([p[0] for p in pts])
            ys = np.array([p[1] for p in pts])
            self.pitch_curve.setData(xs, ys)
            self.pitch_plot.setXRange(cutoff, t, padding=0)

    # -- Pausen-Erinnerung ------------------------------------------------

    def _check_break(self) -> None:
        """Einmal je Durchgang an eine Pause erinnern.

        Gemessen wird die Laufzeit seit dem letzten Start. Wer stoppt und
        wieder startet, hat in der Regel schon pausiert.
        """
        minutes = settings.get_break_minutes()
        if minutes <= 0 or getattr(self, "_break_shown", False):
            return
        if self.elapsed.elapsed() < minutes * 60_000:
            return
        self._break_shown = True
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Information, i18n.t("break_title"),
            i18n.t("break_body", minutes=minutes),
            QtWidgets.QMessageBox.StandardButton.Ok, self)
        self.open_dialog(box)

    # -- Referenz-Aufnahme ------------------------------------------------

    def _update_reference_button(self) -> None:
        name = settings.get_reference_file()
        exists = bool(name) and storage.path_for(name).exists()
        self.btn_reference.setEnabled(exists)
        self.btn_reference.setToolTip(
            i18n.t("reference_play_tip", name=name) if exists
            else i18n.t("reference_none_tip"))

    def _play_reference(self) -> None:
        name = settings.get_reference_file()
        if name:
            self._play_entry({"file": name})

    # -- Aufnahme ---------------------------------------------------------

    def _fill_types(self) -> None:
        """Typ-Auswahl neu aufbauen; eigene Typen koennen dazugekommen sein."""
        blocked = self.type_box.blockSignals(True)
        self.type_box.clear()
        for kind in rectypes.all_types():
            self.type_box.addItem(kind.label, kind.key)
            self.type_box.setItemData(self.type_box.count() - 1, kind.hint,
                                      QtCore.Qt.ItemDataRole.ToolTipRole)
        index = self.type_box.findData(settings.get_recording_type())
        self.type_box.setCurrentIndex(max(0, index))
        self.type_box.blockSignals(blocked)
        # Zeigte die Einstellung auf einen geloeschten Typ, steht jetzt ein
        # anderer im Feld — dann soll auch das gespeichert sein, sonst
        # bekaeme die naechste Aufnahme ein Kuerzel, das niemand mehr sieht.
        settings.set_recording_type(self.type_box.currentData())

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
