# Third-party notices

Dream-VoiceTraining is licensed under the GNU General Public License v3.0 or
later. That choice is not arbitrary: the program links Praat through
parselmouth, and Praat is GPL-3.0. Any redistribution must keep the GPL.

## Runtime dependencies

| Component | Licence | Role |
|---|---|---|
| [Praat](https://www.fon.hum.uva.nl/praat/) (via parselmouth) | GPL-3.0-or-later | Pitch, formant, jitter, shimmer and harmonicity analysis |
| [Parselmouth](https://github.com/YannickJadoul/Parselmouth) | GPL-3.0-or-later | Python bindings for Praat |
| [PySide6 / Qt](https://www.qt.io/) | LGPL-3.0 | User interface |
| [pyqtgraph](https://www.pyqtgraph.org/) | MIT | Spectrogram, plots, waveform |
| [NumPy](https://numpy.org/) | BSD-3-Clause | Numerics and FFT |
| [python-sounddevice](https://python-sounddevice.readthedocs.io/) | MIT | Audio capture |
| [PortAudio](https://www.portaudio.com/) | MIT | Audio backend used by sounddevice |

## Note on the LGPL components

PySide6 and Qt are used as unmodified shared libraries through their public
Python API. Nothing is statically linked and nothing is patched, so the
LGPL-3.0 relinking requirement is satisfied by the ordinary installation:
replacing the PySide6 package in the environment replaces the library.

The AppImage build bundles PySide6. The build script in
`packaging/build-appimage.sh` is part of this repository, so the bundled
libraries can be rebuilt and replaced from source by anyone.

## What is not bundled

ALSA, PulseAudio and PipeWire are always taken from the host system, in the
AppImage as well. `pactl` is invoked as an external command when present; it
is optional and only improves the readability of device names.

## Academic citation

If you use measurements from this program in something publishable, cite
Praat and Parselmouth rather than this tool:

- Boersma, P. & Weenink, D. *Praat: doing phonetics by computer.*
- Jadoul, Y., Thompson, B. & de Boer, B. (2018). Introducing Parselmouth: A
  Python interface to Praat. *Journal of Phonetics*, 71, 1–15.
