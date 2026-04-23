# Epic 3 — Prompt-Qualität

**Datum:** 2026-04-23
**Status:** DRAFT — zu finalisieren im E3-Kickoff-Brainstorm nach Abschluss E2
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e3-prompt-quality`
**Ziel-Version:** v5.1.0 (Minor, Verhaltens-Änderungen)
**Abhängigkeit:** E2 gemerged

## Zweck

Inhaltliche Überarbeitung der Prompts in allen 13 Skills, 5 Commands und 3 Agents. Behebt systemische Schwächen aus dem Skill-Review: Sprach-Inkonsistenz, fehlender Fabrikationsschutz, schwammige Bewertungskriterien, fehlende Few-Shot-Beispiele.

## In-Scope

### Block A — Sprach-Vereinheitlichung auf Deutsch

Alle Prompts in Skills, Commands, Agents auf konsistent Deutsch umstellen. Englisch nur in Code, Dateipfaden, JSON-Keys, Code-Kommentaren. Grund: User arbeitet durchgängig auf Deutsch (globales CLAUDE.md), Code-Switches bei Haiku/Sonnet reduzieren Qualität.

Betrifft: alle 13 Skills, 5 Commands, 3 Agents (komplette Datei-Überarbeitung).

### Block B — Anti-Fabrikations-Klauseln mit Begründung

**Cookbook-konform** (nicht ALLCAPS-NEVER): Pro Skill eine Klausel im Stil:

> *"Erfundene Quellen führen dazu, dass die Arbeit unzitierbar wird und bei der Plagiatsprüfung auffliegt. Arbeite ausschließlich mit Daten aus `literature_state.md` oder direkt geladenen PDFs. Wenn Daten fehlen: frag den User, rate nicht."*

Variiert pro Skill mit konkretem Schadensszenario (Plagiatsvorwurf, Zitationsbruch, Methoden-Fehleinschätzung).

Betrifft: alle 13 Skills, besonders `source-quality-audit`, `literature-gap-analysis`, `abstract-generator`, `submission-checker`, `chapter-writer`, `citation-extraction`.

### Block C — Numerische Schwellen statt Floskeln

Referenz: `plagiarism-check` (N-Gram-Schwellen, Severity-Classification) als Goldstandard.

Ziel-Skills:
- `source-quality-audit` — bereits numerisch, prüfen auf Vollständigkeit
- `advisor` — "common academic standards" → konkrete Kriterien-Liste mit PASS/FAIL
- `methodology-advisor` — Scoring-Matrix pro Methode (Datenqualität, Zeitaufwand, Supervisor-Präferenz, Fit)
- `submission-checker` — schon operationalisiert, Regelwerk pro FH verifizieren
- `style-evaluator` — Fallback-Rubrik bei fehlendem Script (Satzlänge, Metrik-Schwellen)
- `literature-gap-analysis` — Coverage/Diversity/Recency numerisch

### Block D — Few-Shot-Paare (Gut/Schlecht)

Betrifft alle bewertenden/generierenden Skills. Pro Template bzw. Entscheidungsknoten je ein Positiv- und Negativ-Beispiel.

Prio:
- `research-question-refiner` (aktuell: Templates ohne Beispiele)
- `abstract-generator` (Gut/Schlecht-Paar pro Strukturelement)
- `title-generator`
- `chapter-writer` (pro Kapiteltyp)

### Block E — Memory-Precondition-Checks

Standard-Skill-Eröffnung:

> *"Bevor du startest: Prüfe, ob `academic_context.md` und `literature_state.md` vorhanden und aktuell sind. Falls nicht → triggere `academic-context`-Skill. Wenn der User das ablehnt → breche den aktuellen Skill ab und erkläre, warum er ohne Kontext nicht läuft."*

Wird an jeden Skill-Anfang (außer `academic-context` selbst) angehängt.

### Block F — Skill-Abgrenzung `literature-gap-analysis` ↔ `source-quality-audit`

Beide prüfen Coverage, Diversity, Recency. Nirgends ist definiert, wann welcher zuständig ist.

**Vorschlag:**
- `source-quality-audit` → Qualität einzelner Quellen (Impact, Methodik, Peer-Review)
- `literature-gap-analysis` → Vollständigkeit des Korpus (fehlende Themen, Autoren, Methoden)

In beiden SKILL.md-Dateien klare Abgrenzungsklausel + Cross-Reference.

### Block G — Umlaute in Trigger-Descriptions

Descriptions enthalten aktuell ASCII-Ersatz ("Quellenqualitaet", "pruefen", "Schlagwoerter"). User tippt mit Umlauten, Skills triggern schlechter.

**Fix:** Beide Varianten in Description aufführen: "Quellenqualität / Quellenqualitaet", "prüfen / pruefen" etc. Alternativ: nur Umlaut-Variante (User hat Umlaute auf seiner Tastatur).

### Block H — 8 spezifische Einzelprobleme aus dem Skill-Review

1. `commands/search.md:69-71` — konkrete browser-use-Anleitung (überschneidet sich mit E2 Block B)
2. `agents/quote-extractor.md:28-33` — robusterer Pre-Execution-Guard (PDF-Wortzahl, Error-Marker)
3. `agents/query-generator.md:114-126` — CS-Disambiguierung: Code-Switch raus, konkrete CS-Term-Liste
4. `skills/methodology-advisor:52-99` — einheitliche Scoring-Tabelle statt asymmetrische Key-References
5. `skills/research-question-refiner:153-163` — Few-Shot-Paare pro Template (überschneidet sich mit Block D)
6. `skills/abstract-generator:140` — Default bei fehlendem Content: "Preliminary, pending validation"
7. `skills/style-evaluator:139-140` — manuelle Fallback-Rubrik explizit
8. `commands/excel.md` — komplett neu (überschneidet sich mit E2 Block C)

## Out-of-Scope

- Native Citations-API → E4
- Evals-Suiten → E4
- Pushy Descriptions + Trigger-Eval-Loop → E4
- Evaluator-Optimizer-Muster → E4
- Domain-Variants per `references/` → E4

## Offene Fragen für E3-Kickoff-Brainstorm

1. Komplett-Rewrite vs. inkrementell: lieber alle Skills am Stück auf Deutsch umstellen, oder Skill für Skill mit Zwischen-Checkpoints?
2. Schadensszenarien für Anti-Fabrikations-Klauseln: aus Praxis/FH-Leibniz-Regeln, oder generisch?
3. Umlaute: beide Varianten oder nur Umlaute?
4. Memory-Precondition: harter Abbruch oder weicher "Proceed with limited context"?

## Git-Plan (grob)

**Branch:** `refactor/e3-prompt-quality` von `main` nach E2-Merge

**Commits (grob gruppiert):**
1. `refactor(skills): unify language to German across all skills`
2. `refactor(commands+agents): unify language to German`
3. `feat(skills): add anti-fabrication clauses with reasoning`
4. `feat(skills): replace vague thresholds with numeric criteria`
5. `feat(skills): add few-shot examples (good/bad pairs)`
6. `feat(skills): add memory precondition checks`
7. `fix(skills): clarify boundary between literature-gap-analysis and source-quality-audit`
8. `fix(skills): add umlaut variants in trigger descriptions`
9. `fix(agents+commands): address 8 specific issues from skill review`
10. `chore(release): v5.1.0`

## Verifikation

- Komplette Spracheinheit (`grep -l "^#\|^-\|^\*" skills/**/SKILL.md` — keine Englisch-Absätze in den Hauptsektionen)
- Jeder Skill hat Anti-Fabrikations-Klausel (`grep -l "erfund\|fabricat" skills/**/SKILL.md` bestätigt Coverage)
- Jeder Skill hat Memory-Precondition-Check
- Review durch Subagent (z. B. `skill-reviewer`) nach Abschluss
