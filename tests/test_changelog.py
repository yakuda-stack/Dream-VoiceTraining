"""Das Changelog-Fenster: Knopf, Markdown, Netz und Rueckfall."""

import pytest

import paths


@pytest.fixture
def kein_netz(monkeypatch):
    """Jeder Abruf scheitert — so sieht ein Rechner ohne Verbindung aus."""
    import dialogs

    def platzt(*args, **kwargs):
        raise OSError("kein Netz")

    monkeypatch.setattr(dialogs.urllib.request, "urlopen", platzt)


@pytest.fixture
def netz(monkeypatch):
    """Ein Abruf, der eine erfundene Fassung zurueckgibt."""
    import dialogs

    class Antwort:
        def __init__(self, text):
            self._text = text.encode("utf-8")

        def read(self, size=None):
            return self._text[:size] if size else self._text

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def hole(request, timeout=None):
        return Antwort("# Changelog\n\n## [9.9.9] — 2099-01-01\n\n"
                       "- Aus dem Netz geladen\n")

    monkeypatch.setattr(dialogs.urllib.request, "urlopen", hole)


def warte(qt_app, dialog, sekunden=10):
    """Auf den Ladefaden warten, ohne die Oberflaeche einzufrieren."""
    from PySide6 import QtCore

    loop = QtCore.QEventLoop()
    dialog._loader.done.connect(lambda *_: QtCore.QTimer.singleShot(20,
                                                                    loop.quit))
    QtCore.QTimer.singleShot(int(sekunden * 1000), loop.quit)
    loop.exec()
    qt_app.processEvents()


# ------------------------------------------------------------------- Knopf

def test_info_reiter_hat_einen_changelog_knopf(qt_app):
    import i18n
    from dialogs import InfoPage

    page = InfoPage()
    try:
        for lang in ("en", "de"):
            i18n.set_language(lang)
            assert i18n.t("changelog") in InfoPage().btn_changelog.text(), lang
        i18n.set_language("en")
        assert page.btn_changelog.isEnabled()
    finally:
        page.deleteLater()


def test_knopf_oeffnet_das_fenster(qt_app, kein_netz):
    """Der Knopf im Reiter muss beim Dialog ankommen, nicht nur existieren."""
    from dialogs import ChangelogDialog, SettingsDialog

    dialog = SettingsDialog(entries=[])
    try:
        dialog.info.btn_changelog.click()
        qt_app.processEvents()
        fenster = [w for w in qt_app.topLevelWidgets()
                   if isinstance(w, ChangelogDialog)]
        assert fenster, "kein Changelog-Fenster aufgegangen"
        for w in fenster:
            warte(qt_app, w)
            w.close()
    finally:
        dialog.deleteLater()


# -------------------------------------------------------------- Herkunft

def test_lokale_fassung_wenn_kein_netz_da_ist(qt_app, kein_netz):
    import i18n
    from dialogs import ChangelogDialog

    dialog = ChangelogDialog()
    try:
        warte(qt_app, dialog)
        assert dialog.source.text() == i18n.t("changelog_from_disk")
        assert "Changelog" in dialog.view.toPlainText()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_netz_gewinnt_gegen_die_mitgelieferte_datei(qt_app, netz):
    """Die lokale Datei endet bei der eigenen Version, das Netz nicht."""
    import i18n
    from dialogs import ChangelogDialog

    dialog = ChangelogDialog()
    try:
        warte(qt_app, dialog)
        assert dialog.source.text() == i18n.t("changelog_from_web")
        assert "9.9.9" in dialog.view.toPlainText()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_ohne_netz_und_ohne_datei_bleibt_das_fenster_stehen(qt_app, kein_netz,
                                                           monkeypatch):
    import i18n
    from dialogs import ChangelogDialog

    monkeypatch.setattr(paths, "changelog_file", lambda: None)
    dialog = ChangelogDialog()
    try:
        warte(qt_app, dialog)
        assert dialog.source.text() == i18n.t("changelog_from_nowhere")
        assert dialog.view.toPlainText().strip()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_eine_fehlerseite_gilt_nicht_als_changelog(qt_app, monkeypatch):
    """404-Text faengt nicht mit # an und darf nicht durchgehen."""
    import dialogs

    class Antwort:
        def read(self, size=None):
            return b"404: Not Found"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(dialogs.urllib.request, "urlopen",
                        lambda *a, **k: Antwort())
    assert dialogs.ChangelogLoader(online=True)._from_web() == ""


# -------------------------------------------------------------- Darstellung

def test_markdown_wird_gesetzt_und_nicht_als_rohtext_gezeigt(qt_app,
                                                             kein_netz):
    from dialogs import ChangelogDialog

    dialog = ChangelogDialog()
    try:
        warte(qt_app, dialog)
        text = dialog.view.toPlainText()
        # Waere der Text roh, stuenden die Rautezeichen noch drin.
        assert "# Changelog" not in text
        assert text.startswith("Changelog")

        doc = dialog.view.document()
        ebenen = set()
        listen = 0
        block = doc.begin()
        while block.isValid():
            ebenen.add(block.blockFormat().headingLevel())
            listen += block.textList() is not None
            block = block.next()
        assert {1, 2, 3} <= ebenen, "Ueberschriften fehlen"
        assert listen > 5, "Aufzaehlungen fehlen"
    finally:
        dialog.close()
        dialog.deleteLater()


def test_ueberschriften_sind_groesser_als_fliesstext(qt_app, kein_netz):
    """Markdown wird gesetzt, nicht nur geparst.

    Gemessen an einem kurzen eigenen Text: im echten Changelog brechen
    Absaetze um und tragen Listeneinzuege, da sagt die Hoehe eines Blocks
    nichts mehr ueber die Schriftgroesse.
    """
    from dialogs import ChangelogDialog

    dialog = ChangelogDialog()
    dialog.resize(900, 400)
    try:
        warte(qt_app, dialog)
        dialog.view.setMarkdown("# Eins\n\nText\n\n## Zwei\n")
        doc = dialog.view.document()
        doc.setTextWidth(880)
        layout = doc.documentLayout()

        hoehen = {}
        block = doc.begin()
        while block.isValid():
            if block.text().strip():
                hoehen[block.blockFormat().headingLevel()] = \
                    layout.blockBoundingRect(block).height()
            block = block.next()
        assert hoehen[1] > hoehen[2] > hoehen[0], hoehen
    finally:
        dialog.close()
        dialog.deleteLater()


def test_das_fenster_scrollt(qt_app, kein_netz):
    """Ein Changelog ist laenger als jedes Fenster."""
    from dialogs import ChangelogDialog

    dialog = ChangelogDialog()
    dialog.resize(600, 400)
    dialog.show()
    try:
        warte(qt_app, dialog)
        qt_app.processEvents()
        assert dialog.view.verticalScrollBar().maximum() > 0
    finally:
        dialog.close()
        dialog.deleteLater()


# ------------------------------------------------------------- Auslieferung

def test_die_mitgelieferte_datei_wird_gefunden():
    """Sonst faellt das Fenster ohne Netz ins Leere."""
    path = paths.changelog_file()
    assert path is not None and path.is_file()
    assert path.read_text(encoding="utf-8").lstrip().startswith("# Changelog")


def test_alle_pakete_bringen_den_changelog_mit():
    """Ein Rueckfall, der nur im Quellordner liegt, ist keiner."""
    from pathlib import Path

    root = Path(paths.__file__).resolve().parent
    for datei in ("packaging/PKGBUILD",
                  "packaging/build-appimage.sh",
                  "packaging/windows/dream-voicetraining.spec"):
        text = (root / datei).read_text(encoding="utf-8")
        assert "CHANGELOG.md" in text, datei


def test_die_raw_adressen_zeigen_auf_das_projekt():
    assert paths.CHANGELOG_URLS
    for url in paths.CHANGELOG_URLS:
        assert url.startswith("https://raw.githubusercontent.com/")
        assert url.endswith("/CHANGELOG.md")


def test_alle_texte_gibt_es_in_beiden_sprachen():
    import i18n

    keys = [key for key in i18n.STRINGS if key.startswith("changelog")]
    assert len(keys) >= 8
    for key in keys:
        for lang in ("en", "de"):
            assert i18n.STRINGS[key].get(lang, "").strip(), f"{key}/{lang}"
