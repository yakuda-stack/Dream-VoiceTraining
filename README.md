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
| **Linux (One-liner)** | `curl -fsSL https://raw.githubusercontent.com/yakuda-stack/Dream-VoiceTraining/main/install.sh \| bash` | Auto-installs on Arch, Ubuntu, Debian, Fedora, openSUSE |
| **Arch / CachyOS (AUR)** | `paru -S dream-voicetraining` | Official AUR package |
| **Linux (AppImage)** | [Download AppImage](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Single file execution (`chmod +x` & run) |
| **Windows (Installer)** | [Download Setup `.exe`](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Standard installer with Start Menu & Desktop shortcuts |
| **Windows (Portable)** | [Download Portable `.exe`](https://github.com/yakuda-stack/Dream-VoiceTraining/releases) | Self-contained, stores data in local folder |

---

## 📸 Interface Overview

| Live Analysis | Session Management | Detailed Metrics |
| :---: | :---: | :---: |
| <img src="assets/dashboard.png" width="280" alt="Live View"/> | <img src="assets/sessions.png" width="280" alt="Session List"/> | <img src="assets/details.png" width="280" alt="Detail View"/> |
| Real-time Pitch, Formants (F1/F2), & Weight | Track recordings over time with 23 exportable metrics | 18 clinical/acoustic metrics with built-in explanations |

---

## 🚀 Key Features

- **Real-Time Visual Analysis:** Pitch history, live spectrogram with F1/F2 formant tracking, pitch zone indicators, and voice weight (H1–H2).
- **Session History & Analytics:** Save recordings as WAV + JSON metrics. Filter, sort, and manage 23 different vocal parameters.
- **Advanced Region Analysis:** Select and evaluate specific steady-state vowels (e.g., sustained `/a/`, `/i/`, `/u/`) for accurate formant & jitter tracking.
- **Custom Target Profiles:** Compare your measurements against Masculine, Androgynous, Feminine, or fully custom reference ranges.
- **Interactive First-Run Onboarding:** Interactive guided tour highlighting interface controls with animated indicators.
- **100% Offline & Private:** Operates completely offline following XDG specs. No tracking, no telemetry, no cloud dependency.

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

File naming patterns and destination folders can be fully customized in **Settings → Options**.
</details>

---

## 🤖 Note on Development & AI Tooling

* **Idea, Architecture & UX/UI Design:** Conceived, designed, and architected entirely by me.
* **Code Implementation:** Developed, generated, and refactored using Claude Code (Anthropic).
* **Documentation & Copy:** Drafted and formatted with support from Google Gemini.

### AI as a High-Efficiency Tool
Artificial Intelligence serves as a high-efficiency tool to accelerate software engineering. Just as craftsmen shifted from hand-cranked drills to power drills, AI automates laborious execution — while direction, structural integrity, and rigorous testing remain strictly in the hands of the human developer.

Every line of code and documentation is manually audited, executed, and tested. Code quality, architecture, and maintenance responsibility remain 100% mine.

---

## 💬 Community & Support

* **Discord:** [Join Community Server](https://discord.gg/UkhJSz3Ctf)
* **Ko-fi:** [Support on Ko-fi](https://ko-fi.com/yakuda_) *(Optional — software is free and open-source)*
* **License:** [GPL v3](LICENSE) | [Third-Party Notices](THIRD_PARTY_NOTICES.md)