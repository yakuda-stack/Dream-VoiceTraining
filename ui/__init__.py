"""Oberflaeche: Dialoge, Designs, Hilfetexte."""

import os

# pyqtgraph waehlt sein Qt-Binding beim ersten Import. Hier festlegen, bevor
# irgendein Modul unter ui/ es importiert (Begruendung in main.py).
os.environ.setdefault("PYQTGRAPH_QT_LIB", "PySide6")
