---
name: title-generator
description: Use this skill when the user needs a thesis title proposal. Triggers on "Titel vorschlagen", "Titelvorschläge / Titelvorschlaege", "Arbeitstitel", "Thesis title", "thesis title proposal", "Untertitel bitte", or when submission requires a final title. Schlägt Arbeitstitel vor; Für Abstract, Keywords und Zusammenfassung → `abstract-generator`.
license: MIT
---

# Titel-Generator

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Schlägt 5-7 Titelvarianten vor (klassisch-akademisch, fragenbasiert,
kreativ, ergebnisorientiert) mit Rationale und Stärke/Einschränkung.
Basiert auf `./writing_state.md` (fertiger Text) und `./academic_context.md`
(Forschungsfrage). Keine leeren Titel-Hülsen.

## Abgrenzung

Schlägt den finalen Arbeitstitel vor (deskriptiv, These, Frage).
Für Abstract, Keywords, Management Summary → `abstract-generator`.

## Few-Shot-Beispiele (Titelstile)

### Stil: Deskriptiv

**Schlecht** (Grund: zu allgemein, kein Kontext):

> "Eine Untersuchung zu KI in der Lehre"

**Gut** (Grund: Gegenstand + Methode + Kontext):

> "Einsatz generativer KI in FH-Seminaren: Quantitative Analyse von
> Prüfungsleistungen im Studienjahr 2024"

### Stil: These

**Schlecht** (Grund: These ohne Bezug zum Scope):

> "KI ist die Zukunft"

**Gut** (Grund: überprüfbare These + Domäne + Qualifikator):

> "Generative KI verbessert Prüfungsleistungen: Evidenz aus einer
> FH-Stichprobe 2024"

### Stil: Frage

**Schlecht** (Grund: rhetorisch, nicht beantwortet):

> "Sollten Studierende KI nutzen?"

**Gut** (Grund: direkte Forschungsfrage als Titel, empirisch beantwortbar):

> "Wie beeinflusst regelmäßige KI-Nutzung die Prüfungsnoten in BWL- und
> Informatik-Studiengängen? Eine Erhebung an der FH Leibniz 2024"

## Kontext-Dateien

- `./academic_context.md` — Arbeitstyp, Disziplin, Forschungsfrage, Methodik, Sprache
- `./writing_state.md` — abgeschlossene Kapitel, identifizierte Kernargumente

## Analyse-Phase

Analysiere: (1) These/Kernargument, Analyserahmen, Scope, Schlüsselkonzepte; (2) 3-5 stärkste Claims, originellsten Befund, Gegenpositionen; (3) Forschungsansatz, auszeichnende Methoden; (4) domänenspezifische Keywords, häufige Fachbegriffe.

## Titel-Generierung

Genau 5-7 Titelvarianten über diese Kategorien erzeugen:

### Kategorie A: Klassisch-Akademisch (2 Titel)

`[Thema]: [Untertitel mit Scope/Methode]` — formal, deskriptiv, typisch deutsch.

### Kategorie B: Fragenbasiert (1-2 Titel)

Titel als Forschungsfrage — spricht Leser an, spiegelt `./academic_context.md`.

### Kategorie C: Konzeptuell / Kreativ (1-2 Titel)

Kurze Phrase + akademischer Untertitel — Metapher/Paradox, immer mit Untertitel.

### Kategorie D: Ergebnisorientiert (1 Titel)

Kündigt Schlussfolgerung an — passend bei klarem, starkem Befund.

## Output-Format

Jeder Titel mit:

```
## Titelvorschläge

### 1. [Titel] — Kategorie: Klassisch-Akademisch
**Rationale:** [Warum dieser Titel trägt -- was er betont, wie er die Arbeit positioniert]
**Stärke:** [Wichtigster Vorteil]
**Einschränkung:** [Möglicher Nachteil oder Grenze]

### 2. [Titel] — Kategorie: ...
...

---

**Empfehlung:** [Welcher Titel am besten zu Arbeitstyp und Hochschule passt, mit kurzer Begründung]
```

## Qualitätskriterien für Titel

Jeder generierte Titel ist zu prüfen auf:

- **Korrektheit** -- Gibt der Titel den Inhalt der Arbeit korrekt wieder?
- **Spezifität** -- Ist der Scope klar (nicht zu breit, nicht zu eng)?
- **Auffindbarkeit** -- Enthält er Keywords, die die Auffindbarkeit unterstützen?
- **Länge** -- Ziel 8-15 Wörter (inkl. Untertitel); flag bei über 20
- **Konvention** -- Passt er zu typischen Titelmustern für Arbeitstyp und Disziplin?
- **Sprache** -- Sprache der Arbeit einhalten; bei deutschen Arbeiten deutsche Titel (optional eine englische Variante ergänzen)

## Wichtige Regeln

- Den tatsächlichen Arbeitstext vor der Titelgenerierung lesen -- nie nur aus der Gliederung erzeugen, wenn Text da ist
- Die in `./academic_context.md` angegebene Sprache respektieren
- Niemals Clickbait oder sensationalistische Formulierungen vorschlagen
- Titel vermeiden, die die Befunde überhöhen
- Empfehlung mit Begründung an Hochschule und Arbeitstyp binden
- Liegt noch kein Text vor, vorläufige Titel aus Gliederung und Forschungsfrage erzeugen und als vorläufig markieren
