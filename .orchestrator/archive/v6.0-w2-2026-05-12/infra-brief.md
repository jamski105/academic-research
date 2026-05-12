# infra-brief

**Stack:** Claude-Code Plugin-Repo (kein Build-System).
Bestandteile: Markdown (`agents/`, `skills/`, `commands/`, `docs/`),
JS-Hooks (`hooks/*.mjs`, ESM), Bash-Hooks (`hooks/*.sh`),
YAML-Config (`.orchestrator/`, `plugin.json`).

**Test:** Keine Unit-Tests im Plugin-Repo. Eval-Suite läuft separat in
`tests/evals/` und ist lokal-only (braucht `ANTHROPIC_API_KEY`).
Smoke-Checks via `gh issue view`, `gh pr view`, `bash scripts/...`.

**Lint:** keiner konfiguriert.

**Typecheck:** keiner konfiguriert.

**Branch base:** `main`

**Branch pattern:** `feat/v6.0-{chunk_id}` (z. B. `feat/v6.0-F`)

**Conventions** (aus README.md, docs/AUDIT-v6-*):
- Plugin-Design bevorzugt **Agenten/Skills** über Python-Skripte.
- Excel via `document-skills:xlsx`-Skill, nicht selbstgebaut.
- Browser-Automation via `browser-use` (nicht Playwright).
- Deutsche Sprache mit voller Orthografie für User-Facing-Texte.
- Vendoring von Skills statt MCP-Calls, wo möglich (Token-Optimierung).

**CI workflow names:** keine (`.github/workflows/` existiert nicht).
PRs werden manuell oder via `gh pr merge` gemerged.

**Code-Pfade Wave 2:**
- `agents/quote-extractor.md` (#63)
- `skills/citation-extraction/SKILL.md` (#63)
- `skills/chapter-writer/SKILL.md` (#63, #68)
- `agents/quality-reviewer.md` (#68)
- `commands/setup.md` (#68 — Skill-Check)
- `hooks/verbatim-guard.mjs` (NEU, #64)
- `evals/` (#64 — Test-Set)
