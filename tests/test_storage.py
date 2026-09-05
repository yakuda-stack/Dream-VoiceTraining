"""Aufnahmeordner, Monatsunterordner, Typ im Dateinamen und der Umzug."""

from datetime import datetime

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    """storage mit einem eigenen Standardordner und Standardeinstellungen.

    paths wird bewusst nicht neu geladen: settings haelt CONFIG_PATH als
    eigenen Modulwert, und ein Neuladen von paths brachte beide fuer alle
    folgenden Tests auseinander.
    """
    import settings
    import storage

    default = tmp_path / "sessions"
    default.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(storage, "DEFAULT_ROOT", default)

    settings._state["session_dir"] = None
    settings._state["month_folders"] = False
    settings._state["type_in_name"] = False
    monkeypatch.setattr(settings, "save", lambda: None)
    return storage


def entry(name, stamp="2026-03-14T09-00-00", type_key="hum"):
    return {"file": name, "timestamp": stamp.replace("_", "T"),
            "type": type_key}


def test_ohne_optionen_bleibt_der_name_wie_bisher(store):
    stamp = datetime(2026, 3, 14, 9, 5, 0)
    assert store.relative_name(stamp, "hum") == "2026-03-14_09-05-00.wav"


def test_monatsordner_und_typ_im_namen(store):
    stamp = datetime(2026, 3, 14, 9, 5, 0)
    name = store.relative_name(stamp, "vowel_a", month=True, typed=True)
    assert name == "2026-03/2026-03-14_09-05-00_vowel-a.wav"


def test_typkuerzel_haengt_nicht_an_der_sprache(store):
    import i18n
    import rectypes
    i18n.set_language("de")
    assert rectypes.slug("vowel_i") == "vowel-i"
    i18n.set_language("en")
    assert rectypes.slug("vowel_i") == "vowel-i"


def test_eigener_ordner_wird_benutzt(store, tmp_path):
    import settings
    target = tmp_path / "Aufnahmen"
    settings._state["session_dir"] = str(target)
    assert store.root() == target
    assert store.writable(target) == ""


def test_alte_dateien_bleiben_auffindbar(store):
    import settings
    old = store.DEFAULT_ROOT / "2026-03-14_09-00-00.wav"
    old.write_bytes(b"x")
    settings._state["session_dir"] = str(store.DEFAULT_ROOT.parent / "neu")
    assert store.path_for("2026-03-14_09-00-00.wav") == old


def test_umzug_legt_monatsordner_an_und_ergaenzt_den_typ(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "2026-03-14_09-00-00.wav").write_bytes(b"a")
    (source / "2026-04-02_18-30-00.wav").write_bytes(b"b")
    entries = [entry("2026-03-14_09-00-00.wav", "2026-03-14T09:00:00", "hum"),
               entry("2026-04-02_18-30-00.wav", "2026-04-02T18:30:00",
                     "vowel_u")]

    target = tmp_path / "extern"
    result = store.move_all(entries, [source], target, month=True, typed=True)

    assert result["moved"] == 2
    assert entries[0]["file"] == "2026-03/2026-03-14_09-00-00_hum.wav"
    assert (target / entries[1]["file"]).is_file()
    assert not (source / "2026-03-14_09-00-00.wav").exists()


def test_umzug_laesst_selbst_vergebene_namen_in_ruhe(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "Morgenstimme.wav").write_bytes(b"a")
    entries = [entry("Morgenstimme.wav", "2026-03-14T09:00:00", "reading")]

    store.move_all(entries, [source], tmp_path / "neu", month=True, typed=True)
    assert entries[0]["file"] == "2026-03/Morgenstimme.wav"


def test_typ_im_namen_laesst_sich_wieder_abschalten(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "2026-03-14_09-00-00_hum.wav").write_bytes(b"a")
    entries = [entry("2026-03-14_09-00-00_hum.wav", "2026-03-14T09:00:00",
                     "hum")]

    store.move_all(entries, [source], tmp_path / "neu", month=False,
                   typed=False)
    assert entries[0]["file"] == "2026-03-14_09-00-00.wav"


def test_umzug_ueberschreibt_keine_fremde_datei(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "gleich.wav").write_bytes(b"neu")
    target = tmp_path / "ziel"
    target.mkdir()
    (target / "gleich.wav").write_bytes(b"alt")

    entries = [entry("gleich.wav", "2026-03-14T09:00:00", "free")]
    store.move_all(entries, [source], target, month=False, typed=False)

    assert (target / "gleich.wav").read_bytes() == b"alt"
    assert entries[0]["file"] == "gleich-2.wav"


def test_fehlende_datei_bricht_den_umzug_nicht_ab(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "da.wav").write_bytes(b"a")
    entries = [entry("weg.wav", "2026-03-14T09:00:00"),
               entry("da.wav", "2026-03-15T09:00:00")]

    result = store.move_all(entries, [source], tmp_path / "neu", month=False,
                            typed=False)
    assert (result["moved"], result["missing"]) == (1, 1)
    assert entries[0]["file"] == "weg.wav"


def test_eintrag_ohne_zeitstempel_landet_in_unsortiert(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "namenlos.wav").write_bytes(b"a")
    entries = [{"file": "namenlos.wav", "type": "free"}]

    store.move_all(entries, [source], tmp_path / "neu", month=True,
                   typed=False)
    assert entries[0]["file"] == "unsorted/namenlos.wav"


def test_zaehlt_was_noch_woanders_liegt(store, tmp_path):
    source = store.DEFAULT_ROOT
    (source / "a.wav").write_bytes(b"a")
    entries = [entry("a.wav", "2026-03-14T09:00:00")]

    target = tmp_path / "neu"
    assert store.elsewhere(entries, target, month=True, typed=False) == 1
    store.move_all(entries, [source], target, month=True, typed=False)
    assert store.elsewhere(entries, target, month=True, typed=False) == 0
