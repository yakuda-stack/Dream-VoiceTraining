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

"""Reiter Optionen: Speicherort und Namensschema aus Bausteinen."""

from __future__ import annotations

import os

from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from core import i18n
from core import naming
from core import rectypes
from core import settings
from core import storage
from ui import theming
from ui.theming import COLORS as NORD


# ---------------------------------------------- Speicherort und Namen

# Farbe je Baustein. Aus den Rollen des Farbschemas, damit die Marken in
# der Vorschau ein Themenwechsel mitnimmt statt sie fest einzubrennen.
PART_ROLES = {
    "prefix": "purple", "suffix": "purple", "text": "purple",
    "year": "accent", "month": "accent", "day": "accent",
    "week": "accent", "weekrange": "accent", "date": "accent",
    "time": "green",
    "type": "yellow",
    "counter": "red",
}

# Bausteine mit einem ausfuehrlichen Hinweis. Der steht als Tooltip an
# einem kleinen (i) statt als grauer Absatz unter dem Feld: neun Absaetze
# untereinander erklaeren zwar alles, aber man sieht die Liste nicht mehr.
PART_TIPS = {
    "prefix": "opt_text_hint", "suffix": "opt_text_hint",
    "week": "part_week_tip", "time": "opt_seconds_hint",
    "type": "opt_type_hint", "counter": "opt_counter_hint",
}


def info_icon(tip: str) -> QtWidgets.QLabel:
    """Ein kleines (i), das seinen Text erst beim Draufzeigen hergibt."""
    label = QtWidgets.QLabel("ⓘ")
    label.setToolTip(tip)
    label.setCursor(QtCore.Qt.CursorShape.WhatsThisCursor)
    label.setStyleSheet(f"color: {NORD['dim']}; font-size: 13px;")
    return label


class PartRow(QtWidgets.QFrame):
    """Eine Zeile der Baustein-Liste.

    Oben Griff, Haken, Name, Wert und das (i); darunter bei Bedarf eine
    Nebenzeile mit den Einstellungen, die nur diesen Baustein betreffen.
    Die Nebenzeile ist nur zu sehen, wenn der Baustein an ist — Sekunden
    einzustellen, waehrend die Uhrzeit gar nicht im Namen steht, waere eine
    Frage ohne Wirkung.
    """

    changed = QtCore.Signal()

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("partRow")

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(2)

        line = QtWidgets.QHBoxLayout()
        line.setSpacing(8)

        # Sechs Punkte als Griff. Der Mauszeiger wechselt darueber, damit
        # niemand raten muss, ob sich die Zeile ziehen laesst.
        self.grip = QtWidgets.QLabel("⋮⋮")
        self.grip.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
        self.grip.setToolTip(i18n.t("opt_drag_tip"))
        self.grip.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 15px; letter-spacing: -3px;")
        line.addWidget(self.grip)

        self.check = QtWidgets.QCheckBox()
        self.check.toggled.connect(self._toggled)
        line.addWidget(self.check)

        self.name = QtWidgets.QLabel(i18n.t(f"part_{key}"))
        self.name.setMinimumWidth(130)
        line.addWidget(self.name)

        self.inline: QtWidgets.QWidget | None = None
        self.badge = QtWidgets.QLabel("")
        self.badge.setTextFormat(QtCore.Qt.TextFormat.RichText)
        line.addWidget(self.badge)
        line.addStretch(1)

        tip = PART_TIPS.get(key)
        self.info = info_icon(i18n.t(tip)) if tip else None
        if self.info is not None:
            line.addWidget(self.info)
        outer.addLayout(line)

        self._line = line
        self.sub = QtWidgets.QWidget()
        sub_lay = QtWidgets.QHBoxLayout(self.sub)
        sub_lay.setContentsMargins(46, 0, 0, 2)
        sub_lay.setSpacing(8)
        self._sub_lay = sub_lay
        self.sub.hide()
        outer.addWidget(self.sub)

    # -- Bestueckung -------------------------------------------------------

    def set_inline(self, widget: QtWidgets.QWidget) -> None:
        """Ein Eingabefeld mitten in die Zeile, statt in eine eigene Sektion."""
        self.inline = widget
        self._line.insertWidget(3, widget, 1)

    def add_sub(self, *widgets: QtWidgets.QWidget) -> None:
        for widget in widgets:
            self._sub_lay.addWidget(widget)
        self._sub_lay.addStretch(1)

    def _toggled(self) -> None:
        self._update_sub()
        self.changed.emit()

    def _update_sub(self) -> None:
        has_sub = self._sub_lay.count() > 1
        self.sub.setVisible(has_sub and self.check.isChecked())

    # -- Zustand -----------------------------------------------------------

    def set_checked(self, on: bool) -> None:
        self.check.setChecked(bool(on))
        self._update_sub()

    def is_checked(self) -> bool:
        return self.check.isChecked()

    def set_value(self, value: str) -> None:
        """Zeigen, was der Baustein gerade beitraegt — auch abgeschaltet.

        Sonst muesste man einen Baustein erst einschalten, um zu sehen, was
        er tut, und wieder aus, wenn es doch nicht das war.
        """
        if not value:
            self.badge.setText(f"<span style='color:{NORD['dim']};'>—</span>")
            return
        colour = NORD[PART_ROLES.get(self.key, "accent")]
        self.badge.setText(badge_html(value, colour))

    def set_selected(self, on: bool) -> None:
        edge = NORD["accent"] if on else "transparent"
        self.setStyleSheet(
            f"QFrame#partRow {{ border: 1px solid {edge};"
            f" border-radius: 6px; }}")


def badge_html(text: str, colour: str) -> str:
    """Ein farbiges Kaestchen um einen Textbaustein.

    Qt kann in Rich Text kein padding an einem span, also uebernehmen
    geschuetzte Leerzeichen die Luft links und rechts.
    """
    ink = theming.contrast_text(colour)
    text = text.replace("&", "&amp;").replace("<", "&lt;")
    return (f"<span style='background-color:{colour}; color:{ink};"
            f" font-family:monospace;'>&nbsp;{text}&nbsp;</span>")


class PartList(QtWidgets.QWidget):
    """Die Bausteine in ihrer Reihenfolge, mit der Maus umsortierbar.

    Bewusst kein QListWidget: dessen internes Verschieben zerstoert die
    Widgets in den Zeilen, und in den Zeilen stehen hier Eingabefelder.
    Also eigene Zeilen in einem Layout und das Ziehen selbst gemacht — der
    Griff nimmt die Maus, und beim Bewegen tauscht die Zeile ihren Platz.
    """

    changed = QtCore.Signal()
    reordered = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[PartRow] = []
        self._current = 0
        self._dragging: PartRow | None = None

        self._lay = QtWidgets.QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(2)

    # -- Zeilen ------------------------------------------------------------

    def add_row(self, row: PartRow) -> None:
        row.changed.connect(self.changed)
        row.grip.installEventFilter(self)
        self._rows.append(row)
        self._lay.addWidget(row)

    def rows(self) -> list[PartRow]:
        return list(self._rows)

    def row_for(self, key: str) -> PartRow | None:
        for row in self._rows:
            if row.key == key:
                return row
        return None

    def order(self) -> list[str]:
        return [row.key for row in self._rows]

    def set_order(self, keys: list[str]) -> None:
        ordered = [row for key in keys if (row := self.row_for(key))]
        ordered += [row for row in self._rows if row not in ordered]
        for index, row in enumerate(ordered):
            self._lay.insertWidget(index, row)
        self._rows = ordered
        self._show_selection()

    # -- Auswahl (die Pfeilknoepfe brauchen eine) --------------------------

    def currentRow(self) -> int:
        return self._current

    def setCurrentRow(self, index: int) -> None:
        if 0 <= index < len(self._rows):
            self._current = index
            self._show_selection()

    def _show_selection(self) -> None:
        for index, row in enumerate(self._rows):
            row.set_selected(index == self._current)

    def move(self, index: int, target: int) -> bool:
        if not (0 <= index < len(self._rows) and 0 <= target < len(self._rows)):
            return False
        if index == target:
            return False
        row = self._rows.pop(index)
        self._rows.insert(target, row)
        self._lay.insertWidget(target, row)
        self._current = target
        self._show_selection()
        return True

    # -- Ziehen ------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:
        """Der Griff hat die Maus, also kommen die Bewegungen hier an."""
        kind = event.type()
        if kind == QtCore.QEvent.Type.MouseButtonPress:
            self._dragging = obj.parentWidget()
            if self._dragging in self._rows:
                self.setCurrentRow(self._rows.index(self._dragging))
            return False
        if kind == QtCore.QEvent.Type.MouseMove and self._dragging is not None:
            self._drag_to(obj.mapTo(self, event.position().toPoint()).y())
            return False
        if kind == QtCore.QEvent.Type.MouseButtonRelease and self._dragging:
            self._dragging = None
            self.reordered.emit()
            self.changed.emit()
            return False
        return super().eventFilter(obj, event)

    def _drag_to(self, y: int) -> None:
        """Die gezogene Zeile dorthin setzen, wo die Maus gerade steht.

        Gesucht wird die Einfuegestelle: die erste Zeile, deren Mitte unter
        dem Mauszeiger liegt. Ein Sprung ueber mehrere Zeilen ist damit in
        einem Zug erledigt — schrittweises Tauschen mit dem Nachbarn haengt
        daran, dass Qt die Groessen zwischendurch neu rechnet, und das tut
        es waehrend eines Zuges nicht zuverlaessig.
        """
        row = self._dragging
        if row not in self._rows:
            return

        index = self._rows.index(row)
        target = len(self._rows) - 1
        for position, other in enumerate(self._rows):
            if y < other.geometry().center().y():
                target = position
                break
        if target != index:
            self.move(index, target)


class OptionsPage(QtWidgets.QWidget):
    """Aufnahmeordner, Unterordner und der Aufbau des Dateinamens.

    Frueher ein eigenes Fenster, das beim Klick auf "Ordner auswaehlen"
    aufging und erst einmal nach dem Schema fragte, obwohl jemand nur einen
    Ordner suchen wollte. Jetzt ein Reiter in den Einstellungen: wer nur den
    Ordner wechseln will, bekommt den Dateidialog des Systems und sonst
    nichts, und wer am Schema schrauben will, findet es dort, wo die
    anderen Einstellungen auch stehen.

    Zwei Spalten, damit nichts unter den unteren Rand rutscht: links, was
    den Namen zusammensetzt, rechts, was mit vorhandenen Dateien passiert.
    Die Vorschau steht ueber beiden — sie gehoert zu allem.

    Sie rechnet bei jeder Aenderung neu und benutzt dabei peek_counter(),
    dreht den Zaehler also nicht weiter. Sonst stuende er nach einer Minute
    Herumprobieren bei 50.
    """

    changed = QtCore.Signal()
    types_changed = QtCore.Signal()

    def __init__(self, entries: list[dict] | None = None, parent=None):
        super().__init__(parent)
        self.entries = entries if entries is not None else []
        self.folder = str(storage.root())
        self._custom = settings.get_session_dir() is not None
        self._loading = True

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(12)
        root.addWidget(self._build_preview())

        columns_row = QtWidgets.QHBoxLayout()
        columns_row.setSpacing(12)

        left = QtWidgets.QVBoxLayout()
        left.setSpacing(12)
        left.addWidget(self._build_folder())
        left.addWidget(self._build_parts())
        left.addStretch(1)

        right = QtWidgets.QVBoxLayout()
        right.setSpacing(12)
        right.addWidget(self._build_move_box())
        right.addWidget(self._build_counter_box())
        right.addWidget(self._build_types_box())
        right.addStretch(1)

        columns_row.addLayout(left, 3)
        columns_row.addLayout(right, 2)
        root.addLayout(columns_row)
        root.addStretch(1)

        self._load(settings.get_naming())
        self._loading = False
        self._refresh()

    # -- Aufbau ------------------------------------------------------------

    def _build_preview(self) -> QtWidgets.QWidget:
        box = QtWidgets.QFrame()
        box.setObjectName("previewCard")
        box.setStyleSheet(
            f"QFrame#previewCard {{"
            f" background-color: {theming.mix(NORD['bg2'], NORD['accent'], 0.10)};"
            f" border: 1px solid {theming.mix(NORD['border'], NORD['accent'], 0.45)};"
            f" border-radius: 8px; }}")
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(4)

        head = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(i18n.t("opt_preview"))
        title.setStyleSheet(
            f"color: {NORD['dim']}; font-size: 11px; font-weight: 600;")
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(info_icon(i18n.t("opt_preview_hint")))
        lay.addLayout(head)

        # Der Ordner klein und blass darueber, der Name gross darunter: der
        # Ordner aendert sich selten, der Name bei jedem Handgriff.
        self.preview_folder = QtWidgets.QLabel("")
        self.preview_folder.setWordWrap(True)
        self.preview_folder.setStyleSheet(
            f"color: {NORD['dim']}; font-family: monospace; font-size: 11px;")
        lay.addWidget(self.preview_folder)

        self.preview = QtWidgets.QLabel("")
        self.preview.setWordWrap(True)
        self.preview.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.preview.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.preview.setStyleSheet("font-size: 15px; font-weight: 700;")
        lay.addWidget(self.preview)
        return box

    def _build_folder(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("storage_folder"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(6)

        row = QtWidgets.QHBoxLayout()
        self.path_edit = QtWidgets.QLineEdit(self.folder)
        self.path_edit.setReadOnly(True)
        browse = QtWidgets.QPushButton(i18n.t("choose_folder"))
        browse.clicked.connect(self._browse)
        reset = QtWidgets.QPushButton(i18n.t("storage_reset"))
        reset.clicked.connect(self._reset_folder)
        row.addWidget(self.path_edit, 1)
        row.addWidget(browse)
        row.addWidget(reset)
        row.addWidget(info_icon(i18n.t("storage_folder_hint")))
        lay.addLayout(row)

        sub = QtWidgets.QHBoxLayout()
        sub.addWidget(QtWidgets.QLabel(i18n.t("opt_subfolders")))
        self.subfolders = QtWidgets.QComboBox()
        for key in naming.SUBFOLDERS:
            self.subfolders.addItem(i18n.t(f"opt_sub_{key}"), key)
        # Letzter Eintrag: derselbe Baukasten wie beim Dateinamen, nur fuer
        # den Ordner. Wer seine Ordner schon von Hand in einer bestimmten
        # Form fuehrt, kann sie damit fortfuehren.
        self.subfolders.addItem(i18n.t("opt_sub_blocks"), "blocks")
        self.subfolders.currentIndexChanged.connect(self._folder_mode_changed)
        sub.addWidget(self.subfolders, 1)
        sub.addWidget(info_icon(i18n.t("opt_sub_hint")))
        lay.addLayout(sub)

        self.folder_parts = PartList()
        self.folder_parts.changed.connect(self._refresh)
        for key in naming.FOLDER_BLOCKS:
            self.folder_parts.add_row(self._build_folder_row(key))
        self.folder_parts.setMaximumHeight(190)
        self.folder_parts.hide()
        lay.addWidget(self.folder_parts)
        return box

    def _build_folder_row(self, key: str) -> PartRow:
        row = PartRow(key)
        if key == "text":
            self.folder_text = QtWidgets.QLineEdit()
            self.folder_text.setPlaceholderText(i18n.t("opt_folder_text_hint"))
            self.folder_text.setMaxLength(naming.MAX_TEXT)
            self.folder_text.textChanged.connect(self._refresh)
            row.set_inline(self.folder_text)
        return row

    def _folder_mode_changed(self) -> None:
        self.folder_parts.setVisible(self.subfolders.currentData() == "blocks")
        self._refresh()

    def _build_parts(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("opt_parts"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        hint = QtWidgets.QLabel(i18n.t("opt_parts_short"))
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        head.addWidget(hint)
        head.addStretch(1)
        # Nur das Pfeilzeichen, der Rest steht im Tooltip. Die Knoepfe
        # tragen "stepper", damit die breite Seitenpolsterung der normalen
        # Knoepfe nicht greift — die frass das Zeichen auf.
        self.btn_up = QtWidgets.QPushButton("▲")
        self.btn_up.setObjectName("stepper")
        self.btn_up.setToolTip(i18n.t("opt_up"))
        self.btn_up.setFixedWidth(34)
        self.btn_up.clicked.connect(lambda: self._move_part(-1))
        self.btn_down = QtWidgets.QPushButton("▼")
        self.btn_down.setObjectName("stepper")
        self.btn_down.setToolTip(i18n.t("opt_down"))
        self.btn_down.setFixedWidth(34)
        self.btn_down.clicked.connect(lambda: self._move_part(1))
        head.addWidget(self.btn_up)
        head.addWidget(self.btn_down)
        lay.addLayout(head)

        self.parts = PartList()
        self.parts.changed.connect(self._refresh)
        for key in naming.BLOCKS:
            self.parts.add_row(self._build_row(key))
        lay.addWidget(self.parts)
        return box

    def _build_row(self, key: str) -> PartRow:
        """Eine Baustein-Zeile samt der Einstellungen, die nur sie betreffen."""
        row = PartRow(key)

        if key in naming.TEXT_BLOCKS:
            # Das Eingabefeld sitzt in der Zeile selbst. Eine eigene Sektion
            # "Naming" weiter unten hatte dasselbe getan, nur weiter weg von
            # dem Haken, der darueber entscheidet, ob es ueberhaupt zaehlt.
            edit = QtWidgets.QLineEdit()
            edit.setPlaceholderText(i18n.t("opt_text_placeholder"))
            edit.setMaxLength(naming.MAX_TEXT)
            edit.textChanged.connect(self._refresh)
            row.set_inline(edit)
            # self.prefix bzw. self.suffix — die Zeile ist beides zugleich.
            setattr(self, key, edit)

        elif key == "time":
            self.seconds = QtWidgets.QCheckBox(i18n.t("opt_seconds"))
            self.seconds.toggled.connect(self._refresh)
            row.add_sub(self.seconds)

        elif key == "counter":
            self.digits = QtWidgets.QSpinBox()
            self.digits.setRange(naming.MIN_DIGITS, naming.MAX_DIGITS)
            self.digits.setPrefix(i18n.t("opt_digits_prefix"))
            self.digits.valueChanged.connect(self._refresh)
            self.reset_box = QtWidgets.QComboBox()
            for reset in naming.RESETS:
                self.reset_box.addItem(i18n.t(f"opt_reset_{reset}"), reset)
            self.reset_box.currentIndexChanged.connect(self._refresh)
            row.add_sub(self.digits, self.reset_box)

        return row

    def _build_move_box(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("storage_existing"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        head.addStretch(1)
        head.addWidget(info_icon(i18n.t("storage_move_hint")))
        lay.addLayout(head)

        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        self.move_button = QtWidgets.QPushButton(i18n.t("storage_move"))
        self.move_button.clicked.connect(self._move)
        lay.addWidget(self.move_button)
        return box

    def _build_counter_box(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("part_counter"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        self.counter_state = QtWidgets.QLabel("")
        self.counter_state.setWordWrap(True)
        head.addWidget(self.counter_state, 1)
        head.addWidget(info_icon(i18n.t("opt_counter_hint")))
        lay.addLayout(head)

        self.btn_counter = QtWidgets.QPushButton(i18n.t("opt_reset_now"))
        self.btn_counter.clicked.connect(self._reset_counter)
        lay.addWidget(self.btn_counter)
        return box

    # -- Aufnahmetypen -----------------------------------------------------

    def _build_types_box(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("opt_types"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(6)

        head = QtWidgets.QHBoxLayout()
        hint = QtWidgets.QLabel(i18n.t("opt_types_note"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        head.addWidget(hint, 1)
        head.addWidget(info_icon(i18n.t("opt_types_hint")))
        lay.addLayout(head)

        self.type_list = QtWidgets.QListWidget()
        self.type_list.setMaximumHeight(130)
        self.type_list.currentItemChanged.connect(self._type_selected)
        lay.addWidget(self.type_list)

        row = QtWidgets.QHBoxLayout()
        add = QtWidgets.QPushButton(i18n.t("opt_type_add"))
        add.clicked.connect(self._add_type)
        self.btn_type_delete = QtWidgets.QPushButton(i18n.t("delete"))
        self.btn_type_delete.setEnabled(False)
        self.btn_type_delete.clicked.connect(self._delete_type)
        row.addWidget(add)
        row.addStretch(1)
        row.addWidget(self.btn_type_delete)
        lay.addLayout(row)

        self._fill_types()
        return box

    def _fill_types(self, select: str | None = None) -> None:
        """Liste neu aufbauen. Eingebaute stehen mit drin, aber blass.

        Sie lassen sich nicht loeschen; sichtbar sein sollen sie trotzdem,
        schon damit zu sehen ist, welches Kuerzel im Dateinamen landet.
        """
        self.type_list.clear()
        for kind in rectypes.all_types():
            item = QtWidgets.QListWidgetItem(
                f"{kind.label}  ·  {rectypes.slug(kind.key)}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, kind.key)
            if not rectypes.is_user(kind.key):
                item.setForeground(QtGui.QColor(NORD["dim"]))
            self.type_list.addItem(item)
            if kind.key == select:
                self.type_list.setCurrentItem(item)
        self._type_selected()

    def _selected_type(self) -> str | None:
        item = self.type_list.currentItem()
        return None if item is None else item.data(
            QtCore.Qt.ItemDataRole.UserRole)

    def _type_selected(self, *args) -> None:
        self.btn_type_delete.setEnabled(rectypes.is_user(self._selected_type()))

    def _add_type(self) -> None:
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("type_add_title"), i18n.t("name"))
        name = rectypes.clean_name(name)
        if not ok or not name:
            return
        taken = {kind.label.lower() for kind in rectypes.all_types()}
        if name.lower() in taken:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("name_taken"), i18n.t("type_name_taken"))
            return

        code = rectypes.make_slug(name)
        settings.save_user_type(code, name)
        self._fill_types(select=rectypes.USER_PREFIX + code)
        self._refresh()
        self.types_changed.emit()

    def _delete_type(self) -> None:
        key = self._selected_type()
        if not rectypes.is_user(key):
            return
        name = rectypes.label(key)

        # Aufnahmen behalten ihren Typ-Schluessel; nur der Name dazu ist
        # danach weg. Wer das nicht weiss, wundert sich spaeter ueber eine
        # Liste voller Kuerzel.
        used = sum(1 for entry in self.entries if entry.get("type") == key)
        body = i18n.t("type_delete_body", name=name)
        if used:
            body += "\n\n" + i18n.t("type_delete_used", count=used,
                                     slug=rectypes.slug_of(key))
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("type_delete_title"), body)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        settings.delete_user_type(rectypes.slug_of(key))
        self._fill_types()
        self._refresh()
        self.types_changed.emit()

    # -- Bausteine ---------------------------------------------------------

    def _load(self, scheme: dict) -> None:
        """Widgets aus einem Schema fuellen."""
        scheme = naming.normalize(scheme)
        self._loading = True

        folder = scheme["folder"]
        gewaehlt = ("blocks" if folder["mode"] == "blocks"
                    else scheme["subfolders"])
        index = self.subfolders.findData(gewaehlt)
        self.subfolders.setCurrentIndex(max(index, 0))
        self.folder_text.setText(folder["text"])
        self.folder_parts.set_order(folder["order"])
        for row in self.folder_parts.rows():
            row.set_checked(folder["enabled"].get(row.key, False))
        self.folder_parts.setVisible(folder["mode"] == "blocks")
        index = self.reset_box.findData(scheme["counter_reset"])
        self.reset_box.setCurrentIndex(max(index, 0))

        self.prefix.setText(scheme["prefix"])
        self.suffix.setText(scheme["suffix"])
        self.seconds.setChecked(scheme["seconds"])
        self.digits.setValue(scheme["counter_digits"])

        self.parts.set_order(scheme["order"])
        for row in self.parts.rows():
            row.set_checked(scheme["enabled"].get(row.key, False))
        self._loading = False

    def _collect(self) -> dict:
        """Schema aus dem, was gerade in den Widgets steht."""
        gewaehlt = self.subfolders.currentData()
        return naming.normalize({
            "subfolders": gewaehlt if gewaehlt in naming.SUBFOLDERS else "none",
            "folder": {
                "mode": "blocks" if gewaehlt == "blocks" else "period",
                "order": self.folder_parts.order(),
                "enabled": {row.key: row.is_checked()
                            for row in self.folder_parts.rows()},
                "text": self.folder_text.text(),
            },
            "order": self.parts.order(),
            "enabled": {row.key: row.is_checked() for row in self.parts.rows()},
            "prefix": self.prefix.text(),
            "suffix": self.suffix.text(),
            "seconds": self.seconds.isChecked(),
            "counter_digits": self.digits.value(),
            "counter_reset": self.reset_box.currentData(),
        })

    def _move_part(self, step: int) -> None:
        index = self.parts.currentRow()
        if self.parts.move(index, index + step):
            self._refresh()

    # -- Zustand -----------------------------------------------------------

    def _refresh(self) -> None:
        if self._loading:
            return

        scheme = self._collect()
        stamp = datetime.now()
        type_key = settings.get_recording_type()
        counter = storage.peek_counter(scheme, stamp)

        self._loading = True
        for row in self.parts.rows():
            row.set_value(naming.block_value(row.key, scheme, stamp,
                                             type_key, counter))
        for row in self.folder_parts.rows():
            row.set_value(naming.folder_block_value(row.key, scheme, stamp))
        self._loading = False

        self.preview_folder.setText(str(Path(self.folder)) + os.sep)
        self.preview.setText(self._preview_html(scheme, stamp, type_key,
                                                counter))
        self.path_edit.setText(self.folder)

        state = settings.get_name_counter()
        self.counter_state.setText(i18n.t("opt_counter_at", value=counter)
                                   if state["value"]
                                   else i18n.t("opt_counter_fresh"))
        self.btn_counter.setEnabled(bool(state["value"]))

        pending = storage.elsewhere(self.entries, Path(self.folder), scheme)
        self.status.setText(i18n.t("storage_elsewhere", count=pending)
                            if pending else i18n.t("storage_all_here"))
        self.move_button.setEnabled(pending > 0)

    def _preview_html(self, scheme: dict, stamp, type_key: str,
                      counter: int) -> str:
        """Der Name in Marken, damit man sieht, welcher Baustein was macht."""
        def plain(text: str) -> str:
            return f"<span style='color:{NORD['dim']};'>{text}</span>"

        parts = []
        folder = naming.build_folder(scheme, stamp)
        if folder:
            parts.append(badge_html(folder, NORD["accent"]))
            parts.append(plain(os.sep))

        pieces = []
        for key in scheme["order"]:
            if not scheme["enabled"].get(key):
                continue
            value = naming.block_value(key, scheme, stamp, type_key, counter)
            if value:
                pieces.append(badge_html(value, NORD[PART_ROLES[key]]))

        if pieces:
            parts.append(plain(naming.SEPARATOR).join(pieces))
        else:
            # Alles abgeschaltet: naming faellt auf den Zeitstempel zurueck,
            # und das soll die Vorschau auch zeigen statt einer Luecke.
            parts.append(badge_html(naming.build_stem(scheme, stamp, type_key,
                                                      counter),
                                    NORD["accent"]))
        parts.append(plain(".wav"))
        return "".join(parts)

    def _browse(self) -> None:
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, i18n.t("storage_pick_title"), self.folder)
        if not chosen:
            return
        problem = storage.writable(Path(chosen))
        if problem:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("storage_title"),
                i18n.t("storage_not_writable") + f"\n\n{problem}")
            return
        self.folder = chosen
        self._custom = True
        self._refresh()

    def _reset_folder(self) -> None:
        self.folder = str(storage.DEFAULT_ROOT)
        self._custom = False
        self._refresh()

    def _reset_counter(self) -> None:
        settings.set_name_counter("", 0)
        self._refresh()

    # -- Anwenden ----------------------------------------------------------

    def store(self) -> bool:
        """Ordner und Schema uebernehmen. False, wenn der Ordner nicht taugt."""
        problem = storage.writable(Path(self.folder))
        if problem:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("storage_title"),
                i18n.t("storage_not_writable") + f"\n\n{problem}")
            return False
        settings.set_session_dir(None if not self._custom else self.folder)
        settings.set_naming(self._collect())
        self.changed.emit()
        return True

    def snapshot(self) -> tuple:
        return settings.get_session_dir(), settings.get_naming()

    def restore(self, state: tuple) -> None:
        folder, scheme = state
        settings.set_session_dir(folder)
        settings.set_naming(scheme)
        self.folder = str(storage.root())
        self._custom = folder is not None
        self._load(scheme)
        self._refresh()

    def _move(self) -> None:
        """Vorhandene Aufnahmen nachziehen.

        Wendet die Auswahl vorher an: erst die Dateien umziehen und dann
        die Einstellung speichern hinterliesse einen Zustand, in dem die
        Liste auf Namen zeigt, die es noch nicht gibt.
        """
        scheme = self._collect()
        target = Path(self.folder)
        pending = storage.elsewhere(self.entries, target, scheme)
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("storage_move"),
            i18n.t("storage_move_confirm", count=pending, folder=self.folder),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        sources = [storage.root()]
        QtWidgets.QApplication.setOverrideCursor(
            QtCore.Qt.CursorShape.WaitCursor)
        try:
            result = storage.move_all(self.entries, sources, target, scheme)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        self.store()
        self._refresh()

        lines = [i18n.t("storage_move_done", moved=result["moved"],
                        kept=result["kept"])]
        if result["missing"]:
            lines.append(i18n.t("storage_move_missing", count=result["missing"]))
        if result["errors"]:
            lines.append("")
            lines.append(i18n.t("storage_move_failed"))
            lines += result["errors"][:10]
        QtWidgets.QMessageBox.information(
            self, i18n.t("storage_title"), "\n".join(lines))
