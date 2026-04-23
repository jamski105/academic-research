# Changelog

Alle bemerkenswerten Änderungen an diesem Plugin werden hier dokumentiert.

Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [5.0.1] — 2026-04-23

### Changed

- `scripts/setup.sh` zu einem vollständigen Installer ausgebaut. `browser-use` CLI wird jetzt automatisch via `uv` oder `pipx` installiert (falls eines der beiden verfügbar ist) statt nur geprüft zu werden. Zusätzliche Status-Checks für den globalen `browser-use`-Claude-Skill und das `document-skills`-Plugin mit konkreten Install-Hinweisen bei Fehlen.
- `commands/setup.md` ruft jetzt zentral `scripts/setup.sh` auf, statt die einzelnen Schritte inline zu duplizieren. Dokumentiert Ausgabe-Interpretation und Verhalten bei fehlenden Komponenten.

## [5.0.0] — 2026-04-23

> **⚠️ BREAKING:** User müssen Playwright-Konfiguration entfernen und `browser-use`-CLI plus `document-skills` Plugin installieren. Siehe README Prerequisites.

### Changed

- **BREAKING:** Browser-Automation migriert von Playwright-MCP zu `browser-use`-CLI/-Skill. `.mcp.json` enthält keinen Playwright-Eintrag mehr; `configure_permissions.py` setzt `Bash(browser-use:*)` statt `mcp__playwright__*`.
- **BREAKING:** Excel-Generierung delegiert an externes `document-skills:xlsx` Plugin statt eigener `scripts/excel.py`. README dokumentiert neuen Install-Schritt.
- `commands/search.md` Schritt 4: generischer browser-use-Workflow ersetzt Playwright-MCP-Aufrufe.
- `commands/score.md`: Ranking läuft jetzt über `relevance-scorer`-Agent plus inline berechnete Heuristiken, keine Python-Pipeline.
- `commands/excel.md`: komplett neu; ruft `document-skills:xlsx`-Skill auf, prüft vorab Verfügbarkeit.
- Browser-Guides (`config/browser_guides/*.md`): alle 9 Dateien neu, ~15 KB statt 40 KB — keine CSS-Selektoren oder JavaScript-Snippets mehr, reine Hinweise (URL, Auth, Anti-Scraping, datenbankspezifische Fallen).
- SessionStart-Hook: zweiter Hook warnt bei fehlendem `document-skills`-Plugin; Python-Env-Check prüft nicht mehr auf `openpyxl`.

### Removed

- **BREAKING:** `scripts/citations.py` gelöscht. Zitierstile generiert die `citation-extraction`-Skill jetzt inline.
- **BREAKING:** `scripts/style_analysis.py` gelöscht. Metriken berechnet die `style-evaluator`-Skill direkt aus dem Eingabetext.
- **BREAKING:** `scripts/ranking.py` gelöscht. 5D-Scoring-Funktionen sind in `commands/score.md` inline dokumentiert.
- **BREAKING:** `scripts/excel.py` gelöscht. Siehe `document-skills:xlsx`-Integration unter *Changed*.
- Playwright-MCP-Konfiguration, `.playwright-mcp/`-gitignore-Eintrag, Playwright-bezogene Bash-Permissions.
- `openpyxl` aus `scripts/requirements.txt`.
- Tests `tests/test_excel.py`, `tests/test_ranking.py`, `tests/test_style_analysis.py` (Tests der gelöschten Skripte).

### Migration

1. Alte Playwright-Permissions aus `~/.claude/settings.local.json` entfernen oder `/academic-research:setup` erneut ausführen (überschreibt die Liste).
2. `browser-use`-CLI installieren: `uv tool install browser-use` oder `pipx install browser-use`, anschließend `browser-use doctor`.
3. `document-skills` Plugin installieren: `/plugin install document-skills@anthropic-agent-skills`.
4. Alten Playwright-Cache entfernen (optional): `rm -rf ~/.playwright-mcp/` und `rm -rf ~/Library/Caches/ms-playwright/` (auf macOS).
5. Venv neu aufbauen, um `openpyxl` zu entsorgen: `rm -rf ~/.academic-research/venv && /academic-research:setup`.

## [4.0.1] — 2026-04-23

### Fixed

- Defekte Template-Pfade in drei Skills. `advisor`, `methodology-advisor` und `submission-checker` verwiesen auf `${CLAUDE_PLUGIN_ROOT}/templates/...`, die referenzierten Dateien liegen jedoch skill-lokal. Die Skills brachen zur Laufzeit bei Exposé-Generierung, Methodenkatalog-Lookup und FH-Requirements-Check (#12, #13, #14).
- Offene Agent-Permissions in `commands/search.md`. `allowed-tools: Agent` ließ Aufruf beliebiger Subagenten zu — Privilege-Eskalations-Risiko. Jetzt eingeschränkt auf `Agent(query-generator, relevance-scorer, quote-extractor)` (#15).
- Agent-Frontmatter normalisiert. Alle drei Agenten hatten `tools: ""` (mehrdeutiger Leerstring) und einzeilige Descriptions ohne `<example>`-Blöcke. `tools`-Feld entfernt bzw. als Array gesetzt, Descriptions um je zwei `<example>`-Blöcke ergänzt (#16, #17).

### Changed

- `quote-extractor.maxTurns` von 20 auf 5 reduziert. Extraktion ist near-single-shot; 20 war Overkill (#18).
- `relevance-scorer.maxTurns` von 15 auf 3 reduziert. Ein Batch von 10 Papern = 1 Turn, 2 Puffer für Iteration (#18).

## [4.0.0] — Vor 2026-04-23

Erstes getracktes Release. Siehe Git-Historie für frühere Änderungen.
