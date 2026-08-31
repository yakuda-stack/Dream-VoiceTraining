"""Fehlerprotokoll fuer den Debug-Modus.

Sammelt Warnungen, Ausnahmen und alles, was sonst still verschluckt wuerde.
Ohne aktivierten Debug-Modus laeuft nichts anders, es wird nur mitgeschrieben.
"""

from __future__ import annotations

import logging
import platform
import sys
import traceback
from collections import deque
from datetime import datetime

MAX_RECORDS = 500

# (Zeitstempel, Stufe, Quelle, Meldung, Traceback oder "")
RECORDS: deque[tuple[str, str, str, str, str]] = deque(maxlen=MAX_RECORDS)

log = logging.getLogger("dreamvt")


def _add(level: str, source: str, message: str, tb: str = "") -> None:
    RECORDS.append((datetime.now().isoformat(timespec="seconds"),
                    level, source, message, tb))


class _Collector(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        tb = ""
        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info)).rstrip()
        _add(record.levelname, record.name, record.getMessage(), tb)


def record_exception(source: str, exc: BaseException) -> None:
    """Fuer die Stellen, an denen eine Ausnahme bewusst nicht durchschlaegt."""
    _add("ERROR", source, f"{type(exc).__name__}: {exc}",
         "".join(traceback.format_exception(type(exc), exc,
                                            exc.__traceback__)).rstrip())


def record_note(source: str, message: str) -> None:
    _add("INFO", source, message)


def install() -> None:
    """Logging umleiten und unbehandelte Ausnahmen mitschreiben."""
    if any(isinstance(h, _Collector) for h in log.handlers):
        return
    log.setLevel(logging.DEBUG)
    log.addHandler(_Collector())

    previous = sys.excepthook

    def hook(kind, value, tb):
        _add("CRITICAL", "unhandled", f"{kind.__name__}: {value}",
             "".join(traceback.format_exception(kind, value, tb)).rstrip())
        previous(kind, value, tb)

    sys.excepthook = hook


def clear() -> None:
    RECORDS.clear()


def count(level: str | None = None) -> int:
    if level is None:
        return len(RECORDS)
    return sum(1 for r in RECORDS if r[1] == level)


def environment() -> list[str]:
    """Kontext, den man bei einem Fehlerbericht ohnehin immer nachfragt."""
    lines = [
        f"Python      {sys.version.split()[0]}",
        f"Platform    {platform.platform()}",
    ]
    try:
        import paths
        lines.append(f"Version     {paths.APP_VERSION}")
        lines.append(f"Config      {paths.CONFIG_DIR}")
        lines.append(f"Data        {paths.SESSION_DIR}")
    except Exception:
        pass
    for name in ("PySide6", "pyqtgraph", "numpy", "sounddevice", "parselmouth"):
        try:
            module = __import__(name)
            version = getattr(module, "__version__", None) or getattr(
                module, "VERSION", "?")
            lines.append(f"{name:<12}{version}")
        except Exception:
            lines.append(f"{name:<12}not importable")
    return lines


def as_text() -> str:
    out = ["Dream-VoiceTraining — debug log",
           "=" * 34, ""]
    out += environment()
    out += ["", f"{len(RECORDS)} record(s)", ""]
    if not RECORDS:
        out.append("(nothing recorded)")
    for stamp, level, source, message, tb in RECORDS:
        out.append(f"[{stamp}] {level:<8} {source}: {message}")
        if tb:
            out += ["    " + line for line in tb.splitlines()]
        out.append("")
    return "\n".join(out).rstrip() + "\n"
