# Epic 1 — Kritische Fixes

**Datum:** 2026-04-23
**Status:** Design approved
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e1-critical-fixes`
**Ziel-Version:** v4.0.1 (Patch)

## Zweck

E1 fixt alles, was entweder zur Laufzeit bricht, ein Security-Problem darstellt, oder offensichtliche Fehlkonfiguration ist. Keine Content-Änderungen, keine Breaking Changes, keine neuen Features. Diese Fixes müssen vor jedem weiteren Epic gelandet sein, damit spätere Test- und Refactor-Arbeit auf einem stabilen Fundament läuft.

## In-Scope

1. **Pfad-Bugs in drei Skills** (verweisen auf `${CLAUDE_PLUGIN_ROOT}/templates/...`, Dateien liegen aber skill-lokal)
2. **Security-Fix** in `commands/search.md` (offene Agent-Permissions)
3. **Agent-Frontmatter** normalisieren (`tools`-Feld, `<example>`-Blöcke)
4. **`maxTurns` reduzieren** in zwei Agents (Kostenreduktion)

## Out-of-Scope

Explizit NICHT in E1:
- Python-Skripte löschen → E2
- Playwright → browser-use → E2
- `document-skills:xlsx`-Integration → E2
- Sprach-Vereinheitlichung, Anti-Fabrikations-Klauseln, numerische Schwellen → E3
- Citations-API, Evals-Suiten, Pushy Descriptions, Evaluator-Pattern → E4

## Detail pro Fix

### Fix 1 — Pfad-Bug `skills/advisor/SKILL.md:78`

**Aktuell:** Skill referenziert `${CLAUDE_PLUGIN_ROOT}/templates/expose-template.md`. Datei liegt aber unter `skills/advisor/expose-template.md`.

**Änderung:** Pfad in der SKILL.md auf `${CLAUDE_PLUGIN_ROOT}/skills/advisor/expose-template.md` umstellen. Datei bleibt skill-lokal (Entscheidung aus Brainstorming).

**Verifikation:**
- `ls /Users/j65674/Repos/academic-research/skills/advisor/expose-template.md` existiert
- `grep "expose-template" skills/advisor/SKILL.md` zeigt den neuen Pfad

### Fix 2 — Pfad-Bug `skills/methodology-advisor/SKILL.md:29`

**Aktuell:** Referenziert `${CLAUDE_PLUGIN_ROOT}/templates/methodology-catalog.md`. Datei liegt unter `skills/methodology-advisor/methodology-catalog.md`.

**Änderung:** Pfad auf `${CLAUDE_PLUGIN_ROOT}/skills/methodology-advisor/methodology-catalog.md` umstellen.

**Verifikation:** analog Fix 1.

### Fix 3 — Pfad-Bug `skills/submission-checker/SKILL.md:21`

**Aktuell:** Zeile 21 verweist laut Reviewer-Auditing auf `${CLAUDE_PLUGIN_ROOT}/templates/leibniz-fh-requirements.md`. Datei liegt vermutlich unter `skills/submission-checker/leibniz-fh-requirements.md`.

**Änderung:** Erst prüfen: existiert die Datei tatsächlich skill-lokal? Falls ja → Pfad in SKILL.md auf `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` umstellen. Falls die Datei nicht existiert → als separater Findings notieren und nicht in E1 lösen (E3-Kandidat).

**Verifikation:** analog Fix 1.

### Fix 4 — Security `commands/search.md:4`

**Aktuell:**
```yaml
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Agent
```

Das `Agent` ohne Argument erlaubt jedes Subagent-Invokat.

**Änderung:** `Agent(query-generator, relevance-scorer, quote-extractor)` — nur die drei Agents, die der Command tatsächlich aufruft.

**Verifikation:**
- `grep "allowed-tools" commands/search.md` zeigt die drei Agent-Namen
- Command-Ablauf mental durchgespielt: keine anderen Agents werden gebraucht

### Fix 5 — Agent `query-generator.md`: Frontmatter + Description

**Aktuell:** `tools: ""` (leerer String, mehrdeutig). Description ohne `<example>`-Blöcke.

**Änderung:**
- `tools`-Feld komplett entfernen (Agent benötigt keine Tools)
- In die Description zwei `<example>`-Blöcke einfügen, die typische Einsatzszenarien zeigen. Format:
  ```
  <example>
  Context: User startet eine neue Literaturrecherche zu einem Thema
  user: "Suche Literatur zu 'Cloud-Security-Controls im Mittelstand'"
  assistant: "Ich nutze den query-generator-Agent, um Suchqueries für die Datenbanken zu erstellen."
  <commentary>
  Query-Generierung ist der erste Schritt jeder Recherche — Agent wird automatisch vom search-Command aufgerufen.
  </commentary>
  </example>
  ```

**Verifikation:**
- YAML parseable (`python -c "import yaml; yaml.safe_load(open('agents/query-generator.md').read().split('---')[1])"`)
- Description enthält mindestens zwei `<example>`-Blöcke

### Fix 6 — Agent `quote-extractor.md`: Frontmatter + maxTurns

**Aktuell:** `tools: ""`, `maxTurns: 20`, keine `<example>`-Blöcke.

**Änderung:**
- `tools: [Read]` als Array (Agent liest PDFs)
- `maxTurns: 5` (Quote-Extraction ist Single-Shot mit evtl. kurzer Iteration, 20 ist Overkill)
- Zwei `<example>`-Blöcke in Description

**Verifikation:** YAML parseable, `maxTurns` == 5, `tools` ist Array.

### Fix 7 — Agent `relevance-scorer.md`: Frontmatter + maxTurns

**Aktuell:** `tools: ""`, `maxTurns: 15`, keine `<example>`-Blöcke.

**Änderung:**
- `tools`-Feld entfernen (keine Tools nötig)
- `maxTurns: 3` (Batch-Scoring von 10 Papern = 1 Turn, +2 Puffer für Iteration)
- Zwei `<example>`-Blöcke in Description

**Verifikation:** analog Fix 6.

## Git-Plan

**Branch:** `refactor/e1-critical-fixes` von `main`

**Commits (atomar, revertierbar):**

| # | Commit-Message | Dateien |
|---|----------------|---------|
| 1 | `fix(skills): correct template paths in advisor, methodology-advisor, submission-checker` | 3 SKILL.md-Dateien |
| 2 | `fix(commands): restrict search agent permissions to named agents` | `commands/search.md` |
| 3 | `fix(agents): normalize tools field and add example blocks` | 3 Agent-Dateien |
| 4 | `perf(agents): reduce maxTurns for quote-extractor and relevance-scorer` | `quote-extractor.md`, `relevance-scorer.md` |

Commit 3 und 4 betreffen teils dieselben Dateien, bleiben aber getrennt, weil die Änderungstypen (Frontmatter-Normalisierung vs. Performance-Tuning) logisch unterschiedlich sind.

**Version-Bump-Commit (5):** `chore(release): v4.0.1` in `.claude-plugin/plugin.json` und `.claude-plugin/marketplace.json`.

**PR:** gegen `main`, Titel `Refactor E1: Critical Fixes (v4.0.1)`, Body referenziert den Spec.

## Verifikations-Gesamtcheck (pre-merge)

Bevor der PR gemerged wird:

1. Alle sieben Fixes verifiziert (siehe oben)
2. `git diff main..HEAD -- 'skills/**/SKILL.md' 'commands/*.md' 'agents/*.md'` manuell durchgesehen
3. Python-YAML-Parse aller geänderten Frontmatter (kein Parse-Error)
4. `jq` auf `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (valide)
5. Manuelle Sichtprüfung der `<example>`-Blöcke auf sinnvolle Szenarien

## Rollback-Plan

Bei Problemen nach Merge:
- Einzelner Fix defekt → `git revert <commit-sha>` isoliert einen Fix
- Kompletter PR defekt → `git revert -m 1 <merge-sha>` nimmt den gesamten Merge zurück
- Breaking-Verhalten → Version bleibt bei v4.0.0 in `installed_plugins.json` zurück, User updated manuell

## Erfolgskriterien für E1

- Alle drei Pfad-Bugs gefixt, referenzierte Dateien existieren
- `search.md` ruft keine unbekannten Agents mehr auf
- Alle drei Agent-Frontmatter YAML-valide, `tools` korrekt typisiert
- `maxTurns` beider betroffener Agents reduziert
- v4.0.1 gemerged und getaggt
- Keine Regressionen in den bestehenden Tests (`tests/`)

## Begleitende GitHub-Tickets

Jeder der sieben Fixes wird als Sub-Issue angelegt, verlinkt zu einem Epic-Issue `[Epic] E1: Critical Fixes (v4.0.1)`. Sub-Issues können unabhängig bearbeitet und geschlossen werden.
