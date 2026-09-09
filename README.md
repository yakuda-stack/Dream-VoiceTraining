<div align="center">

<img src="packaging/dream-voicetraining.svg" width="110" alt="Dream-VoiceTraining Logo">

# Dream-VoiceTraining

**Measure what your voice is actually doing — and watch it change over time.**

Pitch, resonance, weight, and voice quality — real-time analysis while you speak, tracked across sessions.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Third Party Licenses](https://img.shields.io/badge/Third--Party-Notices-informational)](THIRD_PARTY_NOTICES.md)
![Platform: Linux | Windows](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-informational)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)

[Deutsch Version](README.de.md)

</div>

---

## ⚡ Quick Download & Installation

Native support for **Linux** and **Windows**. No setup required for portable versions.

| Platform | Quick Download / Command | Notes |
| :--- | :--- | :--- |
| **Linux (One-liner)** | `curl -fsSL [https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh](https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh) \| bash` | Auto-installs on Arch, Ubuntu, Debian, Fedora, openSUSE |
| **Arch / CachyOS (AUR)** | `paru -S dream-voicetraining` | Official AUR package |
| **Linux (AppImage)** | [Download AppImage](https://github.com/yakuda-stack/Dream-VoiceTraining/releases/download/v1.1.4/Dream-VoiceTraining-1.1.4-x86_64.AppImage) | Single file execution (`chmod +x` & run) |
| **Windows (Installer)** | [Download Setup `.exe`](https://github.com/yakuda-stack/Dream-VoiceTraining/releases/download/v1.1.4/Dream-VoiceTraining-1.1.4.exe) | Standard installer with Start Menu & Desktop shortcuts |
| **Windows (Portable)** | [Download Portable `.exe`](https://github.com/yakuda-stack/Dream-VoiceTraining/releases/download/v1.1.4/Dream-VoiceTraining-1.1.4-Portable.exe) | Self-contained, stores data in local folder |
| **All Releases** | [GitHub Releases Overview](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | View all release history & full changelogs |

---

## 📸 Interface Overview

| Live Analysis | Session Management | Detailed Metrics |
| :---: | :---: | :---: |
| <img src="assets/dashboard.png" width="280" alt="Live View"/> | <img src="assets/sessions.png" width="280" alt="Session List"/> | <img src="assets/details.png" width="280" alt="Detail View"/> |
| Real-time Pitch, Formants (F1/F2), & Weight | Track recordings over time with 24 exportable metrics | 18 acoustic metrics & detailed spectrogram view |

---

## 🚀 Key Features

- **Real-Time Visual Analysis:** Pitch history, live spectrogram with F1/F2 formant tracking, pitch zone indicators, and voice weight (H1–H2).
- **Import & Existing Audio:** Import external WAV/audio files to analyze existing recordings alongside your live sessions.
- **Session History & Analytics:** Save recordings as WAV + JSON metrics. Filter, sort, and manage 24 different vocal parameters.
- **Advanced Region Analysis & Spectrogram:** Select steady-state vowels (e.g., `/a/`, `/i/`, `/u/`) with a dedicated spectrogram view in the details panel for precise formant & jitter tracking.
- **Custom Prompts & Recording Types:** Select from custom practice texts and define custom recording types for standardized testing.
- **Custom Target Profiles:** Compare your measurements against Masculine, Androgynous, Feminine, or custom reference ranges.
- **100% Offline & Private:** Operates completely offline following XDG specs. No tracking, no telemetry, no cloud dependency.

*(Want to understand how these metrics work? Check out our [Acoustic Metrics & Methodology Guide](docs/metrics.md))*

---

## ⚠️ Important Disclaimer

> **Dream-VoiceTraining is a measuring instrument, not a therapy program or medical device.**

1. **Never train through pain:** Stop immediately if you feel strain, scratching, or hoarseness.
2. **Numbers are orientation, not a grade:** Vocal perception depends on far more factors than physical acoustic metrics alone.
3. **Professional guidance beats software:** A few sessions with a speech-language pathologist (SLP) save hundreds of hours of trial and error.

---

<details>
<summary><b>🛠️ Building from Source & Advanced Installation</b></summary>

### Linux (Manual / Source)
Ensure `portaudio` is installed on your system:
```bash
# System dependency (PortAudio)
sudo pacman -S portaudio                        # Arch / CachyOS
sudo apt install libportaudio2 libpulse0        # Debian / Ubuntu / Mint

# Build & Run
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py
```

### Windows (Manual PowerShell Build)
```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
```
Creates portable and installer executables inside `dist/`.

</details>

<details>
<summary><b>📂 Data & File Management</b></summary>

Files follow standard OS paths:
* **Linux:** `~/.config/dream-voicetraining/` (settings) and `~/.local/share/dream-voicetraining/sessions/` (recordings).
* **Windows:** `%APPDATA%\Dream-VoiceTraining\` (settings) and `%LOCALAPPDATA%\Dream-VoiceTraining\` (recordings).

Custom file naming schemes and target folders can be configured in **Settings → Options**.

</details>

---

## 🤖 Note on Development & AI Tooling

* **Idea, Architecture & UX/UI Design:** Conceived, designed, and architected entirely by me.
* **Code Implementation:** Developed, generated, and refactored using Claude Code (Anthropic).
* **Documentation & Copy:** Drafted and formatted with support from Google Gemini.

### Development Approach
AI tools were used extensively to accelerate development and code generation. System architecture, feature decisions, code reviews, and quality control were managed directly by the developer. All code is tested and verified prior to release.

---

## 💬 Community & Support

* **Discord:** [Join Community Server](https://discord.gg/UkhJSz3Ctf)
* **Ko-fi:** [Support on Ko-fi](https://ko-fi.com/yakuda_) *(Optional — software is free and open-source)*
* **License:** [GPL v3](LICENSE) | [Third-Party Notices](THIRD_PARTY_NOTICES.md)