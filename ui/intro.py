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

"""Einfuehrung beim ersten Start."""

from __future__ import annotations

import json

from PySide6 import QtCore, QtGui, QtWidgets

from core import i18n
from core import paths
from core import settings
from ui.theming import COLORS as NORD

from ui.links import project_links_box
from ui.spotlight import Spotlight


_SPOT_CACHE: dict | None = None


def _shot_spots() -> dict:
    """Markenstellen aus assets/intro/shots.json, einmal gelesen."""
    global _SPOT_CACHE
    if _SPOT_CACHE is None:
        _SPOT_CACHE = {}
        path = paths.intro_shot("shots.json")
        if path is not None:
            try:
                _SPOT_CACHE = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                _SPOT_CACHE = {}
    return _SPOT_CACHE


class ShotView(QtWidgets.QLabel):
    """Bildschirmfoto mit Marken an festen Stellen.

    Die Stellen stehen als Anteil der Bildgroesse in den Seitendaten, damit
    ein neu aufgenommenes Foto nur ausgetauscht werden muss.
    """

    def __init__(self, pixmap: QtGui.QPixmap, spots, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.setStyleSheet(f"border: 1px solid {NORD['bg3']};")
        self.spots = []
        for share_x, share_y in spots:
            spot = Spotlight(self)
            spot.place(QtCore.QPoint(round(share_x * pixmap.width()),
                                     round(share_y * pixmap.height())))
            self.spots.append(spot)


# ---------------------------------------------------------- Erster Start

class IntroDialog(QtWidgets.QDialog):
    """Sprachwahl und kurze Einfuehrung beim ersten Start.

    Laesst sich jederzeit ueber die Einstellungen erneut aufrufen. Nicht
    modal, damit man nebenher schon das Mikrofon einstellen kann — genau
    darum geht es auf der zweiten Seite.
    """

    language_chosen = QtCore.Signal(str)
    finished_intro = QtCore.Signal()
    # Welches Bedienelement im Hauptfenster gerade markiert werden soll,
    # leer heisst keins. Das Hauptfenster kennt seine Knoepfe selbst.
    spotlight = QtCore.Signal(str)

    PAGES = [
        ("intro_level_title", "intro_level_body"),
        ("intro_record_title", "intro_record_body"),
        ("intro_first_title", "intro_first_body"),
        ("intro_help_title", "intro_help_body"),
        ("intro_sessions_title", "intro_sessions_body"),
        ("intro_advanced_title", "intro_advanced_body"),
        ("intro_columns_title", "intro_columns_body"),
        ("intro_settings_title", "intro_settings_body"),
        ("intro_safety_title", "intro_safety_body"),
    ]

    # Bildschirmfoto je Seite. Die Dateien heissen <name>.<sprache>.png und
    # entstehen mit packaging/make-intro-shots.py aus der echten Oberflaeche;
    # die Stellen der Marken stehen daneben in shots.json.
    SHOTS = {
        "intro_help_body": "detail",
        "intro_sessions_body": "sessions",
        "intro_advanced_body": "advanced",
    }

    # Falls shots.json fehlt: grobe Stellen, damit die Marken nicht in der
    # Ecke kleben.
    FALLBACK_SPOTS = {
        "detail": [[0.033, 0.236]],
        "sessions": [[0.112, 0.143], [0.835, 0.565]],
        "advanced": [[0.107, 0.052], [0.300, 0.240], [0.030, 0.932]],
    }

    # Echtes Bedienelement im Hauptfenster, auf das die Seite zeigt.
    POINTS_AT = {
        "intro_level_body": "microphone",
        "intro_record_body": "type",
        "intro_first_body": "type",
        "intro_help_body": "help",
        "intro_sessions_body": "sessions",
        "intro_columns_body": "filter",
        "intro_settings_body": "settings",
    }

    # Seite, die die Projektverweise mitbringt.
    LINK_PAGE = "intro_safety_body"

    # Lesbare Zeilenlaenge, unabhaengig von der Fensterbreite.
    TEXT_WIDTH = 700
    # Rand um den Inhalt: Schrittzeile, Knopfreihe, Raender, Bildlaufleiste.
    CHROME_H = 120
    CHROME_W = 60

    def __init__(self, parent=None, ask_language: bool = True):
        super().__init__(parent)
        self.ask_language = ask_language
        self.preferred_size = QtCore.QSize(0, 0)
        self.setWindowTitle(i18n.t("intro_title"))
        # Klein genug fuer eine reine Textseite; die tatsaechliche Groesse
        # richtet sich in _fit_to_page nach dem, was auf der Seite steht.
        self.setMinimumSize(560, 340)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(12)

        self.step_label = QtWidgets.QLabel("")
        self.step_label.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 10px; letter-spacing: 1px;")
        root.addWidget(self.step_label)

        self.stack = QtWidgets.QStackedWidget()
        if ask_language:
            self.stack.addWidget(self._language_page())
        for title_key, body_key in self.PAGES:
            self.stack.addWidget(self._text_page(title_key, body_key))
        # Ohne das richtet sich der Stapel nach seiner groessten Seite und
        # eine Textseite bekaeme das Fenster der Bildseite.
        for index in range(self.stack.count()):
            self.stack.widget(index).setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Ignored,
                QtWidgets.QSizePolicy.Policy.Ignored)
        root.addWidget(self.stack, 1)

        row = QtWidgets.QHBoxLayout()
        self.btn_skip = QtWidgets.QPushButton(i18n.t("intro_skip"))
        self.btn_skip.clicked.connect(self._finish)
        self.btn_back = QtWidgets.QPushButton(i18n.t("intro_back"))
        self.btn_back.clicked.connect(self._back)
        self.btn_next = QtWidgets.QPushButton(i18n.t("intro_next"))
        self.btn_next.setObjectName("primary")
        self.btn_next.setMinimumWidth(130)
        self.btn_next.clicked.connect(self._next)
        row.addWidget(self.btn_skip)
        row.addStretch(1)
        row.addWidget(self.btn_back)
        row.addWidget(self.btn_next)
        root.addLayout(row)

        self._update()

    # -- Seiten ----------------------------------------------------------

    def _language_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setSpacing(16)
        lay.addStretch(1)

        icon_path = paths.icon_file()
        if icon_path is not None:
            icon = QtWidgets.QLabel()
            icon.setPixmap(QtGui.QIcon(str(icon_path)).pixmap(96, 96))
            icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(icon)

        name = QtWidgets.QLabel(paths.APP_NAME)
        font = name.font()
        font.setPointSize(font.pointSize() + 8)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        name.setFont(font)
        name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name)

        self.language_title = QtWidgets.QLabel(i18n.t("intro_language"))
        self.language_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.language_title)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        self.language_box = QtWidgets.QComboBox()
        self.language_box.setMinimumSize(240, 40)
        for code, label in i18n.available():
            self.language_box.addItem(label, code)
        self.language_box.setCurrentIndex(
            max(0, self.language_box.findData(i18n.LANG)))
        self.language_box.activated.connect(
            lambda _i: self._pick_language(self.language_box.currentData()))
        row.addWidget(self.language_box)
        row.addStretch(1)
        lay.addLayout(row)

        self.language_note = QtWidgets.QLabel(i18n.t("intro_language_body"))
        self.language_note.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.language_note.setWordWrap(True)
        self.language_note.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 11px;")
        lay.addWidget(self.language_note)
        lay.addStretch(1)
        return page

    def _text_page(self, title_key: str, body_key: str) -> QtWidgets.QWidget:
        """Ueberschrift, Text und — wo vorhanden — ein Bildschirmfoto.

        Der Text steht in einem Label statt in einem Textfenster, damit das
        Foto darunter im selben Bildlauf haengt und nicht in einem zweiten.
        """
        page = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        area = QtWidgets.QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(area)

        inner = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 10, 0)
        lay.setSpacing(10)
        area.setWidget(inner)

        # Text und Ueberschrift stehen in einer eigenen Spalte: so bleibt die
        # Zeilenlaenge lesbar, auch wenn darunter ein breites Bild haengt.
        # Eine Breitenbegrenzung am Label selbst reicht nicht — die Hoehe
        # wuerde dann fuer die volle Fensterbreite berechnet und der Text
        # unten abgeschnitten.
        column = QtWidgets.QWidget()
        column.setMaximumWidth(self.TEXT_WIDTH)
        text_lay = QtWidgets.QVBoxLayout(column)
        text_lay.setContentsMargins(0, 0, 0, 0)
        text_lay.setSpacing(10)
        lay.addWidget(column)

        title = QtWidgets.QLabel(i18n.t(title_key))
        title.setObjectName("introtitle")
        font = title.font()
        font.setPointSize(font.pointSize() + 5)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        title.setFont(font)
        title.setStyleSheet(f"color: {NORD['accent']};")
        title.setWordWrap(True)
        text_lay.addWidget(title)

        body = QtWidgets.QLabel(i18n.t(body_key))
        body.setObjectName("introbody")
        body.setTextFormat(QtCore.Qt.TextFormat.RichText)
        body.setWordWrap(True)
        body.setOpenExternalLinks(True)
        body.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        body.setStyleSheet(f"color: {NORD['fg']}; font-size: 13px;")
        body.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft
                          | QtCore.Qt.AlignmentFlag.AlignTop)
        text_lay.addWidget(body)

        shot = self._shot(body_key)
        if shot is not None:
            lay.addWidget(shot, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        # Auf der letzten Seite: wohin man sich wenden kann, wenn etwas
        # klemmt. Am Ende der Einfuehrung gelesen, nicht in den
        # Einstellungen gesucht.
        if body_key == self.LINK_PAGE:
            links = project_links_box()
            links.setMaximumWidth(self.TEXT_WIDTH)
            lay.addWidget(links)
        lay.addStretch(1)

        page.setProperty("title_key", title_key)
        page.setProperty("body_key", body_key)
        return page

    def _shot(self, body_key: str) -> QtWidgets.QWidget | None:
        """Bildschirmfoto mit Marken, sofern die Datei mitgeliefert wurde.

        Fehlt sie — etwa in einem Paket, das nur die .py-Dateien mitnimmt —,
        bleibt die Seite ohne Bild lesbar, statt beim Start zu scheitern.
        """
        name = self.SHOTS.get(body_key)
        if name is None:
            return None
        # Erst die aktuelle Sprache, dann Englisch, dann irgendeine: ein Foto
        # in der falschen Sprache ist besser als gar keins.
        path = None
        for candidate in (f"{name}.{i18n.LANG}.png", f"{name}.en.png",
                          f"{name}.de.png", f"{name}.png"):
            path = paths.intro_shot(candidate)
            if path is not None:
                break
        if path is None:
            return None
        pixmap = QtGui.QPixmap(str(path))
        if pixmap.isNull():
            return None
        return ShotView(pixmap, self._spots(name))

    def _spots(self, name: str) -> list:
        by_language = _shot_spots().get(name, {})
        return (by_language.get(i18n.LANG) or by_language.get("en")
                or self.FALLBACK_SPOTS.get(name, []))

    # -- Ablauf ----------------------------------------------------------

    def _pick_language(self, code: str) -> None:
        i18n.set_language(code)
        settings.set_language(code)
        index = self.language_box.findData(code)
        if index >= 0 and index != self.language_box.currentIndex():
            self.language_box.setCurrentIndex(index)
        self.language_chosen.emit(code)
        self._retranslate()

        # Die Sprachwahl ist die ganze Aufgabe dieser Seite. Wer sie
        # getroffen hat, will nicht noch auf "Weiter" drucken — der kurze
        # Verzug laesst den Knopf einmal aufleuchten, damit die Auswahl
        # sichtbar ankommt.
        if self.stack.currentIndex() == 0:
            QtCore.QTimer.singleShot(220, self._advance_from_language)

    def _advance_from_language(self) -> None:
        if self.stack.currentIndex() == 0 and self.isVisible():
            self._next()

    def _retranslate(self) -> None:
        """Ohne Neuaufbau: nur die sichtbaren Texte tauschen."""
        self.setWindowTitle(i18n.t("intro_title"))
        self.btn_skip.setText(i18n.t("intro_skip"))
        self.btn_back.setText(i18n.t("intro_back"))
        if self.ask_language:
            self.language_title.setText(i18n.t("intro_language"))
            self.language_note.setText(i18n.t("intro_language_body"))

        offset = 1 if self.ask_language else 0
        for index, (title_key, body_key) in enumerate(self.PAGES):
            page = self.stack.widget(index + offset)
            title = page.findChild(QtWidgets.QLabel, "introtitle")
            body = page.findChild(QtWidgets.QLabel, "introbody")
            if title is not None:
                title.setText(i18n.t(title_key))
            if body is not None:
                body.setText(i18n.t(body_key))

            # Das Foto zeigt eine Oberflaeche in der alten Sprache, sobald
            # umgeschaltet wird — also gegen das der neuen tauschen.
            old_links = page.findChild(QtWidgets.QGroupBox, "projectlinks")
            if old_links is not None:
                layout = old_links.parentWidget().layout()
                if layout is not None:
                    fresh = project_links_box()
                    fresh.setMaximumWidth(self.TEXT_WIDTH)
                    layout.replaceWidget(old_links, fresh)
                    old_links.setParent(None)
                    old_links.deleteLater()

            old_shot = page.findChild(ShotView)
            if old_shot is not None:
                new_shot = self._shot(body_key)
                layout = old_shot.parentWidget().layout()
                if new_shot is not None and layout is not None:
                    layout.replaceWidget(old_shot, new_shot)
                    old_shot.setParent(None)
                    old_shot.deleteLater()
        self._update()

    def _update(self) -> None:
        index = self.stack.currentIndex()
        total = self.stack.count()
        self.step_label.setText(
            i18n.t("intro_step", step=index + 1, total=total).upper())
        self.btn_back.setEnabled(index > 0)
        last = index == total - 1
        self.btn_next.setText(
            i18n.t("intro_done") if last else i18n.t("intro_next"))
        self.btn_skip.setVisible(not last)
        # Das Stylesheet muss nach einer Namensaenderung neu greifen.
        self.btn_next.setStyleSheet(self.btn_next.styleSheet())

        page = self.stack.currentWidget()
        body_key = page.property("body_key") if page is not None else None
        self.spotlight.emit(self.POINTS_AT.get(body_key or "", ""))
        self._fit_to_page()

    # -- Groesse ---------------------------------------------------------

    def _fit_to_page(self) -> None:
        """Das Fenster an die aktuelle Seite anpassen.

        Eine reine Textseite in einem Fenster, das fuer ein Bildschirmfoto
        gebaut wurde, ist zu drei Vierteln leer. Statt einer festen Groesse
        fuer alle rechnet jede Seite ihre eigene aus.
        """
        page = self.stack.currentWidget()
        if page is None:
            return

        shot = page.findChild(ShotView)
        width = self.TEXT_WIDTH if shot is None else max(self.TEXT_WIDTH,
                                                         shot.width())
        width += self.CHROME_W

        inner = width - self.CHROME_W
        height = self.CHROME_H
        for name in ("introtitle", "introbody"):
            label = page.findChild(QtWidgets.QLabel, name)
            if label is not None:
                height += self._text_height(
                    label, min(inner, self.TEXT_WIDTH)) + 10
        if shot is not None:
            height += shot.height() + 10
        links = page.findChild(QtWidgets.QGroupBox, "projectlinks")
        if links is not None:
            height += links.sizeHint().height() + 10
        if not self.PAGES or page.property("body_key") is None:
            # Die Sprachseite lebt von ihrem Weissraum.
            width, height = self.TEXT_WIDTH, 520

        width = max(width, self.minimumWidth())
        height = max(height, self.minimumHeight())
        # Was die Seite braucht, unabhaengig vom Bildschirm — daran haengt
        # der Test, der prueft, dass Textseiten kleiner ausfallen.
        self.preferred_size = QtCore.QSize(width, height)

        screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
        if screen is not None:
            free = screen.availableGeometry()
            width = min(width, int(free.width() * 0.95))
            height = min(height, int(free.height() * 0.92))
        self.resize(width, height)

    @staticmethod
    def _text_height(label: QtWidgets.QLabel, width: int) -> int:
        """Hoehe eines umgebrochenen Labels.

        heightForWidth() liefert bei formatiertem Text mit Aufzaehlungen zu
        kleine Werte, deshalb wird derselbe Text hier einmal richtig
        gesetzt und ausgemessen.
        """
        doc = QtGui.QTextDocument()
        doc.setDefaultFont(label.font())
        doc.setHtml(label.text())
        doc.setTextWidth(max(200, width))
        return int(doc.size().height())

    def _next(self) -> None:
        if self.stack.currentIndex() >= self.stack.count() - 1:
            self._finish()
            return
        self.stack.setCurrentIndex(self.stack.currentIndex() + 1)
        self._update()

    def _back(self) -> None:
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))
        self._update()

    def _finish(self) -> None:
        settings.set_intro_done(True)
        self.spotlight.emit("")
        self.finished_intro.emit()
        self.accept()

    def closeEvent(self, event):
        # Auch das Wegklicken zaehlt als gesehen, sonst kommt es bei jedem
        # Start wieder.
        settings.set_intro_done(True)
        self.spotlight.emit("")
        super().closeEvent(event)
