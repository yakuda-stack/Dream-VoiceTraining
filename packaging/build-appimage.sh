#!/usr/bin/env bash
# Baut zwei AppImages mit eigener Python-Umgebung:
#
#   Dream-VoiceTraining-<version>-x86_64.AppImage         FUSE 3 (type2-runtime)
#   Dream-VoiceTraining-<version>-fuse2-x86_64.AppImage   FUSE 2 (AppImageKit)
#
# Warum zwei: die alte Laufzeit braucht libfuse2, das auf neueren Systemen
# nicht mehr vorinstalliert ist. Die neue braucht FUSE 3, das auf aelteren
# fehlt. Beide zusammen decken so ziemlich alles ab. Zur Not laeuft jedes
# AppImage auch mit --appimage-extract-and-run, ganz ohne FUSE.
#
# Voraussetzungen: python3 mit venv, wget, fuse2 oder fuse3.
# appimagetool und die Laufzeiten werden bei Bedarf heruntergeladen.
#
# Das AppImage bringt PySide6 und parselmouth mit und wird dadurch gross
# (grob 250-350 MB). Was es NICHT mitbringt, sind ALSA, PulseAudio und
# PipeWire — die kommen vom Wirtssystem, sonst funktioniert die
# Geraeteauswahl nicht.
set -euo pipefail

APP=Dream-VoiceTraining
ID=dream-voicetraining
ARCH="$(uname -m)"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build"
APPDIR="$BUILD/$APP.AppDir"
VERSION="${1:-$(grep -oP 'APP_VERSION = "\K[^"]+' "$ROOT/paths.py")}"

mkdir -p "$BUILD"
echo ">> $APP $VERSION für $ARCH"

# ---------------------------------------------------------------- AppDir

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib/$ID" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/scalable/apps"

echo ">> Python-Umgebung anlegen"
python3 -m venv "$APPDIR/usr/python"
"$APPDIR/usr/python/bin/pip" install --upgrade pip wheel --quiet
"$APPDIR/usr/python/bin/pip" install --quiet -r "$ROOT/requirements.txt"

echo ">> Programmdateien kopieren"
cp "$ROOT"/*.py "$APPDIR/usr/lib/$ID/"
cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY_NOTICES.md" "$APPDIR/usr/lib/$ID/"

echo ">> Metadaten"
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

echo ">> Ballast entfernen"
find "$APPDIR/usr/python" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$APPDIR/usr/python" -type d -name "tests" -prune -exec rm -rf {} +
rm -rf "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/qml \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/translations \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/examples 2>/dev/null || true

# ------------------------------------------------------------ Werkzeuge

fetch() {
  local url="$1" target="$2"
  [ -x "$target" ] && return 0
  echo ">> Hole $(basename "$target")"
  wget -q --show-progress -O "$target" "$url"
  chmod +x "$target"
}

TOOL="$BUILD/appimagetool-$ARCH.AppImage"
RT_FUSE3="$BUILD/runtime-fuse3-$ARCH"
RT_FUSE2="$BUILD/runtime-fuse2-$ARCH"

fetch "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage" "$TOOL"
fetch "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-$ARCH" "$RT_FUSE3"
fetch "https://github.com/AppImage/AppImageKit/releases/download/continuous/runtime-$ARCH" "$RT_FUSE2"

# appimagetool selbst ist ein AppImage. Ohne FUSE auf dem Bauhost muss es
# sich selbst entpacken.
run_tool() {
  if "$TOOL" --version >/dev/null 2>&1; then
    ARCH="$ARCH" "$TOOL" "$@"
  else
    ARCH="$ARCH" "$TOOL" --appimage-extract-and-run "$@"
  fi
}

# --------------------------------------------------------------- Packen

build_one() {
  local runtime="$1" suffix="$2" out
  out="$BUILD/$APP-$VERSION$suffix-$ARCH.AppImage"
  echo ">> Baue $(basename "$out")"
  rm -f "$out"
  run_tool --runtime-file "$runtime" "$APPDIR" "$out"
  echo "   $(du -h "$out" | cut -f1)"
}

build_one "$RT_FUSE3" ""
build_one "$RT_FUSE2" "-fuse2"

echo
echo "fertig:"
ls -1 "$BUILD"/*.AppImage
echo
echo "Beide testen, dann beide ans GitHub-Release hängen."
echo "Kurztest ohne FUSE:  ./Datei.AppImage --appimage-extract-and-run"
