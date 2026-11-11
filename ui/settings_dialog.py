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

"""Einstellungsdialog. Die Felder werden aus settings.PARAMS erzeugt,
neue Parameter dort eintragen reicht also aus."""

from __future__ import annotations

from dataclasses import asdict

from PySide6 import QtCore, QtWidgets

from core import i18n
from core import settings
from ui.theming import COLORS as NORD
from core.settings import PARAMS, Settings
from ui.changelog import (ChangelogDialog, HighlightsDialog)
from ui.debug_dialog import DebugDialog
from ui.design_editor import DesignEditor
from ui.dialog_common import CUSTOM_LABEL
from ui.info_page import InfoPage
from ui.options_page import OptionsPage
from ui.profile_editor import ProfileEditor


class SettingsDialog(QtWidgets.QDialog):
    """Aenderungen werden per applied-Signal sofort weitergereicht."""

    applied = QtCore.Signal()
    theme_changed = QtCore.Signal()
    intro_requested = QtCore.Signal()
    storage_changed = QtCore.Signal()
    types_changed = QtCore.Signal()

    def __init__(self, parent=None, entries: list[dict] | None = None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("dlg_settings"))
        self.setMinimumSize(660, 660)
        self.resize(720, 820)

        self._spins: dict[str, QtWidgets.QDoubleSpinBox] = {}
        self._loading = False

        root = QtWidgets.QVBoxLayout(self)
        root.setSpacing(14)

        analysis_page = QtWidgets.QWidget()
        analysis_lay = QtWidgets.QVBoxLayout(analysis_page)
        analysis_lay.setContentsMargins(0, 8, 0, 0)
        analysis_lay.addWidget(self._build_template_row())
        analysis_lay.addWidget(self._build_spectrogram_group())
        analysis_lay.addWidget(self._build_training_group())

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._build_params_group())
        analysis_lay.addWidget(scroll, 1)

        # Reihenfolge nach Haeufigkeit, mit der man sie braucht: Optionen
        # und Analyse aendert man gelegentlich, Design einmal, Info liest
        # man nach. Angezeigt wird trotzdem Info — siehe unten.
        self.tabs = QtWidgets.QTabWidget()

        # Ordner und Dateinamen. Der Reiter ist hoch, also in eine Rolle —
        # sonst wandert der Umzugsknopf auf kleinen Bildschirmen unter den
        # unteren Rand des Dialogs.
        self.options = OptionsPage(entries)
        self.options.changed.connect(self.storage_changed)
        self.options.types_changed.connect(self.types_changed)
        options_page = QtWidgets.QScrollArea()
        options_page.setWidgetResizable(True)
        options_page.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        options_page.setWidget(self.options)
        self.tabs.addTab(options_page, i18n.t("tab_options"))

        self.tabs.addTab(analysis_page, i18n.t("tab_analysis"))
        self.profiles = ProfileEditor()
        self.tabs.addTab(self.profiles, i18n.t("tab_profiles"))

        self.design = DesignEditor()
        self.design.changed.connect(self.theme_changed)
        design_page = QtWidgets.QScrollArea()
        design_page.setWidgetResizable(True)
        design_page.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        design_page.setWidget(self.design)
        self.tabs.addTab(design_page, i18n.t("tab_design"))

        self.info = InfoPage()
        self.info.intro_requested.connect(self.intro_requested)
        self.info.debug_requested.connect(self._open_debug)
        self.info.changelog_requested.connect(self._open_changelog)
        self.info.highlights_requested.connect(self._open_highlights)
        self.tabs.addTab(self.info, i18n.t("tab_info"))
        # Info sitzt hinten, wird aber als erstes gezeigt: dort liegen
        # Version, Links, Debug und der Knopf, der die Einfuehrung erneut
        # zeigt — das, was man sucht, wenn man die Einstellungen ohne einen
        # bestimmten Parameter im Kopf oeffnet. Der Platz in der Leiste
        # richtet sich danach, wie oft man etwas aendert, die Startseite
        # danach, was man beim blossen Aufmachen wissen will; das ist
        # nicht dasselbe.
        self.tabs.setCurrentWidget(self.info)
        root.addWidget(self.tabs, 1)

        note = QtWidgets.QLabel(i18n.t("settings_note"))
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {NORD['dim']};")
        root.addWidget(note)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Apply
        )
        SB = QtWidgets.QDialogButtonBox.StandardButton
        buttons.button(SB.Ok).setText(i18n.t("ok"))
        buttons.button(SB.Cancel).setText(i18n.t("cancel"))
        buttons.button(SB.Apply).setText(i18n.t("apply"))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self._reject)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Apply
                       ).clicked.connect(self._apply)

        root.addWidget(buttons)

        self._before = settings.snapshot()
        self._before_template = settings.active_template()
        self._before_guides = settings.get_formant_guides()
        self._before_break = settings.get_break_minutes()
        self._before_storage = self.options.snapshot()
        self._refresh_templates()
        self._load_values(self._before)

    # -- Aufbau ----------------------------------------------------------

    def _build_template_row(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("template"))
        lay = QtWidgets.QHBoxLayout(box)

        self.template_box = QtWidgets.QComboBox()
        self.template_box.currentIndexChanged.connect(self._template_chosen)

        self.btn_save = QtWidgets.QPushButton(i18n.t("save_as"))
        self.btn_save.clicked.connect(self._save_template)
        self.btn_delete = QtWidgets.QPushButton(i18n.t("delete"))
        self.btn_delete.clicked.connect(self._delete_template)

        lay.addWidget(self.template_box, 1)
        lay.addWidget(self.btn_save)
        lay.addWidget(self.btn_delete)
        return box

    def _build_spectrogram_group(self) -> QtWidgets.QWidget:
        """Was im Spektrogramm zusaetzlich zu sehen ist.

        Steht bei der Analyse und nicht bei den Optionen: die Optionen
        handeln von Ordnern und Dateinamen, das hier von dem, was die
        Messung zeigt.
        """
        box = QtWidgets.QGroupBox(i18n.t("adv_spectrogram"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(4)

        self.chk_guides = QtWidgets.QCheckBox(i18n.t("opt_formant_guides"))
        self.chk_guides.setChecked(settings.get_formant_guides())
        lay.addWidget(self.chk_guides)

        hint = QtWidgets.QLabel(i18n.t("opt_formant_guides_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        lay.addWidget(hint)
        return box

    def _build_training_group(self) -> QtWidgets.QWidget:
        """Pausen-Erinnerung: wie lange am Stueck, bevor das Programm mahnt."""
        box = QtWidgets.QGroupBox(i18n.t("adv_training"))
        lay = QtWidgets.QVBoxLayout(box)
        lay.setSpacing(4)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel(i18n.t("opt_break")))
        self.spin_break = QtWidgets.QSpinBox()
        self.spin_break.setRange(0, settings.BREAK_MAX)
        self.spin_break.setSuffix(" min")
        self.spin_break.setSpecialValueText(i18n.t("opt_break_off"))
        self.spin_break.setValue(settings.get_break_minutes())
        row.addWidget(self.spin_break)
        row.addStretch(1)
        lay.addLayout(row)

        hint = QtWidgets.QLabel(i18n.t("opt_break_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
        lay.addWidget(hint)
        return box

    def _build_params_group(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox(i18n.t("parameters"))
        # Direktes Grid statt verschachtelter Widgets: nur so berechnet Qt
        # die Hoehe umbrechender Hinweistexte richtig.
        grid = QtWidgets.QGridLayout(box)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(1, 150)

        row = 0
        for param in PARAMS:
            attr, unit = param.attr, param.unit
            lo, hi, step, decimals = param.lo, param.hi, param.step, param.decimals
            label, tip = param.label, param.hint
            if row:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
                line.setStyleSheet(f"color: {NORD['bg3']};")
                grid.addWidget(line, row, 0, 1, 2)
                row += 1

            caption = QtWidgets.QLabel(label)
            caption.setStyleSheet("font-weight: 600;")
            grid.addWidget(caption, row, 0,
                           QtCore.Qt.AlignmentFlag.AlignLeft
                           | QtCore.Qt.AlignmentFlag.AlignVCenter)

            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(lo, hi)
            spin.setSingleStep(step)
            spin.setDecimals(decimals)
            if unit:
                spin.setSuffix(f" {unit}")
            spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight
                              | QtCore.Qt.AlignmentFlag.AlignVCenter)
            spin.valueChanged.connect(self._value_changed)
            self._spins[attr] = spin
            grid.addWidget(spin, row, 1)
            row += 1

            hint = QtWidgets.QLabel(tip)
            hint.setWordWrap(True)
            hint.setStyleSheet(f"color: {NORD['dim']}; font-size: 11px;")
            hint.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                               QtWidgets.QSizePolicy.Policy.Minimum)
            grid.addWidget(hint, row, 0, 1, 2)
            grid.setRowMinimumHeight(row, 20)
            row += 1
            grid.setRowMinimumHeight(row, 8)
            row += 1
        return box

    def _open_debug(self) -> None:
        dialog = self._show(DebugDialog(self))
        dialog.finished.connect(self.info.update_debug_badge)

    def _open_changelog(self) -> None:
        self._show(ChangelogDialog(self))

    def _open_highlights(self) -> None:
        self._show(HighlightsDialog(self))

    @staticmethod
    def _show(dialog: QtWidgets.QDialog) -> QtWidgets.QDialog:
        """Nicht-modal, damit das Hauptfenster schliessbar bleibt."""
        dialog.setModal(False)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.show()
        dialog.raise_()
        return dialog

    # -- Vorlagen --------------------------------------------------------

    def _refresh_templates(self, select: str | None = None) -> None:
        """Der Schluessel steht in den Daten, der Name nur in der Anzeige.

        Nur so heisst eine eingebaute Vorlage in der englischen Oberflaeche
        auch englisch und die Konfiguration bleibt trotzdem lesbar.
        """
        self._loading = True
        self.template_box.clear()
        self.template_box.addItem(CUSTOM_LABEL(), "")
        for name in settings.all_templates():
            self.template_box.addItem(settings.template_label(name), name)
        target = select or settings.active_template()
        idx = self.template_box.findData(target)
        self.template_box.setCurrentIndex(idx if idx >= 0 else 0)
        self._loading = False
        self._update_delete_state()

    def _current_template(self) -> str:
        return self.template_box.currentData() or ""

    def _update_delete_state(self) -> None:
        name = self._current_template()
        self.btn_delete.setEnabled(
            bool(name) and not settings.is_builtin(name))

    def _template_chosen(self) -> None:
        self._update_delete_state()
        if self._loading:
            return
        name = self._current_template()
        template = settings.all_templates().get(name)
        if template is not None:
            self._load_values(template)

    def _save_template(self) -> None:
        current = self._current_template()
        suggestion = "" if not current or settings.is_builtin(current) else current
        name, ok = QtWidgets.QInputDialog.getText(
            self, i18n.t("template_save_title"), i18n.t("name"), text=suggestion)
        name = name.strip()
        if not ok or not name:
            return
        if settings.is_builtin(name):
            QtWidgets.QMessageBox.warning(
                self, i18n.t("name_taken"), i18n.t("name_taken_body"))
            return
        settings.save_template(name, self._collect())
        self._refresh_templates(select=name)

    def _delete_template(self) -> None:
        name = self._current_template()
        if not name or settings.is_builtin(name):
            return
        answer = QtWidgets.QMessageBox.question(
            self, i18n.t("template_delete_title"),
            i18n.t("template_delete_body", name=name))
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            settings.delete_template(name)
            self._refresh_templates(select=settings.DEFAULT_TEMPLATE)

    # -- Werte -----------------------------------------------------------

    def _load_values(self, values: Settings) -> None:
        self._loading = True
        data = asdict(values)
        for attr, spin in self._spins.items():
            spin.setValue(data[attr])
        self._loading = False

    def _collect(self) -> Settings:
        return Settings(**{a: s.value() for a, s in self._spins.items()}).clamped()

    def _value_changed(self) -> None:
        if self._loading:
            return
        # Handbearbeitung loest die Vorlagenbindung.
        name = self._current_template()
        template = settings.all_templates().get(name)
        if template is not None and asdict(template) != asdict(self._collect()):
            self._loading = True
            self.template_box.setCurrentIndex(0)
            self._loading = False
            self._update_delete_state()

    # -- Aktionen --------------------------------------------------------

    def _apply(self) -> bool:
        """False, wenn der gewaehlte Aufnahmeordner nicht beschreibbar ist.

        Dann bleibt der Dialog offen: mit "OK" wegzugehen und die Aufnahmen
        stillschweigend woanders zu haben, waere die unangenehmere Variante.
        """
        values = self._collect()
        settings.apply(values)
        settings.set_active_template(self._current_template())
        settings.set_formant_guides(self.chk_guides.isChecked())
        settings.set_break_minutes(self.spin_break.value())
        settings.save()
        self._load_values(settings.snapshot())
        self.applied.emit()
        return self.options.store()

    def _accept(self) -> None:
        if self._apply():
            self.accept()

    def _reject(self) -> None:
        # Auch ein zwischenzeitliches "Anwenden" wird zurueckgerollt,
        # inklusive der bereits geschriebenen config.json. Der Umzug ist
        # davon ausgenommen — verschobene Dateien holt niemand zurueck,
        # deshalb wendet der Umzugsknopf seine Auswahl auch sofort an.
        settings.apply(self._before)
        settings.set_active_template(self._before_template)
        settings.set_formant_guides(self._before_guides)
        settings.set_break_minutes(self._before_break)
        settings.save()
        self.options.restore(self._before_storage)
        self.applied.emit()
        self.storage_changed.emit()
        self.reject()
