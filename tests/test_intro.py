"""Erststart-Assistent und portable Erkennung."""

import importlib

import i18n
import settings


def test_erststart_wird_nur_einmal_gezeigt():
    assert settings.get_intro_done() is False
    settings.set_intro_done(True)
    assert settings.get_intro_done() is True
    settings.set_intro_done(False)


def test_merker_ueberlebt_speichern(tmp_path, monkeypatch):
    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "home"))
    import paths
    importlib.reload(paths)
    importlib.reload(settings)

    paths.ensure_dirs()
    settings.set_intro_done(True)
    settings._state["intro_done"] = False
    settings.load()
    assert settings.get_intro_done() is True

    monkeypatch.delenv("DREAM_VOICETRAINING_HOME")
    importlib.reload(paths)
    importlib.reload(settings)


def test_alle_seiten_sind_uebersetzt():
    from dialogs import IntroDialog
    keys = ["intro_title", "intro_language", "intro_language_body",
            "intro_step", "intro_next", "intro_back", "intro_skip",
            "intro_done", "intro_restart"]
    for title_key, body_key in IntroDialog.PAGES:
        keys += [title_key, body_key]
    for key in keys:
        assert key in i18n.STRINGS, key
        for lang in ("en", "de"):
            assert i18n.STRINGS[key][lang].strip(), f"{key}/{lang}"


def test_sicherheitsseite_bleibt_deutlich():
    """Der Hinweis auf Schmerz darf beim Umformulieren nicht verschwinden."""
    for lang, needles in (("en", ("pain", "not a therapy", "hoarse")),
                          ("de", ("schmerz", "kein therapieprogramm", "heiser"))):
        body = i18n.STRINGS["intro_safety_body"][lang].lower()
        for needle in needles:
            assert needle in body, f"{lang}: {needle}"


def test_empfehlung_fuer_die_erste_runde_bleibt_stehen():
    """Ohne den geführten Ablauf ist diese Seite die einzige Anleitung."""
    from dialogs import IntroDialog
    assert ("intro_first_title", "intro_first_body") in IntroDialog.PAGES

    for lang, needles in (("en", ("pitch test", "/a/", "/i/", "/u/")),
                          ("de", ("tonhöhentest", "/a/", "/i/", "/u/"))):
        body = i18n.STRINGS["intro_first_body"][lang].lower()
        for needle in needles:
            assert needle in body, f"{lang}: {needle}"


def test_jedes_bildschirmfoto_wird_mitgeliefert():
    """Fehlt eine Datei, bleibt die Seite stumm — das soll auffallen."""
    import dialogs
    import paths
    from dialogs import IntroDialog
    body_keys = [b for _, b in IntroDialog.PAGES]
    for body_key, name in IntroDialog.SHOTS.items():
        assert body_key in body_keys, body_key
        for lang in ("en", "de"):
            assert paths.intro_shot(f"{name}.{lang}.png") is not None, \
                f"{name}.{lang}.png"

    # Die Stellen der Marken stehen je Sprache daneben.
    spots = dialogs._shot_spots()
    assert spots, "shots.json fehlt"
    for name in IntroDialog.SHOTS.values():
        assert set(spots[name]) == {"en", "de"}, name
        for lang, marks in spots[name].items():
            assert marks, f"{name}/{lang}"
            for share_x, share_y in marks:
                assert 0.0 <= share_x <= 1.0, f"{name}/{lang}"
                assert 0.0 <= share_y <= 1.0, f"{name}/{lang}"


def test_jede_marke_findet_ihr_bedienelement(intro_window):
    """Ein Schluessel ohne Widget waere eine Anleitung, die ins Leere zeigt."""
    from dialogs import IntroDialog
    window = intro_window
    for body_key, key in IntroDialog.POINTS_AT.items():
        assert body_key in [b for _, b in IntroDialog.PAGES], body_key
        target, _ = window._spot_target(key)
        assert target is not None, key

    # Ein unbekannter Schluessel nimmt die Marke weg, statt zu scheitern.
    window.show_spotlight("gibt-es-nicht")
    window.show_spotlight("")


def test_sprachwahl_blaettert_von_allein_weiter(intro_window, qt_app):
    """Die erste Seite hat genau eine Aufgabe, danach geht es weiter."""
    from PySide6 import QtCore
    from dialogs import IntroDialog

    dialog = IntroDialog(intro_window, ask_language=True)
    dialog.show()
    qt_app.processEvents()
    assert dialog.stack.currentIndex() == 0

    dialog._pick_language("de")
    # Der Verzug ist Absicht, damit die Auswahl sichtbar ankommt.
    assert dialog.stack.currentIndex() == 0
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(400, loop.quit)
    loop.exec()
    assert dialog.stack.currentIndex() == 1
    dialog.close()


def test_marke_folgt_den_seiten(intro_window, qt_app):
    from dialogs import IntroDialog

    seen = []
    dialog = IntroDialog(intro_window, ask_language=False)
    dialog.spotlight.connect(seen.append)
    dialog.show()
    qt_app.processEvents()
    dialog._update()          # der Konstruktor hat vor dem Anschluss gemeldet

    for _ in range(len(IntroDialog.PAGES)):
        dialog._next()
    qt_app.processEvents()

    assert "microphone" in seen and "type" in seen and "sessions" in seen
    # Am Ende bleibt keine Marke im Hauptfenster stehen.
    assert seen[-1] == ""
    dialog.close()


def test_jede_marke_ist_am_ende_auch_sichtbar(intro_window, qt_app):
    """Eine Marke auf einem Knopf im Hintergrund erklaert nichts.

    Der Einstellungsknopf liegt im Live-Reiter, die Seite davor blaettert auf
    Sessions — ohne Zurueckschalten versteckt sich die Marke.
    """
    from dialogs import IntroDialog
    window = intro_window
    for key in IntroDialog.POINTS_AT.values():
        window.show_spotlight(key)
        qt_app.processEvents()
        target, _ = window._spot_target(key)
        assert target is not None and target.isVisible(), key
        assert window._spot.isVisible(), key


def test_portable_erkennung(tmp_path, monkeypatch):
    """Portabel heisst: Daten neben der EXE, nicht im Benutzerprofil."""
    import sys

    import paths
    exe = tmp_path / "Dream-VoiceTraining-Portable.exe"
    exe.write_text("x", encoding="utf-8")

    monkeypatch.delenv("DREAM_VOICETRAINING_HOME", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    importlib.reload(paths)

    assert paths.PORTABLE is True
    assert paths.CONFIG_DIR == tmp_path / "Dream-VoiceTraining-Data"
    assert paths.SESSION_DIR.is_relative_to(tmp_path)

    # Ohne Hinweis im Namen und ohne Markerdatei bleibt es normal.
    plain = tmp_path / "Dream-VoiceTraining.exe"
    plain.write_text("x", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(plain))
    importlib.reload(paths)
    assert paths.PORTABLE is False

    # Markerdatei genügt auch bei umbenannter EXE.
    (tmp_path / "portable.txt").write_text("", encoding="utf-8")
    importlib.reload(paths)
    assert paths.PORTABLE is True

    monkeypatch.undo()
    importlib.reload(paths)


def test_ohne_pyinstaller_niemals_portabel():
    import paths
    importlib.reload(paths)
    assert paths.PORTABLE is False


def test_letzte_seite_bringt_die_projektverweise(qt_app):
    """Wer die Einfuehrung durch hat und haengt, soll nicht suchen muessen."""
    import paths
    from dialogs import IntroDialog, PROJECT_LINKS
    from PySide6 import QtWidgets

    urls = [url for _, url in PROJECT_LINKS]
    assert paths.APP_URL in urls
    assert paths.DISCORD_URL in urls
    assert paths.KOFI_URL in urls
    for key, _ in PROJECT_LINKS:
        assert key in i18n.STRINGS, key

    assert IntroDialog.LINK_PAGE == IntroDialog.PAGES[-1][1]

    dialog = IntroDialog(None, ask_language=False)
    last = dialog.stack.widget(dialog.stack.count() - 1)
    box = last.findChild(QtWidgets.QGroupBox, "projectlinks")
    assert box is not None, "Verweise fehlen auf der letzten Seite"

    texts = " ".join(label.text() for label in box.findChildren(QtWidgets.QLabel))
    for url in urls:
        assert f'href="{url}"' in texts, url
    # Das verirrte style=f"..." hat die Angabe frueher unbrauchbar gemacht.
    assert 'style=f"' not in texts
    dialog.close()
