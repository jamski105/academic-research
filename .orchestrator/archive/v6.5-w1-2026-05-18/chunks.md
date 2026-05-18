# v6.5 Wave 1 — Decomposition

**Strategie:** 7 Chunks in 2 Wellen. README-Konflikt zwischen D und G via Dependency serialisiert. Bekannter Cross-Chunk-Konflikt: `tests/baselines/skill_sizes.json` (B, C, E, F).

---

## Welle 1 (parallel, keine harten Dependencies)

### Chunk A — Contextual-Retrieval Vault-Erweiterung
**Tickets:** #109
**Branch:** `feat/v6.5-A-contextual-retrieval`
**Scope:**
- Embedding-Schema: kontextueller Embedding (Chunk + 1-Satz-Kontext) statt nur Chunk
- Hybrid-Retrieval: sqlite-vec + FTS5-BM25 → Reciprocal-Rank-Fusion
- `vault.search(query, rerank=true)` mit optionalem Cohere-/Voyage-Reranker
- Contextual-Embedding-Cache via Anthropic Prompt-Caching
- Eval-Set: 50 Queries × 200 Papers, Recall@10
**Files:**
- `mcp/academic_vault/db.py` (modify — Embedding-Schema)
- `mcp/academic_vault/server.py` (modify — vault.search mit rerank)
- `mcp/academic_vault/retrieval.py` (new — RRF + Reranker-Wrapper)
- `mcp/academic_vault/embeddings.py` (new — Contextual Embedding Generation)
- `tests/test_vault_contextual.py` (new)
- `tests/test_vault_rerank.py` (new)
- `tests/fixtures/retrieval_eval_set.json` (new — 50 Queries Beispieldaten)

**depends_on:** —

---

### Chunk B — Reading-List-Import Skill
**Tickets:** #95
**Branch:** `feat/v6.5-B-reading-list-import`
**Scope:**
- Input: PDF / Markdown / Plaintext mit Quellenliste
- Pipeline: LLM-Parser (Sonnet) extrahiert strukturierte Liste → DOI/ISBN-Resolution → Vault
- Optional anystyle (Ruby) als Backend (Fallback nur LLM)
- User-Rückfrage via AskUserQuestion bei Mehrdeutigkeit
- Test: 30-Item-PDF → 28+ korrekt (≥90%)
**Files:**
- `skills/reading-list-import/SKILL.md` (new)
- `skills/reading-list-import/scripts/parse_list.py` (new — Parser + Resolution)
- `skills/reading-list-import/references/format-hints.md` (new)
- `tests/test_reading_list_import.py` (new)
- `tests/fixtures/reading_list/sample.pdf` (new fixture)
- `tests/baselines/skill_sizes.json` (modify — add reading-list-import)

**depends_on:** —

---

### Chunk C — LaTeX-Export
**Tickets:** #96
**Branch:** `feat/v6.5-C-latex-export`
**Scope:**
- Markdown-Kapitel → `.tex` via Pandoc (Fallback: custom Renderer)
- Bibliographie → `.bib` (biblatex aus Vault, DIN-1505-Stil)
- Per-Uni-Template-Slot: `~/.academic-research/library-profiles/<uni>.tex.template`
- `/academic-research:latex --kapitel <n>|all --output thesis.tex`
- Verbatim-Validation auch auf `*.tex` (hook-Erweiterung)
- 3-Kapitel-Test → kompilierbares `.tex` + `.bib`
**Files:**
- `skills/latex-export/SKILL.md` (new)
- `skills/latex-export/scripts/render_tex.py` (new — Markdown → .tex)
- `skills/latex-export/scripts/build_bib.py` (new — Vault → .bib)
- `skills/latex-export/references/biblatex-din-1505.md` (new — Style-Doku)
- `commands/latex.md` (new)
- `hooks/verbatim-guard.mjs` (modify — *.tex einschließen)
- `tests/test_latex_export.py` (new)
- `tests/baselines/skill_sizes.json` (modify — add latex-export)

**depends_on:** —

---

### Chunk D — SciHub-Tier Agent
**Tickets:** #97
**Branch:** `feat/v6.5-D-scihub-tier`
**Scope:**
- `agents/scihub-fetcher.md` (Sonnet, via browser-use Skill — NICHT Playwright)
- Default OFF; Opt-in via `library-profiles/active.yaml` Flag `scihub_optin: true`
- Bei Erfolg: Vault-Eintrag-Tag `provenance: scihub` (Auditing)
- Output-Hinweis "Quelle via SciHub bezogen — bitte zusätzlich legalen Zugriff klären"
- Ethik-Disclaimer im README + Setup-Frage
**Files:**
- `agents/scihub-fetcher.md` (new)
- `library-profiles/active.yaml.template` (modify or new — scihub_optin Flag)
- `commands/setup.md` (modify — opt-in question)
- `README.md` (modify — Ethik-Disclaimer-Block; **Konflikt mit G**)
- `tests/test_scihub_optin.py` (new)

**depends_on:** — (README-Konflikt mit G handled via depends_on auf D in G)

---

### Chunk E — Topic-Brainstorm Skill
**Tickets:** #107
**Branch:** `feat/v6.5-E-topic-brainstorm`
**Scope:**
- `skills/topic-brainstorm/SKILL.md` (Trigger: "welches Thema?", "Themenfindung", "Idee evaluieren")
- Input: User-Interessen, Studienrichtung, Zeitbudget, Datenzugang
- Output: 3-5 Topic-Kandidaten mit Feasibility/Novelty/Career-Fit-Score
- Pro Topic: 2-3 Forschungsfragen + 1 Pilot-Paper-Set
- Top-Topic landet in `academic_context.md`
**Files:**
- `skills/topic-brainstorm/SKILL.md` (new)
- `skills/topic-brainstorm/scripts/scorer.py` (new — Feasibility/Novelty/Career-Fit-Heuristik)
- `skills/topic-brainstorm/references/scoring-criteria.md` (new)
- `tests/test_topic_brainstorm.py` (new)
- `tests/baselines/skill_sizes.json` (modify — add topic-brainstorm)

**depends_on:** —

---

### Chunk F — Output-Erweiterung (Grant + Poster + Response)
**Tickets:** #108
**Branch:** `feat/v6.5-F-output-extensions`
**Scope (3 Sub-Skills):**
- `skills/grant-proposal/SKILL.md` — DFG/BMBF/EU mit Vault-Quellen, Templates pro Förderlinie
- `skills/conference-poster/SKILL.md` — A0-Poster (LaTeX tikzposter / PowerPoint)
- `skills/reviewer-response/SKILL.md` — point-by-point Response-Letter
- Default OFF — opt-in via `output_targets` in academic_context.md
**Files:**
- `skills/grant-proposal/SKILL.md` (new)
- `skills/grant-proposal/references/dfg.md` (new)
- `skills/grant-proposal/references/bmbf.md` (new)
- `skills/grant-proposal/references/eu-horizon.md` (new)
- `skills/conference-poster/SKILL.md` (new)
- `skills/conference-poster/references/tikzposter-template.md` (new)
- `skills/reviewer-response/SKILL.md` (new)
- `tests/test_grant_proposal.py` (new)
- `tests/test_conference_poster.py` (new)
- `tests/test_reviewer_response.py` (new)
- `tests/baselines/skill_sizes.json` (modify — 3 Einträge)

**depends_on:** —

---

## Welle 2 (nach Welle 1, depends_on D)

### Chunk G — README + CHANGELOG + Migration-Guide
**Tickets:** #98
**Branch:** `feat/v6.5-G-docs-rewrite`
**Scope:**
- `README.md` Rewrite für v6.x: Vault-Section, Universal Book Fetcher, humanizer-de, Per-Uni-Profile, **SciHub-Disclaimer (von D übernommen)**, neue v6.4/v6.5-Features (PRISMA, Meta-Analysis, RoB, Material-Passport, Hooks-Stack, Contextual-Retrieval, LaTeX-Export, Topic-Brainstorm, Grant/Poster/Response, Reading-List-Import)
- `CHANGELOG.md`: alle v6.x-Releases (v6.0/v6.1/v6.2/v6.3/v6.4/v6.5) dokumentiert
- `docs/MIGRATION-v5-to-v6.md`: literature_state → Vault, Skills-Änderungen, Hooks, Per-Uni-Profil
- Glossar erweitern (Vault, Subagent, Site-Profile)
**Files:**
- `README.md` (modify — full rewrite, integriert D's Ethik-Disclaimer)
- `CHANGELOG.md` (new or rewrite)
- `docs/MIGRATION-v5-to-v6.md` (new)

**depends_on:** D (README-Konflikt: D hat Ethik-Disclaimer-Block eingefügt; G integriert ihn in den Rewrite)

---

## Cross-Chunk-Konflikt: `tests/baselines/skill_sizes.json`

4 Chunks (B, C, E, F) ergänzen die JSON-Map. Bekanntes Pattern aus v6.3/v6.4:
- L1 schreibt seinen Eintrag in den Worktree
- Beim Merge auf main muss der nachfolgende PR die JSON konfliktfrei rebasen (manuelle Konflikt-Auflösung via Merge-Commit, da Force-Push verboten)

**L0-Strategie für Phase 7:** Sequentielle Merges via Merge-Commit-Pattern.

---

## Dependency-Graph

```
A — independent
B — independent
C — independent
D ──┐
E — │ independent
F — │ independent
    └──> G (README-Konflikt-Auflösung)
```

## Parallelism Plan

- **Welle 1:** A, B, C, D, E, F — 6 L1-Agents parallel
- **Welle 2 (nach D merge-ready):** G — 1 L1-Agent

## Wave-Total

- 7 Chunks
- 7 Tickets vollständig adressiert
- ~45 Files (modify+new) verteilt
