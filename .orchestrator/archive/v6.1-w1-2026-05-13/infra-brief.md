# infra-brief — academic-research

## Stack
- **Sprache:** Python 3.x (kein zentrales `pyproject.toml`; `requirements.txt` in `mcp/academic_vault/` und `scripts/`)
- **Artefakt:** Claude-Code-Plugin (Skills + Agents + Hooks + Commands + MCP-Server)
- **Tests:** `pytest` (15 Suiten unter `tests/`, inkl. `evals/`-Suite)
- **Lint/Typecheck:** keine projektweite Konfig erkennbar (kein `ruff.toml`, `mypy.ini`, `.flake8`); Code-Style folgt PEP 8 implizit

## Exakte Commands
- **Tests (alle):** `pytest tests/`
- **Eval-Suite:** `pytest tests/evals/`
- **Lint:** (n/a — kein konfigurierter Linter; L1-Agents prüfen Stil per Code-Review)
- **Typecheck:** (n/a)

## Branching
- **Base:** `main` (siehe `.orchestrator/config.yaml`)
- **Pattern:** `feat/{milestone}-{chunk_id}` z. B. `feat/v6.1-F2.1-book-handler`
- **PR-Modus:** Initial Draft (`pr.draft_initially: true`), Title-Pattern `"{milestone}: {chunk_summary}"`

## CI
- **Provider:** GitHub Actions (laut Config), aber **kein** `.github/workflows/` lokal vorhanden
- **Beobachtet:** `Copilot code review` läuft auf jedem PR (extern verdrahtet); Tests via lokalem `pytest`
- **Poll-Timeout:** 30 min (config)
- **Konsequenz:** CI-Pass-Gate stützt sich auf Copilot-Review + lokalen pytest-Run im L1-Worktree; keine GH-Actions-Builds zu erwarten

## Konventionen (relevante Auszüge)
- **Sprache:** Deutsch in Doku, Kommit-Messages, User-Facing Texten. Technische Bezeichner bleiben in Originalform (siehe globale `CLAUDE.md`).
- **Vault-Hook:** PreToolUse-Verbatim-Validation aktiv (`hooks/`) — beim Editieren von Skills, die Vault nutzen, Verbatim-Constraints respektieren.
- **Plugin-Design:** Agenten/Skills vor Python-Skripten bevorzugen (siehe `~/.claude/projects/.../memory/feedback_plugin_design.md`).
- **Excel:** `document-skills:xlsx` verwenden, nicht Custom-Skripte.
- **Browser-Automation:** `browser-use` CLI statt Playwright-MCP.

## Repo-Layout (relevant)
```
agents/       # LLM-Subagents (Markdown-Definitionen)
skills/       # Selbstaktivierende Skills (frontmatter + body)
commands/     # Slash-Commands
hooks/        # PreToolUse / PostToolUse hooks
mcp/          # MCP-Server (academic_vault)
scripts/      # Python-Helper
tests/        # pytest-Suite
evals/        # eval-Cases (frontmatter-JSON pro Skill)
docs/         # AUDIT-v6-roadmap.md, AUDIT-v6-vault.md, evals/
specs/        # Plan-Spezifikationen
```

## CI-Workflow-Namen
- `Copilot code review` (einziger erkennbarer Check via `gh run list`)

## Sicherheits-Notiz
- Issue #73 ist `security`-gelabelt — Seitenmapping-Sanity-Check verhindert falsche Seitenangaben in Zitaten (Halluzinations-Risiko).
