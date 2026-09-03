# Changelog

Notable changes per release. Format follows
[Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.8] — 2026-09-03

### Added

- **The last page of the introduction carries the project links** — source
  code and issues, Discord, Ko-fi — each with the address written out
  underneath, so it is clear where a click leads before making it. They were
  only in *Settings → Info* before, which is not where somebody looks who has
  just finished the introduction and hit a problem.

### Fixed

- Those same links on the info page rendered without their colour: the style
  attribute was built inside an f-string as `style=f"..."`, and the stray `f`
  made the attribute invalid. Both places now build the link from one helper,
  so the next change to it cannot drift apart again.

## [1.0.7] — unreleased

### Fixed

- **Step 9 of the introduction pointed at a button nobody could see.** The
  page about the settings marks the ⚙ button, which sits in the Live tab —
  but the page before it switches to Sessions to show the view button, and
  nothing switched back, so the marker hid itself and the step explained a
  button while pointing at nothing. Which tab to open is no longer decided
  from a list of keys: the window looks up which tab actually contains the
  target and brings that one forward. A control moved to another tab now
  keeps working without anyone remembering to update a special case.

## [1.0.6] — 2026-09-03

### Fixed

- **The Windows build failed at the very last step.** The spec has built two
  single files straight into `dist` since the switch to onefile, but
  `build_windows.ps1` still looked for the old
  `dist\Dream-VoiceTraining\Dream-VoiceTraining.exe` and threw *No executable
  was produced* on a build that had in fact worked. The installer script had
  the same stale path. Both now use the real one, and the script checks for
  both executables so a half-finished build is caught where it happens.

### Added (Windows)

- `packaging/windows/install_windows.ps1` — installing from source, the
  counterpart to `install.sh`. Checks for Python 3.10 or newer, refuses the
  Microsoft Store build (it redirects `%LOCALAPPDATA%`, which is where the
  recordings go), installs Python through winget when it is missing, builds a
  virtual environment under `%LOCALAPPDATA%\Programs`, and creates the
  shortcuts. Reinstalling keeps the environment, so it takes seconds instead of
  downloading Qt again.
- **Both install paths put the program where Windows Search looks.** The
  shortcut goes into the top level of the start menu folder rather than a
  subfolder of it, carries a description for the search to match on, and the
  source install additionally registers under *Apps & features* and nudges the
  shell so the entry appears immediately instead of at the indexer's
  convenience. Pressing the Windows key and typing *dream* or *voice* finds it.
  The setup also registers an App Paths key, so Win+R starts it by name.
- The installer creates the desktop icon by default.
- The portable build ships as one `.exe` instead of a ZIP around a folder.

### Removed

- **The guided run is gone.** The toggle in the toolbar and the panel in the
  Live tab have both been removed, along with their strings and styles. On some
  setups the countdown could leave the panel hanging: the timer kept the stream
  and the recording state to itself, and once that went wrong there was no way
  out other than restarting the program. Everything it did can be done by hand
  — pick a type, record, trim in *Advanced* — so a feature that freezes is
  worse than no feature.

### Added

- **A recommended first round in the first-run introduction**, taking over what
  the guided run used to explain: pitch test (a held hum, about four seconds),
  then /a/, /i/ and /u/ at about three seconds each, every one as its own take
  with its own type, plus the hint to select the calm middle in *Advanced*
  afterwards. Reachable again at any time from *Settings → Info → Show
  introduction again*.
- **A pulsing golden ⓘ points at the control each page is about** — the
  microphone list, the type box, the ⓘ in the toolbar, the Sessions tab, the
  view button. It sits on the real main window rather than on a picture of it,
  ignores mouse clicks so the control underneath stays usable, and survives a
  language switch. Pages about the detail view, which is not open at that
  moment, carry a screenshot with the same marker on the spot that matters.
- **Four new introduction pages**: what F0, F1 and F2 mean and where the two
  ⓘ buttons explain them; advanced mode, with the waveform, the draggable
  region and why cutting out the calm middle is the whole point; making the
  column layout yours, covering the header menu, dragging columns and the view
  dialog; and what sits behind the settings button, tab by tab.
- `packaging/make-intro-shots.py` renders the introduction screenshots from the
  real interface with invented data, once per language. The marker positions
  fall out of it: they are computed from where the tab, the Details button, the
  row ⓘ, the Advanced toggle and the analyse button actually sit, and are
  written to `assets/intro/shots.json`. Hand-taken screenshots go stale and are
  always in one language.
- Screenshots for those pages ship in `assets/intro` and are installed by all
  four packaging paths. If they are missing, the pages stay readable without
  pictures instead of failing.

### Changed

- **Picking a language on the first page moves straight on.** That page has one
  job; making people confirm it with *Next* afterwards was a click for nothing.
- The microphone page now says what to do in one line: pick the microphone from
  the list, press Start, speak normally, watch the level card.
- **The introduction window sizes itself to the page.** One fixed size for all
  of them meant a page with three paragraphs sat in a window built for a
  screenshot, three quarters empty. Text pages now open at roughly 760×380,
  screenshot pages as wide as the picture needs. Heading and text stand in
  their own 700 px column, so line length stays readable under a wider image.
- **The introduction shows screenshots in the interface language**, and swaps
  them when the language changes rather than keeping the pictures it was built
  with.
- **The settings dialog opens on Info.** That tab holds the version, the links,
  the debug window and the button that shows the introduction again — what
  people are looking for when they open settings without a specific parameter
  in mind.
- **Built-in analysis templates are no longer named in German in the English
  interface.** They carried their German names in the code, so *Leises
  Mikrofon* and *Formantmessung (Vokal halten)* showed up untranslated. They
  now have keys and translated labels; an old name in an existing `config.json`
  is migrated on load, so a saved selection survives the update.

- **The About dialog is now an Info tab in the settings**, next to Design.
  Version, links, licence, the note on network use and the file locations all
  live there, and it is reading material rather than a window that wants
  something, so a tab fits it better than a dialog.
- The buttons that used to crowd the settings button row moved to the top of
  that tab: **show introduction again**, debug window, copy system info and
  open folder. The button row is back to OK, Cancel and Apply.
- The debug button keeps its error counter and turns red there just as before.

## [1.0.5] — unreleased

### Added

- **First-run introduction.** On the very first start the program asks for a
  language and then walks through five short pages: set your level, pick a
  recording type, where sessions and details live, where to look things up,
  and one page on not training through pain. It is **not modal**, so the
  microphone can be set up while reading. Reachable again at any time from
  *Settings → Show introduction again*.

### Changed

- **Windows builds are now two single files.** `Dream-VoiceTraining.exe` for
  the installer and `Dream-VoiceTraining-Portable.exe` for carrying around.
  Neither needs an `_internal` folder or anything else beside it — one file is
  the whole program.
- The portable build keeps settings and recordings in a
  `Dream-VoiceTraining-Data` folder next to the executable instead of under
  `%APPDATA%`. It recognises portable mode by the file name, or by a
  `portable.txt` placed beside it if the executable was renamed. If that
  folder cannot be written — a read-only drive, or Program Files — it falls
  back to the normal user folders rather than failing to start.

## [1.0.4] — unreleased

### Added

- **Reference window behind the ⓘ in the toolbar.** Nineteen topics in six
  sections explaining what every number in the program actually is: pitch and
  its percentiles, intonation, the formants F1 to F3 and what physically moves
  them, H1/H2 and weight, harmonicity, jitter and shimmer, how to read the
  spectrogram, what the recording types are for, how target profiles and the
  analysis parameters work, and how to get a first measurement that is worth
  anything.
- The window is **not modal**: it stays open beside the main window, so you can
  look something up while recording rather than instead of recording. Pressing
  ⓘ again brings the existing window forward instead of opening a second one.
- Full-text search across titles, bodies and keywords in the active language.
- Written in English and German, switching with the interface.

## [1.0.3] — unreleased

### Added

- **Windows support.** Settings go to `%APPDATA%\Dream-VoiceTraining`,
  recordings to `%LOCALAPPDATA%` — deliberately the local branch, or a roaming
  profile would drag hundreds of WAV files across the network at every login.
- Device list works without `pactl`. Windows reports the same microphone once
  per host API; the WASAPI entry is kept, the rest dropped, and the API is
  shown in the label so the choice stays traceable. "Stereo Mix" and
  "What U Hear" are classified as monitors, VB-Cable and Voicemeeter as
  virtual sources.
- Build scripts under `packaging/windows`: a PyInstaller spec that bundles the
  PortAudio DLL shipped with sounddevice and drops the Qt modules the program
  never uses, a PowerShell script producing a portable ZIP, and an Inno Setup
  installer that installs without administrator rights and leaves recordings
  and settings alone when uninstalling.
- `Segoe UI` added to the font stack.

### Fixed

- **Spin box arrows sat on top of the number** rather than beside it, so
  clicking the up arrow put the cursor in the field instead of raising the
  value. Styling a `QSpinBox` at all makes Qt stop drawing its sub-controls
  in the right place, and the border-triangle trick from CSS does nothing
  there — Qt wants an image. The arrows are now generated as SVG in the
  theme's text colour and regenerated when the theme changes. On Linux the
  native style happened to hide the problem; it only showed on Windows.

### Note

The Windows build is untested by the author of this changelog entry — it was
written on Linux and could not be executed there. Treat 1.0.3 on Windows as a
first attempt and report what breaks.

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
