#!/bin/bash
# Dream-VoiceTraining — AppImage Builder (bundled Python)
# Benötigt: wget, tar, und bsdtar ODER ar (binutils) zum Auspacken der .deb
# appimagetool, Runtime, Python und die System-Bibliotheken werden
# automatisch geladen (Cache in /tmp).
#
# Die AppImage bringt ALLES selbst mit — auch Python. Grund: der Test im
# AppImage-Katalog (appimage.github.io) läuft auf Ubuntu 22.04 mit
# python3 3.10. Mit dem System-Python passten die hier gebauten Pakete
# (cpython-314) dort nicht und die App brach sofort ab.
# Verwendung:  bash packaging/build-appimage.sh   (egal von wo aus)
#
# Ergebnis:    build/Dream-VoiceTraining-<version>-x86_64.AppImage
#              build/ wird bei JEDEM Lauf komplett geleert — dort liegt
#              danach nur die frische AppImage, nie ein alter Stand.

set -e

# immer vom Projekt-Root aus arbeiten: erst ins Skript-Verzeichnis,
# dann hochgehen bis core/paths.py gefunden ist
cd "$(dirname "$0")"
for _ in 1 2 3; do
    [ -f core/paths.py ] && break
    cd ..
done
if [ ! -f core/paths.py ]; then
    echo "FEHLER: Projekt-Root nicht gefunden (core/paths.py fehlt)."
    echo "        Bitte das Skript in den Dream-VoiceTraining-Ordner legen."
    exit 1
fi

APP="Dream-VoiceTraining"
# Version automatisch aus core/paths.py lesen (APP_VERSION = "1.1.7" -> 1.1.7).
VERSION="$(grep -oP '^APP_VERSION\s*=\s*"v?\K[^"]+' core/paths.py)"
if [ -z "$VERSION" ]; then
    echo "FEHLER: APP_VERSION in core/paths.py nicht gefunden."
    exit 1
fi
ARCH="x86_64"
OUT_DIR="$(pwd)/build"                              # Ziel fuer die fertige AppImage
BUILD_DIR="$OUT_DIR/AppDir"                         # Zwischenstand, wird am Ende geloescht
OUT="$OUT_DIR/${APP}-${VERSION}-${ARCH}.AppImage"
LIB="$BUILD_DIR/usr/lib/dream-voicetraining"

echo "=== Dream-VoiceTraining AppImage Builder ==="
echo "Version: $VERSION"
echo ""

# Sanity-Check: Projektstruktur vorhanden?
for f in main.py core/paths.py ui/dialogs.py voice/analysis.py packaging/dream-voicetraining.svg \
         CHANGELOG.md HIGHLIGHTS.md; do
    if [ ! -e "$f" ]; then
        echo "FEHLER: $f nicht gefunden — bitte aus dem Projekt-Root bauen."
        exit 1
    fi
done

# 0. build/ frisch anlegen
echo "[0/5] Leere build/ ..."
rm -rf "$OUT_DIR"
rm -rf "$(pwd)/AppDir"          # Überbleibsel vom alten Build-Ort im Projekt-Root
mkdir -p "$OUT_DIR"

# 1. appimagetool besorgen
#
# Immer das aktuelle aus github.com/AppImage/appimagetool — NICHT das alte
# aus AppImageKit (wird nicht mehr gepflegt) und nicht ein zufällig
# installiertes: das aktuelle bringt zsyncmake selbst mit, erzeugt also
# die .zsync-Datei für Delta-Updates (siehe Schritt 6) ohne dass zsync auf
# dem System installiert sein muss. Wird einmal nach /tmp geladen.
# Eigenes Tool erzwingen: APPIMAGETOOL=/pfad/zum/appimagetool bash ...
if [ -z "${APPIMAGETOOL:-}" ]; then
    APPIMAGETOOL="/tmp/appimagetool-new-${ARCH}"
    if [ ! -s "$APPIMAGETOOL" ]; then
        echo "[Info] Lade appimagetool (github.com/AppImage/appimagetool)..."
        wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
            -O "$APPIMAGETOOL" || {
            echo "FEHLER: appimagetool konnte nicht geladen werden."
            rm -f "$APPIMAGETOOL"
            exit 1
        }
    fi
    if ! head -c 4 "$APPIMAGETOOL" | grep -q "ELF"; then
        echo "FEHLER: $APPIMAGETOOL ist keine ELF-Datei — Download kaputt."
        rm -f "$APPIMAGETOOL"
        exit 1
    fi
    chmod +x "$APPIMAGETOOL"
fi

# FUSE-Workaround: appimagetool selbst ohne FUSE ausführen
export APPIMAGE_EXTRACT_AND_RUN=1

# 1b. Runtime besorgen — WICHTIG für FUSE 2 *und* FUSE 3
#
# Die Runtime ist der ausführbare Kopf jeder AppImage. Die alte aus
# AppImageKit lädt libfuse.so.2 per dlopen(). Ubuntu >= 22.04 und damit
# Linux Mint >= 21 liefern nur noch fuse3 aus — dort scheitert der Start
# mit "dlopen(): error loading libfuse.so.2", bevor auch nur eine Zeile
# Python läuft.
#
# type2-runtime ist statisch gegen musl+libfuse gelinkt und sucht sich
# zur Laufzeit ein passendes fusermount* im $PATH. Damit laufen dieselbe
# Datei auf fuse2- und fuse3-Systemen, ohne dass jemand libfuse2
# nachinstallieren muss.
RUNTIME_URL="https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${ARCH}"
RUNTIME="/tmp/appimage-runtime-${ARCH}"
if [ ! -s "$RUNTIME" ]; then
    echo "[Info] Lade statische AppImage-Runtime (fuse2+fuse3)..."
    wget -q "$RUNTIME_URL" -O "$RUNTIME" || {
        echo "FEHLER: Runtime konnte nicht geladen werden ($RUNTIME_URL)."
        exit 1
    }
fi
# Sanity-Check: bei einem 404 landet sonst eine HTML-Seite in der
# AppImage und das Ergebnis startet auf *keinem* System.
if ! head -c 4 "$RUNTIME" | grep -q "ELF"; then
    echo "FEHLER: $RUNTIME ist keine ELF-Datei — Download kaputt."
    rm -f "$RUNTIME"
    exit 1
fi
chmod +x "$RUNTIME"

# 1c. Eigenes Python besorgen (python-build-standalone von astral-sh)
#
# Relocatable CPython, läuft ab glibc 2.17. Die Pakete aus requirements.txt
# werden später mit GENAU diesem Python installiert — die Wheels passen
# also immer, egal welches python3 (oder keins) auf dem Zielsystem ist.
# Neue Version: beide Werte von
#   https://github.com/astral-sh/python-build-standalone/releases
PY_VERSION="3.14.7"
PY_RELEASE="20260924"
PY_TARBALL="cpython-${PY_VERSION}+${PY_RELEASE}-${ARCH}-unknown-linux-gnu-install_only.tar.gz"
PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PY_RELEASE}/${PY_TARBALL//+/%2B}"
PY_CACHE="/tmp/${PY_TARBALL}"
if [ ! -s "$PY_CACHE" ]; then
    echo "[Info] Lade Python ${PY_VERSION} (python-build-standalone)..."
    wget -q "$PY_URL" -O "$PY_CACHE" || {
        echo "FEHLER: Python konnte nicht geladen werden ($PY_URL)."
        rm -f "$PY_CACHE"
        exit 1
    }
fi
if ! tar -tzf "$PY_CACHE" >/dev/null 2>&1; then
    echo "FEHLER: $PY_CACHE ist kein gültiges tar.gz — Download kaputt."
    rm -f "$PY_CACHE"
    exit 1
fi

# 1d. System-Bibliotheken, die nicht überall installiert sind
#
# - xcb-util-*: Qt >= 6.5 startet ohne libxcb-cursor0 gar nicht, die
#   anderen braucht das xcb-Plugin ebenfalls. Fehlen z. B. im Katalog-Test.
# - PortAudio (+ JACK-Client): sounddevice wird schon beim Start importiert.
#   Wird NUR benutzt, wenn das System keine eigene PortAudio hat
#   (siehe sitecustomize.py weiter unten).
# Quelle: die offiziellen Ubuntu-22.04-Pakete (jammy). Die sind gegen ein
# altes glibc (2.35) gebaut — Bibliotheken vom Arch-Host bräuchten oft
# glibc >= 2.38 und liefen dort NICHT.
# Neue Version eines Pakets: Dateiname unter
#   https://packages.ubuntu.com/jammy/<paketname>  (Download-Seite)
UBUNTU_POOL="http://archive.ubuntu.com/ubuntu/pool"
DEBS_XCB=(
    "universe/x/xcb-util-cursor/libxcb-cursor0_0.1.1-4ubuntu1_amd64.deb"
    "main/x/xcb-util-wm/libxcb-icccm4_0.4.1-1.1build2_amd64.deb"
    "main/x/xcb-util-image/libxcb-image0_0.4.0-2_amd64.deb"
    "main/x/xcb-util-keysyms/libxcb-keysyms1_0.4.0-1build3_amd64.deb"
    "main/x/xcb-util-renderutil/libxcb-render-util0_0.3.9-1build3_amd64.deb"
    "main/x/xcb-util/libxcb-util1_0.4.0-1build2_amd64.deb"
    "main/libx/libxkbcommon/libxkbcommon-x11-0_1.4.0-1_amd64.deb"
    "main/libx/libxcb/libxcb-xkb1_1.14-3ubuntu3_amd64.deb"
    "main/libx/libxcb/libxcb-xinerama0_1.14-3ubuntu3_amd64.deb"
)
DEBS_AUDIO=(
    "universe/p/portaudio19/libportaudio2_19.6.0-1.1_amd64.deb"
    "main/j/jackd2/libjack-jackd2-0_1.9.20~dfsg-1_amd64.deb"
    "main/d/db5.3/libdb5.3_5.3.28+dfsg1-0.8ubuntu3_amd64.deb"
    "main/libs/libsamplerate/libsamplerate0_0.2.2-1build1_amd64.deb"
)
DEB_CACHE="/tmp/dvt-debs"
mkdir -p "$DEB_CACHE"

# .deb laden (mit Cache) und die .so-Dateien daraus nach $2 kopieren
fetch_deb_libs() {
    local rel="$1" dest="$2"
    local file="$DEB_CACHE/$(basename "$rel")"
    if [ ! -s "$file" ]; then
        local url="$UBUNTU_POOL/${rel//+/%2B}"
        url="${url//\~/%7E}"
        wget -q "$url" -O "$file" || {
            echo "FEHLER: $url nicht ladbar."
            echo "        Vermutlich gibt es eine neuere Version des Pakets —"
            echo "        Dateinamen in DEBS_XCB/DEBS_AUDIO anpassen."
            rm -f "$file"
            exit 1
        }
    fi
    local tmp
    tmp="$(mktemp -d)"
    if command -v bsdtar >/dev/null; then
        (cd "$tmp" && bsdtar -xf "$file" 'data.tar.*' && bsdtar -xf data.tar.*)
    elif command -v ar >/dev/null; then
        (cd "$tmp" && ar x "$file" && tar -xf data.tar.*)
    else
        echo "FEHLER: weder bsdtar noch ar gefunden (pacman -S libarchive binutils)."
        exit 1
    fi
    mkdir -p "$dest"
    # nur Bibliotheken, Symlinks aufgelöst (cp -L)
    find "$tmp" -path '*/lib/*' -name '*.so*' \( -type f -o -type l \) \
        -exec cp -L {} "$dest/" \;
    rm -rf "$tmp"
}

# 2. AppDir Struktur anlegen
echo "[1/5] Erstelle AppDir Struktur..."
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$LIB"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# 3. Programmdateien kopieren
echo "[2/5] Kopiere Programmdateien..."
cp main.py "$LIB/"
cp -r core voice ui "$LIB/"
mkdir -p "$LIB/assets"
cp -r assets/* "$LIB/assets/"
# Changelog- und Highlights-Fenster (ui/docviewer.py)
cp CHANGELOG.md HIGHLIGHTS.md "$LIB/"

# Python-Cache nicht mitschleppen
find "$LIB" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# Wrapper-Script in /usr/bin — startet über AppRun (dort ist die Umgebung)
cat > "$BUILD_DIR/usr/bin/dream-voicetraining" << 'WRAPPER'
#!/bin/bash
exec "$(dirname "$(readlink -f "$0")")/../../AppRun" "$@"
WRAPPER
chmod +x "$BUILD_DIR/usr/bin/dream-voicetraining"

# 4. Icon und Desktop-Datei (generiert, nicht fest)
echo "[3/5] Setze Icon und Desktop-Eintrag..."
cp packaging/dream-voicetraining.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/dream-voicetraining.svg"
cp packaging/dream-voicetraining.svg "$BUILD_DIR/dream-voicetraining.svg"

cat > "$BUILD_DIR/usr/share/applications/dream-voicetraining.desktop" << EOF
[Desktop Entry]
Name=Dream-VoiceTraining
Comment=Voice Analysis
Exec=dream-voicetraining
Icon=dream-voicetraining
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Recorder;
StartupWMClass=Dream-VoiceTraining
EOF

cp "$BUILD_DIR/usr/share/applications/dream-voicetraining.desktop" "$BUILD_DIR/dream-voicetraining.desktop"

# 5. Python + Abhängigkeiten ins AppDir bundeln
echo "[4/5] Bundele Python ${PY_VERSION}, Abhängigkeiten und Bibliotheken..."
tar -xzf "$PY_CACHE" -C "$BUILD_DIR/usr"          # -> usr/python/
PY="$BUILD_DIR/usr/python/bin/python3"
SITE="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"

# mit dem MITGELIEFERTEN Python installieren -> Wheels passen zu ihm
PYTHONNOUSERSITE=1 "$PY" -m pip install --quiet --no-compile \
    --disable-pip-version-check --no-warn-script-location \
    -r requirements.txt || {
    echo "FEHLER: Python-Abhängigkeiten konnten nicht installiert werden."
    exit 1
}
find "$SITE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
# Ballast aus dem Standalone-Python, den die App nie braucht
rm -rf "$BUILD_DIR"/usr/python/lib/python3.*/{idlelib,tkinter,turtledemo,test} \
       "$BUILD_DIR"/usr/python/lib/{libtcl,libtk}* \
       "$BUILD_DIR"/usr/python/lib/{tcl,tk}[0-9]* \
       "$BUILD_DIR"/usr/python/include 2>/dev/null || true

# System-Bibliotheken (siehe 1d)
for d in "${DEBS_XCB[@]}";   do fetch_deb_libs "$d" "$BUILD_DIR/usr/lib/bundled"; done
for d in "${DEBS_AUDIO[@]}"; do fetch_deb_libs "$d" "$BUILD_DIR/usr/lib/portaudio"; done

# PortAudio-Fallback: sounddevice sucht mit ctypes.util.find_library.
# Findet das nichts (keine PortAudio im System), nehmen wir die
# mitgelieferte und laden vorher ihre Abhängigkeiten (JACK), falls auch
# die fehlen. Hat das System eine eigene, bleibt die (passt zum Audio-Setup).
cat > "$SITE/sitecustomize.py" << 'SITECUSTOM'
"""Nur in der AppImage: mitgelieferte PortAudio, wenn das System keine hat."""
import ctypes
import ctypes.util
import os

_find = ctypes.util.find_library
_DIR = os.environ.get("DVT_PORTAUDIO_DIR", "")


def _find_library(name):
    found = _find(name)
    if found is None and name == "portaudio" and _DIR:
        lib = os.path.join(_DIR, "libportaudio.so.2")
        if os.path.exists(lib):
            # Abhängigkeiten nur laden, wenn das System sie nicht hat
            for soname, short in (("libdb-5.3.so", "db-5.3"),
                                  ("libsamplerate.so.0", "samplerate"),
                                  ("libjack.so.0", "jack")):
                if _find(short) is None:
                    ctypes.CDLL(os.path.join(_DIR, soname), ctypes.RTLD_GLOBAL)
            return lib
    return found


ctypes.util.find_library = _find_library
SITECUSTOM

# AppRun Script
cat > "$BUILD_DIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"

# Mitgeliefertes Python — Einstellungen/Pakete vom System ignorieren
unset PYTHONHOME PYTHONPATH
export PYTHONNOUSERSITE=1

# xcb-Bibliotheken für Qt (fehlen auf manchen Systemen, z. B. Ubuntu 22.04)
export LD_LIBRARY_PATH="$HERE/usr/lib/bundled${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
# PortAudio-Fallback, siehe sitecustomize.py
export DVT_PORTAUDIO_DIR="$HERE/usr/lib/portaudio"

cd "$HERE/usr/lib/dream-voicetraining"
exec "$HERE/usr/python/bin/python3" main.py "$@"
APPRUN
chmod +x "$BUILD_DIR/AppRun"

# 6. AppImage bauen (mit der statischen Runtime von oben)
#
# Update-Information für Delta-Updates (zsync). Sie wird IN die AppImage
# geschrieben und sagt Update-Tools (AppImageUpdate, AppImageLauncher,
# AM, AppManager, Gear Lever ...), wo die neue Version liegt:
#   gh-releases-zsync | Benutzer | Repo | latest | Dateimuster
# "latest" = das neueste GitHub-Release, das KEIN Pre-release ist.
# Daneben entsteht Dream-VoiceTraining-<version>-x86_64.AppImage.zsync: die
# Prüfsummen der Blöcke. Ein Tool vergleicht sie mit der alten AppImage
# und lädt nur die Blöcke, die sich geändert haben.
# BEIDE Dateien gehören ins GitHub-Release.
# Ohne zsync bauen: DVT_NO_ZSYNC=1 bash packaging/build-appimage.sh
UPDATE_INFO="gh-releases-zsync|yakuda-stack|Dream-VoiceTraining|latest|Dream-VoiceTraining-*${ARCH}.AppImage.zsync"
UPDATE_ARGS=()
if [ -z "${DVT_NO_ZSYNC:-}" ]; then
    UPDATE_ARGS=(-u "$UPDATE_INFO")
fi
# Dateirechte: alles für alle lesbar, Ordner/Programme ausführbar.
# Sonst übernimmt cp z. B. 600 aus dem Projekt und ein ANDERER Benutzer
# (wie der Katalog-Test) bekommt PermissionError.
chmod -R u+rwX,go+rX,go-w "$BUILD_DIR"
if [ -n "$(find "$BUILD_DIR" ! -perm -o+r -print -quit)" ]; then
    echo "FEHLER: Es gibt noch Dateien, die nicht für alle lesbar sind."
    exit 1
fi

echo "[5/5] Baue AppImage..."
# Die .zsync legt appimagetool (zsyncmake) im AKTUELLEN Ordner ab, nicht
# neben der AppImage. Darum im build/-Ordner aufrufen und nur Dateinamen
# übergeben. Alte .zsync-Reste aus dem Projekt-Root vorher wegräumen.
PROJECT_DIR="$(pwd)"
rm -f "$PROJECT_DIR"/${APP}-*-${ARCH}.AppImage.zsync
(cd "$OUT_DIR" && ARCH="$ARCH" "$APPIMAGETOOL" --runtime-file "$RUNTIME" \
    "${UPDATE_ARGS[@]}" "$BUILD_DIR" "$(basename "$OUT")")

# Falls ein anderes appimagetool sie doch woanders ablegt: einsammeln
for d in "$PROJECT_DIR" "$BUILD_DIR"; do
    if [ ! -s "$OUT.zsync" ] && [ -s "$d/$(basename "$OUT").zsync" ]; then
        mv "$d/$(basename "$OUT").zsync" "$OUT.zsync"
    fi
done
# Notfalls selbst erzeugen (braucht zsync: pacman -S zsync)
if [ -z "${DVT_NO_ZSYNC:-}" ] && [ ! -s "$OUT.zsync" ] && command -v zsyncmake >/dev/null; then
    echo "[Info] appimagetool hat keine .zsync gebaut — erzeuge sie mit zsyncmake..."
    (cd "$OUT_DIR" && zsyncmake -u "$(basename "$OUT")" -o "$(basename "$OUT").zsync" "$(basename "$OUT")")
fi

# 7. Gegenprobe: die fertige Datei darf libfuse.so.2 nicht mehr brauchen.
# Ohne diesen Check merkt man den Rückfall auf die alte Runtime erst,
# wenn sich der erste Mint-Nutzer meldet.
echo ""
if head -c 400000 "$OUT" | strings | grep -q "libfuse\.so\.2"; then
    echo "WARNUNG: Die AppImage verweist noch auf libfuse.so.2 —"
    echo "         die statische Runtime wurde offenbar nicht benutzt."
    echo "         Auf Mint/Ubuntu >= 22.04 startet sie so nicht."
else
    echo "✔ Runtime ist statisch (läuft mit fuse2 UND fuse3)"
fi

# 7b. Delta-Updates: .zsync da, Update-Info wirklich in der Datei?
if [ -z "${DVT_NO_ZSYNC:-}" ]; then
    # ohne APPIMAGE_EXTRACT_AND_RUN: damit würde die Runtime auspacken und
    # die App mit diesem Argument starten, statt es selbst zu beantworten
    EMBEDDED="$(env -u APPIMAGE_EXTRACT_AND_RUN "$OUT" \
        --appimage-updateinformation 2>/dev/null || true)"
    # Beides ist PFLICHT: ohne Update-Info weiß kein Update-Tool, wo es
    # suchen soll, ohne .zsync hat es nichts zum Vergleichen.
    if [ "$EMBEDDED" = "$UPDATE_INFO" ]; then
        echo "✔ Update-Info eingebettet: $EMBEDDED"
    else
        echo "FEHLER: Update-Info fehlt in der AppImage (gelesen: '$EMBEDDED')."
        exit 1
    fi
    if [ -s "$OUT.zsync" ]; then
        echo "✔ Delta-Update-Datei: build/$(basename "$OUT").zsync"
    else
        echo "FEHLER: keine .zsync erzeugt — AppImage-Updates gehen so nicht."
        echo "        zsync installieren (pacman -S zsync) und neu bauen,"
        echo "        oder APPIMAGETOOL leer lassen (das mitgeladene bringt zsyncmake mit)."
        exit 1
    fi
fi

# 8. AppDir wegräumen — in build/ bleiben die AppImage und ihre .zsync
rm -rf "$BUILD_DIR"

echo "✔ Fertig: build/$(basename "$OUT")"
if [ -s "$OUT.zsync" ]; then
    echo "   Ins GitHub-Release: $(basename "$OUT") UND $(basename "$OUT").zsync"
fi
echo "   Zum Starten: chmod +x \"$OUT\" && \"$OUT\""
echo "   Ohne FUSE testen: APPIMAGE_EXTRACT_AND_RUN=1 \"$OUT\""
