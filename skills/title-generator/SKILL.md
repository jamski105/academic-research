---
name: title-generator
description: Use this skill when the user needs a thesis title proposal. Triggers on "Titel vorschlagen", "Titelvorschläge / Titelvorschlaege", "Arbeitstitel", "Thesis title", "thesis title proposal", "Untertitel bitte", or when submission requires a final title. Schlägt Arbeitstitel vor; Für Abstract, Keywords und Zusammenfassung → `abstract-generator`.
license: MIT
---

# Titel-Generator

## Übersicht

Schlägt 5-7 Titelvarianten vor (klassisch-akademisch, fragenbasiert,
kreativ, ergebnisorientiert) mit Rationale und Stärke/Einschränkung.
Basiert auf `./writing_state.md` (fertiger Text) und `./academic_context.md`
(Forschungsfrage). Keine leeren Titel-Hülsen.

## Vorbedingungen

Bevor du startest: Prüfe, ob `./academic_context.md` und `./literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Kernergebnisse kann ich keine Titel-Vorschläge
liefern, weil ich leere Titel-Hülsen ohne Verankerung liefern würde."

## Keine Fabrikation

In den Titel eingebaute Claims ohne Textbeleg machen die Arbeit vor der
Korrektur angreifbar und riskieren Nachfragen im Kolloquium. Arbeite
ausschließlich mit `./writing_state.md` (fertiger Arbeitstext) und
`./academic_context.md` (Forschungsfrage, Kernergebnisse). Fehlen Daten: frag
den User, rate nicht.

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

## Aktivierung dieses Skills

- Der User fragt nach Titelvorschlägen oder möchte seinen Arbeitstitel ändern
- Der User hat einen Entwurf fertig und braucht einen finalen Titel
- Der User sammelt in der Planungsphase Thesis-Titel-Ideen

## Kontext-Dateien

- Lies `./academic_context.md` für Arbeitstyp, Disziplin, Forschungsfrage, Methodik, Sprache und Hochschulanforderungen
- Lies `./writing_state.md` für abgeschlossene Kapitel und während des Schreibens identifizierte Kernargumente

## Analyse-Phase

Vor der Titelgenerierung die Arbeit entlang dieser Dimensionen analysieren:

### 1. Inhaltliche Struktur

- Zentrale These oder Kernargument identifizieren
- Haupttheorie oder Analyserahmen extrahieren
- Scope notieren (Einzelfall, Vergleich, branchenweit)
- Abhängige und unabhängige Variablen bzw. Schlüsselkonzepte bestimmen

### 2. Kernaussagen

- Die 3-5 stärksten Claims der Arbeit extrahieren
- Den originellsten Beitrag oder Befund identifizieren
- Unerwartete Ergebnisse oder Gegenpositionen notieren

### 3. Methodik-Signatur

- Forschungsansatz identifizieren (qualitativ, quantitativ, Mixed, Literaturreview)
- Methoden notieren, die die Arbeit auszeichnen (z. B. Delphi, SLR, Grounded Theory)
- Prüfen, ob die Methodik selbst titelwürdig ist

### 4. Keywords und Terminologie

- Domänenspezifische Keywords aus der Arbeit extrahieren
- Häufigste Fachbegriffe identifizieren
- Selbst geprägte Begriffe oder Framework-Namen notieren

## Titel-Generierung

Genau 5-7 Titelvarianten über diese Kategorien erzeugen:

### Kategorie A: Klassisch-Akademisch (2 Titel)

Struktur: `[Thema]: [Untertitel mit Scope/Methode]`

Eigenschaften:
- Formal, deskriptiv, eindeutig
- Enthält Kernthema und Methodik oder Scope
- Typisch für deutsche Abschlussarbeiten
- Beispielmuster: "Digitale Transformation im Mittelstand: Eine qualitative Analyse der Erfolgsfaktoren"

### Kategorie B: Fragenbasiert (1-2 Titel)

Struktur: Titel als Forschungsfrage oder provokante Frage.

Eigenschaften:
- Spricht den Leser direkt an
- Spiegelt die Forschungsfrage aus `./academic_context.md`
- Passend für explorative oder argumentative Arbeiten

### Kategorie C: Konzeptuell / Kreativ (1-2 Titel)

Struktur: Kurze, einprägsame Phrase mit akademischem Untertitel.

Eigenschaften:
- Nutzt Metapher, Paradox oder prägnante Formulierung
- Immer mit klärendem Untertitel
- Häufiger in Sozial- und Geisteswissenschaften
- Muss professionell bleiben

### Kategorie D: Ergebnisorientiert (1 Titel)

Struktur: Titel, der das zentrale Ergebnis andeutet oder benennt.

Eigenschaften:
- Kündigt die Schlussfolgerung an
- Passend, wenn der Befund klar und stark ist
- In deutscher Tradition weniger üblich, aber zunehmend akzeptiert

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
