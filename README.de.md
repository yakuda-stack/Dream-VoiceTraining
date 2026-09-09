<div align="center">

<img src="packaging/dream-voicetraining.svg" width="110" alt="Dream-VoiceTraining Logo">

# Dream-VoiceTraining

**Messen, was deine Stimme tatsächlich tut — und über Monate verfolgen, wie sie sich verändert.**

Tonhöhe, Resonanz, Schwere und Stimmqualität — Live-Analyse beim Sprechen und dokumentiert über Sessions hinweg.

[![Lizenz: GPL v3](https://img.shields.io/badge/Lizenz-GPLv3-blue.svg)](LICENSE)
[![Drittanbieter-Lizenzen](https://img.shields.io/badge/Drittanbieter-Hinweise-informational)](THIRD_PARTY_NOTICES.md)
![Plattform: Linux | Windows](https://img.shields.io/badge/Plattform-Linux%20%7C%20Windows-informational)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)

[English Version](README.md)

</div>

---

## ⚡ Schnellstart & Download

Volle Unterstützung für **Linux** und **Windows**. Portable Versionen benötigen keine Installation.

| Plattform | Schnellzugriff / Befehl | Hinweis |
| :--- | :--- | :--- |
| **Linux (Einzeiler)** | `curl -fsSL https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh \| bash` | Automatische Installation für Arch, Ubuntu, Debian, Fedora, openSUSE |
| **Arch / CachyOS (AUR)** | `paru -S dream-voicetraining` | Offizielles AUR-Paket |
| **Linux (AppImage)** | [AppImage herunterladen](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Einzelne Datei, direkt ausführbar (`chmod +x`) |
| **Windows (Installer)** | [Setup `.exe` herunterladen](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Standard-Installer mit Startmenü- & Desktop-Kopplung |
| **Windows (Portable)** | [Portable `.exe` herunterladen](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Ohne Installation, speichert Daten im eigenen Ordner |

---

## 📸 Benutzeroberfläche im Überblick

| Live-Analyse | Session-Verwaltung | Detail-Auswertung |
| :---: | :---: | :---: |
| <img src="assets/dashboard.png" width="280" alt="Live-Ansicht"/> | <img src="assets/sessions.png" width="280" alt="Sessionliste"/> | <img src="assets/details.png" width="280" alt="Detailansicht"/> |
| Echtzeit-Tonhöhe, Formanten (F1/F2) & Stimmgewicht | Verfolge Aufnahmen über Zeit mit 23 exportierbaren Spalten | 18 akkurate Messwerte mit Erklärungen per Klick |

---

## 🚀 Hauptfunktionen

- **Echtzeit-Stimmanalyse:** Live-Spektrogramm mit Formanten-Tracking (F1/F2), Tonhöhenverlauf, Zonenanzeige und Stimmgewicht (H1–H2).
- **Session-Verwaltung:** Speichert Takes als WAV + JSON. Sortiere, filtere und vergleiche 23 verschiedene Parameter.
- **Erweiterter Ausschnitts-Modus:** Schneide präzise Abschnitte aus gehaltenen Vokalen (z. B. `/a/`, `/i/`, `/u/`) für exakte Formant-, Jitter- und Shimmer-Werte heraus.
- **Anpassbare Zielprofile:** Vergleiche deine Werte mit Zielbereichen für maskuline, androgyne oder feminine Stimmlagen.
- **Interaktive Einführung:** Geführter Rundgang beim ersten Start mit hervorgehobenen Bedienelementen.
- **100% Lokal & Datenschutzfreundlich:** Funktioniert vollständig offline. Keine Telemetrie, kein Cloud-Zwang, volle Datenkontrolle.

---

## ⚠️ Wichtiger Hinweis

> **Dream-VoiceTraining ist ein Messgerät, kein Therapieprogramm.**

1. **Niemals gegen Schmerz trainieren:** Bei Kratzen, Druckgefühl oder Heiserkeit sofort abbrechen.
2. **Messwerte sind keine Schulnoten:** Stimmwahrnehmung hängt von vielen Faktoren ab, die über reine Akustikwerte hinausgehen.
3. **Logopädie schlägt jede Software:** Eine professionelle Anleitung spart hunderte Stunden Ausprobieren.

---

<details>
<summary><b>🛠️ Selbst Bauen & Entwickler-Installation</b></summary>

### Linux (Quellcode)
System-Abhängigkeit `portaudio` wird benötigt:
```bash
# Systempakete installieren
sudo pacman -S portaudio                        # Arch / CachyOS
sudo apt install libportaudio2 libpulse0        # Debian / Ubuntu / Mint

# Bauen & Starten
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py
```

### Windows (PowerShell Build)
```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
```
Erzeugt Installer und portable EXE im Ordner `dist/`.
</details>

<details>
<summary><b>📂 Speicherorte & Datenstruktur</b></summary>

Standardpfade des Betriebssystems:
* **Linux:** `~/.config/dream-voicetraining/` (Einstellungen) und `~/.local/share/dream-voicetraining/sessions/` (Aufnahmen).
* **Windows:** `%APPDATA%\Dream-VoiceTraining\` (Einstellungen) und `%LOCALAPPDATA%\Dream-VoiceTraining\` (Aufnahmen).

Dateinamen-Schemata und Zielordner lassen sich unter **Einstellungen → Optionen** flexibel anpassen.
</details>

---

## 🤖 Anmerkung zur Entstehung dieses Projekts

* **Idee, Architektur & Systemdesign:** Konzipiert, entworfen und strukturiert von mir.
* **Code-Implementierung:** Geschrieben, generiert und refactort unter Einsatz von Claude Code (Anthropic).
* **Dokumentation & Texte:** Ausformuliert und formatiert mit Unterstützung von Google Gemini.

### KI als modernes Werkzeug
Künstliche Intelligenz ist für mich ein hocheffizientes Werkzeug zur Umsetzung komplexer Softwareprojekte. So wie man früher ein Loch mit der Handbohrmaschine gedreht hat und heute auf den Knopf einer Akkubohrmaschine drückt, nimmt KI das zeitintensive Handwerk ab — die Richtung, die Präzision und die Kontrolle über das Ergebnis liegen jedoch weiterhin vollständig beim Entwickler.

Jede Codezeile und jeder Text wurden vor der Veröffentlichung persönlich geprüft, ausgeführt und getestet. Die Verantwortung für Codequalität, Architektur, Tests und Wartung liegt uneingeschränkt bei mir.

---

## 💬 Community & Support

* **Discord:** [Community-Server beitreten](https://discord.gg/UkhJSz3Ctf)
* **Ko-fi:** [Projekt auf Ko-fi unterstützen](https://ko-fi.com/yakuda_) *(Freiwillig — die Software ist und bleibt kostenlos)*
* **Lizenz:** [GPL v3](LICENSE) | [Drittanbieter-Hinweise](THIRD_PARTY_NOTICES.md)