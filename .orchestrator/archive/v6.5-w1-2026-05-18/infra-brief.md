# infra-brief — v6.5

## Stack
- Python 3.10+ (deps via `scripts/requirements.txt`)
- pytest (~60 Tests nach v6.4)
- MCP-Server: `mcp/academic_vault/` (SQLite + Files-API + neu: sqlite-vec + FTS5)
- Hooks: Node (`*.mjs`) — verbatim-guard, pre-compact, post-tool-use-decisions, mid-session-reinforcement
- Skills: Markdown (SKILL.md) + ggf. Python-Scripts/References
- Agents: Markdown (Sonnet-basiert)

## Test / Lint / Typecheck
- **Test:** `pytest` (Repo-Root) oder `pytest tests/test_<name>.py`
- **Lint:** ad-hoc `python -m py_compile`
- **Typecheck:** keine zentrale mypy-Config

## Branching
- **Base:** `main`
- **Pattern:** `feat/v6.5-<chunk_id>-<slug>`
- **State-Sync:** `mmp/state/v6.5`
- **Archive:** `mmp/archive/v6.5-w1-<date>`

## Conventions (aus Memory + Repo-Praxis)
1. **Plugin-Design:** Agenten/Skills vor Python-Skripten. Statistik/deterministische Logik darf Python sein (z.B. RRF in #109, biblatex-Renderer in #96).
2. **Excel:** `document-skills:xlsx` Skill nutzen.
3. **Browser:** `browser-use` Skill, nicht Playwright-MCP. **Relevant für #97 SciHub-Subagent.**
4. **Sprache:** Deutsch in User-facing-Text; Code/Identifier in EN.
5. **Verbatim-Garantie:** Quotes/Figures via Vault-MCP. In #96 (LaTeX) Verbatim-Validation auch auf `*.tex`.
6. **Squash-Merge:** `gh pr merge --squash --delete-branch`.
7. **Keine --force-Pushes / --no-verify** ohne explizite User-Bestätigung.
8. **Ethik #97 SciHub:** Default OFF, opt-in mit explizitem Disclaimer; Provenance-Tag im Vault.

## CI workflow names
- Kein CI in `.github/workflows/` — Tests laufen lokal

## Sicherheitshinweise
- **API-Keys:** Anthropic-Key + Voyage-/Cohere-Key (für #109 Reranking) in 0600-Config (`~/.academic-research/config.yaml`)
- **Vault-DB:** `~/.academic-research/projects/<slug>/vault.db`
- **PDFs:** `~/.academic-research/pdfs/`
- **SciHub-Opt-in:** `library-profiles/active.yaml` Flag `scihub_optin: true`

## Bash 5 erforderlich
- mmp-lock-scripts brauchen bash 4+ (`/opt/homebrew/bin/bash` statt macOS-default 3.2)

## Bekannte Quirks (aus v6.3 + v6.4)
- L1-Tests dürfen niemals Output-Files im Repo-Root ablegen — immer `tmp_path`
- `tests/baselines/skill_sizes.json` wird bei jedem Skill-Add geändert — sequentiell mergen
- Force-Push verboten → Konflikte via Merge-Commit + Push (kein Rebase auf gepushte Branches)
- `mcp/academic_vault/server.py` ist hochfrequent geändert — bei mehreren Chunks im Vault-Bereich Konsolidierung in einen Chunk bevorzugen
- v6.4: 91c1945-style "stash-pop-Unfälle" — L1-Agents auf saubere Commits achten

## v6.5-Besonderheiten
- **#109:** sqlite-vec ist bereits im Vault verfügbar; Embeddings via Voyage-3 / Granite (lokal) oder Anthropic
- **#108:** 3 neue Skills mit Templates (DFG/BMBF/EU für Grant) — Default-Off-Pattern via output_targets
- **#107:** Übergang zu research-question-refiner darf nicht hardcoded sein — soft handover via academic_context.md
- **#98:** README-Rewrite ist groß; CHANGELOG.md neu anlegen oder existierend?
- **#97:** browser-use Skill (NICHT Playwright-MCP); strenge Ethik-Pfad
- **#96:** Pandoc als externe Dep optional — fallback custom Renderer
- **#95:** anystyle (Ruby) optional — fallback nur LLM-Parser
