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

"""Akustische Analyse: Grundfrequenz (F0) und Formanten (F1/F2) via Praat/parselmouth.

Alle Schwellwerte und Grenzen kommen zur Laufzeit aus settings.CFG und
lassen sich im Programm über den Einstellungsdialog ändern.
"""

from __future__ import annotations

import re

import numpy as np
import parselmouth
from parselmouth.praat import call

import debuglog
import i18n
from settings import CFG


def rms(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))


def _to_sound(samples: np.ndarray, sr: int) -> parselmouth.Sound:
    return parselmouth.Sound(np.ascontiguousarray(samples, dtype=np.float64),
                             sampling_frequency=float(sr))


def _pitch_frames(snd: parselmouth.Sound, time_step: float = 0.01) -> np.ndarray:
    """Alle F0-Frames, 0 wo unstimmhaft.

    voicing_threshold ist der entscheidende Regler: Praats Autokorrelation
    findet in reinem Rauschen sonst Scheinperioden, die sich fast immer
    direkt auf der Untergrenze sammeln.
    """
    pitch = snd.to_pitch_ac(time_step=time_step,
                            pitch_floor=CFG.pitch_floor,
                            pitch_ceiling=CFG.pitch_ceiling,
                            voicing_threshold=CFG.voicing_threshold)
    return np.asarray(pitch.selected_array["frequency"], dtype=np.float64)


def _clean_voiced(freq: np.ndarray) -> np.ndarray:
    """Stimmhafte Werte ohne die typischen Artefakte an der Untergrenze."""
    voiced = freq[freq > 0.0]
    if voiced.size == 0:
        return voiced
    return voiced[voiced > CFG.pitch_floor * 1.10]


def _pitch_track(snd: parselmouth.Sound, time_step: float = 0.01) -> np.ndarray:
    return _clean_voiced(_pitch_frames(snd, time_step))


def _formant_medians(snd: parselmouth.Sound, time_step: float = 0.01,
                     with_f3: bool = False):
    """Median von F1/F2 (optional F3) ueber das Fenster."""
    formant = snd.to_formant_burg(time_step=time_step,
                                  max_number_of_formants=5,
                                  maximum_formant=CFG.formant_ceiling,
                                  window_length=0.025,
                                  pre_emphasis_from=50.0)
    f1_vals, f2_vals, f3_vals = [], [], []
    for i in range(1, formant.get_number_of_frames() + 1):
        t = formant.get_time_from_frame_number(i)
        a = formant.get_value_at_time(1, t)
        b = formant.get_value_at_time(2, t)
        if a is None or b is None or np.isnan(a) or np.isnan(b):
            continue
        # Unplausible LPC-Artefakte rauswerfen.
        if not (150.0 < a < 1300.0) or not (600.0 < b < 3600.0) or b <= a:
            continue
        f1_vals.append(float(a))
        f2_vals.append(float(b))
        c = formant.get_value_at_time(3, t)
        f3_vals.append(float(c) if c is not None and not np.isnan(c)
                       and b < c < 4200.0 else np.nan)
    if len(f1_vals) < 3:
        return (None, None, None) if with_f3 else (None, None)
    f1, f2 = float(np.median(f1_vals)), float(np.median(f2_vals))
    if not with_f3:
        return f1, f2
    arr = np.asarray(f3_vals, dtype=float)
    arr = arr[~np.isnan(arr)]
    return f1, f2, (float(np.median(arr)) if arr.size >= 3 else None)


def _min_window(sr: int) -> int:
    """Praats Autokorrelation braucht mindestens 3 Perioden der Untergrenze."""
    return int(np.ceil(3.0 / CFG.pitch_floor * sr)) + 1


def analyse_window(samples: np.ndarray, sr: int) -> dict:
    """Schnelle Analyse eines kurzen Live-Fensters (~0.3-0.5 s)."""
    out = {"rms": 0.0, "f0": None, "f1": None, "f2": None, "h1_h2": None,
           "voiced": False}
    if samples.size < _min_window(sr):
        return out

    level = rms(samples)
    out["rms"] = level
    if level < CFG.silence_rms:
        return out

    try:
        snd = _to_sound(samples, sr)
        pitch = snd.to_pitch_ac(time_step=0.01,
                                pitch_floor=CFG.pitch_floor,
                                pitch_ceiling=CFG.pitch_ceiling,
                                voicing_threshold=CFG.voicing_threshold)
        voiced = _clean_voiced(
            np.asarray(pitch.selected_array["frequency"], dtype=np.float64))
        if voiced.size >= 3:
            out["f0"] = float(np.median(voiced))
            out["voiced"] = True
            # Formanten nur auf stimmhaftem Material auswerten.
            out["f1"], out["f2"] = _formant_medians(snd)
            # Grober Schritt: live zaehlt Tempo mehr als die letzte Stelle.
            _, _, out["h1_h2"] = _h1_h2(np.asarray(samples, dtype=np.float64),
                                        sr, pitch, step=3)
    except Exception as exc:
        debuglog.record_exception("analysis.analyse_window", exc)
    return out


def analyse_recording(samples: np.ndarray, sr: int) -> dict:
    """Auswertung einer kompletten Aufnahme fuer die Session-Statistik."""
    out = {
        "duration": float(samples.size) / sr if sr else 0.0,
        "f0_median": None, "f0_p10": None, "f0_p90": None,
        "f1_median": None, "f2_median": None,
        "f3_median": None, "f0_sd_st": None, "f0_range_st": None, "hnr": None,
        "jitter_local": None, "shimmer_local": None,
        "h1_db": None, "h2_db": None, "h1_h2": None,
        "voice_breaks_pct": None, "voice_break_count": None,
        "voiced_ratio": 0.0, "peak_db": None, "quality": "zu_kurz",
        "pitch_floor": CFG.pitch_floor,
        "pitch_ceiling": CFG.pitch_ceiling,
        "formant_ceiling": CFG.formant_ceiling,
        "voicing_threshold": CFG.voicing_threshold,
    }
    if samples.size < max(int(0.3 * sr), _min_window(sr)):
        return out

    data = np.asarray(samples, dtype=np.float64)
    frame = max(1, int(0.01 * sr))
    count = data.size // frame
    if count >= 3:
        energy = np.sqrt(np.mean(data[:count * frame].reshape(count, frame) ** 2, axis=1))
        out["peak_db"] = float(20.0 * np.log10(np.percentile(energy, 95) + 1e-12))

    snd = _to_sound(samples, sr)
    freq = _pitch_frames(snd, time_step=0.01)
    voiced = _clean_voiced(freq)
    if freq.size:
        out["voiced_ratio"] = float(voiced.size) / float(freq.size)

    # Zu wenig stimmhaftes Material: lieber gar keine Zahl als eine falsche.
    if out["voiced_ratio"] < CFG.min_voiced_ratio or voiced.size < 5:
        out["quality"] = "kein_signal"
        return out

    out["quality"] = "ok"
    out["f0_median"] = float(np.median(voiced))
    out["f0_p10"] = float(np.percentile(voiced, 10))
    out["f0_p90"] = float(np.percentile(voiced, 90))

    # Melodiefuehrung in Halbtoenen, unabhaengig von der absoluten Lage.
    semitones = 12.0 * np.log2(voiced / out["f0_median"])
    out["f0_sd_st"] = float(np.std(semitones))
    out["f0_range_st"] = float(12.0 * np.log2(out["f0_p90"] / out["f0_p10"]))

    try:
        out["f1_median"], out["f2_median"], out["f3_median"] = _formant_medians(
            snd, time_step=0.02, with_f3=True)
    except Exception as exc:
        debuglog.record_exception("analysis.formants", exc)

    try:
        harmonicity = call(snd, "To Harmonicity (cc)", 0.01, 75.0, 0.1, 1.0)
        value = call(harmonicity, "Get mean", 0, 0)
        if value is not None and not np.isnan(value):
            out["hnr"] = float(value)
    except Exception as exc:
        debuglog.record_exception("analysis.hnr", exc)

    out.update(_perturbation(snd))

    try:
        pitch_obj = snd.to_pitch_ac(time_step=0.01,
                                    pitch_floor=CFG.pitch_floor,
                                    pitch_ceiling=CFG.pitch_ceiling,
                                    voicing_threshold=CFG.voicing_threshold)
        out["h1_db"], out["h2_db"], out["h1_h2"] = _h1_h2(data, sr, pitch_obj)
    except Exception as exc:
        debuglog.record_exception("analysis.h1h2", exc)
    return out


def zone_label(f0: float | None) -> str:
    if f0 is None:
        return "--"
    if f0 < CFG.zone_low:
        return i18n.t("zone_low")
    if f0 < CFG.zone_high:
        return i18n.t("zone_mid")
    return i18n.t("zone_high")


def _perturbation(snd: parselmouth.Sound) -> dict:
    """Jitter, Shimmer und Stimmabbrueche ueber Praats Voice Report."""
    out = {"jitter_local": None, "shimmer_local": None,
           "voice_breaks_pct": None, "voice_break_count": None}
    try:
        pulses = call(snd, "To PointProcess (periodic, cc)",
                      CFG.pitch_floor, CFG.pitch_ceiling)
        value = call(pulses, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        if value is not None and not np.isnan(value):
            out["jitter_local"] = float(value) * 100.0
        value = call([snd, pulses], "Get shimmer (local)",
                     0, 0, 0.0001, 0.02, 1.3, 1.6)
        if value is not None and not np.isnan(value):
            out["shimmer_local"] = float(value) * 100.0
    except Exception as exc:
        debuglog.record_exception("analysis.perturbation", exc)

    try:
        pitch = snd.to_pitch_ac(time_step=0.01,
                                pitch_floor=CFG.pitch_floor,
                                pitch_ceiling=CFG.pitch_ceiling,
                                voicing_threshold=CFG.voicing_threshold)
        pulses = call(snd, "To PointProcess (periodic, cc)",
                      CFG.pitch_floor, CFG.pitch_ceiling)
        report = call([snd, pitch, pulses], "Voice report", 0, 0,
                      CFG.pitch_floor, CFG.pitch_ceiling, 1.3, 1.6, 0.03, 0.45)
        # Praat haengt je nach Fall Zusaetze an, etwa
        # "Degree of voice breaks: 0   (0 seconds / 0 seconds)".
        # Deshalb die erste Zahl herausziehen statt am Doppelpunkt zu trennen.
        def first_number(text: str):
            match = re.search(r"[-+]?\d*\.?\d+", text.split(":", 1)[1])
            return float(match.group()) if match else None

        for line in report.splitlines():
            text = line.strip()
            if text.startswith("Number of voice breaks:"):
                value = first_number(text)
                if value is not None:
                    out["voice_break_count"] = int(value)
            elif text.startswith("Degree of voice breaks:"):
                value = first_number(text)
                if value is not None:
                    out["voice_breaks_pct"] = value
    except Exception as exc:
        debuglog.record_exception("analysis.voice_report", exc)
    return out


def _h1_h2(data: np.ndarray, sr: int, pitch, step: int = 3) -> tuple:
    """Pegel der ersten beiden Harmonischen und ihr Abstand, jeweils in dB.

    H1 und H2 sind auf Vollaussteuerung bezogen und haengen damit am
    Aufnahmepegel — vergleichbar sind sie nur bei gleicher Mikrofoneinstellung.
    Der Abstand H1-H2 ist pegelunabhaengig: gross heisst leichte, behauchte
    Stimmgebung, klein schwere, gepresste. Unkorrigiert, also von den
    Formanten mitbeeinflusst.
    """
    h1_values, h2_values, values = [], [], []
    for i in range(1, pitch.get_number_of_frames() + 1, step):
        f0 = pitch.get_value_in_frame(i)
        if f0 is None or np.isnan(f0) or f0 <= 0.0:
            continue
        window_len = int(4.0 * sr / f0)
        center = int(pitch.get_time_from_frame_number(i) * sr)
        start = center - window_len // 2
        if start < 0 or start + window_len > data.size:
            continue

        segment = data[start:start + window_len] * np.hanning(window_len)
        nfft = 1 << int(np.ceil(np.log2(max(window_len * 4, 512))))
        spectrum = np.abs(np.fft.rfft(segment, nfft))
        freqs = np.fft.rfftfreq(nfft, 1.0 / sr)

        scale = window_len / 2.0

        def peak_db(target: float):
            band = (freqs >= target * 0.85) & (freqs <= target * 1.15)
            if not band.any():
                return None
            return 20.0 * np.log10(spectrum[band].max() / scale + 1e-12)

        h1, h2 = peak_db(f0), peak_db(2.0 * f0)
        if h1 is None or h2 is None:
            continue
        h1_values.append(h1)
        h2_values.append(h2)
        values.append(h1 - h2)

    if len(values) < 5:
        return None, None, None
    return (float(np.median(h1_values)), float(np.median(h2_values)),
            float(np.median(values)))


def stable_span(samples: np.ndarray, sr: int,
                 target: float = 2.0) -> tuple[int, int]:
    """Ausschnitt eines gehaltenen Lautes ohne Ein- und Ausschwingen.

    Sucht das Fenster der Laenge `target`, in dem Pegel und Tonhoehe am
    ruhigsten sind. Gibt Sample-Indizes zurueck; im Zweifel die Mitte.
    """
    total = samples.size
    want = int(target * sr)
    if total <= want:
        return 0, total

    data = np.asarray(samples, dtype=np.float64)
    frame = max(1, int(0.02 * sr))
    count = total // frame
    energy = np.sqrt(np.mean(data[:count * frame].reshape(count, frame) ** 2,
                             axis=1))

    try:
        snd = _to_sound(samples, sr)
        freq = _pitch_frames(snd, time_step=0.02)
    except Exception as exc:
        debuglog.record_exception("analysis.stable_span", exc)
        freq = np.zeros(0)

    span = max(1, want // frame)
    best_score, best_start = None, (count - span) // 2
    loud = np.percentile(energy, 90) if energy.size else 0.0

    for start in range(0, count - span + 1, max(1, span // 8)):
        window = energy[start:start + span]
        if window.size == 0 or loud <= 0.0:
            continue
        # Laut und gleichmaessig im Pegel ...
        score = float(np.mean(window) / loud) - float(np.std(window) / loud)
        # ... und moeglichst durchgehend stimmhaft mit ruhiger Tonhoehe.
        if freq.size:
            piece = freq[start:start + span]
            voiced = piece[piece > 0.0]
            if voiced.size < max(3, piece.size // 3):
                continue
            score += float(voiced.size) / float(max(1, piece.size))
            score -= float(np.std(voiced) / max(np.median(voiced), 1.0)) * 2.0
        if best_score is None or score > best_score:
            best_score, best_start = score, start

    begin = best_start * frame
    return begin, min(total, begin + want)


def analyse_file(path) -> dict:
    """Eine gespeicherte WAV-Datei neu auswerten."""
    from audio import read_wav

    data, sr = read_wav(path)
    return analyse_recording(data.astype(np.float64), sr)
