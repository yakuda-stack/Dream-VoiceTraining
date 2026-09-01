"""Geraeteerkennung, WAV-Ein-/Ausgabe und Ringpuffer."""

import queue
import threading

import numpy as np
import pytest

import audio

PACTL = """Source #48
\tName: alsa_input.usb-Foo-00.analog-stereo
\tDescription: USB Advanced Audio Device Analog Stereo
\tMonitor of Sink: n/a
\tProperties:
\t\talsa.card = "1"
\t\talsa.card_name = "USB Advanced Audio Device"
\t\talsa.device = "0"

Source #52
\tName: wivrn.source
\tDescription: wivrn.source
\tMonitor of Sink: n/a
\tProperties:
\t\tmedia.class = "Audio/Source"

Source #60
\tName: alsa_output.usb-Foo-00.analog-stereo.monitor
\tDescription: Monitor of USB Advanced Audio Device
\tMonitor of Sink: alsa_output.usb-Foo-00.analog-stereo
\tProperties:
\t\tdevice.class = "monitor"
"""

PA_DEVICES = [
    {"name": "USB Advanced Audio Device: USB Audio (hw:1,0)",
     "max_input_channels": 2, "hostapi": 0},
    {"name": "pipewire", "max_input_channels": 64, "hostapi": 0},
]


@pytest.fixture
def pipewire(monkeypatch):
    monkeypatch.setattr(audio, "_run",
                        lambda args: PACTL if "list" in args
                        else "alsa_input.usb-Foo-00.analog-stereo\n")
    monkeypatch.setattr(audio.sd, "query_devices", lambda: PA_DEVICES, raising=False)
    monkeypatch.setattr(audio.sd, "query_hostapis", lambda: [{"name": "ALSA"}],
                        raising=False)


def test_pactl_wird_zerlegt():
    blocks = audio.parse_pactl_sources(PACTL)
    assert [b["Name"] for b in blocks] == [
        "alsa_input.usb-Foo-00.analog-stereo", "wivrn.source",
        "alsa_output.usb-Foo-00.analog-stereo.monitor"]
    assert blocks[0]["props"]["alsa.card"] == "1"
    assert blocks[0]["Description"].startswith("USB Advanced")


def test_quellen_werden_gruppiert_und_benannt(pipewire):
    groups = dict(audio.grouped_sources())
    labels = {title: [s.label for s in items] for title, items in groups.items()}
    flat = [label for items in labels.values() for label in items]
    assert "USB Advanced Audio Device Analog Stereo" in flat
    assert len(groups) == 3


def test_hardware_wird_dem_alsa_geraet_zugeordnet(pipewire):
    by_name = {s.name: s for s in audio.enumerate_sources()}
    hardware = by_name["alsa_input.usb-Foo-00.analog-stereo"]
    assert hardware.pa_index == 0
    assert hardware.is_default is True


def test_virtuelle_quelle_wird_geroutet(pipewire):
    by_name = {s.name: s for s in audio.enumerate_sources()}
    virtual = by_name["wivrn.source"]
    assert virtual.pa_index is None
    assert virtual.pulse_source == "wivrn.source"
    assert virtual.available is True


def test_fehlendes_geraet_bleibt_sichtbar(pipewire):
    sources = audio.enumerate_sources(remembered="weg.source")
    missing = [s for s in sources if s.name == "weg.source"]
    assert len(missing) == 1
    assert missing[0].available is False


def test_einordnung_ohne_pipewire(monkeypatch):
    monkeypatch.setattr(audio, "_run", lambda args: None)
    assert audio._fallback_kind("Monitor of Speakers") == audio.KIND_MONITOR
    assert audio._fallback_kind("wivrn.source") == audio.KIND_VIRTUAL
    assert audio._fallback_kind("Blue Yeti Analog") == audio.KIND_MIC


def test_wav_hin_und_zurueck(tmp_path):
    sr = 48000
    signal = (np.sin(2 * np.pi * 220 * np.arange(sr) / sr) * 0.5).astype(np.float32)
    path = tmp_path / "t.wav"
    audio.write_wav(path, signal, sr)
    data, rate = audio.read_wav(path)
    assert rate == sr and data.size == sr
    assert np.max(np.abs(data - signal)) < 1e-3


def test_huellkurve():
    data = np.sin(np.linspace(0, 100, 50000)).astype(np.float32)
    xs, ys = audio.envelope(data, 500)
    assert xs.size == ys.size == 1000
    assert ys.min() < -0.9 and ys.max() > 0.9


def test_ringpuffer_haelt_nur_die_letzten_sekunden():
    engine = audio.AudioEngine()
    for i in range(400):
        engine._queue.put(np.full(1024, i / 400.0, dtype=np.float32))
    engine.pump()
    assert engine._buffer.size == engine._max_samples
    assert engine.buffer_start == engine.total_samples - engine._buffer.size


def test_absolute_ausschnitte():
    engine = audio.AudioEngine()
    for _ in range(50):
        engine._queue.put(np.zeros(1024, dtype=np.float32))
    engine.pump()
    assert engine.slice_abs(engine.total_samples - 2048, 2048) is not None
    assert engine.slice_abs(engine.total_samples, 2048) is None
    assert engine.slice_abs(-5000, 2048) is None


def test_aufnahme_sammelt_bloecke():
    engine = audio.AudioEngine()
    engine.start_recording()
    for _ in range(20):
        engine._queue.put(np.full(1024, 0.1, dtype=np.float32))
    engine.pump()
    recorded = engine.stop_recording()
    assert recorded.size == 20 * 1024
    assert engine.is_recording is False


WINDOWS_DEVICES = [
    {"name": "Mikrofon (USB Audio Device)", "max_input_channels": 2, "hostapi": 0},
    {"name": "Mikrofon (USB Audio Device)", "max_input_channels": 2, "hostapi": 1},
    {"name": "Mikrofon (USB Audio Device)", "max_input_channels": 2, "hostapi": 2},
    {"name": "Stereomix (Realtek Audio)", "max_input_channels": 2, "hostapi": 0},
    {"name": "CABLE Output (VB-Audio Virtual Cable)", "max_input_channels": 2,
     "hostapi": 2},
]
WINDOWS_APIS = [{"name": "MME"}, {"name": "Windows DirectSound"},
                {"name": "Windows WASAPI"}]


@pytest.fixture
def windows_audio(monkeypatch):
    """Windows nachstellen: kein pactl, mehrere Host-APIs je Gerät."""
    monkeypatch.setattr(audio, "_run", lambda args: None)
    monkeypatch.setattr(audio.sd, "query_devices", lambda: WINDOWS_DEVICES,
                        raising=False)
    monkeypatch.setattr(audio.sd, "query_hostapis", lambda: WINDOWS_APIS,
                        raising=False)


def test_windows_geraete_werden_entdoppelt(windows_audio):
    sources = audio.enumerate_sources()
    names = [s.label for s in sources]
    mikrofone = [n for n in names if n.startswith("Mikrofon")]
    assert len(mikrofone) == 1, names


def test_windows_bevorzugt_wasapi(windows_audio):
    by_label = {s.label: s for s in audio.enumerate_sources()}
    mikrofon = next(s for label, s in by_label.items()
                    if label.startswith("Mikrofon"))
    assert "WASAPI" in mikrofon.label
    assert mikrofon.pa_index == 2          # der WASAPI-Eintrag


def test_windows_einordnung(windows_audio):
    kinds = {s.label.split("  [")[0]: s.kind for s in audio.enumerate_sources()}
    assert kinds["Stereomix (Realtek Audio)"] == audio.KIND_MONITOR
    assert kinds["CABLE Output (VB-Audio Virtual Cable)"] == audio.KIND_VIRTUAL
    assert kinds["Mikrofon (USB Audio Device)"] == audio.KIND_MIC


def test_ohne_pactl_kein_pulse_routing(windows_audio):
    """PULSE_SOURCE gibt es unter Windows nicht — es darf nie gesetzt werden."""
    for source in audio.enumerate_sources():
        assert source.pulse_source is None
        assert source.pa_index is not None
