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

"""Projekt-Links (GitHub, Discord, Ko-fi) und ihre Knoepfe."""

from __future__ import annotations

from typing import NamedTuple

from PySide6 import QtCore, QtGui, QtWidgets

from core import i18n
from core import paths


class ProjectLink(NamedTuple):
    key: str        # Beschriftung in i18n
    url: str        # Ziel aus paths.py
    emoji: str      # Zeichen vor der Beschriftung
    name: str       # objectName, an dem die Farbe in theming.py haengt


# Die drei Adressen des Projekts an einer Stelle: Infoseite und Einfuehrung
# zeigen dieselben, und paths.py haelt sie.
PROJECT_LINKS = (
    ProjectLink("about_source", paths.APP_URL, "\U0001F4E6", "btn_link_github"),
    ProjectLink("about_discord", paths.DISCORD_URL, "\U0001F4AC",
                "btn_link_discord"),
    ProjectLink("about_kofi", paths.KOFI_URL, "\u2615", "btn_link_kofi"),
)

# Schriften, die farbige Emoji mitbringen. Die Liste deckt Windows, macOS
# und die ueblichen Linux-Desktops ab.
EMOJI_FONTS = ("Noto Color Emoji", "Segoe UI Emoji", "Apple Color Emoji",
               "Noto Emoji", "Twemoji", "JoyPixels", "EmojiOne Color")

_EMOJI_OK: bool | None = None


def emoji_available() -> bool:
    """Ob das System ueberhaupt eine Emoji-Schrift hat.

    Auf einem eingerichteten Desktop ja. In einer schlanken Umgebung — ein
    AppImage auf einem Grundsystem ohne Schriftpakete, ein Container —
    nicht, und dann stuende auf dem Knopf ein leeres Kaestchen statt eines
    Zeichens. In dem Fall bleibt die Beschriftung ohne Emoji: schlichter,
    aber lesbar.

    Einmal geprueft und gemerkt; Schriften kommen zur Laufzeit nicht dazu.
    """
    global _EMOJI_OK
    if _EMOJI_OK is None:
        families = {name.lower() for name in QtGui.QFontDatabase.families()}
        _EMOJI_OK = any(font.lower() in families for font in EMOJI_FONTS)
    return _EMOJI_OK


def link_button(link: ProjectLink, parent=None) -> QtWidgets.QPushButton:
    """Ein Knopf je Adresse, Emoji voran.

    Die Adresse stand frueher klein unter dem Verweis, damit sichtbar ist,
    wohin ein Klick fuehrt, bevor man ihn macht. Auf einem Knopf ist dafuer
    kein Platz — sie steht jetzt im Tooltip und in der Statuszeile. Die
    Absicht bleibt, der Platzbedarf nicht.
    """
    label = i18n.t(link.key)
    button = QtWidgets.QPushButton(
        f"{link.emoji}  {label}" if emoji_available() else label, parent)
    button.setObjectName(link.name)
    button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    button.setToolTip(link.url)
    button.setStatusTip(link.url)
    url = link.url
    button.clicked.connect(
        lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)))
    return button


def doc_button(emoji: str, key: str, name: str,
               parent=None) -> QtWidgets.QPushButton:
    """Knopf fuer Changelog und Highlights, im Stil der Projektverweise."""
    label = i18n.t(key)
    button = QtWidgets.QPushButton(
        f"{emoji}  {label}" if emoji_available() else label, parent)
    button.setObjectName(name)
    button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    return button


def project_links_box(extra=()) -> QtWidgets.QGroupBox:
    """Die drei Verweise als Reihe, nicht als Liste.

    Untereinander mit der Adresse darunter nahmen sie sechs Zeilen ein und
    sahen aus wie ein Textblock, den man liest. Es sind drei Knoepfe, die
    man drueckt.

    ``extra`` kommt als zweite Zeile darunter — auf der Infoseite Changelog
    und Highlights. Die Einfuehrung gibt nichts mit und zeigt nur die Links.
    """
    box = QtWidgets.QGroupBox(i18n.t("about_links"))
    box.setObjectName("projectlinks")
    outer = QtWidgets.QVBoxLayout(box)
    outer.setSpacing(8)
    rows = [[link_button(link) for link in PROJECT_LINKS]]
    if extra:
        rows.append(list(extra))
    for widgets in rows:
        lay = QtWidgets.QHBoxLayout()
        lay.setSpacing(8)
        for widget in widgets:
            lay.addWidget(widget)
        # Der Dehner haelt die Knoepfe links zusammen, statt sie ueber die
        # ganze Breite der Infoseite auseinanderzuziehen.
        lay.addStretch(1)
        outer.addLayout(lay)
    return box
