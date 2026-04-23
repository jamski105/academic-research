# Epic 2 — Architektur-Bereinigung

**Datum:** 2026-04-23
**Status:** FINALISIERT (Brainstorm-Ergebnis nach E1-Merge)
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e2-architecture`
**Ziel-Version:** v5.0.0 (Major, Breaking Changes)
**Abhängigkeit:** E1 gemerged (v4.0.1)

## Zweck

Strukturelle Bereinigung der Datei-Landschaft:
- Drei redundante Python-Skripte löschen (citations, style_analysis, ranking), zu denen Skills/Agents existieren.
- `excel.py` ersetzen durch den Claude-eigenen `document-skills:xlsx`-Skill.
- `Playwright-MCP` durch den globalen `browser-use`-Skill (CLI-basiert) ersetzen.
- `pdf.py` bleibt bestehen: Download-Fallback, PyPDF2-Textextraktion, TF-IDF-Index sind Infrastruktur, kein LLM-Ersatz sinnvoll.

Erzeugt das erste Breaking-Change-Release (`v5.0.0`).

## Scope-Übersicht

```
Block A — Skripte löschen (3 Dateien)
Block B — Playwright → browser-use (11 Touchpoints)
Block C — excel.py → document-skills:xlsx (inkl. SessionStart-Check)
Block D — Release (Version, CHANGELOG, Tag)
```

## Block A — Redundante Python-Skripte löschen

### A.1 Zu löschen

| Skript | Größe | Ersatz-Mechanismus |
|--------|-------|--------------------|
| `scripts/citations.py` | 20 KB | Skill `citation-extraction` + Agent `quote-extractor` |
| `scripts/style_analysis.py` | 17 KB | Skill `style-evaluator` |
| `scripts/ranking.py` | 12 KB | Agent `relevance-scorer` + Skill `source-quality-audit` |

Zugehörige Tests ebenfalls löschen:
- `tests/test_excel.py`
- `tests/test_ranking.py`
- `tests/test_style_analysis.py`

### A.2 Zu behalten (explizit)

| Skript | Begründung |
|--------|------------|
| `scripts/search.py` | Multi-API-Suche (CrossRef/OpenAlex/Semantic Scholar/arXiv/BASE/EconBiz/EconStor) — kein Agent-Ersatz |
| `scripts/dedup.py` | Deterministisches String-Matching, kein LLM-Bedarf |
| `scripts/pdf.py` | 5-Tier-Download-Fallback (OpenAlex → Unpaywall → arXiv → DOI → URL), PyPDF2-Parsing, TF-IDF-Index — pures IO und Mathematik |
| `scripts/text_utils.py` | Helper für verbleibende Skripte |
| `scripts/configure_permissions.py` | Setup-Utility (wird in Block B angepasst) |

### A.3 Folge-Änderungen in Commands und Skills

**Commands (grep-bestätigt):**
- `commands/score.md:48` — Python-Aufruf `ranking.py` durch `relevance-scorer`-Agent-Invokation ersetzen
- `commands/search.md:86` — denselben `ranking.py`-Aufruf streichen (Agent-Invokation läuft bereits in Step 7 des Commands)
- `commands/excel.md` — komplett neu, siehe Block C

**Skills (grep-bestätigt):**
- `skills/citation-extraction/SKILL.md:8,87,102,108,114,149` — alle `citations.py`-Verweise auf Agent/Skill-Flow umstellen; keine Python-Pipeline mehr
- `skills/source-quality-audit/SKILL.md:24,64,168` — `score_authority()`/`score_recency()`-Logik direkt im Skill-Prompt beschreiben
- `skills/chapter-writer/SKILL.md:77` — `citations.py`-Referenz durch Agent-Output-Verweis ersetzen
- `skills/style-evaluator/SKILL.md:25,96,140` — `style_analysis.py`-Referenzen streichen; Metriken direkt im Skill-Prompt spezifizieren

**README:**
- `README.md:271,274-276,366-367` — Skripte-Tabelle und Dateibaum auf verbleibende Dateien reduzieren

## Block B — Playwright-MCP → `browser-use`-Skill

### B.1 Kontext

`browser-use` liegt unter `~/.claude/skills/browser-use/` als globaler User-Skill (nicht Bestandteil des Plugins, daher nur README-Hinweis auf CLI-Install). CLI-API ist index-basiert (`state` liefert nummerierte Elemente, keine CSS-Selektoren). Dadurch werden die aktuellen Playwright-Guides (Selektoren + JS-Extraktion) vollständig obsolet.

### B.2 Zu entfernen

| Datei | Änderung |
|-------|----------|
| `.mcp.json` | Komplett ersetzen durch `{"mcpServers": {}}` oder Datei löschen |
| `scripts/configure_permissions.py:22-36` | 14 `mcp__playwright__*`-Permissions und `npx playwright`/`@playwright/mcp`-Bash-Regeln entfernen |
| `scripts/setup.sh:26-34` | Playwright-Install-Block (npx playwright install chromium) entfernen |
| `commands/setup.md` | Playwright-Install-Schritt streichen |
| `settings.json:12` | `"Bash(cp ~/.playwright-mcp/* *)"` raus |
| `.gitignore:27` | `.playwright-mcp/`-Eintrag raus |
| `README.md` | Alle Playwright-Erwähnungen umschreiben oder löschen (ca. 6 Stellen, per `rg -i "playwright" README.md`) |

### B.3 Zu ergänzen

| Datei | Änderung |
|-------|----------|
| `scripts/configure_permissions.py` | Neue Permission: `Bash(browser-use:*)` und `Bash(browser-use *)` (Skill-Rechte) |
| `commands/setup.md` | Schritt: _"Prüfe, ob `browser-use` CLI installiert ist (`browser-use doctor`) und ob der globale `browser-use`-Skill verfügbar ist (`~/.claude/skills/browser-use/SKILL.md`)"_ |
| `README.md` (Prerequisites) | `uv tool install browser-use` oder `pipx install browser-use` dokumentieren; Verweis auf https://github.com/browser-use/browser-use; Node.js-Prereq entfernen, falls sonst nicht mehr gebraucht |

### B.4 `commands/search.md` — Schritt 4 neu

Der heutige Text _"For browser modules (…), use Playwright MCP directly. Read the corresponding browser guide"_ wird ersetzt durch:

> **Schritt 4 (Browser-Search, nur im `standard`/`deep`-Modus, falls `--no-browser` nicht gesetzt):**
>
> Für jedes Browser-Modul in fester Reihenfolge (`google_scholar` → `springer` → `oecd` → `repec` → `opac` → `ebscohost` → `proquest`):
>
> 1. Guide aus `${CLAUDE_PLUGIN_ROOT}/config/browser_guides/<modul>.md` lesen (URL, Auth-Art, Anti-Scraping-Hinweise)
> 2. Bei Auth-Modulen (`ebscohost`, `proquest`, `opac`): zuerst `han_login.md`-Flow durchlaufen
> 3. Mit dem globalen `browser-use`-Skill:
>    - `browser-use open <URL>` — Seite laden
>    - `browser-use state` — klickbare Elemente mit Index abrufen
>    - Query-Feld per Index identifizieren und ausfüllen: `browser-use input <idx> "<QUERY>"`
>    - Suchen auslösen (Enter oder Submit-Button) und `browser-use state` für Ergebnisse
>    - Bei Bedarf paginieren (max. 2 Seiten pro Modul)
>    - Ergebnisse in das `api_results.json`-Schema normalisieren und anhängen
> 4. Bei Fehler (CAPTCHA, Rate-Limit, fehlgeschlagenem Login): `browser-use screenshot`, User informieren, Partial Results behalten

### B.5 Browser-Guides-Umbau

**Strategie: radikale Verschlankung in einem Commit** (alle 9 Guides neu).

**Neues Template pro Guide:**

```markdown
# <Datenbank> — Navigation Guide

**URL:** https://...
**Auth:** keine / HAN-Login (siehe han_login.md) / eigene Credentials in ~/.academic-research/credentials.json
**Max. Ergebnisse:** <N>
**Anti-Scraping:** <Warnung falls relevant — z. B. Scholar CAPTCHA-Risiko, Rate Limits>

## Hinweise

- Datenbankspezifische Besonderheiten (Advanced-Search-Pfad, Sprach-Toggle, Filter-Setup)
- Was `browser-use` nicht aus der Seite selbst erraten kann
- Bekannte Fallen (z. B. nicht ersten Link in Scholar-Ergebniszeile klicken, da Speichern/Zitieren-Buttons mitgezählt werden)
```

**Zielgrößen:**
- No-Auth-Guides (scholar, destatis, oecd, springer, repec): 15-30 Zeilen
- Auth-Guides (ebscohost, proquest, opac): 40-60 Zeilen
- `han_login.md` bleibt als geteilte Login-Referenz, ebenfalls schlank neu (Navigationsflow + Credential-Quelle)

**Alle Playwright-Artefakte raus:** CSS-Selektoren, `browser_snapshot`/`browser_evaluate`/`browser_navigate`/`browser_click`/`browser_type`/`browser_press_key`/`browser_wait_for`, JavaScript-Extraktionssnippets.

## Block C — `document-skills:xlsx`-Integration

### C.1 Löschungen und Umschreibung

1. `scripts/excel.py` löschen (14.5 KB).
2. `requirements.txt` — `openpyxl>=3.1.0` entfernen (wird vom Claude-Skill selbst mitgebracht).
3. `commands/excel.md` komplett neu:
   - **Input:** Pfad zu `.xlsx`/`.csv`/`.tsv` ODER strukturierte Paper-Daten aus Session-Dir (`ranked.json`, `papers.json`).
   - **Flow:** Claude wendet den `document-skills:xlsx`-Skill auf die Eingabe an. Keine Python-Pipeline.
   - **Output:** Excel-Datei im Session-Dir, Dateiname aus Argument oder Default.
   - **Fallback:** Wenn xlsx-Skill nicht verfügbar → klare Fehlermeldung mit Install-Befehl abbrechen.

### C.2 SessionStart-Hook-Erweiterung

`hooks/hooks.json` erweitern. Bestehender Python-Venv-Check bleibt, ein zweiter Hook für xlsx-Verfügbarkeit wird ergänzt:

```json
{
  "type": "command",
  "command": "bash -c '[ -d \"$HOME/.claude/plugins/cache/anthropic-agent-skills/document-skills\" ] || echo \"⚠️  academic-research: document-skills nicht installiert — /academic-research:excel benötigt: /plugin install document-skills@anthropic-agent-skills\"'",
  "timeout": 5
}
```

Bewusst **stumm bei Erfolg**, um Noise zu vermeiden. Nur Warnung bei Fehlen.

### C.3 `/setup`-Command

`commands/setup.md` ergänzen um denselben Pfad-Check plus konkretem Install-Befehl in der Ausgabe (nicht nur Warnung).

### C.4 README

Neuer Prerequisites-Abschnitt:

```markdown
## Voraussetzungen

- Python 3.10+
- `browser-use`-CLI (`uv tool install browser-use`) + globaler Skill unter `~/.claude/skills/browser-use/`
- `document-skills` Plugin (für `/academic-research:excel`):
  /plugin install document-skills@anthropic-agent-skills
```

## Block D — Release

### D.1 Version & Artefakte

- `.claude-plugin/plugin.json`: `4.0.1` → `5.0.0`
- `.claude-plugin/marketplace.json`: `4.0.1` → `5.0.0`
- `CHANGELOG.md`: neuer `## [5.0.0]`-Block, Keep-a-Changelog-Format, mit expliziter **BREAKING**-Kennzeichnung aller betroffenen Stellen
- Git-Tag `v5.0.0` erst nach Merge

### D.2 Umbrella- und Ticket-Updates

- Epic-Issue `#9` — Sub-Tickets `#19-#29` abhaken und schließen
- Umbrella `#7` — E2-Checkbox setzen, E3 als "bereit zum Kickoff" markieren

## Git-Plan — 11 Commits auf `refactor/e2-architecture`

| # | Commit | Inhalt |
|---|--------|--------|
| 1 | `chore(scripts): delete citations.py, style_analysis.py, ranking.py + tests` | 3 Skripte + 3 Tests, kein Code-Call mehr |
| 2 | `refactor(commands): wire score.md and search.md to relevance-scorer agent` | `commands/score.md`, `commands/search.md:86` |
| 3 | `refactor(skills): remove deleted-script references` | citation-extraction, source-quality-audit, chapter-writer, style-evaluator SKILL.md |
| 4 | `refactor: remove Playwright MCP, add browser-use permissions` | .mcp.json, configure_permissions.py, settings.json, setup.sh, .gitignore, commands/setup.md |
| 5 | `refactor(search): migrate commands/search.md Step 4 to browser-use` | `commands/search.md` Browser-Search-Block |
| 6 | `refactor(browser-guides): rewrite all 9 guides for browser-use` | alle 9 Dateien in `config/browser_guides/` |
| 7 | `refactor(excel): replace scripts/excel.py with document-skills:xlsx` | `scripts/excel.py`-Löschung, `commands/excel.md`-Neufassung, requirements.txt schlanker |
| 8 | `feat(hooks): warn on missing document-skills in SessionStart` | `hooks/hooks.json` |
| 9 | `docs(readme): document browser-use + document-skills prerequisites` | `README.md`-Prerequisites, Skripte-Tabelle, Dateibaum |
| 10 | `docs: add v5.0.0 changelog` | `CHANGELOG.md` |
| 11 | `chore(release): v5.0.0` | `plugin.json`, `marketplace.json` |

## Verifikation (vor Merge)

- `rg "citations\.py|style_analysis\.py|ranking\.py|excel\.py"` — nur Treffer in `docs/superpowers/specs/` und `CHANGELOG.md` zulässig
- `rg -i "playwright|mcp__playwright"` — nur Treffer in `docs/superpowers/specs/` und `CHANGELOG.md`
- `rg "browser_snapshot|browser_evaluate|browser_navigate|browser_click|browser_type|browser_press_key|browser_wait_for"` — 0 Treffer
- `rg "browser-use"` — Treffer in `commands/search.md`, `commands/setup.md`, `README.md`, `configure_permissions.py`, allen 9 Browser-Guides, `hooks/hooks.json` (falls referenziert), `CHANGELOG.md`
- `/setup`-Command manuell durchlaufen, SessionStart-Hook-Warnung prüfen (mit und ohne installiertes document-skills)
- `plugin-validator`-Agent auf den Branch ansetzen
- Keine Tests schlagen fehl (die gelöschten Tests sind weg, die verbleibenden müssen weiter grün sein)

## Rollback-Strategie

- Major-Release → bei Problemen im Release pinnen User auf `v4.0.1`
- Pre-Merge: `git revert` des PR-Merges oder Branch verwerfen

## Out-of-Scope

- Inhaltliche Überarbeitung der Prompts → **E3**
- Citations-API, Evals, Prompt Caching → **E4**
- Neue Commands oder Skills

## Entschieden im Brainstorm (Referenz)

1. **pdf.py bleibt** — 5-Tier-Download-Fallback, PyPDF2, TF-IDF sind Infrastruktur, kein LLM-Ersatz sinnvoll.
2. **Ein generischer browser-use-Prompt in `search.md`** — Guides schrumpfen auf URL+Auth+Warnungen, keine Selektoren.
3. **SessionStart-Pfad-Check auf `document-skills`** — stumm bei Erfolg, Warnung bei Fehlen; zusätzlich im `/setup`.
4. **Alle 9 Browser-Guides in einem Commit neu** — einheitlicher Stil, YAGNI-radikale Verschlankung.
