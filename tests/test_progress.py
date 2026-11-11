"""Fortschritt, Serie, Vergleich, Ziel-Anteil, Referenz und Pausen-Erinnerung."""

from datetime import date

import numpy as np

from core import progress


def _entry(stamp, **values):
    return {"timestamp": stamp, "file": f"{stamp}.wav", "quality": "ok",
            "type": "reading", **values}


ENTRIES = [
    _entry("2026-11-01T10:00:00", f0_median=150.0, f2_median=1500.0),
    _entry("2026-11-03T10:00:00", f0_median=170.0),
    _entry("2026-11-02T10:00:00", f0_median=160.0, type="hum"),
    {"timestamp": "2026-11-04T10:00:00", "file": "leer.wav",
     "quality": "kein_signal", "f0_median": None},
]


def test_verlauf_ist_sortiert_und_ohne_stille():
    points = progress.series(ENTRIES, "f0_median")
    assert [v for _, v in points] == [150.0, 160.0, 170.0]


def test_verlauf_nach_typ():
    points = progress.series(ENTRIES, "f0_median", "hum")
    assert [v for _, v in points] == [160.0]


def test_verlauf_unbekannte_spalte():
    assert progress.series(ENTRIES, "label") == []
    assert progress.series(ENTRIES, "gibt_es_nicht") == []


def test_gleitender_mittelwert():
    assert progress.moving_average([1, 2, 3, 4], window=2) == [1, 1.5, 2.5, 3.5]


def test_serie_zaehlt_tage_in_folge():
    entries = [_entry(f"2026-11-{d:02d}T09:00:00") for d in (5, 6, 7, 9, 10)]
    assert progress.streak(entries, today=date(2026, 11, 10)) == 2
    # Heute noch nicht geuebt: die Serie von gestern steht noch.
    assert progress.streak(entries, today=date(2026, 11, 11)) == 2
    assert progress.streak(entries, today=date(2026, 11, 12)) == 0
    assert progress.streak(entries, today=date(2026, 11, 7)) == 3


def test_woche_zaehlt_aufnahmen():
    entries = [_entry(f"2026-11-{d:02d}T09:00:00") for d in (1, 4, 5, 10, 10)]
    assert progress.week_count(entries, today=date(2026, 11, 10)) == 4


def test_ziel_anteil():
    values = [100, 150, 200, float("nan"), 0, 250]
    assert progress.target_share(values, (140.0, 210.0)) == 50.0
    assert progress.target_share(values, (None, 120.0)) == 25.0
    assert progress.target_share(values, None) is None
    assert progress.target_share([], (1.0, 2.0)) is None


def test_vergleich_rechnet_unterschied():
    rows = {c.key: (v, d) for c, v, d in
            progress.compare(ENTRIES[0], ENTRIES[1])}
    assert rows["f0_median"] == ([150.0, 170.0], 20.0)
    assert rows["f2_median"] == ([1500.0, None], None)
    assert "hnr" not in rows


def test_vergleich_mit_vier():
    rows = {c.key: (v, d) for c, v, d in progress.compare(*ENTRIES)}
    assert rows["f0_median"][0] == [150.0, 170.0, 160.0, None]
    assert rows["f0_median"][1] is None


def test_fortschrittsfenster(qt_app):
    from ui.progress_dialog import ProgressDialog

    dialog = ProgressDialog(ENTRIES)
    assert "150" in dialog.summary.text() and "+20" in dialog.summary.text()
    dialog.metric_box.setCurrentIndex(dialog.metric_box.findData("hnr"))
    assert dialog.summary.text()
    dialog.close()


def test_vergleichsfenster_aelter_links(qt_app):
    from ui.compare_dialog import CompareDialog

    dialog = CompareDialog([ENTRIES[1], ENTRIES[0]])
    assert dialog.entries[0] is ENTRIES[0]
    texts = [dialog.table.item(r, 3).text()
             for r in range(dialog.table.rowCount())]
    assert "+20 Hz" in texts
    dialog.close()


def test_vergleichsfenster_bis_vier(qt_app):
    from ui.compare_dialog import CompareDialog

    fuenf = ENTRIES[:3] + [_entry("2026-11-05T10:00:00", f0_median=180.0),
                           _entry("2026-11-06T10:00:00", f0_median=190.0)]
    dialog = CompareDialog(fuenf)
    assert len(dialog.entries) == 4
    assert dialog.table.columnCount() == 6
    texts = [dialog.table.item(r, 5).text()
             for r in range(dialog.table.rowCount())]
    assert "+30 Hz" in texts
    dialog.close()


def test_fortschritt_zielstimme_waehlbar(qt_app):
    from PySide6 import QtWidgets
    from ui.progress_dialog import ProgressDialog

    dialog = ProgressDialog(ENTRIES)
    dialog.profile_box.setCurrentIndex(dialog.profile_box.findData("none"))
    ohne = len(dialog.plot.getPlotItem().items)
    dialog.profile_box.setCurrentIndex(dialog.profile_box.findData("feminin"))
    mit = len(dialog.plot.getPlotItem().items)
    assert mit > ohne
    dialog.close()
    QtWidgets.QApplication.processEvents()


def test_ziel_anteil_landet_in_der_aufnahme(intro_window, monkeypatch):
    from core import settings
    from voice import analysis

    monkeypatch.setattr(settings, "get_profile", lambda: "feminin")
    monkeypatch.setattr(analysis, "voiced_f0",
                        lambda samples, rate: np.array([150.0, 200.0, 220.0, 260.0]))
    entry = {"quality": "ok"}
    intro_window._add_target_share(entry, np.zeros(10), 16000)
    assert entry["target_hit_pct"] == 50.0
    assert entry["target_profile"] == "feminin"

    monkeypatch.setattr(settings, "get_profile", lambda: "none")
    entry = {"quality": "ok"}
    intro_window._add_target_share(entry, np.zeros(10), 16000)
    assert "target_hit_pct" not in entry


def test_referenz_knopf(intro_window, monkeypatch):
    from core import settings

    stored = {}
    monkeypatch.setattr(settings, "get_reference_file",
                        lambda: stored.get("name"))
    monkeypatch.setattr(settings, "set_reference_file",
                        lambda name: stored.__setitem__("name", name))
    intro_window._update_reference_button()
    assert not intro_window.btn_reference.isEnabled()

    played = []
    monkeypatch.setattr(intro_window, "_play_entry", played.append)
    stored["name"] = "probe.wav"
    intro_window._play_reference()
    assert played == [{"file": "probe.wav"}]


def test_pausen_erinnerung_kommt_einmal(intro_window, monkeypatch):
    from core import settings

    monkeypatch.setattr(settings, "get_break_minutes", lambda: 1)
    shown = []
    monkeypatch.setattr(intro_window, "open_dialog", shown.append)

    class Uhr:
        def __init__(self, ms):
            self.ms = ms

        def elapsed(self):
            return self.ms

    monkeypatch.setattr(intro_window, "elapsed", Uhr(30_000))
    intro_window._check_break()
    assert shown == []
    monkeypatch.setattr(intro_window, "elapsed", Uhr(61_000))
    intro_window._check_break()
    intro_window._check_break()
    assert len(shown) == 1
    shown[0].deleteLater()


def test_pausen_erinnerung_aus(intro_window, monkeypatch):
    from core import settings

    monkeypatch.setattr(settings, "get_break_minutes", lambda: 0)
    monkeypatch.setattr(intro_window, "open_dialog",
                        lambda d: (_ for _ in ()).throw(AssertionError))
    intro_window._check_break()


def test_pausen_minuten_werden_begrenzt(monkeypatch):
    from core import settings

    monkeypatch.setattr(settings, "save", lambda: None)
    before = settings.get_break_minutes()
    try:
        settings.set_break_minutes(9999)
        assert settings.get_break_minutes() == settings.BREAK_MAX
        settings.set_break_minutes(-5)
        assert settings.get_break_minutes() == 0
    finally:
        settings.set_break_minutes(before)
