<div align="center">

<img src="packaging/dream-voicetraining.svg" width="110" alt="">

# Dream-VoiceTraining

**Messen, was deine Stimme tatsächlich tut — und über Monate verfolgen, wie
sie sich verändert.**

Tonhöhe, Resonanz, Schwere und Stimmqualität, live beim Sprechen und über
Sessions hinweg dokumentiert.

[![Lizenz: GPL v3](https://img.shields.io/badge/Lizenz-GPLv3-blue.svg)](LICENSE)
![Plattform: Linux | Windows](https://img.shields.io/badge/Plattform-Linux%20%7C%20Windows-informational)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

[English version](README.md)

</div>

---

## Wie es aussieht

<table>
  <tr>
    <td><b>Live-Ansicht</b><br><img src="assets/dashboard.png" alt="Live-Ansicht" width="300"/></td>
    <td><b>Sessionliste</b><br><img src="assets/sessions.png" alt="Sessionliste" width="300"/></td>
    <td><b>Spaltenmenü</b><br><img src="assets/sessions-columns.png" alt="Spaltenmenü" width="300"/></td>
  </tr>
  <tr>
    <td><b>Aufnahme im Detail</b><br><img src="assets/details.png" alt="Detailansicht" width="300"/></td>
    <td><b>Einstellungen · Analyse</b><br><img src="assets/settings-analysis.png" alt="Analyse" width="300"/></td>
    <td><b>Einstellungen · Zielprofile</b><br><img src="assets/settings-profiles.png" alt="Zielprofile" width="300"/></td>
  </tr>
</table>

**Live-Ansicht** — alles in einer Leiste: Sprache, Mikrofon, Aufnahmetyp,
Zielstimme. Darunter die Kacheln, der Zonenbalken, das Spektrogramm mit
markiertem F1 und F2, der Tonhöhenverlauf und der Übungstext.

**Sessionliste** — Rechtsklick auf eine Zeile für Details, Wiedergabe,
Umbenennen, Löschen oder nachträgliches Ändern des Aufnahmetyps. Aufnahmen ohne
verwertbare Stimme sind ausgegraut und sagen das auch, statt erfundene Zahlen
zu zeigen. Rechtsklick auf eine Überschrift bietet Sortieren, Verschieben,
Ausblenden und alle 23 Spalten zum Anhaken.

**Detailansicht** — achtzehn Kennwerte, jeder mit Erklärung hinter dem ⓘ,
geprüft gegen ein Zielprofil und wahlweise verglichen mit einer anderen
Aufnahme. „Erweitert" klappt die Wellenform mit ziehbarem Bereich auf. Das
Beispiel zeigt eine zu leise Aufnahme: die Kennwerte bleiben leer, statt
geraten zu werden.

**Einstellungen** — Analyseparameter mit Vorlagen im einen Reiter, Zielprofile
im anderen, in denen sich jeder der achtzehn Kennwerte einschalten und mit
einem Bereich versehen lässt.

## Bitte zuerst lesen

Das hier ist ein **Messgerät, kein Therapieprogramm.** Es zeigt dir, was deine
Stimme macht. Es sagt dir nicht, was du dagegen tun sollst, und es kann nicht
hören, ob du gut klingst.

- **Trainiere niemals gegen Schmerz.** Wenn der Hals wehtut, wenn es kratzt
  oder wenn du nach einer Session heiser bist: aufhören. Das sind Zeichen von
  zu viel Spannung oder Druck, nicht von Anstrengung, die sich auszahlt. Einen
  überlasteten Stimmapparat wieder hinzubekommen dauert deutlich länger, als
  ihn kaputtzumachen.
- **Die Zahlen sind keine Bewertung.** Die Zielbereiche sind
  Populationsmittelwerte aus der phonetischen Literatur. Zwei Menschen mit
  identischen Werten können völlig unterschiedlich wahrgenommen werden, und
  Wahrnehmung hängt an weit mehr, als hier messbar ist. Nimm sie zur
  Orientierung und vor allem zum Vergleich mit deinen eigenen früheren
  Aufnahmen.
- **Das hier diagnostiziert nichts.** Jitter, Shimmer und Harmonizität kommen
  in klinischer Literatur vor, aber die Werte hier stammen aus normaler
  Sprache über ein Consumer-Mikrofon und bedeuten diagnostisch nichts.
  Anhaltende Heiserkeit gehört zum HNO.
- **Logopädie schlägt jede Software.** Ein paar Stunden mit jemandem, der dich
  wirklich hören kann, ersparen dir hunderte Stunden Rumprobieren, weil du
  dein eigenes Ergebnis am Anfang nicht zuverlässig beurteilen kannst.
  Gendersensible Stimmtherapie ist in Deutschland verordnungs- und
  kassenfähig.

Nützliche Anlaufstellen aus der Community: das
[Voice Resource Project Wiki](https://wiki.sumianvoice.com/),
[Spectrus](https://spec.sumianvoice.com/) für ein schnelles Spektrogramm im
Browser, und r/transvoice.

---

## Was es kann

**Live-Ansicht.** Tonhöhe (F0), die ersten beiden Formanten, die Schwere
(H1–H2) und der Eingangspegel als große Anzeigen. Mit gewählter Zielstimme
färben sie sich grün oder gelb, ohne bleiben sie neutral. Ein scrollendes Spektrogramm mit
gestrichelten Markierungen für F1 und F2, damit du die Resonanz beim Sprechen
wandern siehst. Ein Tonhöhenverlauf über 30 Sekunden mit hinterlegtem
Zielbereich. Ein Zonenbalken, der zeigt, wo du zwischen deinen Grenzen stehst.

**Sessions.** Aufnehmen, und jede Aufnahme wird als WAV samt Kennwerten
abgelegt. Die Liste zeigt Datum, Dauer, Pegel, Tonhöhe und Formanten auf einen
Blick. Was zu leise war oder keine verwertbare Stimme enthielt, wird als
solches markiert statt mit irreführenden Zahlen versehen.

**Detailansicht.** Achtzehn Kennwerte je Aufnahme, jeder mit einer Erklärung
hinter einem ⓘ. Wähle ein Zielprofil — maskulin, androgyn oder feminin — und
jeder Wert wird gegen den passenden Bereich geprüft. Wähle eine beliebige
andere Aufnahme als Vergleich und bekomme eine Differenzspalte. Exportierbar
als lesbarer Text oder als CSV.

**Erweiterter Modus.** Die Wellenform der Aufnahme mit ziehbarem Bereich.
Ausschnitt wählen, nur den auswerten, nur den abspielen. So kommst du an
brauchbare Formant-, Jitter- und Shimmerwerte: eine längere Aufnahme mit
gehaltenem Vokal machen und die stabile Mitte herausschneiden.

**Aufnahmetypen.** Jede Aufnahme wird als Lesetext, Tonhöhentest (gehaltenes
Summen), /a/, /i/, /u/ oder frei abgelegt. Vor der Aufnahme wählbar und als
Spalte sortierbar, damit ein gehaltener Vokal nie mit fließender Sprache
verrechnet wird.

**Einführung beim ersten Start.** Beim allerersten Start fragt das Programm
nach der Sprache — ein Klick darauf blättert gleich weiter — und zeigt dann
neun kurze Seiten: Pegel und Mikrofon, Aufnahmetypen, eine Empfehlung für die
erste Runde (Tonhöhentest, dann /a/, /i/ und /u/, jeweils als eigene Aufnahme),
wo du nachschlägst, was F0 und die Formanten sind, die Sessionliste, der
erweiterte Modus, das Anpassen der Spalten, was hinter dem Einstellungsknopf
steckt, und eine Seite darüber, nicht gegen Schmerz zu trainieren. Jede Seite
öffnet in der Größe, die sie braucht, statt alle in derselben.

Solange eine Seite offen ist, sitzt ein **pulsierendes goldenes ⓘ** auf dem
Bedienelement, um das es gerade geht — Mikrofonliste, Typ-Auswahl, das ⓘ in der
Leiste, der Sessions-Reiter, der Ansichtsknopf —, damit niemand suchen muss.
Seiten über die Detailansicht bringen ein Bildschirmfoto in der Sprache der
Oberfläche mit, mit derselben Marke an der entscheidenden Stelle;
`packaging/make-intro-shots.py` erzeugt diese Fotos neu aus der echten
Oberfläche. Die Einführung ist nicht modal, das Mikrofon
lässt sich also nebenher einstellen, und sie ist jederzeit wieder über
*Einstellungen → Info → Einführung erneut zeigen* erreichbar.

**Sessionliste.** Klick auf eine Spaltenüberschrift sortiert, erneuter Klick
dreht um. Rechtsklick auf eine Zeile für Details, Wiedergabe, Umbenennen oder
Löschen; Rechtsklick auf eine Spaltenüberschrift für Sortieren, Ausblenden
oder das Umschalten beliebiger Spalten direkt aus dem Menü. Spalten lassen
sich per Ziehen in beliebige Reihenfolge bringen. Der
Ansichtsdialog wählt aus, welche der 23 verfügbaren Spalten
sichtbar sind — darunter H1, H2, Jitter, Shimmer und Stimmabbrüche —, legt die
Sortierung fest und begrenzt die Liste optional auf einen Zeitraum.
Exportierbar als Text oder CSV.

**Debugfenster.** Erreichbar über den Einstellungsdialog. Warnungen und abgefangene Ausnahmen mit Traceback und
Umgebungsangaben, als Textdatei exportierbar für Fehlerberichte. Leer ist der
Normalfall.

**Zielprofile.** Ein Dropdown in der Live-Leiste wählt die Zielstimme —
maskulin, androgyn, feminin oder ein eigenes. Es steht bewusst auf *kein Ziel*:
eine Farbe, die sich beim Sprechen ändert, zieht die Aufmerksamkeit auf den
Bildschirm, und Aufmerksamkeit auf dem Bildschirm fehlt bei der Stimme. Die
Detailansicht hat ihre eigene Auswahl und steht auf feminin — Ziele schaust du
dir also hinterher an, statt dich während des Übens von ihnen anmahnen zu
lassen. In den Einstellungen gibt es
einen Reiter, in dem sich der Bereich aller achtzehn Kennwerte bearbeiten
lässt — H1 und H2 einzeln inbegriffen — und unter
eigenem Namen sichern lässt; die drei eingebauten starten mit
Populationsmittelwerten, lassen sich aber anpassen, unter neuem Namen sichern
oder auf die Literaturwerte zurücksetzen.

**Themen.** Acht eingebaute Farbschemata, jede Farbrolle einzeln änderbar,
dazu ein optionales Hintergrundbild mit einstellbarer Durchsichtigkeit der
Flächen.

**Info-Reiter.** Version, Lizenz, Links und wo deine Dateien liegen, mit
Knöpfen für die Einführung, das Debugprotokoll und das Kopieren der
Systeminfos für einen Fehlerbericht.

**Nachschlagewerk.** Das ⓘ in der Leiste öffnet neunzehn Themen, die
erklären, was jede Zahl bedeutet und was sie physikalisch verändert — nicht
modal, es bleibt also neben dem Hauptfenster offen, während du aufnimmst.

**Einstellungen.** Jeder Analyseparameter ist im laufenden Betrieb änderbar,
mit sechs eingebauten Vorlagen für verschiedene Situationen. Nichts davon
braucht einen Neustart.

---

## Die Kennwerte

| Kennwert | Was er dir sagt |
|---|---|
| **F0 Median** | Mittlere Sprechtonhöhe. Der meistgenannte und für sich allein am wenigsten aussagekräftige Wert. |
| **F0 10 % / 90 %** | Wie tief die Satzenden fallen und wie weit du nach oben gehst. |
| **Intonationsbreite** | Standardabweichung in Halbtönen — wie viel Melodie in deiner Sprechweise steckt. |
| **Tonumfang** | Abstand zwischen beiden Enden, in Halbtönen. |
| **F1 / F2 / F3** | Formanten. F2 ist der nützlichste Einzelwert für die Resonanz, F3 hängt eng an der Länge des Ansatzrohrs. |
| **H1 / H2 / H1–H2** | Pegel der ersten beiden Harmonischen und ihr Abstand. Großer Abstand heißt leichte, behauchte Stimmgebung, kleiner heißt schwere, gepresste. |
| **Klarheit (HNR)** | Verhältnis von Klang zu Rauschen. Niedrig heißt behaucht — oder die Aufnahme war zu leise. |
| **Jitter / Shimmer / Stimmabbrüche** | Stabilität von Periode zu Periode. Die Grenzwerte gelten **nur für gehaltene Vokale**, fließende Sprache liegt naturgemäß weit darüber. |
| **Stimmhafter Anteil** | Wie viel der Aufnahme überhaupt als Stimme erkannt wurde. |
| **Aufnahmepegel** | Spitzenpegel. Unter −40 dBFS sind die Messwerte nicht mehr verlässlich. |

Resonanz ist wichtiger als Tonhöhe. Wer F0 anhebt, ohne die Formanten zu
bewegen, klingt nach tiefer Stimme in hoher Lage — deshalb bekommen F2, F3 und
H1–H2 hier genauso viel Gewicht wie F0.

---

## Installation

### Der kurze Weg — jede Distribution

```sh
curl -fsSL https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh | bash
```

Erkennt Debian, Ubuntu, Fedora, Arch, CachyOS und openSUSE, installiert die
Systempakete, für die es kein Python-Äquivalent gibt (PortAudio, venv, git),
holt den Quelltext nach `~/.local/lib/dream-voicetraining`, legt eine eigene
Python-Umgebung an und trägt einen Menüeintrag ein. `sudo` wird ausschließlich
für die Systempakete benutzt und vorher angekündigt, alles andere bleibt unter
`~/.local`.

Ein Skript in die Shell zu pipen heißt, ihm zu vertrauen. Wer lieber erst
hineinschaut — und das ist die vernünftige Gewohnheit:

```sh
curl -fsSLO https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh
less install.sh
bash install.sh
```

Entfernen lässt Aufnahmen und Einstellungen unangetastet:

```sh
bash install.sh --uninstall
```

Nützliche Schalter: `--no-deps` überspringt die Systempakete, `PREFIX=/wohin`
verschiebt die Installation.

### Arch, CachyOS, EndeavourOS — als Paket

`praat-parselmouth` gibt es noch nicht im AUR, also wird es zuerst gebaut.
Dabei werden die mitgelieferten Praat-Quellen kompiliert, das dauert ein paar
Minuten.

```sh
git clone https://github.com/yakuda-stack/Dream-VoiceTraining
cd Dream-VoiceTraining/packaging
makepkg -si -p PKGBUILD.python-praat-parselmouth
paru -Ui
```

`paru` statt `makepkg` im zweiten Schritt: `python-sounddevice` liegt im AUR,
und `makepkg` kennt nur pacman. Mit yay: `yay -Bi .`

Scheitert der Praat-Bau nach einem Python-Sprung in Arch, nimm stattdessen
`PKGBUILD.python-praat-parselmouth-bin` — das installiert das offizielle Wheel
und braucht keinen Compiler.

### Windows

Zwei einzelne Dateien unter
[Releases](https://github.com/yakuda-stack/Dream-VoiceTraining/releases):

- **`Dream-VoiceTraining-<version>-setup.exe`** — installiert ins
  Benutzerprofil, legt einen Startmenüeintrag an, braucht keine
  Administratorrechte.
- **`Dream-VoiceTraining-Portable.exe`** — von überall startbar. Einstellungen
  und Aufnahmen landen in einem Ordner `Dream-VoiceTraining-Data` neben der
  EXE, auf einem USB-Stick bleibt also alles beisammen.

Beide brauchen weder einen `_internal`-Ordner noch sonst eine Datei daneben.

### AppImage

Aus den
[Releases](https://github.com/yakuda-stack/Dream-VoiceTraining/releases)
laden:

```sh
chmod +x Dream-VoiceTraining-*.AppImage
./Dream-VoiceTraining-*.AppImage
```

Eine Datei für jedes System: die Laufzeit nimmt FUSE 3, fällt auf FUSE 2
zurück und entpackt sich notfalls selbst. Nichts zu installieren.

PortAudio muss auf dem System vorhanden sein — es ist bewusst nicht gebündelt,
weil das Audio-Routing vom Wirtssystem kommen muss, damit überhaupt etwas
funktioniert.

### Windows

Installer oder portables ZIP aus den
[Releases](https://github.com/yakuda-stack/Dream-VoiceTraining/releases)
laden. Der Installer braucht keine Administratorrechte und lässt deine
Aufnahmen und Einstellungen beim Deinstallieren stehen.

Sonst ist nichts zu installieren — die PortAudio-Bibliothek steckt im Build.

Selbst bauen braucht Python 3.10+ von python.org (nicht die Store-Fassung,
die den Zugriff auf `%LOCALAPPDATA%` einschränkt):

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
```

Erzeugt `dist\Dream-VoiceTraining\Dream-VoiceTraining.exe` und ein portables
ZIP; mit installiertem [Inno Setup](https://jrsoftware.org/isdl.php)
zusätzlich den Installer.

Deine Dateien liegen unter `%APPDATA%\Dream-VoiceTraining` (Einstellungen)
und `%LOCALAPPDATA%\Dream-VoiceTraining` (Aufnahmen).

### Aus dem Quelltext, zum Entwickeln

```sh
python -m venv .venv
source .venv/bin/activate.fish       # bash/zsh: source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py
```

**PortAudio wird gebraucht** und ist kein Python-Paket:

```sh
sudo pacman -S portaudio                        # Arch, CachyOS
sudo apt install libportaudio2 libpulse0        # Debian, Ubuntu, Mint
sudo dnf install portaudio pulseaudio-utils     # Fedora
sudo zypper install portaudio pulseaudio-utils  # openSUSE
```

`pactl` (aus `libpulse`) ist optional, aber sehr zu empfehlen. Ohne fallen die
Gerätenamen auf rohe ALSA-Bezeichnungen wie
`USB Audio Device: USB Audio (hw:1,0)` zurück statt der lesbaren
PipeWire-Beschreibungen.

Eine virtuelle Umgebung überlebt kein Umbenennen oder Verschieben des
übergeordneten Ordners — das Aktivierungsskript trägt absolute Pfade ein. Wenn
du das Projekt verschiebst, lösch `.venv` und leg sie neu an.

---

## Die erste Messung richtig machen

**Zuerst den Pegel richten, alles andere danach.** `pavucontrol` öffnen, Reiter
Aufnahme, Eingangspegel hochziehen, bis die Pegelkachel beim normalen Sprechen
um die −20 dB anzeigt. Etwa eine Handbreit vom Mikrofon entfernt sitzen,
leicht seitlich, damit Plosive nicht direkt draufknallen. Wird die Kachel rot,
liegt das Signal unter der Stille-Schwelle und es wird gar nichts ausgewertet.

Den Übungstext einmal komplett lesen und aufnehmen. Das ist deine
Nullmessung. Zahlen notieren. Danach `/a/`, `/i/` und `/u/` je drei Sekunden
halten und im erweiterten Modus die stabile Mitte herausschneiden — die geben
dir Formantwerte, die in zwei Monaten noch vergleichbar sind.

Danach gilt: zehn bis fünfzehn Minuten täglich schlagen zwei Stunden am
Wochenende. Immer derselbe Text, dieselbe Mikrofonposition, dieselbe Vorlage,
sonst misst du deinen Aufbau statt deiner Stimme.

Lies nichts in Unterschiede zwischen zwei Aufnahmen hinein, die Minuten
auseinanderliegen. Tagesform, Mikrofonabstand und wie eingesungen du bist
bewegen diese Zahlen stärker als wochenlanges Üben. Für Trends brauchst du
Wochen.

---

## Wo deine Daten liegen

Nach der XDG Base Directory Specification:

```
~/.config/dream-voicetraining/config.json          Einstellungen, Vorlagen
~/.local/share/dream-voicetraining/sessions/       Aufnahmen und Kennwerte
```

`DREAM_VOICETRAINING_HOME` legt beides in einen gemeinsamen Ordner, praktisch
für Tests und portable Varianten. Daten aus früheren Versionen werden beim
ersten Start automatisch übernommen, vorhandene Dateien nie überschrieben.

Alles ist reines WAV und JSON. Nichts wird irgendwohin hochgeladen, es gibt
keine Telemetrie, und das Programm baut überhaupt keine Netzwerkverbindungen
auf.

---

## Wenn etwas nicht stimmt

`diag.py` nimmt drei Sekunden über exakt denselben Weg auf wie das Programm und
zeigt, was am Analyseschritt ankommt:

```sh
python diag.py --list
python diag.py --device 0
```

Interessant sind „Anteil exakt 0", „verschiedene Werte" und die Beispielspalte
am Ende. Diese Ausgabe hat während der Entwicklung zweimal aus einer
zweistündigen Raterei eine fünfminütige Korrektur gemacht.

Häufige Fälle: eine rote Pegelkachel heißt, der Eingangspegel ist zu niedrig
oder du hast eine Monitorquelle statt eines Mikrofons gewählt. „Kein
Sprachsignal" bei einer Aufnahme, in der du definitiv gesprochen hast, heißt,
der Pegel lag unter der Stimmhaftigkeitsschwelle — dann den Pegel richten,
nicht die Schwelle senken.

---

## Changelog

Jede Version ist in [CHANGELOG.md](CHANGELOG.md) dokumentiert (englisch),
samt der behobenen Fehler und woran sie lagen.

Der Ablauf für eine Veröffentlichung — GitHub, AppImage, AUR — steht in
[update_DreamVoiceTraining.txt](update_DreamVoiceTraining.txt).

## Entwicklung

```sh
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

Einhundertsechzehn Tests für den Analysekern, die Persistenz der Einstellungen,
Pfadauflösung und Migration, Geräteerkennung und Vollständigkeit der
Übersetzungen. Zwei davon sind Regressionstests für echte Fehler: Rauschen,
das als Stimme durchging, und das Spektrogramm, das zu einer Farbe kollabierte.

Ein neuer übersetzter Text kommt nach `i18n.py` und wird mit `t("key")`
verwendet. Die Testsuite schlägt fehl, wenn ein Schlüssel benutzt, aber nicht
definiert ist, wenn eine Sprache fehlt oder wenn sich die Platzhalter zwischen
beiden Fassungen unterscheiden.

Beiträge sind willkommen, besonders von Leuten, die selbst an ihrer Stimme
arbeiten und sagen können, welche Zahlen sich als nützlich erwiesen haben und
welche nur Rauschen sind.

---

## Community

- **Discord** — https://discord.gg/UkhJSz3Ctf
- **Ko-fi** — https://ko-fi.com/yakuda_ (rein freiwillig; das Programm ist
  freie Software und bleibt es)

Fehler bitte in den Issue-Tracker. Im Einstellungsdialog gibt es ein
Infofenster mit einem Knopf, der deine Systeminfos kopiert, und ein
Debugfenster, dessen Protokoll sich exportieren lässt — beides angehängt macht
einen Bericht deutlich brauchbarer.

## Lizenz

GPL-3.0-or-later. Keine freie Entscheidung: das Programm linkt Praat über
Parselmouth, und Praat steht unter GPL-3.0. Die vollständige Abhängigkeitsliste
und die Anmerkung zu den LGPL-Komponenten stehen in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Wer Messwerte aus diesem Programm veröffentlicht, zitiert bitte Praat und
Parselmouth, nicht dieses Werkzeug.

## Anmerkung zur Entstehung

Teile dieses Codes sind mit KI-Unterstützung entstanden. Review, Tests und
Wartung liegen bei mir. Jeder Fehler in diesem Repository wurde durch Messen
gefunden, nicht durch Raten — das Diagnoseskript und die Testsuite gibt es,
damit das so bleibt.
