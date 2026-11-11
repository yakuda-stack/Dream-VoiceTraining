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

"""Versionsschild unten rechts, Hintergrundpruefung und Update-Fenster."""

from __future__ import annotations

import threading

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from core import paths
from core import updates
from ui.theming import COLORS as NORD


class UpdateChecker(QtCore.QObject):
    """Fragt GitHub im Hintergrund; meldet sich nur bei einer neueren Version.

    Ein Daemon-Faden statt QThread: schliesst jemand das Fenster, waehrend
    die Anfrage noch laeuft, endet der Faden einfach mit dem Programm,
    statt das Beenden um bis zu sechs Sekunden aufzuhalten.
    """

    found = QtCore.Signal(object)

    def start(self) -> None:
        threading.Thread(target=self._run, name="update-check",
                         daemon=True).start()

    def _run(self) -> None:
        release = updates.fetch_latest()
        if release is None:
            debuglog.log.debug("update: keine Antwort")
            return
        if updates.is_newer(release.version):
            self.found.emit(release)


class VersionLabel(QtWidgets.QLabel):
    """Grau im Normalfall, gelb und klickbar, sobald es ein Update gibt."""

    clicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(f"v{paths.APP_VERSION}", parent)
        self.release: updates.Release | None = None
        self.refresh()

    def set_release(self, release: updates.Release | None) -> None:
        self.release = release
        self.refresh()

    def refresh(self) -> None:
        """Text und Farbe neu setzen, auch nach einem Design-Wechsel."""
        base = "font-size: 10px; padding: 0 8px;"
        if self.release is None:
            self.setText(f"v{paths.APP_VERSION}")
            self.setToolTip(paths.APP_NAME)
            self.setStyleSheet(f"color: {NORD['dim']}; {base}")
            self.unsetCursor()
            return
        self.setText(f"v{paths.APP_VERSION}  ·  ⬆ "
                     + i18n.t("update_label", version=self.release.version))
        self.setToolTip(i18n.t("update_tip", version=self.release.version))
        self.setStyleSheet(
            f"color: {NORD['yellow']}; font-weight: 600; {base}")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if self.release is not None and \
                event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


def _open(url: str) -> None:
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))


class UpdateDialog(QtWidgets.QDialog):
    """Was neu ist, und der passende Download fuer diese Installation."""

    def __init__(self, release: updates.Release, parent=None):
        super().__init__(parent)
        self.release = release
        self.setWindowTitle(i18n.t("update_title"))
        self.resize(620, 520)

        root = QtWidgets.QVBoxLayout(self)
        head = QtWidgets.QLabel(i18n.t(
            "update_head", new=release.version, old=paths.APP_VERSION))
        font = head.font()
        font.setPointSize(font.pointSize() + 3)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        head.setFont(font)
        head.setStyleSheet(f"color: {NORD['yellow']};")
        head.setWordWrap(True)
        root.addWidget(head)

        notes = QtWidgets.QTextBrowser()
        notes.setOpenExternalLinks(True)
        notes.setMarkdown(release.notes or i18n.t("update_no_notes"))
        root.addWidget(notes, 1)

        kind = updates.install_kind()
        hint = QtWidgets.QLabel(i18n.t(f"update_how_{kind}"))
        hint.setWordWrap(True)
        hint.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        hint.setStyleSheet(f"color: {NORD['dim']};")
        root.addWidget(hint)

        buttons = QtWidgets.QHBoxLayout()
        asset = updates.pick_asset(release, kind)
        self.btn_download = None
        if asset is not None:
            name, url = asset
            self.btn_download = QtWidgets.QPushButton(
                "⬇  " + i18n.t("update_download", name=name))
            self.btn_download.setObjectName("primary")
            self.btn_download.clicked.connect(lambda: _open(url))
            buttons.addWidget(self.btn_download)
        page = QtWidgets.QPushButton(i18n.t("update_release_page"))
        page.clicked.connect(lambda: _open(release.url))
        buttons.addWidget(page)
        buttons.addStretch(1)
        close = QtWidgets.QPushButton(i18n.t("close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        root.addLayout(buttons)


class UpdateAskDialog(QtWidgets.QDialog):
    """Einmalige Frage, ob nach Updates gesucht werden darf.

    Oben steht die Sprachauswahl: wer von einer aelteren Version kommt oder
    die Einfuehrung uebersprungen hat, soll die Frage in seiner Sprache lesen
    koennen. Ein Wechsel uebersetzt das Fenster an Ort und Stelle.
    """

    answered = QtCore.Signal(bool)
    language_chosen = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("update_ask")

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)
        # Umbrechende Labels melden ihre Hoehe erst nach dem Setzen des
        # Textes richtig; ohne feste Breite und diese Regel schneidet Qt sie ab.
        root.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

        row = QtWidgets.QHBoxLayout()
        self.language_label = QtWidgets.QLabel()
        self.language_box = QtWidgets.QComboBox()
        for code, name in i18n.available():
            self.language_box.addItem(name, code)
        self.language_box.setCurrentIndex(
            max(0, self.language_box.findData(i18n.LANG)))
        self.language_box.activated.connect(
            lambda _i: self.language_chosen.emit(
                self.language_box.currentData()))
        row.addWidget(self.language_label)
        row.addWidget(self.language_box)
        row.addStretch(1)
        root.addLayout(row)

        self.title = QtWidgets.QLabel()
        font = self.title.font()
        font.setPointSize(font.pointSize() + 3)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        self.title.setFont(font)
        root.addWidget(self.title)

        self.body = QtWidgets.QLabel()
        self.body.setWordWrap(True)
        self.body.setFixedWidth(500)
        root.addWidget(self.body)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.btn_no = QtWidgets.QPushButton()
        self.btn_no.clicked.connect(lambda: self._answer(False))
        self.btn_yes = QtWidgets.QPushButton()
        self.btn_yes.setObjectName("primary")
        self.btn_yes.setDefault(True)
        self.btn_yes.clicked.connect(lambda: self._answer(True))
        buttons.addWidget(self.btn_no)
        buttons.addWidget(self.btn_yes)
        root.addLayout(buttons)

        self.retranslate()

    def retranslate(self) -> None:
        self.setWindowTitle(i18n.t("update_ask_title"))
        self.language_label.setText(i18n.t("language_label"))
        self.title.setText(i18n.t("update_ask_title"))
        self.body.setText(i18n.t("update_ask_body"))
        self.btn_yes.setText(i18n.t("update_ask_yes"))
        self.btn_no.setText(i18n.t("update_ask_no"))
        index = self.language_box.findData(i18n.LANG)
        if index >= 0:
            self.language_box.setCurrentIndex(index)

    def _answer(self, allowed: bool) -> None:
        self.answered.emit(allowed)
        self.accept()
