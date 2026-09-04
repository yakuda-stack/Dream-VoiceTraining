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

"""Sprachumschaltung. Englisch ist die Vorgabe, Deutsch die Alternative.

Neue Texte hier eintragen und im UI ueber t("key") verwenden.
"""

from __future__ import annotations

LANG = "en"
LANGUAGES = ("en", "de")

STRINGS: dict[str, dict[str, str]] = {
    # --- Fenster, Reiter, Steuerleiste ---
    "app_title": {"en": "Voice Training For You", "de": "Voice Training For You"},
    "tab_live": {"en": "Live", "de": "Live"},
    "tab_sessions": {"en": "Sessions", "de": "Sessions"},
    "microphone": {"en": "Microphone", "de": "Mikrofon"},
    "refresh_tip": {"en": "Refresh device list", "de": "Geräteliste aktualisieren"},
    "start": {"en": "Start", "de": "Start"},
    "stop": {"en": "Stop", "de": "Stopp"},
    "record": {"en": "Record", "de": "Aufnahme"},
    "settings": {"en": "Settings", "de": "Einstellungen"},

    # --- Kennzahlen ---
    "card_f0": {"en": "Pitch F0", "de": "Tonhöhe F0"},
    "card_zone": {"en": "Zone", "de": "Zone"},
    "card_level": {"en": "Level", "de": "Pegel"},
    "zone_low": {"en": "low", "de": "tief"},
    "zone_mid": {"en": "androgynous", "de": "androgyn"},
    "zone_high": {"en": "high", "de": "hoch"},

    # --- Diagramme ---
    "spectrogram": {"en": "Spectrogram  ·  dashed: F1 / F2",
                    "de": "Spektrogramm  ·  gestrichelt: F1 / F2"},
    "frequency": {"en": "Frequency", "de": "Frequenz"},
    "history": {"en": "Last 30 seconds", "de": "Verlauf letzte 30 Sekunden"},
    "practice_text": {"en": "Practice text  ·  read the same one every session",
                      "de": "Übungstext  ·  jede Session denselben lesen"},
    "practice_body": {
        "en": "The morning sky was clear and the air still cool. I walked slowly "
              "across the meadow, listened to the birds and stopped at the old oak. "
              "A hedgehog rustled in the leaves. Later the sun came out and "
              "everything went quiet and warm.",
        "de": "Am Morgen war der Himmel klar und die Luft noch kühl. Ich ging "
              "langsam über die Wiese, hörte die Vögel und blieb bei der alten "
              "Eiche stehen. Ein Igel raschelte im Laub. Später kam die Sonne "
              "heraus und alles wurde still und warm.",
    },

    # --- Geraeteliste ---
    "mic_pick_tip": {"en": "Choose a microphone from a bigger list",
                     "de": "Mikrofon aus einer großen Liste wählen"},
    "mic_pick_title": {"en": "Choose an input", "de": "Eingang wählen"},
    "mic_pick_intro": {
        "en": "Pick the input to record from. The technical name of the "
              "selected entry is shown underneath.",
        "de": "Wähle den Eingang, von dem aufgenommen wird. Der technische "
              "Name des markierten Eintrags steht darunter."},
    "mic_pick_use": {"en": "Use this input", "de": "Diesen Eingang benutzen"},
    "mic_pick_default_detail": {
        "en": "Whatever the system currently has set as the default input.",
        "de": "Was im System gerade als Standardeingang eingestellt ist."},
    "mic_pick_note": {
        "en": "The same name twice is not a mistake: a sound card with two "
              "capture inputs reports both under one description, and each "
              "output has its own monitor source. The part in brackets is the "
              "piece of the technical name that tells them apart. If in doubt, "
              "try one, speak, and watch the level card.",
        "de": "Derselbe Name zweimal ist kein Fehler: eine Soundkarte mit zwei "
              "Eingängen meldet beide unter einer Beschreibung, und jeder "
              "Ausgang hat seine eigene Mitschnitt-Quelle. Der Teil in "
              "Klammern ist das Stück des technischen Namens, in dem sie sich "
              "unterscheiden. Im Zweifel einen nehmen, sprechen und auf die "
              "Pegelkachel schauen."},

    "system_default": {"en": "System default", "de": "Systemstandard"},
    "group_mic": {"en": "— Microphones —", "de": "— Mikrofone —"},
    "group_virtual": {"en": "— Virtual sources —", "de": "— Virtuelle Quellen —"},
    "group_monitor": {"en": "— Monitors (listen to an output) —",
                      "de": "— Monitore (Ausgang mithören) —"},
    "not_available": {"en": "(not available)", "de": "(nicht verfügbar)"},
    "source_unavailable": {
        "en": "This source is not available right now. Pick another one or "
              "refresh the list.",
        "de": "Diese Quelle ist gerade nicht verfügbar. Wähle eine andere oder "
              "aktualisiere die Liste."},
    "mic_open_failed": {"en": "Could not open the stream:",
                        "de": "Stream ließ sich nicht öffnen:"},

    # --- Sessions ---
    "col_date": {"en": "Date", "de": "Datum"},
    "col_duration": {"en": "Duration", "de": "Dauer"},
    "col_level": {"en": "Level", "de": "Pegel"},
    "col_f0_median": {"en": "F0 median", "de": "F0 Median"},
    "col_f0_spread": {"en": "F0 10–90 %", "de": "F0 10–90 %"},
    "col_file": {"en": "File", "de": "Datei"},
    "details": {"en": "Details", "de": "Details"},
    "delete": {"en": "Delete", "de": "Löschen"},
    "no_speech": {"en": "no speech signal", "de": "kein Sprachsignal"},
    "quiet": {"en": "quiet", "de": "leise"},
    "open_folder": {"en": "Open folder", "de": "Ordner öffnen"},
    "play": {"en": "Play", "de": "Abspielen"},
    "formant_hint": {
        "en": "Formants are only meaningful on voiced material. For stable F1/F2 "
              "values hold a vowel instead of speaking freely.",
        "de": "Formanten sind nur auf stimmhaftem Material aussagekräftig. Für "
              "stabile F1/F2-Werte einen Vokal halten statt frei zu sprechen."},
    "delete_title": {"en": "Delete recording", "de": "Aufnahme löschen"},
    "delete_question": {
        "en": "Permanently delete “{name}” including the audio file?",
        "de": "„{name}“ mitsamt Audiodatei endgültig löschen?"},
    "deleted": {"en": "{name} deleted.", "de": "{name} gelöscht."},
    "file_missing": {"en": "File not found.", "de": "Datei nicht gefunden."},

    # --- Statusmeldungen ---
    "pick_device": {"en": "Pick a device and press Start.",
                    "de": "Gerät wählen und auf Start drücken."},
    "stopped": {"en": "Stopped.", "de": "Gestoppt."},
    "running": {"en": "Running  ·  {rate} Hz", "de": "Läuft  ·  {rate} Hz"},
    "recording": {"en": "Recording …", "de": "Aufnahme läuft …"},
    "too_short": {"en": "Recording too short, discarded.",
                  "de": "Aufnahme zu kurz, verworfen."},
    "analysing": {"en": "Analysing …", "de": "Werte aus …"},
    "recalculating": {"en": "Recalculating values …", "de": "Werte werden nachgerechnet …"},
    "saved_ok": {"en": "Saved: {name}  ·  F0 median {f0:.0f} Hz  ·  {pct:.0f} % voiced",
                 "de": "Gespeichert: {name}  ·  F0 Median {f0:.0f} Hz  ·  {pct:.0f} % stimmhaft"},
    "saved_nosignal": {
        "en": "{name} saved, but no usable speech signal (only {pct:.0f} % voiced) — "
              "microphone too quiet or too much room noise.",
        "de": "{name} gespeichert, aber kein verwertbares Sprachsignal "
              "(nur {pct:.0f} % stimmhaft) — Mikrofon zu leise oder zu viel Raumrauschen."},
    "saved_plain": {"en": "Saved: {name}", "de": "Gespeichert: {name}"},
    "settings_applied": {"en": "Settings applied  ·  template: {name}",
                         "de": "Einstellungen übernommen  ·  Vorlage: {name}"},

    # --- Einstellungsdialog ---
    "dlg_settings": {"en": "Settings", "de": "Einstellungen"},
    "template": {"en": "Template", "de": "Vorlage"},
    "tpl_standard": {"en": "Standard", "de": "Standard"},
    "tpl_quiet_mic": {"en": "Quiet microphone", "de": "Leises Mikrofon"},
    "tpl_low_voice": {"en": "Low voice / baseline",
                      "de": "Tiefe Stimme / Baseline"},
    "tpl_high_voice": {"en": "High voice", "de": "Hohe Stimme"},
    "tpl_formants": {"en": "Formant measurement (hold a vowel)",
                     "de": "Formantmessung (Vokal halten)"},
    "tpl_noisy": {"en": "Noisy surroundings / stricter",
                  "de": "Lautes Umfeld / strenger"},
    "save_as": {"en": "Save as …", "de": "Speichern unter …"},
    "parameters": {"en": "Parameters", "de": "Parameter"},
    "custom_values": {"en": "— custom values —", "de": "— eigene Werte —"},
    "ok": {"en": "OK", "de": "OK"},
    "cancel": {"en": "Cancel", "de": "Abbrechen"},
    "apply": {"en": "Apply", "de": "Anwenden"},
    "settings_note": {
        "en": "Changes take effect immediately. Saved sessions are untouched — each "
              "entry records the limits it was measured with.",
        "de": "Änderungen wirken sofort auf die laufende Analyse. Bereits "
              "gespeicherte Sessions bleiben unberührt — in jedem Eintrag stehen "
              "die Grenzen, mit denen er gemessen wurde."},
    "template_save_title": {"en": "Save template", "de": "Vorlage speichern"},
    "name": {"en": "Name:", "de": "Name:"},
    "name_taken": {"en": "Name taken", "de": "Name vergeben"},
    "name_taken_body": {
        "en": "Built-in templates cannot be overwritten. Pick a different name.",
        "de": "Eingebaute Vorlagen lassen sich nicht überschreiben. "
              "Wähle einen anderen Namen."},
    "template_delete_title": {"en": "Delete template", "de": "Vorlage löschen"},
    "template_delete_body": {"en": "Really delete “{name}”?",
                             "de": "„{name}“ wirklich löschen?"},

    # --- Detaildialog ---
    "dlg_detail": {"en": "Recording in detail", "de": "Aufnahme im Detail"},
    "recording_head": {"en": "Recording", "de": "Aufnahme"},
    "target": {"en": "Target", "de": "Ziel"},
    "comparison": {"en": "Comparison", "de": "Vergleich"},
    "no_comparison": {"en": "— no comparison —", "de": "— kein Vergleich —"},
    "col_metric": {"en": "Metric", "de": "Kennwert"},
    "col_value": {"en": "Value", "de": "Wert"},
    "col_target": {"en": "Target range", "de": "Zielbereich"},
    "col_verdict": {"en": "Verdict", "de": "Bewertung"},
    "reanalyse": {"en": "Re-analyse", "de": "Neu auswerten"},
    "close": {"en": "Close", "de": "Schließen"},
    "no_signal_note": {
        "en": "This recording had too little voiced material, so the metrics were "
              "deliberately not calculated.",
        "de": "Diese Aufnahme enthielt zu wenig stimmhaftes Material, die "
              "Kennwerte wurden bewusst nicht berechnet."},
    "measured_with": {
        "en": "measured with F0 limits {floor:.0f}–{ceiling:.0f} Hz, "
              "formant ceiling {formant:.0f} Hz",
        "de": "gemessen mit F0-Grenzen {floor:.0f}–{ceiling:.0f} Hz, "
              "Formant-Obergrenze {formant:.0f} Hz"},
    "targets_note": {
        "en": "The target ranges are population averages from the speech science "
              "literature, not prescriptions. Perception depends on more than what "
              "is measurable here. The most meaningful comparison is against your "
              "own earlier recordings.",
        "de": "Die Zielbereiche sind Populationsmittelwerte aus der Literatur zur "
              "Sprechstimme, keine Vorgaben. Wahrnehmung hängt an mehr Faktoren als "
              "hier messbar sind. Am aussagekräftigsten ist der Vergleich mit "
              "deinen eigenen früheren Aufnahmen."},
    "no_wav": {"en": "The WAV file is missing, nothing to recalculate.",
               "de": "Die WAV-Datei fehlt, es lässt sich nichts nachrechnen."},

    # --- Parameter im Einstellungsdialog ---
    "param_silence_rms": {"en": "Silence threshold", "de": "Stille-Schwelle"},
    "param_silence_rms_hint": {
        "en": "Below this level nothing is analysed. Lower it for a quiet microphone.",
        "de": "Unterhalb dieses Pegels wird nicht analysiert. Bei leisem Mikrofon senken."},
    "param_pitch_floor": {"en": "F0 lower limit", "de": "F0 Untergrenze"},
    "param_pitch_floor_hint": {
        "en": "Lower search limit for pitch. Too low invites octave errors, too high "
              "cuts off creak and low sentence endings.",
        "de": "Untere Suchgrenze der Tonhöhenanalyse. Zu tief begünstigt Oktavfehler, "
              "zu hoch schneidet Knarrstimme und tiefe Satzenden weg."},
    "param_pitch_ceiling": {"en": "F0 upper limit", "de": "F0 Obergrenze"},
    "param_pitch_ceiling_hint": {
        "en": "Upper search limit for pitch. A narrow range makes the tracker steadier.",
        "de": "Obere Suchgrenze der Tonhöhenanalyse. Eng gesetzt ist der Tracker stabiler."},
    "param_formant_ceiling": {"en": "Formant ceiling", "de": "Formant-Obergrenze"},
    "param_formant_ceiling_hint": {
        "en": "Praat recommends 5000 Hz for low and 5500 Hz for high voices. "
              "Set wrong it shifts F1 and F2 systematically.",
        "de": "Praat-Empfehlung: 5000 Hz für tiefe, 5500 Hz für hohe Stimmen. "
              "Falsch gesetzt verschiebt sie F1 und F2 systematisch."},
    "param_zone_low": {"en": "Zone boundary, lower", "de": "Zonengrenze unten"},
    "param_zone_low_hint": {
        "en": "Below this boundary the voice is labelled “low”.",
        "de": "Unterhalb dieser Grenze wird als „tief“ eingeordnet."},
    "param_zone_high": {"en": "Zone boundary, upper", "de": "Zonengrenze oben"},
    "param_zone_high_hint": {
        "en": "Above this boundary the voice is labelled “high”. In between lies "
              "the ambiguous range.",
        "de": "Oberhalb dieser Grenze wird als „hoch“ eingeordnet. Dazwischen liegt "
              "der mehrdeutige Bereich."},
    "param_voicing_threshold": {"en": "Voicing threshold", "de": "Stimmhaftigkeit"},
    "param_voicing_threshold_hint": {
        "en": "How periodic a segment must be to count as voice. Low picks up quiet "
              "passages but mistakes noise for speech. High is stricter and discards "
              "some real material.",
        "de": "Wie periodisch ein Abschnitt sein muss, um als Stimme zu gelten. "
              "Niedrig erkennt auch leise Stellen, hält aber Rauschen für Sprache. "
              "Hoch ist strenger und verwirft manche echte Stelle."},
    "param_min_voiced_ratio": {"en": "Minimum voiced share", "de": "Mindestanteil Stimme"},
    "param_min_voiced_ratio_hint": {
        "en": "How much of a recording must be voiced before any values are computed. "
              "Prevents numbers derived from pure room noise.",
        "de": "Wie viel einer Aufnahme stimmhaft sein muss, damit überhaupt Werte "
              "berechnet werden. Verhindert Zahlen aus reinem Raumrauschen."},

    # --- Kennwerte in der Detailansicht ---
    "m_f0_median": {"en": "F0 median", "de": "F0 Median"},
    "m_f0_median_hint": {
        "en": "Average speaking pitch. The most cited value, but not the most important.",
        "de": "Mittlere Sprechtonhöhe. Der meistgenannte, aber nicht wichtigste Wert."},
    "m_f0_p10": {"en": "F0 lower end", "de": "F0 unteres Ende"},
    "m_f0_p10_hint": {"en": "10th percentile — how far sentence endings drop.",
                      "de": "10. Perzentil — wie tief die Satzenden abfallen."},
    "m_f0_p90": {"en": "F0 upper end", "de": "F0 oberes Ende"},
    "m_f0_p90_hint": {"en": "90th percentile — how far up the voice reaches.",
                      "de": "90. Perzentil — wie weit nach oben gegangen wird."},
    "m_f0_sd_st": {"en": "Intonation width", "de": "Intonationsbreite"},
    "m_f0_sd_st_hint": {
        "en": "Standard deviation in semitones. How much melody the speech carries.",
        "de": "Standardabweichung in Halbtönen. Wie viel Melodie in der Sprechweise steckt."},
    "m_f0_range_st": {"en": "Pitch range", "de": "Tonumfang"},
    "m_f0_range_st_hint": {"en": "Distance between lower and upper end in semitones.",
                           "de": "Abstand zwischen unterem und oberem Ende in Halbtönen."},
    "m_f1_median": {"en": "F1", "de": "F1"},
    "m_f1_median_hint": {"en": "First formant. Only reliable on sustained vowels.",
                         "de": "Erster Formant. Nur bei gehaltenen Vokalen belastbar."},
    "m_f2_median": {"en": "F2", "de": "F2"},
    "m_f2_median_hint": {"en": "Second formant. The single most important value for resonance.",
                         "de": "Zweiter Formant. Wichtigster Einzelwert für die Resonanz."},
    "m_f3_median": {"en": "F3", "de": "F3"},
    "m_f3_median_hint": {"en": "Third formant. Closely tied to vocal tract length.",
                         "de": "Dritter Formant. Hängt eng an der Länge des Ansatzrohrs."},
    "m_hnr": {"en": "Clarity (HNR)", "de": "Klarheit (HNR)"},
    "m_hnr_hint": {
        "en": "Ratio of tone to noise. Low means breathy — or the recording was too quiet.",
        "de": "Verhältnis von Klang zu Rauschen. Niedrig heißt behaucht — oder die "
              "Aufnahme war zu leise."},
    "m_voiced_ratio_pct": {"en": "Voiced share", "de": "Stimmhafter Anteil"},
    "m_voiced_ratio_pct_hint": {"en": "How much of the recording was recognised as voice.",
                                "de": "Wie viel der Aufnahme als Stimme erkannt wurde."},
    "m_peak_db": {"en": "Recording level", "de": "Aufnahmepegel"},
    "m_peak_db_hint": {
        "en": "Peak level. Below −40 dB the measurements become unreliable.",
        "de": "Spitzenpegel. Unter −40 dB werden die Messwerte unzuverlässig."},

    "m_h1_db": {"en": "H1 level", "de": "H1 Pegel"},
    "m_h1_db_hint": {
        "en": "Level of the first harmonic, i.e. the fundamental itself. Relative "
              "to full scale, so it moves with your microphone gain — only compare "
              "it between recordings made at the same setting.",
        "de": "Pegel der ersten Harmonischen, also des Grundtons selbst. Bezogen "
              "auf Vollaussteuerung und damit vom Mikrofonpegel abhängig — nur "
              "zwischen Aufnahmen mit gleicher Einstellung vergleichbar."},
    "m_h2_db": {"en": "H2 level", "de": "H2 Pegel"},
    "m_h2_db_hint": {
        "en": "Level of the second harmonic, one octave above the fundamental. "
              "Same gain caveat as H1. What actually matters is the gap to H1.",
        "de": "Pegel der zweiten Harmonischen, eine Oktave über dem Grundton. "
              "Gleicher Vorbehalt wie bei H1. Aussagekräftig ist erst der Abstand "
              "zu H1."},
    "m_h1_h2": {"en": "Weight (H1–H2)", "de": "Schwere (H1–H2)"},
    "m_h1_h2_hint": {
        "en": "Level gap between the first two harmonics. High means a light, "
              "breathy setting, low means a heavy, pressed one. Uncorrected, so "
              "the formants influence it.",
        "de": "Pegelabstand der ersten beiden Harmonischen. Hoch heißt leichte, "
              "behauchte Stimmgebung, niedrig schwere, gepresste. Unkorrigiert, "
              "die Formanten beeinflussen den Wert also mit."},
    "m_jitter_local": {"en": "Jitter (local)", "de": "Jitter (lokal)"},
    "m_jitter_local_hint": {
        "en": "Cycle-to-cycle variation of pitch. The reference range applies to a "
              "sustained vowel; connected speech is naturally much higher.",
        "de": "Schwankung der Periodenlänge von Zyklus zu Zyklus. Der Zielbereich "
              "gilt für gehaltene Vokale, fließende Sprache liegt naturgemäß "
              "deutlich höher."},
    "m_shimmer_local": {"en": "Shimmer (local)", "de": "Shimmer (lokal)"},
    "m_shimmer_local_hint": {
        "en": "Cycle-to-cycle variation of amplitude. Same caveat as jitter — the "
              "range only applies to a sustained vowel.",
        "de": "Schwankung der Amplitude von Zyklus zu Zyklus. Gleicher Vorbehalt "
              "wie bei Jitter — der Bereich gilt nur für gehaltene Vokale."},
    "m_voice_breaks_pct": {"en": "Voice breaks", "de": "Stimmabbrüche"},
    "m_voice_breaks_pct_hint": {
        "en": "Share of the signal where voicing collapses. In read text pauses and "
              "unvoiced consonants count too, so high values are expected.",
        "de": "Anteil des Signals, in dem die Stimmgebung abreißt. In Lesetext "
              "zählen Pausen und stimmlose Laute mit, hohe Werte sind dort normal."},
    "m_voice_break_count": {"en": "Number of breaks", "de": "Anzahl Abbrüche"},
    "m_voice_break_count_hint": {
        "en": "How often voicing collapsed. Only meaningful on a sustained vowel.",
        "de": "Wie oft die Stimmgebung abgerissen ist. Nur bei gehaltenem Vokal "
              "aussagekräftig."},
    "advanced": {"en": "Advanced", "de": "Erweitert"},
    "advanced_hint": {
        "en": "Drag the edges of the highlighted region to pick a part of the "
              "recording, then analyse just that. Useful for isolating a single "
              "sustained vowel from a longer take. The stored session values stay "
              "untouched until you save the selection.",
        "de": "Zieh die Ränder des markierten Bereichs, um einen Teil der Aufnahme "
              "zu wählen, und werte nur den aus. Praktisch, um einen einzelnen "
              "gehaltenen Vokal aus einer längeren Aufnahme herauszulösen. Die "
              "gespeicherten Werte bleiben unberührt, bis du die Auswahl sicherst."},
    "waveform": {"en": "Waveform", "de": "Wellenform"},
    "seconds": {"en": "s", "de": "s"},
    "analyse_selection": {"en": "Analyse selection", "de": "Auswahl auswerten"},
    "full_recording": {"en": "Whole recording", "de": "Ganze Aufnahme"},
    "play_selection": {"en": "Play selection", "de": "Auswahl abspielen"},
    "save_selection": {"en": "Save selection as session values",
                       "de": "Auswahl als Sessionwerte speichern"},
    "selection_label": {"en": "Selection: {start:.2f} – {end:.2f} s  ({length:.2f} s)",
                        "de": "Auswahl: {start:.2f} – {end:.2f} s  ({length:.2f} s)"},
    "showing_selection": {
        "en": "Showing the selection {start:.2f}–{end:.2f} s, not the whole recording.",
        "de": "Angezeigt wird die Auswahl {start:.2f}–{end:.2f} s, nicht die "
              "ganze Aufnahme."},
    "selection_too_short": {"en": "Selection is too short to analyse.",
                            "de": "Die Auswahl ist zu kurz für eine Auswertung."},
    "selection_saved": {"en": "Selection saved as the values for this session.",
                        "de": "Auswahl als Werte dieser Session gespeichert."},
    "col_type": {"en": "Type", "de": "Typ"},
    "type_reading": {"en": "Reading text", "de": "Lesetext"},
    "type_reading_hint": {
        "en": "The practice text, read the same way every session. Your reference "
              "for pitch and intonation.",
        "de": "Der Übungstext, jede Session gleich gelesen. Deine Referenz für "
              "Tonhöhe und Melodieführung."},
    "type_hum": {"en": "Pitch test (hum)", "de": "Tonhöhentest (Summen)"},
    "type_hum_hint": {
        "en": "A held “mmm” or “ahh” at a comfortable pitch. The cleanest way to "
              "measure pitch, weight and stability without articulation getting "
              "in the way.",
        "de": "Ein gehaltenes „mhh“ oder „ahh“ in bequemer Lage. Der sauberste "
              "Weg, Tonhöhe, Schwere und Stabilität zu messen, ohne dass die "
              "Artikulation dazwischenfunkt."},
    "type_vowel_a": {"en": "Vowel /a/", "de": "Vokal /a/"},
    "type_vowel_a_hint": {"en": "Held “ah”. Open vowel, high F1.",
                          "de": "Gehaltenes „ah“. Offener Vokal, hohes F1."},
    "type_vowel_i": {"en": "Vowel /i/", "de": "Vokal /i/"},
    "type_vowel_i_hint": {"en": "Held “ee”. Close front vowel, high F2.",
                          "de": "Gehaltenes „ih“. Geschlossen und vorn, hohes F2."},
    "type_vowel_u": {"en": "Vowel /u/", "de": "Vokal /u/"},
    "type_vowel_u_hint": {"en": "Held “oo”. Close back vowel, low F2.",
                          "de": "Gehaltenes „uh“. Geschlossen und hinten, tiefes F2."},
    "type_free": {"en": "Free", "de": "Frei"},
    "type_free_hint": {"en": "Anything else — conversation, a phrase, an experiment.",
                       "de": "Alles andere — Gespräch, ein Satz, ein Versuch."},
    "recording_type": {"en": "Type", "de": "Typ"},

    "level_live_warning": {
        "en": "Level low ({level:.0f} dBFS) — the analysis may find no usable "
              "voice. Raise the gain or move closer.",
        "de": "Pegel niedrig ({level:.0f} dBFS) — die Auswertung findet "
              "womöglich keine verwertbare Stimme. Pegel hoch oder näher ran."},
    "change_type": {"en": "Change type", "de": "Typ ändern"},

    "tab_analysis": {"en": "Analysis", "de": "Analyse"},
    "tab_info": {"en": "Info", "de": "Info"},
    "tab_design": {"en": "Design", "de": "Design"},
    "design_hint": {
        "en": "Pick a theme, then recolour anything you like or drop an image "
              "behind the window.",
        "de": "Wähle ein Thema, färbe einzelne Elemente um oder leg ein Bild "
              "hinter das Fenster."},
    "theme": {"en": "Theme", "de": "Thema"},
    "colors": {"en": "Colors", "de": "Farben"},
    "reset_colors": {"en": "Reset colors", "de": "Farben zurücksetzen"},
    "background": {"en": "Background", "de": "Hintergrund"},
    "add_image": {"en": "Add image", "de": "Bild hinzufügen"},
    "no_background": {"en": "None", "de": "Keins"},
    "card_opacity": {"en": "Card opacity", "de": "Deckkraft der Flächen"},
    "opacity_hint": {
        "en": "Only has an effect with a background image.",
        "de": "Wirkt nur zusammen mit einem Hintergrundbild."},
    "choose_image": {"en": "Choose a background image",
                     "de": "Hintergrundbild wählen"},
    "image_filter": {"en": "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
                     "de": "Bilder (*.png *.jpg *.jpeg *.webp *.bmp)"},
    "remove_image": {"en": "Remove image", "de": "Bild entfernen"},
    "remove_image_body": {"en": "Remove “{name}” from the list?",
                          "de": "„{name}“ aus der Liste entfernen?"},
    "pick_color": {"en": "Pick a colour for “{role}”",
                   "de": "Farbe für „{role}“ wählen"},
    "theme_default": {"en": "Default", "de": "Standard"},
    "theme_carbon": {"en": "Carbon", "de": "Carbon"},
    "theme_nebula": {"en": "Nebula", "de": "Nebula"},
    "theme_embers": {"en": "Embers", "de": "Embers"},
    "theme_grass": {"en": "Grass", "de": "Grass"},
    "theme_ocean": {"en": "Ocean", "de": "Ocean"},
    "theme_rose": {"en": "Rose", "de": "Rose"},
    "theme_mono": {"en": "Mono", "de": "Mono"},
    "role_accent": {"en": "Accent", "de": "Akzent"},
    "role_window": {"en": "Window", "de": "Fenster"},
    "role_sidebar": {"en": "Sidebar", "de": "Leisten"},
    "role_cards": {"en": "Cards", "de": "Flächen"},
    "role_inner": {"en": "Inner boxes", "de": "Innenflächen"},
    "role_border": {"en": "Borders", "de": "Ränder"},
    "role_text": {"en": "Text", "de": "Text"},
    "role_dim": {"en": "Secondary text", "de": "Nebentext"},
    "role_danger": {"en": "Stop / delete", "de": "Stopp / Löschen"},
    "role_ok": {"en": "Good", "de": "Gut"},
    "role_warn": {"en": "Warning", "de": "Warnung"},
    "role_highlight": {"en": "Highlight", "de": "Hervorhebung"},
    "tab_profiles": {"en": "Target profiles", "de": "Zielprofile"},
    "target_voice": {"en": "Target voice", "de": "Zielstimme"},
    "profiles_hint": {
        "en": "A target profile is the range each metric should fall into. The "
              "three built-in ones start from population averages in the "
              "literature; you can adjust them and press Save, or use Save as "
              "to keep a separate profile. Reset restores the original values "
              "at any time. The selected profile colours the live readouts and "
              "the verdict column in the detail view.",
        "de": "Ein Zielprofil legt fest, in welchem Bereich jeder Kennwert liegen "
              "soll. Die drei eingebauten starten mit Populationsmittelwerten "
              "aus der Literatur; du kannst sie anpassen und auf Speichern "
              "drücken oder über Speichern unter ein eigenes Profil anlegen. "
              "Zurücksetzen holt die Ursprungswerte jederzeit zurück. Das "
              "gewählte Profil färbt die Live-Kacheln und die Bewertungsspalte "
              "in der Detailansicht."},
    "profile_save": {"en": "Save", "de": "Speichern"},
    "profile_reset": {"en": "Reset to default", "de": "Auf Vorgabe zurücksetzen"},
    "profile_reset_title": {"en": "Reset profile", "de": "Profil zurücksetzen"},
    "profile_reset_body": {
        "en": "Restore “{name}” to the values from the literature?",
        "de": "„{name}“ auf die Werte aus der Literatur zurücksetzen?"},
    "profile_overridden": {
        "en": "Adjusted by you — the original values are one click away.",
        "de": "Von dir angepasst — die Ursprungswerte sind einen Klick entfernt."},
    "profile_modified": {"en": "Unsaved changes", "de": "Nicht gespeicherte Änderungen"},
    "profile_saved": {"en": "Saved.", "de": "Gespeichert."},
    "profile_low": {"en": "from", "de": "von"},
    "profile_high": {"en": "to", "de": "bis"},
    "profile_unused": {"en": "no target for this metric",
                       "de": "kein Ziel für diesen Kennwert"},
    "profile_save_title": {"en": "Save target profile", "de": "Zielprofil speichern"},
    "profile_delete_title": {"en": "Delete target profile", "de": "Zielprofil löschen"},
    "profile_delete_body": {"en": "Really delete the profile “{name}”?",
                            "de": "Zielprofil „{name}“ wirklich löschen?"},
    "profile_needs_values": {
        "en": "Enable at least one metric before saving a profile.",
        "de": "Schalte mindestens einen Kennwert ein, bevor du speicherst."},
    "profile_custom": {"en": "my target", "de": "mein Ziel"},
    "set_custom_target": {"en": "Use these values as my target",
                          "de": "Diese Werte als mein Ziel übernehmen"},
    "custom_target_set": {
        "en": "Saved as “my target”, with a tolerance of ±{percent:.0f} % around "
              "each value. Pick it in the target dropdown to compare against it.",
        "de": "Als „mein Ziel“ gespeichert, mit ±{percent:.0f} % Toleranz um "
              "jeden Wert. Über die Zielauswahl vergleichst du dagegen."},
    "custom_target_missing": {
        "en": "This recording has no usable values to build a target from.",
        "de": "Diese Aufnahme hat keine verwertbaren Werte für ein Ziel."},
    "custom_target_clear": {"en": "Clear my target", "de": "Mein Ziel löschen"},
    "col_name": {"en": "Name", "de": "Name"},
    "rename": {"en": "Rename …", "de": "Umbenennen …"},
    "rename_title": {"en": "Rename recording", "de": "Aufnahme umbenennen"},
    "rename_prompt": {"en": "Name (the file is renamed too):",
                      "de": "Name (die Datei wird mit umbenannt):"},
    "rename_failed": {"en": "The file could not be renamed:",
                      "de": "Die Datei ließ sich nicht umbenennen:"},
    "rename_exists": {"en": "A recording with that file name already exists.",
                      "de": "Eine Aufnahme mit diesem Dateinamen gibt es schon."},
    "move_left": {"en": "Move left", "de": "Nach links schieben"},
    "move_right": {"en": "Move right", "de": "Nach rechts schieben"},
    "hide_column": {"en": "Hide “{name}”", "de": "„{name}“ ausblenden"},
    "columns_menu": {"en": "Columns", "de": "Spalten"},
    "manage_columns": {"en": "Manage columns …", "de": "Spalten verwalten …"},
    "sort_by_this": {"en": "Sort by this column", "de": "Nach dieser Spalte sortieren"},
    "last_column": {"en": "The last visible column cannot be hidden.",
                    "de": "Die letzte sichtbare Spalte lässt sich nicht ausblenden."},
    "filter": {"en": "View …", "de": "Ansicht …"},
    "filter_title": {"en": "List view", "de": "Listenansicht"},
    "filter_columns": {"en": "Visible columns", "de": "Sichtbare Spalten"},
    "filter_columns_hint": {
        "en": "Pick which measurements the list shows. Everything is stored "
              "either way — this only changes what is on screen and what an "
              "export contains.",
        "de": "Wähle, welche Messwerte die Liste zeigt. Gespeichert wird ohnehin "
              "alles — das ändert nur die Anzeige und was im Export landet."},
    "filter_sort": {"en": "Sorting", "de": "Sortierung"},
    "filter_sort_by": {"en": "Sort by", "de": "Sortieren nach"},
    "filter_descending": {"en": "Newest / largest first",
                          "de": "Neueste / größte zuerst"},
    "filter_period": {"en": "Time range", "de": "Zeitraum"},
    "filter_period_on": {"en": "Only show recordings in a period",
                         "de": "Nur Aufnahmen aus einem Zeitraum zeigen"},
    "filter_from": {"en": "From", "de": "Von"},
    "filter_to": {"en": "To", "de": "Bis"},
    "select_all": {"en": "All", "de": "Alle"},
    "select_none": {"en": "None", "de": "Keine"},
    "select_default": {"en": "Default", "de": "Standard"},
    "shown_count": {"en": "{shown} of {total} recordings shown",
                    "de": "{shown} von {total} Aufnahmen angezeigt"},
    "export_list": {"en": "Export list …", "de": "Liste exportieren …"},
    "export_list_title": {"en": "Export session list",
                          "de": "Sessionliste exportieren"},
    "report_list_title": {"en": "Dream-VoiceTraining — session list",
                          "de": "Dream-VoiceTraining — Sessionliste"},
    "export_language_title": {"en": "Export language", "de": "Sprache des Exports"},
    "export_language_body": {
        "en": "Which language should the exported file be written in?",
        "de": "In welcher Sprache soll die Datei geschrieben werden?"},
    "language_de": {"en": "German", "de": "Deutsch"},
    "language_en": {"en": "English", "de": "Englisch"},
    "install_offer_title": {"en": "Set up Dream-VoiceTraining?",
                            "de": "Dream-VoiceTraining einrichten?"},
    "install_offer_body": {
        "en": "<p>Right now the program is running from wherever you saved "
              "it. Shall it move to its own folder and add a shortcut?</p>"
              "<p>It would copy itself to<br><code>{folder}</code><br>put an "
              "icon on the desktop and an entry in the start menu, and show "
              "up under Apps &amp; features like any other program. Then it "
              "restarts from there.</p>"
              "<p>Your recordings and settings are not affected either way. "
              "This is asked once.</p>",
        "de": "<p>Das Programm läuft gerade von dort, wo du es gespeichert "
              "hast. Soll es in seinen eigenen Ordner umziehen und eine "
              "Verknüpfung anlegen?</p>"
              "<p>Es kopiert sich dann nach<br><code>{folder}</code><br>legt "
              "ein Symbol auf den Schreibtisch und einen Eintrag ins "
              "Startmenü und erscheint unter „Apps und Features“ wie jedes "
              "andere Programm. Danach startet es von dort neu.</p>"
              "<p>Aufnahmen und Einstellungen sind so oder so nicht "
              "betroffen. Die Frage kommt nur einmal.</p>"},
    "install_failed": {
        "en": "Copying failed, so nothing was changed:\n\n{error}",
        "de": "Das Kopieren ist gescheitert, es wurde nichts geändert:"
              "\n\n{error}"},

    "intro_title": {"en": "Welcome", "de": "Willkommen"},
    "intro_language": {"en": "Choose your language",
                       "de": "Sprache wählen"},
    "intro_language_body": {
        "en": "You can change this at any time with the EN/DE switch in the "
              "toolbar.",
        "de": "Lässt sich jederzeit über den EN/DE-Schalter in der Leiste "
              "ändern."},
    "intro_step": {"en": "Step {step} of {total}", "de": "Schritt {step} von {total}"},
    "intro_next": {"en": "Next", "de": "Weiter"},
    "intro_back": {"en": "Back", "de": "Zurück"},
    "intro_skip": {"en": "Skip", "de": "Überspringen"},
    "intro_done": {"en": "Get started", "de": "Los geht’s"},
    "intro_restart": {"en": "Show introduction again",
                      "de": "Einführung erneut zeigen"},

    "intro_level_title": {"en": "Set your level first",
                          "de": "Zuerst den Pegel richten"},
    "intro_level_body": {
        "en": "<p>Pick the microphone from the list and press <b>Start</b>. "
              "Speak normally and watch the level card.</p>"
              "<p>The pulsing golden ⓘ in the main window points at the "
              "control this page is about — it moves along as you go through "
              "these pages.</p>"
              "<p>Aim for roughly <b>−20 dB</b>. Below −40 dB the analysis "
              "stops being trustworthy — it will report noise as a voice, or "
              "refuse to report anything at all.</p>"
              "<p>Raise the input in <code>pavucontrol</code> or sit closer, "
              "about a hand's width away and slightly off to the side.</p>",
        "de": "<p>Wähle das Mikrofon aus der Liste und drücke <b>Start</b>. "
              "Sprich normal und schaue auf den Kachelpegel.</p>"
              "<p>Das pulsierende goldene ⓘ im Hauptfenster zeigt auf das "
              "Bedienelement, um das es auf dieser Seite geht — es wandert "
              "mit, während du weiterblätterst.</p>"
              "<p>Ziel sind rund <b>−20 dB</b>. Unter −40 dB wird die "
              "Auswertung unzuverlässig — sie hält dann Rauschen für Stimme "
              "oder verweigert die Werte ganz.</p>"
              "<p>Zieh den Eingang in <code>pavucontrol</code> hoch oder setz "
              "dich näher, etwa eine Handbreit und leicht seitlich.</p>"},

    "intro_record_title": {"en": "Record with a type",
                           "de": "Aufnehmen mit Typ"},
    "intro_record_body": {
        "en": "<p>Before recording, pick a <b>type</b>: reading text, a held "
              "hum, or one of the vowels. The type decides what the numbers "
              "are worth later — a median over reading text and a held vowel "
              "measure different things.</p>"
              "<p>The type can still be changed afterwards from the row's "
              "context menu, so a take filed under the wrong one is not "
              "lost.</p>",
        "de": "<p>Vor der Aufnahme einen <b>Typ</b> wählen: Lesetext, "
              "gehaltenes Summen oder einen der Vokale. Der Typ entscheidet, "
              "was die Zahlen später wert sind — ein Median über Lesetext und "
              "ein gehaltener Vokal messen verschiedene Dinge.</p>"
              "<p>Der Typ lässt sich später über das Kontextmenü der Zeile "
              "ändern, eine falsch abgelegte Aufnahme ist also nicht "
              "verloren.</p>"},

    "intro_first_title": {"en": "A good first round",
                          "de": "Eine gute erste Runde"},
    "intro_first_body": {
        "en": "<p>Once the level sits right, record these four, one after the "
              "other, each as its own take:</p>"
              "<ul>"
              "<li><b>Pitch test (hum)</b> — a held “mmm” at a comfortable "
              "pitch, about four seconds.</li>"
              "<li><b>Vowel /a/</b> — a held “ah”, about three seconds.</li>"
              "<li><b>Vowel /i/</b> — a held “ee”, about three seconds.</li>"
              "<li><b>Vowel /u/</b> — a held “oo”, about three seconds.</li>"
              "</ul>"
              "<p>Pick the matching type before each one, hold the sound as "
              "steadily as you can, and breathe in between. Held sounds are "
              "what make formants, jitter and shimmer comparable between "
              "sessions — connected speech moves too much for that.</p>"
              "<p>Beginning and end of a take are always a bit unsteady. In "
              "the detail view, <b>Advanced</b> lets you drag a region over "
              "the calm middle and analyse only that.</p>"
              "<p>Reading the practice text once as <b>Reading text</b> is a "
              "good baseline on top of that.</p>",
        "de": "<p>Wenn der Pegel stimmt, nimm diese vier nacheinander auf, "
              "jede als eigene Aufnahme:</p>"
              "<ul>"
              "<li><b>Tonhöhentest (Summen)</b> — ein gehaltenes „mhh“ in "
              "bequemer Lage, etwa vier Sekunden.</li>"
              "<li><b>Vokal /a/</b> — ein gehaltenes „ah“, etwa drei "
              "Sekunden.</li>"
              "<li><b>Vokal /i/</b> — ein gehaltenes „ih“, etwa drei "
              "Sekunden.</li>"
              "<li><b>Vokal /u/</b> — ein gehaltenes „uh“, etwa drei "
              "Sekunden.</li>"
              "</ul>"
              "<p>Vor jeder Aufnahme den passenden Typ wählen, den Laut so "
              "ruhig wie möglich halten und dazwischen durchatmen. Gehaltene "
              "Laute sind das, was Formanten, Jitter und Shimmer zwischen "
              "Sessions vergleichbar macht — fließende Sprache bewegt sich "
              "dafür zu stark.</p>"
              "<p>Anfang und Ende einer Aufnahme sind immer etwas unruhig. In "
              "der Detailansicht kannst du unter <b>Erweitert</b> einen "
              "Bereich über die ruhige Mitte ziehen und nur den auswerten.</p>"
              "<p>Den Übungstext einmal als <b>Lesetext</b> zu lesen ist "
              "zusätzlich eine gute Nullmessung.</p>"},

    "intro_sessions_title": {"en": "Sessions and details",
                             "de": "Sessions und Details"},
    "intro_sessions_body": {
        "en": "<p>Every recording lands in the <b>Sessions</b> tab — the "
              "second tab at the top left, marked below. Click a column "
              "header to sort, right-click a row for playback, renaming or "
              "deletion.</p>"
              "<p><b>Details</b> at the end of a row opens that recording: "
              "all eighteen metrics, each checked against your target "
              "profile, and optionally compared against another take.</p>"
              "<p>Recordings without a usable voice say so instead of showing "
              "invented numbers.</p>",
        "de": "<p>Jede Aufnahme landet im Reiter <b>Sessions</b> — der zweite "
              "Reiter oben links, unten markiert. Klick auf eine "
              "Spaltenüberschrift sortiert, Rechtsklick auf eine Zeile bietet "
              "Wiedergabe, Umbenennen und Löschen.</p>"
              "<p><b>Details</b> am Ende einer Zeile öffnet die Aufnahme: "
              "alle achtzehn Kennwerte, jeder gegen dein Zielprofil geprüft "
              "und auf Wunsch mit einer anderen Aufnahme verglichen.</p>"
              "<p>Aufnahmen ohne verwertbare Stimme sagen das auch, statt "
              "erfundene Zahlen zu zeigen.</p>"},

    "intro_advanced_title": {"en": "Advanced mode — analysing a section",
                             "de": "Erweiterter Modus — Ausschnitt auswerten"},
    "intro_advanced_body": {
        "en": "<p>At the bottom of the detail view, <b>Advanced</b> unfolds "
              "the waveform of the recording with a draggable region. Drag "
              "its edges over the part you want, then press <b>Analyse "
              "selection</b> — the table above updates to that section "
              "alone.</p>"
              "<p>This is the point of the whole thing: a held vowel has a "
              "beginning where you are still finding the sound and an end "
              "where the air runs out. Both distort formants, jitter and "
              "shimmer. Cutting out the calm middle is what turns those "
              "numbers into something you can track over weeks.</p>"
              "<p>Nothing is overwritten — the stored session values stay "
              "untouched until you press <b>Save selection as session "
              "values</b>. <b>Whole recording</b> goes back to the full "
              "take.</p>",
        "de": "<p>Unten in der Detailansicht klappt <b>Erweitert</b> die "
              "Wellenform der Aufnahme mit einem ziehbaren Bereich auf. Zieh "
              "seine Ränder über den gewünschten Teil und drück <b>Auswahl "
              "auswerten</b> — die Tabelle darüber zeigt dann nur noch diesen "
              "Ausschnitt.</p>"
              "<p>Genau darum geht es: ein gehaltener Vokal hat einen Anfang, "
              "in dem du den Laut noch suchst, und ein Ende, in dem die Luft "
              "ausgeht. Beides verzerrt Formanten, Jitter und Shimmer. Die "
              "ruhige Mitte herauszuschneiden macht aus diesen Zahlen erst "
              "etwas, das sich über Wochen verfolgen lässt.</p>"
              "<p>Überschrieben wird nichts — die gespeicherten Sessionwerte "
              "bleiben unangetastet, bis du <b>Auswahl als Sessionwerte "
              "speichern</b> drückst. <b>Ganze Aufnahme</b> holt die "
              "vollständige Aufnahme zurück.</p>"},

    "intro_columns_title": {"en": "Make the list yours",
                            "de": "Die Liste anpassen"},
    "intro_columns_body": {
        "en": "<p>The list ships with a sensible dozen columns, but all "
              "twenty-three are available: F0 lower and upper end, pitch "
              "range, F1, weight, clarity, voice breaks, voiced share and the "
              "rest.</p>"
              "<p><b>Right-click any column header</b> for a checkable list "
              "of them, plus sorting and hiding. Columns can be dragged into "
              "any order, and the order is remembered.</p>"
              "<p><b>View …</b>, marked in the main window, does the same in "
              "one dialog and can additionally limit the list to a date "
              "range. <b>Export …</b> beside it writes the list as text or "
              "CSV.</p>",
        "de": "<p>Die Liste startet mit einem sinnvollen Dutzend Spalten, "
              "verfügbar sind aber alle dreiundzwanzig: F0 unteres und oberes "
              "Ende, Tonumfang, F1, Schwere, Klarheit, Stimmabbrüche, "
              "stimmhafter Anteil und der Rest.</p>"
              "<p><b>Rechtsklick auf eine Spaltenüberschrift</b> zeigt sie "
              "alle zum Anhaken, dazu Sortieren und Ausblenden. Spalten "
              "lassen sich per Ziehen in beliebige Reihenfolge bringen, die "
              "bleibt erhalten.</p>"
              "<p><b>Ansicht …</b>, im Hauptfenster markiert, macht dasselbe "
              "in einem Dialog und kann die Liste zusätzlich auf einen "
              "Zeitraum begrenzen. <b>Exportieren …</b> daneben schreibt die "
              "Liste als Text oder CSV.</p>"},

    "intro_help_title": {"en": "What F0, F1 and F2 mean",
                         "de": "Was F0, F1 und F2 bedeuten"},
    "intro_help_body": {
        "en": "<p>The <b>ⓘ</b> at the right end of the toolbar — marked in "
              "the main window right now — opens a reference with nineteen "
              "topics: what F0, the formants, weight and the quality measures "
              "are, and what physically changes them. It stays open beside "
              "the main window, so you can look something up while "
              "recording.</p>"
              "<p>There is a second, smaller ⓘ in front of every single row "
              "of the detail view, marked in the picture below. Hovering it "
              "explains that one metric in two sentences, which is usually "
              "all you need in the moment.</p>"
              "<p><b>Settings</b> holds the analysis parameters, the target "
              "profiles and the design tab — and a button to show this "
              "introduction again.</p>",
        "de": "<p>Das <b>ⓘ</b> am rechten Ende der Leiste — gerade im "
              "Hauptfenster markiert — öffnet ein Nachschlagewerk mit "
              "neunzehn Themen: was F0, die Formanten, die Schwere und die "
              "Qualitätsmaße sind und was sie physikalisch verändert. Es "
              "bleibt neben dem Hauptfenster offen, du kannst also während "
              "der Aufnahme nachschlagen.</p>"
              "<p>Ein zweites, kleineres ⓘ steht vor jeder einzelnen Zeile "
              "der Detailansicht, im Bild unten markiert. Fährst du darüber, "
              "erklärt es diesen einen Kennwert in zwei Sätzen — meistens "
              "genau das, was man im Moment braucht.</p>"
              "<p>Unter <b>Einstellungen</b> liegen die Analyseparameter, die "
              "Zielprofile und der Design-Reiter — und ein Knopf, der diese "
              "Einführung erneut zeigt.</p>"},

    "intro_settings_title": {"en": "What is in the settings",
                             "de": "Was in den Einstellungen steckt"},
    "intro_settings_body": {
        "en": "<p>The <b>⚙ Settings</b> button, marked in the main window, "
              "opens four tabs:</p>"
              "<ul>"
              "<li><b>Analysis</b> — the limits the measurement runs with: "
              "pitch floor and ceiling, formant ceiling, silence threshold and "
              "how much of a take has to be voiced. Templates hold whole sets "
              "of them, so you can switch between a quiet microphone and a "
              "vowel measurement without retyping, and save your own.</li>"
              "<li><b>Target profiles</b> — the ranges each metric is checked "
              "against. The built-in feminine, androgynous and masculine "
              "profiles can be edited and reset, and you can build your own, "
              "including straight from one of your recordings.</li>"
              "<li><b>Design</b> — eight colour themes, a colour picker per "
              "role, a background image and the card opacity.</li>"
              "<li><b>Info</b> — version, links, licence, where your files "
              "live, the debug window with its error counter, and the button "
              "that shows this introduction again.</li>"
              "</ul>"
              "<p>Changing a limit never touches saved recordings: each entry "
              "records the limits it was measured with.</p>",
        "de": "<p>Der Knopf <b>⚙ Einstellungen</b>, im Hauptfenster markiert, "
              "öffnet vier Reiter:</p>"
              "<ul>"
              "<li><b>Analyse</b> — die Grenzen, mit denen gemessen wird: "
              "untere und obere Tonhöhengrenze, Formant-Obergrenze, "
              "Stilleschwelle und wie viel einer Aufnahme stimmhaft sein "
              "muss. Vorlagen speichern ganze Sätze davon, du wechselst also "
              "zwischen leisem Mikrofon und Vokalmessung, ohne alles neu "
              "einzutippen, und legst eigene an.</li>"
              "<li><b>Zielprofile</b> — die Bereiche, gegen die jeder "
              "Kennwert geprüft wird. Die eingebauten Profile feminin, "
              "androgyn und maskulin lassen sich ändern und zurücksetzen, und "
              "du kannst eigene anlegen, auch direkt aus einer deiner "
              "Aufnahmen.</li>"
              "<li><b>Design</b> — acht Farbschemata, ein Farbwähler je "
              "Rolle, ein Hintergrundbild und die Deckkraft der Kacheln.</li>"
              "<li><b>Info</b> — Version, Links, Lizenz, wo deine Dateien "
              "liegen, das Debugfenster mit seinem Fehlerzähler und der "
              "Knopf, der diese Einführung erneut zeigt.</li>"
              "</ul>"
              "<p>Eine geänderte Grenze fasst gespeicherte Aufnahmen nie an: "
              "jeder Eintrag hält fest, mit welchen Grenzen er gemessen "
              "wurde.</p>"},

    "intro_safety_title": {"en": "One thing before you start",
                           "de": "Eine Sache noch"},
    "intro_safety_body": {
        "en": "<p>This is a <b>measuring instrument, not a therapy "
              "programme</b>. It shows what your voice does. It cannot hear "
              "whether you sound good, and it cannot diagnose anything.</p>"
              "<p><b>Never train through pain.</b> If your throat hurts, if it "
              "feels scratchy, or if you are hoarse afterwards: stop. Those "
              "are signs of too much tension, not of effort paying off.</p>"
              "<p>A speech-language pathologist can hear things no software "
              "can. A few sessions save a lot of guessing.</p>",
        "de": "<p>Das hier ist ein <b>Messgerät, kein Therapieprogramm</b>. Es "
              "zeigt, was deine Stimme tut. Es kann nicht hören, ob du gut "
              "klingst, und es diagnostiziert nichts.</p>"
              "<p><b>Trainiere niemals gegen Schmerz.</b> Wenn der Hals "
              "wehtut, wenn es kratzt oder wenn du danach heiser bist: "
              "aufhören. Das sind Zeichen von zu viel Spannung, nicht von "
              "Anstrengung, die sich auszahlt.</p>"
              "<p>Logopädie hört Dinge, die keine Software hört. Ein paar "
              "Stunden ersparen viel Rumprobieren.</p>"},
    "help": {"en": "Help", "de": "Hilfe"},
    "help_title": {"en": "What the numbers mean",
                   "de": "Was die Zahlen bedeuten"},
    "help_tip": {"en": "Look up what a metric means — the program stays usable",
                 "de": "Nachschlagen, was ein Kennwert bedeutet — das Programm "
                       "bleibt nutzbar"},
    "help_search": {"en": "Search …", "de": "Suchen …"},
    "help_count": {"en": "{shown} of {total} topics",
                   "de": "{shown} von {total} Themen"},
    "help_no_match": {"en": "Nothing found.", "de": "Nichts gefunden."},
    "about": {"en": "About", "de": "Info"},
    "about_title": {"en": "About Dream-VoiceTraining",
                    "de": "Über Dream-VoiceTraining"},
    "about_tagline": {
        "en": "Measure what your voice is doing — pitch, resonance, weight and "
              "voice quality — and follow it across months.",
        "de": "Messen, was deine Stimme tut — Tonhöhe, Resonanz, Schwere und "
              "Stimmqualität — und über Monate verfolgen."},
    "about_links": {"en": "Links", "de": "Links"},
    "about_source": {"en": "Source code and issues", "de": "Quelltext und Fehler"},
    "about_discord": {"en": "Discord", "de": "Discord"},
    "about_kofi": {"en": "Support on Ko-fi", "de": "Auf Ko-fi unterstützen"},
    "about_license_head": {"en": "Licence", "de": "Lizenz"},
    "about_license": {
        "en": "GPL-3.0-or-later. Not a free choice: the program links Praat "
              "through Parselmouth, and Praat is GPL-3.0. Qt/PySide6 is LGPL-3.0 "
              "and used unmodified. Full details in THIRD_PARTY_NOTICES.md.",
        "de": "GPL-3.0-or-later. Keine freie Entscheidung: das Programm linkt "
              "Praat über Parselmouth, und Praat steht unter GPL-3.0. Qt/PySide6 "
              "ist LGPL-3.0 und wird unverändert verwendet. Einzelheiten in "
              "THIRD_PARTY_NOTICES.md."},
    "about_privacy_head": {"en": "Network and data", "de": "Netzwerk und Daten"},
    "about_privacy": {
        "en": "The program makes no network connections at all. There is no "
              "telemetry and no update check. Your recordings stay on your "
              "machine as plain WAV and JSON files.",
        "de": "Das Programm baut überhaupt keine Netzwerkverbindungen auf. Es "
              "gibt keine Telemetrie und keine Aktualisierungsprüfung. Deine "
              "Aufnahmen bleiben als reine WAV- und JSON-Dateien auf deinem "
              "Rechner."},
    "about_paths": {"en": "Files", "de": "Dateien"},
    "about_citation": {
        "en": "If you publish measurements made with this, cite Praat (Boersma & "
              "Weenink) and Parselmouth (Jadoul et al., 2018), not this tool.",
        "de": "Wer Messwerte aus diesem Programm veröffentlicht, zitiert bitte "
              "Praat (Boersma & Weenink) und Parselmouth (Jadoul et al., 2018), "
              "nicht dieses Werkzeug."},
    "about_health": {
        "en": "This is a measuring instrument, not a therapy programme, and it "
              "cannot diagnose anything. Never train through pain or hoarseness. "
              "A speech-language pathologist can hear things no software can.",
        "de": "Das hier ist ein Messgerät, kein Therapieprogramm, und es "
              "diagnostiziert nichts. Trainiere niemals gegen Schmerz oder "
              "Heiserkeit. Logopädie hört Dinge, die keine Software hört."},
    "copy_env": {"en": "Copy system info", "de": "Systeminfos kopieren"},
    "copied": {"en": "Copied to clipboard.", "de": "In die Zwischenablage kopiert."},
    "debug": {"en": "Debug", "de": "Debug"},
    "debug_title": {"en": "Debug log", "de": "Fehlerprotokoll"},
    "debug_hint": {
        "en": "Warnings and errors that the program caught instead of crashing. "
              "Empty is the normal state. If something behaves oddly, export "
              "this and attach it to a bug report.",
        "de": "Warnungen und Fehler, die das Programm abgefangen hat, statt "
              "abzustürzen. Leer ist der Normalfall. Wenn sich etwas seltsam "
              "verhält, exportier das hier und häng es an einen Fehlerbericht."},
    "debug_empty": {"en": "Nothing recorded.", "de": "Nichts aufgezeichnet."},
    "debug_clear": {"en": "Clear", "de": "Leeren"},
    "debug_refresh": {"en": "Refresh", "de": "Aktualisieren"},
    "debug_count": {"en": "{count} entries, {errors} of them errors",
                    "de": "{count} Einträge, davon {errors} Fehler"},
    "col_time": {"en": "Time", "de": "Zeit"},
    "col_level_dbg": {"en": "Level", "de": "Stufe"},
    "col_source": {"en": "Source", "de": "Quelle"},
    "col_message": {"en": "Message", "de": "Meldung"},
    "export": {"en": "Export …", "de": "Exportieren …"},
    "export_title": {"en": "Export report", "de": "Bericht exportieren"},
    "export_filter": {"en": "Text file (*.txt);;CSV file (*.csv)",
                      "de": "Textdatei (*.txt);;CSV-Datei (*.csv)"},
    "exported": {"en": "Report written to {path}", "de": "Bericht geschrieben nach {path}"},
    "export_failed": {"en": "Export failed", "de": "Export fehlgeschlagen"},
    "report_title": {"en": "Dream-VoiceTraining — session report",
                     "de": "Dream-VoiceTraining — Sessionbericht"},
    "report_generated": {"en": "Generated", "de": "Erstellt"},
    "report_recording": {"en": "Recording", "de": "Aufnahme"},
    "report_selection": {"en": "Selection", "de": "Auswahl"},
    "report_notes": {"en": "Notes", "de": "Hinweise"},
    "report_explanations": {"en": "Explanations", "de": "Erklärungen"},
    "info_tip": {"en": "What does this mean?", "de": "Was bedeutet das?"},
    "range_join": {"en": "to", "de": "bis"},
    "vowel_only_marker": {"en": "vowel", "de": "Vokal"},
    "vowel_only_note": {
        "en": "Rows marked “vowel” have reference ranges that only apply to a "
              "sustained vowel recording. In connected speech these values are "
              "naturally much higher and say nothing about voice health.",
        "de": "Bei den mit „Vokal“ markierten Zeilen gelten die Zielbereiche nur "
              "für Aufnahmen eines gehaltenen Vokals. In fließender Sprache sind "
              "die Werte naturgemäß viel höher und sagen nichts über die "
              "Stimmgesundheit aus."},

    # --- Profile und Bewertungen ---
    "profile_none": {"en": "no target", "de": "kein Ziel"},
    "profile_masc": {"en": "masculine", "de": "maskulin"},
    "profile_andro": {"en": "androgynous", "de": "androgyn"},
    "profile_fem": {"en": "feminine", "de": "feminin"},
    "verdict_below": {"en": "below", "de": "darunter"},
    "verdict_within": {"en": "within range", "de": "im Bereich"},
    "verdict_above": {"en": "above", "de": "darüber"},
}


def set_language(code: str) -> None:
    global LANG
    if code in LANGUAGES:
        LANG = code


def t(key: str, **kwargs) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(LANG) or entry.get("en") or key
    return text.format(**kwargs) if kwargs else text
