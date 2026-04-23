---
name: Literature Gap Analysis
description: Dieser Skill wird genutzt, wenn der User seine Literaturabdeckung analysieren, fehlende Quellen finden oder Lücken in seiner Forschungsbasis identifizieren möchte. Triggers on "Literaturlücken", "Coverage", "fehlende Quellen", "Gap Analysis", "Quellenabdeckung", "literature gaps", "missing sources", "Abdeckung prüfen", oder wenn ein anderer Skill erkennt, dass Kapitel nicht ausreichend quellengestützt sind.
---

# Literatur-Lückenanalyse

Analysiert die Thesis-Gliederung gegen die bestehende Literatursammlung und erzeugt einen kapitelweisen Abdeckungsbericht. Identifiziert gut abgedeckte Themen, fehlende Quellen, fehlende Gegenargumente und methodische Lücken. Bietet gezielte Suche zur Lückenschließung an.

## Vorbedingungen

Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Themenliste in `academic_context.md` kann ich keine Gap-Bewertung
liefern, weil ich gegen unbekannte Ziele vergleichen würde."

## Keine Fabrikation

Erfundene Abdeckungs-Statements oder Quellenlisten sind für die FH Leibniz ein Plagiatsbefund und
führen zu einem Plagiatsverdacht, wenn behauptete Quellen nicht existieren. Arbeite ausschließlich mit Daten aus
`literature_state.md` oder direkt geladenen PDFs. Fehlen Daten: frag den User,
rate nicht.

## Coverage-Metriken (numerisch)

Berechne und berichte jede dieser 3 Metriken:

1. **Coverage** — Anteil abgedeckter Schlüsselthemen aus `academic_context.md`
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

## Aktivierung dieses Skills

- Der User fragt nach Literatur-Abdeckung oder Vollständigkeit
- Der User möchte wissen, welche Kapitel mehr Quellen brauchen
- Ein anderer Skill (Advisor, Chapter Writer, Citation Extraction) meldet unzureichende Quellenlage
- Der User bereitet ein Betreuer-Gespräch vor und möchte einen Statusüberblick

## Memory-Dateien

### Lesen

- `academic_context.md` — Gliederung, Forschungsfrage, Unterfragen, Schlüsselkonzepte
- `literature_state.md` — Quelleninventar, Kapitelzuordnungen, PDF-Status, Zitatanzahlen

### Schreiben

- `literature_state.md` — Ergebnisse der Gap-Analyse und Coverage-Scores aktualisieren

## Voraussetzungen

Beide Dateien, `academic_context.md` (mit Gliederung) und `literature_state.md` (mit mindestens einigen Quellen), müssen existieren. Fehlt eines:

- Kein akademischer Kontext — Academic-Context-Skill triggern
- Kein Literaturstatus — zuerst `/search` vorschlagen, um einen Quellenbestand aufzubauen

## Core-Workflow

### 1. Laden und Gegenüberstellen

Beide Memory-Dateien lesen. Eine Matrix aufbauen:

- **Zeilen** — Kapitel und Unterabschnitte aus der Gliederung
- **Spalten** — Coverage-Dimensionen (siehe unten)

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

Einen strukturierten Report im folgenden Format erzeugen:

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

Nach der Analyse:

1. `literature_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Ergebnisse schreiben: pro-Kapitel-Coverage-Scores, identifizierte Lücken, Empfehlungen
3. Zeitstempel der letzten Analyse aktualisieren

## Vergleich mit ähnlichen Arbeiten

Bei der Vollständigkeitsbewertung berücksichtigen:

- **Standardreferenzen** — Sind die üblichen Grundlagenwerke des Felds enthalten?
- **Aktuelle Reviews** — Gibt es aktuelle Literaturreviews oder Meta-Analysen?
- **Methodenreferenzen** — Werden Standard-Methodenlehrbücher zitiert?
- **Institutionelle Anforderungen** — Erfüllt die Quellenzahl das für den Arbeitstyp erwartete Minimum?

Typische Minima nach Arbeitstyp:

| Arbeitstyp | Minimum Quellen | Peer-Review-Minimum |
|------------|-----------------|---------------------|
| Bachelorarbeit | 25-35 | 60% |
| Masterarbeit | 40-60 | 70% |
| Hausarbeit | 10-20 | 50% |

## Wichtige Regeln

- **Fakten berichten, nicht werten** — Coverage-Daten objektiv präsentieren; der User setzt Prioritäten
- **Vorschlagen, nicht automatisch ausführen** — Vor Such-Triggern immer nachfragen
- **Limitationen anerkennen** — Die Gap-Analyse hängt von korrekten Kapitelzuordnungen im Literaturstatus ab
- **Nach Änderungen neu laufen lassen** — Nach Literatur-Updates eine erneute Analyse vorschlagen
- **Keine Fehlalarme** — Nur Lücken flaggen, wo die Gliederung klar Quellenbedarf vorsieht
