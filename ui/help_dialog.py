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

"""Nachschlagefenster."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from ui import helptext
from core import i18n
from ui.theming import COLORS as NORD


# ------------------------------------------------------- Nachschlagefenster

class HelpDialog(QtWidgets.QDialog):
    """Erklaert, was die Kennwerte bedeuten.

    Bewusst nicht modal: man schlaegt etwas nach, waehrend man aufnimmt,
    und nicht statt dessen.
    """

    def __init__(self, parent=None, topic: str | None = None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("help_title"))
        self.setMinimumSize(880, 620)
        self.resize(1000, 720)

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(10)

        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(i18n.t("help_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        root.addWidget(self.search)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(240)
        self.tree.currentItemChanged.connect(self._show_current)
        splitter.addWidget(self.tree)

        self.view = QtWidgets.QTextBrowser()
        self.view.setOpenExternalLinks(True)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 700])
        root.addWidget(splitter, 1)

        row = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel("")
        self.count_label.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        row.addWidget(self.count_label, 1)
        close = QtWidgets.QPushButton(i18n.t("close"))
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        root.addLayout(row)

        self._fill()
        self.show_topic(topic or helptext.TOPICS[0].key)

    # -- Inhalt ----------------------------------------------------------

    def _fill(self, needle: str = "") -> None:
        self.tree.clear()
        shown = 0
        for section in helptext.SECTIONS:
            matches = [t for t in helptext.topics_in(section) if t.matches(needle)]
            if not matches:
                continue
            head = QtWidgets.QTreeWidgetItem([helptext.section_title(section)])
            head.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            font = head.font(0)
            font.setBold(True)
            head.setFont(0, font)
            head.setForeground(0, QtGui.QColor(NORD["dim"]))
            self.tree.addTopLevelItem(head)
            for topic in matches:
                child = QtWidgets.QTreeWidgetItem([topic.localised_title()])
                child.setData(0, QtCore.Qt.ItemDataRole.UserRole, topic.key)
                head.addChild(child)
                shown += 1
            head.setExpanded(True)
        self.count_label.setText(
            i18n.t("help_count", shown=shown, total=len(helptext.TOPICS)))

    def _filter(self, needle: str) -> None:
        self._fill(needle)
        first = self._first_topic_item()
        if first is not None:
            self.tree.setCurrentItem(first)
        else:
            self.view.setHtml(self._wrap(f"<p>{i18n.t('help_no_match')}</p>"))

    def _first_topic_item(self):
        for i in range(self.tree.topLevelItemCount()):
            head = self.tree.topLevelItem(i)
            if head.childCount():
                return head.child(0)
        return None

    def show_topic(self, key: str) -> None:
        for i in range(self.tree.topLevelItemCount()):
            head = self.tree.topLevelItem(i)
            for j in range(head.childCount()):
                child = head.child(j)
                if child.data(0, QtCore.Qt.ItemDataRole.UserRole) == key:
                    self.tree.setCurrentItem(child)
                    return

    def _show_current(self, current, _previous=None) -> None:
        if current is None:
            return
        key = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not key:
            return
        topic = helptext.TOPIC_BY_KEY.get(key)
        if topic is None:
            return
        self.view.setHtml(self._wrap(
            f"<h2>{topic.localised_title()}</h2>{topic.localised_body()}"))
        self.view.verticalScrollBar().setValue(0)

    @staticmethod
    def _wrap(body: str) -> str:
        return f"""
<html><head><style>
body {{ color: {NORD['fg']}; font-size: 13px; }}
h2 {{ color: {NORD['accent']}; font-size: 17px; margin-bottom: 2px; }}
p {{ margin: 8px 0; line-height: 145%; }}
ul {{ margin: 6px 0; }}
li {{ margin: 4px 0; }}
b {{ color: {NORD['fg']}; }}
code {{ color: {NORD['accent']}; }}
</style></head><body>{body}</body></html>
"""
