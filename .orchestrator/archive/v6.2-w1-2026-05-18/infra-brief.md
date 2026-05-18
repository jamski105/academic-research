# infra-brief — academic-research

## Stack
- **Sprache:** Python 3.x (`requirements.txt` in `mcp/academic_vault/` und `scripts/`; kein zentrales `pyproject.toml`)
- **Artefakt:** Claude-Code-Plugin (Skills + Agents + Hooks + Commands + MCP-Server) — `.claude-plugin/plugin.json`, Plugin-Name `academic-research`
- **Tests:** `pytest` (~20 Suiten unter `tests/`, inkl. `tests/evals/`)
- **Lint/Typecheck:** keine projektweite Konfig erkennbar (kein `ruff.toml`, `mypy.ini`, `.flake8`); Code-Style folgt PEP 8 implizit

## Exakte Commands
- **Tests (alle):** `~/.academic-research/venv/bin/python -m pytest tests/ -v`
- **Eval-Suite:** `~/.academic-research/venv/bin/python -m pytest tests/evals/ -v` (braucht `ANTHROPIC_API_KEY`)
- **Quick-Test (CI-Gate Stand-in):** `pytest tests/` (System-Python falls Venv fehlt; v6.1-Lessons zeigen `/opt/homebrew/opt/python@3.14` als Default — nur PyPDF2 installiert, nicht `pypdf`)
- **Lint:** (n/a — kein konfigurierter Linter; L1-Agents prüfen Stil per Code-Review)
- **Typecheck:** (n/a)

## Branching
- **Base:** `main`
- **Pattern:** `feat/{milestone}-{chunk_id}` — für v6.2 also `feat/v6.2-A-…`, `feat/v6.2-B-…`, etc.
- **PR-Modus:** Initial Draft (`pr.draft_initially: true`), Title-Pattern `"{milestone}: {chunk_summary}"`

## CI
- **Provider:** GitHub Actions (laut Config), aber **kein** `.github/workflows/` lokal vorhanden
- **Beobachtet:** `Copilot code review` läuft auf jedem PR (extern verdrahtet); Tests via lokalem `pytest` im L1-Worktree
- **Poll-Timeout:** 30 min (config)
- **Konsequenz:** CI-Pass-Gate stützt sich auf Copilot-Review + lokalen `pytest`-Run im L1-Worktree; keine GH-Actions-Builds zu erwarten

## Konventionen (relevante Auszüge)
- **Sprache:** Deutsch in Doku, Commit-Messages, User-Facing Texten. Technische Bezeichner bleiben in Originalform (siehe globale `~/.claude/CLAUDE.md`).
- **Vault-Hook:** PreToolUse-Verbatim-Validation aktiv (`hooks/`) — beim Editieren von Skills, die Vault nutzen, Verbatim-Constraints respektieren.
- **Plugin-Design:** Agenten/Skills vor Python-Skripten bevorzugen (User-Memory `feedback_plugin_design.md`).
- **Excel:** `document-skills:xlsx`-Skill nutzen, nicht Custom-Skripte (User-Memory `feedback_excel_skill.md`).
- **Browser-Automation:** `browser-use`-Skill statt Playwright (User-Memory `feedback_browser_use.md`) — **kritisch für v6.2 F16-Tickets**.
- **Vendoring** von Skills statt MCP-Calls, wo möglich.

## Repo-Layout (relevant für v6.2)
```
agents/       # LLM-Subagents (Markdown-Definitionen) — neu für F16: book-fetcher, tib-fetcher, oapen-fetcher, doabooks-fetcher, kvk-fetcher, springer-book, degruyter, nationallizenzen, ebook-central, auth-helper, generic-fetcher
skills/       # Selbstaktivierende Skills
commands/     # Slash-Commands — neu für F16/F5: commands/fetch.md, commands/pickup.md
hooks/        # PreToolUse / PostToolUse hooks
mcp/          # MCP-Server (academic_vault)
scripts/      # Python-Helper — F6 erweitert scripts/pdf.py um 3 Tier-Funktionen
tests/        # pytest-Suite
tests/evals/  # eval-Cases (frontmatter-JSON pro Skill)
docs/         # AUDIT-v6-roadmap.md, AUDIT-v6-vault.md, evals/ — Browser-Guides #87 landen unter docs/
specs/v6.2/   # Plan-Spezifikationen für v6.2-Chunks (neu anlegen)
```

## CI-Workflow-Namen
- `Copilot code review` (einziger erkennbarer Check)

## Sicherheits-Notizen (v6.2)
- Issue **#83** ist `security`-gelabelt — `auth-helper` muss Credentials niemals in Logs, Vault oder PR-Diffs landen lassen; sensitive Speicherung nur in OS-Keychain/Profil-Datei mit `0600`-Perms.
- Browser-Subagenten (F16) führen externe HTTP-Requests aus — Plan-Gate prüft Sandboxing (no shell-exec, no arbitrary FS-writes außerhalb Vault).
- **Allowlist statt Blocklist:** Per-Uni-Profile (#86) definieren erlaubte Auth-Hosts pro Hochschule.

## v6.1-Lessons (aus `.orchestrator/lessons.jsonl`, relevant für Python-Arbeit)
- `b""`-Strings dürfen keine non-ASCII-Zeichen enthalten → XML-Fixtures als `.encode('utf-8')` schreiben
- PyPDF2 Outline-Items: `get_destination_page_number()` mit `hasattr(item,'page')`-Fallback
- `subprocess.which` existiert nicht → `shutil.which`
- pytest läuft auf `/opt/homebrew/opt/python@3.14` mit **PyPDF2** (nicht pypdf) → `_get_pdf_reader()`-Fallback-Pattern verwenden
