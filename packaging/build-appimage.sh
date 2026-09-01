#!/usr/bin/env bash
# Baut ein AppImage mit eigener Python-Umgebung.
#
#   bash packaging/build-appimage.sh
#     -> Dream-VoiceTraining-<version>-x86_64.AppImage
#        Eine Datei fuer alles. Die Laufzeit (uruntime) nimmt FUSE 3, faellt
#        auf FUSE 2 zurueck und entpackt sich notfalls selbst, wenn gar kein
#        FUSE vorhanden ist.
#
#   bash packaging/build-appimage.sh --classic
#     -> zusaetzlich zwei Dateien mit den offiziellen AppImage-Laufzeiten,
#        eine fuer FUSE 3 und eine fuer FUSE 2. Nur noetig, wenn jemand die
#        Originallaufzeit ausdruecklich verlangt.
#
# Voraussetzungen: python3 mit venv, curl. FUSE wird zum Bauen nicht gebraucht.
#
# Das AppImage bringt PySide6 und parselmouth mit und wird dadurch gross
# (grob 250-350 MB). Was es NICHT mitbringt, sind ALSA, PulseAudio und
# PipeWire — die kommen vom Wirtssystem, sonst funktioniert die
# Geraeteauswahl nicht.
set -euo pipefail

APP=Dream-VoiceTraining
ID=dream-voicetraining
ARCH="$(uname -m)"
URUNTIME_VERSION="v0.6.1"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build"
APPDIR="$BUILD/$APP.AppDir"

CLASSIC=0
VERSION=""
for arg in "$@"; do
  case "$arg" in
    --classic) CLASSIC=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) VERSION="$arg" ;;
  esac
done
[ -n "$VERSION" ] || VERSION="$(grep -oP 'APP_VERSION = "\K[^"]+' "$ROOT/paths.py")"

say() { printf '\033[1;36m::\033[0m %s\n' "$*"; }

mkdir -p "$BUILD"
say "$APP $VERSION für $ARCH"

# ---------------------------------------------------------------- AppDir

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/$ID" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/scalable/apps"

say "Python-Umgebung anlegen"
python3 -m venv "$APPDIR/usr/python"
"$APPDIR/usr/python/bin/pip" install --upgrade pip wheel --quiet
"$APPDIR/usr/python/bin/pip" install --quiet -r "$ROOT/requirements.txt"

say "Programmdateien kopieren"
cp "$ROOT"/*.py "$APPDIR/usr/lib/$ID/"
cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY_NOTICES.md" "$APPDIR/usr/lib/$ID/"

say "Metadaten"
cp "$ROOT/packaging/$ID.desktop" "$APPDIR/usr/share/applications/$ID.desktop"
cp "$ROOT/packaging/$ID.desktop" "$APPDIR/$ID.desktop"
cp "$ROOT/packaging/$ID.svg" \
   "$APPDIR/usr/share/icons/hicolor/scalable/apps/$ID.svg"
cp "$ROOT/packaging/$ID.svg" "$APPDIR/$ID.svg"
for size in 32 48 64 128 256; do
  install -Dm644 "$ROOT/packaging/icons/$size.png" \
    "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/$ID.png"
done
cp "$ROOT/packaging/icons/256.png" "$APPDIR/.DirIcon"

cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
# Qt faellt unter Wayland sonst gern auf xcb zurueck
[ -n "${QT_QPA_PLATFORM:-}" ] || {
    [ -n "${WAYLAND_DISPLAY:-}" ] && export QT_QPA_PLATFORM=wayland
}
export PATH="$HERE/usr/python/bin:$PATH"
exec "$HERE/usr/python/bin/python3" "$HERE/usr/lib/dream-voicetraining/main.py" "$@"
RUN
chmod +x "$APPDIR/AppRun"

# Der venv zeigt auf das Python des Bauhosts; Shebangs neutralisieren.
sed -i "1s|^#!.*python3\$|#!/usr/bin/env python3|" "$APPDIR/usr/python/bin/"* 2>/dev/null || true

say "Ballast entfernen"
find "$APPDIR/usr/python" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$APPDIR/usr/python" -type d -name "tests" -prune -exec rm -rf {} +
rm -rf "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/qml \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/translations \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/examples 2>/dev/null || true

# ------------------------------------------------------------ Werkzeuge

fetch() {
  local url="$1" target="$2"
  [ -x "$target" ] && return 0
  say "Hole $(basename "$target")"
  curl -fsSL --retry 3 -o "$target" "$url"
  chmod +x "$target"
}

TOOL="$BUILD/appimagetool-$ARCH.AppImage"
fetch "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage" "$TOOL"

# appimagetool ist selbst ein AppImage. Ohne FUSE auf dem Bauhost muss es
# sich entpacken, sonst kommt es gar nicht erst hoch.
TOOL_ARGS=()
"$TOOL" --version >/dev/null 2>&1 || TOOL_ARGS=(--appimage-extract-and-run)

pack() {
  local runtime="$1" out="$2"
  shift 2
  say "Baue $(basename "$out")"
  rm -f "$out"
  ARCH="$ARCH" "$TOOL" "${TOOL_ARGS[@]}" --runtime-file "$runtime" "$@" \
      "$APPDIR" "$out"
  printf '   %s\n' "$(du -h "$out" | cut -f1)"
}

# ------------------------------------------------------- Hybrid (Vorgabe)

URUNTIME="$BUILD/uruntime-$ARCH"
fetch "https://github.com/VHSgunzo/uruntime/releases/download/$URUNTIME_VERSION/uruntime-appimage-squashfs-$ARCH" "$URUNTIME"
pack "$URUNTIME" "$BUILD/$APP-$VERSION-$ARCH.AppImage"

# ------------------------------------------------ Originallaufzeiten

if [ "$CLASSIC" -eq 1 ]; then
  RT3="$BUILD/runtime-fuse3-$ARCH"
  RT2="$BUILD/runtime-fuse2-$ARCH"
  fetch "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-$ARCH" "$RT3"
  fetch "https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-$ARCH" "$RT2"

  pack "$RT3" "$BUILD/$APP-$VERSION-fuse3-$ARCH.AppImage"
  # Die alte Laufzeit versteht nur xz und zlib, appimagetool packt sonst zstd.
  pack "$RT2" "$BUILD/$APP-$VERSION-fuse2-$ARCH.AppImage" --comp xz
fi

echo
say "fertig:"
ls -1 "$BUILD"/*.AppImage
echo
echo "   Kurztest:            ./Datei.AppImage"
echo "   Test ohne FUSE:      ./Datei.AppImage --appimage-extract-and-run"
