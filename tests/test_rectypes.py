"""Aufnahmetypen, stabile Mitte und eigenes Ziel."""

import numpy as np
import pytest

import analysis
import i18n
import rectypes
import settings
import targets


def test_alle_typen_sind_uebersetzt():
    for kind in rectypes.TYPES:
        for lang in ("en", "de"):
            i18n.set_language(lang)
            assert kind.label.strip() and kind.hint.strip(), kind.key
    i18n.set_language("en")


def test_gefuehrter_ablauf_nur_gehaltene_laute():
    for key in rectypes.GUIDED:
        kind = rectypes.get(key)
        assert kind.sustained is True, key
        assert kind.seconds and kind.seconds >= 3.0, key


def test_unbekannter_typ_faellt_zurueck():
    assert rectypes.get(None).key == rectypes.DEFAULT
    assert rectypes.get("gibt-es-nicht").key == rectypes.DEFAULT


def test_stabile_mitte_meidet_rand(sr, vowel):
    """Ein- und Ausschwingen soll nicht im Ausschnitt landen."""
    body = vowel(f0=130.0, seconds=3.0)
    silence = np.zeros(int(0.7 * sr))
    signal = np.concatenate([silence, body, silence])

    begin, end = analysis.stable_span(signal, sr, 2.0)
    assert (end - begin) == pytest.approx(2.0 * sr, rel=0.02)
    # Der Ausschnitt liegt im lauten Teil, nicht in der Stille.
    assert np.sqrt(np.mean(signal[begin:end] ** 2)) > 0.5 * np.sqrt(
        np.mean(body ** 2))


def test_stabile_mitte_bei_kurzem_signal(sr, vowel):
    short = vowel(f0=130.0, seconds=1.0)
    begin, end = analysis.stable_span(short, sr, 2.0)
    assert (begin, end) == (0, short.size)


def test_eigenes_ziel_aus_einer_aufnahme():
    source = {"f0_median": 180.0, "f2_median": 1800.0, "h1_h2": 6.0,
              "hnr": 15.0}
    ranges = targets.build_custom(source)
    assert set(ranges) <= set(targets.CUSTOM_KEYS)
    low, high = ranges["f0_median"]
    assert low < 180.0 < high
    assert "hnr" not in ranges          # Qualitaet ist kein Ziel


def test_eigenes_ziel_nie_null_breit():
    ranges = targets.build_custom({"f0_sd_st": 0.0})
    low, high = ranges["f0_sd_st"]
    assert high > low


def test_eigenes_ziel_wirkt_in_der_bewertung():
    settings.save_user_profile("Testziel", targets.build_custom({"f0_median": 180.0}))
    key = targets.USER_PREFIX + "Testziel"
    i18n.set_language("en")

    assert key in targets.profile_keys()
    assert targets.profile_label(key) == "Testziel"
    assert targets.verdict(180.0, targets.range_for("f0_median", key)) == \
        i18n.t("verdict_within")
    assert targets.verdict(120.0, targets.range_for("f0_median", key)) == \
        i18n.t("verdict_below")
    # Ohne hinterlegten Wert gibt es keinen Bereich.
    assert targets.range_for("f3_median", key) is None


def test_eingebaute_profile_bleiben_unangetastet():
    before = dict(targets.PROFILES["feminin"])
    settings.save_user_profile("Kopie", targets.profile_ranges("feminin"))
    settings.save_user_profile("Kopie", {"f0_median": [1.0, 2.0]})
    assert targets.PROFILES["feminin"] == before
    assert targets.range_for("f0_median", "feminin") == (180.0, 250.0)


def test_profile_werden_sortiert_und_geloescht():
    settings.save_user_profile("Zebra", {"f0_median": [100.0, 200.0]})
    settings.save_user_profile("Alpha", {"f0_median": [100.0, 200.0]})
    keys = targets.profile_keys()
    assert keys[:4] == targets.BUILTIN_ORDER
    assert keys[4:] == [targets.USER_PREFIX + "Alpha",
                        targets.USER_PREFIX + "Zebra"]

    assert settings.delete_user_profile("Zebra") is True
    assert settings.delete_user_profile("Zebra") is False
    assert targets.USER_PREFIX + "Zebra" not in targets.profile_keys()


def test_leeres_ziel_ergibt_nichts():
    assert targets.build_custom({"f0_median": None, "quality": "kein_signal"}) == {}


def test_eingebautes_profil_laesst_sich_anpassen_und_zuruecksetzen():
    """Der Literaturwert bleibt im Code, die Anpassung liegt daneben."""
    assert targets.range_for("f0_median", "feminin") == (180.0, 250.0)

    settings.save_builtin_override("feminin", {"f0_median": [170.0, 240.0]})
    assert targets.range_for("f0_median", "feminin") == (170.0, 240.0)
    assert targets.is_overridden("feminin") is True
    # Der Wert im Code bleibt unangetastet.
    assert targets.PROFILES["feminin"]["f0_median"] == (180.0, 250.0)

    assert settings.reset_builtin("feminin") is True
    assert targets.range_for("f0_median", "feminin") == (180.0, 250.0)
    assert targets.is_overridden("feminin") is False
    assert settings.reset_builtin("feminin") is False


def test_anpassung_ersetzt_das_ganze_profil():
    """Was beim Speichern fehlt, gilt danach als nicht gesetzt."""
    settings.save_builtin_override("androgyn", {"f0_median": [150.0, 180.0]})
    assert targets.range_for("f0_median", "androgyn") == (150.0, 180.0)
    assert targets.range_for("f0_sd_st", "androgyn") is None
    settings.reset_builtin("androgyn")
    assert targets.range_for("f0_sd_st", "androgyn") is not None


def test_eigenes_profil_hat_vorrang_vor_anpassung():
    settings.save_builtin_override("feminin", {"f0_median": [170.0, 240.0]})
    settings.save_user_profile("feminin", {"f0_median": [1.0, 2.0]})
    # Verschiedene Schluessel, keine Kollision.
    assert targets.range_for("f0_median", "feminin") == (170.0, 240.0)
    assert targets.range_for("f0_median", "user:feminin") == (1.0, 2.0)


def test_alle_kennwerte_sind_profilierbar():
    keys = targets.profile_keys_all()
    assert len(keys) == len(targets.METRICS)
    # Genau die, die auch in der Detailansicht stehen — H1 und H2 einzeln.
    for expected in ("h1_db", "h2_db", "h1_h2", "hnr", "jitter_local",
                     "shimmer_local", "peak_db"):
        assert expected in keys, expected


def test_profil_hat_vorrang_vor_den_qualitaetsgrenzen():
    """Ein Profil darf auch HNR oder Jitter festlegen."""
    assert targets.range_for("hnr", "feminin") == (15.0, None)

    settings.save_builtin_override("feminin", {"hnr": [20.0, 35.0]})
    assert targets.range_for("hnr", "feminin") == (20.0, 35.0)

    settings.reset_builtin("feminin")
    assert targets.range_for("hnr", "feminin") == (15.0, None)


def test_qualitaetsgrenzen_gelten_ohne_profileintrag():
    for profile in ("none", "maskulin", "feminin"):
        assert targets.range_for("peak_db", profile) == (-30.0, -8.0)


def test_seed_bleibt_auf_zielgroessen_beschraenkt():
    """'Als mein Ziel' soll keinen Aufnahmepegel als Ziel setzen."""
    ranges = targets.build_custom({"f0_median": 180.0, "peak_db": -22.0,
                                   "hnr": 15.0, "h1_db": -40.0})
    assert "f0_median" in ranges
    assert "peak_db" not in ranges and "hnr" not in ranges


def test_live_ziel_startet_aus_und_ist_vom_detail_getrennt():
    """Eine mitlaufende Zielfarbe lenkt beim Sprechen ab."""
    assert settings.get_live_profile() == "none"
    assert settings.get_profile() == "feminin"

    settings.set_live_profile("androgyn")
    assert settings.get_live_profile() == "androgyn"
    assert settings.get_profile() == "feminin"

    settings.set_profile("maskulin")
    assert settings.get_live_profile() == "androgyn"


def test_ohne_ziel_wird_nichts_bewertet():
    for key in ("f0_median", "f2_median", "h1_h2"):
        assert targets.range_for(key, "none") is None
        assert targets.is_within(120.0, targets.range_for(key, "none")) is None
