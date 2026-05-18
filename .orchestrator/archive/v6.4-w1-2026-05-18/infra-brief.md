# infra-brief — v6.4

## Stack
- Python 3.10+ (kein zentrales pyproject.toml; deps via `scripts/requirements.txt`)
- pytest (50 Tests)
- MCP-Server: `mcp/academic_vault/` (SQLite + Files-API)
- Hooks: Node (`*.mjs`) — verbatim-guard, hooks.json
- Skills: Markdown (SKILL.md) + ggf. Python-Scripts/References
- Agents: Markdown (`agents/<name>.md`) — Sonnet-basiert

## Test / Lint / Typecheck
- **Test:** `pytest` (Repo-Root) oder `pytest tests/test_<name>.py` (Einzeltest)
  - In Worktrees: kein zentrales venv; pytest-deps müssen vorhanden sein
  - Python-deps via `pip install -r scripts/requirements.txt`
- **Lint:** keine globale Config; ad-hoc `python -m py_compile`
- **Typecheck:** keine zentrale mypy-Config

## Branching
- **Base:** `main`
- **Pattern:** `feat/v6.4-<chunk_id>-<slug>`
- **State-Sync:** `mmp/state/v6.4` (Branch via state-sync.sh)
- **Archive:** `mmp/archive/v6.4-w1-<date>`

## Conventions (aus Memory + Repo-Praxis)
1. **Plugin-Design:** Agenten/Skills vor Python-Skripten bevorzugen. Wenn ein Agent das auch kann, kein Script schreiben.
2. **Excel:** `document-skills:xlsx` Skill nutzen, nicht openpyxl direkt.
3. **Browser:** `browser-use` Skill, nicht Playwright-MCP.
4. **Sprache:** Deutsch in User-facing-Text (Skills/Commands/Hooks); Code/Identifier in EN.
5. **Verbatim-Garantie:** Quotes/Figures via Vault-MCP, nicht via Modell-Reproduktion (verbatim-guard.mjs erzwingt das).
6. **Squash-Merge** auf main mit `gh pr merge --squash --delete-branch`.
7. **Keine --force-Pushes / --no-verify** ohne explizite User-Bestätigung.

## CI workflow names
- (zu prüfen: `.github/workflows/` existiert nicht im Hauptbranch — kein CI heute)
- Tests laufen lokal vor Merge

## Sicherheitshinweise
- **API-Keys:** Anthropic-Key + ggf. Zotero-Key in 0600-Config (`~/.academic-research/config.yaml`); nie ins Repo committen
- **Vault-DB:** `~/.academic-research/projects/<slug>/vault.db` (außerhalb Repo)
- **PDFs:** `~/.academic-research/pdfs/` (außerhalb Repo)

## Bash 5 erforderlich
- mmp-lock-scripts nutzen Variable-FD-Syntax (`{var}<>file`), die bash 3.2 (macOS default) NICHT unterstützt
- Verwende `/opt/homebrew/bin/bash` für Lock-Scripts

## Bekannte Quirks (aus v6.3)
- L1-Tests dürfen niemals Output-Files im Repo-Root ablegen — immer `tmp_path` oder explizit `--output-dir`
- skill_sizes.json wird bei jedem Skill-Add aktualisiert — Cross-Chunk-Konflikte handhaben durch sequentielles Merging oder Pre-Reservierung
