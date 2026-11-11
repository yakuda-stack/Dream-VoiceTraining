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

"""Design-Reiter: Farbvorlagen, eigene Farben, Hintergrund."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from core import debuglog
from core import i18n
from core import paths
from ui import theming
from ui.theming import COLORS as NORD


# ------------------------------------------------------------ Design-Reiter

class ThemeTile(QtWidgets.QAbstractButton):
    """Vorschaukachel eines Themas: fuenf Farbstreifen plus Name."""

    STRIPES = ["bg", "sidebar", "bg3", "accent", "fg"]

    def __init__(self, name: str, colors: dict, parent=None):
        super().__init__(parent)
        self.name = name
        self.colors = colors
        self.setCheckable(True)
        self.setFixedSize(96, 92)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        strip_h = height - 24

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        step = (width - 8) / len(self.STRIPES)
        for i, key in enumerate(self.STRIPES):
            painter.setBrush(QtGui.QColor(self.colors.get(key, "#000000")))
            painter.drawRect(QtCore.QRectF(4 + i * step, 4, step + 0.5,
                                           strip_h - 8))

        painter.setPen(QtGui.QPen(
            QtGui.QColor(NORD["accent"] if self.isChecked() else NORD["border"]),
            2 if self.isChecked() else 1))
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QtCore.QRectF(2, 2, width - 4, strip_h - 4), 6, 6)

        painter.setPen(QtGui.QColor(
            NORD["accent"] if self.isChecked() else NORD["fg"]))
        painter.drawText(QtCore.QRectF(0, strip_h, width, 20),
                         QtCore.Qt.AlignmentFlag.AlignCenter, self.text())
        painter.end()


class ColorButton(QtWidgets.QPushButton):
    """Farbfeld, das beim Klick den Farbwaehler oeffnet."""

    picked = QtCore.Signal(str, str)      # rolle, farbe

    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self.setMinimumHeight(30)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._choose)
        self.refresh()

    def refresh(self) -> None:
        color = theming.COLORS.get(self.role.key, "#000000")
        self.setText(self.role.label)
        self.setStyleSheet(
            f"QPushButton {{ background: {color};"
            f" color: {theming.contrast_text(color)};"
            f" border: 1px solid {theming.mix(color, NORD['fg'], 0.25)};"
            " border-radius: 5px; padding: 5px 10px; text-align: left;"
            " font-weight: 500; }")

    def _choose(self) -> None:
        current = QtGui.QColor(theming.COLORS.get(self.role.key, "#000000"))
        chosen = QtWidgets.QColorDialog.getColor(
            current, self, i18n.t("pick_color", role=self.role.label))
        if chosen.isValid():
            self.picked.emit(self.role.key, chosen.name())


class DesignEditor(QtWidgets.QWidget):
    """Thema, Einzelfarben, Hintergrundbild und Deckkraft."""

    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loading = False

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(12)

        hint = QtWidgets.QLabel(i18n.t("design_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        root.addWidget(hint)

        # -- Themen --
        themes = QtWidgets.QGroupBox(i18n.t("theme"))
        grid = QtWidgets.QGridLayout(themes)
        grid.setSpacing(8)
        self.tiles: dict[str, ThemeTile] = {}
        for i, (name, colors) in enumerate(theming.PRESETS.items()):
            tile = ThemeTile(name, colors)
            tile.setText(i18n.t(f"theme_{name}"))
            tile.clicked.connect(lambda _=False, n=name: self._use_preset(n))
            self.tiles[name] = tile
            grid.addWidget(tile, i // 5, i % 5)
        grid.setColumnStretch(5, 1)
        root.addWidget(themes)

        # -- Farben --
        colors_box = QtWidgets.QGroupBox(i18n.t("colors"))
        colors_lay = QtWidgets.QVBoxLayout(colors_box)

        top = QtWidgets.QHBoxLayout()
        top.addStretch(1)
        reset = QtWidgets.QPushButton("↺  " + i18n.t("reset_colors"))
        reset.clicked.connect(self._reset_colors)
        top.addWidget(reset)
        colors_lay.addLayout(top)

        swatches = QtWidgets.QGridLayout()
        swatches.setSpacing(6)
        self.buttons: dict[str, ColorButton] = {}
        for i, role in enumerate(theming.ROLES):
            button = ColorButton(role)
            button.picked.connect(self._color_picked)
            self.buttons[role.key] = button
            swatches.addWidget(button, i // 3, i % 3)
        for column in range(3):
            swatches.setColumnStretch(column, 1)
        colors_lay.addLayout(swatches)
        root.addWidget(colors_box)

        # -- Hintergrund --
        background = QtWidgets.QGroupBox(i18n.t("background"))
        bg_lay = QtWidgets.QVBoxLayout(background)

        bg_top = QtWidgets.QHBoxLayout()
        bg_top.addStretch(1)
        add = QtWidgets.QPushButton("＋  " + i18n.t("add_image"))
        add.setObjectName("primary")
        add.clicked.connect(self._add_image)
        bg_top.addWidget(add)
        bg_lay.addLayout(bg_top)

        self.thumbs = QtWidgets.QHBoxLayout()
        self.thumbs.setSpacing(8)
        holder = QtWidgets.QWidget()
        holder.setLayout(self.thumbs)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setFixedHeight(112)
        scroll.setWidget(holder)
        bg_lay.addWidget(scroll)

        opacity_row = QtWidgets.QHBoxLayout()
        opacity_row.addWidget(QtWidgets.QLabel(i18n.t("card_opacity")))
        self.opacity = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.opacity.setRange(20, 100)
        self.opacity.setValue(theming.card_opacity())
        self.opacity.valueChanged.connect(self._opacity_changed)
        self.opacity_label = QtWidgets.QLabel("")
        self.opacity_label.setFixedWidth(48)
        self.opacity_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight
                                        | QtCore.Qt.AlignmentFlag.AlignVCenter)
        opacity_row.addWidget(self.opacity, 1)
        opacity_row.addWidget(self.opacity_label)
        bg_lay.addLayout(opacity_row)

        note = QtWidgets.QLabel(i18n.t("opacity_hint"))
        note.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        bg_lay.addWidget(note)
        root.addWidget(background)
        root.addStretch(1)

        self.refresh()

    # -- Zustand ---------------------------------------------------------

    def refresh(self) -> None:
        self._loading = True
        current = theming.preset_name()
        for name, tile in self.tiles.items():
            tile.setChecked(name == current)
            tile.update()
        for button in self.buttons.values():
            button.refresh()
        self.opacity.setValue(theming.card_opacity())
        self.opacity_label.setText(f"{theming.card_opacity()} %")
        self._fill_backgrounds()
        self._loading = False

    def _fill_backgrounds(self) -> None:
        while self.thumbs.count():
            item = self.thumbs.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.thumbs.addWidget(self._thumb(None))
        paths.ensure_dirs()
        for path in sorted(paths.BACKGROUND_DIR.glob("*")):
            if path.is_file():
                self.thumbs.addWidget(self._thumb(path))
        self.thumbs.addStretch(1)

    def _thumb(self, path) -> QtWidgets.QWidget:
        active = (str(path) if path else None) == theming.background()

        box = QtWidgets.QWidget()
        box.setFixedWidth(124)
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        button = QtWidgets.QPushButton()
        button.setFixedSize(120, 68)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        border = NORD["accent"] if active else NORD["border"]
        if path is None:
            button.setText(i18n.t("no_background"))
            button.setStyleSheet(
                f"QPushButton {{ background: {NORD['bg']};"
                f" border: 2px solid {border}; border-radius: 6px;"
                f" color: {NORD['dim']}; }}")
        else:
            button.setIcon(QtGui.QIcon(str(path)))
            button.setIconSize(QtCore.QSize(116, 64))
            button.setStyleSheet(
                f"QPushButton {{ border: 2px solid {border};"
                " border-radius: 6px; padding: 0; }")
        button.clicked.connect(lambda _=False, p=path: self._use_background(p))
        lay.addWidget(button)

        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(2, 0, 2, 0)
        caption = QtWidgets.QLabel(
            i18n.t("no_background") if path is None else path.stem[:14])
        caption.setStyleSheet(f"color: {NORD['dim']}; font-size: 10px;")
        row.addWidget(caption, 1)
        if path is not None:
            remove = QtWidgets.QToolButton()
            remove.setText("🗑")
            remove.setAutoRaise(True)
            remove.setStyleSheet(
                f"QToolButton {{ color: {NORD['dim']}; border: none; }}"
                f"QToolButton:hover {{ color: {NORD['red']}; }}")
            remove.clicked.connect(lambda _=False, p=path: self._remove_image(p))
            row.addWidget(remove)
        lay.addLayout(row)
        return box

    # -- Aktionen --------------------------------------------------------

    def _emit(self) -> None:
        if not self._loading:
            self.changed.emit()

    def _use_preset(self, name: str) -> None:
        theming.use_preset(name)
        self.refresh()
        self._emit()

    def _color_picked(self, key: str, color: str) -> None:
        theming.apply(colors={key: color})
        self.buttons[key].refresh()
        self._emit()

    def _reset_colors(self) -> None:
        theming.reset_colors()
        self.refresh()
        self._emit()

    def _opacity_changed(self, value: int) -> None:
        self.opacity_label.setText(f"{value} %")
        theming.apply(opacity=value)
        self._emit()

    def _use_background(self, path) -> None:
        theming.apply(bg_image=str(path) if path else None)
        self._fill_backgrounds()
        self._emit()

    def _add_image(self) -> None:
        chosen, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, i18n.t("choose_image"), str(Path.home()),
            i18n.t("image_filter"))
        if not chosen:
            return
        paths.ensure_dirs()
        source = Path(chosen)
        target = paths.BACKGROUND_DIR / source.name
        counter = 1
        while target.exists() and target.resolve() != source.resolve():
            target = paths.BACKGROUND_DIR / f"{source.stem}-{counter}{source.suffix}"
            counter += 1
        try:
            if target.resolve() != source.resolve():
                shutil.copy2(source, target)
        except OSError as exc:
            debuglog.record_exception("design.add_image", exc)
            QtWidgets.QMessageBox.warning(self, i18n.t("add_image"), str(exc))
            return
        self._use_background(target)

    def _remove_image(self, path) -> None:
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("remove_image"),
            i18n.t("remove_image_body", name=path.name))
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        try:
            path.unlink()
        except OSError as exc:
            debuglog.record_exception("design.remove_image", exc)
            return
        if theming.background() == str(path):
            theming.apply(bg_image=None)
            self._emit()
        self._fill_backgrounds()
