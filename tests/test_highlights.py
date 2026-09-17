"""Highlights-Knopf, eigene Datei und die zweite Zeile unter den Links."""

import pytest

from core import paths
from test_changelog import kein_netz, netz, warte  # noqa: F401


def test_info_reiter_hat_einen_highlights_knopf(qt_app):
    from core import i18n
    from ui.dialogs import InfoPage

    for lang in ("en", "de"):
        i18n.set_language(lang)
        page = InfoPage()
        try:
            assert i18n.t("highlights") in page.btn_highlights.text(), lang
        finally:
            page.deleteLater()
    i18n.set_language("en")


def test_changelog_und_highlights_sind_zweite_zeile_der_links(qt_app):
    """Beide Knoepfe sitzen im Links-Kasten, unter den drei Verweisen."""
    from PySide6 import QtWidgets
    from ui.dialogs import InfoPage, PROJECT_LINKS

    page = InfoPage()
    try:
        box = page.findChild(QtWidgets.QGroupBox, "projectlinks")
        assert box is not None
        outer = box.layout()
        assert isinstance(outer, QtWidgets.QVBoxLayout)
        assert outer.count() == 2

        def knoepfe(row):
            lay = outer.itemAt(row).layout()
            return [lay.itemAt(i).widget() for i in range(lay.count())
                    if lay.itemAt(i).widget() is not None]

        assert len(knoepfe(0)) == len(PROJECT_LINKS)
        assert knoepfe(1) == [page.btn_changelog, page.btn_highlights]
    finally:
        page.deleteLater()


def test_changelog_nicht_mehr_in_der_oberen_zeile(qt_app):
    from PySide6 import QtWidgets
    from ui.dialogs import InfoPage

    page = InfoPage()
    try:
        oben = page.layout().itemAt(1).layout()
        widgets = [oben.itemAt(i).widget() for i in range(oben.count())]
        assert page.btn_changelog not in widgets
        assert page.btn_highlights not in widgets
        assert page.btn_intro in widgets
    finally:
        page.deleteLater()


def test_einfuehrung_zeigt_weiter_nur_die_links(qt_app):
    from PySide6 import QtWidgets
    from ui import dialogs

    box = dialogs.project_links_box()
    try:
        assert len(box.findChildren(QtWidgets.QPushButton)) == \
            len(dialogs.PROJECT_LINKS)
    finally:
        box.deleteLater()


def test_knopf_oeffnet_das_highlights_fenster(qt_app, kein_netz):
    from ui.dialogs import HighlightsDialog, SettingsDialog

    dialog = SettingsDialog(entries=[])
    try:
        dialog.info.btn_highlights.click()
        qt_app.processEvents()
        fenster = [w for w in qt_app.topLevelWidgets()
                   if isinstance(w, HighlightsDialog)]
        assert fenster, "kein Highlights-Fenster aufgegangen"
        for w in fenster:
            warte(qt_app, w)
            w.close()
    finally:
        dialog.deleteLater()


def test_highlights_kommen_aus_der_eigenen_datei(qt_app, kein_netz):
    from core import i18n
    from ui.dialogs import HighlightsDialog

    dialog = HighlightsDialog()
    try:
        warte(qt_app, dialog)
        assert dialog.source.text() == i18n.t("changelog_from_disk")
        text = dialog.view.toPlainText()
        assert text.startswith("Highlights")
        assert paths.APP_VERSION in text
        assert dialog.windowTitle() == i18n.t("highlights_title")
    finally:
        dialog.close()
        dialog.deleteLater()


def test_ohne_datei_meldet_das_highlights_fenster_das(qt_app, kein_netz,
                                                     monkeypatch):
    from core import i18n
    from ui.dialogs import HighlightsDialog

    monkeypatch.setattr(paths, "highlights_file", lambda: None)
    dialog = HighlightsDialog()
    try:
        warte(qt_app, dialog)
        assert dialog.source.text() == i18n.t("changelog_from_nowhere")
        assert i18n.t("highlights_missing").split("\n")[0].lstrip("# ") \
            in dialog.view.toPlainText()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_highlights_laden_ihre_eigenen_adressen(monkeypatch):
    from ui import dialogs

    gefragt = []

    def hole(request, timeout=None):
        gefragt.append(request.full_url)
        raise OSError("kein Netz")

    monkeypatch.setattr(dialogs.urllib.request, "urlopen", hole)
    loader = dialogs.ChangelogLoader(online=True,
                                     urls=dialogs.HighlightsDialog._urls)
    assert loader._from_web() == ""
    assert gefragt == list(paths.HIGHLIGHTS_URLS)
    for url in gefragt:
        assert url.endswith("/HIGHLIGHTS.md")


def test_die_highlights_datei_passt_zur_version():
    """Wer die Version anhebt, muss auch die Highlights ergaenzen."""
    path = paths.highlights_file()
    assert path is not None and path.is_file()
    text = path.read_text(encoding="utf-8")
    assert text.lstrip().startswith("# Highlights")
    erste = next(line for line in text.splitlines() if line.startswith("## "))
    assert erste.startswith(f"## {paths.APP_VERSION}"), erste


def test_alle_pakete_bringen_die_highlights_mit():
    from pathlib import Path

    root = paths.SOURCE_DIR
    for datei in ("packaging/PKGBUILD",
                  "packaging/build-appimage.sh",
                  "packaging/windows/dream-voicetraining.spec"):
        text = (root / datei).read_text(encoding="utf-8")
        assert "HIGHLIGHTS.md" in text, datei


def test_versionen_stimmen_ueberein():
    """paths.py, PKGBUILD, CHANGELOG und READMEs zeigen dieselbe Version."""
    import re
    from pathlib import Path

    root = paths.SOURCE_DIR
    v = paths.APP_VERSION
    pkgbuild = (root / "packaging/PKGBUILD").read_text(encoding="utf-8")
    assert f"pkgver={v}\n" in pkgbuild
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(r"^## \[(.+?)\]", changelog, re.M).group(1) == v
    for readme in ("README.md", "README.de.md"):
        text = (root / readme).read_text(encoding="utf-8")
        assert f"/download/v{v}/" in text, readme
        assert paths.DISCORD_URL in text, readme


def test_highlights_texte_in_beiden_sprachen():
    from core import i18n

    for key in ("highlights", "highlights_title", "highlights_missing"):
        for lang in ("en", "de"):
            assert i18n.STRINGS[key].get(lang, "").strip(), f"{key}/{lang}"


def test_neue_knoepfe_haben_einen_stil():
    from ui import theming

    qss = theming.stylesheet()
    assert "#btn_link_changelog" in qss
    assert "#btn_link_highlights:hover" in qss
