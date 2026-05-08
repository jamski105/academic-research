# infra-brief

Stack: Python 3.x Claude-Code-Plugin (academic-research v5.4.0)
Dependencies: anthropic>=0.40, httpx>=0.25, PyPDF2>=3.0, pyyaml>=6.0, openpyxl>=3.1, pandas>=2.0
(siehe `scripts/requirements.txt`)

Test: `pytest tests/ -v`
Lint: keine Konfiguration vorhanden (kein ruff/black/flake8 im Repo)
Typecheck: keine Konfiguration vorhanden (kein mypy/pyright)
Branch base: main
Branch pattern: `feat/v6.0-{chunk_id}`

## Konventionen

- **Repo-Typ:** Claude-Code-Plugin (siehe `.claude-plugin/plugin.json`).
- **Komponenten:**
  - `commands/` — Slash-Commands (`*.md` mit YAML-Frontmatter)
  - `agents/` — Subagents (`*.md` mit YAML-Frontmatter)
  - `skills/` — Skills (`SKILL.md` + optional `references/`)
  - `hooks/hooks.json` — Hook-Definitionen
  - `scripts/` — Python-Helper (search, dedup, pdf, project_bootstrap)
  - `tests/` — pytest, inkl. `tests/evals/` für Eval-Suite
  - `evals/` — 43 Quality-Prompts + 260 Trigger-Prompts (siehe `evals/SCHEMA.md`)
- **Sprache:** Deutsch in Kommentaren/Docs/Tickets, Englisch in Code-Identifiern.
- **Keine .github/workflows/** — kein CI im Repo. Tests laufen lokal.
- **Kein AGENTS.md / CLAUDE.md** auf Repo-Root.
- **`.claude/settings.json`** existiert (Plugin-eigene Settings).
- **xlsx-Skill ist vendored** (siehe Commit 5a295b1, PR #58).

## CI workflow names

(keine — kein .github/workflows/ Verzeichnis)

## Test-Konvention

`tests/` enthält Top-Level Pytest-Files:
- `test_search.py`, `test_dedup.py`, `test_cross_references.py`,
  `test_skills_manifest.py`, `test_skill_naming.py`, `test_project_bootstrap.py`
- `tests/evals/` — Eval-Suite (separat, braucht `ANTHROPIC_API_KEY`)

## Plugin-internal Hinweise

- `${CLAUDE_PLUGIN_ROOT}` ist die Plugin-Root für hooks/.mcp.json.
- Vault-MCP (#62) wird unter `mcp/academic-vault/` erwartet (neuer Sub-Tree).
- Beta-Header `anthropic-beta: files-api-2025-04-14` für #65 nötig.
