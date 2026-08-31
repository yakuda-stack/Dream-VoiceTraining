"""Analysekern: erkennt er Stimme, und weist er Rauschen ab?"""

import numpy as np
import pytest

import analysis
import settings


def test_erkennt_grundfrequenz(vowel, sr):
    for target in (100.0, 150.0, 220.0):
        result = analysis.analyse_window(vowel(f0=target), sr)
        assert result["voiced"] is True
        assert result["f0"] == pytest.approx(target, rel=0.03)


def test_formanten_in_richtiger_reihenfolge(vowel, sr):
    result = analysis.analyse_window(vowel(f0=110.0), sr)
    assert result["f1"] is not None and result["f2"] is not None
    assert result["f1"] < result["f2"]


def test_stille_ergibt_keine_werte(sr):
    result = analysis.analyse_window(np.zeros(int(0.5 * sr)), sr)
    assert result["voiced"] is False
    assert result["f0"] is None and result["f1"] is None


def test_rauschen_wird_abgewiesen(noise, sr):
    """Der Regressionstest zum Fehler, bei dem Rauschen 64 Hz ergab."""
    result = analysis.analyse_recording(noise(seconds=4.0), sr)
    assert result["quality"] == "kein_signal"
    assert result["f0_median"] is None
    assert result["voiced_ratio"] < settings.CFG.min_voiced_ratio


def test_werte_an_der_untergrenze_fliegen_raus():
    settings.apply(settings.Settings(pitch_floor=60.0))
    freq = np.array([0.0, 61.0, 63.0, 120.0, 130.0, 140.0])
    cleaned = analysis._clean_voiced(freq)
    assert cleaned.min() >= 60.0 * 1.10
    assert set(cleaned) == {120.0, 130.0, 140.0}


def test_vollstaendige_auswertung(vowel, sr):
    result = analysis.analyse_recording(vowel(f0=130.0, seconds=3.0), sr)
    assert result["quality"] == "ok"
    assert result["f0_median"] == pytest.approx(130.0, rel=0.03)
    for key in ("f0_p10", "f0_p90", "f0_sd_st", "f0_range_st", "peak_db"):
        assert result[key] is not None, key
    assert result["voiced_ratio"] > 0.5


def test_kennwerte_der_stimmqualitaet(vowel, sr):
    result = analysis.analyse_recording(vowel(f0=120.0, seconds=3.0), sr)
    for key in ("hnr", "jitter_local", "shimmer_local", "h1_db", "h2_db", "h1_h2"):
        assert result[key] is not None, key
    assert result["h1_h2"] == pytest.approx(result["h1_db"] - result["h2_db"], abs=1.5)


def test_zu_kurz(sr):
    result = analysis.analyse_recording(np.zeros(100), sr)
    assert result["quality"] == "zu_kurz"


def test_grenzen_werden_mitgeschrieben(vowel, sr):
    settings.apply(settings.Settings(pitch_floor=70.0, pitch_ceiling=400.0))
    result = analysis.analyse_recording(vowel(f0=130.0), sr)
    assert result["pitch_floor"] == 70.0
    assert result["pitch_ceiling"] == 400.0


def test_zonen_beschriftung():
    settings.apply(settings.Settings(zone_low=145.0, zone_high=185.0))
    assert analysis.zone_label(None) == "--"
    assert analysis.zone_label(120.0) != analysis.zone_label(165.0)
    assert analysis.zone_label(165.0) != analysis.zone_label(220.0)


def test_datei_auswertung(tmp_path, vowel, sr):
    import audio
    path = tmp_path / "probe.wav"
    audio.write_wav(path, vowel(f0=140.0, seconds=2.0).astype(np.float32), sr)
    result = analysis.analyse_file(path)
    assert result["f0_median"] == pytest.approx(140.0, rel=0.03)


def test_voice_report_mit_zusaetzen(monkeypatch, vowel, sr):
    """Regression: Praat hängt an manche Zeilen Klammerzusätze an."""
    import debuglog
    from parselmouth.praat import call as real_call

    REPORT = """-- Voice report --
Number of voice breaks: 0   (0 seconds / 0 seconds)
Degree of voice breaks: 0   (0 seconds / 0 seconds)
"""

    def fake_call(target, command, *args):
        if command == "Voice report":
            return REPORT
        return real_call(target, command, *args)

    monkeypatch.setattr(analysis, "call", fake_call)
    debuglog.clear()
    result = analysis.analyse_recording(vowel(f0=130.0, seconds=2.0), sr)

    assert result["voice_break_count"] == 0
    assert result["voice_breaks_pct"] == 0.0
    assert not [r for r in debuglog.RECORDS if "voice_report" in r[2]]


def test_voice_report_prozentform(monkeypatch, vowel, sr):
    from parselmouth.praat import call as real_call

    REPORT = ("Number of voice breaks: 3\n"
              "Degree of voice breaks: 12.5%   (0.4 seconds / 3.2 seconds)\n")

    def fake_call(target, command, *args):
        return REPORT if command == "Voice report" else real_call(target, command, *args)

    monkeypatch.setattr(analysis, "call", fake_call)
    result = analysis.analyse_recording(vowel(f0=130.0, seconds=2.0), sr)
    assert result["voice_break_count"] == 3
    assert result["voice_breaks_pct"] == 12.5
