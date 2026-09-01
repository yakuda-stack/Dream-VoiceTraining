"""Ablageorte und Uebernahme aus frueheren Versionen."""

import importlib


def test_folgt_der_xdg_spezifikation(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.delenv("DREAM_VOICETRAINING_HOME", raising=False)
    import paths
    importlib.reload(paths)

    assert paths.CONFIG_PATH == tmp_path / "c" / "dream-voicetraining" / "config.json"
    assert paths.SESSION_DIR == tmp_path / "d" / "dream-voicetraining" / "sessions"


def test_umgebungsvariable_legt_alles_zusammen(tmp_path, monkeypatch):
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "portable"))
    import paths
    importlib.reload(paths)
    assert paths.CONFIG_DIR == paths.DATA_DIR == tmp_path / "portable"


def test_uebernimmt_aus_programmordner_und_alter_app_id(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.delenv("DREAM_VOICETRAINING_HOME", raising=False)
    import paths
    importlib.reload(paths)

    program = tmp_path / "prog"
    (program / "sessions").mkdir(parents=True)
    (program / "config.json").write_text('{"values": {"pitch_floor": 70}}')
    (program / "sessions" / "alt.wav").write_bytes(b"x")

    legacy = tmp_path / "d" / "voicetfy" / "sessions"
    legacy.mkdir(parents=True)
    (legacy / "aelter.wav").write_bytes(b"y")

    moved = paths.migrate_from(program)
    assert sorted(moved) == ["aelter.wav", "alt.wav", "config.json"]
    assert paths.CONFIG_PATH.exists()
    assert {p.name for p in paths.SESSION_DIR.iterdir()} == {"alt.wav", "aelter.wav"}
    assert not (program / "sessions").exists()


def test_vorhandene_dateien_werden_nicht_ueberschrieben(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
    monkeypatch.delenv("DREAM_VOICETRAINING_HOME", raising=False)
    import paths
    importlib.reload(paths)
    paths.ensure_dirs()
    paths.CONFIG_PATH.write_text("neu", encoding="utf-8")

    program = tmp_path / "prog2"
    program.mkdir()
    (program / "config.json").write_text("alt", encoding="utf-8")

    paths.migrate_from(program)
    assert paths.CONFIG_PATH.read_text(encoding="utf-8") == "neu"
    assert (program / "config.json").exists()


def test_windows_ablageorte(tmp_path, monkeypatch):
    """Konfiguration ins servergespeicherte Profil, Aufnahmen lokal."""
    import importlib
    import paths
    importlib.reload(paths)

    monkeypatch.delenv("DREAM_VOICETRAINING_HOME", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setattr(paths, "WINDOWS", True)

    config, data = paths._roots()
    assert config == tmp_path / "Roaming" / paths.APP_NAME
    assert data == tmp_path / "Local" / paths.APP_NAME
    # Aufnahmen dürfen nicht im Roaming-Zweig landen.
    assert "Roaming" not in str(data)

    importlib.reload(paths)


def test_umgebungsvariable_schlaegt_windows(tmp_path, monkeypatch):
    import importlib
    import paths
    importlib.reload(paths)

    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "portable"))
    config, data = paths._roots()
    assert config == data == tmp_path / "portable"

    importlib.reload(paths)


def test_prozessname_bricht_unter_windows_nicht(monkeypatch):
    import paths
    monkeypatch.setattr(paths, "WINDOWS", True)
    paths.set_process_name()          # darf einfach nichts tun
