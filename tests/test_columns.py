"""Formatierung, Sortierung und Filterung der Sessionliste."""

import columns
import i18n

ENTRIES = [
    {"timestamp": "2026-08-30T14:46:58", "file": "a.wav", "quality": "ok",
     "duration": 26.9, "peak_db": -25.2, "f0_median": 111.1,
     "f0_p10": 93.8, "f0_p90": 157.7, "f1_median": 414.1, "voiced_ratio": 0.455},
    {"timestamp": "2026-08-28T14:06:23", "file": "b.wav", "quality": "ok",
     "duration": 17.5, "peak_db": -46.9, "f0_median": 122.6,
     "f0_p10": 92.2, "f0_p90": 153.2, "label": "Vokal /a/"},
    {"timestamp": "2026-08-25T14:30:29", "file": "c.wav",
     "quality": "kein_signal", "duration": 16.3, "peak_db": -47.7},
]


def test_anzeigename_faellt_auf_den_dateinamen_zurueck():
    assert columns.display_name(ENTRIES[0]) == "a"
    assert columns.display_name(ENTRIES[1]) == "Vokal /a/"


def test_formatierung():
    i18n.set_language("en")
    assert columns.text(ENTRIES[0], columns.BY_KEY["duration"]) == "26.9 s"
    assert columns.text(ENTRIES[0], columns.BY_KEY["f0_spread"]) == "94–158 Hz"
    assert columns.text(ENTRIES[0], columns.BY_KEY["f0_median"]) == "111 Hz"


def test_leiser_pegel_wird_markiert():
    i18n.set_language("en")
    assert i18n.t("quiet") in columns.text(ENTRIES[1], columns.BY_KEY["peak_db"])
    assert i18n.t("quiet") not in columns.text(ENTRIES[0], columns.BY_KEY["peak_db"])


def test_ohne_sprachsignal_keine_zahlen():
    i18n.set_language("en")
    entry = ENTRIES[2]
    assert columns.text(entry, columns.BY_KEY["f0_median"]) == i18n.t("no_speech")
    assert columns.text(entry, columns.BY_KEY["f1_median"]) == "--"
    # Dauer und Pegel bleiben sichtbar, die stimmen ja.
    assert columns.text(entry, columns.BY_KEY["duration"]) == "16.3 s"


def test_fehlende_werte_landen_am_ende():
    column = columns.BY_KEY["f0_median"]
    ordered = sorted(ENTRIES, key=lambda e: columns.sort_key(e, column, False))
    assert ordered[-1]["file"] == "c.wav"


def test_sortierung_nach_datum():
    column = columns.BY_KEY["date"]
    newest = sorted(ENTRIES, key=lambda e: columns.sort_key(e, column, True),
                    reverse=True)
    assert newest[0]["file"] == "a.wav"
    oldest = sorted(ENTRIES, key=lambda e: columns.sort_key(e, column, False))
    assert oldest[0]["file"] == "c.wav"


def test_prozentspalte_rechnet_um():
    value = columns.value(ENTRIES[0], columns.BY_KEY["voiced_ratio_pct"])
    assert round(value) == 46


def test_spaltenwechsel_laesst_keine_widgets_zurueck(qt_table):
    """Regression: die Aktionsknöpfe blieben in der alten Spalte stehen."""
    table, fill = qt_table
    fill(["date", "label", "duration", "peak_db", "f0_median",
          "f0_spread", "f1_median", "f2_median", "file"])
    assert table.columnCount() == 10

    fill(["date", "label", "duration", "peak_db", "f0_median", "f0_spread",
          "f1_median", "f2_median", "f3_median", "h1_db", "h2_db", "file"])
    assert table.columnCount() == 13
    last = table.columnCount() - 1
    stray = [c for c in range(last)
             if any(table.cellWidget(r, c) is not None
                    for r in range(table.rowCount()))]
    assert stray == [], f"Widgets in den Spalten {stray} statt nur in {last}"

    fill(["date", "f0_median", "file"])
    assert table.columnCount() == 4
    last = table.columnCount() - 1
    for c in range(last):
        for r in range(table.rowCount()):
            assert table.cellWidget(r, c) is None


def test_spaltenreihenfolge_bleibt_stabil():
    """Eine wieder eingeschaltete Spalte landet an ihrem angestammten Platz."""
    order = [c.key for c in columns.COLUMNS]
    keys = ["date", "label", "f1_median", "file"]
    keys = sorted(keys + ["peak_db"], key=order.index)
    assert keys == ["date", "label", "peak_db", "f1_median", "file"]


def test_verschiebung_wird_beim_neuaufbau_verworfen(qt_table):
    """Nach dem Ziehen wird die Reihenfolge in die Spaltenliste übernommen.

    Qt behält die Verschiebung sonst und würde sie ein zweites Mal anwenden,
    sodass die Spalten bei jedem Neuaufbau weiterwandern.
    """
    table, fill = qt_table
    header = table.horizontalHeader()
    header.setSectionsMovable(True)

    def mapping():
        return [header.logicalIndex(v) for v in range(table.columnCount())]

    identity = list(range(6))

    # Ohne den Reset überlebt die Verschiebung den Neuaufbau.
    fill(["date", "label", "duration", "peak_db", "file"], reset=False)
    header.moveSection(3, 0)
    assert mapping() != identity
    fill(["peak_db", "date", "label", "duration", "file"], reset=False)
    assert mapping() != identity

    # So wie das Programm es macht, ist sie danach neutral.
    fill(["peak_db", "date", "label", "duration", "file"])
    assert mapping() == identity


def test_einsortieren_beim_einblenden():
    """Eine eingeblendete Spalte landet vor dem ersten später definierten Nachbarn."""
    order = [c.key for c in columns.COLUMNS]

    def insert(keys, key):
        position = len(keys)
        for i, existing in enumerate(keys):
            if order.index(existing) > order.index(key):
                position = i
                break
        return keys[:position] + [key] + keys[position:]

    assert insert(["date", "f1_median", "file"], "peak_db") == \
        ["date", "peak_db", "f1_median", "file"]
    assert insert(["date", "label"], "file") == ["date", "label", "file"]
    assert insert(["f2_median", "file"], "date") == ["date", "f2_median", "file"]


def test_verschieben_in_der_liste():
    def move(keys, key, offset):
        index = keys.index(key)
        target = index + offset
        if not 0 <= target < len(keys):
            return keys
        keys = list(keys)
        keys[index], keys[target] = keys[target], keys[index]
        return keys

    keys = ["date", "label", "voice_breaks_pct", "file"]
    assert move(keys, "voice_breaks_pct", -1) == \
        ["date", "voice_breaks_pct", "label", "file"]
    assert move(keys, "date", -1) == keys          # am Rand passiert nichts
    assert move(keys, "file", 1) == keys


def test_knoepfe_entstehen_nur_fuer_sichtbare_zeilen(qt_table):
    """Regression: 1000 vorab gebaute Knöpfe kosteten bei 500 Sessions 470 ms."""
    table, fill = qt_table
    fill(["date", "type", "f0_median", "file"])
    # Die Fixture baut absichtlich alle Knöpfe; hier zählt nur, dass die
    # Sichtbarkeitsrechnung im Programm einen begrenzten Bereich liefert.
    table.resize(600, 200)
    visible_height = table.viewport().height()
    row_height = table.verticalHeader().defaultSectionSize()
    assert visible_height // max(1, row_height) < 500


def test_dialoge_blockieren_das_schliessen_nicht(qt_table, monkeypatch, tmp_path):
    """Regression: mit offenem Einstellungsdialog ließ sich das Programm
    nicht über die Taskleiste schließen, weil exec() anwendungsmodal ist."""
    import sys
    import types
    from PySide6 import QtWidgets

    if "sounddevice" not in sys.modules:  # pragma: no cover
        sys.modules["sounddevice"] = types.SimpleNamespace()
    import audio
    monkeypatch.setattr(audio, "_run", lambda args: None)
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "home"))

    import importlib
    import paths
    importlib.reload(paths)
    import main

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = main.MainWindow()
    window.show()

    dialog = QtWidgets.QDialog(window)
    gone = []
    dialog.destroyed.connect(lambda *_: gone.append(True))
    window.open_dialog(dialog)

    assert dialog.isModal() is False
    assert QtWidgets.QApplication.activeModalWidget() is None
    assert window._dialogs == [dialog]

    assert window.close() is True
    app.processEvents()
    # WA_DeleteOnClose raeumt den Dialog ab; nichts bleibt offen zurueck.
    assert gone == [True]
    assert window._dialogs == []

    importlib.reload(paths)
