"""Selbstinstallation der Windows-EXE beim ersten Start.

Wer die EXE aus dem Browser laedt, startet sie aus dem Download-Ordner und
hat danach kein Symbol, keinen Startmenue-Eintrag und beim Aufraeumen des
Ordners kein Programm mehr. Das Setup loest das, aber nicht jeder laedt das
Setup.

Deshalb fragt das Programm beim ersten Start einmal nach — nur einmal, die
Antwort steht danach in der Konfiguration — und legt sich bei Ja nach
%LOCALAPPDATA%\\Programs, wo Windows Programme ohne Administratorrechte
erwartet. Verknuepfung auf dem Schreibtisch, Eintrag im Startmenue, damit die
Suche das Programm findet, und ein Eintrag unter "Apps und Features".

Was hier absichtlich nicht passiert:

* Die portable Variante wird nicht angefasst. "Portabel" heisst, dass die
  Datei liegen bleibt, wo sie liegt, und ihre Daten daneben schreibt.
* Die laufende EXE wird nicht geloescht. Windows laesst das nicht zu, solange
  sie laeuft. Stattdessen wird kopiert, aus dem neuen Ort neu gestartet und
  die alte Datei vom neuen Prozess entfernt, dem sie nicht mehr im Weg steht.

Kein Qt in diesem Modul, damit sich die Entscheidungen ohne Oberflaeche und
auch unter Linux pruefen lassen.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import paths
import settings

UNINSTALL_KEY = (r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
                 "\\" + paths.APP_NAME)
APP_PATHS_KEY = (r"Software\Microsoft\Windows\CurrentVersion\App Paths"
                 "\\" + paths.APP_NAME + ".exe")
HANDOVER_FLAG = "--installed-from"
BLURB = "Voice training: pitch, resonance, weight and voice quality"

# Ohne Konsolenfenster und ohne dass ein Fenster nach vorne springt.
_NO_WINDOW = 0x08000000


# --------------------------------------------------------------- Orte

def target_dir() -> Path:
    """Wohin sich das Programm legt.

    Derselbe Ort, den das Setup und install_windows.ps1 benutzen — sonst
    haette man am Ende zwei Installationen nebeneinander.
    """
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / "AppData" / "Local"
    return root / "Programs" / paths.APP_NAME


def target_exe() -> Path:
    return target_dir() / f"{paths.APP_NAME}.exe"


def desktop_link() -> Path:
    # USERPROFILE\Desktop trifft es nicht, wenn der Schreibtisch verschoben
    # oder per OneDrive umgeleitet ist; der Shell-Ordner ist die Wahrheit.
    return _shell_folder("Desktop") / f"{paths.APP_NAME}.lnk"


def menu_link() -> Path:
    return (_shell_folder("Programs") / f"{paths.APP_NAME}.lnk")


def _shell_folder(name: str) -> Path:
    """Schreibtisch- oder Startmenue-Ordner des Benutzers."""
    if name == "Programs":
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
        return root / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    home = Path(os.environ.get("USERPROFILE") or Path.home())
    one_drive = os.environ.get("OneDrive")
    if one_drive and (Path(one_drive) / name).is_dir():
        return Path(one_drive) / name
    return home / name


def in_program_files(executable: Path | None = None) -> bool:
    """Ob die EXE unter Program Files liegt, also vom Setup kommt."""
    executable = Path(executable or sys.executable).resolve()
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        base = os.environ.get(variable)
        if not base:
            continue
        try:
            executable.relative_to(Path(base).resolve())
            return True
        except (ValueError, OSError):
            continue
    return False


# ------------------------------------------------------ Anbieten oder nicht

def should_offer(executable: Path | None = None) -> bool:
    """Ob die Frage beim Start ueberhaupt Sinn hat.

    Nur eine eingepackte EXE unter Windows, die nicht portabel laeuft, noch
    nicht am Zielort liegt und noch nicht gefragt wurde.
    """
    if not paths.WINDOWS or not paths.FROZEN:
        return False
    if settings.get_install_asked():
        return False

    executable = Path(executable or sys.executable).resolve()
    if paths.looks_portable(executable):
        return False
    if in_program_files(executable):
        # Ueber setup.exe nach Program Files installiert: Verknuepfungen und
        # Eintrag hat der Installer schon gemacht.
        return False
    try:
        if executable.parent.resolve() == target_dir().resolve():
            return False
    except OSError:
        # Zielordner nicht erreichbar — dann lieber nicht anbieten.
        return False
    return True


# ---------------------------------------------------------------- Einrichten

def install(executable: Path | None = None) -> Path:
    """Kopieren, verknuepfen, eintragen. Gibt den neuen Ort zurueck.

    Wirft OSError, wenn schon das Kopieren scheitert — dann ist nichts
    passiert und der Aufrufer kann es sagen. Verknuepfungen und
    Registrierung sind Beigaben: schlagen sie fehl, laeuft das Programm am
    neuen Ort trotzdem.
    """
    source = Path(executable or sys.executable).resolve()
    destination = target_exe()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source != destination:
        shutil.copy2(source, destination)

    for link in (desktop_link(), menu_link()):
        try:
            make_shortcut(link, destination)
        except OSError:
            pass
    try:
        register(destination)
    except OSError:
        pass
    return destination


def shortcut_script(link: Path, target: Path) -> str:
    """PowerShell-Zeile, die eine .lnk schreibt.

    Ueber WScript.Shell, weil eine Verknuepfung sonst COM von Hand
    braeuchte und pywin32 keine Abhaengigkeit dieses Programms ist.
    """
    return (
        "$s = (New-Object -ComObject WScript.Shell)"
        f".CreateShortcut('{_ps_quote(link)}'); "
        f"$s.TargetPath = '{_ps_quote(target)}'; "
        f"$s.WorkingDirectory = '{_ps_quote(target.parent)}'; "
        f"$s.Description = '{_ps_quote(BLURB)}'; "
        "$s.Save()")


def make_shortcut(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-Command",
         shortcut_script(link, target)],
        check=True, creationflags=_NO_WINDOW, timeout=60,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def uninstall_command(directory: Path | None = None) -> str:
    """Was unter "Apps und Features" als Deinstallation hinterlegt wird.

    Aufnahmen und Einstellungen bleiben liegen: sie stecken unter
    %APPDATA% und %LOCALAPPDATA% und gehoeren dem Benutzer, nicht dem
    Installationsordner.
    """
    directory = directory or target_dir()
    removals = "','".join(_ps_quote(item)
                          for item in (desktop_link(), menu_link()))
    return (
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \""
        f"Remove-Item -Force '{removals}' -ErrorAction SilentlyContinue; "
        "Remove-Item -Recurse -Force "
        f"'HKCU:\\{UNINSTALL_KEY}' -ErrorAction SilentlyContinue; "
        "Remove-Item -Recurse -Force "
        f"'HKCU:\\{APP_PATHS_KEY}' -ErrorAction SilentlyContinue; "
        f"Remove-Item -Recurse -Force '{_ps_quote(directory)}' "
        "-ErrorAction SilentlyContinue\"")


def register(destination: Path) -> None:
    """App Paths und den Eintrag unter "Apps und Features" schreiben."""
    import winreg                      # nur unter Windows vorhanden

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, APP_PATHS_KEY) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(destination))
        winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ,
                          str(destination.parent))

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
        for name, value in (
                ("DisplayName", paths.APP_NAME),
                ("DisplayVersion", paths.APP_VERSION),
                ("Publisher", "Yakuda"),
                ("URLInfoAbout", paths.APP_URL),
                ("DisplayIcon", str(destination)),
                ("InstallLocation", str(destination.parent)),
                ("UninstallString", uninstall_command(destination.parent))):
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        for name in ("NoModify", "NoRepair"):
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)


# ------------------------------------------------------------- Uebergabe

def relaunch(destination: Path, leftover: Path) -> None:
    """Die neue EXE starten und ihr die alte Datei zum Loeschen nennen."""
    subprocess.Popen([str(destination), HANDOVER_FLAG, str(leftover)],
                     cwd=str(destination.parent),
                     creationflags=_NO_WINDOW | 0x00000008)  # DETACHED


def handover_path(argv: list[str] | None = None) -> Path | None:
    argv = list(argv if argv is not None else sys.argv)
    if HANDOVER_FLAG not in argv:
        return None
    index = argv.index(HANDOVER_FLAG)
    if index + 1 >= len(argv):
        return None
    return Path(argv[index + 1])


def delete_leftover(path: Path | None, attempts: int = 4,
                    pause: float = 0.15) -> bool:
    """Die zurueckgelassene EXE entfernen, falls sie schon frei ist.

    Ein paar kurze Versuche, weil der alte Prozess vielleicht noch beim
    Beenden ist. Klappt es nicht, bleibt die Datei liegen — das ist ein
    Schoenheitsfehler und kein Grund, den Start aufzuhalten.
    """
    if path is None:
        return False
    for attempt in range(attempts):
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return True
        except OSError:
            if attempt + 1 < attempts:
                time.sleep(pause)
    return False


def _ps_quote(value) -> str:
    """Fuer einfache Anfuehrungszeichen in PowerShell verdoppelt man sie."""
    return str(value).replace("'", "''")
