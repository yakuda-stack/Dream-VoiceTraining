# Changelog

All notable changes are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/). Versions follow
[Semantic Versioning](https://semver.org/).

Alle Änderungen sind hier dokumentiert, englisch und deutsch.

## [1.0.0] — unreleased

### Added / Neu

- **EN** — Live view with pitch (F0), first two formants, level meter, a
  scrolling spectrogram with F1/F2 markers and a 30 second pitch history.
- **EN** — Session recording with a persistent history, per-session metrics
  and playback.
- **EN** — Detail view per recording with 18 metrics, selectable target
  profile (masculine / androgynous / feminine), comparison against any other
  recording, per-metric explanations and text/CSV export.
- **EN** — Advanced mode: waveform with a draggable region, so a single
  sustained vowel can be isolated from a longer take and analysed on its own.
- **EN** — Settings dialog with runtime-adjustable analysis parameters and
  six built-in templates plus user-defined ones.
- **EN** — English and German interface, switchable at runtime.
- **EN** — Readable PipeWire/PulseAudio device names via `pactl`, grouped
  into microphones, virtual sources and monitors.
- **EN** — `diag.py` for diagnosing capture problems from the terminal.

- **DE** — Live-Ansicht mit Tonhöhe (F0), den ersten beiden Formanten,
  Pegelanzeige, scrollendem Spektrogramm mit F1/F2-Markierung und
  30-Sekunden-Verlauf.
- **DE** — Aufnahmen mit dauerhafter Historie, Kennwerten je Session und
  Wiedergabe.
- **DE** — Detailansicht je Aufnahme mit 18 Kennwerten, wählbarem Zielprofil
  (maskulin / androgyn / feminin), Vergleich gegen jede andere Aufnahme,
  Erklärungen zu jedem Wert und Export als Text oder CSV.
- **DE** — Erweiterter Modus: Wellenform mit ziehbarem Bereich, um einen
  einzelnen gehaltenen Vokal aus einer längeren Aufnahme herauszulösen.
- **DE** — Einstellungsdialog mit zur Laufzeit änderbaren Analyseparametern,
  sechs eingebauten Vorlagen und eigenen.
- **DE** — Englische und deutsche Oberfläche, im Betrieb umschaltbar.
- **DE** — Lesbare PipeWire-/PulseAudio-Gerätenamen über `pactl`, gruppiert
  nach Mikrofonen, virtuellen Quellen und Monitoren.
- **DE** — `diag.py` zur Diagnose von Aufnahmeproblemen im Terminal.

- **EN** — Session list: click a column header to sort, click again to
  reverse. Right-click a row for details, playback, rename or delete. A view
  dialog controls which of the 23 available columns are shown, how the list is
  sorted and whether a date range is applied. The list exports to text or CSV.
- **EN** — Right-clicking a column header offers sorting, hiding that column,
  a checkable list of all columns and a shortcut into the view dialog, which
  now has an Apply button that updates the list without closing. Columns can
  also be dragged into any order directly in the header; the order is stored.
- **EN** — About dialog in the settings, with version, licence summary,
  links to source, Discord and Ko-fi, the file locations and a button that
  copies the system information for bug reports. No update check: the program
  makes no network connections.
- **EN** — Debug window (reachable from the settings dialog) collecting warnings and caught exceptions with
  tracebacks and environment details, exportable as a text file.
- **EN** — Exports ask which language to write when the interface is German;
  an English interface exports English without asking.

- **DE** — Sessionliste: Klick auf eine Spaltenüberschrift sortiert, erneuter
  Klick dreht um. Rechtsklick auf eine Zeile für Details, Wiedergabe,
  Umbenennen oder Löschen. Ein Ansichtsdialog steuert, welche der 23
  verfügbaren Spalten sichtbar sind, wonach sortiert wird und ob ein Zeitraum
  gilt. Die Liste lässt sich als Text oder CSV exportieren.
- **DE** — Rechtsklick auf eine Spaltenüberschrift bietet Sortieren, diese
  Spalte ausblenden, eine Liste aller Spalten zum Anhaken und den Sprung in
  den Ansichtsdialog, der jetzt einen Übernehmen-Knopf hat und die Liste
  aktualisiert, ohne sich zu schließen. Spalten lassen sich außerdem direkt in
  der Kopfzeile in beliebige Reihenfolge ziehen; die Reihenfolge wird
  gespeichert.
- **DE** — Infofenster in den Einstellungen, mit Version, Lizenzübersicht,
  Links zu Quelltext, Discord und Ko-fi, den Ablageorten und einem Knopf, der
  die Systeminfos für Fehlerberichte kopiert. Ohne Aktualisierungsprüfung, das
  Programm baut keine Netzwerkverbindungen auf.
- **DE** — Debugfenster, erreichbar über den Einstellungsdialog, das Warnungen und abgefangene Ausnahmen mit
  Traceback und Umgebungsangaben sammelt, exportierbar als Textdatei.
- **DE** — Exporte fragen bei deutscher Oberfläche nach der Sprache; bei
  englischer Oberfläche wird ohne Rückfrage englisch geschrieben.

- **EN** — Recording types: reading text, pitch test (a held hum), /a/, /i/,
  /u/ and free. Picked before recording, shown and sortable as a column, and
  the basis for comparing like with like later on.
- **EN** — Recording type can be changed afterwards, from the row context menu
  or the detail view.
- **EN** — Live view also shows weight (H1–H2), and each readout turns green
  or amber against the target profile you picked, so you can see while
  speaking whether you are inside your range.
- **EN** — Guided run: a toggle, off by default, that shows a panel in the
  Live tab rather than a window, styled like the other sections. It walks through hum, /a/, /i/ and /u/
  with a countdown, trims each take to its steadiest stretch and files it
  under the right type. A popup in the middle of the screen pulls you out of
  holding a sound, so everything stays in one place with the readouts and the
  spectrogram still running beside it.
- **EN** — Level hint while recording: after three seconds without a usable
  peak the status bar says so. Checking at the moment Record is pressed would
  be pointless — nobody has spoken yet.
- **EN** — Target profiles are now a proper feature: a dropdown in the Live
  toolbar picks the target voice, and a dedicated tab in the settings lets you
  edit the ranges per metric and save them under your own name. The three
  built-in profiles can be adjusted too: Save keeps your version, Save as
  makes a separate profile, and Reset brings back the values from the
  literature at any time.
  Any recording can still seed a profile via “use these values as my target”.
- **EN** — Icon redesigned and shipped as SVG plus PNG from 16 to 512 pixels;
  the window and task manager now show the program name and icon rather than
  python3.

- **DE** — Aufnahmetypen: Lesetext, Tonhöhentest (gehaltenes Summen), /a/,
  /i/, /u/ und frei. Vor der Aufnahme wählbar, als Spalte sicht- und
  sortierbar, und die Grundlage dafür, später Gleiches mit Gleichem zu
  vergleichen.
- **DE** — Der Aufnahmetyp lässt sich nachträglich ändern, über das
  Kontextmenü der Zeile oder in der Detailansicht.
- **DE** — Geführter Ablauf: ein Umschalter führt mit Countdown durch Summen, /a/,
  /i/ und /u/, kürzt jede Aufnahme automatisch auf ihren ruhigsten Abschnitt
  und legt sie unter dem passenden Typ ab.
- **DE** — Pegelhinweis während der Aufnahme: bleibt der Ausschlag drei
  Sekunden lang zu klein, sagt es die Statuszeile. Eine Prüfung im Moment des
  Klicks wäre sinnlos, da hat noch niemand gesprochen.
- **DE** — Zielprofile sind jetzt eine richtige Funktion: ein Dropdown in der
  Live-Leiste wählt die Zielstimme, und ein eigener Reiter in den
  Einstellungen lässt die Bereiche je Kennwert bearbeiten und unter eigenem
  Namen sichern. Auch die eingebauten lassen sich anpassen: Speichern behält
  deine Fassung, Speichern unter legt ein eigenes Profil an, und Zurücksetzen
  holt die Literaturwerte jederzeit zurück. Eine beliebige Aufnahme kann weiterhin über
  „Diese Werte als mein Ziel übernehmen“ ein Profil füllen.
- **DE** — Icon neu gezeichnet, als SVG und als PNG von 16 bis 512 Pixel
  ausgeliefert; Fenster und Systemmonitor zeigen jetzt Programmnamen und
  Symbol statt python3.

- **EN** — One-line installer at the repository root that detects Debian,
  Ubuntu, Fedora, Arch, CachyOS and openSUSE, installs the system packages
  that have no Python equivalent, sets up its own environment and adds a menu
  entry. `--uninstall` removes it again and keeps your recordings.

- **DE** — Installationsskript im Wurzelverzeichnis, das Debian, Ubuntu,
  Fedora, Arch, CachyOS und openSUSE erkennt, die Systempakete ohne
  Python-Entsprechung nachinstalliert, eine eigene Umgebung anlegt und einen
  Menüeintrag einträgt. `--uninstall` entfernt alles wieder und lässt die
  Aufnahmen stehen.

### Changed / Geändert

- **EN** — The Live view starts with no target selected. A colour changing
  while you speak pulls attention to the screen, and that is attention taken
  off your voice. The detail view keeps its own selection and still defaults
  to feminine.
- **EN** — The guided-run button lights up in a brighter blue while active.
- **EN** — README reworked with screenshots.

- **DE** — Die Live-Ansicht startet ohne gewähltes Ziel. Eine Farbe, die sich
  beim Sprechen ändert, zieht die Aufmerksamkeit auf den Bildschirm, und die
  fehlt dann bei der Stimme. Die Detailansicht hat ihre eigene Auswahl und
  steht weiterhin auf feminin.
- **DE** — Der Knopf für den geführten Ablauf leuchtet im aktiven Zustand in
  einem helleren Blau.
- **DE** — README überarbeitet, mit Screenshots.

- **EN** — Target profiles cover all eighteen metrics, not just six. H1 and H2
  can be targeted separately, as can HNR, jitter, shimmer and the recording
  level. A profile entry now takes precedence over the built-in quality range
  for that metric.
- **EN** — The session list starts with date, name, type, F0 median and range,
  intonation width, F2, F3, H1, H2, jitter and shimmer.

- **DE** — Zielprofile umfassen alle achtzehn Kennwerte statt nur sechs. H1
  und H2 lassen sich einzeln festlegen, ebenso HNR, Jitter, Shimmer und der
  Aufnahmepegel. Ein Profileintrag geht der eingebauten Qualitätsgrenze für
  diesen Kennwert vor.
- **DE** — Die Sessionliste startet mit Datum, Name, Typ, F0-Median und
  -Spanne, Intonationsbreite, F2, F3, H1, H2, Jitter und Shimmer.

- **EN** — The session list now starts with the measurements that matter for
  voice training: level, F0 median and range, intonation width, F2, F3 and
  H1–H2. Duration and filename are one click away in the header menu.
- **EN** — Removed the settings dialog's "restore defaults" button; the
  built-in "Standard" template does exactly the same thing.

- **DE** — Die Sessionliste startet jetzt mit den Größen, die beim
  Stimmtraining zählen: Pegel, F0-Median und -Spanne, Intonationsbreite, F2,
  F3 und H1–H2. Dauer und Dateiname sind einen Klick im Kopfzeilenmenü
  entfernt.
- **DE** — Der Knopf „Zurücksetzen" im Einstellungsdialog ist weg; die
  eingebaute Vorlage „Standard" macht genau dasselbe.

- **EN** — Tabs can be pulled out into their own window: right-click the tab
  bar or double-click a tab. Closing the window docks it back, and the last
  remaining tab stays put.

- **DE** — Reiter lassen sich in ein eigenes Fenster ziehen: Rechtsklick auf
  die Reiterleiste oder Doppelklick auf einen Reiter. Das Fenster zu schließen
  hängt ihn zurück, der letzte verbleibende Reiter bleibt an Ort und Stelle.

### Fixed / Behoben

- **EN** — Voice report parsing broke when Praat appended a bracketed note,
  as in "Degree of voice breaks: 0   (0 seconds / 0 seconds)". Jitter and
  shimmer survived, but the break counts were silently lost.
- **EN** — With a dialog open, closing the program from the taskbar did
  nothing. The dialogs ran application-modal, and Qt discards the window
  manager's close request to a blocked window before it reaches the program.
  All dialogs are now non-modal and are closed along with the main window.
- **EN** — A detached tab came up empty, because removeTab() hides the page
  and it was never made visible again.
- **EN** — Session list built an action button for every row up front, which
  cost about half a second at 500 recordings. They are now created only for
  rows in view.

- **DE** — Das Auswerten des Voice Reports scheiterte, sobald Praat einen
  Klammerzusatz anhängt, etwa „Degree of voice breaks: 0   (0 seconds /
  0 seconds)". Jitter und Shimmer kamen durch, die Abbruchzahlen gingen still
  verloren.
- **DE** — Bei geöffnetem Dialog bewirkte „Schließen" aus der Taskleiste
  nichts. Die Dialoge liefen anwendungsmodal, und Qt verwirft die
  Schließanfrage des Fenstermanagers an ein blockiertes Fenster, bevor sie im
  Programm ankommt. Alle Dialoge sind jetzt nicht-modal und werden mit dem
  Hauptfenster geschlossen.
- **DE** — Ein ausgehängter Reiter blieb leer, weil removeTab() die Seite
  versteckt und sie nie wieder sichtbar gemacht wurde.
- **DE** — Die Sessionliste baute für jede Zeile im Voraus Aktionsknöpfe, was
  bei 500 Aufnahmen eine halbe Sekunde kostete. Sie entstehen jetzt nur noch
  für sichtbare Zeilen.

- **EN** — Spectrogram rendered as a single flat colour. `setRect()` was
  called before an image existed, so pyqtgraph could not derive a scale and
  stretched one pixel across the whole plot.
- **EN** — Room noise was reported as a voice at roughly the pitch floor.
  Praat's autocorrelation finds spurious periods in noise; the voicing
  threshold is now configurable, values near the floor are discarded, and a
  minimum voiced share is required before any numbers are produced.
- **EN** — Cancelling the settings dialog after pressing Apply restored the
  in-memory values but not the file on disk.
- **EN** — Delete button label was cut off by a fixed width.
- **EN** — Action buttons stayed behind in old columns after changing the
  visible-column selection, because `setColumnCount()` does not remove
  existing cell widgets.

- **DE** — Spektrogramm zeigte eine einfarbige Fläche. `setRect()` wurde vor
  dem ersten Bild aufgerufen, wodurch pyqtgraph keine Skalierung bilden
  konnte und ein einzelnes Pixel über die ganze Fläche zog.
- **DE** — Raumrauschen wurde als Stimme knapp über der Untergrenze
  ausgegeben. Praats Autokorrelation findet in Rauschen Scheinperioden; die
  Stimmhaftigkeitsschwelle ist jetzt einstellbar, Werte nahe der Untergrenze
  fliegen raus, und es braucht einen Mindestanteil stimmhafter Frames, bevor
  überhaupt Zahlen entstehen.
- **DE** — Abbrechen nach „Anwenden" stellte die Werte im Speicher zurück,
  nicht aber die bereits geschriebene Datei.
- **DE** — Beschriftung des Löschknopfs wurde durch eine feste Breite
  abgeschnitten.
- **DE** — Aktionsknöpfe blieben nach einer Änderung der Spaltenauswahl in
  den alten Spalten stehen, weil `setColumnCount()` vorhandene Cell-Widgets
  nicht entfernt.
