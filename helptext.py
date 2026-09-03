# Dream-VoiceTraining — voice analysis for training your speaking voice
# Copyright (C) 2026  Yakuda
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Inhalte des Nachschlagefensters.

Getrennt vom UI-Code, weil es viel Text ist und weil er sich so ohne
Ruecksicht auf Layoutfragen erweitern laesst. Jeder Eintrag hat einen
Titel und einen Rumpf in beiden Sprachen; der Rumpf ist einfaches HTML.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import i18n

SECTIONS = ["basics", "pitch", "resonance", "quality", "workflow", "practice"]

SECTION_TITLES = {
    "basics": {"en": "Basics", "de": "Grundlagen"},
    "pitch": {"en": "Pitch", "de": "Tonhöhe"},
    "resonance": {"en": "Resonance and weight", "de": "Resonanz und Schwere"},
    "quality": {"en": "Voice quality", "de": "Stimmqualität"},
    "workflow": {"en": "Working with the program", "de": "Umgang mit dem Programm"},
    "practice": {"en": "Practice", "de": "Übung"},
}


@dataclass(frozen=True)
class Topic:
    key: str
    section: str
    title: dict
    body: dict
    keywords: dict = field(default_factory=dict)

    def localised_title(self) -> str:
        return self.title.get(i18n.LANG) or self.title["en"]

    def localised_body(self) -> str:
        return self.body.get(i18n.LANG) or self.body["en"]

    def matches(self, needle: str) -> bool:
        needle = needle.strip().lower()
        if not needle:
            return True
        haystack = " ".join([
            self.localised_title(),
            self.localised_body(),
            self.keywords.get(i18n.LANG, ""),
            self.keywords.get("en", ""),
        ]).lower()
        return needle in haystack


def _t(en: str, de: str) -> dict:
    return {"en": en, "de": de}


TOPICS: list[Topic] = [

    # ------------------------------------------------------------ basics
    Topic(
        "overview", "basics",
        _t("What this program measures", "Was dieses Programm misst"),
        _t("""
<p>Every recording is run through <b>Praat</b>, the standard tool of academic
phonetics, and reduced to eighteen numbers. Those numbers describe four
independent things:</p>
<ul>
<li><b>Pitch</b> — how high or low the voice sits, and how much it moves.</li>
<li><b>Resonance</b> — the size the vocal tract sounds like, measured through
the formants F1, F2 and F3.</li>
<li><b>Weight</b> — how heavily or lightly the vocal folds vibrate, measured
through the gap between the first two harmonics.</li>
<li><b>Quality</b> — how steady and how clear the sound is.</li>
</ul>
<p>These are separate. A voice can be high and heavy, or low and light. That
is exactly why pitch alone is a poor description, and why this program shows
you more than one number.</p>
<p><b>What it cannot do:</b> it cannot hear you. It has no opinion on whether
you sound good, natural or convincing. It reports physical measurements. The
perceptual judgement stays with you and with people who listen to you.</p>
""", """
<p>Jede Aufnahme läuft durch <b>Praat</b>, das Standardwerkzeug der
akademischen Phonetik, und wird auf achtzehn Zahlen heruntergebrochen. Diese
Zahlen beschreiben vier voneinander unabhängige Dinge:</p>
<ul>
<li><b>Tonhöhe</b> — wie hoch oder tief die Stimme liegt und wie viel sie sich
bewegt.</li>
<li><b>Resonanz</b> — wie groß das Ansatzrohr klingt, gemessen über die
Formanten F1, F2 und F3.</li>
<li><b>Schwere</b> — wie schwer oder leicht die Stimmlippen schwingen,
gemessen über den Abstand der ersten beiden Harmonischen.</li>
<li><b>Qualität</b> — wie gleichmäßig und wie klar der Klang ist.</li>
</ul>
<p>Das sind getrennte Größen. Eine Stimme kann hoch und schwer sein oder tief
und leicht. Genau deshalb ist Tonhöhe allein eine schlechte Beschreibung, und
genau deshalb zeigt dir dieses Programm mehr als eine Zahl.</p>
<p><b>Was es nicht kann:</b> es kann dich nicht hören. Es hat keine Meinung
dazu, ob du gut, natürlich oder überzeugend klingst. Es meldet physikalische
Messwerte. Das Urteil bleibt bei dir und bei Menschen, die dir zuhören.</p>
"""),
        _t("introduction start begin", "einführung anfang start")),

    Topic(
        "spectrogram", "basics",
        _t("Reading the spectrogram", "Das Spektrogramm lesen"),
        _t("""
<p>Time runs left to right, frequency bottom to top, and brightness is how
much energy sits at that frequency. Two patterns matter:</p>
<p><b>Horizontal stripes.</b> These are the harmonics — the fundamental and
its whole-number multiples. Their spacing <i>is</i> your pitch: wider spacing
means a higher voice. If the stripes are crisp and evenly spaced, the voice is
steady.</p>
<p><b>Bright bands across several stripes.</b> These are the formants. They do
not move with pitch; they move when you change the shape of your mouth and
throat. The dashed lines mark where the program currently estimates F1 and
F2.</p>
<p>Noise between the harmonics — a general grey fuzz — is breath. A lot of it
means either a breathy voice or a bad recording.</p>
<p>This is the single most useful display for resonance work, because you can
watch a formant move while you change something, with no delay and no numbers
to interpret.</p>
""", """
<p>Die Zeit läuft von links nach rechts, die Frequenz von unten nach oben, und
die Helligkeit zeigt, wie viel Energie bei dieser Frequenz liegt. Zwei Muster
sind wichtig:</p>
<p><b>Waagerechte Streifen.</b> Das sind die Harmonischen — der Grundton und
seine ganzzahligen Vielfachen. Ihr Abstand <i>ist</i> deine Tonhöhe: größerer
Abstand heißt höhere Stimme. Sind die Streifen scharf und gleichmäßig, ist die
Stimme ruhig.</p>
<p><b>Helle Bänder quer über mehrere Streifen.</b> Das sind die Formanten. Sie
wandern nicht mit der Tonhöhe, sondern wenn du die Form von Mund und Rachen
änderst. Die gestrichelten Linien zeigen, wo das Programm gerade F1 und F2
vermutet.</p>
<p>Rauschen zwischen den Harmonischen — ein allgemeiner grauer Schleier — ist
Atem. Viel davon heißt entweder behauchte Stimme oder schlechte Aufnahme.</p>
<p>Für die Arbeit an der Resonanz ist das die nützlichste Anzeige überhaupt,
weil du einen Formanten wandern siehst, während du etwas veränderst — ohne
Verzögerung und ohne Zahlen deuten zu müssen.</p>
"""),
        _t("harmonics stripes bands", "harmonische streifen bänder")),

    # ------------------------------------------------------------- pitch
    Topic(
        "f0", "pitch",
        _t("F0 median — pitch", "F0 Median — Tonhöhe"),
        _t("""
<p><b>What it is:</b> the fundamental frequency, in hertz. How often your
vocal folds open and close per second. This is what people mean by "how high
someone talks". The median is used rather than the average because a single
creaky syllable would drag an average down.</p>
<p><b>Rough orientation:</b> typical male speech sits around 100–130 Hz,
typical female speech around 180–220 Hz. Between roughly 145 and 185 Hz
listeners stop agreeing, which is why that band is shaded in the pitch
history.</p>
<p><b>What it does not tell you:</b> almost everything else. Raising pitch
without changing resonance produces a voice that reads as "low voice speaking
high", not as a different voice. This is the most common mistake in voice
training, and the reason this program deliberately shows F0 next to five other
numbers instead of alone.</p>
""", """
<p><b>Was es ist:</b> die Grundfrequenz in Hertz. Wie oft sich deine
Stimmlippen pro Sekunde öffnen und schließen. Das ist, was Leute meinen, wenn
sie sagen, jemand rede hoch oder tief. Genommen wird der Median und nicht der
Mittelwert, weil eine einzige knarrende Silbe den Mittelwert nach unten
zöge.</p>
<p><b>Grobe Orientierung:</b> typisch männliche Sprache liegt um 100–130 Hz,
typisch weibliche um 180–220 Hz. Zwischen etwa 145 und 185 Hz sind sich
Hörende uneinig — deshalb ist dieser Bereich im Tonhöhenverlauf hinterlegt.</p>
<p><b>Was es dir nicht sagt:</b> fast alles andere. Tonhöhe anzuheben, ohne die
Resonanz zu ändern, ergibt eine Stimme, die als „tiefe Stimme in hoher Lage"
gehört wird, nicht als andere Stimme. Das ist der häufigste Fehler im
Stimmtraining und der Grund, warum dieses Programm F0 bewusst neben fünf
anderen Zahlen zeigt statt allein.</p>
"""),
        _t("pitch fundamental frequency hertz", "tonhöhe grundfrequenz hertz")),

    Topic(
        "f0_ends", "pitch",
        _t("F0 lower and upper end", "F0 unteres und oberes Ende"),
        _t("""
<p>The 10th and 90th percentile of your voiced pitch. Nine tenths of your
speech lies between them.</p>
<p><b>The lower end</b> is where sentence endings land. Many people push their
median up successfully but keep dropping into their old range at the end of
every sentence — and endings are exactly where listeners pay attention. If
your median has moved but your lower end has not, that is your next target.</p>
<p><b>The upper end</b> shows how far up you go when you emphasise something.
A very low upper end usually means a flat, careful delivery, which reads as
guarded rather than as any particular gender.</p>
<p>Percentiles are used instead of minimum and maximum because a single
squeak or one creaky word would otherwise define the whole range.</p>
""", """
<p>Das 10. und das 90. Perzentil deiner stimmhaften Tonhöhe. Neun Zehntel
deiner Sprache liegen dazwischen.</p>
<p><b>Das untere Ende</b> ist der Ort der Satzenden. Viele heben ihren Median
erfolgreich an, fallen aber am Satzende weiter in die alte Lage — und genau
auf Satzenden achten Hörende besonders. Wenn dein Median sich bewegt hat, dein
unteres Ende aber nicht, ist das dein nächstes Ziel.</p>
<p><b>Das obere Ende</b> zeigt, wie weit du nach oben gehst, wenn du etwas
betonst. Ein sehr niedriges oberes Ende bedeutet meist eine flache, vorsichtige
Sprechweise — das wirkt zurückhaltend, nicht nach einem bestimmten
Geschlecht.</p>
<p>Genommen werden Perzentile statt Minimum und Maximum, weil sonst ein
einzelner Quietscher oder ein knarrendes Wort den ganzen Bereich bestimmen
würde.</p>
"""),
        _t("percentile p10 p90 range", "perzentil spanne satzende")),

    Topic(
        "intonation", "pitch",
        _t("Intonation width and pitch range", "Intonationsbreite und Tonumfang"),
        _t("""
<p>Both are measured in <b>semitones</b>, not hertz, because the ear hears
pitch differences as ratios. Going from 100 to 120 Hz and from 200 to 240 Hz
sounds like the same step, and both are about 3 semitones.</p>
<p><b>Intonation width</b> is the standard deviation — how much your pitch
moves around, moment to moment. Melody, in other words.</p>
<p><b>Pitch range</b> is the distance between the lower and upper end. It
describes the space you use; the intonation width describes how busily you
move inside it.</p>
<p>Speech read aloud typically lands between 2 and 5 semitones of intonation
width. Below 2 sounds monotone. Above 6 starts to sound sing-song.</p>
<p>This is worth attention because it is the one thing here you can change
today, without any physical adjustment and without strain. It also tends to
carry more perceptual weight than a few hertz of median pitch.</p>
""", """
<p>Beides wird in <b>Halbtönen</b> gemessen, nicht in Hertz, weil das Ohr
Tonhöhenunterschiede als Verhältnisse hört. Von 100 auf 120 Hz und von 200 auf
240 Hz klingt nach demselben Schritt, und beides sind rund 3 Halbtöne.</p>
<p><b>Die Intonationsbreite</b> ist die Standardabweichung — wie stark sich
deine Tonhöhe von Moment zu Moment bewegt. Also Melodie.</p>
<p><b>Der Tonumfang</b> ist der Abstand zwischen unterem und oberem Ende. Er
beschreibt den Raum, den du nutzt; die Intonationsbreite beschreibt, wie
lebhaft du dich darin bewegst.</p>
<p>Vorgelesene Sprache liegt üblicherweise zwischen 2 und 5 Halbtönen
Intonationsbreite. Unter 2 klingt monoton, über 6 wird es Singsang.</p>
<p>Das lohnt Aufmerksamkeit, weil es das Einzige hier ist, das du heute ändern
kannst — ohne körperliche Umstellung und ohne Anstrengung. Und es wiegt in der
Wahrnehmung oft schwerer als ein paar Hertz Median.</p>
"""),
        _t("semitone melody monotone variation", "halbton melodie monoton")),

    # --------------------------------------------------------- resonance
    Topic(
        "formants", "resonance",
        _t("Formants — what they actually are", "Formanten — was sie wirklich sind"),
        _t("""
<p>Your vocal folds produce a buzz full of harmonics. That buzz then travels
through your throat, mouth and lips, and that space resonates: some
frequencies are amplified, others damped. The amplified regions are the
<b>formants</b>.</p>
<p>This matters because the formants depend on the <i>shape and size</i> of
the space, not on the pitch. Two consequences follow:</p>
<ul>
<li>You can change your formants without changing your pitch at all, and the
other way round. They are independent controls.</li>
<li>A shorter, narrower vocal tract pushes <i>all</i> formants up. That is the
main acoustic cue for a smaller-sounding speaker, and it is what "resonance"
means in voice training.</li>
</ul>
<p>Practically: raising the larynx slightly, bringing the tongue forward and
up, and narrowing the space behind the teeth all raise formants. Yawning,
dropping the larynx and opening the throat lower them.</p>
<p><b>Important limitation:</b> in flowing speech the formants move with every
vowel, because every vowel <i>is</i> a formant configuration. A median over a
read text mixes them all together. For a number you can compare across weeks,
record a sustained vowel and use Advanced mode to cut out the steady
middle.</p>
""", """
<p>Deine Stimmlippen erzeugen ein Summen voller Harmonischer. Dieses Summen
läuft durch Rachen, Mund und Lippen, und dieser Raum schwingt mit: manche
Frequenzen werden verstärkt, andere gedämpft. Die verstärkten Bereiche sind
die <b>Formanten</b>.</p>
<p>Das ist wichtig, weil die Formanten von <i>Form und Größe</i> des Raums
abhängen, nicht von der Tonhöhe. Daraus folgt zweierlei:</p>
<ul>
<li>Du kannst deine Formanten ändern, ohne die Tonhöhe anzufassen, und
umgekehrt. Es sind unabhängige Regler.</li>
<li>Ein kürzeres, engeres Ansatzrohr schiebt <i>alle</i> Formanten nach oben.
Das ist der akustische Hauptreiz für eine kleiner klingende sprechende Person,
und genau das meint „Resonanz" im Stimmtraining.</li>
</ul>
<p>Praktisch: den Kehlkopf leicht anheben, die Zunge nach vorn und oben
bringen und den Raum hinter den Zähnen verengen hebt die Formanten. Gähnen,
Kehlkopf senken und den Rachen weiten senkt sie.</p>
<p><b>Wichtige Einschränkung:</b> in fließender Sprache wandern die Formanten
mit jedem Vokal, denn jeder Vokal <i>ist</i> eine Formantstellung. Ein Median
über einen Lesetext mischt alles zusammen. Für eine über Wochen vergleichbare
Zahl nimm einen gehaltenen Vokal auf und schneide im erweiterten Modus die
ruhige Mitte heraus.</p>
"""),
        _t("resonance vocal tract length larynx", "resonanz ansatzrohr kehlkopf")),

    Topic(
        "f1", "resonance",
        _t("F1 — the first formant", "F1 — der erste Formant"),
        _t("""
<p>The lowest resonance, usually between 300 and 900 Hz. It tracks <b>how open
your mouth is</b>: the wider the jaw and the lower the tongue, the higher F1.</p>
<p>Say "ee" and then "ah" while watching the spectrogram. The lowest bright
band jumps upward on "ah" — that is F1 responding to the open jaw.</p>
<p>F1 is the least useful of the three for voice training, because it is
dominated by which vowel you happen to be saying. It becomes meaningful only
when you compare the same vowel to itself across sessions.</p>
""", """
<p>Die tiefste Resonanz, meist zwischen 300 und 900 Hz. Sie folgt der
<b>Mundöffnung</b>: je weiter der Kiefer und je tiefer die Zunge, desto höher
F1.</p>
<p>Sag „ih" und dann „ah" und schau dabei aufs Spektrogramm. Das unterste
helle Band springt bei „ah" nach oben — das ist F1, das auf den offenen Kiefer
reagiert.</p>
<p>Für das Stimmtraining ist F1 der am wenigsten nützliche der drei, weil er
vor allem davon abhängt, welchen Vokal du gerade sprichst. Aussagekräftig wird
er erst, wenn du denselben Vokal über mehrere Sessions mit sich selbst
vergleichst.</p>
"""),
        _t("first formant jaw openness vowel", "erster formant kiefer öffnung vokal")),

    Topic(
        "f2", "resonance",
        _t("F2 — the most useful formant", "F2 — der nützlichste Formant"),
        _t("""
<p>Usually between 900 and 2500 Hz. It tracks <b>where your tongue sits front
to back</b>: front vowels like "ee" push F2 high, back vowels like "oo" pull it
low.</p>
<p>For voice training this is the single most informative formant, because
tongue position forward and a narrower front cavity are exactly what shortens
the effective vocal tract. Population figures put typical male speech around
1500–1600 Hz and typical female speech around 1700–1900 Hz, averaged across
vowels.</p>
<p>Treat those numbers with care: they come from sustained vowels or from
carefully controlled corpora. Your own F2 over a read text is not directly
comparable to them. What <i>is</i> comparable is your own F2 on the same vowel,
measured the same way, three weeks apart.</p>
""", """
<p>Meist zwischen 900 und 2500 Hz. Er folgt der <b>Zungenlage vorn oder
hinten</b>: vordere Vokale wie „ih" treiben F2 hoch, hintere wie „uh" ziehen
ihn herunter.</p>
<p>Für das Stimmtraining ist das der aussagekräftigste Formant, denn eine
weiter vorn liegende Zunge und ein engerer vorderer Raum sind genau das, was
das wirksame Ansatzrohr verkürzt. Populationswerte liegen für typisch
männliche Sprache bei etwa 1500–1600 Hz und für typisch weibliche bei etwa
1700–1900 Hz, gemittelt über Vokale.</p>
<p>Nimm diese Zahlen mit Vorsicht: sie stammen aus gehaltenen Vokalen oder
sorgfältig kontrollierten Korpora. Dein eigenes F2 über einen Lesetext ist
damit nicht direkt vergleichbar. Vergleichbar ist dagegen dein eigenes F2 auf
demselben Vokal, gleich gemessen, drei Wochen später.</p>
"""),
        _t("second formant tongue front back", "zweiter formant zunge vorn hinten")),

    Topic(
        "f3", "resonance",
        _t("F3 — vocal tract length", "F3 — Länge des Ansatzrohrs"),
        _t("""
<p>Usually between 2300 and 3300 Hz. Of the three, F3 depends least on which
vowel you are saying and most on the <b>overall length</b> of the vocal tract
and on lip rounding.</p>
<p>That makes it a comparatively honest measure of resonance even in connected
speech — it drifts less with the words. If your F2 rises but F3 stays put, you
have probably changed tongue position without changing effective length; if
both rise together, the tract itself is behaving as if it were shorter.</p>
<p>Rounding your lips lengthens the tract and lowers F3. Spreading them
slightly raises it.</p>
""", """
<p>Meist zwischen 2300 und 3300 Hz. Von den dreien hängt F3 am wenigsten davon
ab, welchen Vokal du sprichst, und am meisten von der <b>Gesamtlänge</b> des
Ansatzrohrs und von der Lippenrundung.</p>
<p>Damit ist er selbst in fließender Sprache ein vergleichsweise ehrliches Maß
für Resonanz — er wandert weniger mit den Wörtern. Steigt dein F2, während F3
stehen bleibt, hast du wahrscheinlich die Zungenlage geändert, ohne die
wirksame Länge zu ändern. Steigen beide zusammen, verhält sich das Ansatzrohr
tatsächlich wie ein kürzeres.</p>
<p>Gerundete Lippen verlängern das Rohr und senken F3. Leicht gespreizte heben
ihn.</p>
"""),
        _t("third formant lip rounding length", "dritter formant lippen rundung länge")),

    Topic(
        "weight", "resonance",
        _t("H1, H2 and weight", "H1, H2 und die Schwere"),
        _t("""
<p><b>H1</b> is the level of the first harmonic — the fundamental itself.
<b>H2</b> is the second, one octave above. Both are given relative to full
scale, so they move with your microphone gain: only compare them between
recordings made at the same setting.</p>
<p><b>H1–H2, the gap between them, is the interesting number</b>, because it
is independent of gain. It reflects how your vocal folds close:</p>
<ul>
<li><b>Large gap (high H1–H2)</b> — the folds spend more of each cycle open.
Light, soft, somewhat breathy production. Thin vocal fold mass.</li>
<li><b>Small or negative gap</b> — the folds close firmly and quickly. Heavy,
pressed, dense production. Thick vocal fold mass.</li>
</ul>
<p>In voice training this is usually called <b>weight</b>, and it matters a
lot: heavy weight makes a voice read as large regardless of pitch, and it also
makes going higher harder and more tiring. Lightening the weight often makes
pitch work easier rather than adding to it.</p>
<p>The measurement here is uncorrected, meaning the formants influence it
somewhat. Use it as a trend on the same vowel rather than as an absolute.</p>
""", """
<p><b>H1</b> ist der Pegel der ersten Harmonischen — des Grundtons selbst.
<b>H2</b> ist die zweite, eine Oktave darüber. Beide sind auf Vollaussteuerung
bezogen und wandern damit mit dem Mikrofonpegel: vergleiche sie nur zwischen
Aufnahmen mit gleicher Einstellung.</p>
<p><b>Der Abstand H1–H2 ist die interessante Zahl</b>, denn er ist
pegelunabhängig. Er spiegelt, wie deine Stimmlippen schließen:</p>
<ul>
<li><b>Großer Abstand (hohes H1–H2)</b> — die Lippen sind in jedem Zyklus
länger offen. Leichte, weiche, etwas behauchte Stimmgebung. Geringe Masse.</li>
<li><b>Kleiner oder negativer Abstand</b> — die Lippen schließen fest und
schnell. Schwere, gepresste, dichte Stimmgebung. Große Masse.</li>
</ul>
<p>Im Stimmtraining heißt das <b>Schwere</b> oder Gewicht, und es zählt viel:
hohes Gewicht lässt eine Stimme groß wirken, unabhängig von der Tonhöhe, und
macht das Höhergehen zugleich schwerer und anstrengender. Das Gewicht zu
verringern erleichtert die Arbeit an der Tonhöhe oft, statt sie zu
vermehren.</p>
<p>Die Messung hier ist unkorrigiert, die Formanten beeinflussen sie also
etwas. Nimm sie als Verlauf auf demselben Vokal, nicht als absoluten Wert.</p>
"""),
        _t("h1 h2 weight breathy pressed mass", "schwere gewicht behaucht gepresst masse")),

    # ----------------------------------------------------------- quality
    Topic(
        "hnr", "quality",
        _t("Clarity (HNR)", "Klarheit (HNR)"),
        _t("""
<p>The harmonics-to-noise ratio, in decibels: how much of the sound is
periodic tone versus how much is turbulent noise. Higher means clearer.</p>
<p>Modal speech usually lands above 15 dB. Lower values mean either a breathy
production — air escaping through folds that do not fully close — or, far more
often in practice, <b>a recording that was too quiet</b>. The program cannot
tell those two apart, so check your level before concluding anything about
your voice.</p>
<p>Worth watching while you work on pitch: if HNR falls as your pitch rises,
you are getting there by letting air through rather than by changing how the
folds vibrate. That is the point to stop and try a different route.</p>
""", """
<p>Das Verhältnis von Harmonischen zu Rauschen in Dezibel: wie viel des Klangs
periodischer Ton ist und wie viel turbulentes Rauschen. Höher heißt klarer.</p>
<p>Normale Sprechstimme liegt meist über 15 dB. Niedrigere Werte bedeuten
entweder behauchte Stimmgebung — Luft, die durch nicht ganz schließende Lippen
entweicht — oder, in der Praxis weit häufiger, <b>eine zu leise Aufnahme</b>.
Das Programm kann beides nicht auseinanderhalten, prüf also den Pegel, bevor du
etwas über deine Stimme schließt.</p>
<p>Beim Arbeiten an der Tonhöhe lohnt der Blick darauf: fällt HNR, während die
Tonhöhe steigt, kommst du dort oben an, indem du Luft durchlässt, statt die
Schwingung zu ändern. Das ist der Punkt zum Aufhören und Anderswegprobieren.</p>
"""),
        _t("harmonics noise ratio breathy hoarse", "harmonizität rauschen behaucht heiser")),

    Topic(
        "jitter_shimmer", "quality",
        _t("Jitter, shimmer and voice breaks", "Jitter, Shimmer und Stimmabbrüche"),
        _t("""
<p><b>Jitter</b> is how much the length of each vibration cycle varies from the
next. <b>Shimmer</b> is the same for loudness. <b>Voice breaks</b> count the
places where voicing collapses entirely.</p>
<p>All three describe stability, and all three carry a large warning: <b>the
reference ranges apply to sustained vowels only.</b> The classic thresholds —
jitter below about 1 %, shimmer below about 3.8 % — come from clinical
recordings of someone holding a single "ah". Connected speech naturally
produces values several times higher, because every pause, every consonant and
every pitch change counts as instability. A jitter of 2.5 % on a read text
means nothing at all.</p>
<p>That is why those rows are marked "(vowel)". Record a held vowel, trim it in
Advanced mode, and only then are the numbers worth reading.</p>
<p><b>These are not a diagnosis.</b> They appear in clinical literature, but
those measurements are made with calibrated equipment in controlled rooms.
Yours come from a consumer microphone. If you are worried about hoarseness,
see an ENT doctor, not a spreadsheet.</p>
""", """
<p><b>Jitter</b> ist, wie stark die Länge jedes Schwingungszyklus vom nächsten
abweicht. <b>Shimmer</b> ist dasselbe für die Lautstärke. <b>Stimmabbrüche</b>
zählen die Stellen, an denen die Stimmgebung ganz zusammenbricht.</p>
<p>Alle drei beschreiben Stabilität, und alle drei tragen eine große Warnung:
<b>die Referenzbereiche gelten ausschließlich für gehaltene Vokale.</b> Die
bekannten Grenzwerte — Jitter unter etwa 1 %, Shimmer unter etwa 3,8 % —
stammen aus klinischen Aufnahmen eines gehaltenen „ah". Fließende Sprache
erzeugt naturgemäß ein Vielfaches davon, denn jede Pause, jeder Konsonant und
jeder Tonhöhenwechsel zählt als Instabilität. Ein Jitter von 2,5 % auf einem
Lesetext bedeutet schlicht nichts.</p>
<p>Deshalb sind diese Zeilen mit „(Vokal)" markiert. Nimm einen gehaltenen
Vokal auf, schneide ihn im erweiterten Modus zu, und erst dann lohnt sich der
Blick auf die Zahlen.</p>
<p><b>Das ist keine Diagnose.</b> Die Größen kommen in klinischer Literatur
vor, aber dort wird mit kalibriertem Gerät in kontrollierten Räumen gemessen.
Deine stammen von einem Consumer-Mikrofon. Wer sich wegen Heiserkeit sorgt,
geht zum HNO und nicht in eine Tabelle.</p>
"""),
        _t("jitter shimmer stability breaks pathology",
           "jitter shimmer stabilität abbrüche krankhaft")),

    Topic(
        "level", "quality",
        _t("Recording level and voiced share", "Aufnahmepegel und stimmhafter Anteil"),
        _t("""
<p><b>Recording level</b> is the peak of the recording in dBFS. Aim for roughly
−20 dB while speaking normally. Below −40 dB the analysis stops being
trustworthy: pitch detection starts finding patterns in noise, and clarity
collapses for reasons that have nothing to do with your voice.</p>
<p>Fix it in <code>pavucontrol</code> under the recording tab, or by sitting
closer — about a hand's width, slightly off to the side so plosives do not hit
the microphone directly.</p>
<p><b>Voiced share</b> is how much of the recording was recognised as voice at
all. Read text typically lands between 40 % and 65 %; the rest is pauses and
unvoiced consonants. A very low share on a recording where you definitely
spoke means the level was too low, not that you did something wrong.</p>
<p>If the share falls below the configured minimum, the program refuses to
produce numbers and says so instead. That is deliberate: a wrong measurement
you compare against for weeks is worse than no measurement.</p>
""", """
<p><b>Der Aufnahmepegel</b> ist der Spitzenwert in dBFS. Ziel sind rund −20 dB
beim normalen Sprechen. Unter −40 dB wird die Auswertung unzuverlässig: die
Tonhöhenerkennung findet Muster im Rauschen, und die Klarheit bricht ein aus
Gründen, die nichts mit deiner Stimme zu tun haben.</p>
<p>Richten lässt sich das in <code>pavucontrol</code> im Reiter Aufnahme oder
durch näheres Sitzen — etwa eine Handbreit, leicht seitlich, damit Plosive
nicht direkt aufs Mikrofon knallen.</p>
<p><b>Der stimmhafte Anteil</b> sagt, wie viel der Aufnahme überhaupt als
Stimme erkannt wurde. Lesetext liegt typisch zwischen 40 % und 65 %, der Rest
sind Pausen und stimmlose Laute. Ein sehr niedriger Anteil bei einer Aufnahme,
in der du definitiv gesprochen hast, heißt: der Pegel war zu niedrig, nicht
dass du etwas falsch gemacht hättest.</p>
<p>Fällt der Anteil unter den eingestellten Mindestwert, verweigert das
Programm die Zahlen und sagt das auch. Das ist Absicht: ein falscher Messwert,
gegen den du wochenlang vergleichst, ist schlimmer als gar keiner.</p>
"""),
        _t("level gain dbfs quiet voiced", "pegel aussteuerung leise stimmhaft")),

    # ---------------------------------------------------------- workflow
    Topic(
        "types", "workflow",
        _t("Recording types", "Aufnahmetypen"),
        _t("""
<p>Every recording is filed under a type, and the type decides what its
numbers are worth.</p>
<ul>
<li><b>Reading text</b> — the practice text, read the same way every session.
Your reference for pitch, intonation and overall delivery. Formants averaged
over it are not meaningful.</li>
<li><b>Pitch test (hum)</b> — a held "mmm" or "ahh" at a comfortable pitch.
The cleanest way to measure pitch, weight and stability, because articulation
is not in the way.</li>
<li><b>Vowel /a/, /i/, /u/</b> — held vowels. These are what make formants,
jitter and shimmer comparable across weeks. /a/ is open, /i/ is front and
high-F2, /u/ is back and rounded; together they sample the space.</li>
<li><b>Free</b> — anything else. Conversation, a phrase, an experiment.</li>
</ul>
<p>The type can be changed afterwards from the right-click menu, so a
mis-filed recording is not lost.</p>
<p>Comparing a reading text against a held vowel produces nonsense. Keeping
types apart is the whole point of having them.</p>
""", """
<p>Jede Aufnahme wird unter einem Typ abgelegt, und der Typ entscheidet, was
ihre Zahlen wert sind.</p>
<ul>
<li><b>Lesetext</b> — der Übungstext, jede Session gleich gelesen. Deine
Referenz für Tonhöhe, Melodie und Sprechweise insgesamt. Über ihn gemittelte
Formanten sind nicht aussagekräftig.</li>
<li><b>Tonhöhentest (Summen)</b> — ein gehaltenes „mhh" oder „ahh" in bequemer
Lage. Der sauberste Weg, Tonhöhe, Schwere und Stabilität zu messen, weil die
Artikulation nicht dazwischenfunkt.</li>
<li><b>Vokal /a/, /i/, /u/</b> — gehaltene Vokale. Sie machen Formanten,
Jitter und Shimmer über Wochen vergleichbar. /a/ ist offen, /i/ ist vorn und
hat hohes F2, /u/ ist hinten und gerundet; zusammen tasten sie den Raum ab.</li>
<li><b>Frei</b> — alles andere. Gespräch, ein Satz, ein Versuch.</li>
</ul>
<p>Der Typ lässt sich über das Kontextmenü nachträglich ändern, eine falsch
abgelegte Aufnahme ist also nicht verloren.</p>
<p>Einen Lesetext gegen einen gehaltenen Vokal zu vergleichen ergibt Unsinn.
Die Typen auseinanderzuhalten ist der ganze Zweck der Sache.</p>
"""),
        _t("type reading vowel hum sustained", "typ lesetext vokal summen gehalten")),

    Topic(
        "advanced", "workflow",
        _t("Advanced mode — analysing a section", "Erweiterter Modus — Ausschnitt auswerten"),
        _t("""
<p>In the detail view, "Advanced" unfolds the waveform of the recording with a
draggable region. Analyse just that region, play just that region.</p>
<p>This exists for one reason: a held vowel has a beginning where you are
still finding the sound and an end where you are running out of air. Both
distort formants, jitter and shimmer. Cutting out the steady middle is what
turns those numbers from noise into something you can track.</p>
<p>The analysis is non-destructive — the stored values stay untouched until you
press "save selection as session values". A yellow note above the table tells
you which range you are currently looking at.</p>
<p>This is the step that turns a held vowel into a number worth tracking, so
it is worth the two clicks.</p>
""", """
<p>In der Detailansicht klappt „Erweitert" die Wellenform der Aufnahme mit
einem ziehbaren Bereich auf. Nur diesen Bereich auswerten, nur ihn
abspielen.</p>
<p>Das gibt es aus einem Grund: ein gehaltener Vokal hat einen Anfang, in dem
du den Laut noch suchst, und ein Ende, in dem dir die Luft ausgeht. Beides
verzerrt Formanten, Jitter und Shimmer. Die ruhige Mitte herauszuschneiden
macht aus diesen Zahlen erst etwas Verfolgbares.</p>
<p>Die Auswertung ist folgenlos — die gespeicherten Werte bleiben unangetastet,
bis du „Auswahl als Sessionwerte speichern" drückst. Ein gelber Hinweis über
der Tabelle sagt, welchen Bereich du gerade siehst.</p>
<p>Genau dieser Schritt macht aus einem gehaltenen Vokal erst eine Zahl, die
sich verfolgen lässt — die zwei Klicks lohnen sich.</p>
"""),
        _t("advanced selection waveform trim region",
           "erweitert auswahl wellenform zuschneiden")),

    Topic(
        "profiles", "workflow",
        _t("Target profiles", "Zielprofile"),
        _t("""
<p>A target profile is a set of ranges each metric should fall into. The
selected profile colours the live readouts green or amber and fills the verdict
column in the detail view.</p>
<p>The three built-in profiles describe <b>pitch only</b>: median, the two
percentiles, intonation width and range. Formant ranges were deliberately left
out, because the literature figures come from sustained vowels while what would
be compared is a median over reading text. A verdict drawn from that would say
nothing.</p>
<p>They are population averages, not prescriptions. Two people with identical
numbers can be perceived completely differently.</p>
<p>You can adjust any built-in profile and press Save, or Save as to keep a
separate one; Reset brings the literature values back. Any of the eighteen
metrics can be switched on and given a range — including F1, F2, F3 and weight,
which makes sense once you are working with sustained vowels.</p>
<p>The most meaningful target is one derived from your own recording: open a
take you like and press "use these values as my target".</p>
<p><b>In the Live view the target starts at "no target" on purpose.</b> A
colour changing while you speak pulls your attention to the screen, and
attention on the screen is attention off your voice.</p>
""", """
<p>Ein Zielprofil ist ein Satz Bereiche, in denen jeder Kennwert liegen soll.
Das gewählte Profil färbt die Live-Kacheln grün oder gelb und füllt die
Bewertungsspalte in der Detailansicht.</p>
<p>Die drei eingebauten Profile beschreiben <b>nur die Tonhöhe</b>: Median, die
beiden Perzentile, Intonationsbreite und Umfang. Formantbereiche fehlen
bewusst, denn die Literaturwerte stammen von gehaltenen Vokalen, verglichen
würde aber ein Median über Lesetext. Eine Bewertung daraus sagte nichts.</p>
<p>Es sind Populationsmittelwerte, keine Vorgaben. Zwei Menschen mit
identischen Zahlen können völlig unterschiedlich wahrgenommen werden.</p>
<p>Du kannst jedes eingebaute Profil anpassen und auf Speichern drücken, oder
über Speichern unter ein eigenes anlegen; Zurücksetzen holt die Literaturwerte
zurück. Jeder der achtzehn Kennwerte lässt sich einschalten und mit einem
Bereich versehen — auch F1, F2, F3 und die Schwere, was sinnvoll wird, sobald
du mit gehaltenen Vokalen arbeitest.</p>
<p>Das aussagekräftigste Ziel ist eines aus deiner eigenen Aufnahme: öffne eine,
die dir gefällt, und drück „Diese Werte als mein Ziel übernehmen".</p>
<p><b>In der Live-Ansicht steht das Ziel bewusst auf „kein Ziel".</b> Eine
Farbe, die sich beim Sprechen ändert, zieht die Aufmerksamkeit auf den
Bildschirm — und die fehlt dann bei der Stimme.</p>
"""),
        _t("target profile goal green amber", "ziel profil grün gelb bewertung")),

    Topic(
        "settings", "workflow",
        _t("Analysis settings", "Analyseparameter"),
        _t("""
<p>These change how the measurement itself is done. The defaults are sensible;
change them when the measurement is clearly wrong, not to make the numbers look
better.</p>
<ul>
<li><b>Silence threshold</b> — below this level nothing is analysed. Lower it
for a quiet microphone.</li>
<li><b>F0 lower and upper limit</b> — the search range for pitch. Set too low,
the tracker invents octave errors; set too high, it cuts off creak and low
sentence endings. A narrow range is more stable.</li>
<li><b>Formant ceiling</b> — Praat's recommendation is 5000 Hz for low and
5500 Hz for high voices. Set wrongly it shifts F1 and F2 systematically, so it
is worth getting right before comparing formants.</li>
<li><b>Zone boundaries</b> — where the display calls a pitch low, ambiguous or
high. Cosmetic; they do not affect measurement.</li>
<li><b>Voicing threshold</b> — how periodic a stretch must be to count as
voice. This is the important one: Praat's autocorrelation finds spurious
periods in noise, and they pile up right at the lower F0 limit. Raising it
makes the analysis stricter.</li>
<li><b>Minimum voiced share</b> — how much of a recording must be voiced before
any values are produced at all. Prevents numbers derived from room noise.</li>
</ul>
<p>Templates store whole sets of these, so you can switch between a quiet
microphone and a sustained-vowel setup without retyping.</p>
""", """
<p>Diese Werte ändern, wie gemessen wird. Die Vorgaben sind vernünftig; ändere
sie, wenn die Messung sichtbar falsch ist, nicht damit die Zahlen schöner
aussehen.</p>
<ul>
<li><b>Stille-Schwelle</b> — unterhalb dieses Pegels wird nicht analysiert. Bei
leisem Mikrofon senken.</li>
<li><b>F0 Unter- und Obergrenze</b> — der Suchbereich für die Tonhöhe. Zu tief
gesetzt erfindet der Tracker Oktavfehler, zu hoch schneidet er Knarrstimme und
tiefe Satzenden weg. Ein enger Bereich ist stabiler.</li>
<li><b>Formant-Obergrenze</b> — Praats Empfehlung sind 5000 Hz für tiefe und
5500 Hz für hohe Stimmen. Falsch gesetzt verschiebt sie F1 und F2
systematisch, das lohnt sich also vor jedem Formantvergleich.</li>
<li><b>Zonengrenzen</b> — ab wo die Anzeige eine Tonhöhe tief, mehrdeutig oder
hoch nennt. Rein kosmetisch, die Messung ändert sich nicht.</li>
<li><b>Stimmhaftigkeit</b> — wie periodisch ein Abschnitt sein muss, um als
Stimme zu gelten. Das ist der wichtige Regler: Praats Autokorrelation findet
in Rauschen Scheinperioden, und die sammeln sich direkt an der unteren
F0-Grenze. Höher heißt strenger.</li>
<li><b>Mindestanteil Stimme</b> — wie viel einer Aufnahme stimmhaft sein muss,
damit überhaupt Werte entstehen. Verhindert Zahlen aus Raumrauschen.</li>
</ul>
<p>Vorlagen speichern ganze Sätze davon, du kannst also zwischen leisem
Mikrofon und Vokalmessung wechseln, ohne alles neu einzutippen.</p>
"""),
        _t("settings parameters threshold praat", "einstellungen parameter schwelle praat")),

    # ---------------------------------------------------------- practice
    Topic(
        "getting_started", "practice",
        _t("Getting your first measurement right", "Die erste Messung richtig machen"),
        _t("""
<p><b>Fix the level before anything else.</b> Open <code>pavucontrol</code>,
recording tab, and raise the input until the level card sits around −20 dB
while you speak normally. Everything else is worthless until this is right.</p>
<p><b>Then record a baseline.</b> Read the practice text once, all of it, as
type "Reading text". Note the numbers.</p>
<p><b>Then the vowels.</b> Record four more takes, each with its own type: the
pitch test (a held hum, about four seconds), then /a/, /i/ and /u/, about three
seconds each. Hold every sound as steadily as you can. That gives you formant
and stability values that will still be comparable in two months.</p>
<p>Afterwards open each of them, unfold “Advanced” and drag the region over the
calm middle — the beginning where you are still finding the sound and the end
where the air runs out both distort the numbers.</p>
<p><b>From then on:</b> ten to fifteen minutes a day beats two hours at the
weekend. Same text, same microphone position, same template every time —
otherwise you are measuring your setup rather than your voice.</p>
<p>Do not read anything into differences between two takes minutes apart. Time
of day, microphone distance and how warmed up you are move these numbers more
than weeks of practice do. Trends need weeks.</p>
""", """
<p><b>Zuerst den Pegel richten, alles andere danach.</b> <code>pavucontrol</code>
öffnen, Reiter Aufnahme, Eingang hochziehen, bis die Pegelkachel beim normalen
Sprechen um die −20 dB anzeigt. Bis das stimmt, ist alles andere wertlos.</p>
<p><b>Dann eine Nullmessung.</b> Den Übungstext einmal komplett lesen, als Typ
„Lesetext". Zahlen notieren.</p>
<p><b>Dann die Vokale.</b> Vier weitere Aufnahmen, jede mit passendem Typ: den
Tonhöhentest (gehaltenes Summen, etwa vier Sekunden), dann /a/, /i/ und /u/ mit
je etwa drei Sekunden. Jeden Laut so ruhig wie möglich halten. Das ergibt
Formant- und Stabilitätswerte, die in zwei Monaten noch vergleichbar sind.</p>
<p>Danach jede davon öffnen, „Erweitert“ aufklappen und den Bereich über die
ruhige Mitte ziehen — der Anfang, in dem du den Laut noch suchst, und das Ende,
in dem die Luft ausgeht, verzerren die Zahlen.</p>
<p><b>Danach gilt:</b> zehn bis fünfzehn Minuten täglich schlagen zwei Stunden
am Wochenende. Immer derselbe Text, dieselbe Mikrofonposition, dieselbe
Vorlage — sonst misst du deinen Aufbau statt deiner Stimme.</p>
<p>Lies nichts in Unterschiede zwischen zwei Aufnahmen hinein, die Minuten
auseinanderliegen. Tagesform, Mikrofonabstand und wie eingesungen du bist
bewegen diese Zahlen stärker als wochenlanges Üben. Für Trends brauchst du
Wochen.</p>
"""),
        _t("start baseline first measurement", "start nullmessung erste messung")),

    Topic(
        "safety", "practice",
        _t("Health and limits", "Gesundheit und Grenzen"),
        _t("""
<p><b>This is a measuring instrument, not a therapy programme.</b> It shows you
what your voice is doing. It does not tell you what to do about it, and it
cannot hear whether you sound good.</p>
<p><b>Never train through pain.</b> If your throat hurts, if it feels scratchy,
or if you are hoarse after a session: stop. Those are signs of too much tension
or pressure, not of effort paying off. An overworked voice takes considerably
longer to recover than it takes to damage.</p>
<p><b>The numbers are not a score.</b> The reference ranges are population
averages. Perception depends on far more than anything measurable here — on
rhythm, word choice, volume, posture, context and on who is listening.</p>
<p><b>This cannot diagnose anything.</b> Jitter, shimmer and harmonicity appear
in clinical literature, but those values come from calibrated equipment.
Persistent hoarseness belongs to an ENT doctor.</p>
<p><b>A speech-language pathologist beats any software.</b> A few sessions with
someone who can actually hear you will save you hundreds of hours of guessing,
because early on you cannot judge your own output reliably. In Germany,
gender-affirming voice therapy is prescribable and covered by statutory health
insurance.</p>
""", """
<p><b>Das hier ist ein Messgerät, kein Therapieprogramm.</b> Es zeigt dir, was
deine Stimme tut. Es sagt dir nicht, was du dagegen tun sollst, und es kann
nicht hören, ob du gut klingst.</p>
<p><b>Trainiere niemals gegen Schmerz.</b> Wenn der Hals wehtut, wenn es
kratzt oder wenn du nach einer Session heiser bist: aufhören. Das sind Zeichen
von zu viel Spannung oder Druck, nicht von Anstrengung, die sich auszahlt.
Einen überlasteten Stimmapparat wieder hinzubekommen dauert erheblich länger,
als ihn zu überlasten.</p>
<p><b>Die Zahlen sind keine Bewertung.</b> Die Zielbereiche sind
Populationsmittelwerte. Wahrnehmung hängt an weit mehr, als hier messbar ist —
an Rhythmus, Wortwahl, Lautstärke, Haltung, Kontext und daran, wer zuhört.</p>
<p><b>Das hier diagnostiziert nichts.</b> Jitter, Shimmer und Harmonizität
kommen in klinischer Literatur vor, aber dort wird mit kalibriertem Gerät
gemessen. Anhaltende Heiserkeit gehört zum HNO.</p>
<p><b>Logopädie schlägt jede Software.</b> Ein paar Stunden mit jemandem, der
dich wirklich hören kann, ersparen dir hunderte Stunden Rumprobieren, weil du
dein eigenes Ergebnis am Anfang nicht zuverlässig beurteilen kannst.
Gendersensible Stimmtherapie ist in Deutschland verordnungs- und
kassenfähig.</p>
"""),
        _t("safety health pain hoarse therapy doctor",
           "gesundheit sicherheit schmerz heiser therapie arzt")),
]

TOPIC_BY_KEY = {topic.key: topic for topic in TOPICS}


def topics_in(section: str) -> list[Topic]:
    return [topic for topic in TOPICS if topic.section == section]


def section_title(section: str) -> str:
    entry = SECTION_TITLES.get(section, {})
    return entry.get(i18n.LANG) or entry.get("en") or section
