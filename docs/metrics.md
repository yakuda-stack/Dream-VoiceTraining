# Acoustic Metrics & Methodology

What Dream-VoiceTraining measures, how it measures it, and what the numbers
can and cannot tell you.

[Deutsche Fassung](metrics.de.md) · [back to the README](../README.md)

---

## The short version

A recording is broken into 10 ms frames. For each frame the program asks
Praat — through [parselmouth](https://parselmouth.readthedocs.io/) — what the
fundamental frequency is, whether the frame is voiced at all, and where the
vocal tract resonances sit. Everything else is statistics over the frames that
came back voiced.

That last part matters. Unvoiced frames — breaths, pauses, consonants — are
thrown away before any average is taken. A median over voiced frames is what
your voice does while it is producing tone, not an average that silence drags
downward.

If less than 15 % of the recording is voiced, the recording is marked
*no usable voice* and no numbers are stored at all. An invented number is
worse than a missing one.

---

## Pitch

Five metrics, all derived from the same voiced pitch track.

| Metric | What it is |
| :--- | :--- |
| **F0 median** | The middle of your pitch, in Hz. Median rather than mean: one octave jump does not move it. |
| **F0 lower end** | The 10th percentile — where the bottom of your range sits in normal speech. |
| **F0 upper end** | The 90th percentile — the top, excluding the outliers. |
| **Intonation width** | Standard deviation of the pitch track in semitones. How much melody there is. |
| **Pitch range** | Distance from lower to upper end, in semitones. |

The last two are in semitones on purpose. A 20 Hz wobble around 100 Hz and a
20 Hz wobble around 220 Hz sound nothing alike; in semitones they are what
they are — 3.2 and 1.5. Absolute Hz would make a low voice look expressive
and a high one flat.

Pitch is searched between **60 Hz and 500 Hz** by default. Both ends are
adjustable under *Settings → Analysis*. Widening the window is not free: the
further apart floor and ceiling sit, the more often the tracker mistakes a
harmonic for the fundamental.

---

## Resonance

| Metric | What it is |
| :--- | :--- |
| **F1** | First formant. Roughly: how open the vowel is. |
| **F2** | Second formant. Roughly: how far forward the tongue is. Carries most of what people hear as a "bright" or "dark" voice. |
| **F3** | Third formant. Less about the vowel, more about the size of the tract above the larynx. |

Formants are properties of the vowel being spoken, not of the voice on its
own. `/i/` has a high F2 and `/u/` a low one in *every* speaker. Comparing F2
from a reading text against F2 from another reading text only works if both
texts had the same vowels in roughly the same proportion — which is why the
program offers a fixed practice text and a *sustained vowel* recording type.

For anything you intend to track over weeks, record a held `/a/`, `/i/` or
`/u/` and compare like with like. Formant analysis looks up to **5000 Hz** by
default.

---

## Weight and voice quality

| Metric | What it is | Healthy range |
| :--- | :--- | :--- |
| **H1 level**, **H2 level** | Levels of the first and second harmonic, in dB. | — |
| **Weight (H1–H2)** | Difference between them. A large positive value goes with a breathier, lighter production; a small or negative one with a pressed, heavier one. | — |
| **Clarity (HNR)** | Harmonics-to-noise ratio in dB — how much of the signal is periodic tone rather than noise. | above 15 dB |
| **Jitter (local)** | Cycle-to-cycle variation in *length*. | below 1.04 % |
| **Shimmer (local)** | Cycle-to-cycle variation in *amplitude*. | below 3.81 % |
| **Voice breaks** | Share of the recording where voicing dropped out mid-phonation. | below 5 % |
| **Number of breaks** | How many separate dropouts. | — |
| **Voiced share** | How much of the recording was voiced at all. | above 30 % |
| **Recording level** | 95th percentile of frame energy, in dBFS. | −30 to −8 dBFS |

**Jitter, shimmer and the two break metrics are only meaningful on a sustained
vowel.** In running speech every consonant is a legitimate interruption, and
the numbers come out high for reasons that have nothing to do with your voice.
The detail window marks these rows accordingly. Reading them off a reading
text and worrying about the result is the single most common way to
misinterpret this program.

Recording level is not a voice metric — it is a check on the recording. A take
below −30 dBFS is too quiet for the analysis to be reliable, and one above
−8 dBFS is close enough to clipping to distort the harmonics. Fix the input
gain rather than the take.

---

## Target profiles

Three built-in profiles, and any number of your own. The values are population
means from the speech-science literature, not goals anyone has to reach.

| | Masculine | Androgynous | Feminine |
| :--- | :---: | :---: | :---: |
| **F0 median** | 85–130 Hz | 145–175 Hz | 180–250 Hz |
| **F0 lower end** | 70–110 Hz | 115–150 Hz | 145–200 Hz |
| **F0 upper end** | 120–200 Hz | 180–250 Hz | 210–300 Hz |
| **Intonation width** | 2.0–4.5 ST | 2.5–5.0 ST | 3.0–5.5 ST |
| **Pitch range** | 4.0–11.0 ST | 5.0–13.0 ST | 7.0–16.0 ST |

Two things follow from "population means". First, a value outside a range is
not a fault — plenty of people are read as their target while sitting outside
it, because pitch is only one of several cues and not the strongest one.
Second, the ranges overlap, and the gaps between them are not empty space:
nothing happens at 144 Hz that does not happen at 146 Hz.

You can build your own profile from your own recordings — *Take these values
as my target* in the detail window — and edit any of the eighteen metrics
individually.

---

## Recording so that two sessions are comparable

The analysis is repeatable. The recording usually is not, and that is where
most unexplained "changes" come from.

- **Same microphone, same distance, same room.** Distance changes level;
  level changes which frames count as voiced. A different room changes the
  formants you measure without changing the ones you produce.
- **Same material.** The built-in practice text exists for this. Read all of
  it, the same way, every time — or use one of your own and stay with it.
- **Same type.** A held vowel and a reading text are not comparable
  measurements even on the same day. The recording type is stored with every
  take so you can filter by it.
- **At least a few seconds.** Under 0.3 s nothing is analysed at all, and
  under a couple of seconds the percentiles are noise.
- **Compare weeks, not takes.** Day-to-day variation in a healthy voice is
  larger than most of the effects worth measuring. Two recordings a week apart
  say more than ten in one afternoon.

---

## What this cannot tell you

It cannot tell you how you are perceived. Perception depends on resonance,
intonation, articulation, word choice, speed and context; this program
measures the acoustic part and nothing else.

It cannot tell you whether your voice is healthy. Jitter, shimmer and HNR are
used clinically, but by clinicians, alongside an examination and a history.
An unusual number here is a reason to see someone, never a diagnosis.

It cannot tell you what to change. It tells you what is, over time. What to do
about it is exactly what a speech-language pathologist is for — a few sessions
save hundreds of hours of guessing, and this program is far more useful
alongside one than instead of one.

And it will never be a reason to keep going through pain. Scratching, pressure
or hoarseness means stop, whatever the numbers say.
