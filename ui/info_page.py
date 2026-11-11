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

"""Info-Seite der Einstellungen."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from core import paths
from core import settings
from core import storage
from ui.theming import COLORS as NORD

from ui.links import (doc_button, project_links_box)


# ------------------------------------------------------------- Infofenster

class InfoPage(QtWidgets.QWidget):
    """Version, Lizenz, Links und der gesundheitliche Hinweis.

    Sitzt als Reiter in den Einstellungen statt in einem eigenen Fenster:
    es ist Nachschlagestoff, kein Dialog, der etwas von einem will.

    Verbindungen nach draußen: die Update-Prüfung beim Start (nur nach
    Zustimmung, hier änderbar) und der Changelog, wenn jemand den Knopf drückt. Gesendet
    wird dabei nichts außer der Anfrage selbst.
    """

    intro_requested = QtCore.Signal()
    debug_requested = QtCore.Signal()
    changelog_requested = QtCore.Signal()
    highlights_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(14)
        root.addLayout(self._build_head())

        # Ganz oben, weil es die Handlung ist und nicht die Lektüre.
        actions = QtWidgets.QHBoxLayout()
        self.btn_intro = QtWidgets.QPushButton("▶  " + i18n.t("intro_restart"))
        self.btn_intro.setObjectName("primary")
        self.btn_intro.clicked.connect(self.intro_requested)
        self.btn_debug = QtWidgets.QPushButton("🐞  " + i18n.t("debug"))
        self.btn_debug.clicked.connect(self.debug_requested)
        # Changelog und Highlights sitzen seit 1.1.7 als zweite Zeile unter
        # den Projektverweisen (siehe _build_body): beides sind Dinge, die
        # man nachschlaegt, keine Handlungen wie die Knoepfe hier oben.
        self.btn_changelog = doc_button("\U0001F5D2", "changelog",
                                        "btn_link_changelog")
        self.btn_changelog.clicked.connect(self.changelog_requested)
        self.btn_highlights = doc_button("\u2728", "highlights",
                                         "btn_link_highlights")
        self.btn_highlights.clicked.connect(self.highlights_requested)
        copy = QtWidgets.QPushButton(i18n.t("copy_env"))
        copy.clicked.connect(self._copy_environment)
        folder = QtWidgets.QPushButton(i18n.t("open_folder"))
        folder.clicked.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(str(paths.CONFIG_DIR))))
        for widget in (self.btn_intro, self.btn_debug, copy, folder):
            actions.addWidget(widget)
        actions.addStretch(1)
        root.addLayout(actions)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._build_body())
        root.addWidget(scroll, 1)

        self.update_debug_badge()

    def update_debug_badge(self) -> None:
        errors = sum(1 for record in debuglog.RECORDS
                     if record[1] in ("ERROR", "CRITICAL"))
        self.btn_debug.setText("🐞  " + i18n.t("debug")
                               + (f"  ({errors})" if errors else ""))
        self.btn_debug.setStyleSheet(
            f"color: {NORD['red']};" if errors else "")

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
        version.setStyleSheet(f"color: {NORD['dim']};")
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

        # Frueher stand der Stil hier direkt im f-String und enthielt ein
        # verirrtes style=f"..." — die Angabe war damit ungueltig und die
        # Verweise blieben ungefaerbt. Jetzt baut das eine Stelle.
        lay.addWidget(project_links_box(
            extra=(self.btn_changelog, self.btn_highlights)))

        lay.addWidget(self._section(i18n.t("about_license_head"),
                                    i18n.t("about_license")))
        lay.addWidget(self._section(i18n.t("about_privacy_head"),
                                    i18n.t("about_privacy")))
        self.chk_updates = QtWidgets.QCheckBox(i18n.t("update_check_option"))
        self.chk_updates.setChecked(bool(settings.get_update_check()))
        self.chk_updates.toggled.connect(settings.set_update_check)
        lay.addWidget(self.chk_updates)
        lay.addWidget(self._section(
            i18n.t("about_paths"),
            f"{paths.CONFIG_PATH}\n{storage.root()}", mono=True))

        note = QtWidgets.QLabel(i18n.t("about_health"))
        note.setWordWrap(True)
        note.setStyleSheet(
            f"color: {NORD['yellow']}; border: 1px solid {NORD['border']};"
            " border-radius: 8px; padding: 10px;")
        lay.addWidget(note)

        citation = QtWidgets.QLabel(i18n.t("about_citation"))
        citation.setWordWrap(True)
        citation.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
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
            label.setStyleSheet(f"color: {NORD['dim']};")
        lay.addWidget(label)
        return box

    def _copy_environment(self) -> None:
        QtWidgets.QApplication.clipboard().setText(
            "\n".join(debuglog.environment()))
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), i18n.t("copied"), self)
