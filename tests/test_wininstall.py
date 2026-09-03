"""Die Selbstinstallation unter Windows.

Ausgefuehrt wird sie hier nicht — Registry und Verknuepfungen gibt es unter
Linux nicht. Geprueft werden die Entscheidungen und die Zeichenketten, die
an PowerShell gehen, denn dort steckt der Aerger: ein falsches
Anfuehrungszeichen und der Befehl macht etwas anderes.
"""

import paths
import settings
import wininstall


def test_ohne_windows_wird_nicht_gefragt(monkeypatch):
    monkeypatch.setattr(paths, "WINDOWS", False)
    monkeypatch.setattr(paths, "FROZEN", True)
    assert wininstall.should_offer("/tmp/Dream-VoiceTraining.exe") is False


def test_aus_dem_quellcode_gestartet_wird_nicht_gefragt(monkeypatch):
    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setattr(paths, "FROZEN", False)
    assert wininstall.should_offer("/tmp/Dream-VoiceTraining.exe") is False


def test_portable_bleibt_liegen(monkeypatch, tmp_path):
    """Portabel heisst: die Datei zieht nicht um, sonst waere sie es nicht."""
    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setattr(paths, "FROZEN", True)
    monkeypatch.setattr(settings, "get_install_asked", lambda: False)

    exe = tmp_path / "Dream-VoiceTraining-1.0.9-Portable.exe"
    exe.write_bytes(b"")
    assert paths.looks_portable(exe) is True
    assert wininstall.should_offer(exe) is False

    # Auch der Merker daneben zaehlt, egal wie die Datei heisst.
    plain = tmp_path / "Dream-VoiceTraining.exe"
    plain.write_bytes(b"")
    (tmp_path / paths.PORTABLE_MARKER).write_text("", encoding="utf-8")
    assert wininstall.should_offer(plain) is False


def test_aus_program_files_wird_nicht_gefragt(monkeypatch, tmp_path):
    """Da hat das Setup schon alles angelegt."""
    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setattr(paths, "FROZEN", True)
    monkeypatch.setattr(settings, "get_install_asked", lambda: False)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))

    exe = tmp_path / "Dream-VoiceTraining" / "Dream-VoiceTraining.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    assert wininstall.in_program_files(exe) is True
    assert wininstall.should_offer(exe) is False


def test_bereits_gefragt_wird_nicht_wieder_gefragt(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setattr(paths, "FROZEN", True)
    monkeypatch.setattr(settings, "get_install_asked", lambda: True)
    exe = tmp_path / "Dream-VoiceTraining.exe"
    exe.write_bytes(b"")
    assert wininstall.should_offer(exe) is False


def test_aus_dem_downloadordner_wird_gefragt(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "WINDOWS", True)
    monkeypatch.setattr(paths, "FROZEN", True)
    monkeypatch.setattr(settings, "get_install_asked", lambda: False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)
    monkeypatch.delenv("ProgramW6432", raising=False)

    exe = tmp_path / "Downloads" / "Dream-VoiceTraining.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    assert wininstall.should_offer(exe) is True


def test_anfuehrungszeichen_im_pfad_zerlegen_den_befehl_nicht(monkeypatch, tmp_path):
    """Ein Benutzername wie O'Brien darf den PowerShell-Aufruf nicht kippen."""
    link = tmp_path / "O'Brien" / "Dream-VoiceTraining.lnk"
    target = tmp_path / "O'Brien" / "Dream-VoiceTraining.exe"
    script = wininstall.shortcut_script(link, target)
    # Verdoppelt, nicht durchgereicht: sonst endet die Zeichenkette hier.
    assert "O''Brien" in script
    assert "O'Brien'" not in script.replace("O''Brien", "")
    assert script.count("CreateShortcut") == 1


def test_deinstallation_raeumt_verknuepfungen_und_schluessel(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    command = wininstall.uninstall_command(tmp_path / "Programs" / "App")
    for part in ("Dream-VoiceTraining.lnk", "Uninstall\\Dream-VoiceTraining",
                 "App Paths\\Dream-VoiceTraining.exe", "Remove-Item"):
        assert part in command, part
    # Aufnahmen und Einstellungen tauchen darin nicht auf.
    assert "sessions" not in command


def test_uebergabe_loescht_die_alte_datei(tmp_path):
    old = tmp_path / "Dream-VoiceTraining.exe"
    old.write_bytes(b"x")
    assert wininstall.handover_path(
        ["app.exe", wininstall.HANDOVER_FLAG, str(old)]) == old
    assert wininstall.handover_path(["app.exe"]) is None
    # Ein Aufruf ohne Pfad hinter dem Schalter darf nicht stolpern.
    assert wininstall.handover_path(["app.exe", wininstall.HANDOVER_FLAG]) is None

    assert wininstall.delete_leftover(old, attempts=1) is True
    assert not old.exists()
    # Schon weg ist auch in Ordnung.
    assert wininstall.delete_leftover(old, attempts=1) is True
    assert wininstall.delete_leftover(None) is False
