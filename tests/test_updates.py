"""Update-Pruefung gegen GitHub-Releases und das gelbe Versionsschild."""

import io
import json

from core import paths, updates

RELEASE = {
    "tag_name": "v9.1.0",
    "html_url": "https://github.com/yakuda-stack/Dream-VoiceTraining/releases/tag/v9.1.0",
    "body": "## Neu\n- etwas",
    "assets": [
        {"name": "Dream-VoiceTraining-9.1.0-x86_64.AppImage",
         "browser_download_url": "https://example.invalid/a.AppImage"},
        {"name": "Dream-VoiceTraining-9.1.0-x86_64.AppImage.zsync",
         "browser_download_url": "https://example.invalid/a.zsync"},
        {"name": "Dream-VoiceTraining-9.1.0.exe",
         "browser_download_url": "https://example.invalid/setup.exe"},
        {"name": "Dream-VoiceTraining-9.1.0-Portable.exe",
         "browser_download_url": "https://example.invalid/portable.exe"},
    ],
}


def test_versionen_vergleichen():
    assert updates.is_newer("1.2.1", "1.2.0")
    assert updates.is_newer("v1.10.0", "1.9.9")
    assert updates.is_newer("2", "1.9")
    assert not updates.is_newer("1.2.0", "1.2.0")
    assert not updates.is_newer("1.2", "1.2.0")
    assert not updates.is_newer("1.1.9", "1.2.0")
    assert not updates.is_newer("quatsch", "1.2.0")
    assert updates.parse_version("1.3.0_alpha") == (1, 3, 0)


def test_release_lesen():
    release = updates.parse_release(RELEASE)
    assert release.version == "9.1.0"
    assert len(release.assets) == 4
    assert updates.parse_release({**RELEASE, "prerelease": True}) is None
    assert updates.parse_release({**RELEASE, "draft": True}) is None
    assert updates.parse_release({"tag_name": "nightly"}) is None


def test_passender_download():
    release = updates.parse_release(RELEASE)
    assert updates.pick_asset(release, "appimage")[0].endswith(".AppImage")
    assert updates.pick_asset(release, "windows")[0] == "Dream-VoiceTraining-9.1.0.exe"
    assert updates.pick_asset(release, "portable")[0].endswith("-Portable.exe")
    assert updates.pick_asset(release, "aur") is None
    assert updates.pick_asset(release, "source") is None


def test_installationsart(monkeypatch):
    monkeypatch.setenv("APPIMAGE", "/tmp/x.AppImage")
    assert updates.install_kind() == "appimage"


def test_abholen_ohne_netz(monkeypatch):
    def platzt(*a, **k):
        raise OSError("kein Netz")
    monkeypatch.setattr(updates.urllib.request, "urlopen", platzt)
    assert updates.fetch_latest() is None


def test_abholen(monkeypatch):
    class Antwort(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(updates.urllib.request, "urlopen",
                        lambda *a, **k: Antwort(json.dumps(RELEASE).encode()))
    assert updates.fetch_latest().version == "9.1.0"


def test_schild_wird_gelb_und_oeffnet_fenster(intro_window, monkeypatch):
    from ui.update_check import UpdateDialog

    label = intro_window.version_label
    assert label.text() == f"v{paths.APP_VERSION}"
    intro_window._open_update()
    assert not any(isinstance(d, UpdateDialog) for d in intro_window._dialogs)

    monkeypatch.setenv("APPIMAGE", "/tmp/x.AppImage")
    intro_window._update_found(updates.parse_release(RELEASE))
    assert "9.1.0" in label.text()
    intro_window._open_update()
    dialogs = [d for d in intro_window._dialogs if isinstance(d, UpdateDialog)]
    assert len(dialogs) == 1
    assert dialogs[0].btn_download is not None
    # Ein zweiter Klick holt dasselbe Fenster nach vorn.
    intro_window._open_update()
    assert len([d for d in intro_window._dialogs
                if isinstance(d, UpdateDialog)]) == 1
    dialogs[0].close()

    # Ein Neuaufbau (Sprache, Design) laesst das Schild gelb.
    intro_window._build_ui()
    assert "9.1.0" in intro_window.version_label.text()


def test_pruefung_abschaltbar(intro_window, monkeypatch):
    from core import settings

    monkeypatch.setattr(settings, "get_update_check", lambda: False)
    intro_window._update_checker = None
    intro_window.check_for_updates()
    assert intro_window._update_checker is None


def _gespeichert(monkeypatch, start):
    from core import settings

    wert = {"v": start}
    monkeypatch.setattr(settings, "get_update_check", lambda: wert["v"])
    monkeypatch.setattr(settings, "set_update_check",
                        lambda an: wert.__setitem__("v", bool(an)))
    return wert


def _weg(box):
    from PySide6 import QtCore
    box.close()
    QtCore.QCoreApplication.sendPostedEvents(
        None, QtCore.QEvent.Type.DeferredDelete)


def _frage(window):
    return [d for d in window._dialogs if d.objectName() == "update_ask"]


def test_ungefragt_kommt_erst_die_frage(intro_window, monkeypatch):
    from ui import update_check

    wert = _gespeichert(monkeypatch, None)
    gestartet = []
    monkeypatch.setattr(update_check.UpdateChecker, "start",
                        lambda self: gestartet.append(True))

    intro_window.check_for_updates()
    boxen = _frage(intro_window)
    assert len(boxen) == 1 and not gestartet
    # Nicht zweimal fragen.
    intro_window.check_for_updates()
    assert len(_frage(intro_window)) == 1

    box = boxen[0]
    box.btn_yes.click()
    assert wert["v"] is True
    assert gestartet == [True]
    _weg(box)


def test_nein_bleibt_offline(intro_window, monkeypatch):
    from ui import update_check

    wert = _gespeichert(monkeypatch, None)
    monkeypatch.setattr(update_check.UpdateChecker, "start",
                        lambda self: (_ for _ in ()).throw(AssertionError))
    intro_window.check_for_updates()
    box = _frage(intro_window)[0]
    box.btn_no.click()
    assert wert["v"] is False
    _weg(box)
    intro_window.check_for_updates()
    assert not _frage(intro_window)


def test_frage_wartet_auf_die_einfuehrung(intro_window, monkeypatch, qt_app):
    from ui.dialogs import IntroDialog

    _gespeichert(monkeypatch, None)
    intro = IntroDialog(intro_window, ask_language=False)
    intro_window.open_dialog(intro)
    intro_window.check_for_updates()
    assert not _frage(intro_window)
    _weg(intro)


def test_alte_konfiguration_ohne_eintrag_wird_gefragt(tmp_path, monkeypatch):
    import json
    from core import settings

    datei = tmp_path / "config.json"
    datei.write_text(json.dumps({"language": "de"}), encoding="utf-8")
    monkeypatch.setattr(settings, "CONFIG_PATH", datei)
    vorher = settings._state["update_check"]
    try:
        settings.load()
        assert settings.get_update_check() is None
        datei.write_text(json.dumps({"update_check": False}), encoding="utf-8")
        settings.load()
        assert settings.get_update_check() is False
    finally:
        settings._state["update_check"] = vorher


def test_frage_hat_sprachauswahl(intro_window, monkeypatch):
    from core import i18n, settings

    _gespeichert(monkeypatch, None)
    gesetzt = []
    monkeypatch.setattr(settings, "set_language", gesetzt.append)
    intro_window._set_language("en")
    intro_window.check_for_updates()
    box = _frage(intro_window)[0]
    codes = [box.language_box.itemData(i)
             for i in range(box.language_box.count())]
    assert codes == list(i18n.LANGUAGES)

    box.language_box.setCurrentIndex(box.language_box.findData("de"))
    box.language_chosen.emit("de")
    assert i18n.LANG == "de"
    assert box.btn_no.text() == i18n.t("update_ask_no")
    assert "offline" in box.btn_no.text()
    assert intro_window.lang_box.currentData() == "de"
    _weg(box)
    intro_window._set_language("en")
