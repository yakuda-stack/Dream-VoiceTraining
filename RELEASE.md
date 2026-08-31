# Einrichten und veröffentlichen

Zwei Teile: **A** einmalig beim Aufsetzen, **B** bei jeder neuen Version.

Version steht an genau einer Stelle: `APP_VERSION` in `paths.py`. Alles andere
liest von dort.

---

# A — Einmalig

## A1. Arbeitsumgebung

Eine venv überlebt kein Umbenennen oder Verschieben des Ordners, weil im
Aktivierungsskript absolute Pfade stehen. Nach einem Umzug also neu anlegen:

```fish
cd ~/Schreibtisch/voice-training/Dream-VoiceTraining
rm -rf .venv
python -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements-dev.txt
python main.py                       # startet es?
python -m pytest tests/ -q           # 86 passed
```

## A2. Git und erster Push

Prüfen, ob GitHub beim Anlegen schon einen Commit erzeugt hat — das passiert,
wenn README, .gitignore oder Lizenz eingeschaltet waren:

```fish
git ls-remote https://github.com/yakuda-stack/Dream-VoiceTraining.git
```

**Leere Ausgabe** heißt leeres Repository, dann:

```fish
git init -b main
git add -A
git commit -m "Dream-VoiceTraining 1.0.0"
git remote add origin git@github.com:yakuda-stack/Dream-VoiceTraining.git
git push -u origin main
```

**Kommt eine Zeile zurück**, gibt es dort schon Geschichte. Dann einmalig:

```fish
git init -b main
git add -A
git commit -m "Dream-VoiceTraining 1.0.0"
git remote add origin git@github.com:yakuda-stack/Dream-VoiceTraining.git
git fetch origin
git rebase origin/main               # bei Konflikt in LICENSE: unsere behalten
git push -u origin main
```

Falls das Rebase zickt und dort ohnehin nur die generierte Lizenz liegt:
`git push -u --force origin main`. Nur solange noch niemand geklont hat.

Danach kontrollieren, dass nichts Falsches mitgegangen ist:

```fish
git ls-files | grep -E "\.venv|sessions/|config\.json"     # muss leer sein
```

## A3. GitHub einstellen

Bei „About" rechts oben aufs Zahnrad:

**Description**

```
Voice analysis for training your speaking voice on Linux — pitch, formants,
resonance and voice quality, tracked across sessions. Built on Praat.
```

**Topics**

```
voice-training  transvoice  praat  formants  linux  pyside6
speech-analysis  pitch-detection  python  qt
```

Website leer lassen oder Ko-fi eintragen. Unter *Settings → General* Wikis und
Projects abschalten, wenn du sie nicht benutzt — sonst wirken die leeren Reiter
wie ein unfertiges Projekt. Issues anlassen, dahin sollen Fehlerberichte.

Prüfen, ob GitHub die Lizenz erkennt: neben dem Repo-Namen sollte „GPL-3.0"
stehen. Wenn nicht, ist die `LICENSE` beschädigt.

## A4. AUR vorbereiten

Nur nötig, wenn du dort veröffentlichen willst.

**SSH-Schlüssel hinterlegen** (einmal pro Rechner): Schlüssel unter
https://aur.archlinux.org/ im Profil eintragen, dann testen:

```fish
ssh aur@aur.archlinux.org help
```

**Zuerst die Abhängigkeit.** `python-praat-parselmouth` gibt es im AUR noch
nicht, ohne sie ist dein Paket nicht installierbar:

```fish
cd ~/aur
git clone ssh://aur@aur.archlinux.org/python-praat-parselmouth.git
cd python-praat-parselmouth
cp ~/Schreibtisch/voice-training/Dream-VoiceTraining/packaging/PKGBUILD.python-praat-parselmouth PKGBUILD
updpkgsums                           # echte Prüfsummen eintragen
makepkg -si                          # baut Praat mit, dauert einige Minuten
makepkg --printsrcinfo > .SRCINFO    # Pflicht, sonst lehnt das AUR ab
git add PKGBUILD .SRCINFO
git commit -m "Initial import: python-praat-parselmouth 0.4.7"
git push origin master               # das AUR nutzt master, nicht main
```

**Dann das Programm** — erst nachdem der Tag `v1.0.0` auf GitHub liegt, sonst
findet `updpkgsums` das Archiv nicht:

```fish
cd ~/aur
git clone ssh://aur@aur.archlinux.org/dream-voicetraining.git
cd dream-voicetraining
cp ~/Schreibtisch/voice-training/Dream-VoiceTraining/packaging/PKGBUILD .
updpkgsums
makepkg -si
dream-voicetraining                  # startet? Icon? Name im Systemmonitor?
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD .SRCINFO
git commit -m "Initial import: dream-voicetraining 1.0.0"
git push origin master
```

## A5. AppImage einmal durchlaufen lassen

```fish
cd ~/Schreibtisch/voice-training/Dream-VoiceTraining
bash packaging/build-appimage.sh
```

Braucht FUSE und lädt `appimagetool` beim ersten Mal herunter. Rechne mit ein
bis zwei Anläufen. Danach auf einem anderen Rechner oder in einer VM ohne
Python-Umgebung testen — das ist der ganze Sinn eines AppImage.

---

# B — Bei jeder Version

## B1. Vorbereiten

```fish
cd ~/Schreibtisch/voice-training/Dream-VoiceTraining
source .venv/bin/activate.fish
```

Version anheben in `paths.py`:

```python
APP_VERSION = "1.0.1"
```

`CHANGELOG.md` ergänzen, zweisprachig, Überschrift von `[1.0.1] — unreleased`
auf das Datum setzen.

## B2. Prüfen

```fish
python -m pytest tests/ -q                              # alles grün?
desktop-file-validate packaging/dream-voicetraining.desktop
bash -n install.sh packaging/build-appimage.sh
python main.py                                          # kurz von Hand testen
```

Von Hand mindestens: aufnehmen, Detailansicht öffnen, Sprache umschalten,
Einstellungen öffnen und Programm über die Taskleiste schließen.

## B3. GitHub

```fish
git add -A
git commit -m "v1.0.1"
git push origin main
git tag -a v1.0.1 -m "v1.0.1"
git push origin v1.0.1
```

## B4. AppImage und Archiv

```fish
bash packaging/build-appimage.sh
# -> build/Dream-VoiceTraining-1.0.1-x86_64.AppImage

cd ~/Schreibtisch/voice-training
tar --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
    -czf Dream-VoiceTraining-v1.0.1.tar.gz Dream-VoiceTraining/
```

Auf GitHub unter *Releases → Draft a new release* den Tag `v1.0.1` wählen, den
Changelog-Abschnitt als Beschreibung einfügen und beide Dateien anhängen.

## B5. AUR

```fish
cd ~/aur/dream-voicetraining
nano PKGBUILD                        # pkgver=1.0.1, pkgrel=1
updpkgsums                           # lädt den neuen Tag, ersetzt Prüfsumme
makepkg -si                          # bauen und installieren
dream-voicetraining                  # testen: startet? Icon? Prozessname?
makepkg --printsrcinfo > .SRCINFO    # PFLICHT
git add PKGBUILD .SRCINFO
git commit -m "Update to v1.0.1"
git push origin master               # AUR nutzt master!
```

Bei reinen Paketänderungen ohne neue Programmversion bleibt `pkgver` gleich und
`pkgrel` geht um eins hoch.

---

## Wenn etwas schiefgeht

**`updpkgsums` findet das Archiv nicht** — der Tag ist noch nicht auf GitHub.
Erst B3, dann B5.

**AUR lehnt den Push ab** — meistens fehlt `.SRCINFO` oder es ist veraltet.
`makepkg --printsrcinfo > .SRCINFO` und neu committen.

**AppImage startet, findet aber kein Mikrofon** — PortAudio kommt vom
Wirtssystem und ist bewusst nicht gebündelt. Auf dem Testsystem
`libportaudio2` beziehungsweise `portaudio` installieren.

**Nutzer meldet einen Absturz** — im Programm unter *Einstellungen → Info →
Systeminfos kopieren* und *Einstellungen → Debug → Exportieren*. Beides an den
Issue hängen, dann steht dort alles, was man sonst nachfragen müsste.
