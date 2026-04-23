# Epic 2 — Architektur-Bereinigung

**Datum:** 2026-04-23
**Status:** DRAFT — zu finalisieren im E2-Kickoff-Brainstorm nach Abschluss E1
**Parent:** [Refactor Overview](2026-04-23-academic-research-refactor-overview.md)
**Branch:** `refactor/e2-architecture`
**Ziel-Version:** v5.0.0 (Major, Breaking Changes)
**Abhängigkeit:** E1 gemerged

## Zweck

Strukturelle Bereinigung der Datei-Landschaft: redundante Python-Skripte löschen, Playwright durch `browser-use` ersetzen, externes `document-skills:xlsx` einbinden. Erzeugt das erste Breaking-Change-Release (v5.0.0).

## In-Scope

### Block A — Redundante Python-Skripte löschen

Begründung laut User: Skills/Agents performen besser als heuristische Python-Skripte. Gilt, wenn Skill/Agent denselben Task abdeckt.

| Skript | Ersatz | Aktion |
|--------|--------|--------|
| `scripts/citations.py` (20 KB) | Skill `citation-extraction` + Agent `quote-extractor` | Löschen |
| `scripts/style_analysis.py` (17 KB) | Skill `style-evaluator` | Löschen |
| `scripts/ranking.py` (12 KB) | Agent `relevance-scorer` + Skill `source-quality-audit` | Löschen |
| `scripts/excel.py` (14.5 KB) | externer Skill `document-skills:xlsx` | Löschen (siehe Block C) |
| `scripts/pdf.py` (13.6 KB) | Agent `quote-extractor` via Read-Tool | **Prüfen**, dann löschen oder behalten |
| `scripts/search.py` (19.5 KB) | kein Ersatz (CrossRef/OpenAlex/arXiv-APIs) | Behalten |
| `scripts/dedup.py` (4.7 KB) | String-Matching-Utility, kein Agent-Case | Behalten |
| `scripts/text_utils.py` (2.9 KB) | Helper für verbleibende Skripte | Behalten |
| `scripts/configure_permissions.py` (2 KB) | Setup-Utility (wird in Block B angepasst) | Behalten |

**Folgen für Skills/Commands, die auf gelöschte Skripte verweisen:**
- SKILL.md-Referenzen entfernen, durch Skill/Agent-Nutzung ersetzen
- `commands/score.md`: Python-Aufruf durch Agent-Invokation ersetzen
- `commands/excel.md`: komplett auf xlsx-Skill umstellen (Block C)

### Block B — Playwright-MCP → browser-use-Skill

**Zu ändern (12 Stellen):**

| Datei | Änderung |
|-------|----------|
| `.mcp.json` | Playwright-MCP-Server-Eintrag komplett entfernen |
| `scripts/configure_permissions.py:22-36` | 14 `mcp__playwright__*`-Permissions raus, browser-use-Permissions rein |
| `scripts/setup.sh:27-30` | `npx playwright install`-Block raus |
| `commands/setup.md:36-38` | Playwright-Install-Schritt raus |
| `commands/search.md:69-71` | `"use Playwright MCP directly"` → konkrete Anleitung für `browser-use`-Skill |
| `settings.json:12` | `Bash(cp ~/.playwright-mcp/* *)` raus |
| `README.md:26` | Node.js-Voraussetzung überprüfen (browser-use braucht Python) |
| `README.md:95-101` | Install-Block umschreiben |
| `README.md:198,318,337,392` | Doku auf browser-use umstellen |
| `config/browser_guides/*.md` | Navigationsguides von Playwright-Selektoren auf browser-use-Prompts umschreiben (Scholar, Springer, OECD, RePEc, OPAC) |
| `.gitignore:27` | `.playwright-mcp/` raus |

### Block C — `document-skills:xlsx`-Integration

**Entscheidung:** Plugins können andere Plugins nicht direkt auto-installieren. Integration läuft über:

1. `scripts/excel.py` löschen
2. `commands/excel.md` umschreiben: statt Python-Aufruf → Hinweis an Claude, den `document-skills:xlsx`-Skill anzuwenden, mit klarer Input/Output-Spezifikation
3. **README-Voraussetzung** ergänzen: `/plugin install document-skills@anthropic-agent-skills` als Install-Step dokumentieren
4. **SessionStart-Hook** in `hooks/hooks.json` erweitern: prüft, ob xlsx-Skill verfügbar, zeigt Warnung falls nicht
5. `/setup`-Command ergänzt diesen Check ebenfalls

## Out-of-Scope

- Inhaltliche Überarbeitung der Prompts → E3
- Citations-API, Evals → E4
- Neue Commands oder Skills

## Offene Fragen für E2-Kickoff-Brainstorm

1. `scripts/pdf.py` — wirklich löschbar, oder braucht `quote-extractor` PDF-Preprocessing, das Read-Tool nicht leistet (OCR, Passwort-entsperrt, Encoding)?
2. Wie soll `commands/search.md` bei Browser-Modulen mit `browser-use` konkret aussehen? Ein Prompt pro Datenbank oder ein generischer Prompt mit Parametern?
3. SessionStart-Hook-Check auf externen Skill: welche API/welches Flag? Ggf. Klärung nötig in der Claude-Code-Doku.
4. Config-Browser-Guides: komplett neu schreiben oder inkrementell? Migration pro Datenbank?

## Git-Plan (grob, wird verfeinert)

**Branch:** `refactor/e2-architecture` von `main` (nach E1-Merge)

**Commits (grob gruppiert):**
1. `chore(scripts): remove citations.py, style_analysis.py, ranking.py`
2. `refactor(commands): update score and related commands to use agents`
3. `refactor: remove Playwright MCP, migrate to browser-use`
4. `refactor(excel): replace scripts/excel.py with document-skills:xlsx integration`
5. `docs: update README for browser-use and document-skills requirements`
6. `chore(release): v5.0.0`

## Verifikation

- Keine Verweise mehr auf gelöschte Skripte (`grep -r "citations\.py\|style_analysis\.py\|ranking\.py\|excel\.py"`)
- Keine Verweise mehr auf Playwright (`grep -ri "playwright"`)
- `/setup`-Command läuft sauber durch
- `browser-use`-Skill wird für Browser-Datenbanken korrekt angesteuert
- xlsx-Skill-Check in SessionStart-Hook funktioniert

## Rollback

Major-Release, deshalb Rollback = User muss zurück auf v4.0.1 pinnen. Pre-Merge: üblicher Branch-Revert-Pfad.
