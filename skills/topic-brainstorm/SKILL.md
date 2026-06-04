---
name: topic-brainstorm
description: Use this skill when the user needs help finding or evaluating a thesis topic. Triggers on "welches Thema?", "Themenfindung", "Idee evaluieren", "Thema gesucht", "ich brauche ein Thema", "welches Thema lohnt", "Thema für Bachelorarbeit / Thema fuer Bachelorarbeit", "Thema für Masterarbeit", or when academic-context is missing a topic. Fokus auf strategische Themensuche und Bewertung; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`.
license: MIT
---

# Topic-Brainstorm Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

> **Override Vorbedingungen:** Kein bestehendes `./academic_context.md` erforderlich —
> dieser Skill hilft dabei, das Thema erst zu finden.

## Übersicht

Unterstützt den User bei der strategischen Themenfindung: 3-5 Topic-Kandidaten
mit Feasibility-, Novelty- und Career-Fit-Scores, 2-3 Forschungsfragen pro
Kandidat und ein Pilot-Paper-Set. Übergang zu `research-question-refiner` nahtlos.

## Abgrenzung

Hilft beim Finden eines Themas (Erstanlage/Bewertung).
Für Schärfung einer bestehenden Forschungsfrage → `research-question-refiner`.
Für Gliederung und Methodik → `advisor` / `methodology-advisor`.

## Kontext-Dateien

- Lesen: `./academic_context.md` (falls vorhanden — Studiengang, Präferenzen)
- Schreiben: `./academic_context.md` — Thema des gewählten Top-Topics eintragen

## Core-Workflow

### Schritt 1: Eingaben sammeln

Stelle dem User vier strukturierte Fragen via `AskUserQuestion`:

```
Für eine gute Themenempfehlung brauche ich vier Angaben:

1. Studienrichtung?
   - Wirtschaftsinformatik (Bachelor/Master)
   - BWL / Betriebswirtschaft
   - Informatik
   - Maschinenbau
   - Andere → freitext

2. Interessensgebiete (frei, z.B. "Cyber Security, KI, Nachhaltigkeit")

3. Zeitbudget?
   - 3 Monate
   - 6 Monate
   - 12 Monate

4. Datenzugang?
   - Public Datasets (Kaggle, STATISTA, Eurostat usw.)
   - Literatur-Only (kein eigener Datensatz)
   - Interview-fähig (Zugang zu Experten/Unternehmen)
   - Unternehmensdaten (NDA-Umgebung)
```

### Schritt 2: Scorer aufrufen

Rufe `skills/topic-brainstorm/scripts/scorer.py` auf mit den gesammelten Werten:

```bash
python skills/topic-brainstorm/scripts/scorer.py \
  --interests "<INTERESSEN>" \
  --field "<STUDIENRICHTUNG>" \
  --budget "<ZEITBUDGET>" \
  --data-access "<DATENZUGANG>" \
  --output-mode full
```

### Schritt 3: Ergebnisse präsentieren

Präsentiere die 5 Kandidaten in dieser Tabellenform:

```
## Topic-Kandidaten

| # | Thema | Feasibility | Novelty | Career-Fit | Gesamt |
|---|-------|-------------|---------|------------|--------|
| 1 | [Titel] | X/10 | X/10 | X/10 | XX/30 |
...

**Empfehlung: [Top-Topic-Titel]** (Score: XX/30)
```

Zeige pro Topic:
- Die 2-3 Forschungsfragen
- Das Pilot-Paper-Set (1-3 Referenzen)

Score-Legende (aus `skills/topic-brainstorm/references/scoring-criteria.md`):
- **Feasibility**: Datenverfügbarkeit + Zeitaufwand + Methoden-Match
- **Novelty**: Lücken-Indikator (Anzahl recent vs. older papers in area)
- **Career-Fit**: Schlagwort-Überschneidung mit Studienrichtung + Berufsbild

### Schritt 4: User-Auswahl und Context-Update

Frage den User, welches Thema er wählt:

```
Welches Thema möchtest du weiterverfolgen?
(1) [Titel 1] — Empfehlung
(2) [Titel 2]
...
Oder: Eigene Variante (freitext)
```

Nach Auswahl:
1. Rufe Scorer erneut mit `--write-context ./academic_context.md` auf
   (oder schreibe das Thema direkt in die Datei)
2. Bestätige die Speicherung: "Das Thema wurde in `academic_context.md` eingetragen."

### Schritt 5: Handover zu research-question-refiner

Beende mit einem Soft-Handover-Hinweis:

```
Das Thema ist jetzt in deinem akademischen Kontext gespeichert.

Nächster Schritt: Forschungsfrage präzisieren
→ Sag "Forschungsfrage formulieren" oder "Fragestellung schärfen",
  um den `research-question-refiner` zu starten und aus den
  vorgeschlagenen Forschungsfragen eine präzise Hauptfrage zu entwickeln.
```

## Scoring-Dimensionen

Drei Scores (je 0-10), Summe ergibt den Gesamtscore (0-30):

- **Feasibility**: Datenverfügbarkeit + Zeitaufwand + Methoden-Match
- **Novelty**: Forschungslücken-Heuristik (Stichwort-Überschneidung mit Interessensgebieten)
- **Career-Fit**: Schlagwort-Überschneidung mit Studienrichtung

Scoring-Kriterien (alle Modifikator-Tabellen für Datenverfügbarkeit, Zeitbudget
und Studienrichtung) siehe `skills/topic-brainstorm/references/scoring-criteria.md`.

## Wichtige Regeln

- **Keine Themen aufdrängen** — 5 Optionen zeigen, User entscheidet
- **Scores transparent erklären** — Immer die Scoring-Kriterien kurz erläutern
- **Pilot-Papers sind Hinweise, keine Gewissheiten** — Darauf hinweisen, dass reale Literaturrecherche folgen muss
- **Vor dem Schreiben bestätigen** — Explizit fragen, ob das Thema in `academic_context.md` gespeichert werden soll
- **Handover sanft** — Nicht erzwingen; research-question-refiner als Hinweis, nicht als Pflicht
- **Deutsche Ausgabe** — Alle User-facing Texte auf Deutsch
