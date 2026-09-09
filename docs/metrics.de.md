# Akustik & Methodik

Was Dream-VoiceTraining misst, wie es das tut und was die Zahlen aussagen —
und was nicht.

[English version](metrics.md) · [zurück zur README](../README.de.md)

---

## Kurzfassung

Eine Aufnahme wird in 10-ms-Abschnitte zerlegt. Für jeden fragt das Programm
Praat — über [parselmouth](https://parselmouth.readthedocs.io/) —, wie hoch
die Grundfrequenz ist, ob der Abschnitt überhaupt stimmhaft ist und wo die
Resonanzen des Ansatzrohrs liegen. Alles Weitere ist Statistik über die
Abschnitte, die stimmhaft zurückkamen.

Der letzte Punkt ist wichtig. Stimmlose Abschnitte — Atem, Pausen,
Konsonanten — fliegen raus, bevor irgendein Mittelwert gebildet wird. Ein
Median über stimmhafte Abschnitte beschreibt, was deine Stimme tut, während
sie klingt, und nicht einen Durchschnitt, den die Stille nach unten zieht.

Sind weniger als 15 % der Aufnahme stimmhaft, gilt sie als *keine verwertbare
Stimme* und es werden gar keine Werte gespeichert. Eine erfundene Zahl ist
schlechter als eine fehlende.

---

## Tonhöhe

Fünf Kennwerte, alle aus derselben stimmhaften Tonhöhenspur.

| Kennwert | Was er ist |
| :--- | :--- |
| **F0 Median** | Die Mitte deiner Tonhöhe in Hz. Median statt Mittelwert: ein einzelner Oktavsprung verschiebt ihn nicht. |
| **F0 unteres Ende** | Das 10. Perzentil — wo der Boden deiner Sprechlage liegt. |
| **F0 oberes Ende** | Das 90. Perzentil — die Decke, ohne die Ausreißer. |
| **Intonationsbreite** | Streuung der Tonhöhenspur in Halbtönen. Wie viel Melodie da ist. |
| **Tonumfang** | Abstand zwischen unterem und oberem Ende, in Halbtönen. |

Die letzten beiden stehen mit Absicht in Halbtönen. Ein Schwanken um 20 Hz bei
100 Hz und dasselbe bei 220 Hz klingen völlig verschieden; in Halbtönen sind
sie, was sie sind — 3,2 und 1,5. In Hertz sähe eine tiefe Stimme lebendig aus
und eine hohe monoton.

Gesucht wird die Tonhöhe standardmäßig zwischen **60 Hz und 500 Hz**. Beide
Grenzen lassen sich unter *Einstellungen → Analyse* verstellen. Ein weiteres
Fenster ist nicht umsonst: je weiter Boden und Decke auseinanderliegen, desto
öfter hält der Algorithmus eine Oberschwingung für den Grundton.

---

## Resonanz

| Kennwert | Was er ist |
| :--- | :--- |
| **F1** | Erster Formant. Grob: wie offen der Vokal ist. |
| **F2** | Zweiter Formant. Grob: wie weit vorn die Zunge steht. Trägt das meiste von dem, was als „helle" oder „dunkle" Stimme gehört wird. |
| **F3** | Dritter Formant. Weniger eine Frage des Vokals, mehr eine der Größe des Raums oberhalb des Kehlkopfs. |

Formanten gehören zum gesprochenen Vokal, nicht zur Stimme an sich. `/i/` hat
bei *jedem* Menschen ein hohes F2 und `/u/` ein tiefes. Das F2 zweier
Lesetexte zu vergleichen funktioniert nur, wenn beide Texte dieselben Vokale
in ungefähr derselben Verteilung enthielten — deshalb gibt es einen festen
Übungstext und den Aufnahmetyp *gehaltener Vokal*.

Für alles, was du über Wochen verfolgen willst: nimm ein gehaltenes `/a/`,
`/i/` oder `/u/` auf und vergleiche Gleiches mit Gleichem. Die
Formantanalyse schaut standardmäßig bis **5000 Hz**.

---

## Schwere und Stimmqualität

| Kennwert | Was er ist | Unauffällig |
| :--- | :--- | :--- |
| **H1 Pegel**, **H2 Pegel** | Pegel der ersten und zweiten Harmonischen in dB. | — |
| **Schwere (H1–H2)** | Die Differenz. Ein großer positiver Wert geht mit behauchter, leichterer Stimmgebung einher, ein kleiner oder negativer mit gepresster, schwererer. | — |
| **Klarheit (HNR)** | Verhältnis von Klang zu Rauschen in dB — wie viel des Signals periodischer Ton ist. | über 15 dB |
| **Jitter (lokal)** | Schwankung der Periodenlänge von Schwingung zu Schwingung. | unter 1,04 % |
| **Shimmer (lokal)** | Schwankung der Amplitude von Schwingung zu Schwingung. | unter 3,81 % |
| **Stimmabbrüche** | Anteil der Aufnahme, in dem die Stimmhaftigkeit mitten im Ton abriss. | unter 5 % |
| **Anzahl Abbrüche** | Wie viele einzelne Aussetzer. | — |
| **Stimmhafter Anteil** | Wie viel der Aufnahme überhaupt stimmhaft war. | über 30 % |
| **Aufnahmepegel** | 95. Perzentil der Abschnittsenergie in dBFS. | −30 bis −8 dBFS |

**Jitter, Shimmer und die beiden Abbruch-Kennwerte sind nur bei einem
gehaltenen Vokal aussagekräftig.** In fließender Rede ist jeder Konsonant eine
berechtigte Unterbrechung, und die Werte fallen aus Gründen hoch aus, die mit
deiner Stimme nichts zu tun haben. Das Detailfenster markiert diese Zeilen
entsprechend. Sie an einem Lesetext abzulesen und sich darüber zu sorgen ist
das häufigste Missverständnis bei diesem Programm.

Der Aufnahmepegel ist kein Stimmwert, sondern eine Kontrolle der Aufnahme.
Unter −30 dBFS ist ein Take zu leise, als dass die Analyse verlässlich wäre,
über −8 dBFS so nah an der Übersteuerung, dass die Harmonischen verzerren. Da
gehört die Eingangsverstärkung nachjustiert, nicht der Take.

---

## Zielprofile

Drei eingebaute Profile, dazu beliebig viele eigene. Die Werte sind
Populationsmittel aus der sprachwissenschaftlichen Literatur, keine Vorgaben,
die jemand erreichen müsste.

| | Maskulin | Androgyn | Feminin |
| :--- | :---: | :---: | :---: |
| **F0 Median** | 85–130 Hz | 145–175 Hz | 180–250 Hz |
| **F0 unteres Ende** | 70–110 Hz | 115–150 Hz | 145–200 Hz |
| **F0 oberes Ende** | 120–200 Hz | 180–250 Hz | 210–300 Hz |
| **Intonationsbreite** | 2,0–4,5 HT | 2,5–5,0 HT | 3,0–5,5 HT |
| **Tonumfang** | 4,0–11,0 HT | 5,0–13,0 HT | 7,0–16,0 HT |

Aus „Populationsmittel" folgt zweierlei. Erstens ist ein Wert außerhalb eines
Bereichs kein Fehler — viele Menschen werden als ihr Ziel gelesen, obwohl sie
daneben liegen, weil die Tonhöhe nur einer von mehreren Hinweisen ist und
nicht der stärkste. Zweitens überlappen die Bereiche, und die Lücken dazwischen
sind kein leerer Raum: bei 144 Hz passiert nichts, was bei 146 Hz nicht auch
passiert.

Ein eigenes Profil lässt sich aus den eigenen Aufnahmen bauen — *Diese Werte
als mein Ziel übernehmen* im Detailfenster — und jeder der achtzehn Kennwerte
einzeln anpassen.

---

## So werden zwei Sessions vergleichbar

Die Auswertung ist wiederholbar. Die Aufnahme ist es meistens nicht, und
daher kommen die meisten unerklärlichen „Veränderungen".

- **Gleiches Mikrofon, gleicher Abstand, gleicher Raum.** Der Abstand ändert
  den Pegel, der Pegel ändert, welche Abschnitte als stimmhaft zählen. Ein
  anderer Raum ändert die Formanten, die du misst, ohne die zu ändern, die du
  erzeugst.
- **Gleiches Material.** Dafür gibt es den Übungstext. Lies ihn ganz und
  jedes Mal gleich — oder nimm einen eigenen und bleib dabei.
- **Gleicher Typ.** Ein gehaltener Vokal und ein Lesetext sind auch am selben
  Tag keine vergleichbaren Messungen. Der Aufnahmetyp steht bei jedem Take
  dabei, danach lässt sich filtern.
- **Ein paar Sekunden mindestens.** Unter 0,3 s wird gar nichts ausgewertet,
  unter ein paar Sekunden sind die Perzentile Rauschen.
- **Wochen vergleichen, nicht Takes.** Die Tagesschwankung einer gesunden
  Stimme ist größer als das meiste, was zu messen sich lohnt. Zwei Aufnahmen
  im Abstand einer Woche sagen mehr als zehn an einem Nachmittag.

---

## Was das Programm nicht kann

Es kann dir nicht sagen, wie du wahrgenommen wirst. Wahrnehmung hängt an
Resonanz, Sprechmelodie, Artikulation, Wortwahl, Tempo und Kontext; hier wird
der akustische Teil gemessen und sonst nichts.

Es kann dir nicht sagen, ob deine Stimme gesund ist. Jitter, Shimmer und HNR
werden klinisch verwendet — von Fachleuten, zusammen mit Untersuchung und
Anamnese. Ein auffälliger Wert hier ist ein Grund, jemanden aufzusuchen, nie
eine Diagnose.

Es kann dir nicht sagen, was du ändern sollst. Es sagt dir, was ist, über die
Zeit. Was daraus folgt, ist genau die Frage, für die es Logopädie gibt — ein
paar Termine sparen hunderte Stunden Ausprobieren, und dieses Programm ist
neben einer Therapie sehr viel nützlicher als anstelle einer.

Und es ist nie ein Grund, gegen Schmerz weiterzumachen. Kratzen, Druckgefühl
oder Heiserkeit heißt aufhören, ganz gleich, was die Zahlen sagen.
