# Changelog

Alle bemerkenswerten Änderungen an diesem Plugin werden hier dokumentiert.

Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [5.1.0] — 2026-04-23

### Added

- **Anti-Fabrikations-Klauseln** in allen 13 Skills (Block B). Skill-spezifische FH-Leibniz-Konsequenzen (Plagiatsbefund, Note 5 für Forschungsdesign, Täuschungsversuch nach Prüfungsordnung, nicht-abgabefähige Arbeit, nachträgliche Überarbeitung nach Abgabe, …) mit Cookbook-Stil (Begründung + Handlung, kein ALLCAPS-NEVER).
- **Memory-Precondition-Checks** in 12 Skills (Block E, außer `academic-context` selbst). Harter Abbruch, wenn `academic_context.md`/`literature_state.md` fehlt und der User den `academic-context`-Trigger ablehnt — mit skill-spezifischer Abbruch-Begründung.
- **Few-Shot-Paare (Gut/Schlecht mit Grund-Annotation)** in 4 Skills (Block D): `research-question-refiner` (4 Template-Typen), `abstract-generator` (4 IMRaD-Abschnitte), `title-generator` (3 Stile), `chapter-writer` (3 Kapiteltypen).
- **Skill-Abgrenzung** zwischen `literature-gap-analysis` und `source-quality-audit` (Block F). Jeweils ein `## Abgrenzung`-Abschnitt mit Kriterien-Liste und Delegations-Hinweis.
- Smoke-Test `tests/test_skills_manifest.py` — 51 parametrisierte Tests für Frontmatter-Validität, Sektions-Vollständigkeit und Umlaut-Paare.

### Changed

- **Sprache einheitlich Deutsch** in allen 13 Skills, 5 Commands, 3 Agents (Block A). Englisch bleibt nur in Code, Pfaden, JSON-Keys, Frontmatter-Keys, Code-Kommentaren und Shell-Kommandos. Englische Fachbegriffe wie Abstract, Peer-Review, IMRaD, Cluster bleiben erhalten.
- **Numerische Schwellen** in 5 Skills (Block C):
  - `advisor`: 7-Kriterien-PASS/FAIL-Checkliste (Forschungsfrage ≤ 25 Wörter, ≥ 3 Kapitel, ≥ 15 Quellen, …)
  - `methodology-advisor`: 4-Dimensionen-Scoring-Matrix (Skala 1–5) plus Empfehlungs-Schwellen (≥ 16 / 10–15 / < 10)
  - `submission-checker`: 8-Punkte-FH-Leibniz-Formalia-Check (Seitenränder 2,5 cm, Schrift Times 12 pt/Arial 11 pt, Zeilenabstand 1,5, …)
  - `style-evaluator`: 5-Metriken-Fallback-Rubrik (Satzlänge 15–25 Wörter, Passiv < 30 %, Nominalstil < 40 %, Füllwörter < 5 %, 0 Code-Switches)
  - `literature-gap-analysis`: Coverage ≥ 80 %, Diversity ≥ 5 Autor*innen-Gruppen, Recency ≥ 40 % ab 2020
- **Umlaut-Varianten** in allen 13 Skill-Trigger-Descriptions (Block G): `"Quellenqualität / Quellenqualitaet"`, `"prüfen / pruefen"`, `"Titelvorschläge / Titelvorschlaege"` etc.

### Fixed

- `agents/quote-extractor.md`: robusterer Pre-Execution-Guard (PDF-Wortzahl ≥ 500, Fehler-Marker-Check `[FEHLER]`/`extraction failed`/`<scanned image>`, Mindest-Seitenzahl ≥ 2) (Block H.2).
- `agents/query-generator.md`: CS-Disambiguierung mit 4 Fachkontext-Varianten (Informatik / Medizin / Recht / Biochemie), Code-Switch aus den Anweisungen entfernt (Block H.3).
- `skills/abstract-generator/SKILL.md`: Default-String `"Preliminary, pending validation"` → `"Vorläufig, Validierung ausstehend"` (Block H.6).

### Migration

Keine Migration nötig. Skills laufen sofort nach Update weiter, werden nur präziser und deutscher. `academic-context`-Skill bleibt rückwärtskompatibel mit älterem Memory-Format.

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
