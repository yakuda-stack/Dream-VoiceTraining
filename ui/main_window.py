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

"""Hauptfenster: setzt Live- und Sessions-Reiter zusammen und verwaltet Dialoge, Sprache und Design."""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
import sounddevice as sd
from PySide6 import QtCore, QtWidgets

from core import i18n
from core import paths
from voice import practice
from core import settings
from ui import theming
from voice.audio import (SPEC_CEIL_DB, SPEC_FLOOR_DB, AudioEngine)
from ui.dialogs import (HelpDialog, IntroDialog, SettingsDialog, Spotlight)
from core import wininstall
from core.settings import CFG
from ui.constants import (TICK_MS, NFFT, SPEC_COLS, MAX_FREQ)
from ui.live_tab import LiveTabMixin
from ui.update_check import (UpdateAskDialog, UpdateChecker, UpdateDialog,
                             VersionLabel)
from ui.session_tab import SessionTabMixin

SESSION_DIR = paths.SESSION_DIR
SESSION_INDEX = paths.SESSION_INDEX


class MainWindow(LiveTabMixin, SessionTabMixin, QtWidgets.QMainWindow):

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
        # elapsed misst den laufenden Durchgang, run_seconds summiert die
        # vorherigen. Zusammen ergeben sie eine Uhr, die nur laeuft, solange
        # der Stream laeuft — siehe _clock().
        self.elapsed = QtCore.QElapsedTimer()
        self.elapsed.start()
        self.run_seconds = 0.0
        self._break_shown = False
        self.f0_smooth: deque[float] = deque(maxlen=3)
        # Steht schon vor dem UI-Aufbau, weil die Auswahlliste beim
        # Fuellen dagegen vergleicht.
        self._practice_key = practice.BUILTIN

        paths.ensure_dirs()
        self.sessions = self._load_sessions()
        self.view = settings.get_view()
        self._rows: list[dict] = []
        self._reordering = False
        self._record_peak = 0.0
        self._action_rows: set[int] = set()
        self._action_column = None
        self._dialogs: list[QtWidgets.QDialog] = []
        self.version_label = None
        # Die Marke der Einfuehrung haengt am Fenster, nicht am Reiterinhalt:
        # so ueberlebt sie einen Neuaufbau der Oberflaeche.
        self._spot = None
        self._spot_key = ""

        self.ui_language = i18n.LANG
        self._build_ui()
        self._refresh_devices()
        self._fill_session_table()

        self.setStyleSheet(theming.window_background_style())

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.setInterval(TICK_MS)

    def _n_bins(self) -> int:
        return int(MAX_FREQ / (self.sr / NFFT)) + 1

    # -- UI-Aufbau -------------------------------------------------------

    def _build_ui(self) -> None:
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_live_tab(), i18n.t("tab_live"))
        tabs.addTab(self._build_session_tab(), i18n.t("tab_sessions"))
        self.tabs = tabs
        self.setCentralWidget(tabs)
        if self.statusBar() is not None:
            self.status = self.statusBar()
            self.status.showMessage(i18n.t("pick_device"))

            # Dezent unten rechts, damit sie in einem Fehlerbericht
            # mitfotografiert wird, ohne sich in den Vordergrund zu draengen.
            # Die Statusleiste ueberlebt einen Neuaufbau der Reiter, das
            # Schild darf also nur einmal entstehen.
            if self.version_label is None:
                self.version_label = VersionLabel()
                self.version_label.clicked.connect(self._open_update)
                self.status.addPermanentWidget(self.version_label)
            self.version_label.refresh()

    # -- Aktualisierung ---------------------------------------------------

    def check_for_updates(self) -> None:
        """Einmal im Hintergrund fragen, wenn es erlaubt ist.

        Ist noch nichts entschieden, kommt zuerst die Frage — aber nicht
        mitten in die Einfuehrung oder ueber einen anderen modalen Dialog.
        """
        choice = settings.get_update_check()
        if choice is None:
            self._ask_update_check()
            return
        if not choice:
            return
        self._update_checker = UpdateChecker(self)
        self._update_checker.found.connect(self._update_found)
        self._update_checker.start()

    def _ask_update_check(self) -> None:
        if QtWidgets.QApplication.activeModalWidget() is not None:
            QtCore.QTimer.singleShot(2000, self.check_for_updates)
            return
        for dialog in self._dialogs:
            if isinstance(dialog, IntroDialog):
                dialog.finished.connect(
                    lambda _=0: QtCore.QTimer.singleShot(
                        600, self.check_for_updates))
                return
            if getattr(dialog, "objectName", lambda: "")() == "update_ask":
                return

        ask = UpdateAskDialog(self)
        ask.language_chosen.connect(
            lambda code: (self._set_language(code), ask.retranslate()))
        ask.answered.connect(self._update_answered)
        self.open_dialog(ask)

    def _update_answered(self, allowed: bool) -> None:
        settings.set_update_check(allowed)
        if allowed:
            self.check_for_updates()

    def _update_found(self, release) -> None:
        self.version_label.set_release(release)

    def _open_update(self) -> None:
        release = self.version_label.release
        if release is None:
            return
        for dialog in self._dialogs:
            if isinstance(dialog, UpdateDialog):
                dialog.raise_()
                dialog.activateWindow()
                return
        self.open_dialog(UpdateDialog(release, self))

    # -- Erscheinungsbild -------------------------------------------------

    def apply_theme(self) -> None:
        """Farben, Hintergrundbild und Deckkraft übernehmen.

        Die Oberfläche wird neu aufgebaut, weil Stiftfarben und
        Diagrammhintergründe beim Erzeugen der Widgets gesetzt werden und
        ein Stylesheet sie nicht erreicht.
        """
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.setStyleSheet(theming.stylesheet())
        self.setStyleSheet(theming.window_background_style())

        settings.set_theme(theming.snapshot())
        self._rebuild_keeping_state()

    def _rebuild_keeping_state(self) -> None:
        was_running = self.engine.running
        was_recording = self.engine.is_recording

        self._build_ui()
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
        self.show_spotlight(self._spot_key)

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

    # -- Sprache ----------------------------------------------------------

    def _set_language(self, code: str) -> None:
        if not code:
            return
        index = self.lang_box.findData(code)
        if index >= 0 and index != self.lang_box.currentIndex():
            self.lang_box.blockSignals(True)
            self.lang_box.setCurrentIndex(index)
            self.lang_box.blockSignals(False)
        # Gegen die Sprache pruefen, in der die Oberflaeche gebaut wurde, nicht
        # gegen die globale — sonst bleibt ein Wechsel wirkungslos, wenn beide
        # auseinanderlaufen.
        if code == self.ui_language:
            return

        i18n.set_language(code)
        settings.set_language(code)

        # Der Audiostrom lebt unabhaengig vom UI, deshalb laesst sich die
        # Oberflaeche gefahrlos neu aufbauen.
        self.ui_language = code
        self._rebuild_keeping_state()

    # -- Einstellungen ----------------------------------------------------

    def show_intro(self, ask_language: bool = True) -> None:
        for dialog in self._dialogs:
            if isinstance(dialog, IntroDialog):
                dialog.raise_()
                dialog.activateWindow()
                return
        dialog = IntroDialog(self, ask_language)
        dialog.language_chosen.connect(self._set_language)
        dialog.spotlight.connect(self.show_spotlight)
        dialog.finished.connect(lambda _=0: self.show_spotlight(""))
        self.open_dialog(dialog)

    # -- Wegweiser der Einfuehrung ----------------------------------------

    def show_spotlight(self, key: str) -> None:
        """Goldene Marke auf das Bedienelement setzen, um das es gerade geht.

        Die Einfuehrung nennt nur einen Schluessel; welches Widget dahinter
        steckt, weiss allein das Hauptfenster. Ein unbekannter Schluessel
        nimmt die Marke weg, statt zu scheitern.
        """
        self._spot_key = key or ""
        if self._spot is None:
            if not self._spot_key:
                return
            self._spot = Spotlight(self)

        target, anchor = self._spot_target(self._spot_key)
        if target is None:
            self._spot.detach()
            return
        # Liegt das Ziel in einem Reiter, der nicht vorn ist, zeigt die Marke
        # auf etwas Unsichtbares und versteckt sich. Vorher aufblaettern.
        # Nach Schluesseln zu entscheiden ging beim Einstellungsknopf schief:
        # der steht im Live-Reiter, die Seite davor hatte auf Sessions
        # umgeschaltet, und die Marke blieb unsichtbar.
        self._reveal(target)
        self._spot.attach(target, anchor)

    def _reveal(self, target: QtWidgets.QWidget) -> None:
        """Den Reiter nach vorn holen, in dem das Ziel liegt.

        Sitzt das Ziel in keinem Reiter — die Reiterleiste selbst etwa —,
        bleibt die Ansicht, wie sie ist.
        """
        for index in range(self.tabs.count()):
            page = self.tabs.widget(index)
            if page is target or page.isAncestorOf(target):
                self.tabs.setCurrentIndex(index)
                return

    def _spot_target(self, key: str):
        if key == "microphone":
            return self.device_box, None
        if key == "type":
            return self.type_box, None
        if key == "help":
            return self.btn_help, lambda w: QtCore.QPoint(w.width() // 2,
                                                          w.height() // 2)
        if key == "settings":
            return self.btn_settings, None
        if key == "filter":
            return getattr(self, "btn_filter", None), None
        if key == "sessions":
            bar = self.tabs.tabBar()
            return bar, lambda w: QtCore.QPoint(w.tabRect(1).right(),
                                                w.tabRect(1).top() + 8)
        return None, None

    def _open_help(self, topic: str | None = None) -> None:
        """Nicht modal: nachschlagen waehrend der Aufnahme, nicht statt ihr."""
        for dialog in self._dialogs:
            if isinstance(dialog, HelpDialog):
                if topic:
                    dialog.show_topic(topic)
                dialog.raise_()
                dialog.activateWindow()
                return
        self.open_dialog(HelpDialog(self, topic))

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, entries=self.sessions)
        dialog.applied.connect(self._apply_settings)
        dialog.theme_changed.connect(self.apply_theme)
        dialog.intro_requested.connect(self.show_intro)
        # Ein Umzug hat entry["file"] veraendert, ein Ordnerwechsel den Ort:
        # beides muss in die Liste, bevor jemand auf Abspielen drueckt.
        dialog.storage_changed.connect(self._session_changed)
        # Ein neuer oder geloeschter Typ aendert die Auswahl im Livebereich
        # und die Beschriftungen in der Sessionliste.
        dialog.types_changed.connect(self._types_changed)
        self.open_dialog(dialog)

    def _types_changed(self) -> None:
        self._fill_types()
        self._fill_session_table()

    def _show_formant_guides(self) -> None:
        """Orientierungslinien ein- oder ausblenden.

        Nur die Sichtbarkeit: die Linien neu zu bauen hiesse, sie aus dem
        Diagramm zu nehmen und wieder hineinzuhaengen, und dabei geht die
        Reihenfolge gegenueber Bild und Messlinien verloren.
        """
        visible = settings.get_formant_guides()
        for line in self.spec_guides:
            line.setVisible(visible)

    def _apply_settings(self) -> None:
        self._fill_profiles()
        self._show_formant_guides()
        self.zone_region.setRegion((CFG.zone_low, CFG.zone_high))
        lo = min(60.0, CFG.pitch_floor)
        hi = min(CFG.pitch_ceiling, max(320.0, CFG.zone_high + 120.0))
        self.pitch_plot.setYRange(lo, hi, padding=0)
        self.zone_bar.update()
        self.f0_smooth.clear()
        name = settings.template_label(settings.active_template())
        self.status.showMessage(i18n.t("settings_applied", name=name))

    # -- Erster Start unter Windows ---------------------------------------

    def start_first_run(self, offer_install: bool, with_intro: bool) -> None:
        """Frage und Einfuehrung nacheinander, nicht uebereinander.

        Beides mit einem Zeitgeber zu starten legt die Einfuehrung hinter
        den modalen Dialog — von dort holt sie niemand hervor.
        """
        if offer_install and self._offer_install():
            return                      # startet vom neuen Ort neu
        if with_intro:
            self.show_intro()

    def _offer_install(self) -> bool:
        """Anbieten, sich einzurichten. True, wenn ein Neustart laeuft."""
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("install_offer_title"),
            i18n.t("install_offer_body", folder=str(wininstall.target_dir())),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes)

        # Auch ein Nein wird vermerkt: die Frage kommt nur einmal.
        settings.set_install_asked(True)
        settings.save()
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return False

        try:
            destination = wininstall.install()
        except OSError as error:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("install_offer_title"),
                i18n.t("install_failed", error=str(error)))
            return False

        wininstall.relaunch(destination, Path(sys.executable).resolve())
        QtCore.QTimer.singleShot(0, QtWidgets.QApplication.quit)
        return True

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
        self.timer.stop()
        self.engine.stop()
        try:
            sd.stop()
        except Exception:
            pass
        super().closeEvent(event)
