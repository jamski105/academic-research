---
name: Submission Checker
description: Dieser Skill wird genutzt, wenn der User vor der Abgabe seiner akademischen Arbeit formale Anforderungen prüfen möchte. Triggers on "formale Pruefung", "Abgabe-Check", "Formatierung pruefen", "abgabefertig", "submission check", "formal requirements", "Deckblatt pruefen", "Eidesstattliche Erklaerung", "Seitenraender", "Formatvorlage", oder wenn der User sich auf die finale Abgabe vorbereitet.
---

# Abgabe-Prüfer

Prüft, ob eine akademische Arbeit alle formalen Abgabeanforderungen erfüllt: Seitenzahl, Formatierung, Quellenzahl, Pflichtabschnitte (Deckblatt, Inhaltsverzeichnis, Eidesstattliche Erklärung, Anhang) und hochschulspezifische Regeln.

## Aktivierung dieses Skills

- Der User fragt, ob seine Arbeit abgabefertig ist
- Der User möchte Formatierung oder formale Anforderungen verifizieren
- Qualitätssicherung vor der Abgabe
- Der User fragt nach konkreten formalen Elementen (Deckblatt, Eidesstattliche Erklärung etc.)

## Memory- und Referenzdateien

- Lies `academic_context.md` für Arbeitstyp, Universität, Studiengang und Zitationsstil
- Lies `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` für hochschulspezifische Formalia
- Lies `writing_state.md` für aktuelle Wortzahlen und Kapitelstatus

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

Gegen Anforderungen aus `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` prüfen:

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

Compliance mit gängigen Formatierungsregeln prüfen:

**Typografie:**
- Schrift: Times New Roman 12pt oder Arial 11pt (je nach Hochschule)
- Zeilenabstand: 1.5
- Ränder: links 3 cm (Bindung), rechts 2.5 cm, oben 2.5 cm, unten 2 cm
- Blocksatz
- Seitenzahlen: arabisch ab Einleitung (Front Matter in römischen Ziffern)

**Überschriften:**
- Konsistente Hierarchie (keine übersprungenen Ebenen)
- Nummerierte Überschriften (1, 1.1, 1.1.1 -- max. 3 Ebenen)
- Keine Schuster-Überschriften (Überschrift am Seitenende, Text beginnt erst auf der nächsten Seite)

**Absätze:**
- Keine Einzelsatz-Absätze
- Konsistente Absatz-Einrückung oder -Abstände

### 4. Quellenzahl und Zitationsqualität

Ausreichende Quellennutzung prüfen:

| Arbeitstyp       | Minimum Quellen |
|------------------|-----------------|
| Bachelorarbeit   | 25-40           |
| Masterarbeit     | 40-60           |
| Hausarbeit       | 10-20           |
| Seminararbeit    | 15-25           |

Prüfen:
- Gesamtzahl eindeutiger Quellen in der Bibliografie
- Alle In-Text-Zitate haben einen Eintrag im Literaturverzeichnis
- Alle Literatureinträge werden im Text mindestens einmal zitiert
- Zitierformat entspricht dem Stil aus `academic_context.md` (APA7, IEEE, Harvard etc.)
- Kein Kapitel ohne Zitate (Ausnahme: Strukturvorschau in der Einleitung und Ausblick im Fazit)

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
- Enthält den geforderten Wortlaut gemäß `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md`
- Enthält Ort-/Datum-Feld
- Enthält Unterschriftenfeld

## Evaluations-Workflow

1. `academic_context.md` lesen, um Arbeitstyp und Hochschule zu bestimmen
2. `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` für spezifische Anforderungen lesen
3. `writing_state.md` für den aktuellen Fertigstellungsgrad lesen
4. Die Arbeit gegen die Checkliste prüfen
5. Jede Dimension als PASS, PARTIAL oder FAIL scoren
6. Ergebnisse strukturiert ausgeben
7. Fixes nach Schweregrad priorisieren

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

- Immer zuerst `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` prüfen -- hochschulspezifische Regeln überschreiben allgemeine Konventionen
- Ist die Datei nicht verfügbar, deutsche Standard-Konventionen nutzen und vermerken, dass hochschulspezifische Prüfung nicht möglich war
- Formatierung nie als korrekt annehmen ohne zu prüfen -- Formatfehler sind der häufigste Grund für Abgabeverzögerungen
- Zwischen harten Anforderungen (FAIL = keine Abgabe möglich) und weichen Empfehlungen (PARTIAL = sollte behoben werden) unterscheiden
- Ist die Arbeit noch nicht fertig, Check auf vorhandene Abschnitte laufen lassen und offene Prüfpunkte benennen
- Ergebnisse auf Deutsch präsentieren, wenn `academic_context.md` Deutsch als Sprache angibt
