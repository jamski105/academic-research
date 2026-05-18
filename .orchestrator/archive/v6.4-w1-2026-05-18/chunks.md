# v6.4 Wave 1 — Decomposition

**Strategie:** 8 Chunks in 2 parallelen Wellen.
Datei-Konflikte vermieden über Dependency-Serialisierung; bekannter Cross-Chunk-Konflikt: `tests/baselines/skill_sizes.json` (mehrere Chunks fügen Skill-Einträge hinzu — Merge-Konflikt-Pattern aus v6.3 bekannt, sequentiell mergen).

---

## Welle 1 (parallel, keine Dependencies untereinander)

### Chunk A — Vault-Foundation (Schema + MCP-Tools)
**Tickets:** #90 (Daten-Layer), #100 (Daten-Layer), #102 (Daten-Layer), #104 (Daten-Layer)
**Branch:** `feat/v6.4-A-vault-foundation`
**Scope:**
- Neue Tabellen: `decisions`, `glossary`, `style_overrides`, `score_history`, `risk_of_bias_assessments`, `material_passport`, `vault_locked_status`
- Neue MCP-Tools (Vault):
  - `vault.add_decision(category, text, rationale)`, `vault.list_decisions(category?, active_only?)`
  - `vault.glossary_add(term, def)`, `vault.glossary_lookup(term)`
  - `vault.style_overrides_add(key, value)`, `vault.style_overrides_list()`
  - `vault.add_score_snapshot(paper_id, session_id, scores_json)`, `vault.get_score_history(paper_id, k?)`
  - `vault.add_risk_of_bias(paper_id, study_type, domain_scores_json)`, `vault.list_risk_of_bias(paper_id?)`
  - `vault.export_material_passport(slug)` → schreibt JSON gegen `material-passport.schema.json`
  - `vault.lock_passport(slug)` / `vault.is_locked(slug)`
  - `vault.export_snapshot(slug)` → Tarball (für #91-Hook)
- JSON-Schema für material-passport.json
**Files (boundary):**
- `mcp/academic_vault/db.py` (modify — Tabellen + DAO-Methoden)
- `mcp/academic_vault/migrate.py` (modify — Migration v6.4)
- `mcp/academic_vault/server.py` (modify — MCP-Tool-Registrierungen)
- `mcp/academic_vault/material_passport.py` (new — Builder + Schema-Validation)
- `mcp/academic_vault/material-passport.schema.json` (new)
- `tests/test_vault_decisions.py` (new)
- `tests/test_vault_score_history.py` (new)
- `tests/test_vault_material_passport.py` (new)
- `tests/test_vault_risk_of_bias.py` (new)

**depends_on:** —

---

### Chunk C — Search-Workflow Extensions (PRISMA-Counter + Batch + Interactive)
**Tickets:** #92, #94, #105
**Branch:** `feat/v6.4-C-search-workflow`
**Scope:**
- `commands/search.md`: `--batch` (≥50 Paper) + `--interactive` Flag dokumentieren
- `scripts/search.py`: Counter pro Modul (n_identified/n_after_dedup/n_excluded_screening/n_excluded_eligibility/n_included); Batch-Submission via Anthropic Message-Batches; Interactive-Mode Phase-1-Outline + Approval-Gate
- `scripts/batch_api.py` (new): Anthropic-Batch-API-Wrapper
- `skills/prisma-flow/SKILL.md` (new): rendert Mermaid in `kapitel/methodik.md`
- `skills/prisma-flow/references/prisma-checklist.md` (new, 27 PRISMA-2020-Items)
- `skills/prisma-flow/scripts/render_flow.py` (new): Mermaid-Renderer
- `skills/chapter-writer/SKILL.md` (modify): Approval-Gate nach Outline
- `tests/baselines/skill_sizes.json` (modify — add prisma-flow)
**Files (boundary):**
- `commands/search.md`
- `scripts/search.py`
- `scripts/batch_api.py` (new)
- `skills/prisma-flow/SKILL.md` (new)
- `skills/prisma-flow/references/prisma-checklist.md` (new)
- `skills/prisma-flow/scripts/render_flow.py` (new)
- `skills/chapter-writer/SKILL.md`
- `tests/test_prisma_flow.py` (new)
- `tests/test_batch_api.py` (new)
- `tests/test_search_interactive.py` (new)
- `tests/baselines/skill_sizes.json`

**depends_on:** —

---

### Chunk E — Meta-Analysis Agent
**Tickets:** #101
**Branch:** `feat/v6.4-E-meta-analysis`
**Scope:**
- `agents/meta-analysis.md` (Sonnet) — Input: ≥3 Studien aus Vault
- `scripts/meta_analysis.py` — DerSimonian-Laird Random-Effects-Modell, I² + τ², Forest-Plot Mermaid
- Output in `kapitel/meta-analyse.md`
- Out of Scope: Network-Meta-Analyse
**Files (boundary):**
- `agents/meta-analysis.md` (new)
- `scripts/meta_analysis.py` (new)
- `skills/_common/meta-analysis-models.md` (new — DerSimonian-Laird Doku)
- `tests/test_meta_analysis.py` (new)

**depends_on:** —

---

### Chunk G — Citation-Styles MLA/Vancouver/Springer
**Tickets:** #106
**Branch:** `feat/v6.4-G-citation-styles`
**Scope:**
- 3 neue References (mla.md, vancouver.md, springer-author-date.md, je 8. Ed./aktuell)
- Variant-Selector in `skills/citation-extraction/SKILL.md` auf 7 Stile erweitern
- Eval: pro Stil 5 Beispiel-Quellen
**Files (boundary):**
- `skills/citation-extraction/references/mla.md` (new)
- `skills/citation-extraction/references/vancouver.md` (new)
- `skills/citation-extraction/references/springer-author-date.md` (new)
- `skills/citation-extraction/SKILL.md`
- `tests/test_citation_styles_v6_4.py` (new)

**depends_on:** —

---

### Chunk H — CSL-Import Skill
**Tickets:** #93
**Branch:** `feat/v6.4-H-csl-import`
**Scope:**
- `skills/citation-style-import/SKILL.md` (new)
- `skills/citation-style-import/scripts/csl_import.py` (new) — lädt `.csl` aus citation-style-language/styles
- Parser extrahiert relevante Felder zu Prompt-Regeln
- Output: `skills/citation-extraction/references/custom-<style>.md`
- `tests/baselines/skill_sizes.json` (modify — add citation-style-import)
**Files (boundary):**
- `skills/citation-style-import/SKILL.md` (new)
- `skills/citation-style-import/scripts/csl_import.py` (new)
- `skills/citation-style-import/references/csl-spec.md` (new)
- `tests/test_csl_import.py` (new)
- `tests/baselines/skill_sizes.json`

**depends_on:** —

---

## Welle 2 (parallel nach Welle 1, depends_on A)

### Chunk B — Hooks-Stack + history.md
**Tickets:** #91, #103
**Branch:** `feat/v6.4-B-hooks-stack`
**Scope:**
- `hooks/pre-compact.mjs` (new): schreibt Tarball aus academic_context.md + literature_state.md + writing_state.md + `vault.export_snapshot()` nach `~/.academic-research/snapshots/<slug>/<ts>.tgz`
- `hooks/post-tool-use-decisions.mjs` (new): bei `Write` auf `*.md` im Projektordner → 1-Zeile in `decisions.log`
- `hooks/mid-session-reinforcement.mjs` (new): nach 20 User-Messages oder Compaction → System-Hint mit Top-5-Decisions aus `vault.list_decisions(active_only=true)`
- `hooks/hooks.json` (modify): neue Hooks registrieren
- `commands/history.md` (modify): `--restore <ts>` packt Snapshot zurück
**Files (boundary):**
- `hooks/pre-compact.mjs` (new)
- `hooks/post-tool-use-decisions.mjs` (new)
- `hooks/mid-session-reinforcement.mjs` (new)
- `hooks/hooks.json`
- `commands/history.md`
- `tests/test_hook_snapshot.py` (new)
- `tests/test_hook_decisions_log.py` (new)
- `tests/test_hook_midsession.py` (new)
- `tests/test_history_restore.py` (new)

**depends_on:** A (nutzt `vault.export_snapshot`, `vault.list_decisions`, `vault.add_decision`)

---

### Chunk D — Risk-of-Bias Agent
**Tickets:** #100 (Agent-Anteil)
**Branch:** `feat/v6.4-D-risk-of-bias`
**Scope:**
- `agents/risk-of-bias.md` (Sonnet) — Cochrane RoB 2 / ROBINS-I / CASP
- Per Domain: low | some concerns | high + Begründung mit verbatim Quote via `vault.add_quote`
- Vault-Persistence via `vault.add_risk_of_bias` (kommt aus Chunk A)
- PRISMA-Flow zeigt RoB-Verteilung (Verzahnung mit Chunk C, lose — kein File-Konflikt)
**Files (boundary):**
- `agents/risk-of-bias.md` (new)
- `skills/_common/rob-cochrane-refs.md` (new)
- `skills/_common/rob-casp-refs.md` (new)
- `skills/_common/rob-robins-i-refs.md` (new)
- `tests/test_risk_of_bias_agent.py` (new)

**depends_on:** A (nutzt `vault.add_risk_of_bias`, `vault.add_quote`)

---

### Chunk F — Material-Passport Skill
**Tickets:** #104 (Skill-Anteil)
**Branch:** `feat/v6.4-F-material-passport`
**Scope:**
- `skills/material-passport/SKILL.md` (new) — Trigger: User-Request "Reproduzierbarkeits-Manifest"
- `skills/material-passport/scripts/build_passport.py` (new) — Wrapper um `vault.export_material_passport`
- Ergänzt `kapitel/methodik.md` automatisch um Block "Reproduzierbarkeit"
- `vault.lock_passport()` Aufruf bei Abgabe
- `tests/baselines/skill_sizes.json` (modify — add material-passport)
**Files (boundary):**
- `skills/material-passport/SKILL.md` (new)
- `skills/material-passport/scripts/build_passport.py` (new)
- `tests/test_material_passport_skill.py` (new)
- `tests/baselines/skill_sizes.json`

**depends_on:** A (nutzt `vault.export_material_passport`, `vault.lock_passport`)

---

## Cross-Chunk-Konflikt: `tests/baselines/skill_sizes.json`

Drei Chunks (C, F, H) ergänzen die JSON-Map. Bekanntes v6.3-Pattern:
- L1 schreibt seinen Eintrag in den Worktree
- Beim Merge auf main muss der nachfolgende PR die JSON konfliktfrei rebasen (manuelle Konflikt-Auflösung wie bei v6.3 PR #144)

L0-Strategie: Wenn Welle-1-PRs sequentiell auf main mergen, Konflikte lösen wir Chunk-für-Chunk in Phase 7.

---

## Dependency-Graph

```
A ────┐
      ├──> B
      ├──> D
      └──> F
C — independent
E — independent
G — independent
H — independent
```

## Parallelism Plan

- **Welle 1:** A, C, E, G, H — 5 L1-Agents parallel
- **Welle 2 (nach A merge-ready):** B, D, F — 3 L1-Agents parallel

## Wave-Total

- 8 Chunks
- 12 Tickets vollständig adressiert
- ~57 Files (modify+new) verteilt
