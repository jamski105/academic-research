# infra-brief — academic-research (v6.3 Wave 1)

## Stack
- **Sprache:** Python 3.x (`requirements.txt` in `mcp/academic_vault/` und `scripts/`; kein zentrales `pyproject.toml`)
- **Artefakt:** Claude-Code-Plugin (Skills + Agents + Hooks + Commands + MCP-Server) — `.claude-plugin/plugin.json`, Plugin-Name `academic-research`
- **Tests:** `pytest` (~30+ Suiten unter `tests/`, inkl. `tests/evals/`)
- **Lint/Typecheck:** keine projektweite Konfig erkennbar — Code-Style folgt PEP 8 implizit

## Exakte Commands
- **Tests (alle):** `~/.academic-research/venv/bin/python -m pytest tests/ -v`
- **Eval-Suite:** `~/.academic-research/venv/bin/python -m pytest tests/evals/ -v` (braucht `ANTHROPIC_API_KEY`)
- **Quick-Test (CI-Gate Stand-in):** `pytest tests/` (System-Python falls Venv fehlt; v6.1-Lessons zeigen `/opt/homebrew/opt/python@3.14` als Default — nur PyPDF2 installiert, nicht `pypdf`)
- **Lint:** (n/a — kein konfigurierter Linter; L1-Agents prüfen Stil per Code-Review)
- **Typecheck:** (n/a)

## Branching
- **Base:** `main`
- **Pattern:** `feat/{milestone}-{chunk_id}` — für v6.3 also `feat/v6.3-A-…`, `feat/v6.3-B-…`
- **PR-Modus:** Initial Draft (`pr.draft_initially: true`), Title-Pattern `"{milestone}: {chunk_summary}"`

## CI
- **Provider:** GitHub Actions (laut Config), aber **kein** `.github/workflows/` lokal vorhanden
- **Beobachtet:** `Copilot code review` läuft auf jedem PR (extern verdrahtet); Tests via lokalem `pytest` im L1-Worktree
- **Poll-Timeout:** 30 min (config)
- **Konsequenz:** CI-Pass-Gate stützt sich auf Copilot-Review + lokalen `pytest`-Run im L1-Worktree

## Konventionen (relevante Auszüge)
- **Sprache:** Deutsch in Doku, Commit-Messages, User-Facing Texten. Technische Bezeichner bleiben in Originalform.
- **Plugin-Design:** Agenten/Skills vor Python-Skripten bevorzugen (User-Memory `feedback_plugin_design.md`).
- **Excel:** `document-skills:xlsx`-Skill nutzen, nicht Custom-Skripte (User-Memory `feedback_excel_skill.md`).
- **Browser-Automation:** `browser-use`-Skill statt Playwright (User-Memory `feedback_browser_use.md`).
- **Vendoring** von Skills statt MCP-Calls, wo möglich.

## Repo-Layout (relevant für v6.3)
```
agents/       # LLM-Subagents (Markdown-Definitionen)
skills/       # Selbstaktivierende Skills — neu für v6.3: skills/zotero-import/, skills/notebook-bundle/
commands/     # Slash-Commands
hooks/        # PreToolUse / PostToolUse hooks
mcp/          # MCP-Server (academic_vault) — Vault-API stabil seit v5.x
scripts/      # Python-Helper — requirements.txt erweitern um pyzotero (optional) und pypdf/PyPDF2-Concat-Helper
tests/        # pytest-Suite — neu: test_zotero_import.py, test_notebook_bundle.py
docs/         # AUDIT-v6-roadmap.md, AUDIT-v6-vault.md
specs/v6.3/   # Plan-Spezifikationen für v6.3-Chunks (neu anlegen)
```

## CI-Workflow-Namen
- `Copilot code review` (einziger erkennbarer Check)

## Sicherheits-Notizen (v6.3)
- **Ticket #88 (Zotero):** API-Keys sind Credentials. Speicherung in `~/.academic-research/config.yaml`, **niemals** in Vault-DB, Logs oder PR-Diffs. Bei Test-Fixtures Mock-Keys verwenden (`zotero_test_key`).
- **Allowlist für Zotero-API:** Zotero-Web-API-Host (`api.zotero.org`) — kein generischer HTTP-Client. pyzotero kümmert sich.
- **NotebookLM-Bundle:** Bundle-PDF enthält **User-Daten** (alle ausgewählten Paper). Speicherort `<projekt>/notebook-bundle-<ts>.pdf` lokal — kein automatischer Upload, manueller User-Flow.

## v6.2-Lessons (relevant für v6.3)
- Wo Vault-API genutzt wird: `add_paper(...)` + `ensure_file(...)` sind synchron, geben aussagekräftige Fehler bei Duplikaten
- pytest fail-fast: bestehende `test_token_reduction[chapter-writer]` ist known-failure und darf nicht blocken
- Cross-Chunk-Mocking-Pattern: Vault-API in Tests mocken statt echte DB anlegen
- Code-Review-Gate: ≥80 Findings blockieren — L1 soll proaktiv Validierung (Input-Sanity, Error-Messages) einbauen
- Polish-Agent (`code-simplifier`) ändert kein Verhalten — file-by-file revert bei Test-Bruch
