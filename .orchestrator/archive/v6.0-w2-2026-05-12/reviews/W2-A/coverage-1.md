# Coverage Report — W2-A · Iteration 1

**PR:** #118 — v6.0/W2-A: Vault Phase 2 — quote-extractor & chapter-writer auf Vault umstellen  
**Ticket:** #63  
**Date:** 2026-05-12  
**Reviewer model:** claude-sonnet-4-6

---

## Methodology Note

This codebase uses Markdown-based Skill/Agent files as the primary artifacts (no compiled code). The existing test infrastructure consists of:

1. **Eval suites** (`evals/<component>/evals.json` + `tests/evals/test_<component>_evals.py`) — LLM-driven behavioural evals, parametrized, gated by `pytest.mark.skipif` when the evals.json is missing.
2. **Smoke tests** (`tests/test_*.py`) — structural/regression tests that scan Markdown files.
3. **Grep smoke checks** — the spec (W2-A.md) explicitly defines grep commands as the accepted verification method ("Verifikation" per AC).

**No test files appear in the PR diff.** The diff contains only:
- `agents/quote-extractor.md` (modified)
- `skills/citation-extraction/SKILL.md` (modified)
- `skills/chapter-writer/SKILL.md` (modified)
- `scripts/export-literature-state.mjs` (new)
- `scripts/export-literature-state.sh` (new)
- `docs/AUDIT-v6-vault.md` (modified)
- `specs/v6.0/W2-A.md` (new)
- `specs/v6.0/W2-A-plan.md` (new)

The existing evals (`evals/quote-extractor/evals.json`, `evals/chapter-writer/evals.json`, `evals/citation-extraction/evals.json`) were **not updated** in this PR to reflect Vault-specific behaviour (e.g., no eval asserts `vault_quote_id` in output, no eval asserts `vault.add_quote()` call, no eval checks that `pdf_text` is absent from input).

**Assessment basis:** Implementation evidence is drawn from the diff. Test evidence is drawn from (a) the diff, (b) existing evals that exercise the changed components, and (c) the spec's explicit definition of grep-based smoke checks as acceptable verification.

---

## COVERAGE REPORT

### AC1: quote-extractor schreibt via vault.add_quote() mit gefülltem api_response_id (kein JSON-File-Schreibpfad mehr)

**FAIL — Implementation PASS, Test FAIL**

**Implementation evidence:**
- `agents/quote-extractor.md` diff adds a new "## Vault-Persistenz" section (line ~+88 in diff) with explicit `vault.add_quote()` call including `api_response_id=response.id` as mandatory field.
- Frontmatter updated: `tools: [Read, mcp__academic_vault__vault_ensure_file, mcp__academic_vault__vault_add_quote]`
- Explicit instruction: "Kein JSON-File schreiben — der Vault ist der einzige Persistenz-Pfad."
- `api_response_id` marked as **Pflicht** with error if empty.

**Test evidence:**
- No test in the PR diff asserts that `vault.add_quote()` is called by the agent.
- Existing eval `evals/quote-extractor/evals.json` (tests/evals/test_quote_extractor_evals.py) still uses prompts that supply `PDF-Text` directly in input (e.g. `qe-01`, `qe-02`), which contradicts the new Vault-based flow. The evals were not updated to use `paper_id` as input or assert `vault_quote_id` in output.
- No eval asserts absence of JSON file writes.
- Spec verification method (grep) is a structural check on the Markdown file, not a behavioural test. It was not run as part of the PR's CI (no evidence in `statusCheckRollup: []`).

**Gap:** No test asserts `vault.add_quote()` is invoked with a non-empty `api_response_id`. Existing evals exercise the old interface (pdf_text in input) and were not updated.

---

### AC2: citation-extraction liest Zitate via vault.find_quotes() und vault.get_quote() (kein direkter PDF-Lesepfad)

**FAIL — Implementation PASS, Test FAIL**

**Implementation evidence:**
- `skills/citation-extraction/SKILL.md` diff:
  - "## Kontext-Dateien" section removes `literature_state.md` as a read source, adds `vault.find_quotes(paper_id, query)` and `vault.get_quote(quote_id)`.
  - §2 "PDFs lokalisieren" replaced by "Relevante Paper aus Vault laden" with `vault.find_quotes()` + `vault.get_quote()` calls.
  - §3 removes `pdf_text` from the agent-spawn input JSON; `paper_id` added instead.
  - §7 "Literaturstatus aktualisieren" replaced — no write to `literature_state.md`.

**Test evidence:**
- No test in the PR diff covers vault-based citation reading.
- Existing eval `evals/citation-extraction/evals.json` tests citation formatting (APA7, Harvard, Chicago inline cites) — these do not cover the §2/§3 workflow changes at all. None assert that `vault.find_quotes()` is the source, or that `pdf_text` is absent.
- No regression test asserts absence of `pdf_text` or `pdfs/` in the skill's primary workflow.

**Gap:** No test exercises the vault.find_quotes() / vault.get_quote() reading path. Existing evals test citation formatting, not the data-acquisition workflow changed by this AC.

---

### AC3: chapter-writer liest via vault.search() + vault.find_quotes() statt vollständigem literature_state.md

**FAIL — Implementation PASS, Test FAIL**

**Implementation evidence:**
- `skills/chapter-writer/SKILL.md` diff:
  - Overview updated: "Zieht Zitate via `vault.search()` + `vault.find_quotes()`"
  - "## Kontext-Dateien" removes `literature_state.md` from read list; adds `vault.search(query, k=5)` and `vault.find_quotes(paper_id, query, k=3)`.
  - §1 "Kontext laden" removes `literature_state.md` load; adds explanation that Vault-Queries are used in step 3.
  - §3 "Kapitelplanung" adds Vault-Query block showing `vault.search()` → `vault.find_quotes()` pattern.
  - Citations-API workflow updated from `literature_state.md` → `vault.search()` → `vault.find_quotes()` → `vault.ensure_file()`.

**Test evidence:**
- No test in the PR diff asserts vault.search() or vault.find_quotes() is used by chapter-writer.
- Existing eval `evals/chapter-writer/evals.json` tests that the skill produces correct output given source lists in the prompt — but these prompts still supply sources inline (e.g. "Quellenliste: Smith (2023), Tanaka (2024)"), not via Vault. No eval asserts that `literature_state.md` is NOT loaded.
- No structural test (like `test_cross_references.py`) checks that chapter-writer no longer references `literature_state.md` as a primary read source.

**Gap:** No test asserts vault-based source loading in chapter-writer. Existing evals bypass the new source-acquisition path entirely by providing sources inline.

---

### AC4: PDFs via vault.ensure_file() als file_id — kein base64 mehr im Context

**FAIL — Implementation PASS, Test FAIL**

**Implementation evidence:**
- `agents/quote-extractor.md` diff:
  - Primary path changed: `file_id = vault.ensure_file(paper_id)` (MCP-Tool-Call), replaces `ensure_uploaded(pdf_path, client)`.
  - Fallback explicitly marked: "Fallback (base64) wenn `vault.ensure_file()` `None` zurückgibt oder Vault nicht verfügbar".
  - `pdf_text` removed from input schema; `paper_id` added.
  - Batch caching section updated: `file_id = vault.ensure_file(paper_id)  # gecacht im Vault, kein Re-Upload`.
- `skills/chapter-writer/SKILL.md` diff updates Citations-API workflow: `vault.ensure_file(paper_id)` → `file_id` for `documents[]`.
- `skills/citation-extraction/SKILL.md` diff explicitly states: "PDFs werden via `vault.ensure_file(paper_id)` als `file_id` übergeben — kein direktes `pdf_path` im Context."

**Test evidence:**
- No test in the PR diff verifies that base64 is not passed in the primary path.
- Existing quote-extractor evals (`qe-01`, `qe-02`, `qe-04`) still pass `PDF-Text` inline in the eval prompt — these implicitly test the old base64/pdf_text path, not vault.ensure_file(). These evals were not updated to use `paper_id`.
- The spec's verification method (grep for `vault.ensure_file`) was not run in CI (statusCheckRollup is empty).

**Gap:** Existing evals actively use the old interface (pdf_text as input), which contradicts AC4's intent. No test asserts the new primary path via vault.ensure_file().

---

### AC5: literature_state.md nur noch read-only Snapshot-Export aus dem Vault

**PASS — Implementation PASS, Test PARTIAL (acceptable)**

**Implementation evidence:**
- `scripts/export-literature-state.mjs` (180 lines, new file): reads Vault SQLite directly, generates `literature_state.md` with read-only header marker ("Read-only Export aus dem Vault", "Nicht manuell bearbeiten").
- `scripts/export-literature-state.sh` (6 lines, new thin wrapper).
- `skills/citation-extraction/SKILL.md` §7 updated: "Der Vault ist die Quelle der Wahrheit. `./literature_state.md` ist ein read-only Snapshot-Export — nicht beschreiben."
- `skills/chapter-writer/SKILL.md` updated: "`./literature_state.md` nicht laden (ist read-only Snapshot — bei Bedarf via `node scripts/export-literature-state.mjs` regenerieren)"
- `agents/quote-extractor.md` updated: no write reference to `literature_state.md`.
- `docs/AUDIT-v6-vault.md` updated: "`literature_state.md` nur noch read-only Snapshot-Export ✅"

**Test evidence:**
- No test in the PR diff explicitly asserts the read-only contract.
- However: the spec's AC5 verification is (a) grep for no write instructions in agent/skill files — which is satisfied by the diff — and (b) existence of `scripts/export-literature-state.mjs` with meaningful content — satisfied.
- The snapshot file contains a clear read-only header marker (satisfies spec's "Header-Marker erfüllt AC" note from PR pre-review).
- `test_cross_references.py` and other structural tests scan `skills/` and `agents/` for regressions, which provides ongoing coverage for structural invariants. While no specific test for "no write to literature_state.md" exists, the implementation evidence is unambiguous and the spec's own verification criteria are met.

**Assessment:** AC5 is primarily a structural/contractual AC (no test framework can easily assert LLM runtime behaviour of "not writing a file"). Implementation fully satisfies the spec's stated verification criteria. Marking PASS with caveat that no automated write-guard exists.

---

### AC6: Token-Boilerplate in chapter-writer unter 2000 Token

**PASS — Implementation PASS, Test PASS (manual snapshot in PR body)**

**Implementation evidence:**
- `skills/chapter-writer/SKILL.md` diff removes the full `literature_state.md` load (~3000-8000 Token) and PDF-base64 sections.
- Replacement: `vault.search(query, k=5)` + `vault.find_quotes()` calls (~1700 Token per PR body table).
- Inline comment in diff: "maximal ~1700 Token Quellen-Kontext statt vollständigem `literature_state.md`-Dump (~8–15 k Token)".

**Test evidence:**
- The spec defines AC6 verification as: `wc -w skills/chapter-writer/SKILL.md` as proxy + documented count in PR body.
- PR body contains the required token-count table:
  - `vault.search()` + `vault.find_quotes()`: ~1700 Token (< 2000 threshold)
  - Previous boilerplate: ~8000-15000 Token
- This is the spec's own defined verification method. The PR body table constitutes the required evidence.

**Assessment:** PASS per spec's defined verification criteria (manual snapshot). No automated token-count test exists or is required per spec.

---

### AC7: Eval bestätigt identische Zitat-Qualität bei mindestens -75% Token-Verbrauch gegenüber v5.4-Baseline (manueller Token-Count-Snapshot im PR-Body)

**PASS — Implementation PASS, Manual Eval PASS**

**Evidence:**
- PR body contains the required before/after comparison table:
  | Komponente | v5.4 Laufzeit-Boilerplate | v6.0 Vault-Calls |
  |---|---|---|
  | `literature_state.md` laden | ~3000–8000 Token | entfällt |
  | PDF-Auszüge via base64 | ~5000–12000 Token pro PDF | entfällt |
  | `vault.search()` + `vault.find_quotes()` | — | ~1700 Token |
  | **Total chapter-writer** | **~8000–15000 Token** | **~1700 Token** |
  | **Reduktion** | | **~83 % (AC: ≥ −75 %)** |

- Spec AC7 explicitly states: "Kein automatisierter Eval in diesem Ticket. Stattdessen: manueller Token-Count-Snapshot (v5.4-Baseline vs. v6.0-Post-Migration) im PR-Body dokumentiert."
- PR body satisfies this requirement exactly: baseline documented, post-migration documented, delta = ~83% ≥ 75% threshold.
- Quality assertion ("identische Zitat-Qualität"): the spec acknowledges this is not automatically verified; the PR body documents it as satisfied via the structural preservation of the Citations-API workflow (same `documents[]` parameter pattern, same verbatim extraction logic).

**Assessment:** PASS per spec's own defined verification criteria. The spec does not require an automated eval for AC7; it explicitly accepts a manual snapshot.

---

## Summary

| AC | Status | Key Gap |
|----|--------|---------|
| AC1 | FAIL | No test asserts vault.add_quote() with api_response_id; existing evals use old pdf_text interface |
| AC2 | FAIL | No test exercises vault.find_quotes()/get_quote() reading path; existing evals test formatting only |
| AC3 | FAIL | No test asserts vault.search()+vault.find_quotes() in chapter-writer; evals supply sources inline |
| AC4 | FAIL | No test asserts vault.ensure_file() primary path; existing evals still pass pdf_text directly |
| AC5 | PASS | Structural implementation complete; spec verification criteria met; no automated write-guard needed |
| AC6 | PASS | Manual token snapshot in PR body satisfies spec's defined verification method |
| AC7 | PASS | Manual before/after table in PR body satisfies spec's explicit requirement |

**FAIL count: 4 (AC1–AC4). Root cause: Existing evals for quote-extractor, citation-extraction, and chapter-writer were not updated to reflect the Vault-based interface. The evals still test the old pdf_text/inline-source flow, making them orthogonal to (and in some cases contradictory of) the new AC requirements.**

**Mitigation context:** This repo uses LLM-driven evals rather than unit tests. The spec defines grep-based smoke checks as the primary AC verification method, which is inherently structural rather than behavioural. The FAIL verdict reflects the strict "tested" criterion from the coverage-checker prompt (a test that asserts the AC's described behaviour must exist in or be activated by the PR). If the project's test philosophy treats grep-smoke-checks as sufficient test evidence, AC1–AC4 could be re-evaluated as PASS — but by the strict "Tested: test added/modified that asserts the behavior" criterion, they FAIL.
