"""Namensschema: Bausteine, Reihenfolge, Zaehler und die Optionen-Seite."""

from datetime import datetime

import pytest

import naming


STAMP = datetime(2026, 9, 7, 14, 30, 15)      # Montag, KW 37


@pytest.fixture
def store(tmp_path, monkeypatch):
    """storage mit eigenem Standardordner und leerem Schema."""
    import settings
    import storage

    default = tmp_path / "sessions"
    default.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(storage, "DEFAULT_ROOT", default)

    settings._state["session_dir"] = None
    settings._state["month_folders"] = False
    settings._state["type_in_name"] = False
    settings._state["naming"] = None
    settings._state["name_counter"] = {"period": "", "value": 0}
    monkeypatch.setattr(settings, "save", lambda: None)
    return storage


def scheme(**over):
    """Vorgabeschema mit gezielt geaenderten Werten."""
    base = naming.normalize(None)
    enabled = dict(base["enabled"])
    enabled.update(over.pop("enabled", {}))
    base.update(over)
    base["enabled"] = enabled
    return naming.normalize(base)


# ------------------------------------------------------------- Bausteine

def test_vorgabe_ist_das_alte_schema():
    """Wer nie in die Optionen schaut, darf nichts merken."""
    assert naming.build_stem(naming.DEFAULT, STAMP) == "2026-09-07_14-30-15"
    assert naming.build_folder(naming.DEFAULT, STAMP) == ""


def test_reihenfolge_bestimmt_den_namen():
    front = scheme(order=["prefix", "date", "time", "type", "counter",
                          "suffix", "year", "month", "week"],
                   enabled={"type": True, "prefix": True},
                   prefix="Voice-Training")
    assert naming.build_stem(front, STAMP, "vowel_a") == \
        "Voice-Training_2026-09-07_14-30-15_vowel-a"

    back = scheme(order=["date", "time", "type", "prefix", "counter",
                         "suffix", "year", "month", "week"],
                  enabled={"type": True, "prefix": True},
                  prefix="Voice-Training")
    assert naming.build_stem(back, STAMP, "vowel_a") == \
        "2026-09-07_14-30-15_vowel-a_Voice-Training"


def test_abgeschaltete_bausteine_behalten_ihren_platz():
    """Ein Baustein soll beim Wiedereinschalten dort landen, wo er stand."""
    order = ["prefix", "date", "week", "time", "type", "counter", "suffix",
             "year", "month"]
    aus = scheme(order=order, enabled={"week": False})
    an = scheme(order=order, enabled={"week": True})
    assert naming.build_stem(aus, STAMP) == "2026-09-07_14-30-15"
    assert naming.build_stem(an, STAMP) == "2026-09-07_KW37_14-30-15"


def test_monat_traegt_nur_den_monat_bei():
    """Sonst ergaeben Jahr und Monat zusammen 2026_2026-09."""
    nur = scheme(enabled={key: key == "month" for key in naming.BLOCKS})
    assert naming.build_stem(nur, STAMP) == "09"

    beides = scheme(enabled={key: key in ("year", "month")
                             for key in naming.BLOCKS})
    assert naming.build_stem(beides, STAMP) == "2026_09"


def test_monatsnamen_gelten_weiter_als_selbst_vergeben():
    """Sonst liesse ein Umzug die Dateien der alten Fassungen liegen."""
    assert naming.looks_generated("09") is True
    assert naming.looks_generated("2026_09_14-30-15") is True
    # Das alte Format aus den Fassungen bis 1.1.2 ebenfalls.
    assert naming.looks_generated("2026-09") is True
    # Eine zweistellige Zahl, die kein Monat sein kann, aber nicht.
    assert naming.looks_generated("42") is False


def test_uhrzeit_ohne_sekunden():
    kurz = scheme(seconds=False)
    assert naming.build_stem(kurz, STAMP) == "2026-09-07_14-30"


def test_zaehler_bekommt_die_eingestellten_stellen():
    drei = scheme(enabled={"counter": True})
    assert naming.build_stem(drei, STAMP, counter=7).endswith("_007")
    fuenf = scheme(enabled={"counter": True}, counter_digits=5)
    assert naming.build_stem(fuenf, STAMP, counter=7).endswith("_00007")


def test_leeres_schema_erzeugt_keinen_namenlosen_dateinamen():
    """Alles abgeschaltet darf nicht in einer Datei namens .wav enden."""
    leer = scheme(enabled={key: False for key in naming.BLOCKS})
    assert naming.build_stem(leer, STAMP) == "2026-09-07_14-30-15"


def test_freitext_wird_entschaerft():
    assert naming.clean_text("Voice Training") == "Voice-Training"
    assert naming.clean_text("a/b\\c:d*e") == "a-b-c-d-e"
    # Der Trenner selbst darf nicht im Freitext stehen, sonst laesst sich
    # ein fertiger Name nicht mehr in Bausteine zerlegen.
    assert "_" not in naming.clean_text("Pitch_Test")


def test_leerer_freitext_faellt_weg():
    still = scheme(enabled={"prefix": True, "suffix": True}, prefix="",
                   suffix="")
    assert naming.build_stem(still, STAMP) == "2026-09-07_14-30-15"


# ------------------------------------------------------------ Unterordner

@pytest.mark.parametrize("kind, expected", [
    ("none", ""),
    ("day", "2026-09-07"),
    ("week", "2026-KW37"),
    ("month", "2026-09"),
    ("year", "2026"),
])
def test_unterordner_je_zeitraum(kind, expected):
    assert naming.build_folder(scheme(subfolders=kind), STAMP) == expected


def test_monatsordner_behaelt_das_jahr():
    """Anders als der Namensbaustein.

    Der Ordnerschluessel steuert auch den Zaehler-Neustart. Ohne das Jahr
    landete der Januar 2027 im Ordner des Januars 2026.
    """
    assert naming.period_key("month", STAMP) == "2026-09"
    assert naming.period_key("month", datetime(2027, 9, 1)) == "2027-09"


def test_kalenderwoche_benutzt_das_iso_jahr():
    """Der 1. Januar 2027 gehoert noch in die letzte Woche von 2026."""
    silvester = datetime(2027, 1, 1, 12, 0, 0)
    assert naming.build_folder(scheme(subfolders="week"), silvester) == \
        "2026-KW53"


def test_kalenderwoche_bleibt_bei_einem_sprachwechsel_gleich():
    import i18n
    week = scheme(enabled={"week": True})
    i18n.set_language("de")
    deutsch = naming.build_stem(week, STAMP)
    i18n.set_language("en")
    assert naming.build_stem(week, STAMP) == deutsch


# ---------------------------------------------------------- Kaputte Werte

def test_unsinn_in_der_konfiguration_kippt_nichts():
    kaputt = naming.normalize({"subfolders": "woechentlich", "order": "nein",
                               "enabled": 7, "counter_digits": "viele",
                               "counter_reset": None})
    assert kaputt["subfolders"] == "none"
    assert kaputt["counter_reset"] == "never"
    assert kaputt["counter_digits"] == 3
    assert sorted(kaputt["order"]) == sorted(naming.BLOCKS)


def test_doppelte_und_fehlende_bausteine_werden_geradegezogen():
    krumm = naming.normalize({"order": ["date", "date", "time"]})
    assert krumm["order"][:2] == ["date", "time"]
    assert sorted(krumm["order"]) == sorted(naming.BLOCKS)


def test_uebernahme_aus_den_alten_schaltern():
    alt = naming.from_legacy(month_folders=True, type_in_name=True)
    assert alt["subfolders"] == "month"
    assert naming.relative(alt, STAMP, "hum") == \
        "2026-09/2026-09-07_14-30-15_hum.wav"


# ------------------------------------------------------- Erzeugte erkennen

@pytest.mark.parametrize("stem", [
    "2026-09-07_14-30-15",
    "2026-09-07_14-30-15_vowel-a",
    "2026-09-07_14-30_hum_001",
    "2026-09_KW37_14-30-15",
])
def test_erzeugte_namen_werden_erkannt(stem):
    assert naming.looks_generated(stem) is True


@pytest.mark.parametrize("stem", [
    "Morgenstimme",
    "Test vor dem Arzttermin",
    "hum",                       # nur ein Typ, kein Zeitbaustein
    "",
])
def test_selbst_vergebene_namen_bleiben_unangetastet(stem):
    assert naming.looks_generated(stem) is False


def test_eigener_freitext_zaehlt_als_erzeugt():
    mit = scheme(enabled={"prefix": True}, prefix="Voice-Training")
    assert naming.looks_generated("Voice-Training_2026-09-07_14-30-15", mit)
    # Ohne das Schema fehlt der Bezug — dann lieber in Ruhe lassen.
    assert not naming.looks_generated("Voice-Training_2026-09-07_14-30-15")


# ------------------------------------------------------------------ Zaehler

def test_zaehler_laeuft_hoch_und_die_vorschau_verbraucht_ihn_nicht(store):
    zaehler = scheme(enabled={"counter": True})
    assert store.peek_counter(zaehler, STAMP) == 1
    assert store.peek_counter(zaehler, STAMP) == 1
    assert store.take_counter(zaehler, STAMP) == 1
    assert store.take_counter(zaehler, STAMP) == 2
    assert store.peek_counter(zaehler, STAMP) == 3


def test_zaehler_faengt_im_neuen_zeitraum_wieder_bei_eins_an(store):
    taeglich = scheme(enabled={"counter": True}, counter_reset="day")
    store.take_counter(taeglich, STAMP)
    store.take_counter(taeglich, STAMP)
    morgen = STAMP.replace(day=8)
    assert store.peek_counter(taeglich, morgen) == 1


def test_zaehler_ohne_ruecksetzen_laeuft_ueber_jahre_weiter(store):
    nie = scheme(enabled={"counter": True})
    store.take_counter(nie, STAMP)
    spaeter = STAMP.replace(year=2028)
    assert store.peek_counter(nie, spaeter) == 2


def test_abgeschalteter_zaehler_wird_nicht_verbraucht(store):
    import settings
    settings._state["naming"] = scheme()          # Zaehler aus
    store.next_name(STAMP, "hum")
    store.next_name(STAMP, "hum")
    assert settings.get_name_counter()["value"] == 0


def test_next_name_folgt_dem_eingestellten_schema(store):
    import settings
    settings._state["naming"] = scheme(
        subfolders="week", enabled={"type": True, "counter": True})
    assert store.next_name(STAMP, "vowel_i") == \
        "2026-KW37/2026-09-07_14-30-15_vowel-i_001.wav"
    assert store.next_name(STAMP, "vowel_i").endswith("_002.wav")


# ------------------------------------------------------------------- Umzug

def entry(name, stamp="2026-09-07T14:30:15", type_key="hum"):
    return {"file": name, "timestamp": stamp, "type": type_key}


def test_umzug_bringt_alles_ins_neue_schema(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "2026-09-07_14-30-15.wav").write_bytes(b"a")
    entries = [entry("2026-09-07_14-30-15.wav")]

    ziel = tmp_path / "extern"
    result = store.move_all(entries, [source], ziel,
                            scheme(subfolders="day", enabled={"type": True}))
    assert result["moved"] == 1
    assert entries[0]["file"] == "2026-09-07/2026-09-07_14-30-15_hum.wav"


def test_umzug_vergibt_zaehler_in_aufnahmereihenfolge(store, tmp_path):
    source = store.DEFAULT_ROOT
    for name in ("2026-09-07_14-30-15.wav", "2026-09-07_09-00-00.wav"):
        (source / name).write_bytes(b"a")
    entries = [entry("2026-09-07_14-30-15.wav", "2026-09-07T14:30:15"),
               entry("2026-09-07_09-00-00.wav", "2026-09-07T09:00:00")]

    store.move_all(entries, [source], tmp_path / "neu",
                   scheme(enabled={"counter": True}, counter_reset="day"))
    # Die fruehere Aufnahme bekommt die 1, egal wo sie in der Liste steht.
    assert entries[1]["file"].endswith("_001.wav")
    assert entries[0]["file"].endswith("_002.wav")


def test_leere_unterordner_werden_nach_einem_wechsel_weggeraeumt(store,
                                                                tmp_path):
    source = store.DEFAULT_ROOT
    monat = source / "2026-09"
    monat.mkdir()
    (monat / "2026-09-07_14-30-15.wav").write_bytes(b"a")
    entries = [entry("2026-09/2026-09-07_14-30-15.wav")]

    store.move_all(entries, [source], tmp_path / "neu",
                   scheme(subfolders="day"))
    assert not monat.exists()


# ---------------------------------------------------------- Optionen-Seite

@pytest.fixture
def options(qt_app, store):
    from dialogs import OptionsPage
    page = OptionsPage([])
    yield page
    page.deleteLater()


def test_optionen_zeigen_das_gespeicherte_schema(qt_app, store):
    import settings
    from dialogs import OptionsPage
    settings._state["naming"] = scheme(subfolders="month",
                                       enabled={"type": True})
    page = OptionsPage([])
    try:
        assert page.subfolders.currentData() == "month"
        assert page._collect()["enabled"]["type"] is True
    finally:
        page.deleteLater()


def test_vorschau_trennt_ordner_und_dateinamen(options):
    assert options.preview_folder.text().startswith(str(options.folder))
    assert ".wav" in options.preview.text()


def test_vorschau_zeigt_jeden_baustein_als_eigene_marke(options):
    """Man soll sehen, welcher Baustein welchen Teil des Namens macht."""
    import re
    for key in ("type", "counter"):
        options.parts.row_for(key).set_checked(True)
    marken = re.findall(r"background-color", options.preview.text())
    # Datum, Uhrzeit, Typ, Zaehler
    assert len(marken) == 4


def test_vorschau_zieht_sofort_nach(options):
    vorher = options.preview.text()
    index = options.subfolders.findData("day")
    options.subfolders.setCurrentIndex(index)
    assert options.preview.text() != vorher
    assert options._collect()["subfolders"] == "day"


def test_freitext_wird_in_der_zeile_eingegeben(options):
    """Kein eigener Abschnitt weiter unten — das Feld sitzt im Baustein."""
    from PySide6 import QtWidgets
    for key in naming.TEXT_BLOCKS:
        inline = options.parts.row_for(key).inline
        assert isinstance(inline, QtWidgets.QLineEdit), key

    options.parts.row_for("prefix").set_checked(True)
    options.prefix.setText("Voice Training")
    assert options._collect()["prefix"] == "Voice-Training"
    assert "Voice-Training" in options.preview.text()


def test_nebenzeile_haengt_am_baustein(options):
    """Sekunden und Zaehlerstellen erscheinen erst mit ihrem Baustein."""
    for key in ("counter", "time"):
        row = options.parts.row_for(key)
        row.set_checked(False)
        assert row.sub.isVisibleTo(row) is False, key
        row.set_checked(True)
        assert row.sub.isVisibleTo(row) is True, key


def test_bausteine_ohne_eigene_einstellung_haben_keine_nebenzeile(options):
    for key in ("date", "year", "month", "prefix"):
        row = options.parts.row_for(key)
        row.set_checked(True)
        assert row.sub.isVisibleTo(row) is False, key


def test_erklaerungen_stecken_in_tooltips(options):
    """Kein grauer Fliesstext mehr unter den Feldern."""
    from dialogs import PART_TIPS
    for key in naming.BLOCKS:
        row = options.parts.row_for(key)
        assert row.grip.toolTip(), key
        if key in PART_TIPS:
            assert row.info is not None and row.info.toolTip(), key


def test_pfeilknopf_verschiebt_einen_baustein(options):
    reihe = options._collect()["order"]
    options.parts.setCurrentRow(1)
    options._move_part(-1)
    getauscht = options._collect()["order"]
    assert getauscht[0] == reihe[1] and getauscht[1] == reihe[0]


def test_pfeilknoepfe_tragen_pfeile_und_zeigen_sie_auch(qt_app, store):
    """Nicht nur beschriftet, sondern breit genug fuer das Zeichen.

    Die Seitenpolsterung der normalen Knoepfe hatte das Dreieck einmal auf
    einen Strich zusammengekuerzt — sichtbar war die Absicht danach nicht
    mehr.
    """
    from PySide6 import QtGui, QtWidgets
    import theming
    from dialogs import OptionsPage

    qt_app.setStyleSheet(theming.stylesheet())
    page = OptionsPage([])
    page.show()
    qt_app.processEvents()
    try:
        for knopf, zeichen in ((page.btn_up, "▲"), (page.btn_down, "▼")):
            assert knopf.text() == zeichen
            assert knopf.toolTip()
            metrik = QtGui.QFontMetrics(knopf.font())
            assert metrik.inFont(zeichen)

            option = QtWidgets.QStyleOptionButton()
            knopf.initStyleOption(option)
            platz = knopf.style().subElementRect(
                QtWidgets.QStyle.SubElement.SE_PushButtonContents,
                option, knopf)
            assert platz.width() >= metrik.horizontalAdvance(zeichen), zeichen
    finally:
        qt_app.setStyleSheet("")
        page.close()
        page.deleteLater()


def test_verschieben_ueber_den_rand_passiert_nicht(options):
    reihe = options._collect()["order"]
    options.parts.setCurrentRow(0)
    options._move_part(-1)
    options.parts.setCurrentRow(len(reihe) - 1)
    options._move_part(1)
    assert options._collect()["order"] == reihe


def drag(qt_app, page, key, ziel_index):
    """Eine Zeile am Griff nehmen und auf die Hoehe einer anderen ziehen."""
    from PySide6 import QtCore, QtGui, QtWidgets

    grip = page.parts.row_for(key).grip

    def send(kind, y_in_grip):
        local = QtCore.QPointF(4, y_in_grip)
        event = QtGui.QMouseEvent(
            kind, local, grip.mapToGlobal(local),
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier)
        QtWidgets.QApplication.sendEvent(grip, event)

    send(QtCore.QEvent.Type.MouseButtonPress, 4)
    ziel = page.parts.rows()[ziel_index].geometry().top() + 2
    oben = grip.mapTo(page.parts, QtCore.QPoint(0, 0)).y()
    send(QtCore.QEvent.Type.MouseMove, ziel - oben)
    qt_app.processEvents()
    send(QtCore.QEvent.Type.MouseButtonRelease, 4)
    qt_app.processEvents()


def test_ziehen_am_griff_sortiert_um(qt_app, store):
    """Die Griffe muessen halten, was die sechs Punkte versprechen."""
    from dialogs import OptionsPage
    page = OptionsPage([])
    page.resize(700, 900)
    page.show()
    qt_app.processEvents()
    try:
        assert page.parts.order().index("counter") > 0
        drag(qt_app, page, "counter", 0)
        assert page.parts.order()[0] == "counter"
        assert page._collect()["order"][0] == "counter"
    finally:
        page.close()
        page.deleteLater()


def test_reihenfolge_landet_im_schema(options):
    options.parts.setCurrentRow(options.parts.order().index("counter"))
    options._move_part(-1)
    assert options._collect()["order"] == options.parts.order()


def test_reiter_stehen_in_der_gewuenschten_reihenfolge(qt_app, store):
    from dialogs import SettingsDialog
    import i18n

    dialog = SettingsDialog(entries=[])
    try:
        beschriftungen = [dialog.tabs.tabText(i)
                          for i in range(dialog.tabs.count())]
        assert beschriftungen == [i18n.t("tab_options"), i18n.t("tab_analysis"),
                                  i18n.t("tab_profiles"), i18n.t("tab_design"),
                                  i18n.t("tab_info")]
    finally:
        dialog.deleteLater()


def test_einstellungen_oeffnen_trotzdem_auf_info(qt_app, store):
    """Der Platz in der Leiste sagt nichts darueber, was zuerst zu sehen ist."""
    from dialogs import SettingsDialog
    import i18n

    dialog = SettingsDialog(entries=[])
    try:
        assert dialog.tabs.currentWidget() is dialog.info
        assert dialog.tabs.tabText(dialog.tabs.currentIndex()) == \
            i18n.t("tab_info")
    finally:
        dialog.deleteLater()


def test_einfuehrung_nennt_den_optionen_reiter():
    """Wer die Einfuehrung liest, soll wissen, wo die Benennung steckt."""
    import i18n

    for lang in ("en", "de"):
        i18n.set_language(lang)
        seite = i18n.t("intro_settings_body")
        assert i18n.t("tab_options") in seite, lang
        for reiter in ("tab_analysis", "tab_profiles", "tab_design",
                       "tab_info"):
            assert i18n.t(reiter) in seite, f"{lang}/{reiter}"
    i18n.set_language("en")


def test_jeder_baustein_hat_eine_beschriftung():
    import i18n
    for key in naming.BLOCKS:
        for lang in ("en", "de"):
            i18n.set_language(lang)
            assert i18n.t(f"part_{key}") != f"part_{key}", f"{key}/{lang}"
    i18n.set_language("en")


def test_jede_auswahl_hat_eine_beschriftung():
    import i18n
    for lang in ("en", "de"):
        i18n.set_language(lang)
        for key in naming.SUBFOLDERS:
            assert i18n.t(f"opt_sub_{key}") != f"opt_sub_{key}", key
        for key in naming.RESETS:
            assert i18n.t(f"opt_reset_{key}") != f"opt_reset_{key}", key
    i18n.set_language("en")


# ------------------------------------------------- Ordner aus Bausteinen

def test_ordner_aus_bausteinen():
    """Die Form, in der Wochenordner ueblicherweise von Hand entstehen."""
    scheme = naming.normalize({"folder": {
        "mode": "blocks",
        "order": ["week", "weekrange", "text"],
        "enabled": {"week": True, "weekrange": True, "text": True,
                    "year": False, "month": False, "day": False,
                    "date": False},
        "text": "Voice Training"}})
    assert naming.build_folder(scheme, STAMP) == "KW37 07.09-13.09 Voice Training"


def test_wochenspanne_ist_montag_bis_sonntag():
    assert naming.week_range(datetime(2026, 9, 9, 13, 45)) == "07.09-13.09"
    # Auch von einem Sonntag aus gesehen dieselbe Woche.
    assert naming.week_range(datetime(2026, 9, 13, 23, 0)) == "07.09-13.09"


def test_ordnerbausteine_ohne_umschaltung_wirkungslos():
    """Wer bei einem Zeitraum bleibt, merkt vom Baukasten nichts."""
    scheme = naming.normalize({"subfolders": "month", "folder": {
        "enabled": {"week": True, "text": True}, "text": "Egal"}})
    assert naming.build_folder(scheme, STAMP) == "2026-09"


def test_leerer_ordner_bleibt_leer():
    scheme = naming.normalize({"folder": {
        "mode": "blocks",
        "enabled": {key: False for key in naming.FOLDER_BLOCKS}}})
    assert naming.build_folder(scheme, STAMP) == ""


def test_ordnertext_darf_leerzeichen_haben():
    """Anders als im Dateinamen — Ordner tragen sie ohne Probleme."""
    scheme = naming.normalize({"folder": {"text": "Voice Training"}})
    assert scheme["folder"]["text"] == "Voice Training"
    # Ein Schraegstrich wuerde einen Unterordner aufmachen und fliegt raus.
    scheme = naming.normalize({"folder": {"text": "a/b"}})
    assert "/" not in scheme["folder"]["text"]


def test_tag_traegt_nur_den_tag_bei():
    nur = scheme(enabled={key: key == "day" for key in naming.BLOCKS})
    assert naming.build_stem(nur, STAMP) == "07"
    zusammen = scheme(enabled={key: key in ("year", "month", "day")
                               for key in naming.BLOCKS})
    assert naming.build_stem(zusammen, STAMP) == "2026_09_07"
