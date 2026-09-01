# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller-Beschreibung fuer Dream-VoiceTraining.
# Aufruf ueber packaging/windows/build_windows.ps1, nicht direkt.

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

ROOT = Path(SPECPATH).resolve().parents[1]
PACKAGING = ROOT / "packaging"

sys.path.insert(0, str(ROOT))
import paths as app_paths          # noqa: E402  — nur fuer die Versionsnummer

# sounddevice bringt die PortAudio-DLL im Paket mit; ohne diese beiden
# Zeilen fehlt sie im Build und das Programm findet kein Mikrofon.
binaries = collect_dynamic_libs("sounddevice")
datas = collect_data_files("sounddevice")

# parselmouth ist eine kompilierte Erweiterung, PyInstaller findet sie
# ueber den Import — der Eintrag hier ist die Absicherung.
hiddenimports = ["parselmouth", "sounddevice", "_sounddevice"]

datas += [
    (str(PACKAGING / "dream-voicetraining.ico"), "."),
    (str(PACKAGING / "dream-voicetraining.svg"), "."),
    (str(ROOT / "LICENSE"), "."),
    (str(ROOT / "THIRD_PARTY_NOTICES.md"), "."),
]

analysis = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Qt bringt sonst Web-Engine, 3D und Multimedia mit, die hier niemand
    # braucht und die den Build um hunderte Megabyte aufblaehen.
    excludes=[
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtMultimedia",
        "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtBluetooth",
        "PySide6.QtNetworkAuth", "PySide6.QtPositioning", "PySide6.QtSql",
        "PySide6.QtTest", "PySide6.QtDesigner", "PyQt5", "PyQt6",
        "tkinter", "matplotlib", "IPython", "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Dream-VoiceTraining",
    icon=str(PACKAGING / "dream-voicetraining.ico"),
    debug=False,
    strip=False,
    upx=False,
    # Ohne Konsole; Fehler landen im Debugfenster des Programms.
    console=False,
    version_info=None,
)

COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Dream-VoiceTraining",
)
