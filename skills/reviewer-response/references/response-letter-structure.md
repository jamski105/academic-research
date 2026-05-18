# Response-Letter-Struktur — Point-by-Point Format

Dieses Dokument definiert das Standardformat für Reviewer-Response-Letters
in wissenschaftlichen Zeitschriften.

---

## Überblick

Ein Response-Letter beantwortet jeden Reviewer-Kommentar einzeln (point-by-point).
Ziel: Dem Editor und den Reviewern zeigen, dass jede Kritik ernst genommen
und systematisch adressiert wurde.

---

## Aufbau des Response-Letters

### 1. Einleitender Brief an den Editor

```
Sehr geehrte/r [Editor-Name],

vielen Dank für die sorgfältige Begutachtung unseres Manuskripts
"[Titel]" (Manuskriptnummer: [Nr.]). Wir danken den Reviewern
für ihre konstruktiven Kommentare und haben das Manuskript entsprechend
überarbeitet.

Im Folgenden beantworten wir jeden Kommentar punkt-für-punkt.
Geänderte Textstellen sind im überarbeiteten Manuskript farblich markiert.

Mit freundlichen Grüßen,
[Autorenname(n)]
```

### 2. Point-by-Point-Antworten

Pro Reviewer einen Abschnitt. Pro Kommentar eine nummerierte Antwort.

**Struktur pro Kommentar:**

```
---
**Reviewer [N], Kommentar [M]:**
> [Kommentartext wörtlich zitiert]

**Antwort:**
[Dankesformel + Erläuterung/Revision]

[Optional: Vault-Quote-Verweis: "Zur Unterstützung dieser Aussage
verweisen wir auf [Quote #<quote_id>]: "[verbatim]" (Autor Jahr, S. [n])."]

[Optional: Manuskript-Änderung: "Wir haben den Text auf S. [X], Z. [Y]
wie folgt geändert: '[neuer Text]'"]
---
```

### 3. Beispiel mit 5 Reviewer-Kommentaren

---

**Reviewer 1, Kommentar 1:**
> Die Stichprobengröße von n=45 erscheint für die gewählte Analyse zu klein.

**Antwort:**
Wir danken dem Reviewer für diesen wichtigen Hinweis.
Eine Power-Analyse (G*Power 3.1) ergab für den verwendeten t-Test
bei mittlerer Effektgröße (d=0.5) und α=.05 eine Teststärke von 1-β=0.78,
was über dem Mindeststandard von 0.80 liegt, wenn man d=0.55 zugrunde legt.
Wir haben die Power-Analyse auf S. 8, Z. 3–7 ergänzt. Vault-Beleg: [Quote #42].

---

**Reviewer 1, Kommentar 2:**
> Die theoretische Einbettung in Kapitel 2 fehlt Bezüge zur neueren Literatur.

**Antwort:**
Wir stimmen zu. Wir haben Kapitel 2 um drei aktuelle Publikationen erweitert
(Müller 2023; Schmidt & Weber 2022; Chen et al. 2021). Die überarbeitete
Passage findet sich auf S. 4–5. Vault-Belege: [Quote #15], [Quote #23].

---

**Reviewer 2, Kommentar 3:**
> Die Operationalisierung von Konstrukt X ist nicht ausreichend begründet.

**Antwort:**
Der Reviewer hat recht, dass die Begründung zu knapp war. Wir haben
Abschnitt 3.2 erweitert und die Wahl des Instruments (MLQ-5X) nun detaillierter
begründet. Insbesondere beziehen wir uns auf die Validierungsstudien
von Bass & Avolio (2004). Vault-Beleg: [Quote #7].

---

**Reviewer 2, Kommentar 4:**
> Es ist unklar, wie mit fehlenden Werten umgegangen wurde.

**Antwort:**
Dies hatten wir im eingereichten Manuskript nicht explizit beschrieben.
Wir haben S. 9, Z. 12–16 ergänzt: Fehlende Werte (2,3% der Fälle)
wurden mittels multipler Imputation (m=10) nach Little & Rubin (2019)
behandelt. Vault-Beleg: [Quote #31].

---

**Reviewer 3, Kommentar 5:**
> Die Diskussion der Limitationen ist zu kurz und sollte ausgebaut werden.

**Antwort:**
Wir danken dem Reviewer für diesen konstruktiven Hinweis.
Wir haben Abschnitt 5.4 (Limitationen) von einem Absatz auf drei Absätze
erweitert. Insbesondere adressieren wir nun: (1) das Querschnittsdesign,
(2) die Selbstauskunfts-Problematik, (3) die Einschränkung auf eine Branche.
Vault-Beleg für methodische Einordnung: [Quote #19].

---

## Vault-Beweise (Vault-Anchored Evidence)

Vault-Quotes werden via `vault.add_quote()` angelegt und als `[Quote #<id>]`
im Response-Letter referenziert:

```python
vault.add_quote(
    paper_id="<paper_id>",
    verbatim="<Zitat-Text>",
    page=<Seitenzahl>,
    context="Beleg fuer Reviewer-Antwort zu Kommentar N"
)
# Gibt quote_id zurück
```

Im Response-Letter:
```
Vault-Beleg: [Quote #<quote_id>]: "[verbatim]" ([Autor Jahr], S. [n])
```

---

## Tonalität-Regeln

1. **Sachlich und respektvoll** — keine Emotionen
2. **Dankbar, aber nicht servil** — einmal "Wir danken" pro Kommentar reicht
3. **Präzise** — konkrete Seitenangaben für alle Änderungen
4. **Transparent** — wenn Reviewer falsch liegt, freundlich korrigieren mit Beleg
5. **Vollständig** — keinen Kommentar unbeantwortet lassen
