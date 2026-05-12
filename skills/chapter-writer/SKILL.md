---
name: chapter-writer
description: Use this skill when the user writes a chapter of an academic work. Triggers on "Einleitung schreiben", "Theorieteil / Theoretischer Rahmen", "Methodik-Kapitel / Methodenteil", "Empirie / Ergebnisse darstellen", "Diskussion schreiben", "Fazit / Schlussteil", "Übergänge formulieren / Uebergaenge formulieren", or when a chapter body with proper citations is needed. Schreibt vollständige Kapitelentwürfe; Für Abstract/Keywords → `abstract-generator`; für Zitations-Formatierung → `citation-extraction`.
compatibility: Claude API mit documents[] und citations.enabled
license: MIT
---

# Kapitel-Autor

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Schreibt konkrete Kapitel (Einleitung, Theorieteil, Methodik, Empirie,
Diskussion, Fazit) für akademische Arbeiten. Zieht Zitate via
`vault.search()` + `vault.find_quotes()` und folgt dem Disziplin-Register.

## Abgrenzung

Schreibt Kapitel-Prosa und baut Zitate in die Argumentation ein.
Für reines Extrahieren wörtlicher Zitate aus einem PDF → `citation-extraction`.

## Few-Shot-Beispiele (pro Kapiteltyp)

### Kapitel: Theorie

**Schlecht** (Grund: Definitionen aneinandergereiht, keine Struktur-Argumentation):

> "Führung ist wichtig. Transformationale Führung ist eine Führungsart.
> Sie wurde von Bass beschrieben."

**Gut** (Grund: Definition + Einordnung + Abgrenzung, mit Beleg):

> "Transformationale Führung bezeichnet ein Führungskonzept, bei dem
> Vorgesetzte Mitarbeiter durch Vision und individuelle Förderung über
> transaktionale Anreize hinaus motivieren (Bass 1985, S. 22). Abgrenzung
> zur transaktionalen Führung: Transaktional beruht auf Leistungs-
> Gegenleistungs-Tausch, transformational auf intrinsischer Motivation
> (Bass & Riggio 2006)."

### Kapitel: Methoden

**Schlecht** (Grund: keine Begründung, keine Operationalisierung):

> "Wir haben eine Umfrage gemacht."

**Gut** (Grund: Wahl + Begründung + Operationalisierung + Grenzen):

> "Gewählt wurde ein standardisierter Online-Fragebogen, weil nur so die
> angestrebte Stichprobengröße n ≥ 100 im Zeitrahmen erreichbar war.
> Führungsstil wurde mittels MLQ-5X operationalisiert (Avolio & Bass
> 2004). Limitation: Selbstauskunft der Mitarbeiter zur Führungs-
> Wahrnehmung, keine Beobachtungsdaten."

### Kapitel: Diskussion

**Schlecht** (Grund: Ergebnis-Wiederholung ohne Einordnung):

> "Die Umfrage hat gezeigt, dass transformationale Führung besser wirkt.
> Das passt zu den Erwartungen."

**Gut** (Grund: Befund + Literatur-Kontext + Abweichungs-Erklärung):

> "Der gefundene positive Effekt transformationaler Führung auf
> Mitarbeiterzufriedenheit (β=0,38, p<0,01) deckt sich mit der Meta-
> Analyse von Judge & Piccolo (2004), fällt aber schwächer aus als dort
> berichtet (β=0,59). Mögliche Erklärung: Branchenspezifika in
> Metallverarbeitung (hohe Arbeitsteilung) dämpfen Führungseffekte —
> konsistent mit Liao & Chuang (2007)."

## Kontext-Dateien

- Lesen: `./academic_context.md` (Forschungsfrage, Gliederung, Zitationsstil),
  `./writing_state.md` (Fortschritt)
- Vault-Queries: `vault.search(query, k=5)` für relevante Paper,
  `vault.find_quotes(paper_id, query, k=3)` für Zitat-Kandidaten
- Schreiben: `./writing_state.md` — Wortzahlen und Kapitelstatus aktualisieren
- `./literature_state.md` nicht laden (ist read-only Snapshot — bei Bedarf
  via `node scripts/export-literature-state.mjs` regenerieren)

## Core-Workflow

### 1. Kontext laden

Lies `./academic_context.md` und `./writing_state.md`.
Fehlt `./academic_context.md`: `academic-context`-Skill triggern.
Fehlt Gliederung: `advisor`-Skill vorschlagen.

Quellen nicht aus `literature_state.md` laden — stattdessen Vault-Queries
verwenden (Schritt 3 unten). So werden nur relevante Quellen geladen,
nicht die komplette Literaturliste.

### 2. Ziel-Kapitel bestimmen

Frage den User, welches Kapitel oder welcher Abschnitt geschrieben werden soll, falls nicht klar. Kläre:

- Kapitelnummer und -titel aus der Gliederung
- Scope — Was soll das Kapitel leisten?
- Verfügbare zugeordnete Quellen
- Erwarteter Umfang (Seitenschätzung aus der Gliederung)

### 3. Kapitelplanung

Bevor geschrieben wird, erstelle einen kurzen internen Plan:

1. **Abschnitts-Aufbau** — Unterabschnitte mit 2-3 Sätzen Inhaltsbeschreibung
2. **Quellen-Mapping via Vault** — Vault-Queries pro Unterabschnitt:
   ```
   vault.search("<Kapitelthema>", k=5)
   → [paper_id, snippet] für relevante Paper

   vault.find_quotes(paper_id, query="<Unterabschnitts-Frage>", k=3)
   → [verbatim, page, quote_id] für Zitat-Kandidaten
   ```
   Ergebnis: maximal ~1700 Token Quellen-Kontext statt vollständigem
   `literature_state.md`-Dump (~8–15 k Token).
3. **Argumentationsfluss** — Wie das Kapitel seinen Beitrag zur Forschungsfrage aufbaut
4. **Schlüsseldefinitionen** — Begriffe, die eingeführt oder referenziert werden müssen

Plan dem User zur Freigabe vorlegen, bevor gedraftet wird.

### 4. Draften

Schreibe das Kapitel Abschnitt für Abschnitt. Für jeden Abschnitt:

1. Text in der Sprache der Arbeit entwerfen (Default: Deutsch)
2. In-Text-Zitate im konfigurierten Zitationsstil einbauen (Default: APA7)
3. Formales akademisches Register nutzen — keine Umgangssprache, keine Ich-Form, außer die Methodik verlangt es
4. Wo sinnvoll, explizit an die Forschungsfrage anknüpfen
5. Entwurf dem User zur Durchsicht vorlegen

#### Schreibrichtlinien

- **Absatzstruktur** — Topic Sentence, Ausarbeitung, Evidenz, Synthese
- **Zitationsdichte** — In Theoriekapiteln mindestens ein Zitat pro substanzieller Aussage; weniger in Methodik/Analyse
- **Übergänge** — Jeder Abschnitt endet mit einer Brücke zum nächsten
- **Hedging-Sprache** — Angemessene Abschwächung bei Aussagen ("deutet darauf hin", "weist darauf hin", "laut")
- **Keine Füllwörter** — Jeder Satz muss zur Argumentation beitragen

#### Quellenintegration

Beim Zitieren die Daten aus dem `citation-extraction`-Skill nutzen (inline-formatiert nach dem in `./academic_context.md` konfigurierten Stil). Paper über das formatierte Zitat referenzieren. Folgende Integrationsmuster werden unterstützt:

- **Direktzitat** — Exakter Wortlaut in Anführungszeichen mit Seitenzahl
- **Paraphrase** — In eigenen Worten wiedergeben, mit Zitat
- **Zusammenfassung** — Argumentation einer Quelle verdichten, mit Zitat
- **Synthese** — Mehrere Quellen kombinieren, um einen Punkt zu stützen

### 5. User-Review-Zyklus

Nach dem Vorstellen jedes Abschnittsentwurfs:

- Auf User-Feedback warten, bevor weitergeschrieben wird
- Edits, Rewrites oder Freigaben akzeptieren
- Feedback in den nächsten Abschnitt übernehmen
- Nie ohne Bestätigung des Users zum nächsten Abschnitt übergehen

Liefert der User eigene Notizen oder Stichpunkte, bau sie zu akademischer Prosa aus und bewahre die inhaltliche Absicht.

### 6. Kapitel-Zusammensetzung

Nachdem alle Abschnitte reviewt und freigegeben sind:

1. Abschnitte zum Gesamtkapitel zusammenführen
2. Interne Konsistenz prüfen (Terminologie, Argumentationsfluss)
3. Alle Zitate auf Vollständigkeit und Formatierung prüfen
4. Kapitel-Einleitung (außer bei Thesis-Einleitung) und Kapitel-Zusammenfassung ergänzen
5. Finale Wortzahl berichten

### 7. Writing-State aktualisieren

Nach der Freigabe des Kapitels durch den User:

1. `./writing_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Aktuelles Kapitel, Wortzahl und Fortschrittsstatus aktualisieren
3. Kapitel im Fortschrittstracking als "draft complete" markieren

## Spezielle Kapiteltypen

### Einleitung

Struktur: Themenrelevanz, Problemstellung, Forschungsfrage, Methodik-Überblick, Gliederungs-Vorschau. Zuletzt schreiben oder nach Fertigstellung der anderen Kapitel überarbeiten.

### Theoretischer Rahmen

Hohe Zitationsdichte. Alle Schlüsselkonzepte definieren. Perspektiven verschiedener Autoren vergleichen. Auf den später verwendeten Analyserahmen hinarbeiten.

### Methodik

Den gewählten Ansatz begründen. Datenerhebung und -analyse beschreiben. Limitationen adressieren. Methodik-Literatur referenzieren.

### Analyse / Ergebnisse

Den theoretischen Rahmen auf die Daten anwenden. Befunde entlang der Unterfragen oder Themen strukturieren. Evidenz aus Primär- oder Sekundärquellen nutzen.

### Fazit

Befunde pro Unterfrage zusammenfassen. Die Hauptfrage beantworten. Limitationen und zukünftige Forschung diskutieren. Keine neuen Quellen.

## Zitat-Einbindung via Citations-API

Beim Einweben von Zitaten in Kapitel-Prosa: Quellen-PDFs im `documents`-Parameter an Claude uebergeben, damit die API die Quellenbindung erzwingt. Jedes Paraphrase-Segment mit einem `citations[]`-Eintrag nachweisbar.

**Workflow:**
1. `vault.search("<Kapitelthema>", k=5)` → relevante `paper_id`s
2. Pro paper_id: `vault.find_quotes(paper_id, query, k=3)` → Zitat-Kandidaten
3. Pro Paper: `vault.ensure_file(paper_id)` → `file_id` für Citations-API
4. API-Call mit `documents[]` (file_id), `citations.enabled: true`
5. Output-Text enthält `citations[]`-Blöcke — als Inline-Zitate nach
   Variant-Zitierstil aus `./academic_context.md` rendern.

**Fallback:** Gibt `vault.ensure_file()` `None` zurück (kein PDF im Vault),
nutze den Vault-Zitat-Text (`verbatim`) direkt als Prompt-basiertes Zitat
ohne Citations-API-Erzwingung.

## Qualitaets-Review vor finalem Output

Nach der Generierung des Kapitel-Entwurfs triggere den `quality-reviewer`-Agent:

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Entwurfs-Text>",
    "criteria": [
      {"name": "Satzlaenge Median", "threshold": "15-25 Woerter", "metric": "median"},
      {"name": "Passiv-Quote", "threshold": "< 30%", "metric": "percentage"},
      {"name": "Nominalstil", "threshold": "< 40%", "metric": "percentage"},
      {"name": "Quellen pro 1000 Woerter", "threshold": ">= 5", "metric": "count_per_1000"}
    ],
    "context": {"component": "chapter-writer", "iteration": <N>}
  }
)
```

**Bei PASS:** Output an User liefern.
**Bei REVISE:** Empfehlungen anwenden, erneut generieren, iteration += 1.
**Bei iteration >= 2:** PASS-with-warnings akzeptieren und die verbleibenden Warnungen dem User transparent machen.

## Wichtige Regeln

- **Nie ohne User-Review schreiben** — Jeden Abschnitt zur Durchsicht vorlegen, bevor weitergearbeitet wird
- **Nie Zitate fabrizieren** — Nur Quellen nutzen, die im Literaturstatus existieren
- **User-Voice bewahren** — Wenn der User Notizen liefert, Formulierung und Intention respektieren
- **Sprache der Arbeit einhalten** — In der Sprache schreiben, die im akademischen Kontext angegeben ist
- **Fortschritt tracken** — Nach freigegebenen Drafts immer `./writing_state.md` aktualisieren
- **Lücken flaggen** — Fehlt für einen Abschnitt eine Quelle, das melden und `/search` anbieten
