#!/usr/bin/env bash
#
# Dream-VoiceTraining — Installation
#
#   curl -fsSL https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh | bash
#
# oder, wenn du lieber erst hineinschaust (empfohlen):
#
#   curl -fsSLO https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh
#   less install.sh && bash install.sh
#
# Was passiert:
#   1. Distribution erkennen und die Systempakete nachinstallieren, die es
#      nicht als Python-Paket gibt (PortAudio, venv, git).
#   2. Quelltext nach ~/.local/lib/dream-voicetraining holen.
#   3. Eigene Python-Umgebung anlegen und die Abhaengigkeiten hineinlegen.
#   4. Starter, Menueeintrag und Symbole in ~/.local eintragen.
#
# Nichts davon fasst Systemverzeichnisse an; sudo wird ausschliesslich fuer
# Schritt 1 benutzt und vorher angekuendigt.
#
#   bash install.sh --uninstall     entfernt alles wieder
#   bash install.sh --no-deps       ueberspringt die Systempakete
#
# Copyright (C) 2026  Yakuda — GPL-3.0-or-later

set -euo pipefail

APP_ID="dream-voicetraining"
APP_NAME="Dream-VoiceTraining"
REPO="https://github.com/yakuda-stack/Dream-VoiceTraining.git"
BRANCH="main"

PREFIX="${PREFIX:-$HOME/.local}"
LIBDIR="$PREFIX/lib/$APP_ID"
BINDIR="$PREFIX/bin"
APPDIR="$PREFIX/share/applications"
ICONBASE="$PREFIX/share/icons/hicolor"

SKIP_DEPS=0
ACTION="install"
for arg in "$@"; do
  case "$arg" in
    --uninstall) ACTION="uninstall" ;;
    --no-deps)   SKIP_DEPS=1 ;;
    -h|--help)   sed -n '2,28p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $arg" >&2; exit 1 ;;
  esac
done

say()  { printf '\033[1;36m::\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

# ------------------------------------------------------------ deinstallieren

if [ "$ACTION" = "uninstall" ]; then
  rm -rf "$LIBDIR" "$BINDIR/$APP_ID" "$APPDIR/$APP_ID.desktop"
  rm -f "$ICONBASE/scalable/apps/$APP_ID.svg"
  for size in 16 24 32 48 64 128 256 512; do
    rm -f "$ICONBASE/${size}x${size}/apps/$APP_ID.png"
  done
  command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$APPDIR" 2>/dev/null || true
  say "Entfernt."
  echo "   Deine Aufnahmen und Einstellungen bleiben erhalten:"
  echo "     ~/.config/$APP_ID"
  echo "     ~/.local/share/$APP_ID"
  exit 0
fi

# ------------------------------------------------------------- Systempakete

detect_family() {
  [ -r /etc/os-release ] || { echo unknown; return; }
  # shellcheck disable=SC1091
  . /etc/os-release
  for candidate in "${ID:-}" ${ID_LIKE:-}; do
    case "$candidate" in
      debian|ubuntu)            echo debian; return ;;
      fedora|rhel|centos)       echo fedora; return ;;
      arch|archlinux|cachyos)   echo arch;   return ;;
      opensuse*|suse)           echo suse;   return ;;
    esac
  done
  echo unknown
}

install_deps() {
  local family="$1" sudo_cmd=""
  if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 || die "sudo fehlt und du bist nicht root."
    sudo_cmd="sudo"
  fi

  case "$family" in
    debian)
      set -- python3 python3-venv python3-pip libportaudio2 libpulse0 git
      say "Systempakete (apt): $*"
      $sudo_cmd apt-get update -qq
      $sudo_cmd apt-get install -y "$@"
      ;;
    fedora)
      set -- python3 python3-pip portaudio pulseaudio-utils git
      say "Systempakete (dnf): $*"
      $sudo_cmd dnf install -y "$@"
      ;;
    arch)
      set -- python python-pip portaudio libpulse git
      say "Systempakete (pacman): $*"
      $sudo_cmd pacman -S --needed --noconfirm "$@"
      ;;
    suse)
      set -- python3 python3-pip portaudio pulseaudio-utils git
      say "Systempakete (zypper): $*"
      $sudo_cmd zypper --non-interactive install "$@"
      ;;
    *)
      warn "Distribution nicht erkannt. Bitte selbst installieren:"
      warn "  Python 3.10+ samt venv, PortAudio, libpulse (für pactl), git"
      warn "Danach mit --no-deps erneut aufrufen."
      exit 1
      ;;
  esac
}

# --------------------------------------------------------------- Quelltext

fetch_source() {
  # Aus einem vorhandenen Checkout heraus wird nichts heruntergeladen.
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -f "$here/main.py" ] && [ -f "$here/requirements.txt" ]; then
    say "Verwende den Quelltext aus $here"
    SOURCE="$here"
    return
  fi

  command -v git >/dev/null 2>&1 || die "git fehlt."
  SOURCE="$(mktemp -d)"
  say "Hole $REPO"
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$SOURCE/src" >/dev/null 2>&1 \
    || die "Klonen fehlgeschlagen."
  SOURCE="$SOURCE/src"
}

# ------------------------------------------------------------------ Ablauf

FAMILY="$(detect_family)"
say "$APP_NAME wird installiert  ·  erkannt: $FAMILY"

if [ "$SKIP_DEPS" -eq 0 ]; then
  install_deps "$FAMILY"
else
  say "Systempakete übersprungen (--no-deps)"
fi

command -v python3 >/dev/null 2>&1 || die "python3 nicht gefunden."
python3 - <<'PY' || die "Python 3.10 oder neuer wird gebraucht."
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY

if ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
  warn "PortAudio wurde nicht gefunden — ohne die Bibliothek gibt es keine"
  warn "Aufnahme. Die Installation läuft weiter, prüf das aber."
fi

fetch_source

say "Programmdateien nach $LIBDIR"
rm -rf "$LIBDIR"
mkdir -p "$LIBDIR" "$BINDIR" "$APPDIR" "$ICONBASE/scalable/apps"
cp "$SOURCE"/*.py "$LIBDIR/"
cp "$SOURCE/LICENSE" "$SOURCE/THIRD_PARTY_NOTICES.md" "$LIBDIR/" 2>/dev/null || true

say "Python-Umgebung anlegen (das dauert eine Minute)"
python3 -m venv "$LIBDIR/venv"
"$LIBDIR/venv/bin/pip" install --upgrade pip --quiet
"$LIBDIR/venv/bin/pip" install --quiet -r "$SOURCE/requirements.txt"

say "Starter und Menüeintrag"
cat > "$BINDIR/$APP_ID" <<LAUNCH
#!/bin/sh
exec "$LIBDIR/venv/bin/python3" "$LIBDIR/main.py" "\$@"
LAUNCH
chmod +x "$BINDIR/$APP_ID"

sed "s|^Exec=.*|Exec=$BINDIR/$APP_ID|" \
    "$SOURCE/packaging/$APP_ID.desktop" > "$APPDIR/$APP_ID.desktop"
cp "$SOURCE/packaging/$APP_ID.svg" "$ICONBASE/scalable/apps/$APP_ID.svg"
for size in 16 24 32 48 64 128 256 512; do
  if [ -f "$SOURCE/packaging/icons/$size.png" ]; then
    mkdir -p "$ICONBASE/${size}x${size}/apps"
    cp "$SOURCE/packaging/icons/$size.png" "$ICONBASE/${size}x${size}/apps/$APP_ID.png"
  fi
done
command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$APPDIR" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -f -t "$ICONBASE" 2>/dev/null || true

echo
say "Fertig."
echo "   Start über das Anwendungsmenü oder:  $BINDIR/$APP_ID"
case ":$PATH:" in
  *":$BINDIR:"*) ;;
  *) echo
     warn "$BINDIR liegt nicht in deinem PATH."
     echo "   fish:  fish_add_path $BINDIR"
     echo "   bash:  echo 'export PATH=\"\$PATH:$BINDIR\"' >> ~/.bashrc" ;;
esac
echo
echo "   Deinstallieren:  bash install.sh --uninstall"
