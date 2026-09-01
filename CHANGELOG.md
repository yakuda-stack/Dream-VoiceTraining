# Changelog

Notable changes per release. Format follows
[Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.2] — 2026-09-02

### Fixed

- **The Details button crashed the program** with
  `NameError: name 'color' is not defined`. A stylesheet inside an f-string
  had single braces where CSS needs them doubled, so Python read `color` as an
  expression instead of literal text. It only fired when the detail dialog was
  actually built, which no test did — the theming rewrite had replaced the
  hardcoded colours in those stylesheets without anything checking the result.
  There is now a test that constructs every dialog (details, settings, view,
  debug, about) plus a check across all source files for unescaped braces.

### Changed

- **Renaming a recording renames the WAV file too.** Having a recording called
  one thing in the program and another in the folder makes it impossible to
  find when tidying up by hand. The name is sanitised — no path separators, no
  control characters, capped at 80 characters — and a collision is refused
  rather than overwriting an existing take.

## [1.0.1] — 2026-09-02

### Added

- **Design tab in the settings.** Eight themes — Default, Carbon, Nebula,
  Embers, Grass, Ocean, Rose, Mono — shown as preview tiles. Twelve colour
  roles can be recoloured individually with a picker: accent, window, bars,
  cards, inner boxes, borders, text, secondary text, stop/delete, good,
  warning and highlight. "Reset colors" returns to the theme's own palette
  without touching the background or opacity.
- **Background image.** Drop an image behind the window, managed as a small
  gallery under `~/.local/share/dream-voicetraining/backgrounds`. A slider
  sets how transparent the panels are on top of it; without an image the
  panels stay opaque, since translucency over a flat colour only looks washed
  out.
- The version number sits quietly in the bottom right of the status bar, so a
  screenshot in a bug report carries it without anyone having to ask.
- Everything applies immediately and is stored in `config.json`. Changing a
  theme rebuilds the interface, because pen colours and plot backgrounds are
  set when widgets are created and a stylesheet cannot reach them.

### Fixed

- **The Details button crashed the program.** A stylesheet built as an
  f-string had a CSS brace that was not doubled, so Python read `{ color: … }`
  as an expression. It only surfaced when the dialog was actually opened,
  which no test did. Two tests now cover it: one builds every dialog in the
  program, one scans the source for the same mistake.
- **The About dialog crashed** for the same reason, with a colour key that had
  been mangled into `yellowf`.

### Changed

- **Built-in target profiles now describe pitch only:** F0 median, the 10th
  and 90th percentiles, intonation width and pitch range. The formant ranges
  are gone. They came from the literature on *sustained vowels*, but what they
  were compared against was a median over connected reading text — two
  different things, and a verdict drawn from that said nothing. Anyone who
  wants formant targets can switch them on in the settings or derive a profile
  from a recording of their own, where the comparison is self-consistent.
- **Detachable tabs removed.** They were a nice idea and worked, but they
  complicated the rebuild path that language and theme switching depend on,
  for a feature nobody asked for twice.
- Switching a metric off does not switch off its warnings: level, HNR, jitter,
  shimmer, voice breaks and voiced share keep their own quality ranges.

## [1.0.0] — 2026-09-01

First release.

### Live view

- Pitch (F0), the first two formants, weight (H1–H2) and input level as large
  readouts. Pick a target voice and each one turns green or amber against it;
  leave it off and they stay neutral.
- Scrolling spectrogram with dashed markers where F1 and F2 sit.
- Pitch history over the last 30 seconds with the target zone shaded, plus a
  zone bar showing where you are between the configured boundaries.
- Level hint while recording: if the peak stays too low for three seconds, the
  status bar says so. Checking at the moment Record is pressed would be
  pointless — nobody has spoken yet.

### Recordings and sessions

- Six recording types: reading text, pitch test (a held hum), /a/, /i/, /u/
  and free. Picked before recording, changeable afterwards, and the basis for
  comparing like with like later on.
- Guided run: a toggle, off by default, showing a panel inside the Live tab
  rather than a window. It walks through hum, /a/, /i/ and /u/ with a
  countdown, trims each take to its steadiest stretch and files it under the
  right type. A popup in the middle of the screen pulls you out of holding a
  sound, so everything stays in one place with the spectrogram still running.
- Session list with 23 available columns. Click a header to sort, click again
  to reverse, drag headers to reorder. Right-click a row for details,
  playback, renaming, deletion or changing the type; right-click a header for
  sorting, hiding or any column straight from the menu.
- View dialog for column selection, sort order and an optional date range,
  with an Apply button that updates the list without closing.
- Recordings without a usable voice are marked as such instead of being given
  invented numbers.
- Export the list as text or CSV.

### Detail view

- Eighteen metrics per recording, each with an explanation behind an ⓘ:
  F0 median and percentiles, intonation width, pitch range, F1–F3, H1, H2,
  H1–H2, HNR, jitter, shimmer, voice breaks, voiced share and level.
- Checked against a target profile, optionally compared against any other
  recording, exportable as text or CSV.
- Advanced mode: the waveform with a draggable region, so a single sustained
  vowel can be isolated from a longer take and analysed on its own. This is
  what makes formants, jitter and shimmer comparable between sessions.
- Jitter, shimmer and voice breaks are marked "(vowel)" — their reference
  ranges apply to sustained vowels only, and connected speech is naturally far
  higher.

### Target profiles

- A dropdown in the Live toolbar picks the target voice. It starts at *no
  target* on purpose: a colour changing while you speak pulls attention to the
  screen, and that is attention taken off your voice. The detail view keeps
  its own selection and defaults to feminine.
- A settings tab edits the range of any of the eighteen metrics — H1 and H2
  separately included — and saves it under your own name. The three built-in
  profiles start from population averages in the literature and can be
  adjusted too: Save keeps your version, Save as makes a separate profile, and
  Reset brings back the original values.
- Any recording can seed a profile via "use these values as my target".

### Settings and interface

- Every analysis parameter adjustable while the program runs, with six
  built-in templates. Nothing requires a restart.
- English and German interface, switchable at runtime.
- Readable PipeWire/PulseAudio device names via `pactl`, grouped into
  microphones, virtual sources and monitors. Virtual sources and monitors are
  routed through `PULSE_SOURCE` so they can actually be recorded from.
- Tabs can be pulled into their own window: right-click the tab bar or
  double-click a tab. Closing the window docks it back.
- Debug window collecting warnings and caught exceptions with tracebacks and
  environment details, exportable for bug reports.
- About dialog with version, licence summary, links and a button that copies
  the system information. No update check — the program makes no network
  connections at all.
- Exports ask which language to write when the interface is German; an English
  interface exports English without asking.

### Storage and packaging

- Follows the XDG Base Directory Specification: settings in
  `~/.config/dream-voicetraining`, recordings in
  `~/.local/share/dream-voicetraining`. Data from earlier layouts is picked up
  automatically on first start and existing files are never overwritten.
- One-line installer detecting Debian, Ubuntu, Fedora, Arch, CachyOS and
  openSUSE, installing the system packages that have no Python equivalent.
- AUR packages `dream-voicetraining` and `python-praat-parselmouth`.
- AppImage with a runtime that uses FUSE 3, falls back to FUSE 2 and extracts
  itself when neither is available — one file for every system.
- The window and process lists show the program name and icon rather than
  python3.
- `diag.py` for diagnosing capture problems from the terminal.

### Fixed during development

Real bugs, found by measuring rather than guessing. Listed because the
reasoning may be useful to anyone reading the code.

- **Spectrogram rendered as a single flat colour.** `setRect()` was called
  before an image existed, so pyqtgraph could not derive a scale and stretched
  a single pixel across the whole plot. Diagnosed by reading the exact colour
  out of a screenshot and mapping it back to a dB value.
- **Room noise was reported as a voice** at roughly the pitch floor. Praat's
  autocorrelation finds spurious periods in noise. The voicing threshold is
  now configurable, values near the floor are discarded, and a minimum voiced
  share is required before any numbers are produced.
- **Crash on start where PyQt6 is installed**, with a TypeError and a
  segfault. pyqtgraph picks its own Qt binding at import time and prefers
  PyQt6 over PySide6, then receives PySide6 objects. The binding is now pinned
  before pyqtgraph is imported. Invisible in a virtual environment, which only
  contains PySide6 — it took testing the packaged build to surface.
- **`python-colorama` missing from the package dependencies.** pyqtgraph
  imports colorama at load time but lists it only as a check dependency, so
  the package built cleanly and would have crashed on every user's first
  start. Caught by running the test suite inside `check()`.
- **Voice report parsing broke** when Praat appended a bracketed note, as in
  `Degree of voice breaks: 0   (0 seconds / 0 seconds)`. Jitter and shimmer
  survived, the break counts were silently lost.
- **Cancelling the settings dialog after pressing Apply** restored the
  in-memory values but not the file on disk.
- **The program could not be closed from the taskbar** while a dialog was
  open. The dialogs ran application-modal, and Qt discards the window
  manager's close request to a blocked window before it reaches the program.
  All dialogs are now non-modal and close with the main window.
- **A detached tab came up empty**, because `removeTab()` hides the page and
  it was never made visible again.
- **Action buttons stayed behind in old columns** after changing the visible
  column selection, because `setColumnCount()` does not remove existing cell
  widgets.
- **Column reordering was applied twice** on every refresh, so columns kept
  drifting, because Qt keeps its own visual order separately from the model.
- **The session list built an action button for every row up front**, costing
  about half a second at 500 recordings. They are now created only for rows in
  view: 360 ms down to 54 ms.
- **The delete button label was cut off** by a fixed width.
