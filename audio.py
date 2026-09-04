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

"""Mikrofon-Capture ueber sounddevice mit Ringpuffer und Aufnahmefunktion."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import wave
from dataclasses import dataclass

import numpy as np
import sounddevice as sd

import i18n

SAMPLE_RATE = 48000
BLOCKSIZE = 1024
BUFFER_SECONDS = 4.0

DEFAULT_KEY = "__default__"


KIND_MIC = "mic"
KIND_VIRTUAL = "virtual"
KIND_MONITOR = "monitor"

KIND_TITLE_KEYS = {
    KIND_MIC: "group_mic",
    KIND_VIRTUAL: "group_virtual",
    KIND_MONITOR: "group_monitor",
}
KIND_ORDER = (KIND_MIC, KIND_VIRTUAL, KIND_MONITOR)

# Namensmuster fuer den Fall, dass kein pactl vorhanden ist — also unter
# Windows immer, unter Linux ohne PulseAudio/PipeWire.
MONITOR_HINTS = ("monitor", "stereo mix", "stereomix", "what u hear",
                 "wave out", "loopback")
VIRTUAL_HINTS = ("null", "virtual", "remap", "echo-cancel", "combined",
                 "dummy", "pipe", ".source", "sink", "wivrn", "obs",
                 "vb-audio", "cable", "voicemeeter")

# Unter Windows meldet PortAudio dasselbe Geraet ueber mehrere Host-APIs.
# WASAPI hat die geringste Latenz und die verlaesslichsten Namen.
HOSTAPI_ORDER = ("wasapi", "wdm-ks", "directsound", "mme")

# PortAudio-Geraete, ueber die sich beliebige PipeWire-Quellen erreichen lassen.
ROUTER_NAMES = ("pipewire", "pulse", "default")


@dataclass
class Source:
    """Eine auswaehlbare Eingangsquelle."""
    name: str                       # stabiler Schluessel fuers Merken
    label: str                      # Anzeigetext
    kind: str = KIND_MIC
    pa_index: int | None = None     # direkt oeffenbares PortAudio-Geraet
    pulse_source: str | None = None # sonst: ueber PULSE_SOURCE geroutet
    is_default: bool = False
    detail: str = ""                # technischer Name, fuer die Auswahl

    @property
    def available(self) -> bool:
        return self.pa_index is not None or self.pulse_source is not None


def _fallback_kind(name: str) -> str:
    low = name.lower()
    if any(h in low for h in MONITOR_HINTS):
        return KIND_MONITOR
    if any(h in low for h in VIRTUAL_HINTS):
        return KIND_VIRTUAL
    return KIND_MIC


# ------------------------------------------------------------ PipeWire

def _run(args: list[str]) -> str | None:
    try:
        env = {**os.environ, "LC_ALL": "C"}
        res = subprocess.run(args, capture_output=True, text=True,
                             timeout=3.0, env=env)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout if res.returncode == 0 else None


def parse_pactl_sources(text: str) -> list[dict]:
    """`pactl list sources` (LC_ALL=C) in Dictionaries zerlegen."""
    blocks: list[dict] = []
    current: dict | None = None
    in_props = False

    for line in text.splitlines():
        if line.startswith("Source #"):
            current = {"props": {}}
            blocks.append(current)
            in_props = False
            continue
        if current is None:
            continue

        stripped = line.strip()
        if stripped == "Properties:":
            in_props = True
            continue
        # Properties enden beim naechsten Feld auf einfacher Einrueckung.
        if in_props and not line.startswith("\t\t"):
            in_props = False

        if in_props:
            key, sep, value = stripped.partition(" = ")
            if sep:
                current["props"][key] = value.strip().strip('"')
            continue

        for field in ("Name", "Description", "Monitor of Sink"):
            prefix = field + ": "
            if stripped.startswith(prefix):
                current[field] = stripped[len(prefix):].strip()
                break
    return [b for b in blocks if b.get("Name")]


def _pipewire_sources() -> tuple[list[Source], dict[str, dict]] | None:
    text = _run(["pactl", "list", "sources"])
    if text is None:
        return None

    default_name = (_run(["pactl", "get-default-source"]) or "").strip()
    blocks = parse_pactl_sources(text)

    result: list[Source] = []
    for block in blocks:
        name = block["Name"]
        props = block["props"]
        label = (block.get("Description")
                 or props.get("device.description")
                 or name)

        monitor = block.get("Monitor of Sink", "n/a")
        if monitor and monitor != "n/a":
            kind = KIND_MONITOR
        elif "alsa.card" in props:
            kind = KIND_MIC
        else:
            kind = KIND_VIRTUAL

        result.append(Source(name=name, label=label, kind=kind, detail=name,
                             is_default=(name == default_name)))
    return result, {b["Name"]: b["props"] for b in blocks}


# ------------------------------------------------------------ PortAudio

def _portaudio_devices() -> tuple[list[tuple[int, str]], int | None]:
    """(Index, Name) aller Eingangsgeraete plus Index des Standardgeraets."""
    return ([(index, name) for index, name, _api in _portaudio_detailed()],
            _portaudio_default())


def _portaudio_default() -> int | None:
    try:
        return sd.default.device[0]
    except Exception:
        return None


def _portaudio_detailed() -> list[tuple[int, str, str]]:
    """(Index, Name, Host-API) aller Eingangsgeraete."""
    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
    except Exception:
        return []

    out = []
    for index, device in enumerate(devices):
        if device.get("max_input_channels", 0) < 1:
            continue
        api_index = device.get("hostapi")
        api = ""
        if isinstance(api_index, int) and 0 <= api_index < len(hostapis):
            api = hostapis[api_index].get("name", "")
        out.append((index, device.get("name", f"Gerät {index}"), api))
    return out


def _api_rank(api: str) -> int:
    """Sortiergewicht der Host-API; unbekannte landen hinten."""
    low = api.lower()
    for rank, needle in enumerate(HOSTAPI_ORDER):
        if needle in low:
            return rank
    return len(HOSTAPI_ORDER)


def _find_router(pa_devices: list[tuple[int, str]]) -> int | None:
    """PortAudio-Geraet, das an PipeWire/PulseAudio haengt."""
    for wanted in ROUTER_NAMES:
        for idx, name in pa_devices:
            if name.strip().lower() == wanted:
                return idx
    for idx, name in pa_devices:
        if any(w in name.lower() for w in ROUTER_NAMES):
            return idx
    return None


def _match_alsa(props: dict, pa_devices: list[tuple[int, str]]) -> int | None:
    """PipeWire-Quelle einem direkten ALSA-Geraet zuordnen."""
    card, device = props.get("alsa.card"), props.get("alsa.device")
    if card is not None and device is not None:
        needle = f"hw:{card},{device}"
        for idx, name in pa_devices:
            if needle in name:
                return idx
    card_name = props.get("alsa.card_name")
    if card_name:
        for idx, name in pa_devices:
            if name.startswith(card_name):
                return idx
    return None


# ------------------------------------------------------------ Sammeln

def enumerate_sources(remembered: str | None = None) -> list[Source]:
    """Alle Eingangsquellen mit lesbaren Namen.

    Bevorzugt PipeWire/PulseAudio, weil dort die Beschreibungen stehen.
    Ohne pactl bleibt die reine PortAudio-Liste.
    """
    pa_devices, pa_default = _portaudio_devices()
    pipewire = _pipewire_sources()

    if pipewire is None:
        # Kein PipeWire erreichbar: PortAudio-Namen direkt verwenden.
        # Dasselbe Geraet taucht unter Windows mehrfach auf, einmal je
        # Host-API. Wir behalten die beste und nennen sie im Anzeigetext,
        # damit die Auswahl nachvollziehbar bleibt.
        best: dict[str, tuple[int, int, str, str]] = {}
        for index, name, api in _portaudio_detailed():
            rank = _api_rank(api)
            previous = best.get(name)
            if previous is None or rank < previous[1]:
                best[name] = (index, rank, name, api)

        sources = []
        for index, _rank, name, api in best.values():
            label = f"{name}  [{api}]" if api else name
            sources.append(Source(name=f"{name}|{api}", label=label,
                                  kind=_fallback_kind(name), pa_index=index,
                                  detail=api,
                                  is_default=(index == pa_default)))
        sources.sort(key=lambda src: src.label.lower())
    else:
        pw_sources, raw = pipewire
        router = _find_router(pa_devices)
        sources = []
        for src in pw_sources:
            src.pa_index = _match_alsa(raw.get(src.name, {}), pa_devices)
            if src.pa_index is None and router is not None:
                src.pulse_source = src.name
            sources.append(src)

    disambiguate(sources)

    known = {s.name for s in sources}
    if remembered and remembered not in known and remembered != DEFAULT_KEY:
        sources.append(Source(name=remembered, label=remembered,
                              kind=_fallback_kind(remembered)))
    return sources


def disambiguate(sources: list[Source]) -> None:
    """Gleich benannte Quellen unterscheidbar machen.

    Eine Soundkarte mit zwei Eingaengen meldet beide unter derselben
    Beschreibung, und drei HDMI-Ausgaenge desselben Monitors ergeben drei
    gleich heissende Mitschnitt-Quellen. Sie zu verstecken waere falsch —
    es sind verschiedene Eingaenge. Stattdessen bekommt jede den Teil ihres
    technischen Namens angehaengt, in dem sie sich unterscheiden: aus zwei
    "USB Audio Device" wird eines mit "00" und eines mit "01".
    """
    groups: dict[str, list[Source]] = {}
    for source in sources:
        groups.setdefault(source.label.strip().lower(), []).append(source)

    for items in groups.values():
        if len(items) < 2:
            continue
        details = [item.detail or item.name for item in items]
        head = len(_common_prefix(details))
        tail = len(_common_prefix([text[::-1] for text in details]))
        for item, text in zip(items, details):
            middle = text[head:len(text) - tail].strip(" .-_:")
            item.label = f"{item.label}  ({middle})" if middle else item.label
        if len({item.label for item in items}) != len(items):
            # Der technische Name unterscheidet sich nicht — dann bleibt nur
            # das Durchnummerieren, damit die Auswahl eindeutig ist.
            for number, item in enumerate(items, start=1):
                item.label = f"{item.label}  ({number})"


def _common_prefix(values: list[str]) -> str:
    if not values:
        return ""
    first, rest = values[0], values[1:]
    for index, character in enumerate(first):
        if any(len(other) <= index or other[index] != character
               for other in rest):
            return first[:index]
    return first


def grouped_sources(remembered: str | None = None) -> list[tuple[str, list[Source]]]:
    """Quellen als [(Ueberschrift, [Source, ...]), ...] in fester Reihenfolge."""
    by_kind: dict[str, list[Source]] = {k: [] for k in KIND_ORDER}
    for src in enumerate_sources(remembered):
        by_kind.setdefault(src.kind, []).append(src)
    for items in by_kind.values():
        items.sort(key=lambda s: (not s.available, not s.is_default, s.label.lower()))
    return [(i18n.t(KIND_TITLE_KEYS[k]), by_kind[k])
            for k in KIND_ORDER if by_kind[k]]


class AudioEngine:
    """Nimmt kontinuierlich auf, haelt die letzten Sekunden vor und kann mitschneiden."""

    def __init__(self, samplerate: int = SAMPLE_RATE):
        self.samplerate = samplerate
        self._stream: sd.InputStream | None = None
        self._queue: queue.Queue[np.ndarray] = queue.Queue()

        self._buffer = np.zeros(0, dtype=np.float32)
        self._max_samples = int(BUFFER_SECONDS * samplerate)
        self.total_samples = 0          # absolut seit Start
        self.buffer_start = 0           # absoluter Index von _buffer[0]

        self._recording = False
        self._record_chunks: list[np.ndarray] = []
        self._lock = threading.Lock()

        self.last_error: str | None = None

    # -- Stream-Steuerung ------------------------------------------------

    def start(self, source: "Source | int | None" = None) -> bool:
        """Quelle oeffnen. Akzeptiert ein Source-Objekt oder direkt einen Index."""
        self.stop()
        self.last_error = None

        if isinstance(source, Source):
            device = source.pa_index
            pulse_source = source.pulse_source
            if device is None and pulse_source is not None:
                device = _find_router(_portaudio_devices()[0])
        else:
            device, pulse_source = source, None

        # Der ALSA-/Pulse-Client liest PULSE_SOURCE beim Verbinden aus.
        previous = os.environ.get("PULSE_SOURCE")
        if pulse_source is not None:
            os.environ["PULSE_SOURCE"] = pulse_source
        try:
            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                blocksize=BLOCKSIZE,
                device=device,
                channels=1,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            return True
        except Exception as exc:
            self.last_error = str(exc)
            self._stream = None
            return False
        finally:
            if pulse_source is not None:
                if previous is None:
                    os.environ.pop("PULSE_SOURCE", None)
                else:
                    os.environ["PULSE_SOURCE"] = previous

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    @property
    def running(self) -> bool:
        return self._stream is not None

    def _callback(self, indata, frames, time_info, status):
        # Laeuft im Audio-Thread: nur kopieren, nichts rechnen.
        self._queue.put(indata[:, 0].copy())

    # -- Puffer ----------------------------------------------------------

    def pump(self) -> int:
        """Neue Bloecke aus der Queue in den Ringpuffer holen. Gibt neue Sample-Anzahl zurueck."""
        chunks = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return 0

        new = np.concatenate(chunks)
        with self._lock:
            if self._recording:
                self._record_chunks.append(new.copy())

        self._buffer = np.concatenate([self._buffer, new])
        self.total_samples += new.size
        if self._buffer.size > self._max_samples:
            cut = self._buffer.size - self._max_samples
            self._buffer = self._buffer[cut:]
        self.buffer_start = self.total_samples - self._buffer.size
        return new.size

    def latest(self, seconds: float) -> np.ndarray:
        n = int(seconds * self.samplerate)
        if self._buffer.size == 0:
            return np.zeros(0, dtype=np.float32)
        return self._buffer[-n:].copy()

    def slice_abs(self, start_abs: int, length: int) -> np.ndarray | None:
        """Fenster anhand absoluter Sample-Indizes, oder None wenn nicht mehr im Puffer."""
        offset = start_abs - self.buffer_start
        if offset < 0 or offset + length > self._buffer.size:
            return None
        return self._buffer[offset:offset + length]

    # -- Aufnahme --------------------------------------------------------

    def start_recording(self) -> None:
        with self._lock:
            self._record_chunks = []
            self._recording = True

    def stop_recording(self) -> np.ndarray:
        with self._lock:
            self._recording = False
            chunks = self._record_chunks
            self._record_chunks = []
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks)

    @property
    def is_recording(self) -> bool:
        return self._recording

    def recorded_seconds(self) -> float:
        with self._lock:
            n = sum(c.size for c in self._record_chunks)
        return n / self.samplerate


def write_wav(path, samples: np.ndarray, samplerate: int) -> None:
    data = np.clip(samples, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(pcm.tobytes())


def read_wav(path) -> tuple[np.ndarray, int]:
    """Mono-Samples als float32 in [-1, 1] plus Abtastrate."""
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def envelope(data: np.ndarray, points: int = 2000):
    """Min/Max-Huellkurve fuer die Wellenformdarstellung."""
    if data.size == 0:
        return np.zeros(0), np.zeros(0)
    step = max(1, data.size // points)
    count = data.size // step
    block = data[:count * step].reshape(count, step)
    lows, highs = block.min(axis=1), block.max(axis=1)
    xs = np.repeat(np.arange(count, dtype=np.float64) * step, 2)
    ys = np.empty(count * 2, dtype=np.float64)
    ys[0::2], ys[1::2] = lows, highs
    return xs, ys
