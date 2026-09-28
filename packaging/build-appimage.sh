#!/bin/bash
# Dream-VoiceTraining — AppImage Builder (bundled Python)
# Benötigt: python3, pip (appimagetool wird automatisch geladen)
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
for f in main.py core/paths.py ui/mainwindow.py packaging/dream-voicetraining.svg \
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

# Wrapper-Script in /usr/bin
cat > "$BUILD_DIR/usr/bin/dream-voicetraining" << 'WRAPPER'
#!/bin/bash
cd "$(dirname "$0")/../lib/dream-voicetraining"
exec python3 main.py "$@"
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

# 5. Python-Abhängigkeiten ins AppDir bundeln
echo "[4/5] Bundele Python-Abhängigkeiten..."
SITE="$BUILD_DIR/usr/lib/python3"
mkdir -p "$SITE"

if python3 -m pip --version >/dev/null 2>&1; then
    PIP=(python3 -m pip)
else
    PIP=(pip)
fi

"${PIP[@]}" install --quiet --no-compile --target="$SITE" -r requirements.txt || {
    echo "FEHLER: Python-Abhängigkeiten konnten nicht installiert werden."
    exit 1
}
find "$SITE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

# AppRun Script
cat > "$BUILD_DIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$HERE/usr/lib/python3:$PYTHONPATH"
export PATH="$HERE/usr/bin:$PATH"

# Prüfe ob python3 vorhanden ist
if ! command -v python3 >/dev/null 2>&1; then
    echo "Dream-VoiceTraining: python3 nicht gefunden." >&2
    echo "  Debian/Ubuntu/Mint:  sudo apt install python3" >&2
    echo "  Fedora:              sudo dnf install python3" >&2
    exit 1
fi

exec "$HERE/usr/bin/dream-voicetraining" "$@"
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
