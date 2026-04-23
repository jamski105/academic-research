# Epic 4 — Cookbook-Adoption

**Datum:** 2026-04-23
**Status:** FINAL — im E4-Kickoff-Brainstorm finalisiert
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e4-cookbook`
**Ziel-Version:** v5.2.0 (Minor, neue Features)
**Abhängigkeit:** E3 gemerged (v5.1.0 + v5.1.1 auf `main`)

## Zweck

Adoption der offiziellen Anthropic-Patterns aus `anthropics/anthropic-cookbook` und `anthropics/skills`. Macht das Plugin messbar qualitativ (Evals), halluzinationssicher (Citations-API) und triggerrobust (Pushy Descriptions + Trigger-Eval).

## Entscheidungs-Zusammenfassung

| Frage | Entscheidung |
|-------|--------------|
| Release-Struktur | Gebündelter Minor v5.2.0 für alle 6 Blöcke |
| Citations-Location-Format | `page_location` primär (PDFs), `char_location` Fallback (HTML/MD) |
| Evals-Runner | pytest-basiert in `tests/evals/`, parametrized über `evals/<skill>/*.json` |
| CI-Integration | Lokal-only, manuell vor Release. Kein CI-Trigger (API-Kosten) |
| Pushy-Radikalität | Moderat — imperativ + 3–4 Trigger-Beispiele, kein ALLCAPS |
| Quality-Reviewer-Architektur | Eigener Agent `agents/quality-reviewer.md` (Sonnet-Modell) |
| Domain-References-Scope | Vollständig (10 Dateien): 4 Zitierstile, 2 Sprachen, 4 Submission-Profile |

## In-Scope

### Block A — Native Citations-API

**Cookbook-Quelle:** `anthropic-cookbook/misc/using_citations.ipynb`

Die Claude-API hat ein Citations-Feature, das auf API-Ebene erzwingt, dass Claude nur aus gelieferten Dokumenten zitiert. Halluzinationssicherer als jede Prompt-Klausel.

**Location-Format:**
- **Primär:** `page_location` — Ausgabe enthält Seitenzahlen direkt (`S. 42–43`), zitierfähig ohne Nachbearbeitung. Ziel-Format für alle PDFs.
- **Fallback:** `char_location` — nur für HTML-/Markdown-Quellen ohne Seitenstruktur.

**Betroffene Komponenten:**
- `agents/quote-extractor.md` — Pre-Execution-Guard (Wortzahl-Check, Fehler-Marker, Mindest-Seitenzahl) **entfernt**. API-Citations erzwingen die Quellen-Bindung. Guard-Code ersatzlos raus.
- `skills/citation-extraction/SKILL.md` — Prompt-basierte Zitation umstellen: Claude-Aufruf bekommt `documents[]` mit PDFs als base64-kodierte Anhänge, Output mit `citations[]`-Feld.
- `skills/chapter-writer/SKILL.md` — beim Quellen-Einweben Citations-API nutzen, damit Kapitel-Prosa nachweisbar an Quellen gebunden ist.

**Aufwand:** Medium — API-Schema-Anpassung, base64-Enkodierung der PDFs, Location-Format-Mapping auf Zitations-String-Ausgabe.

### Block B — Evals-Suite pro Skill und Agent

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md` + `references/schemas.md`

Jedes Skill **und jeder Agent** bekommt messbare Qualitäts-Evaluierung mit Baseline-Vergleich. Agents werden genauso evaluiert wie Skills — `quote-extractor` und `relevance-scorer` sind die zwei höchstpriorisierten Kandidaten überhaupt.

**Infrastruktur:**
- **Runner:** pytest-basiert — `tests/evals/test_<component>_evals.py` pro Skill/Agent (Namens-Präfix egal, parametrized-ID identifiziert die Komponente)
- **Datenformat:** `evals/<component>/evals.json` mit Schema:
  ```json
  {
    "prompts": [
      {
        "id": "p1",
        "input": "User-Prompt-Text",
        "expected": {
          "type": "substring" | "regex" | "json_field",
          "value": "erwarteter Substring / Regex-Muster / JSONPath"
        },
        "mode": "with_skill" | "without_skill" | "both"
      }
    ]
  }
  ```
- **Expectation-Typen:**
  - `substring` — String muss als Teilstring im Output vorkommen
  - `regex` — Regex matcht den Output
  - `json_field` — Output ist JSON, Feld an JSONPath existiert und ist nicht-leer
- **Baseline-Vergleich:** Fixture-Parameter `mode=with_skill` vs `mode=without_skill`. **Delta = PASS-Rate(with_skill) − PASS-Rate(without_skill)** in Prozentpunkten.
- **Reports:** `docs/evals/<YYYY-MM-DD>-<component>.md` mit PASS/FAIL pro Prompt + Delta-Tabelle

**Ausführung:**
- Lokal: `pytest tests/evals/ -v`
- **Kein CI-Trigger** (Anthropic-API-Kosten vermeiden)
- Vor jedem Release manuell ausführen, Reports committen

**Priorität (nach Halluzinationsrisiko, absteigend):**
1. `quote-extractor` (Agent)
2. `citation-extraction` (Skill)
3. `abstract-generator` (Skill)
4. `source-quality-audit` (Skill)
5. `chapter-writer` (Skill)
6. Rest: 8 Skills (advisor, style-evaluator, plagiarism-check, research-question-refiner, literature-gap-analysis, methodology-advisor, submission-checker, title-generator, academic-context) + 2 Agents (relevance-scorer, query-generator)

**Verifikations-Schwelle:** Baseline-Gap **≥ 20 Prozentpunkte** Differenz in der PASS-Rate zwischen `with_skill` und `without_skill` (sonst rechtfertigt das Skill/Agent seine Existenz nicht). Beispiel: 95 % PASS mit Skill, 70 % PASS ohne Skill → Delta = 25 pp → PASS.

### Block C — Pushy Descriptions + Trigger-Eval-Loop

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md`

Zitat: *"Claude has a tendency to 'undertrigger' skills […] please make the skill descriptions a little bit 'pushy'"*.

**Pushy-Stil (moderat):**
- Beginn: `Use this skill when …` / `Triggers on …`
- 3–4 konkrete Trigger-Beispiele in Anführungszeichen, inkl. Umlaut-Paare (aus E3 Block G)
- Delegations-Hinweis an Nachbar-Skill (aus E3/E3-Follow-up)
- **Kein** ALL-CAPS-"MUST", kein "ALWAYS" — bleibt deutschsprachig formal

**Trigger-Eval-Set pro Skill:**
- Datei: `evals/<skill>/trigger_evals.json`
- **20 Prompts** pro Skill:
  - 8–10 **should-trigger** — klare Fälle, deutsche Formulierungen, Fachjargon, Paraphrasen
  - 8–10 **should-not-trigger** — Near-Misses, Nachbar-Skills (z. B. für `research-question-refiner`: Prompts, die zu `academic-context` gehören), unspezifische Alltagsfragen
- Schema:
  ```json
  {
    "should_trigger": ["prompt 1", "prompt 2", ...],
    "should_not_trigger": ["prompt 1", "prompt 2", ...]
  }
  ```

**Runner:** `tests/evals/test_triggers.py` — parametrized über alle Skills, prüft Trigger-Entscheidung via Claude-API mit minimalem System-Prompt (nur Skill-Descriptions als Kontext).

**Verifikations-Schwellen:**
- Should-trigger-Recall ≥ 85 % (8/10 oder besser)
- Should-not-trigger-False-Positive ≤ 10 % (1/10 oder besser)

### Block D — Evaluator-Optimizer-Muster via `quality-reviewer`-Agent

**Cookbook-Quelle:** `anthropic-cookbook/patterns/agents/evaluator_optimizer.ipynb`, `orchestrator_workers.ipynb`

**Neuer Agent:** `agents/quality-reviewer.md`

**Spezifikation:**
- **Modell:** `sonnet` (schneller als opus, reicht für Reviewer-Rolle)
- **Input:**
  - `content`: der generierte Text (Kapitel-Prosa, Abstract, Gliederungs-Feedback)
  - `criteria`: Kriterien-Checkliste mit numerischen Schwellen (aus E3 Block C)
  - `context`: relevante Metadaten aus `academic_context.md`
- **Output-Schema:**
  ```
  VERDICT: PASS | REVISE
  BEGRUENDUNG: <konkrete Text-Referenzen mit Zeile/Abschnitt>
  EMPFEHLUNGEN: <priorisierte Fix-Liste, falls REVISE>
  ```
- **Aufruf-Kontext:**
  - `chapter-writer`: vor finalem Kapitel-Output, prüft Satzlänge, Passiv-Quote, Nominalstil, Quellen-Pro-1000-Wörter
  - `abstract-generator`: vor finalem Abstract, prüft IMRaD-Struktur, Wortzahl (150–250), Keyword-Dichte
  - `advisor`: vor finalem Gliederungs-Feedback, prüft 7-Kriterien-Checkliste
- **Loop-Begrenzung:** max 2 Revisions-Iterationen, dann PASS-with-warnings weiterreichen (keine Endlos-Schleife)

**Frontmatter:**
```yaml
---
name: quality-reviewer
description: Evaluator-Optimizer-Agent. <example>...</example>
model: sonnet
tools: [Read]
maxTurns: 3
---
```

### Block E — Domain-Organisation via `references/<variant>.md`

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md` — Abschnitt "Domain organization"

Skills mit mehreren Regelwerken: SKILL.md = Workflow + Variant-Selector, konkrete Regeln in `references/<variant>.md`. Claude lädt nur die relevante Variante ins Context.

**Betroffene Skills (10 Varianten-Dateien gesamt):**

1. `skills/citation-extraction/references/`
   - `apa.md` — APA7 (Default)
   - `harvard.md` — Harvard
   - `chicago.md` — Chicago Author-Date
   - `din1505.md` — DIN 1505-2 (deutsche Norm)

2. `skills/style-evaluator/references/`
   - `academic-de.md` — deutsche akademische Stilregeln
   - `academic-en.md` — englische akademische Stilregeln

3. `skills/submission-checker/references/`
   - `fh-leibniz.md` — FH-Leibniz Formalia (Default, aktuell inline in SKILL.md)
   - `uni-general.md` — generische deutsche Universitäts-Formalia
   - `journal-ieee.md` — IEEE Journal-Einreichungs-Checkliste
   - `journal-acm.md` — ACM Journal-Einreichungs-Checkliste

**SKILL.md-Anpassung:**
- Workflow-Schritt "1. Variant wählen" ergänzen — liest `academic_context.md` (z. B. `Zitationsstil: APA7` → lädt `apa.md`)
- Variant-Selection-Logik als Tabelle im SKILL.md
- Fallback auf Default-Variante, wenn Kontext-Feld leer

### Block F — Prompt-Caching

**Cookbook-Quelle:** `anthropic-cookbook/misc/prompt_caching.ipynb`

`relevance-scorer` verarbeitet Batches von 10+ Papern. System-Prompt + Scoring-Rubrik sind statisch → gecacht.

**Betroffene Komponenten:**
- `agents/relevance-scorer.md` — Cache-Breakpoint auf System-Prompt + 5D-Scoring-Rubrik. Pro Batch nur der Papers-Array variabel.
- `agents/quote-extractor.md` — Cache-Breakpoint auf Extraktions-Instruktionen, wenn Batch-PDFs verarbeitet werden.

**Implementierung:**
- `cache_control: {"type": "ephemeral"}` auf die statischen Content-Blöcke im API-Call
- Dokumentation des Cache-Breakpoints im Agent-Frontmatter als Kommentar (für zukünftige Leser)

**Nicht betroffen:** Keine Python-Skripte mehr (alle API-Aufrufe wurden in v5.0.0 entfernt, nur agents/ machen API-Calls).

**Verifikations-Schwelle:** `cache_read_input_tokens > 0` ab dem 2. Request im Batch, messbare Token-Ersparnis in Evals-Report.

## Out-of-Scope

- **MCP-Server-Umstellung** mit formalem `outputSchema` → aktuell kein MCP-Server exponiert
- **Neue Skills** über die existierenden 13 hinaus
- **UI-Komponenten oder Dashboards** für Eval-Reports (Markdown-Reports reichen)
- **Automatische Trigger-Eval-Orchestrierung** via quality-reviewer — Trigger-Evals laufen nur als pytest, nicht in den Skill-Workflows selbst
- **Externes Eval-Framework** (`inspect-ai`) — pytest reicht

## Git-Plan

**Branch:** `refactor/e4-cookbook` von `main` nach E3-Merge (bereits erfüllt)

**Commits (thematisch gruppiert):**

1. `feat(agents): adopt native Citations API in quote-extractor and chapter-writer`
2. `feat(skills): migrate citation-extraction to Citations API with documents[]`
3. `feat(evals): introduce pytest-based evals suite with baseline comparison`
4. `feat(skills): pushy descriptions and trigger-eval sets (20 prompts per skill)`
5. `feat(agents): introduce quality-reviewer agent (evaluator-optimizer pattern)`
6. `refactor(skills): domain-organized references for citation-extraction, style-evaluator, submission-checker`
7. `perf(agents): prompt caching in relevance-scorer and quote-extractor`
8. `docs(evals): add baseline eval reports for v5.2.0`
9. `chore(release): v5.2.0`

**PR-Strategie:** Ein großer PR gegen `main`, squash-merge, Tag `v5.2.0` setzen und pushen.

## Verifikation

- `pytest tests/evals/` grün, alle Skills/Agents mit messbarem Baseline-Gap ≥ 20 Prozentpunkte
- `pytest tests/evals/test_triggers.py` grün, Recall ≥ 85 %, False-Positive ≤ 10 %
- Citations-API: manuelle Spot-Checks an 5 PDFs aus realen Arbeiten, Seitenzahlen in Output korrekt
- `quality-reviewer` wird in `chapter-writer`, `abstract-generator`, `advisor` vor finalem Output aufgerufen (Code-Review des Workflow-Schritts)
- 10 `references/<variant>.md`-Dateien existieren, Variant-Selector liest `academic_context.md`
- Token-Messung Prompt-Caching: `cache_read_input_tokens` > 0 nach 2. Request im Batch
- Smoke-Test `tests/test_skills_manifest.py` weiter 51/51 grün (keine Regressions)
- CHANGELOG-Block `[5.2.0] — 2026-04-23` mit Added/Changed/Removed-Subsections
- `plugin.json` + `marketplace.json` Version auf `5.2.0`
