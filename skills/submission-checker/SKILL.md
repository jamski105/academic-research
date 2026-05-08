---
name: submission-checker
description: Use this skill when the user prepares final submission (formalia check). Triggers on "Abgabe prüfen / Abgabe pruefen", "FH-Leibniz-Formalia", "Formatierung", "Seitenränder / Seitenraender", "Zeilenabstand", "Schriftart", "submission check", or when the user nears deadline. Prüft institutsspezifische Formalia; Default-Profil FH Leibniz, weitere via `references/<variant>.md`.
license: MIT
---

# Abgabe-Prüfer

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Prüft Formalia vor Abgabe: Pflichtabschnitte, Seitenumfang, Formatierung,
Quellenzahl, Abbildungen/Tabellen, eidesstattliche Erklärung. Verwendet
hochschulspezifische Regeln aus `references/<variant>.md` (Default:
FH Leibniz).

## Abgrenzung

Prüft Formalia der Enddatei gegen Hochschul-Regeln.
Für Abstract, Keywords, Management-Summary → `abstract-generator`.
Für den Titel selbst → `title-generator`.
Für Kontextdaten (Arbeitstyp, Hochschule) → `academic-context`.

## Variant-Selector

Lies `./academic_context.md`, Feld `Universitaet` und/oder `Arbeitstyp`:

| Kontext | Referenz-Datei |
|---------|----------------|
| FH Leibniz (Default) | `references/fh-leibniz.md` |
| Andere deutsche Uni | `references/uni-general.md` |
| IEEE-Konferenz/-Journal | `references/journal-ieee.md` |
| ACM-Konferenz/-Journal | `references/journal-acm.md` |

Fehlt das Feld → `fh-leibniz.md` als Default (Plugin-Default ist FH Leibniz). Unbekannt → Rueckfrage.

## Kontext- und Referenzdateien

- `./academic_context.md` — Arbeitstyp, Universität, Zitationsstil
- `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/references/fh-leibniz.md` — hochschulspezifische Formalia
- `./writing_state.md` — Wortzahlen, Kapitelstatus

## Checklisten-Dimensionen

### 1. Pflichtabschnitte

Präsenz aller verpflichtenden Abschnitte in der korrekten Reihenfolge prüfen:

**Front Matter:**
- [ ] Deckblatt -- Titel, Autor:in, Matrikelnummer, Betreuer:in, Abgabedatum, Hochschullogo
- [ ] Abstract (falls für den Arbeitstyp erforderlich)
- [ ] Inhaltsverzeichnis -- mit Seitenzahlen
- [ ] Abbildungsverzeichnis -- falls Abbildungen enthalten sind
- [ ] Tabellenverzeichnis -- falls Tabellen enthalten sind
- [ ] Abkürzungsverzeichnis -- falls Abkürzungen verwendet werden

**Hauptteil:**
- [ ] Einleitung -- mit Forschungsfrage, Methodik-Überblick, Strukturvorschau
- [ ] Hauptkapitel -- laut Gliederung
- [ ] Fazit/Schluss -- mit Zusammenfassung, Limitationen, Ausblick

**Back Matter:**
- [ ] Literaturverzeichnis -- alle zitierten Quellen, korrekt formatiert
- [ ] Anhang -- falls im Text referenziert
- [ ] Eidesstattliche Erklärung -- unterzeichnete Erklärung eigenständiger Arbeit

### 2. Seitenzahl und Umfang

Gegen Anforderungen aus `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/references/fh-leibniz.md` prüfen:

| Arbeitstyp       | Typischer Umfang (Seiten) |
|------------------|---------------------------|
| Bachelorarbeit   | 30-50                     |
| Masterarbeit     | 60-80                     |
| Hausarbeit       | 12-20                     |
| Seminararbeit    | 15-25                     |
| Facharbeit       | 8-15                      |

Verifizieren:
- Gesamtseitenzahl im zulässigen Rahmen
- Front Matter und Back Matter nicht mitgezählt (falls die Hochschule das verlangt)
- Kein Kapitel überproportional lang oder kurz

### 3. Formatierung

**Typografie:** Schrift Times New Roman 12pt/Arial 11pt, Zeilenabstand 1.5, Ränder links 3cm/rechts 2.5cm/oben+unten 2.5cm/2cm, Blocksatz, Seitenzahlen arabisch ab Einleitung.

**Überschriften:** Konsistente Hierarchie, nummeriert (max. 3 Ebenen), keine Schuster-Überschriften.

**Absätze:** Keine Einzelsatz-Absätze, konsistente Einrückung.

### 4. Quellenzahl und Zitationsqualität

Ausreichende Quellennutzung prüfen:

| Arbeitstyp       | Minimum Quellen |
|------------------|-----------------|
| Bachelorarbeit   | 25-40           |
| Masterarbeit     | 40-60           |
| Hausarbeit       | 10-20           |
| Seminararbeit    | 15-25           |

Prüfen: Quellenzahl, In-Text↔Bibliographie-Abgleich, Zitierformat (aus `./academic_context.md`), kein zitatfreies Kapitel (außer Intro-Vorschau + Ausblick).

### 5. Abbildungen und Tabellen

Falls Abbildungen oder Tabellen vorhanden:
- Jede hat eine nummerierte Beschriftung ("Abbildung 1:", "Tabelle 1:")
- Jede wird im Text referenziert
- Nummerierung sequenziell und konsistent
- Quellenangabe unter jeder Abbildung/Tabelle
- Abbildungs-/Tabellenverzeichnis im Front Matter stimmt mit dem Inhalt überein

### 6. Eidesstattliche Erklärung

Verifizieren:
- Vorhanden als letzte Seite (oder gemäß hochschulspezifischer Platzierungsregel)
- Enthält den geforderten Wortlaut gemäß `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/references/fh-leibniz.md`
- Enthält Ort-/Datum-Feld
- Enthält Unterschriftenfeld

## Evaluations-Workflow

1. Kontext-Dateien lesen (academic_context → Arbeitstyp/Hochschule, fh-leibniz.md → Anforderungen, writing_state → Fertigstellung)
2. Arbeit gegen Checkliste prüfen, Dimensionen PASS/PARTIAL/FAIL scoren
3. Strukturiert ausgeben, Fixes nach Schweregrad priorisieren

## Output-Format

```
## Abgabe-Check: [Arbeitstitel]

**Typ:** [Arbeitstyp] | **Uni:** [Hochschule] | **Datum:** [Prüfdatum]

### Ergebnis-Übersicht

| Prüfbereich           | Status              | Details           |
|-----------------------|---------------------|-------------------|
| Pflichtabschnitte     | PASS/PARTIAL/FAIL   | [X/Y vorhanden]   |
| Seitenumfang          | PASS/PARTIAL/FAIL   | [N Seiten]        |
| Formatierung          | PASS/PARTIAL/FAIL   | [Issues count]    |
| Quellenanzahl         | PASS/PARTIAL/FAIL   | [N Quellen]       |
| Abbildungen/Tabellen  | PASS/PARTIAL/FAIL   | [Issues count]    |
| Eidesstattl. Erkl.    | PASS/PARTIAL/FAIL   | [vorhanden/fehlt] |

### Kritische Mängel (sofort beheben)
[FAIL-Punkte mit konkreten Fix-Anweisungen auflisten]

### Empfehlungen (sollte behoben werden)
[PARTIAL-Punkte mit Verbesserungsvorschlägen auflisten]

### Bestanden
[PASS-Punkte zur Bestätigung auflisten]
```

## Wichtige Regeln

- Immer zuerst `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/references/fh-leibniz.md` prüfen -- hochschulspezifische Regeln überschreiben allgemeine Konventionen
- Ist die Datei nicht verfügbar, deutsche Standard-Konventionen nutzen und vermerken, dass hochschulspezifische Prüfung nicht möglich war
- Formatierung nie als korrekt annehmen ohne zu prüfen -- Formatfehler sind der häufigste Grund für Abgabeverzögerungen
- Zwischen harten Anforderungen (FAIL = keine Abgabe möglich) und weichen Empfehlungen (PARTIAL = sollte behoben werden) unterscheiden
- Ist die Arbeit noch nicht fertig, Check auf vorhandene Abschnitte laufen lassen und offene Prüfpunkte benennen
- Ergebnisse auf Deutsch präsentieren, wenn `./academic_context.md` Deutsch als Sprache angibt

## Few-Shot-Beispiele

### Stil: Formalia-Bewertung

**Schlecht** (Grund: PASS ohne dokumentierte Prüfung):

> "Formatierung ist OK."

**Gut** (Grund: dimensionaler Score mit konkretem Prüfpunkt):

> "Formatierung: PARTIAL. Zeilenabstand 1.0 statt geforderten 1.5
> (Seiten 12-18). Fix: Absätze 12-18 markieren, Zeilenabstand in
> Formatvorlage 'Standard' auf 1.5 setzen."
