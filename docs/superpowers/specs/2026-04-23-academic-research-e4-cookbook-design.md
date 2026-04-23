# Epic 4 — Cookbook-Adoption

**Datum:** 2026-04-23
**Status:** DRAFT — zu finalisieren im E4-Kickoff-Brainstorm nach Abschluss E3
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e4-cookbook`
**Ziel-Version:** v5.2.0 (Minor, neue Features)
**Abhängigkeit:** E3 gemerged

## Zweck

Adoption der offiziellen Anthropic-Patterns aus `anthropics/anthropic-cookbook` und `anthropics/skills`. Macht das Plugin messbar qualitativ (Evals), halluzinationssicher (Citations-API) und triggerrobust (Pushy Descriptions + Trigger-Eval).

## In-Scope

### Block A — Native Citations-API

**Cookbook-Quelle:** `anthropic-cookbook/misc/using_citations.ipynb`

Die Claude-API hat ein Citations-Feature, das auf API-Ebene erzwingt, dass Claude nur aus gelieferten Dokumenten zitiert. Halluzinationssicherer als jede Prompt-Klausel.

**Betroffene Komponenten:**
- `agents/quote-extractor.md` — Pre-Execution-Guard raus, Citations-API rein
- `skills/citation-extraction` — Prompt-basierte Zitation umstellen
- `skills/chapter-writer` — beim Quellen-Einweben Citations-API nutzen

**Aufwand:** Medium — erfordert API-Schema-Anpassung (`documents`-Parameter, Location-Format wählen: char/page/content-block).

### Block B — Evals-Suite pro Skill

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md` + `references/schemas.md`

Jedes Skill bekommt `evals/evals.json` mit:
- Test-Prompts
- Verifizierbare `expectations`
- Baseline-Vergleich: with_skill vs. without_skill

**Priorität (nach Halluzinationsrisiko):**
1. `quote-extractor`
2. `citation-extraction`
3. `abstract-generator`
4. `source-quality-audit`
5. `chapter-writer`
6. Rest

**Infrastruktur:**
- Test-Runner (Python-Script oder node-basiert)
- CI-Integration? Oder manuell vor Release?
- Eval-Reports in `docs/evals/`

### Block C — Pushy Descriptions + Trigger-Eval-Loop

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md`

Zitat: *"Claude has a tendency to 'undertrigger' skills […] please make the skill descriptions a little bit 'pushy'"*.

**Vorgehen:**
1. Alle 13 Skill-Descriptions "pushy" umformulieren
2. Pro Skill ein Trigger-Eval-Set mit **20 Prompts**:
   - 8-10 should-trigger (klare Fälle, deutsche Formulierungen, Fachjargon)
   - 8-10 should-not-trigger (Near-Misses, Nachbar-Skills, unspezifische Alltagsfragen)
3. Trigger-Eval als Teil der Evals-Suite aus Block B

### Block D — Evaluator-Optimizer-Muster

**Cookbook-Quelle:** `anthropic-cookbook/patterns/agents/evaluator_optimizer.ipynb`, `orchestrator_workers.ipynb`

Iterative Skills (chapter-writer, advisor) bekommen eine Generator/Evaluator-Trennung.

**Neuer Agent:** `quality-reviewer`
- Input: generierter Inhalt + Kriterien-Checkliste (numerische Schwellen aus E3 Block C)
- Output: PASS/REVISE mit konkreter Begründung
- Wird von `chapter-writer`, `abstract-generator`, `advisor` vor finalem Output aufgerufen

### Block E — Domain-Organisation via `references/<variant>.md`

**Cookbook-Quelle:** `anthropics/skills/skills/skill-creator/SKILL.md` — Abschnitt "Domain organization"

Skills mit mehreren Zielgruppen/Regelwerken bekommen SKILL.md als Workflow + Variant-Auswahl, pro Variante eine `references/<variant>.md`.

**Betroffene Skills:**
- `citation-extraction` → `references/{apa,harvard,chicago,din1505}.md`
- `style-evaluator` → `references/{academic-de,academic-en}.md`
- `submission-checker` → `references/{fh-leibniz,uni-general,journal-ieee,journal-acm}.md`

### Block F — Prompt-Caching

**Cookbook-Quelle:** `anthropic-cookbook/misc/prompt_caching.ipynb`

`relevance-scorer` verarbeitet Batches von 10+ Papern. System-Prompt + Scoring-Rubrik sind statisch → gecacht. Spart massiv Tokens/Latenz.

**Betroffene Komponenten:**
- `agents/relevance-scorer.md` — Cache-Breakpoints definieren
- Evtl. `agents/quote-extractor.md` für Batch-PDFs
- `scripts/search.py` (falls weiterhin benutzt) — API-Calls mit cache_control

## Out-of-Scope

- MCP-Server-Umstellung mit formalem `outputSchema` → nicht relevant, weil aktuell kein MCP-Server exponiert wird
- Neue Skills über die existierenden 13 hinaus
- UI-Komponenten oder Dashboards

## Offene Fragen für E4-Kickoff-Brainstorm

1. Citations-API: char-Level oder page-Level Locations (User-Erwartung bei akademischen Quellen)?
2. Evals-Runner: Python-eigen oder existierendes Framework (`pytest`, `inspect-ai`)?
3. CI-Integration: GitHub Actions oder manuell?
4. Pushy Descriptions: radikal oder moderat? Balance zwischen Undertriggering und Overtriggering.
5. `quality-reviewer`-Agent: eigener Agent oder in `chapter-writer` eingebettet als Inline-Schritt?
6. Welche Submission-Varianten wirklich relevant (FH-Leibniz ist fix, welche anderen)?

## Git-Plan (grob)

**Branch:** `refactor/e4-cookbook` von `main` nach E3-Merge

**Commits (grob gruppiert):**
1. `feat(agents): adopt native Citations API in quote-extractor and chapter-writer`
2. `feat(skills): migrate citation-extraction to Citations API`
3. `feat(evals): introduce evals suite with baseline comparison`
4. `feat(skills): pushy descriptions and trigger-eval sets`
5. `feat(agents): introduce quality-reviewer and evaluator-optimizer pattern`
6. `refactor(skills): domain-organized references for citation-extraction and submission-checker`
7. `perf: prompt caching in relevance-scorer`
8. `docs: evals reports`
9. `chore(release): v5.2.0`

## Verifikation

- Alle Evals-Suites laufen grün, Baseline-Gap dokumentiert
- Trigger-Eval zeigt messbares Undertriggering-Reduction
- Citations-API liefert location-genaue Zitate (manuelle Spot-Checks)
- `quality-reviewer` wird vor Output aufgerufen (Code-Review)
- Token-Ersparnis durch Caching messbar (vor/nach)
