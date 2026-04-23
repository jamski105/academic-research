# Academic-Research Plugin — Refactor-Overview (v4 → v5)

**Datum:** 2026-04-23
**Status:** Design approved, Implementation pro Epic
**Autor:** jam@ahler.org, assistiert durch Claude Code

## Ausgangslage

Das academic-research-Plugin (v4.0.0) ist strukturell solide, hat aber nach Reviews durch `plugin-validator`, `skill-reviewer` und Cookbook-Abgleich 25+ diskrete Findings über vier Themenbereiche. Ein einzelner Implementation-Plan wäre zu groß und zu riskant. Dieses Dokument dokumentiert die Decomposition und gibt den Rahmen für die vier Sub-Projekte vor.

## Entscheidungen (nach Brainstorming)

- **Scope-Struktur:** Vier Epics nacheinander, jedes mit eigenem Spec → Plan → Implementation → PR-Zyklus.
- **Constraints:** Keine. Breaking Changes zulässig, keine Deadline, keine Abhängigkeits-Sperre.
- **Git-Strategie:** Feature-Branch pro Epic (`refactor/e1-*`, `refactor/e2-*`, ...), ein PR pro Epic gegen `main`. Version-Bump nach jedem Merge.
- **Template-Architektur:** Skill-lokal. Templates bleiben im jeweiligen Skill-Ordner, keine zentrale `templates/`-Hierarchie.

## Epic-Übersicht

### E1 — Kritische Fixes (v4.0.1)

**Branch:** `refactor/e1-critical-fixes`
**Umfang:** ~½ Tag
**Risiko:** niedrig
**Abhängigkeit:** keine

Fixt ausschließlich Laufzeit-Bugs, eine Security-Lücke und offensichtliche Fehlkonfigurationen. Keine Content-Änderungen, keine Breaking Changes.

- Pfad-Bugs in `advisor`, `methodology-advisor`, `submission-checker`
- `commands/search.md`: offene Agent-Permissions einschränken
- Agent-Frontmatter: `tools` als Array, `<example>`-Blöcke in Description
- `maxTurns` reduzieren: `quote-extractor` 20→5, `relevance-scorer` 15→3

Detail-Spec: [2026-04-23-academic-research-e1-critical-fixes-design.md](2026-04-23-academic-research-e1-critical-fixes-design.md)

### E2 — Architektur-Bereinigung (v4.1.0 → v5.0.0)

**Branch:** `refactor/e2-architecture`
**Umfang:** 2-3 Tage
**Risiko:** mittel (Regressionspotential in Suche und Export)
**Abhängigkeit:** E1

Strukturelle Bereinigung der Datei-Landschaft. Breaking Changes an Commands und MCP-Setup.

- Redundante Python-Skripte löschen:
  - `scripts/citations.py` (ersetzt durch Skill `citation-extraction` + Agent `quote-extractor`)
  - `scripts/style_analysis.py` (ersetzt durch Skill `style-evaluator`)
  - `scripts/ranking.py` (ersetzt durch Agent `relevance-scorer` + Skill `source-quality-audit`)
  - `scripts/excel.py` (ersetzt durch `document-skills:xlsx`)
  - Prüfen: `scripts/pdf.py` (ggf. ersetzbar durch `quote-extractor`-Agent)
- Playwright-MCP → `browser-use`-Skill migrieren (12 Stellen: `.mcp.json`, `configure_permissions.py`, `setup.sh`, `README.md`, `commands/setup.md`, `commands/search.md`, `settings.json`, `config/browser_guides/*.md`, `.gitignore`)
- `document-skills:xlsx`-Integration: `commands/excel.md` umbauen, README-Voraussetzung, SessionStart-Hook-Check
- Betroffene Skills anpassen, die auf gelöschte Skripte verwiesen haben

Wird in eigenem Brainstorm-Zyklus detailliert.

### E3 — Prompt-Qualität (v5.1.0)

**Branch:** `refactor/e3-prompt-quality`
**Umfang:** 3-5 Tage
**Risiko:** mittel (Verhalten ändert sich spürbar)
**Abhängigkeit:** E2

Inhaltliche Überarbeitung aller Prompts in Skills, Commands, Agents.

- Sprach-Vereinheitlichung: alles Deutsch, Englisch nur in Code/Pfaden/JSON-Keys
- Anti-Fabrikations-Klauseln mit Begründung (Cookbook-konform: kein blankes ALLCAPS-NEVER, sondern Begründung + Handlungsanweisung)
- Numerische Schwellen statt Floskeln (Plagiarism-Check als Goldstandard)
- Few-Shot-Paare (Gut/Schlecht) in allen bewertenden Skills
- Memory-Precondition-Checks als Standard-Skill-Eröffnung
- Umlaute in Trigger-Descriptions (ä/ö/ü statt ae/oe/ue, zusätzlich zur ASCII-Variante)
- Skill-Abgrenzung zwischen `literature-gap-analysis` und `source-quality-audit` explizit machen
- Die 8 spezifischen Einzelprobleme aus dem Skill-Review

Wird in eigenem Brainstorm-Zyklus detailliert.

### E4 — Cookbook-Adoption (v5.2.0)

**Branch:** `refactor/e4-cookbook`
**Umfang:** 3-5 Tage
**Risiko:** hoch (API-Änderungen, Test-Infrastruktur)
**Abhängigkeit:** E3

Adoption der offiziellen Anthropic-Patterns.

- Native Citations-API im `quote-extractor` und `citation-extraction` (ersetzt heuristische Pre-Execution-Guards)
- Evals-Suite pro Skill (`evals/evals.json` mit `expectations`, Baseline with_skill vs. without_skill)
- Pushy Descriptions + Trigger-Eval-Loop (20 Prompts je Skill: 8-10 should-trigger, 8-10 should-not-trigger inkl. Near-Misses)
- Evaluator-Optimizer-Muster: neuer Agent `quality-reviewer`, Generator/Evaluator-Trennung in iterativen Skills
- Domain-Organisation via `references/<variant>.md` für `citation-extraction` (APA, Harvard, Chicago, DIN 1505) und `style-evaluator`
- Prompt-Caching im `relevance-scorer` für Batch-Runs

Wird in eigenem Brainstorm-Zyklus detailliert.

## Arbeitsweise-Regeln für alle Epics

1. **Ein Feature-Branch pro Epic.** Kein Cross-Epic-Commit.
2. **Nach jedem Epic:** Version-Bump in `.claude-plugin/plugin.json` und `.claude-plugin/marketplace.json`, Eintrag im CHANGELOG.
3. **Vor jedem Merge:** Statische Verifikation (YAML-Parse, Path-Checks, JSON-Validity). Ab E4 zusätzlich Evals-Suite.
4. **Rollback:** Atomare Commits, so dass `git revert` pro Fix möglich bleibt.
5. **Out-of-Scope strikt respektieren:** Findings, die thematisch zu einem späteren Epic gehören, nicht vorziehen.

## Versionierung

| Epic | Ziel-Version | Änderungstyp |
|------|--------------|--------------|
| E1 | v4.0.1 | Patch (reine Bugfixes) |
| E2 | v5.0.0 | Major (Breaking: Skripte weg, Playwright weg) |
| E3 | v5.1.0 | Minor (Verhalten ändert sich, aber API stabil) |
| E4 | v5.2.0 | Minor (neue Features, Citations-API, Evals) |

## Was dieses Dokument NICHT leistet

- Keine Detail-Spezifikation einzelner Fixes — das leisten die Epic-Specs.
- Kein Implementation-Plan — den erzeugt pro Epic das `writing-plans`-Skill.
- Keine Zeitschätzung mit Deadlines — Aufwände sind grobe Orientierung.
