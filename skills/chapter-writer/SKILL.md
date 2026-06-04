---
name: chapter-writer
description: Use this skill when the user wants a chapter SCHREIBEN (Text-Output, kein Review). Triggers on "Kapitel SCHREIBEN", "Einleitung schreiben", "Theorieteil ausformulieren / Theoretischer Rahmen", "Methodik-Kapitel / Methodenteil", "Empirie / Ergebnisse darstellen", "Diskussion schreiben / Diskussionsteil drafted", "Fazit / Schlussteil", "Übergänge formulieren / Uebergaenge formulieren". Für reines Struktur-/Gliederungs-Feedback ohne Neuschrieb → `advisor`. Für Abstract/Keywords → `abstract-generator`. Für Zitations-Formatierung → `citation-extraction`.
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
Diskussion, Fazit). Zieht Zitate via `vault.search()` +
`vault.find_quotes()` und folgt dem Disziplin-Register.

## Abgrenzung

Erzeugt Kapitel-Prosa als **Text-Output** und baut Zitate in die
Argumentation ein.
Struktur-/Gliederungs-Feedback ohne Neuschrieb → `advisor`.
Wörtliche Zitate aus PDF → `citation-extraction`.

## Few-Shot-Beispiele (pro Kapiteltyp)

Schlecht-/Gut-Beispiele pro Kapiteltyp (Theorie, Methoden, Diskussion):
`${CLAUDE_PLUGIN_ROOT}/skills/chapter-writer/references/chapter-examples.md`. Vor dem Draften lesen.

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
verwenden (Schritt 4): nur relevante Quellen, nicht die komplette Liste.

### 2. Ziel-Kapitel bestimmen

Falls unklar, den User fragen, welches Kapitel/welcher Abschnitt zu schreiben
ist. Kläre: Kapitelnummer und -titel, Scope (was das Kapitel leisten soll),
zugeordnete Quellen, erwarteter Umfang (Seitenschätzung aus der Gliederung).

### 3. Approval-Gate nach Outline (Interactive Mode)

Wenn `/search --interactive` aktiv war oder der User explizit eine
Freigabe-Runde wünscht, **Approval-Gate vor dem Draften einbauen**:

1. Outline (Abschnitts-Aufbau aus Schritt 4 unten) dem User vorlegen.
2. Via `AskUserQuestion` Optionen anbieten:
   - **Freigeben** — Outline übernehmen, Draften starten
   - **Abschnitte anpassen** — Gliederung ändern, dann erneut vorlegen
   - **Quellen ergänzen** — `/search` erneut aufrufen
   - **Scope ändern** — Kapitelziel neu definieren
3. Erst nach expliziter Freigabe ("Freigeben") mit dem Draften beginnen.

Bei `--interactive=off` (default) ohne `/search --interactive`-Kontext:
Kapitelplanung direkt starten (kein Gate).

### 4. Kapitelplanung

Bevor geschrieben wird, erstelle einen kurzen internen Plan:

1. **Abschnitts-Aufbau** — Unterabschnitte mit 2-3 Sätzen Inhaltsbeschreibung
2. **Quellen-Mapping via Vault** — pro Unterabschnitt:
   `vault.search("<Kapitelthema>", k=5)` → `[paper_id, snippet]`, dann
   `vault.find_quotes(paper_id, query="<Unterabschnitts-Frage>", k=3)` →
   `[verbatim, page, quote_id]`. Ergebnis: ~1700 Token Quellen-Kontext statt
   vollständigem `literature_state.md`-Dump.
3. **Argumentationsfluss** — wie das Kapitel zur Forschungsfrage beiträgt
4. **Schlüsseldefinitionen** — einzuführende oder referenzierte Begriffe

Plan dem User zur Freigabe vorlegen, bevor gedraftet wird.

### 5. Draften

Schreibe das Kapitel Abschnitt für Abschnitt. Je Abschnitt:

1. Text in der Sprache der Arbeit entwerfen (Default: Deutsch)
2. In-Text-Zitate im konfigurierten Zitationsstil einbauen (Default: APA7)
3. Formales akademisches Register — keine Umgangssprache, keine Ich-Form (außer die Methodik verlangt es)
4. Wo sinnvoll, explizit an die Forschungsfrage anknüpfen
5. Entwurf dem User zur Durchsicht vorlegen

#### Schreibrichtlinien

- **Absatzstruktur** — Topic Sentence, Ausarbeitung, Evidenz, Synthese
- **Zitationsdichte** — In Theoriekapiteln min. ein Zitat pro substanzieller Aussage; weniger in Methodik/Analyse
- **Übergänge** — Jeder Abschnitt endet mit einer Brücke zum nächsten
- **Hedging-Sprache** — Angemessene Abschwächung ("deutet darauf hin", "weist darauf hin", "laut")
- **Keine Füllwörter** — Jeder Satz trägt zur Argumentation bei

#### Quellenintegration

Zitatdaten aus `citation-extraction` nutzen (inline-formatiert nach dem Stil aus
`./academic_context.md`). Integrationsmuster: **Direktzitat** (Wortlaut + Seite),
**Paraphrase** (eigene Worte + Zitat), **Zusammenfassung** (verdichtet + Zitat),
**Synthese** (mehrere Quellen kombiniert).

### 6. User-Review-Zyklus

Nach dem Vorstellen jedes Abschnittsentwurfs:

- Auf User-Feedback warten, bevor weitergeschrieben wird
- Edits, Rewrites oder Freigaben akzeptieren
- Feedback in den nächsten Abschnitt übernehmen
- Nie ohne Bestätigung des Users zum nächsten Abschnitt übergehen

Liefert der User Notizen oder Stichpunkte, bau sie zu akademischer Prosa aus und
bewahre die inhaltliche Absicht.

### 7. Kapitel-Zusammensetzung

Nachdem alle Abschnitte reviewt und freigegeben sind:

1. Abschnitte zum Gesamtkapitel zusammenführen
2. Interne Konsistenz prüfen (Terminologie, Argumentationsfluss)
3. Alle Zitate auf Vollständigkeit und Formatierung prüfen
4. Kapitel-Einleitung (außer Thesis-Einleitung) und -Zusammenfassung ergänzen
5. Finale Wortzahl nennen

### 8. Writing-State aktualisieren

Nach der Freigabe des Kapitels durch den User:

1. `./writing_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Aktuelles Kapitel, Wortzahl und Fortschrittsstatus aktualisieren
3. Kapitel im Fortschrittstracking als "draft complete" markieren

## Spezielle Kapiteltypen

Struktur- und Zitations-Profile pro Kapiteltyp (Einleitung, Theoretischer
Rahmen, Methodik, Analyse/Ergebnisse, Fazit):
`${CLAUDE_PLUGIN_ROOT}/skills/chapter-writer/references/chapter-types.md`. Beim Kapitelplanung-Schritt
das passende Profil anwenden.

## Zitat-Einbindung via Citations-API

Quellen-PDFs im `documents`-Parameter übergeben, damit die API die
Quellenbindung erzwingt; jedes Paraphrase-Segment via `citations[]`
nachweisbar. Vollständiger Workflow und Fallback (kein PDF im Vault):
`${CLAUDE_PLUGIN_ROOT}/skills/chapter-writer/references/citations-api.md`.

## Humanizer-Audit-Pass (nur Hochschul-Kontext)

Vor dem `quality-reviewer`-Aufruf prüfen, ob ein Anti-KI-Audit-Pass nötig ist
(Hochschul-Marker in `academic_context.md`, kein `humanizer_de: off`).
Trigger, Ausführung und Ergebnis-Handling:
`${CLAUDE_PLUGIN_ROOT}/skills/chapter-writer/references/humanizer-audit.md`.

## Qualitaets-Review vor finalem Output

Nach der Generierung des Kapitel-Entwurfs (ggf. nach Humanizer-Audit-Pass)
triggere den `quality-reviewer`-Agent. Vollständige Kriterien-Konfiguration und
PASS-/REVISE-Handling: `${CLAUDE_PLUGIN_ROOT}/skills/chapter-writer/references/quality-review-config.md`.

## Wichtige Regeln

- **Nie ohne User-Review schreiben** — Jeden Abschnitt vor dem Weiterarbeiten vorlegen
- **Nie Zitate fabrizieren** — Nur Quellen aus dem Literaturstatus nutzen
- **User-Voice bewahren** — Bei User-Notizen Formulierung und Intention respektieren
- **Sprache der Arbeit einhalten** — In der im akademischen Kontext angegebenen Sprache schreiben
- **Fortschritt tracken** — Nach freigegebenen Drafts `./writing_state.md` aktualisieren
- **Lücken flaggen** — Fehlt einem Abschnitt eine Quelle, melden und `/search` anbieten
