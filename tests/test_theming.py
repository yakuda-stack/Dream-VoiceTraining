"""Farbschema, Vorlagen und Stylesheet."""

import i18n
import theming


def test_alle_vorlagen_haben_alle_rollen():
    for name, colors in theming.PRESETS.items():
        missing = [key for key in theming.ROLE_KEYS if key not in colors]
        assert not missing, f"{name}: {missing}"


def test_alle_farben_sind_gueltige_hexwerte():
    for name, colors in theming.PRESETS.items():
        for key, value in colors.items():
            assert value.startswith("#") and len(value) == 7, f"{name}.{key}"
            int(value[1:], 16)


def test_rollen_sind_uebersetzt():
    for role in theming.ROLES:
        for lang in ("en", "de"):
            i18n.set_language(lang)
            assert role.label.strip(), role.key
    for name in theming.PRESETS:
        assert f"theme_{name}" in i18n.STRINGS, name
    i18n.set_language("en")


def test_text_bleibt_lesbar():
    """Auf hellen Flächen darf keine helle Schrift landen."""
    for name, colors in theming.PRESETS.items():
        assert theming.is_light(colors["fg"]), f"{name}: Text zu dunkel"
        assert not theming.is_light(colors["bg"]), f"{name}: Fenster zu hell"
    assert theming.contrast_text("#ffffff") == "#101010"
    assert theming.contrast_text("#000000") != "#101010"


def test_vorlage_wechseln_und_zuruecksetzen():
    theming.use_preset("ocean")
    assert theming.COLORS["accent"] == theming.PRESETS["ocean"]["accent"]
    assert theming.deviates_from_preset() is False

    theming.apply(colors={"accent": "#ff0000"})
    assert theming.deviates_from_preset() is True

    theming.reset_colors()
    assert theming.COLORS["accent"] == theming.PRESETS["ocean"]["accent"]
    theming.use_preset("default")


def test_farbtabelle_bleibt_dasselbe_objekt():
    """Module halten eine Referenz; ein Wechsel darf sie nicht ersetzen."""
    reference = theming.COLORS
    theming.use_preset("rose")
    assert theming.COLORS is reference
    assert reference["accent"] == theming.PRESETS["rose"]["accent"]
    theming.use_preset("default")


def test_stylesheet_enthaelt_die_aktiven_farben():
    theming.use_preset("nebula")
    sheet = theming.stylesheet()
    for key in ("accent", "bg", "bg2", "fg"):
        assert theming.COLORS[key] in sheet, key
    assert "{" not in sheet.replace("{{", "").split("QWidget")[0]
    theming.use_preset("default")


def test_deckkraft_wirkt_nur_mit_bild():
    theming.apply(bg_image=None, opacity=50)
    assert "rgba" not in theming.stylesheet()
    theming.apply(bg_image="/tmp/x.png")
    assert "rgba" in theming.stylesheet()
    theming.apply(bg_image=None, opacity=100)


def test_deckkraft_wird_begrenzt():
    theming.apply(opacity=5)
    assert theming.card_opacity() == 20
    theming.apply(opacity=500)
    assert theming.card_opacity() == 100


def test_zustand_ueberlebt_speichern_und_laden():
    theming.use_preset("embers")
    theming.apply(colors={"accent": "#123456"}, bg_image="/tmp/bild.png",
                  opacity=70)
    data = theming.snapshot()

    theming.use_preset("default")
    theming.apply(bg_image=None, opacity=100)
    theming.restore(data)

    assert theming.preset_name() == "embers"
    assert theming.COLORS["accent"] == "#123456"
    assert theming.background() == "/tmp/bild.png"
    assert theming.card_opacity() == 70

    theming.use_preset("default")
    theming.apply(bg_image=None, opacity=100)


def test_defekter_zustand_kippt_nichts():
    theming.restore({"preset": "gibt-es-nicht", "colors": "kein dict"})
    assert theming.COLORS["accent"] == theming.PRESETS["default"]["accent"]
    theming.restore(None)
    theming.restore({})


def test_versionsschild_entsteht_nur_einmal(monkeypatch, tmp_path):
    """Regression: die Statusleiste überlebt den Neuaufbau der Reiter, das
    Schild wurde bei jedem Sprach- oder Themenwechsel erneut angehängt."""
    from PySide6 import QtWidgets

    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "home"))
    import audio
    monkeypatch.setattr(audio, "_run", lambda args: None)

    import importlib
    import paths
    importlib.reload(paths)
    import main

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = main.MainWindow()

    def labels():
        return [w.text() for w in window.status.findChildren(QtWidgets.QLabel)
                if w.text().startswith("v")]

    assert labels() == [f"v{paths.APP_VERSION}"]
    window._set_language("de")
    window._set_language("en")
    theming.use_preset("ocean")
    window.apply_theme()
    app.processEvents()
    assert labels() == [f"v{paths.APP_VERSION}"]

    window.close()
    theming.use_preset("default")
    importlib.reload(paths)


def test_keine_verschluckten_css_klammern():
    """Regression: sobald {NORD['x']} in ein Stylesheet kommt, wird der String
    zum f-String und die CSS-Klammern müssen verdoppelt werden. Sonst liest
    Python "{ color: ...}" als Ausdruck mit Formatangabe — das kompiliert und
    scheitert erst, wenn das Widget gebaut wird."""
    import ast
    import pathlib

    def literal_parts(node):
        """Nur die festen Textteile; {{ steht darin bereits als {."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return "".join(literal_parts(part) for part in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return literal_parts(node.left) + literal_parts(node.right)
        return ""

    root = pathlib.Path(__file__).resolve().parents[1]
    problems = []

    for path in sorted(root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "setStyleSheet"):
                continue
            for argument in node.args:
                text = literal_parts(argument)
                if not text.strip():
                    continue
                # Ein Stylesheet mit Selektor braucht Klammern; fehlen sie im
                # Literal, hat der f-String sie als Ausdruck geschluckt.
                selector = any(word in text for word in
                               ("QPushButton", "QToolButton", "QLabel",
                                "QWidget", "QFrame", "QProgressBar",
                                "QTableWidget", "QGroupBox", "QComboBox"))
                if text.count("{") != text.count("}"):
                    problems.append(f"{path.name}:{node.lineno} (unpaarig)")
                elif selector and "{" not in text:
                    # Der Selektor steht da, die Klammer nicht — Python hat sie
                    # als Formatangabe verschluckt.
                    problems.append(f"{path.name}:{node.lineno} (Klammer fehlt)")

    assert not problems, "verschluckte CSS-Klammern in: " + ", ".join(problems)


def test_jeder_dialog_laesst_sich_bauen(monkeypatch, tmp_path):
    """Regression: ein Stylesheet mit falsch maskierten Klammern fällt erst
    beim Öffnen des Dialogs auf, nicht beim Importieren."""
    from PySide6 import QtWidgets

    monkeypatch.setenv("DREAM_VOICETRAINING_HOME", str(tmp_path / "home"))
    import audio
    monkeypatch.setattr(audio, "_run", lambda args: None)

    import importlib
    import paths
    importlib.reload(paths)
    import dialogs
    import main

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setStyleSheet(theming.stylesheet())
    window = main.MainWindow()

    entry = {"timestamp": "2026-09-01T10:00:00", "file": "a.wav",
             "type": "reading", "quality": "ok", "duration": 20.0,
             "peak_db": -22.0, "f0_median": 120.0, "f0_p10": 90.0,
             "f0_p90": 160.0}
    window.sessions = [entry]
    window._fill_session_table()

    built = [
        dialogs.SettingsDialog(window),
        dialogs.SessionDetailDialog(entry, [entry], paths.SESSION_DIR, window),
        dialogs.FilterDialog(window.view, window),
        dialogs.DebugDialog(window),
        dialogs.AboutDialog(window),
        dialogs.DesignEditor(),
        dialogs.ProfileEditor(),
        dialogs.GuidedPanel(window.engine, window.store_recording, window),
    ]
    for widget in built:
        widget.show()
    app.processEvents()

    # Der erweiterte Bereich baut seine Stile erst beim Aufklappen.
    detail = built[1]
    detail.btn_advanced.setChecked(True)
    app.processEvents()

    for widget in built:
        widget.close()
    window.close()
    importlib.reload(paths)


def test_keine_falsch_maskierten_klammern_in_stylesheets():
    """Sucht f-Strings, in denen eine CSS-Klammer nicht verdoppelt wurde."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    broken = []
    for name in ("main.py", "dialogs.py", "theming.py"):
        for number, line in enumerate(
                (root / name).read_text(encoding="utf-8").splitlines(), 1):
            for match in re.finditer(r'''[fF](["'])(.*?)\1''', line):
                body = match.group(2).replace("{{", "\x00").replace("}}", "\x01")
                # {name} ist eine Einsetzung, "{ color:" dagegen CSS.
                if re.search(r"\{\s*[a-zA-Z-]+\s*:\s", body):
                    broken.append(f"{name}:{number}")
    assert not broken, f"CSS-Klammern nicht verdoppelt: {broken}"
