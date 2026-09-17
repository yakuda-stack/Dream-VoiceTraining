#!/usr/bin/env python3
"""
scripts/bump_version.py — Version an allen Stellen gleichzeitig setzen
=====================================================================
Ersetzt den Schritt "Dateien aendern" aus update_voice_training.txt.
Von Hand war das fehleranfaellig: vergisst man die PKGBUILD, baut das AUR
den alten Tag; vergisst man die READMEs, zeigen die Download-Links ins Leere.

    python3 scripts/bump_version.py 1.3.0                   # Version setzen
    python3 scripts/bump_version.py --check                 # nur pruefen
    python3 scripts/bump_version.py --check --expect 1.3.0

Gepflegt werden:
  1. core/paths.py             -> APP_VERSION = "1.3.0"   (Quelle der Wahrheit)
  2. packaging/PKGBUILD        -> pkgver=1.3.0 und pkgrel=1
  3. README.md, README.de.md   -> Download-Links auf v1.3.0

Was das Skript NICHT tut (bewusst):
  * keinen Git-Tag setzen und nichts pushen
  * CHANGELOG.md und HIGHLIGHTS.md nicht schreiben — der Text kommt von dir;
    das Skript erinnert nur daran, wenn der Block fehlt
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

PATHS_PY = ROOT / "core" / "paths.py"
PKGBUILD = ROOT / "packaging" / "PKGBUILD"
READMES = (ROOT / "README.md", ROOT / "README.de.md")
CHANGELOG = ROOT / "CHANGELOG.md"
HIGHLIGHTS = ROOT / "HIGHLIGHTS.md"

# Erlaubt: 1.3.0 sowie 1.3.0_alpha (Unterstrich!). Ein Bindestrich ist in
# pkgver nicht zulaessig.
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(_[A-Za-z0-9]+)?$")

# .../releases/download/v1.1.7/Dream-VoiceTraining-1.1.7...
DOWNLOAD_RE = re.compile(r"/download/v([^/]+)/Dream-VoiceTraining-([0-9][^-\"')\s]*?)(?=[-.](?:x86_64|Portable|exe))")


# --------------------------------------------------------------------------- #
#  Lesen
# --------------------------------------------------------------------------- #
def read_paths_py():
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"',
                  PATHS_PY.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def read_pkgbuild():
    text = PKGBUILD.read_text(encoding="utf-8")
    m = re.search(r"^pkgver=(.+)$", text, re.M)
    r = re.search(r"^pkgrel=(.+)$", text, re.M)
    return (m.group(1).strip() if m else None,
            r.group(1).strip() if r else None)


def read_readme(path):
    """Alle Versionen, die in den Download-Links vorkommen."""
    found = set()
    for tag, name in DOWNLOAD_RE.findall(path.read_text(encoding="utf-8")):
        found.update((tag, name))
    return sorted(found)


def top_block(path, pattern):
    """Version der obersten ##-Ueberschrift, oder None."""
    if not path.exists():
        return None
    m = re.search(pattern, path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
#  Pruefen
# --------------------------------------------------------------------------- #
def check(expect=None):
    """0 = alles stimmig, 1 = Abweichung. Gibt jede Abweichung einzeln aus."""
    v_app = read_paths_py()
    v_pkg, pkgrel = read_pkgbuild()
    readmes = {p.name: read_readme(p) for p in READMES}

    print(f"core/paths.py        APP_VERSION = {v_app}")
    print(f"packaging/PKGBUILD   pkgver      = {v_pkg}   (pkgrel={pkgrel})")
    for name, versions in readmes.items():
        print(f"{name:<20} Downloads   = {', '.join(versions) or '-'}")

    problems = []
    if not v_app:
        problems.append("core/paths.py: APP_VERSION nicht gefunden")
    if not v_pkg:
        problems.append("PKGBUILD: pkgver nicht gefunden")
    if v_pkg and v_app and v_pkg != v_app:
        problems.append(f"PKGBUILD steht auf {v_pkg}, core/paths.py auf {v_app}")
    for name, versions in readmes.items():
        if not versions:
            problems.append(f"{name}: keine Download-Links gefunden")
        elif v_app and versions != [v_app]:
            problems.append(f"{name}: Download-Links auf {', '.join(versions)}")

    if expect and v_app and v_app != expect:
        problems.append(f"Erwartet wurde {expect}, im Code steht {v_app}")

    # Bewusst nur Hinweise: der Text kommt von dir, das Skript schreibt ihn
    # nicht. Die Tests (test_versionen_stimmen_ueberein) sind da strenger.
    c_top = top_block(CHANGELOG, r"^## \[([^\]]+)\]")
    h_top = top_block(HIGHLIGHTS, r"^## (\S+)")
    if v_app and c_top != v_app:
        print(f"\nHinweis: CHANGELOG.md hat oben noch keinen Block [{v_app}] "
              f"(oben steht {c_top}).")
    if v_app and h_top != v_app:
        print(f"Hinweis: HIGHLIGHTS.md hat oben noch keinen Block {v_app} "
              f"(oben steht {h_top}).")

    if problems:
        print("\nFEHLER:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nAlle Versionsangaben stimmen ueberein.")
    return 0


# --------------------------------------------------------------------------- #
#  Setzen
# --------------------------------------------------------------------------- #
def _sub(path, pattern, replacement, description, count=1):
    """count=1: genau einmal ersetzen. count=0: alle, mindestens einmal."""
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(pattern, replacement, text, count=count, flags=re.M)
    if n == 0:
        print(f"  !! {description}: Muster nicht gefunden — Datei unveraendert")
        return False
    path.write_text(new_text, encoding="utf-8")
    print(f"  ok {description}" + (f" ({n}x)" if count == 0 else ""))
    return True


def bump(new_version):
    if not VERSION_RE.match(new_version):
        print(f"Ungueltige Version: {new_version}")
        print("Erwartet: 1.2.3 oder 1.2.3_alpha (Unterstrich, kein Bindestrich!)")
        return 1

    old = read_paths_py()
    print(f"Version {old} -> {new_version}\n")

    ok = True
    ok &= _sub(PATHS_PY, r'^APP_VERSION\s*=\s*"[^"]+"',
               f'APP_VERSION = "{new_version}"', "core/paths.py")
    ok &= _sub(PKGBUILD, r"^pkgver=.+$", f"pkgver={new_version}",
               "PKGBUILD pkgver")
    # pkgrel IMMER auf 1: neue Upstream-Version = neuer Build.
    ok &= _sub(PKGBUILD, r"^pkgrel=.+$", "pkgrel=1", "PKGBUILD pkgrel")
    for readme in READMES:
        ok &= _sub(readme, DOWNLOAD_RE.pattern,
                   f"/download/v{new_version}/Dream-VoiceTraining-{new_version}",
                   f"{readme.name} Download-Links", count=0)

    if not ok:
        return 1

    print(f"""
Naechste Schritte (siehe update_voice_training.txt):

  1. CHANGELOG.md:  "## [{new_version}] — <Datum>" GANZ OBEN
     HIGHLIGHTS.md: "## {new_version} — <Datum>"   GANZ OBEN (2-3 Punkte)
  2. python -m pytest tests/ -q
  3. git commit, push, Tag v{new_version}
  4. Release bauen, AUR aktualisieren
""")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Version an allen Stellen setzen/pruefen")
    ap.add_argument("version", nargs="?", help="neue Version, z. B. 1.3.0")
    ap.add_argument("--check", action="store_true",
                    help="nur pruefen, nichts aendern")
    ap.add_argument("--expect", help="zusaetzlich gegen diese Version pruefen (Tag-Name)")
    args = ap.parse_args()

    if args.check or not args.version:
        return check(expect=args.expect)
    return bump(args.version)


if __name__ == "__main__":
    sys.exit(main())
