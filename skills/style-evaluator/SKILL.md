---
name: style-evaluator
description: Use this skill when the user wants to evaluate academic writing style (without source comparison). Triggers on "Stil prüfen / Stil pruefen", "Schreibstil", "Satzlänge / Satzlaenge", "Passiv-Quote", "Nominalstil", "style evaluation", or when a chapter draft needs stylistic review. Bewertet Stil-Qualität ohne Quellenbezug; Für Textähnlichkeit → `plagiarism-check`.
license: MIT
---

# Stil-Evaluator

## Übersicht

Bewertet Menschlichkeit, KI-Detektions-Anfälligkeit, Kohärenz, Duplikation
und akademische Qualität von Text. Gewichteter 0-100-Score über 5 Dimensionen.
Bietet Rewrite-Vorschläge für geflaggte Stellen ohne Bedeutung zu verlieren.

## Vorbedingungen

Bevor du startest: Prüfe, ob `./academic_context.md` und `./literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Text-Korpus-Kontext in `./writing_state.md` kann ich kein Stil-Urteil
liefern, weil ich gegen disziplinfremde Normen urteilen würde."

## Keine Fabrikation

Erfundene Stil-Urteile über nicht gelesenen Text lassen tatsächlich fragwürdigen
Stil unentdeckt und untergraben den Wert des Stil-Checks. Arbeite ausschließlich
mit dem eingereichten User-Text und den Metriken aus `./writing_state.md`.
Fehlen Daten: frag den User, rate nicht.

## Abgrenzung

Bewertet Stil-Qualität ohne Quellenbezug (Satzlänge, Passiv-Quote, Nominalstil,
KI-Detektions-Muster, Füllwörter-Dichte).
Für Ähnlichkeit zu konkreten Quellen → `plagiarism-check`.

## Fallback-Rubrik (ohne Script)

Wenn kein externes Stil-Analyse-Script verfügbar ist, prüfe manuell gegen
diese 5 Schwellen:

| Metrik | Schwelle | Messverfahren |
|---|---|---|
| **Satzlänge (Ø)** | 15–25 Wörter | 20 zufällige Sätze, Mittelwert |
| **Passiv-Quote** | < 30 % | "wird/werden/wurde/wurden + Partizip II" in Stichprobe 20 Sätze |
| **Nominalstil-Anteil** | < 40 % | Sätze mit ≥ 3 Nominalphrasen (auf "-ung/-heit/-keit/-tion") in Stichprobe |
| **Füllwörter-Dichte** | < 5 % | "quasi, eigentlich, irgendwie, sozusagen, gewissermaßen" vs. Gesamtwörter |
| **Code-Switches** | 0 | Englische Wörter außerhalb etablierter Fachbegriffe |

Ausgabe: Tabelle Metrik + Ist-Wert + Schwelle + PASS/FAIL.

## Aktivierung dieses Skills

- Der User reicht Text zur Qualitäts- oder Stilbewertung ein
- Der User befürchtet, dass der Text zu KI-generiert klingt
- Der User bittet um Textverbesserung oder natürlicheres Schreiben
- Ein anderer Skill (z. B. `chapter-writer`) fordert ein Post-Write-Qualitätsgate an

## Variant-Selector

Lies `./academic_context.md`, Feld `Sprache`:

| Sprache | Referenz-Datei |
|---------|----------------|
| Deutsch (Default) | `references/academic-de.md` |
| English | `references/academic-en.md` |

Fehlt das Feld → `academic-de.md` als Default (Plugin-Default ist Deutsch). Unbekannte Sprache → Rueckfrage.

## Kontext-Dateien

- Lies `./writing_state.md` für aktuellen Kapitelkontext und frühere Scores
- Lies `./academic_context.md` für Zitationsstil, Sprache und Arbeitstyp
- Aktualisiere `./writing_state.md` nach jedem Lauf mit neuen Bewertungsscores

## Metriken

Die quantitativen Metriken (Satzlängenverteilung, Übergangsfrequenz, Vokabular-Diversität, n-Gramm-Wiederholung) berechnet Claude direkt aus dem Eingabetext — keine externe Pipeline. Siehe Rubrik unten für konkrete Messvorschriften pro Dimension.

## Scoring-Rubrik (0-100)

Jede Dimension unabhängig bewerten, dann gewichteten Gesamtwert bilden.

### 1. Menschlichkeit (Gewicht: 0.30)

Wirkt der Text authentisch menschlich geschrieben?

Indikatoren für NIEDRIGE Menschlichkeit (Abzüge):
- Standardabweichung der Satzlänge unter 4 Wörtern (zu uniform)
- Mehr als 30 % der Sätze beginnen mit demselben syntaktischen Muster
- Fehlen von Hedging-Sprache, Einschränkungen oder vorsichtigen Formulierungen
- Keine rhetorischen Fragen, Einschübe oder Ich-Perspektive, wo angemessen
- Absatzlängen zu uniform (alle innerhalb 10 % des Durchschnitts)

Indikatoren für HOHE Menschlichkeit (Pluspunkte):
- Natürliche Variation der Satzlänge (kurz und lang gemischt)
- Gelegentliche informelle Konnektoren neben formalen
- Topic Sentences variieren zwischen Absätzen
- Spürbare persönliche analytische Stimme

### 2. Anti-KI-Detektion (Gewicht: 0.25)

Muster flaggen, die KI-Detektoren (GPTZero, Turnitin AI, Originality.ai) häufig identifizieren.

Prüfen auf:
- **Uniforme Satzlängen** -- Standardabweichung berechnen; flag bei < 5 Wörtern
- **Wiederholte Übergänge** -- Flag, wenn "Darüber hinaus", "Furthermore", "Moreover", "Zusätzlich", "In conclusion" mehr als zweimal je 1000 Wörter auftauchen
- **Fehlende persönliche Stimme** -- Flag bei null Ich-Pronomen dort, wo Methodik oder Meinung erwartet werden
- **Zu perfekte Struktur** -- Flag, wenn jeder Absatz identisch dem Muster Topic-Evidenz-Analyse folgt
- **Lexikalische Vorhersagbarkeit** -- Flag, wenn die 10 häufigsten Content-Wörter über 15 % aller Content-Wörter ausmachen
- **Burstiness-Score** -- Variation der Perplexität pro Satz messen; bei zu flachem Verlauf flaggen

### 3. Kohärenz (Gewicht: 0.20)

Logischen Fluss zwischen Sätzen und Absätzen bewerten.

Prüfen auf:
- Themen-Kontinuität (jeder Absatz bringt das Argument voran)
- Logik-Konnektoren passen zur tatsächlichen logischen Relation
- Keine waisen Aussagen (Behauptungen ohne vorausgehenden Kontext oder nachfolgende Evidenz)
- Saubere Übergänge zwischen Abschnitten
- Konsistente Terminologie (kein unerklärter Synonym-Wechsel)

### 4. Duplikations-Erkennung (Gewicht: 0.15)

Interne Wiederholung im Text identifizieren.

Prüfen auf:
- Wiederholte Phrasen (3+ Wörter, mehr als zweimal)
- Paraphrasierte Duplikate (dieselbe Idee in benachbarten Absätzen)
- Redundante Einleitungs-/Abschlusssätze über Abschnitte hinweg
- Copy-Paste-Artefakte

### 5. Akademische Qualität (Gewicht: 0.10)

Formale akademische Standards bewerten.

Prüfen auf:
- Saubere Zitat-Integration (nicht nur Klammer-Drops)
- Argumentationsstruktur (Claim, Evidenz, Analyse)
- Register-Konsistenz (keine umgangssprachlichen Brüche in formalen Stellen, keine überformale Sprache in Anwendungsabschnitten)
- Terminologische Präzision
- Angemessener Einsatz von Passiv vs. Aktiv je nach Disziplin

## Evaluations-Workflow

1. Den eingereichten Text lesen (vollständiges Kapitel, Abschnitt oder Absatz)
2. `./writing_state.md` und `./academic_context.md` für Kontext lesen
3. Berechne quantitative Metriken inline aus dem Eingabetext (Satzlängen, Übergänge, n-Gramme, Vokabular-Diversität)
4. Jede Dimension (0-100) nach Rubrik und Metriken scoren
5. Gewichteten Gesamtwert berechnen: `total = 0.30*human + 0.25*anti_ai + 0.20*coherence + 0.15*duplication + 0.10*academic`
6. Ergebnisse strukturiert präsentieren (siehe Output-Format unten)
7. `./writing_state.md` mit den neuen Scores aktualisieren

## Output-Format

Ergebnisse präsentieren als:

```
## Stil-Bewertung: [Abschnitt/Kapitel]

| Dimension            | Score | Status |
|----------------------|-------|--------|
| Menschlichkeit       | XX    | OK/WARN/FAIL |
| Anti-KI-Detektion    | XX    | OK/WARN/FAIL |
| Kohärenz             | XX    | OK/WARN/FAIL |
| Duplikation          | XX    | OK/WARN/FAIL |
| Akademische Qualität | XX    | OK/WARN/FAIL |
| **Gesamt**           | **XX**| **STATUS** |

### Geflaggte Probleme
[Jedes Problem mit Position und Severity auflisten]

### Rewrite-Vorschläge
[Konkrete Neufassungen für WARN/FAIL-Stellen unter Bedeutungserhalt]
```

Status-Schwellen: OK >= 75, WARN 50-74, FAIL < 50.

## Rewrite-Modus

Bei Bitte um Neuformulierung geflaggter Abschnitte:

1. Geflaggte Passage isolieren
2. Exakte Argumentation und alle Zitate bewahren
3. Satzstruktur, -länge und Satzanfänge variieren
4. Wo sinnvoll, natürliches Hedging einbauen ("Dies deutet darauf hin...", "Es erscheint...")
5. Zu symmetrische Absatzstrukturen aufbrechen
6. Neufassung bewerten und Score-Verbesserung bestätigen

## Wichtige Regeln

- Nie Metriken fabrizieren -- berechne alle Werte nachvollziehbar aus dem Text und zeige die Rechenbasis, wenn der User danach fragt
- Bei Rewrites immer Argumentation und Zitate des Autors erhalten
- Konservativ scoren -- eine 100 ist für keinen Text realistisch
- Flaggen ja, automatisch umschreiben ohne User-Zustimmung nein
- Deutsche Labels im Output, wenn `./academic_context.md` Deutsch als Sprache angibt
- Score-Historie in `./writing_state.md` pflegen, um Verbesserung über die Zeit zu zeigen

## Few-Shot-Beispiele

### Stil: Anti-KI-Detektion

**Schlecht** (Grund: uniforme Satzlänge, erwartbare Transitionen):

> "Darüber hinaus ist Digitalisierung wichtig. Furthermore können
> Unternehmen profitieren. Moreover ist Geschwindigkeit ein Faktor."

**Gut** (Grund: variierte Syntax, natürliche Hedges):

> "Digitalisierung bleibt zentral. Unternehmen profitieren — allerdings
> nur, wenn Geschwindigkeit nicht das einzige Kriterium ist."

### Stil: Rewrite mit Argument-Erhalt

**Schlecht** (Grund: Rewrite verändert Argumentation):

> Original: "Die Stichprobe ist klein (n=8), daher explorativ."
> Rewrite: "Die Stichprobe ist klein, aber repräsentativ."

**Gut** (Grund: Rewrite erhält Argumentation, variiert Struktur):

> Original: "Die Stichprobe ist klein (n=8), daher explorativ."
> Rewrite: "Mit n=8 bleibt die Studie explorativ — die Ergebnisse
> skizzieren Hypothesen, sie prüfen sie nicht."
