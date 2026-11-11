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

"""Changelog- und Highlights-Fenster."""

from __future__ import annotations

import urllib.request

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from core import paths
from ui.theming import COLORS as NORD


# ------------------------------------------------------------- Changelog

class ChangelogLoader(QtCore.QThread):
    """Holt die Versionshistorie, erst aus dem Netz, dann von der Platte.

    In einem eigenen Faden, weil ein hoeflicher Zeitablauf immer noch
    mehrere Sekunden dauert — und ein Fenster, das beim Aufgehen so lange
    steht, sieht abgestuerzt aus.

    Das ist die einzige Stelle, an der dieses Programm eine Verbindung nach
    draussen aufbaut, und sie entsteht nur, wenn jemand den Knopf drueckt.
    Gesendet wird dabei nichts ausser der Anfrage selbst.
    """

    #: Text und Herkunft ("online", "local" oder "" fuer nichts gefunden).
    done = QtCore.Signal(str, str)

    TIMEOUT = 6.0
    # Der Changelog ist ein paar Dutzend Kilobyte gross. Die Grenze schuetzt
    # davor, sich an einer Antwort festzulesen, die etwas ganz anderes ist.
    MAX_BYTES = 512 * 1024

    def __init__(self, online: bool = True, parent=None, urls=None,
                 local=None, marker: str = "#"):
        super().__init__(parent)
        self.online = online
        # Ohne Angabe der Changelog. Die Highlights reichen ihre eigenen
        # Adressen und ihre eigene Datei herein, der Ablauf ist derselbe.
        # Beides wird erst beim Laden nachgeschlagen, damit ein Test oder
        # ein Paket paths.* noch austauschen kann.
        self._urls = urls
        self._local = local
        self.marker = marker

    def run(self) -> None:
        if self.online:
            text = self._from_web()
            if text:
                self.done.emit(text, "online")
                return
        text = self._from_disk()
        self.done.emit(text, "local" if text else "")

    def _from_web(self) -> str:
        urls = self._urls() if self._urls else paths.CHANGELOG_URLS
        for url in urls:
            try:
                request = urllib.request.Request(
                    url, headers={"User-Agent":
                                  f"{paths.APP_NAME}/{paths.APP_VERSION}"})
                with urllib.request.urlopen(request,
                                            timeout=self.TIMEOUT) as answer:
                    raw = answer.read(self.MAX_BYTES)
            except Exception as exc:
                # Kein Netz ist der Normalfall, nicht der Fehlerfall: das
                # Fenster hat einen Rueckfall und braucht keinen Alarm.
                debuglog.log.debug("changelog: %s: %s", url, exc)
                continue
            text = raw.decode("utf-8", "replace").strip()
            # Ein Umleitungsziel oder eine Fehlerseite ist kein Changelog.
            if text.startswith(self.marker):
                return text
        return ""

    def _from_disk(self) -> str:
        path = self._local() if self._local else paths.changelog_file()
        if path is None:
            return ""
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            debuglog.log.warning("changelog: %s: %s", path, exc)
            return ""


class ChangelogDialog(QtWidgets.QDialog):
    """Die Versionshistorie als lesbarer Text.

    Qt setzt Markdown selbst, es braucht also kein weiteres Paket dafuer.
    Der Text kommt bevorzugt aus dem Netz — die mitgelieferte Datei ist so
    alt wie die installierte Fassung, und wer wissen will, was seit seiner
    Version passiert ist, erfaehrt daraus nichts.
    """

    #: Was dieses Fenster zeigt. HighlightsDialog tauscht nur diese Angaben.
    TITLE_KEY = "changelog_title"
    MISSING_KEY = "changelog_missing"
    WEB_PATH = "/blob/main/CHANGELOG.md"

    @staticmethod
    def _urls():
        return paths.CHANGELOG_URLS

    @staticmethod
    def _local():
        return paths.changelog_file()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t(self.TITLE_KEY))
        self.resize(760, 640)
        self.setMinimumSize(480, 360)
        self._loader: ChangelogLoader | None = None

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(10)

        self.view = QtWidgets.QTextBrowser()
        self.view.setOpenExternalLinks(True)
        self.view.setStyleSheet("font-size: 13px;")
        root.addWidget(self.view, 1)

        row = QtWidgets.QHBoxLayout()
        self.source = QtWidgets.QLabel("")
        self.source.setWordWrap(True)
        self.source.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        row.addWidget(self.source, 1)

        self.btn_reload = QtWidgets.QPushButton(i18n.t("changelog_reload"))
        self.btn_reload.clicked.connect(lambda: self._load(online=True))
        row.addWidget(self.btn_reload)

        self.btn_web = QtWidgets.QPushButton(i18n.t("changelog_open_web"))
        self.btn_web.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl(paths.APP_URL + self.WEB_PATH)))
        row.addWidget(self.btn_web)

        close = QtWidgets.QPushButton(i18n.t("close"))
        close.setObjectName("primary")
        close.clicked.connect(self.close)
        row.addWidget(close)
        root.addLayout(row)

        self._load(online=True)

    # -- Laden -------------------------------------------------------------

    def _load(self, online: bool) -> None:
        if self._loader is not None and self._loader.isRunning():
            return
        self.btn_reload.setEnabled(False)
        self.source.setText(i18n.t("changelog_loading"))
        # Solange nichts da ist, schon einmal die Datei von der Platte
        # zeigen: eine leere Flaeche waehrend des Wartens sieht kaputt aus.
        if not self.view.toPlainText():
            local = self._make_loader(False)._from_disk()
            if local:
                self.view.setMarkdown(local)

        self._loader = self._make_loader(online)
        self._loader.done.connect(self._show_text)
        self._loader.start()

    def _make_loader(self, online: bool) -> ChangelogLoader:
        return ChangelogLoader(online, self, urls=self._urls,
                               local=self._local)

    def _show_text(self, text: str, origin: str) -> None:
        self.btn_reload.setEnabled(True)
        if not text:
            self.view.setMarkdown(i18n.t(self.MISSING_KEY))
            self.source.setText(i18n.t("changelog_from_nowhere"))
            return

        self.view.setMarkdown(text)
        self.view.verticalScrollBar().setValue(0)
        self.source.setText(i18n.t("changelog_from_web") if origin == "online"
                            else i18n.t("changelog_from_disk"))

    def closeEvent(self, event) -> None:
        """Den Faden zu Ende laufen lassen, bevor das Fenster verschwindet.

        Ein noch laufender QThread, dessen Fenster geloescht wird, nimmt das
        Programm mit.
        """
        if self._loader is not None and self._loader.isRunning():
            self._loader.done.disconnect()
            self._loader.wait(int(ChangelogLoader.TIMEOUT * 1000) + 500)
        super().closeEvent(event)


class HighlightsDialog(ChangelogDialog):
    """Nur das Wichtigste je Version, aus HIGHLIGHTS.md.

    Der Changelog erklaert jede Aenderung ausfuehrlich — gut zum Nachlesen,
    zu lang, um schnell zu sehen, was neu ist. Die Highlights sind eine
    eigene, von Hand gepflegte Datei mit ein paar Zeilen pro Version.
    Laden, Rueckfall und Darstellung sind dieselben wie beim Changelog.
    """

    TITLE_KEY = "highlights_title"
    MISSING_KEY = "highlights_missing"
    WEB_PATH = "/blob/main/HIGHLIGHTS.md"

    @staticmethod
    def _urls():
        return paths.HIGHLIGHTS_URLS

    @staticmethod
    def _local():
        return paths.highlights_file()
