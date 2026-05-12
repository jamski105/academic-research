# v6.0 Wave 2 — Chunks

**Generated:** 2026-05-12
**Tickets in scope:** #63 (Vault Phase 2), #64 (Verbatim-Guard), #68 (humanizer-de Integration)
**Deferred:** #55 (manueller Eval-Run, kein Orchestrator-Workflow)

## Dependency-Graph

```
        ┌─────────────────────────┐
        │  W2-A  #63 Vault Phase 2│
        │  refactor chapter-writer │
        │  + quote-extractor + … │
        └────────────┬────────────┘
                     │ (chapter-writer Vault-Pfad muss stehen)
                     ▼
        ┌─────────────────────────┐
        │  W2-C  #68 humanizer-de │
        │  Pipeline-Hook in       │
        │  chapter-writer + setup │
        └─────────────────────────┘

        ┌─────────────────────────┐
        │  W2-B  #64 Verbatim-Guard│   (parallel, unabhängig)
        │  PreToolUse-Hook        │
        └─────────────────────────┘
```

**Parallelism:** W2-A und W2-B parallel · W2-C nach W2-A · #55 deferred.

---

## W2-A — Vault Phase 2 (refactor)

- **Ticket:** #63
- **Branch:** `feat/v6.0-W2-A`
- **Depends_on:** —
- **Files** (boundary):
  - `agents/quote-extractor.md` (edit — `vault.add_quote()` mit `api_response_id`)
  - `skills/citation-extraction/SKILL.md` (edit — Reads via `vault.find_quotes()` + `vault.get_quote()`)
  - `skills/chapter-writer/SKILL.md` (edit — `vault.search()` + `vault.find_quotes()` statt `literature_state.md`)
  - `scripts/export-literature-state.{mjs|sh}` (NEU — read-only Snapshot-Export aus Vault)
  - `docs/AUDIT-v6-vault.md` (optional: §5 Statusmarker auf "implementiert")
- **Estimated:** 4–5 files · ~300 LOC · 6h
- **AC (verbatim aus #63):**
  - `agents/quote-extractor.md` schreibt extrahierte Zitate ausschliesslich via `vault.add_quote()` mit gefülltem `api_response_id`-Feld
  - `skills/citation-extraction/SKILL.md` liest Zitate ausschliesslich via `vault.find_quotes()` und `vault.get_quote()`
  - `skills/chapter-writer/SKILL.md` liest via `vault.search()` + `vault.find_quotes()` statt des vollständigen `literature_state.md`
  - PDFs werden via `vault.ensure_file()` als `file_id` übergeben — kein base64 mehr im Context
  - `literature_state.md` wird nur noch als read-only Snapshot-Export aus dem Vault generiert
  - Token-Boilerplate in `chapter-writer` liegt unter 2 000 Token (vorher ~10 k)
  - Eval bestätigt identische Zitat-Qualität bei ≥ −75 % Token-Verbrauch gegenüber v5.4-Baseline (manueller Snapshot im PR-Body)
- **Out of Scope** (per User-Entscheidung):
  - `PreToolUse`-Hook für Verbatim-Validation auf `kapitel/*.md` → Scope von #64

---

## W2-B — Verbatim-Guard Hook (security)

- **Ticket:** #64
- **Branch:** `feat/v6.0-W2-B`
- **Depends_on:** —
- **Files** (boundary):
  - `hooks/verbatim-guard.mjs` (NEU — PreToolUse für Write auf `kapitel/*.md`, `*.tex`)
  - `plugin.json` (edit — Hook-Eintrag, falls Plugin-Hooks dort registriert werden)
  - `evals/verbatim-guard/` (NEU — 10 Test-Cases: 5 echt, 5 erfunden)
  - `docs/AUDIT-v6-vault.md` (optional: §3 Option A Statusmarker)
- **Estimated:** 3–4 files · ~250 LOC · 5h
- **AC (verbatim aus #64):**
  - `hooks/verbatim-guard.mjs` parst Anführungszeichen-Spans (`"…"`, `„…"`, `«…»`, ` ``…'' ` )
  - Lookup gegen `vault.search_quote_text(verbatim)` — bei mismatch: Block + Hinweis
  - Bypass-Flag: `<!-- vault-guard: skip -->`
  - Eval-Set: 10 Test-Cases (5 echt / 5 erfunden)
  - Echte Vault-Quotes: 100 % pass
  - Erfundene Quotes: 100 % block
  - False-Positive-Rate < 5 %

---

## W2-C — humanizer-de Integration (feature)

- **Ticket:** #68
- **Branch:** `feat/v6.0-W2-C`
- **Depends_on:** W2-A (chapter-writer Vault-Pfad muss merged sein)
- **Files** (boundary):
  - `skills/chapter-writer/SKILL.md` (edit — humanizer-de(audit) vor quality-reviewer)
  - `agents/quality-reviewer.md` (edit — Hinweis, dass Audit-Pass bereits erfolgte)
  - `commands/setup.md` (edit — Skill-Existenz-Check für `~/.codex/skills/humanizer-de/`)
  - `evals/humanizer-de-pipeline/` (NEU — ≥3 Drafts mit GPTZero-Score-Vergleich)
- **Estimated:** 3–4 files · ~200 LOC · 4h
- **AC (verbatim aus #68):**
  - `skills/chapter-writer/SKILL.md` ruft `humanizer-de` im Mode `audit` auf, **bevor** `quality-reviewer` aufgerufen wird
  - Humanizer-Schritt nur ausgelöst, wenn `output_target ∈ {Bachelor, Master, Diplom, Dissertation}`
  - `./academic_context.md` unterstützt Bypass-Flag `humanizer_de: off`
  - `commands/setup.md` prüft Skill-Existenz unter `~/.codex/skills/humanizer-de/`; fehlt er, gibt Setup einen Hinweis aus (kein Hard-Fail)
  - `evals/humanizer-de-pipeline/` mit ≥3 Drafts inkl. GPTZero-Score-Vergleich vor/nach Humanizer-Pass
  - Ist `output_target` nicht gesetzt oder kein Hochschul-Marker enthalten, bleibt der Humanizer-Schritt standardmäßig deaktiviert
  - `agents/quality-reviewer.md` erhält Hinweis, dass `humanizer-de(audit)`-Pass bereits gelaufen ist (kein doppelter Audit-Lauf)
- **Out of Scope** (per User-Entscheidung):
  - `style-evaluator` (Roadmap §7.2 Punkt 1) bleibt unverändert

---

## Cap-Budget

- Max parallel: 2 chunks (W2-A + W2-B)
- Max sequential after: 1 chunk (W2-C)
- Per-chunk caps: ≤15 files · ≤500 LOC · ≤8h → alle 3 Chunks im Budget.

## Boundary-Overlaps

- `skills/chapter-writer/SKILL.md` berührt von W2-A und W2-C → **seriell via `depends_on`**, kein paralleler Konflikt.
- Keine weiteren Overlaps.

## Open Questions

— (alle aus Phase 0.5 in den Tickets resolved)
