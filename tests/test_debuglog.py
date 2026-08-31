"""Fehlerprotokoll."""

import debuglog


def test_ausnahme_wird_mit_traceback_festgehalten():
    debuglog.clear()
    try:
        raise ValueError("probe")
    except ValueError as exc:
        debuglog.record_exception("test.source", exc)

    assert debuglog.count() == 1
    stamp, level, source, message, tb = debuglog.RECORDS[0]
    assert level == "ERROR" and source == "test.source"
    assert "probe" in message and "ValueError" in tb


def test_analyse_fehler_landen_im_protokoll(monkeypatch, vowel, sr):
    """Ein kaputter Praat-Aufruf darf die Auswertung nicht stillschweigend leeren."""
    import analysis
    debuglog.clear()

    def boom(*args, **kwargs):
        raise RuntimeError("praat kaputt")

    monkeypatch.setattr(analysis, "_formant_medians", boom)
    result = analysis.analyse_recording(vowel(f0=130.0), sr)

    assert result["f0_median"] is not None      # Rest wird trotzdem berechnet
    assert result["f1_median"] is None
    assert any("formants" in r[2] for r in debuglog.RECORDS)


def test_umgebungsangaben_sind_vollstaendig():
    text = "\n".join(debuglog.environment())
    for expected in ("Python", "Platform", "Version", "Config", "Data"):
        assert expected in text


def test_bericht_bleibt_lesbar_wenn_nichts_passiert_ist():
    debuglog.clear()
    text = debuglog.as_text()
    assert "0 record(s)" in text and "nothing recorded" in text


def test_ringpuffer_begrenzt():
    debuglog.clear()
    for i in range(debuglog.MAX_RECORDS + 50):
        debuglog.record_note("test", f"Meldung {i}")
    assert debuglog.count() == debuglog.MAX_RECORDS
