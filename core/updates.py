# Dream-VoiceTraining — voice analysis for training your speaking voice
# Copyright (C) 2026  Yakuda
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Aktualisierungspruefung gegen die GitHub-Releases, ohne Qt.

Gefragt wird nur nach dem neuesten Release; gesendet wird dabei nichts
ausser der Anfrage selbst. Laeuft nur nach Zustimmung (einmalige Frage),
aenderbar unter Einstellungen → Info.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field

from core import paths

API_URL = ("https://api.github.com/repos/yakuda-stack/Dream-VoiceTraining"
           "/releases/latest")
RELEASES_URL = paths.APP_URL + "/releases"
TIMEOUT = 6.0
MAX_BYTES = 512 * 1024


@dataclass
class Release:
    version: str
    url: str
    notes: str = ""
    assets: dict[str, str] = field(default_factory=dict)   # Name -> Download


def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.0' / '1.2.0_beta' -> (1, 2, 0). Unlesbares wird zu ()."""
    match = re.match(r"^\s*v?(\d+(?:\.\d+)*)", str(text or ""))
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(remote: str, local: str = paths.APP_VERSION) -> bool:
    a, b = parse_version(remote), parse_version(local)
    if not a or not b:
        return False
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) > b + (0,) * (width - len(b))


def parse_release(data: dict) -> Release | None:
    tag = str(data.get("tag_name") or "")
    if not parse_version(tag) or data.get("draft") or data.get("prerelease"):
        return None
    assets = {}
    for asset in data.get("assets") or []:
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if name and url:
            assets[str(name)] = str(url)
    return Release(version=tag.lstrip("v"),
                   url=str(data.get("html_url") or RELEASES_URL),
                   notes=str(data.get("body") or "").strip(),
                   assets=assets)


def install_kind() -> str:
    """Wie dieses Programm installiert ist: appimage, aur, portable, windows, source."""
    if os.environ.get("APPIMAGE"):
        return "appimage"
    if sys.platform.startswith("win"):
        return "portable" if paths.PORTABLE else "windows"
    if str(paths.SOURCE_DIR).startswith("/usr/lib/"):
        return "aur"
    return "source"


def pick_asset(release: Release, kind: str) -> tuple[str, str] | None:
    """(Dateiname, Download) passend zur Installationsart, sonst None."""
    def find(test):
        for name, url in release.assets.items():
            if test(name.lower()):
                return name, url
        return None

    if kind == "appimage":
        return find(lambda n: n.endswith(".appimage"))
    if kind == "portable":
        return find(lambda n: n.endswith("-portable.exe"))
    if kind == "windows":
        return find(lambda n: n.endswith(".exe") and "portable" not in n)
    return None


def fetch_latest(url: str = API_URL) -> Release | None:
    """Neuestes Release holen. None bei jedem Fehler — kein Netz ist normal."""
    request = urllib.request.Request(url, headers={
        "User-Agent": f"{paths.APP_NAME}/{paths.APP_VERSION}",
        "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            data = json.loads(answer.read(MAX_BYTES).decode("utf-8", "replace"))
    except Exception:
        return None
    return parse_release(data) if isinstance(data, dict) else None
