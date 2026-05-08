---
name: academic-context
description: Use this skill whenever the user starts or updates a thesis, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit or academic paper. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", "akademischer Kontext prüfen / akademischer Kontext pruefen", or when another skill needs context that does not yet exist. Fokus auf Erstanlage und Verwaltung des Kontexts; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`.
license: MIT
---

# Akademischer Kontext

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

> **Override Vorbedingungen:** Keine Vorbedingungen — dieser Skill bootet den
> Kontext. Alle anderen Skills setzen voraus, dass `./academic_context.md`
> existiert, und triggern diesen Skill bei Fehlen.

## Übersicht

Bootet den akademischen Kontext einer Arbeit: Thema, Forschungsfrage,
Arbeitstyp, Methodik, Disziplin, Hochschule. Schreibt das Ergebnis in
`./academic_context.md` als Single Source of Truth für alle anderen Skills.

## Kontext-Dateien

Alle im aktuellen Projekt-Ordner (cwd):
- `./academic_context.md` — Arbeitsprofil, Forschungsfrage, Methodik, Gliederung, Fortschritt
- `./literature_state.md` — Quellen-Inventar, Kapitelzuordnungen, Lücken
- `./writing_state.md` — Kapitelstatus, Wortzahlen, Style-Scores

## Core-Workflow

### Erstaktivierung (noch kein Kontext vorhanden)

Existiert keine `./academic_context.md` im Projekt-Ordner, sammle im Gespräch folgende Informationen:

1. **Universität und Studiengang** — Default: Leibniz FH Hannover, BWL/Wirtschaftsinformatik
2. **Arbeitstyp** — Bachelorarbeit, Masterarbeit, Hausarbeit, Seminararbeit, Facharbeit
3. **Thema** — Arbeitstitel der Abschlussarbeit
4. **Forschungsfrage** — Hauptfrage und Unterfragen
5. **Methodik** — Literaturreview, Fallstudie, empirisch, Mixed Methods
6. **Zitationsstil** — Default: APA7 (unterstützt auch IEEE, Harvard, Chicago, MLA)
7. **Sprache** — Default: Deutsch
8. **Betreuer** — Name (optional)
9. **Abgabetermin** — Datum (optional)
10. **Gliederung** — Kapitelstruktur, falls schon geplant

Schreibe die gesammelten Informationen in `./academic_context.md` mit dieser Struktur:

```markdown
---
name: academic-context
description: Akademischer Kontext der aktuellen Abschlussarbeit
type: project
---

### Profil
- Universität: [...]
- Studiengang: [...]
- Zitationsstil: [...]
- Sprache: [...]

### Arbeit
- Typ: [...]
- Thema: [...]
- Forschungsfrage: [...]
- Unterfragen: [...]
- Methodik: [...]
- Betreuer: [...]
- Abgabetermin: [...]

### Gliederung
[Nummerierte Gliederung, falls vorhanden]

### Schlüsselkonzepte
[Schlüsselkonzepte mit Kurzbeschreibung]

### Fortschritt
[Checkliste abgeschlossener/in Bearbeitung befindlicher Elemente]
```

### Update-Aktivierung (Kontext existiert bereits)

Lies `./academic_context.md`, identifiziere Änderungen aus dem Gespräch, aktualisiere nur betroffene Abschnitte. Typische Updates: Gliederung, Fortschritt, neue Konzepte, Forschungsfragen-Schärfung, Methodik-Entscheidung.

### Unterstützung anderer Skills

Braucht ein anderer Skill Kontext: Prüfe ob `./academic_context.md` existiert. Wenn ja — nutze sie. Wenn nein — informiere den User und biete Setup an.

## Few-Shot-Beispiele

### Stil: Forschungsfrage-Fixierung

**Schlecht** (Grund: zu weit, nicht in Bachelor-Zeitrahmen beantwortbar):

> "Wie wirkt sich Künstliche Intelligenz auf die Gesellschaft aus?"

**Gut** (Grund: Scope + Kontext + messbare Dimensionen):

> "Wie verändert der Einsatz generativer KI die Bewertungskriterien für
> textbasierte Prüfungen an der FH Leibniz im Studienjahr 2024/25?"

### Stil: Methodik-Notation

**Schlecht** (Grund: Oberbegriff ohne Operationalisierung):

> Methodik: Qualitative Forschung

**Gut** (Grund: Konkret + zählbar + reproduzierbar):

> Methodik: 12 semi-strukturierte Interviews (je 45 min) mit
> Lehrenden an drei FH-Standorten, Auswertung per Inhaltsanalyse
> nach Mayring.

## Wichtige Regeln

- **Nie ohne vorheriges Lesen überschreiben** — Immer erst den aktuellen Stand lesen, bevor Updates geschrieben werden
- **User-Daten bewahren** — Nie Informationen löschen, deren Entfernen der User nicht explizit verlangt hat
- **Deutsche Feldbezeichnungen** — Die Kontextdateien nutzen deutsche Labels passend zur Sprache des Users
- **Datumsformat** — ISO-Format (YYYY-MM-DD) für Abgabetermine und Zeitstempel
- **Inkrementelle Updates** — Nur geänderte Abschnitte aktualisieren, nicht die ganze Datei
- **Größere Änderungen bestätigen** — Vor einer Umstrukturierung der Gliederung oder dem Ändern der Forschungsfrage Rücksprache mit dem User halten
