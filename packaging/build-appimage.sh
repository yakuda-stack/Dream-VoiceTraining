#!/usr/bin/env bash
# Baut ein AppImage mit eigenem Python-Environment.
#
# Voraussetzungen: python3, python3-venv, wget, fuse2 oder fuse3.
# appimagetool wird bei Bedarf heruntergeladen.
#
# Das AppImage bringt PySide6 und parselmouth mit und wird dadurch gross
# (grob 250-350 MB). Was es NICHT mitbringt, sind ALSA, PulseAudio und
# PipeWire — die kommen vom Wirtssystem, sonst funktioniert die
# Geraeteauswahl nicht.
set -euo pipefail

APP=Dream-VoiceTraining
ID=dream-voicetraining
VERSION="${1:-$(grep -oP 'APP_VERSION = "\K[^"]+' ../paths.py)}"
ARCH="$(uname -m)"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$ROOT/build"
APPDIR="$BUILD/$APP.AppDir"

echo ">> $APP $VERSION für $ARCH"
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
# Qt unter Wayland ohne gesetzte Plattform sonst gern auf xcb zurueckfaellt
[ -n "${QT_QPA_PLATFORM:-}" ] || {
    [ -n "${WAYLAND_DISPLAY:-}" ] && export QT_QPA_PLATFORM=wayland
}
export PATH="$HERE/usr/python/bin:$PATH"
exec "$HERE/usr/python/bin/python3" "$HERE/usr/lib/dream-voicetraining/main.py" "$@"
RUN
chmod +x "$APPDIR/AppRun"

# Der venv verweist auf das Python des Bauhosts; das umbiegen.
sed -i "s|^#!.*python3\$|#!/usr/bin/env python3|" "$APPDIR/usr/python/bin/"* 2>/dev/null || true

echo ">> Ballast entfernen"
find "$APPDIR/usr/python" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$APPDIR/usr/python" -type d -name "tests" -prune -exec rm -rf {} +
rm -rf "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/qml \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/Qt/translations \
       "$APPDIR/usr/python/lib/python"*/site-packages/PySide6/examples 2>/dev/null || true

TOOL="$BUILD/appimagetool-$ARCH.AppImage"
if [ ! -x "$TOOL" ]; then
  echo ">> appimagetool holen"
  wget -q -O "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage"
  chmod +x "$TOOL"
fi

echo ">> AppImage bauen"
OUT="$BUILD/$APP-$VERSION-$ARCH.AppImage"
ARCH="$ARCH" "$TOOL" "$APPDIR" "$OUT"

echo
echo "fertig: $OUT"
du -h "$OUT" | cut -f1
