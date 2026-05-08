---
name: literature-gap-analysis
description: Use this skill when the user wants to analyze literature coverage, find missing sources, or identify gaps. Triggers on "Literaturlücken / Literaturluecken", "Coverage", "fehlende Quellen", "Gap Analysis", "Quellenabdeckung", "literature gaps", "missing sources", "Abdeckung prüfen / Abdeckung pruefen", or when another skill detects under-sourced chapters. Bewertet Korpus-Vollständigkeit; Für einzelne Quellen-Qualität → `source-quality-audit`.
license: MIT
---

# Literatur-Lückenanalyse

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Analysiert die Literaturbasis auf Abdeckungslücken (fehlende Themen,
Autor*innen-Gruppen, Methoden, Zeiträume). Identifiziert disziplinäre
Blindstellen und liefert konkrete Such-Queries für `/search`. Ergänzt
den `source-quality-audit` (der bewertet Einzelquellen, nicht Korpus).

> **Skill-spezifische Vorbedingung:** Fehlt `./literature_state.md` oder ist
> leer → schlage zuerst `/search` vor, um einen Quellenbestand aufzubauen,
> und trigger diesen Skill danach erneut.

## Abgrenzung

Dieser Skill bewertet **Korpus-Vollständigkeit**:
- Fehlende Schlüsselthemen aus `./academic_context.md`
- Fehlende Autor*innen-Gruppen (Cluster-Diversität)
- Fehlende Methoden-Perspektiven (qualitativ/quantitativ/mixed)
- Fehlende Zeitperioden (Aktualitäts-Lücken)
- Fehlende disziplinäre Sichtweisen (Mono- vs. Multi-Disziplinarität)

Für die Bewertung **einzelner Quellen** (Impact, Methodik der Einzelquelle,
Peer-Review-Status) → `source-quality-audit`.

Beide Skills greifen auf `./literature_state.md` zu, aber mit unterschiedlichem
Fokus. Wenn der User „Peer-Review" oder „Quellenqualität einzelner Artikel"
erwähnt → delegiere an `source-quality-audit`.

## Coverage-Metriken (numerisch)

Berechne und berichte jede dieser 3 Metriken:

1. **Coverage** — Anteil abgedeckter Schlüsselthemen aus `./academic_context.md`
   - Schwelle: ≥ 80 %
   - Formel: `abgedeckte_Themen / gesamte_Schluesselthemen * 100`
2. **Diversity** — Zahl eigenständiger Autor*innen-Gruppen (Co-Autor-Cluster)
   - Schwelle: ≥ 5 Gruppen
   - Zählweise: Autor*innen, die nur untereinander zusammen publizieren, zählen als 1 Gruppe
3. **Recency** — Anteil Quellen ab Publikationsjahr 2020
   - Schwelle: ≥ 40 %
   - Formel: `Quellen_ab_2020 / Gesamtquellen * 100`

Ausgabe: Tabelle Metrik + Ist-Wert + Schwelle + PASS/FAIL + bei FAIL: konkreter
Verbesserungsvorschlag (welches Thema, welche Autor*innen, welcher Zeitraum fehlt).

## Kontext-Dateien

- Lesen: `./academic_context.md` (Gliederung, Schlüsselkonzepte), `./literature_state.md` (Quelleninventar, Kapitelzuordnungen)
- Schreiben: `./literature_state.md` — Coverage-Scores und Gap-Ergebnisse aktualisieren

## Core-Workflow

### 1. Laden und Gegenüberstellen

Beide Kontext-Dateien lesen. Matrix: Zeilen = Kapitel/Unterabschnitte, Spalten = Coverage-Dimensionen (siehe unten).

### 2. Coverage-Dimensionen

Jedes Kapitel entlang dieser Dimensionen bewerten:

#### Quellenanzahl
- 0 Quellen — KRITISCH: keine Abdeckung
- 1-2 Quellen — WARNUNG: dünne Abdeckung
- 3-5 Quellen — OK für Unterabschnitte
- 5+ Quellen — Gut für Hauptkapitel

#### Quellen-Qualität
- Anteil Peer-Review-Quellen pro Kapitel
- Präsenz von Standard-/Grundlagenwerken
- Aktualität — Anteil Quellen aus den letzten 5 Jahren
- Quellen-Diversität — mehrere Autoren, nicht nur eine Forschungsgruppe

#### Argumentations-Balance
- Sind stützende UND gegensätzliche Positionen vertreten?
- Werden alternative Theorien oder Frameworks erwähnt?
- Gibt es mindestens eine Quelle, die das Hauptargument hinterfragt?

#### Methodische Passung
- Referenzieren die Methodikkapitel etablierte Methodenliteratur?
- Wird die gewählte Methode durch zitierte Präzedenzen gestützt?
- Werden Limitationen der Methode mit Quellen diskutiert?

### 3. Coverage-Report erstellen

Einen strukturierten Report im Format aus `## Output-Format` (siehe unten) erzeugen.

### 4. Lücken-Klassifikation

Jede identifizierte Lücke einordnen:

| Lücken-Typ | Beschreibung | Priorität |
|------------|--------------|-----------|
| KRITISCH | Kapitel hat keine Quellen | Sofort |
| STRUKTURELL | Fehlendes Grundlagen-/Standardwerk | Hoch |
| BALANCE | Keine Gegenargumente oder Alternativsichten | Hoch |
| AKTUALITÄT | Alle Quellen älter als 5 Jahre | Mittel |
| TIEFE | Zu wenige Quellen für den Kapitel-Scope | Mittel |
| DIVERSITÄT | Alle Quellen von derselben Autor/Gruppe | Niedrig |

### 5. Such-Empfehlungen

Für jede Lücke eine gezielte Such-Empfehlung erzeugen:

- **Such-Query** — Abgeleitet aus Kapiteltitel, Schlüsselkonzepten und Lücken-Typ
- **Vorgeschlagene Module** — Welche Such-Module liefern am wahrscheinlichsten Treffer
- **Vorgeschlagener Modus** — quick bei kleinen Lücken, deep bei kritischen Lücken
- **Erwarteter Quellentyp** — Journal-Artikel, Konferenzbeitrag, Buchkapitel, Report

Beispiel:
```
GAP: Kapitel 3.2 "DevOps Governance Modelle" — keine Gegenargumente
QUERY: "DevOps governance challenges limitations criticism"
MODULE: semantic_scholar, crossref
MODE: standard
EXPECTED: Journal-Artikel zu Governance-Limitationen
```

### 6. Automatisiertes Lücken-Schließen

Mit User-Freigabe `/search` für jede Lücke mit den empfohlenen Queries triggern. Nach Abschluss:

1. Neue Treffer gegen die Lücken-Anforderungen prüfen
2. Kapitelzuordnung für neue Quellen vorschlagen
3. Coverage-Report aktualisieren
4. Coverage-Scores neu berechnen

### 7. Literaturstatus aktualisieren

`./literature_state.md` lesen, dann Coverage-Scores, Lücken, Empfehlungen und Zeitstempel schreiben.

## Vergleich mit ähnlichen Arbeiten

Prüfen auf: Standardreferenzen des Felds, aktuelle Literaturreviews/Meta-Analysen, Methodenlehrbücher, institutionelle Mindest-Quellenzahl.

Typische Minima nach Arbeitstyp:

| Arbeitstyp | Minimum Quellen | Peer-Review-Minimum |
|------------|-----------------|---------------------|
| Bachelorarbeit | 25-35 | 60% |
| Masterarbeit | 40-60 | 70% |
| Hausarbeit | 10-20 | 50% |

## Output-Format

```
## Literatur-Coverage-Report

### Gesamtbewertung
- Quellen gesamt: [N]
- Peer-reviewed: [N]%
- Durchschnittsalter: [N] Jahre
- Kapitel ohne Quellen: [N]
- Gesamtabdeckung: [SCORE]%

### Kapitelweise Analyse

#### [Kapiteltitel]
- Zugewiesene Quellen: [N]
- Peer-reviewed: [N]%
- Status: [KRITISCH / LÜCKE / AUSREICHEND / GUT]
- Fehlend: [konkrete Lückenbeschreibung]
- Empfehlung: [gezielte Aktion]
```

## Few-Shot-Beispiele

### Stil: Gap-Identifikation

**Schlecht** (Grund: vage ohne konkrete Lücke):

> "Es fehlen noch einige Quellen zu KI und Lehre."

**Gut** (Grund: konkretes Konzept + Zahl + Such-Empfehlung):

> "Unterversorgt: 'formative Bewertung mit KI' — nur 1 Quelle im Korpus.
> Empfehlung: /search 'formative assessment AI higher education 2023-2024'
> mit Modulen semanticscholar + openalex."

### Stil: Corpus-Coverage

**Schlecht** (Grund: unklar was abgedeckt ist):

> "Literaturbasis ist okay."

**Gut** (Grund: Coverage pro Forschungsfrage-Dimension):

> "Abdeckung Forschungsfrage 1 (KI-Adoption): 12 Quellen OK.
> Abdeckung Nebenfrage 2 (ethische Implikationen): 2 Quellen UNTER-SERVIERT."

## Wichtige Regeln

- **Fakten berichten, nicht werten** — Coverage-Daten objektiv präsentieren; der User setzt Prioritäten
- **Vorschlagen, nicht automatisch ausführen** — Vor Such-Triggern immer nachfragen
- **Limitationen anerkennen** — Die Gap-Analyse hängt von korrekten Kapitelzuordnungen im Literaturstatus ab
- **Nach Änderungen neu laufen lassen** — Nach Literatur-Updates eine erneute Analyse vorschlagen
- **Keine Fehlalarme** — Nur Lücken flaggen, wo die Gliederung klar Quellenbedarf vorsieht
