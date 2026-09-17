"""Ordneraufbau und Versionsskript."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("core", "voice", "ui")


def test_im_hauptordner_liegt_nur_main_py():
    assert sorted(p.name for p in ROOT.glob("*.py")) == ["main.py"]


def test_jedes_paket_ist_ein_paket():
    for name in PACKAGES:
        assert (ROOT / name / "__init__.py").is_file(), name
        assert list((ROOT / name).glob("*.py")) != [], name


def test_alle_pakete_werden_mitgeliefert():
    """Ein Ordner, den ein Installer vergisst, ist ein Absturz beim Start."""
    for datei in ("packaging/PKGBUILD", "packaging/build-appimage.sh",
                  "install.sh", "packaging/windows/install_windows.ps1"):
        text = (ROOT / datei).read_text(encoding="utf-8-sig")
        for name in PACKAGES:
            assert name in text, f"{datei}: {name}"


def test_versionsnummer_wird_aus_core_gelesen():
    for datei in ("packaging/build-appimage.sh",
                  "packaging/windows/build_windows.ps1",
                  "packaging/windows/install_windows.ps1"):
        text = (ROOT / datei).read_text(encoding="utf-8-sig")
        assert "core" in text and "paths.py" in text, datei


def _bump(root, *args):
    return subprocess.run([sys.executable, str(root / "scripts/bump_version.py"),
                           *args], capture_output=True, text=True)


def test_bump_check_ist_im_projekt_gruen():
    from core import paths
    result = _bump(ROOT, "--check", "--expect", paths.APP_VERSION)
    assert result.returncode == 0, result.stdout


def test_bump_setzt_alle_stellen(tmp_path):
    kopie = tmp_path / "p"
    for teil in ("scripts", "core", "packaging"):
        shutil.copytree(ROOT / teil, kopie / teil,
                        ignore=shutil.ignore_patterns("__pycache__", "icons",
                                                      "windows"))
    for datei in ("README.md", "README.de.md", "CHANGELOG.md", "HIGHLIGHTS.md"):
        shutil.copy2(ROOT / datei, kopie / datei)

    result = _bump(kopie, "9.8.7")
    assert result.returncode == 0, result.stdout
    assert 'APP_VERSION = "9.8.7"' in (kopie / "core/paths.py").read_text()
    pkgbuild = (kopie / "packaging/PKGBUILD").read_text()
    assert "pkgver=9.8.7\n" in pkgbuild and "pkgrel=1\n" in pkgbuild
    for readme in ("README.md", "README.de.md"):
        text = (kopie / readme).read_text(encoding="utf-8")
        assert text.count("/download/v9.8.7/Dream-VoiceTraining-9.8.7") == 3

    check = _bump(kopie, "--check", "--expect", "9.8.7")
    assert check.returncode == 0, check.stdout
    assert "CHANGELOG.md hat oben noch keinen Block" in check.stdout


def test_bump_lehnt_bindestrich_ab(tmp_path):
    result = _bump(ROOT, "1.3-0")
    assert result.returncode == 1
    assert "Unterstrich" in result.stdout
