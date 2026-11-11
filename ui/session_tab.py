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

"""Sessions-Reiter: Tabelle, Spalten, Filter, Export, Wiedergabe und Import."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd
from PySide6 import QtCore, QtGui, QtWidgets

from voice import analysis
from core import columns
from core import debuglog
from core import i18n
from core import naming
from core import progress
from core import rectypes
from core import settings
from core import storage
from voice import targets
from ui.theming import COLORS as NORD
from voice import audio as audio_mod
from voice.audio import write_wav
from ui.compare_dialog import CompareDialog
from ui.progress_dialog import ProgressDialog
from ui.dialogs import (FilterDialog, SessionDetailDialog, ask_export_language,
                        export_language)


class SessionTabMixin:
    """Alles, was zum Sessions-Reiter gehoert. Wird in MainWindow eingemischt."""

    def _build_session_tab(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)

        bar = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel("")
        self.count_label.setStyleSheet(f"color: {NORD['dim']};")
        btn_filter = QtWidgets.QPushButton(i18n.t("filter"))
        btn_filter.clicked.connect(self._open_filter)
        self.btn_filter = btn_filter
        btn_import = QtWidgets.QPushButton(i18n.t("import_list"))
        btn_import.clicked.connect(self._import_files)
        btn_export = QtWidgets.QPushButton(i18n.t("export_list"))
        btn_export.clicked.connect(self._export_list)
        self.streak_label = QtWidgets.QLabel("")
        self.streak_label.setStyleSheet(f"color: {NORD['green']};")
        self.btn_progress = QtWidgets.QPushButton(i18n.t("progress"))
        self.btn_progress.clicked.connect(self._open_progress)
        self.btn_compare = QtWidgets.QPushButton(i18n.t("compare"))
        self.btn_compare.setToolTip(i18n.t("compare_pick_two"))
        self.btn_compare.clicked.connect(self._compare_selected)
        bar.addWidget(self.count_label)
        bar.addSpacing(16)
        bar.addWidget(self.streak_label, 1)
        bar.addWidget(self.btn_progress)
        bar.addWidget(self.btn_compare)
        bar.addSpacing(10)
        bar.addWidget(btn_filter)
        bar.addWidget(btn_import)
        bar.addWidget(btn_export)
        lay.addLayout(bar)

        self.table = QtWidgets.QTableWidget(0, 0)
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._row_menu)
        self.table.doubleClicked.connect(
            lambda index: self._open_details(self._entry_at(index.row())))

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._header_clicked)
        header.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._header_menu)
        header.setSectionsMovable(True)
        header.sectionMoved.connect(self._section_moved)
        self.table.verticalScrollBar().valueChanged.connect(self._populate_actions)
        lay.addWidget(self.table)

        row = QtWidgets.QHBoxLayout()
        btn_play = QtWidgets.QPushButton(i18n.t("play"))
        btn_play.clicked.connect(self._play_selected)
        btn_stop = QtWidgets.QPushButton(i18n.t("stop"))
        btn_stop.clicked.connect(lambda: sd.stop())
        btn_dir = QtWidgets.QPushButton(i18n.t("open_folder"))
        btn_dir.clicked.connect(self._open_storage_folder)
        btn_where = QtWidgets.QPushButton(i18n.t("choose_folder"))
        btn_where.clicked.connect(self._open_storage)
        row.addWidget(btn_play)
        row.addWidget(btn_stop)
        row.addStretch(1)
        row.addWidget(btn_dir)
        row.addWidget(btn_where)
        lay.addLayout(row)

        hint = QtWidgets.QLabel(i18n.t("formant_hint"))
        hint.setStyleSheet(f"color: {NORD['dim']};")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        return page

    # -- Ansicht der Liste -----------------------------------------------

    def _visible_columns(self) -> list:
        keys = self.view.get("columns") or columns.DEFAULT_VISIBLE
        chosen = [columns.BY_KEY[k] for k in keys if k in columns.BY_KEY]
        return chosen or [columns.BY_KEY[k] for k in columns.DEFAULT_VISIBLE]

    def _filtered_sessions(self) -> list[dict]:
        entries = list(self.sessions)

        if self.view.get("period_on"):
            start = self.view.get("period_from") or ""
            end = self.view.get("period_to") or ""
            entries = [e for e in entries
                       if (not start or e.get("timestamp", "")[:10] >= start)
                       and (not end or e.get("timestamp", "")[:10] <= end)]

        column = columns.BY_KEY.get(self.view.get("sort", "date"),
                                    columns.BY_KEY["date"])
        descending = bool(self.view.get("descending", True))
        entries.sort(key=lambda e: columns.sort_key(e, column, descending),
                     reverse=descending)
        # Fehlende Werte bleiben unten, auch wenn absteigend sortiert wird.
        present = [e for e in entries if columns.value(e, column) not in (None, "")]
        missing = [e for e in entries if columns.value(e, column) in (None, "")]
        return present + missing

    def _entry_at(self, row: int) -> dict | None:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def _header_clicked(self, index: int) -> None:
        visible = self._visible_columns()
        if not 0 <= index < len(visible):
            return
        key = visible[index].key
        if self.view.get("sort") == key:
            self.view["descending"] = not self.view.get("descending", True)
        else:
            self.view["sort"] = key
            self.view["descending"] = True
        settings.set_view(self.view)
        self._fill_session_table()

    def _header_menu(self, position) -> None:
        header = self.table.horizontalHeader()
        menu = self.build_header_menu(header.logicalIndexAt(position))
        menu.exec(header.mapToGlobal(position))

    def build_header_menu(self, index: int) -> QtWidgets.QMenu:
        """Rechtsklick auf eine Ueberschrift: ausblenden oder verwalten.

        Aufbau und Anzeige sind getrennt, damit sich der Inhalt ohne
        blockierendes exec() pruefen laesst.
        """
        visible = self._visible_columns()
        clicked = visible[index] if 0 <= index < len(visible) else None

        menu = QtWidgets.QMenu(self)

        if clicked is not None:
            action = menu.addAction(i18n.t("sort_by_this"))
            action.triggered.connect(
                lambda _=False, i=index: self._header_clicked(i))

            left = menu.addAction(i18n.t("move_left"))
            left.setEnabled(index > 0)
            left.triggered.connect(
                lambda _=False, key=clicked.key: self._move_column(key, -1))
            right = menu.addAction(i18n.t("move_right"))
            right.setEnabled(index < len(visible) - 1)
            right.triggered.connect(
                lambda _=False, key=clicked.key: self._move_column(key, 1))
            menu.addSeparator()

            hide = menu.addAction(i18n.t("hide_column", name=clicked.label))
            hide.triggered.connect(
                lambda _=False, key=clicked.key: self._hide_column(key))
            if len(visible) <= 1:
                hide.setEnabled(False)
                hide.setToolTip(i18n.t("last_column"))
            menu.addSeparator()

        keys = {c.key for c in visible}
        submenu = menu.addMenu(i18n.t("columns_menu"))
        for column in columns.COLUMNS:
            entry = submenu.addAction(column.label)
            entry.setCheckable(True)
            entry.setChecked(column.key in keys)
            entry.triggered.connect(
                lambda checked, key=column.key: self._toggle_column(key, checked))

        menu.addSeparator()
        menu.addAction(i18n.t("manage_columns"), self._open_filter)
        return menu

    def _section_moved(self, _logical: int, _old: int, _new: int) -> None:
        """Reihenfolge nach dem Ziehen einer Ueberschrift uebernehmen."""
        if self._reordering:
            return
        header = self.table.horizontalHeader()
        count = self.table.columnCount()
        if count < 2:
            return

        self._reordering = True
        try:
            # Die Aktionsspalte bleibt immer ganz rechts.
            action_visual = header.visualIndex(count - 1)
            if action_visual != count - 1:
                header.moveSection(action_visual, count - 1)

            visible = self._visible_columns()
            order = []
            for visual in range(count - 1):
                logical = header.logicalIndex(visual)
                if 0 <= logical < len(visible):
                    order.append(visible[logical].key)
        finally:
            self._reordering = False

        if order and order != [c.key for c in self._visible_columns()]:
            self._set_columns(order)

    def _move_column(self, key: str, offset: int) -> None:
        keys = [c.key for c in self._visible_columns()]
        if key not in keys:
            return
        index = keys.index(key)
        target = index + offset
        if not 0 <= target < len(keys):
            return
        keys[index], keys[target] = keys[target], keys[index]
        self._set_columns(keys)

    def _set_columns(self, keys: list[str]) -> None:
        if not keys:
            return
        self.view["columns"] = keys
        settings.set_view(self.view)
        self._fill_session_table()

    def _hide_column(self, key: str) -> None:
        keys = [c.key for c in self._visible_columns() if c.key != key]
        self._set_columns(keys)

    def _toggle_column(self, key: str, wanted: bool) -> None:
        keys = [c.key for c in self._visible_columns()]
        if wanted and key not in keys:
            # An der Stelle einfuegen, an der die Spalte laut Definition
            # hingehoert — relativ zu den bereits sichtbaren Nachbarn.
            order = [c.key for c in columns.COLUMNS]
            position = len(keys)
            for i, existing in enumerate(keys):
                if order.index(existing) > order.index(key):
                    position = i
                    break
            keys = keys[:position] + [key] + keys[position:]
        elif not wanted and key in keys:
            if len(keys) <= 1:
                return
            keys.remove(key)
        self._set_columns(keys)

    def _open_filter(self) -> None:
        dialog = FilterDialog(self.view, self)
        dialog.applied.connect(self._apply_view)
        self.open_dialog(dialog)

    def _open_storage_folder(self) -> None:
        folder = storage.ensure_root()
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(str(folder)))

    def _open_storage(self) -> None:
        """Ordner waehlen — der Dialog des Systems und sonst nichts.

        Frueher ging hier ein eigenes Fenster auf, das erst einmal nach dem
        Ablageschema fragte, obwohl jemand nur einen Ordner suchen wollte.
        Das Schema steht jetzt in den Einstellungen unter "Optionen".
        """
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, i18n.t("storage_pick_title"), str(storage.root()))
        if not chosen:
            return

        # Vorher ausprobieren: erst beim Speichern zu scheitern hiesse
        # Aufnahme gemacht, Aufnahme weg.
        problem = storage.writable(Path(chosen))
        if problem:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("storage_title"),
                i18n.t("storage_not_writable") + f"\n\n{problem}")
            return

        settings.set_session_dir(chosen)
        self._fill_session_table()
        self.status.showMessage(i18n.t("storage_folder_set", folder=chosen))

    def _apply_view(self, view: dict) -> None:
        self.view = view
        settings.set_view(self.view)
        self._fill_session_table()

    def _row_menu(self, position) -> None:
        row = self.table.rowAt(position.y())
        entry = self._entry_at(row)
        if entry is None:
            return

        picked = self._selected_entries()
        if not any(e is entry for e in picked):
            self.table.selectRow(row)
            picked = [entry]

        menu = QtWidgets.QMenu(self)
        menu.addAction(i18n.t("details"), lambda: self._open_details(entry))
        menu.addAction(i18n.t("play"), lambda: self._play_entry(entry))
        if 2 <= len(picked) <= progress.MAX_COMPARE:
            menu.addAction(i18n.t("compare"),
                           lambda: self._open_compare(picked))
        if settings.get_reference_file() == entry.get("file"):
            menu.addAction(i18n.t("reference_clear"),
                           lambda: self._set_reference(None))
        else:
            menu.addAction(i18n.t("reference_set"),
                           lambda: self._set_reference(entry))
        menu.addSeparator()
        submenu = menu.addMenu(i18n.t("change_type"))
        current = entry.get("type")
        # Bei einem geloeschten eigenen Typ soll kein Haken irgendwo
        # sitzen; get() faende sonst den Standardtyp und behauptete, die
        # Aufnahme sei ein Lesetext.
        marked = current if rectypes.exists(current) else rectypes.get(current).key
        for kind in rectypes.all_types():
            action = submenu.addAction(kind.label)
            action.setCheckable(True)
            action.setChecked(kind.key == marked)
            action.triggered.connect(
                lambda _=False, e=entry, k=kind.key: self._set_type(e, k))

        menu.addAction(i18n.t("rename"), lambda: self._rename_session(entry))
        menu.addAction(i18n.t("delete"), lambda: self._delete_session(entry))
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _set_type(self, entry: dict, key: str) -> None:
        if entry.get("type") == key:
            return
        entry["type"] = key
        self._save_sessions()
        self._fill_session_table()

    def _rename_session(self, entry: dict) -> None:
        """Anzeigename und Datei umbenennen.

        Beides zusammen, sonst heisst eine Aufnahme im Programm anders als
        im Ordner und man findet sie beim Aufraeumen nicht wieder.
        """
        current = columns.display_name(entry)
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("rename_title"), i18n.t("rename_prompt"), text=current)
        if not ok:
            return

        name = name.strip()
        if not name or name == current:
            return

        old_name = entry.get("file", "")
        old_path = storage.path_for(old_name)
        suffix = Path(old_name).suffix or ".wav"
        # Der Unterordner bleibt: eine Aufnahme vom Maerz gehoert nicht
        # deshalb in den September, weil sie einen neuen Namen bekommt.
        new_name = (storage.folder_part(old_name)
                    + self._safe_filename(name) + suffix)
        new_path = old_path.parent / Path(new_name).name

        if new_path != old_path:
            if new_path.exists() or any(e.get("file") == new_name
                                        for e in self.sessions if e is not entry):
                QtWidgets.QMessageBox.warning(
                    self, i18n.t("rename_title"), i18n.t("rename_exists"))
                return
            try:
                if old_path.exists():
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    old_path.rename(new_path)
            except OSError as exc:
                debuglog.record_exception("main.rename_session", exc)
                QtWidgets.QMessageBox.warning(
                    self, i18n.t("rename_title"),
                    i18n.t("rename_failed") + f"\n\n{exc}")
                return
            entry["file"] = new_name

        entry["label"] = name
        self._save_sessions()
        self._fill_session_table()

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Anzeigename in einen Dateinamen ueberfuehren.

        Schraegstriche und aehnliches wuerden sonst neue Ordner aufmachen
        oder den Namen unbrauchbar machen.
        """
        cleaned = "".join("-" if c in '/\\:*?"<>|' or ord(c) < 32 else c
                          for c in name).strip(" .")
        cleaned = " ".join(cleaned.split())
        return (cleaned or "recording")[:80]

    def _fill_session_table(self) -> None:
        visible = self._visible_columns()
        self._rows = self._filtered_sessions()

        # setColumnCount raeumt vorhandene Cell-Widgets nicht ab. Ohne das
        # Leeren blieben die Aktionsknoepfe in der Spalte stehen, in der die
        # Aktionsspalte vor einer Aenderung der Auswahl lag.
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setColumnCount(len(visible) + 1)
        sort_key = self.view.get("sort")
        arrow = " ▼" if self.view.get("descending", True) else " ▲"
        self.table.setHorizontalHeaderLabels(
            [c.label + (arrow if c.key == sort_key else "") for c in visible] + [""])
        self.table.setRowCount(len(self._rows))
        reference = settings.get_reference_file()

        for r, entry in enumerate(self._rows):
            no_signal = entry.get("quality", "ok") == "kein_signal"
            peak = entry.get("peak_db")
            quiet = isinstance(peak, (int, float)) and peak < columns.QUIET_DB

            is_reference = entry.get("file") == reference
            for c, column in enumerate(visible):
                text = columns.text(entry, column)
                if is_reference and column.key == "label":
                    text = f"★ {text}"
                item = QtWidgets.QTableWidgetItem(text)
                if is_reference and column.key == "label":
                    item.setToolTip(i18n.t("reference_marker"))
                if no_signal:
                    item.setForeground(QtGui.QColor(NORD["dim"]))
                elif quiet and column.key == "peak_db":
                    item.setForeground(QtGui.QColor(NORD["yellow"]))
                self.table.setItem(r, c, item)

        # Die Aktionsknoepfe entstehen erst, wenn eine Zeile sichtbar wird.
        # Sie im Voraus fuer alle Zeilen zu bauen kostete bei 500 Sessions
        # eine knappe halbe Sekunde.
        self._action_rows.clear()
        self._action_column = len(visible)
        self.table.resizeColumnsToContents()
        self._populate_actions()
        self._fit_action_column()
        self.count_label.setText(i18n.t("shown_count", shown=len(self._rows),
                                        total=len(self.sessions)))
        self.streak_label.setText(i18n.t(
            "streak", days=progress.streak(self.sessions),
            count=progress.week_count(self.sessions)))

    def _populate_actions(self) -> None:
        """Knoepfe fuer den sichtbaren Ausschnitt nachziehen."""
        column = self._action_column
        if column is None or not self._rows:
            return

        first = self.table.rowAt(0)
        last = self.table.rowAt(self.table.viewport().height() - 1)
        first = 0 if first < 0 else first
        last = self.table.rowCount() - 1 if last < 0 else last
        first = max(0, first - 4)
        last = min(self.table.rowCount() - 1, last + 4)

        for row in range(first, last + 1):
            if row in self._action_rows:
                continue
            entry = self._entry_at(row)
            if entry is None:
                continue
            self.table.setCellWidget(row, column, self._row_actions(entry))
            self._action_rows.add(row)

    def _fit_action_column(self) -> None:
        last = self.table.columnCount() - 1
        widest = 0
        for row in self._action_rows:
            widget = self.table.cellWidget(row, last)
            if widget is not None:
                widest = max(widest, widget.sizeHint().width())
        self.table.setColumnWidth(last, max(widest + 12, 190))

    def _row_actions(self, entry: dict) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(box)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        details = QtWidgets.QPushButton(i18n.t("details"))
        details.setObjectName("rowaction")
        details.clicked.connect(lambda _=False, e=entry: self._open_details(e))

        remove = QtWidgets.QPushButton(i18n.t("delete"))
        remove.setObjectName("danger")
        remove.clicked.connect(lambda _=False, e=entry: self._delete_session(e))

        # Keine feste Breite: sonst schneidet Qt bei längeren Beschriftungen ab.
        for button in (details, remove):
            button.setMinimumWidth(button.sizeHint().width())
        lay.addWidget(details)
        lay.addWidget(remove)
        lay.addStretch(1)
        return box

    def _open_details(self, entry) -> None:
        if entry is None:
            return
        # Alte Eintraege kennen die neueren Kennwerte noch nicht.
        if "hnr" not in entry and entry.get("quality", "ok") == "ok":
            path = storage.path_for(entry.get("file", ""))
            if path.exists():
                self.status.showMessage(i18n.t("recalculating"))
                QtWidgets.QApplication.processEvents()
                try:
                    entry.update(analysis.analyse_file(path))
                    self._save_sessions()
                    self._fill_session_table()
                except Exception as exc:
                    debuglog.record_exception("main.open_details", exc)
                self.status.clearMessage()

        dialog = SessionDetailDialog(entry, list(self._rows), storage.root(), self)
        dialog.changed.connect(self._session_changed)
        self.open_dialog(dialog)

    def _session_changed(self) -> None:
        self._save_sessions()
        self._fill_session_table()

    def _delete_session(self, entry: dict) -> None:
        name = entry.get("file", "")
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("delete_title"), i18n.t("delete_question", name=name),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No)
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        path = storage.path_for(name)
        try:
            if name and path.exists():
                path.unlink()
        except OSError as exc:
            debuglog.record_exception("main.delete_session", exc)
            QtWidgets.QMessageBox.warning(self, i18n.t("delete"), str(exc))
            return

        if entry in self.sessions:
            self.sessions.remove(entry)

        # Dialoge sind nicht-modal und koennten den geloeschten Eintrag
        # noch anzeigen.
        for dialog in list(self._dialogs):
            if getattr(dialog, "entry", None) is entry:
                dialog.close()

        self._save_sessions()
        self._fill_session_table()
        self.status.showMessage(i18n.t("deleted", name=name))

    # -- Listenexport ------------------------------------------------------

    def _list_report(self) -> str:
        visible = self._visible_columns()
        head = [c.label for c in visible]
        table = [[columns.text(e, c) for c in visible] for e in self._rows]
        widths = [max(len(head[i]), *(len(row[i]) for row in table)) if table
                  else len(head[i]) for i in range(len(head))]

        out = [i18n.t("report_list_title"),
               "=" * len(i18n.t("report_list_title")),
               f"{i18n.t('report_generated')}: "
               f"{datetime.now().isoformat(timespec='seconds')}",
               i18n.t("shown_count", shown=len(self._rows),
                      total=len(self.sessions))]
        if self.view.get("period_on"):
            out.append(f"{i18n.t('filter_period')}: "
                       f"{self.view.get('period_from')} – {self.view.get('period_to')}")
        out += ["", "  ".join(h.ljust(widths[i]) for i, h in enumerate(head)).rstrip(),
                "  ".join("-" * w for w in widths)]
        for row in table:
            out.append("  ".join(v.ljust(widths[i])
                                 for i, v in enumerate(row)).rstrip())
        return "\n".join(out) + "\n"

    def _list_csv(self) -> str:
        visible = self._visible_columns()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([c.key for c in visible])
        for entry in self._rows:
            row = []
            for column in visible:
                raw = columns.value(entry, column)
                row.append("" if raw is None else
                           (f"{raw:.4f}" if isinstance(raw, float) else str(raw)))
            writer.writerow(row)
        return buffer.getvalue()

    def _export_list(self) -> None:
        language = ask_export_language(self)
        if language is None:
            return
        suggestion = str(storage.root() / "sessions.txt")
        path, chosen = QtWidgets.QFileDialog.getSaveFileName(
            self, i18n.t("export_list_title"), suggestion, i18n.t("export_filter"))
        if not path:
            return
        if not Path(path).suffix:
            path += ".csv" if "csv" in (chosen or "").lower() else ".txt"

        try:
            with export_language(language):
                text = (self._list_csv() if path.lower().endswith(".csv")
                        else self._list_report())
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            debuglog.record_exception("main.export_list", exc)
            QtWidgets.QMessageBox.warning(self, i18n.t("export_failed"), str(exc))
            return
        QtWidgets.QMessageBox.information(
            self, i18n.t("export_list_title"), i18n.t("exported", path=path))

    def _play_entry(self, entry: dict) -> None:
        path = storage.path_for(entry.get("file", ""))
        if not path.exists():
            self.status.showMessage(i18n.t("file_missing"))
            return
        try:
            data, rate = audio_mod.read_wav(path)
            sd.play(data, rate)
        except Exception as exc:
            debuglog.record_exception("main.play", exc)
            self.status.showMessage(str(exc))

    def _selected_entries(self) -> list[dict]:
        rows = sorted({index.row() for index in
                       self.table.selectionModel().selectedRows()})
        return [e for e in (self._entry_at(r) for r in rows) if e is not None]

    # -- Fortschritt, Vergleich, Referenz ---------------------------------

    def _open_progress(self) -> None:
        self.open_dialog(ProgressDialog(self.sessions, self))

    def _compare_selected(self) -> None:
        picked = self._selected_entries()
        if not 2 <= len(picked) <= progress.MAX_COMPARE:
            QtWidgets.QMessageBox.information(
                self, i18n.t("compare_title"), i18n.t("compare_pick_two"))
            return
        self._open_compare(picked)

    def _open_compare(self, picked: list[dict]) -> None:
        dialog = CompareDialog(picked, self)
        dialog.play_requested.connect(self._play_entry)
        self.open_dialog(dialog)

    def _set_reference(self, entry: dict | None) -> None:
        settings.set_reference_file(entry.get("file") if entry else None)
        if entry is not None:
            self.status.showMessage(i18n.t(
                "reference_saved", name=columns.display_name(entry)))
        self._fill_session_table()
        self._update_reference_button()

    def _play_selected(self) -> None:
        entry = self._entry_at(self.table.currentRow())
        if entry is not None:
            self._play_entry(entry)

    def store_recording(self, samples: np.ndarray, type_key: str,
                        span: tuple[float, float] | None = None,
                        rate: int | None = None,
                        stamp: datetime | None = None,
                        stem: str | None = None,
                        refresh: bool = True) -> dict:
        """WAV schreiben, auswerten und in die Historie aufnehmen.

        rate gehoert zu den Abtastwerten und ist ohne Angabe die des
        Aufnahmegeraets. Eine importierte Datei bringt ihre eigene mit —
        mit der falschen laegen Tonhoehe und Formanten um genau deren
        Verhaeltnis daneben.

        stamp ist der Zeitpunkt der Aufnahme, nicht der des Speicherns.
        Beim Import steht dort das Aenderungsdatum der Datei, damit sie im
        Ordner ihres Monats landet und in der Liste an der richtigen
        Stelle steht.

        stem ist ein mitgebrachter Name ohne Endung. Beim Import steht
        dort der Name der Quelldatei, damit die Aufnahme in der Liste unter
        dem Namen auftaucht, unter dem sie vorher auf der Platte lag. Der
        Zaehler wird dabei nicht weitergedreht — er steht ja gar nicht im
        Namen.

        refresh=False laesst Speichern und Tabellenaufbau aus — beim
        Import ueber mehrere Dateien lohnt sich das erst am Ende.
        """
        rate = int(rate or self.sr)
        stamp = stamp or datetime.now()
        name = (storage.relative_name(stamp, type_key, stem=stem) if stem
                else storage.next_name(stamp, type_key))
        path = storage.free_path(storage.root() / name)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_wav(path, samples, rate)
        name = path.relative_to(storage.root()).as_posix()

        # Die vollstaendige Auswertung braucht rund 0,13 s je Sekunde Audio
        # und laeuft im UI-Thread. Wenigstens sichtbar machen, dass gerechnet
        # wird, statt das Fenster stumm einfrieren zu lassen.
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        try:
            stats = analysis.analyse_recording(samples, rate)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

        entry = {"timestamp": stamp.isoformat(timespec="seconds"),
                 "file": name, "type": type_key, **stats}
        self._add_target_share(entry, samples, rate)
        if span is not None:
            entry["selection"] = [round(span[0], 3), round(span[1], 3)]

        self.sessions.append(entry)
        if refresh:
            self._save_sessions()
            self._fill_session_table()
        return entry

    @staticmethod
    def _add_target_share(entry: dict, samples: np.ndarray, rate: int) -> None:
        """Anteil der Aufnahme im F0-Zielbereich des Auswertungsprofils.

        Bleibt weg, wenn kein Ziel gewaehlt ist oder nichts Stimmhaftes da
        ist — eine 0 waere dann eine Behauptung statt einer Messung.
        """
        if entry.get("quality", "ok") != "ok":
            return
        profile = settings.get_profile()
        span = targets.range_for("f0_median", profile)
        try:
            share = progress.target_share(analysis.voiced_f0(samples, rate),
                                          span)
        except Exception as exc:
            debuglog.record_exception("main.target_share", exc)
            return
        if share is not None:
            entry["target_hit_pct"] = round(share, 1)
            entry["target_profile"] = profile

    # -- Import ------------------------------------------------------------

    def _import_files(self) -> None:
        """Vorhandene WAV-Dateien in die Sessionliste aufnehmen.

        Die Dateien werden kopiert, nicht verschoben: das Original liegt
        oft in einem Ordner, den jemand anderes verwaltet, und ein Umzug
        aus der Sessionliste heraus wuerde es dort wegnehmen.
        """
        paths_chosen, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, i18n.t("import_title"), str(Path.home()),
            i18n.t("import_filter"))
        if not paths_chosen:
            return

        type_key = self._ask_import_type(len(paths_chosen))
        if type_key is None:
            return

        added, failed = self._import_all(paths_chosen, type_key)

        if added:
            self._save_sessions()
            self._fill_session_table()
            self.status.showMessage(i18n.t("import_done", count=added))
        if failed:
            QtWidgets.QMessageBox.warning(
                self, i18n.t("import_failed_title"),
                i18n.t("import_failed_body", count=len(failed))
                + "\n\n" + "\n".join(failed[:12]))
        elif not added:
            self.status.showMessage(i18n.t("import_nothing"))

    def _ask_import_type(self, count: int) -> str | None:
        """Ein Typ fuer alle gewaehlten Dateien.

        Je Datei zu fragen waere bei einem Ordner voller Aufnahmen eine
        Klickstrecke; wer sie doch einzeln braucht, aendert den Typ danach
        im Kontextmenue der Liste.
        """
        kinds = rectypes.all_types()
        labels = [kind.label for kind in kinds]
        current = max(0, [k.key for k in kinds].index(
            rectypes.get(settings.get_recording_type()).key))
        choice, ok = QtWidgets.QInputDialog.getItem(
            self, i18n.t("import_title"), i18n.t("import_type", count=count),
            labels, current, False)
        if not ok:
            return None
        for kind in kinds:
            if kind.label == choice:
                return kind.key
        return rectypes.DEFAULT

    def _import_all(self, paths_chosen, type_key: str) -> tuple[int, list[str]]:
        """Reihum einlesen und ablegen. Zurueck kommt (Anzahl, Fehlerzeilen).

        Eine Datei, die sich nicht lesen laesst, beendet den Durchgang
        nicht — bei zwanzig ausgewaehlten Dateien waere sonst eine kaputte
        genug, um die anderen neunzehn zu verlieren.
        """
        added, failed = 0, []
        for number, raw in enumerate(paths_chosen, start=1):
            source = Path(raw)
            self.status.showMessage(
                i18n.t("import_running", number=number,
                       total=len(paths_chosen), name=source.name))
            QtWidgets.QApplication.processEvents()
            try:
                samples, rate = audio_mod.read_wav(source)
                if samples.size < int(0.2 * rate):
                    raise ValueError(i18n.t("import_too_short"))
                # Das Aenderungsdatum ist das Naechste, was eine Datei an
                # Aufnahmezeitpunkt hergibt. Es entscheidet ueber den
                # Monatsordner und den Platz in der Liste.
                stamp = datetime.fromtimestamp(source.stat().st_mtime)
                self.store_recording(samples, type_key, rate=rate,
                                     stamp=stamp,
                                     stem=naming.clean_stem(source.stem),
                                     refresh=False)
                added += 1
            except Exception as exc:
                debuglog.record_exception("main.import_files", exc)
                failed.append(f"{source.name}: {exc}")
        return added, failed
