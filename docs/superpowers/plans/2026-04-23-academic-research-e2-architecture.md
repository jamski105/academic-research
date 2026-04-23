# E2 Architecture Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bereinigen der Architektur des `academic-research`-Plugins: drei redundante Python-Skripte löschen, Playwright-MCP durch den globalen `browser-use`-Skill ersetzen, `excel.py` durch den externen `document-skills:xlsx`-Skill ersetzen, Release `v5.0.0` (Breaking).

**Architecture:** Branch `refactor/e2-architecture`. 11 atomare Commits, ein PR gegen `main`. Kein neuer Code — Löschungen, Command-Rewrites, Doku-Updates und Hook-Ergänzung. Verifikation per `rg` und manuelles Durchspielen von `/setup`.

**Tech Stack:** Python 3.10+, Claude Code Plugin-System, `browser-use` CLI, `document-skills:xlsx` (externes Plugin), Bash, SessionStart-Hook.

**Spec:** `docs/superpowers/specs/2026-04-23-academic-research-e2-architecture-design.md`

---

## File Structure

### Zu löschen

- `scripts/citations.py` (20 KB) — Skill `citation-extraction` + Agent `quote-extractor` übernehmen
- `scripts/style_analysis.py` (17 KB) — Skill `style-evaluator` übernimmt
- `scripts/ranking.py` (12 KB) — Agent `relevance-scorer` + Skill `source-quality-audit` übernehmen
- `scripts/excel.py` (14.5 KB) — `document-skills:xlsx` übernimmt
- `tests/test_excel.py`, `tests/test_ranking.py`, `tests/test_style_analysis.py` — Tests der gelöschten Skripte

### Zu ändern (Commands)

- `commands/score.md` — Python-`ranking.py`-Aufruf durch Agent-Hinweis ersetzen
- `commands/search.md` — zwei Stellen: Zeile 86 (`ranking.py`-Call raus) und Schritt 4 (Playwright → browser-use)
- `commands/excel.md` — komplett neu: `document-skills:xlsx` statt Python-Pipeline
- `commands/setup.md` — Playwright-Schritt raus, browser-use-Prereq + xlsx-Check rein

### Zu ändern (Skills)

- `skills/citation-extraction/SKILL.md` — `citations.py`-Verweise (Zeilen 8, 87, 102, 108, 114, 149) raus
- `skills/source-quality-audit/SKILL.md` — `ranking.py`-Verweise (Zeilen 22-24, 64, 168) raus
- `skills/chapter-writer/SKILL.md` — `citations.py`-Verweis (Zeile 77) raus
- `skills/style-evaluator/SKILL.md` — `style_analysis.py`-Verweise (Zeilen 24-25, 96, 140) raus

### Zu ändern (Konfiguration)

- `.mcp.json` — Playwright-MCP-Eintrag weg
- `scripts/configure_permissions.py` — Playwright-Permissions raus, `Bash(browser-use:*)` rein
- `scripts/setup.sh` — Playwright-Install-Block raus
- `scripts/requirements.txt` — `openpyxl` raus
- `settings.json` — `Bash(cp ~/.playwright-mcp/* *)` raus
- `.gitignore` — `.playwright-mcp/` raus
- `hooks/hooks.json` — zweiter SessionStart-Hook (document-skills-Check) dazu
- `.claude-plugin/plugin.json` — Version `4.0.1` → `5.0.0`
- `.claude-plugin/marketplace.json` — Version `4.0.1` → `5.0.0`

### Zu ändern (Doku)

- `README.md` — Prerequisites (Node.js raus, browser-use rein, document-skills rein), Skripte-Tabelle kürzen, Dateibaum anpassen, alle Playwright-Erwähnungen raus
- `CHANGELOG.md` — neuer `## [5.0.0]`-Block

### Zu ändern (Browser-Guides — alle in einem Commit)

- `config/browser_guides/google_scholar.md`
- `config/browser_guides/destatis.md`
- `config/browser_guides/oecd.md`
- `config/browser_guides/springer.md`
- `config/browser_guides/repec.md`
- `config/browser_guides/opac.md`
- `config/browser_guides/ebscohost.md`
- `config/browser_guides/proquest.md`
- `config/browser_guides/han_login.md`

---

## Task 0: Branch und Plan-Commit

**Files:**
- Create: `docs/superpowers/plans/2026-04-23-academic-research-e2-architecture.md` (diese Datei)

- [ ] **Step 1: Branch prüfen**

```bash
git branch --show-current
```
Erwartet: `refactor/e2-architecture`. Falls nicht: `git checkout -b refactor/e2-architecture` von `main` aus.

- [ ] **Step 2: Plan-Commit**

```bash
git add docs/superpowers/plans/2026-04-23-academic-research-e2-architecture.md
git commit -m "$(cat <<'EOF'
docs(plan): E2 architecture cleanup implementation plan

11 atomare Commits für v5.0.0: Skripte löschen, Playwright → browser-use,
excel.py → document-skills:xlsx.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 1: Redundante Skripte und Tests löschen

**Commit:** `chore(scripts): delete citations.py, style_analysis.py, ranking.py + tests`

**Closes:** #19, #20, #21 (Teil 1)

**Files:**
- Delete: `scripts/citations.py`
- Delete: `scripts/style_analysis.py`
- Delete: `scripts/ranking.py`
- Delete: `tests/test_excel.py`, `tests/test_ranking.py`, `tests/test_style_analysis.py`

- [ ] **Step 1: Skripte und Tests löschen**

```bash
git rm scripts/citations.py scripts/style_analysis.py scripts/ranking.py
git rm tests/test_excel.py tests/test_ranking.py tests/test_style_analysis.py
```

- [ ] **Step 2: Verifizieren, dass Dateien weg sind**

```bash
ls scripts/citations.py scripts/style_analysis.py scripts/ranking.py 2>&1
```
Erwartet: drei Zeilen "No such file or directory".

- [ ] **Step 3: Restliche Tests laufen lassen (müssen grün bleiben)**

```bash
cd /Users/j65674/Repos/academic-research
~/.academic-research/venv/bin/python -m pytest tests/ -q 2>&1 | tail -10
```
Erwartet: kein Fehler (die verbleibenden Tests sollen durchlaufen — wenn keine anderen Tests existieren, meldet pytest "no tests ran", das ist ok).

- [ ] **Step 4: Commit**

```bash
git commit -m "$(cat <<'EOF'
chore(scripts): delete citations.py, style_analysis.py, ranking.py + tests

Redundant zu Skills/Agents. Ersatz:
- citations.py → skill citation-extraction + agent quote-extractor
- style_analysis.py → skill style-evaluator
- ranking.py → agent relevance-scorer + skill source-quality-audit

Closes #19 #20 #21 (teilweise, Migration in Folge-Commit).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: score.md und search.md an Agent verdrahten

**Commit:** `refactor(commands): wire score.md and search.md to relevance-scorer agent`

**Closes:** #19, #20, #21 (Teil 2)

**Files:**
- Modify: `commands/score.md`
- Modify: `commands/search.md:85-92` (der `ranking.py`-Aufruf in Step 6)

- [ ] **Step 1: `commands/score.md` komplett neu schreiben**

Inhalt (gesamte Datei ersetzen):

```markdown
---
description: Score and rank literature with 5D scoring system (Relevance, Recency, Quality, Authority, Accessibility)
disable-model-invocation: true
allowed-tools: Read, Agent(relevance-scorer)
argument-hint: [papers.json] [--query "..."] [--mode standard]
---

# Literature Scoring

Re-score and rank papers using the `relevance-scorer`-Agent. Der Agent bewertet Titel+Abstract gegen die Query auf einer 0.0-1.0-Skala und liefert Reasoning und Confidence je Paper.

## Usage

- `/academic-research:score` — Score papers from latest session
- `/academic-research:score papers.json --query "DevOps"` — Score specific file
- `/academic-research:score --mode deep` — Score with additional confidence pass

## 5D Dimensions (Referenz, Agent übernimmt 1D-Relevance)

| Dimension | Weight | Source |
|-----------|--------|--------|
| Relevanz | 0.35 | `relevance-scorer`-Agent (Titel+Abstract-Match) |
| Aktualität | 0.20 | 5-Jahre-Halbwertszeit-Decay, berechnet aus `year`-Feld |
| Qualität | 0.15 | Citations-per-year mit Log-Scaling, aus `citation_count` |
| Autorität | 0.15 | Venue-Heuristik aus `venue`/`source`-Feld |
| Zugang | 0.15 | Open Access > Institutional > DOI > URL > Nichts |

Die 4 nicht-Relevanz-Dimensionen werden direkt in der Command-Logik als arithmetische Funktionen berechnet (siehe Gewichtungen). Keine Python-Pipeline.

## Clusters

- **Kernliteratur** (green): Total ≥ 0.75, Relevance ≥ 0.80
- **Ergänzungsliteratur** (blue): Total ≥ 0.50, Relevance ≥ 0.50
- **Hintergrundliteratur** (gray): Total ≥ 0.30
- **Methodenliteratur** (yellow): Methodology keywords in title/abstract

## Implementation

### Step 1: Paper-Quelle finden

```bash
LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
PAPERS=~/.academic-research/sessions/$LATEST/deduped.json
```

Bei explizitem Argument: verwende diesen Pfad.

### Step 2: Relevance-Scoring via Agent

Papers in Batches à 10 an den `relevance-scorer`-Agent schicken. Input pro Batch:

```json
{
  "user_query": "<QUERY>",
  "papers": [
    {"doi": "...", "title": "...", "abstract": "...", "year": 2023}
  ]
}
```

Output-Feld `relevance_score` je Paper als 0.0-1.0-Float einsammeln.

### Step 3: 4 weitere Dimensionen berechnen

Je Paper:

- `recency = exp(-ln(2) * (current_year - year) / 5)` — exponentieller Decay, 5-Jahres-Halbwertszeit
- `quality = min(log10(citations / max(1, years_since_pub) + 1) / 2, 1.0)` — Log-skalierte Citations-pro-Jahr
- `authority` = 1.0 für bekannte Top-Venues (IEEE, ACM, Springer, Nature, Elsevier), 0.7 für indexierte Journals, 0.4 für Konferenzen, 0.2 sonst
- `access` = 1.0 für Open Access, 0.8 für DOI mit Institutional Access, 0.5 für nur DOI, 0.2 für nur URL

### Step 4: Gesamtscore und Cluster

```
total = 0.35 * relevance + 0.20 * recency + 0.15 * quality + 0.15 * authority + 0.15 * access
```

Cluster per Threshold-Tabelle oben zuordnen.

### Step 5: Ausgabe

Papers nach Cluster sortiert als formatted Markdown-Tabelle ausgeben. Als JSON in `ranked.json` im Session-Dir speichern.
```

- [ ] **Step 2: `commands/search.md` Zeilen 85-92 anpassen**

Die Zeilen 85-92 in `commands/search.md` (der alte `ranking.py`-Aufruf in Step 6):

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py \
  --papers "$SESSION_DIR/deduped.json" \
  --query "$QUERY" \
  --mode "$MODE" \
  --scoring-config "${CLAUDE_PLUGIN_ROOT}/config/scoring.yaml" \
  --output "$SESSION_DIR/ranked.json"
```

ersetzen durch:

```markdown
Step 6 (5D-Ranking + Cluster): Die Heuristik-Dimensionen (Aktualität, Qualität, Autorität, Zugang) werden direkt in diesem Command berechnet — siehe Formeln in `commands/score.md` → "4 weitere Dimensionen berechnen". Gesamtscore wie dort, Clusterzuweisung ebenfalls. Das Resultat in `$SESSION_DIR/ranked.json` schreiben.
```

- [ ] **Step 3: Verifikation: keine Python-Calls auf gelöschte Skripte**

```bash
grep -n "ranking\.py\|citations\.py\|style_analysis\.py" commands/score.md commands/search.md
```
Erwartet: keine Treffer.

- [ ] **Step 4: Commit**

```bash
git add commands/score.md commands/search.md
git commit -m "$(cat <<'EOF'
refactor(commands): wire score.md and search.md to relevance-scorer agent

- score.md: Python-Pipeline entfernt, nutzt relevance-scorer-Agent +
  inline-berechnete Heuristiken (Aktualität, Qualität, Autorität, Zugang).
- search.md:86: ranking.py-Aufruf durch Hinweis auf Command-interne
  Ranking-Logik ersetzt.

Closes #19 #20 #21.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Script-Referenzen in 4 Skills entfernen

**Commit:** `refactor(skills): remove deleted-script references`

**Files:**
- Modify: `skills/citation-extraction/SKILL.md` (Zeilen 8, 87, 102-117, 149)
- Modify: `skills/source-quality-audit/SKILL.md` (Zeilen 22-24, 64, 168)
- Modify: `skills/chapter-writer/SKILL.md` (Zeile 77)
- Modify: `skills/style-evaluator/SKILL.md` (Zeilen 24-25, 96, 140)

- [ ] **Step 1: `citation-extraction/SKILL.md` — Zeile 8**

Ersetze:

```markdown
Extract relevant quotes from academic PDFs, format citations in the required style, and organize citation data by chapter. Uses the quote-extractor agent for extraction and `citations.py` for formatting and export.
```

durch:

```markdown
Extract relevant quotes from academic PDFs, format citations in the required style, and organize citation data by chapter. Uses the quote-extractor agent for extraction and inline citation formatting logic (see "Citation Formatting" below).
```

- [ ] **Step 2: `citation-extraction/SKILL.md` — Abschnitt "Citation Formatting" (Zeilen 85-117)**

Ersetze den gesamten Abschnitt ab Zeile 85 (inkl. der drei Bash-Codeblöcke mit `citations.py`) durch:

```markdown
### 5. Citation Formatting

Formatiere Zitate inline nach dem in `academic_context.md` konfigurierten Stil. Keine externe Skript-Pipeline — Claude generiert die Formate direkt aus den strukturierten Paper-Daten.

#### Supported Styles

| Style | In-text Example | Bibliography Example |
|-------|----------------|----------------------|
| APA7 | (Müller, 2023, S. 45) | Müller, H. (2023). *Title*. Journal, 12(3), 44-67. |
| IEEE | [1, p. 45] | [1] H. Müller, "Title," *Journal*, vol. 12, no. 3, pp. 44-67, 2023. |
| Harvard | (Müller 2023, p. 45) | Müller, H. 2023, 'Title', *Journal*, vol. 12, no. 3, pp. 44-67. |
| Chicago | (Müller 2023, 45) | Müller, H. 2023. "Title." *Journal* 12 (3): 44-67. |
| BibTeX | `\cite{mueller2023}` | `@article{mueller2023, author={Müller, H.}, title={Title}, ...}` |

#### Output-Formate

Claude erzeugt bei Bedarf:
- **In-text-Zitat** — exakt im konfigurierten Stil mit Seitenzahl
- **Literaturverzeichnis-Eintrag** — formatiert pro Quelle
- **BibTeX-Datei** — für LaTeX-Integration (in `~/.academic-research/citations.bib` persistieren)
- **Markdown-Bibliographie** — für Review, sortiert nach Autor/Jahr
- **JSON** — wenn andere Skills die Daten strukturiert brauchen
```

- [ ] **Step 3: `citation-extraction/SKILL.md` — Zeile 149**

Ersetze:

```markdown
Support these output formats via `citations.py`:
```

durch:

```markdown
Support these output formats (inline generiert, kein externes Skript):
```

- [ ] **Step 4: `source-quality-audit/SKILL.md` — "Scripts"-Abschnitt (Zeilen 22-24)**

Den ganzen Abschnitt:

```markdown
## Scripts

Use `${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py` for source metadata analysis (venue authority scoring via `score_authority()`, recency scoring via `score_recency()`).
```

**komplett entfernen** (inkl. Leerzeilen davor/danach — keine Ersatzsektion).

- [ ] **Step 5: `source-quality-audit/SKILL.md` — Zeile 64**

Ersetze:

```markdown
Use `score_recency()` from `${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py` for per-source recency computation.
```

durch:

```markdown
Berechne Recency inline: `recency = exp(-ln(2) * (current_year - year) / 5)` — exponentieller Decay, 5-Jahres-Halbwertszeit.
```

- [ ] **Step 6: `source-quality-audit/SKILL.md` — Zeile 168**

Ersetze:

```markdown
- Use `score_authority()` from `ranking.py` for venue classification when metadata is available
```

durch:

```markdown
- Klassifiziere Venues inline: 1.0 für Top-Venues (IEEE, ACM, Springer, Nature, Elsevier), 0.7 für indexierte Journals, 0.4 für Konferenzen, 0.2 sonst
```

- [ ] **Step 7: `chapter-writer/SKILL.md` — Zeile 77**

Ersetze:

```markdown
When citing sources, use the citation data from `${CLAUDE_PLUGIN_ROOT}/scripts/citations.py` output. Reference papers by their formatted citation. Support these integration patterns:
```

durch:

```markdown
When citing sources, use the citation data produced by the Citation Extraction skill (inline-formatiert nach dem in `academic_context.md` konfigurierten Stil). Reference papers by their formatted citation. Support these integration patterns:
```

- [ ] **Step 8: `style-evaluator/SKILL.md` — "Scripts"-Abschnitt (Zeilen 22-25)**

Entferne den Abschnitt:

```markdown
## Scripts

Run `${CLAUDE_PLUGIN_ROOT}/scripts/style_analysis.py` for quantitative metrics (sentence length distribution, transition frequency, vocabulary diversity, n-gram repetition). Use script output as input to the scoring rubric below.
```

und ersetze ihn durch:

```markdown
## Metriken

Die quantitativen Metriken (Satzlängenverteilung, Übergangsfrequenz, Vokabular-Diversität, n-Gramm-Wiederholung) berechnet Claude direkt aus dem Eingabetext — keine externe Pipeline. Siehe Rubrik unten für konkrete Messvorschriften pro Dimension.
```

- [ ] **Step 9: `style-evaluator/SKILL.md` — Zeile 96 (im Workflow)**

Ersetze:

```markdown
3. Run `${CLAUDE_PLUGIN_ROOT}/scripts/style_analysis.py` with the text as input
```

durch:

```markdown
3. Berechne quantitative Metriken inline aus dem Eingabetext (Satzlängen, Übergänge, n-Gramme, Vokabular-Diversität)
```

- [ ] **Step 10: `style-evaluator/SKILL.md` — Zeile 140**

Ersetze:

```markdown
- Never fabricate metrics -- if `style_analysis.py` is unavailable, perform manual assessment and note the limitation
```

durch:

```markdown
- Never fabricate metrics -- berechne alle Werte nachvollziehbar aus dem Text und zeige die Rechenbasis, wenn der User danach fragt
```

- [ ] **Step 11: Verifikation: keine Skill-Dateien referenzieren mehr gelöschte Skripte**

```bash
grep -rn "citations\.py\|style_analysis\.py\|ranking\.py" skills/
```
Erwartet: keine Treffer.

- [ ] **Step 12: Commit**

```bash
git add skills/citation-extraction/SKILL.md skills/source-quality-audit/SKILL.md skills/chapter-writer/SKILL.md skills/style-evaluator/SKILL.md
git commit -m "$(cat <<'EOF'
refactor(skills): remove deleted-script references

Skills beschreiben Logik jetzt inline statt auf gelöschte Python-Skripte
zu verweisen:
- citation-extraction: Format-Logik im Prompt
- source-quality-audit: Recency/Authority-Formeln im Prompt
- chapter-writer: Verweis auf Skill-Output statt Skript
- style-evaluator: Metrik-Berechnung inline

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Playwright-MCP komplett entfernen

**Commit:** `refactor: remove Playwright MCP, add browser-use permissions`

**Closes:** #23, #26 (Teil 1)

**Files:**
- Modify: `.mcp.json` (Playwright-Eintrag raus)
- Modify: `scripts/configure_permissions.py:22-36` (Playwright-Permissions raus, `browser-use`-Permissions rein)
- Modify: `scripts/setup.sh:26-34` (Playwright-Install-Block raus)
- Modify: `commands/setup.md` (Schritt 5 raus, browser-use-Prereq rein)
- Modify: `settings.json:12` (Playwright-Bash-Regel raus)
- Modify: `.gitignore:27` (`.playwright-mcp/` raus)

- [ ] **Step 1: `.mcp.json` leeren**

Neuer Inhalt:

```json
{
  "mcpServers": {}
}
```

Alternative: Datei ganz löschen, wenn das Plugin keinen anderen MCP-Server braucht. Prüfen mit `cat .mcp.json`; wenn `playwright` der einzige Server ist, die leere Variante behalten (Plugin-Konvention).

- [ ] **Step 2: `scripts/configure_permissions.py` — neue Permission-Liste**

Ersetze `REQUIRED_PERMISSIONS` (Zeilen 15-37) durch:

```python
REQUIRED_PERMISSIONS = [
    "Bash(~/.academic-research/venv/bin/python *)",
    "Bash(~/.academic-research/venv/bin/pip *)",
    "Bash(python3 *)",
    "Bash(mkdir *)",
    "Bash(ls *)",
    "Bash(cat *)",
    "Bash(browser-use:*)",
    "Bash(browser-use *)",
]
```

- [ ] **Step 3: `scripts/setup.sh` — Playwright-Block entfernen**

Entferne Zeilen 26-34 (der Block `if command -v npx …` bis `fi`). Ersatz: zwei Zeilen zur browser-use-Prüfung:

```bash
if command -v browser-use &>/dev/null; then
  browser-use doctor &>/dev/null && echo "✅ browser-use: ready" || echo "⚠️  browser-use: install ok, but doctor meldet Probleme — bitte 'browser-use doctor' manuell prüfen"
else
  echo "⚠️  browser-use nicht gefunden — Browser-Module (Scholar, EBSCO, …) werden nicht funktionieren. Install: 'uv tool install browser-use' oder 'pipx install browser-use'"
fi
```

- [ ] **Step 4: `commands/setup.md` — Schritt 5 ersetzen**

Den Block (Zeilen 36-40):

```markdown
5. Install Playwright browser (required for browser search modules):
```bash
npx playwright install chromium --with-deps
```
If `npx` is not found, browser modules will be unavailable but API search still works.
```

ersetzen durch:

```markdown
5. Install `browser-use` CLI (required for browser search modules):
```bash
uv tool install browser-use   # oder: pipx install browser-use
browser-use doctor
```
Wenn `browser-use` nicht installiert ist, funktionieren API-Module weiter, aber keine Browser-Datenbanken (Google Scholar, Springer, OECD, RePEc, OPAC, EBSCO, ProQuest).
```

Weiterhin in `commands/setup.md` den `allowed-tools`-Frontmatter-Eintrag anpassen (Zeile 4) — `Bash(npx *)` entfernen:

```yaml
allowed-tools: Bash(python3 *), Bash(mkdir *), Bash(~/.academic-research/venv/bin/pip *)
```

- [ ] **Step 5: `settings.json` — Playwright-Zeile raus**

Entferne Zeile 12: `"Bash(cp ~/.playwright-mcp/* *)"`. Stelle sicher, dass das vorangegangene Komma korrekt bleibt.

- [ ] **Step 6: `.gitignore` — Playwright-Zeile raus**

Entferne Zeile 27 (`.playwright-mcp/`).

- [ ] **Step 7: Verifikation**

```bash
grep -rn "playwright" . --include='*.json' --include='*.py' --include='*.sh' --include='*.md' --exclude-dir=docs | grep -v CHANGELOG | grep -v browser_guides
```
Erwartet: keine Treffer (außer in `docs/superpowers/specs/` und `CHANGELOG.md`, die wir ausgeschlossen haben). Browser-Guides kommen in Task 6 dran.

- [ ] **Step 8: Commit**

```bash
git add .mcp.json scripts/configure_permissions.py scripts/setup.sh commands/setup.md settings.json .gitignore
git commit -m "$(cat <<'EOF'
refactor: remove Playwright MCP, add browser-use permissions

- .mcp.json: Playwright-Server-Eintrag entfernt
- configure_permissions.py: 14 mcp__playwright__*-Rechte + npx-Regeln raus,
  dafür Bash(browser-use:*) und Bash(browser-use *) rein
- setup.sh: npx playwright install-Block raus, browser-use doctor-Check rein
- commands/setup.md: Schritt 5 (Playwright-Install) → browser-use-Install
- settings.json: Bash(cp ~/.playwright-mcp/* *) raus
- .gitignore: .playwright-mcp/ raus

Browser-Guides-Umbau folgt in eigenem Commit.

Closes #23.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `search.md` Schritt 4 auf browser-use migrieren

**Commit:** `refactor(search): migrate commands/search.md Step 4 to browser-use`

**Closes:** #24

**Files:**
- Modify: `commands/search.md` (Step 4, Zeilen ~67-75)

- [ ] **Step 1: `commands/search.md` Step 4 neu schreiben**

Die Zeilen ab `### Step 4: Browser search ...` bis zum Ende des Step-4-Abschnitts (vor `### Step 5: Deduplication`) ersetzen durch:

```markdown
### Step 4: Browser search (standard/deep modes, unless --no-browser)

Für jedes Browser-Modul in fester Reihenfolge:

1. **No-Auth zuerst:** `google_scholar` → `springer` → `oecd` → `repec`
2. **Auth danach:** `ebscohost` → `proquest` → `opac`

Pro Modul:

1. Lies den Guide aus `${CLAUDE_PLUGIN_ROOT}/config/browser_guides/<modul>.md` (URL, Auth-Typ, Anti-Scraping-Hinweise, datenbankspezifische Fallen).
2. Bei Auth-Modulen (`ebscohost`, `proquest`, `opac`): folge zuerst `${CLAUDE_PLUGIN_ROOT}/config/browser_guides/han_login.md`.
3. Steuere den Browser mit dem globalen `browser-use`-Skill (CLI-basiert, index-orientiert, keine CSS-Selektoren):
   - `browser-use open <URL>` — Seite laden
   - `browser-use state` — klickbare Elemente mit Index abrufen
   - Query-Feld per Index identifizieren: `browser-use input <idx> "<QUERY>"`
   - Suche auslösen (Enter oder Submit-Button per Index klicken): `browser-use click <idx>`
   - Nach Warten auf Laden: `browser-use state` erneut, um Ergebnislisten auszulesen
   - Bei Bedarf paginieren — maximal 2 Seiten pro Modul
4. Ergebnisse ins `api_results.json`-Schema normalisieren (`title`, `authors`, `year`, `venue`, `doi`, `url`, `source_module`, `snippet`) und an die bestehende Ergebnisliste anhängen.
5. Fehlerbehandlung:
   - CAPTCHA erkannt → `browser-use screenshot` machen, User informieren, Partial Results behalten.
   - Login schlägt fehl → Modul überspringen, Warnung loggen, weitermachen mit nächstem Modul.
   - Rate-Limit → 30s Pause, einmal retry, dann Modul überspringen.

Append results to `$SESSION_DIR/api_results.json`.
```

- [ ] **Step 2: Frontmatter `allowed-tools` in `commands/search.md` anpassen**

Zeile 4 aktuell:

```yaml
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Agent(query-generator, relevance-scorer, quote-extractor)
```

neu:

```yaml
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Bash(browser-use:*), Bash(browser-use *), Agent(query-generator, relevance-scorer, quote-extractor)
```

- [ ] **Step 3: Verifikation**

```bash
grep -n "browser-use" commands/search.md
grep -n "Playwright MCP\|playwright" commands/search.md
```
Erwartet: Treffer in Step 4, keine Playwright-Treffer mehr.

- [ ] **Step 4: Commit**

```bash
git add commands/search.md
git commit -m "$(cat <<'EOF'
refactor(search): migrate commands/search.md Step 4 to browser-use

Ein generischer browser-use-Workflow ersetzt die alte Playwright-MCP-
Anleitung. Keine Selektoren mehr — browser-use-Skill steuert
semantisch über Indizes aus 'browser-use state'.

allowed-tools erweitert um Bash(browser-use:*) und Bash(browser-use *).

Closes #24.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Alle 9 Browser-Guides verschlanken

**Commit:** `refactor(browser-guides): rewrite all 9 guides for browser-use (no selectors)`

**Closes:** #25

**Files:** (alle in einem Commit)
- Modify: `config/browser_guides/google_scholar.md`
- Modify: `config/browser_guides/destatis.md`
- Modify: `config/browser_guides/oecd.md`
- Modify: `config/browser_guides/springer.md`
- Modify: `config/browser_guides/repec.md`
- Modify: `config/browser_guides/han_login.md`
- Modify: `config/browser_guides/ebscohost.md`
- Modify: `config/browser_guides/proquest.md`
- Modify: `config/browser_guides/opac.md`

**Zielgröße:** no-auth-Guides 15-30 Zeilen, auth-Guides 40-60 Zeilen. Alle CSS-Selektoren, JavaScript-Snippets und Playwright-Commands (`browser_snapshot`, `browser_evaluate`, `browser_navigate`, `browser_click`, `browser_type`, `browser_press_key`, `browser_wait_for`) raus.

- [ ] **Step 1: `google_scholar.md` ersetzen**

Neuer Inhalt (komplett):

```markdown
# Google Scholar — Navigation Guide

**URL:** https://scholar.google.com
**Auth:** keine
**Max. Ergebnisse:** 20 (2 Seiten à 10)
**Anti-Scraping:** **hoch** — Google blockiert Bots aggressiv. 2-3 Sekunden Pause zwischen Aktionen. Bei CAPTCHA: Screenshot machen, User informieren, Partial Results zurückgeben. Max. ~100 Requests/Tag pro IP.

## Hinweise

- URL-Parameter: `?q=<QUERY>` für Erstsuche, `?start=10&q=<QUERY>` für Seite 2.
- Nach `browser-use state` enthält jede Ergebniszeile mehrere Links: Titel, PDF, Zitationen ("Cited by N" / "Zitiert von N"), "Speichern", "Zitieren". **Nicht den ersten Link in der Ergebniszeile klicken** — wähle anhand des Link-Texts (z. B. "Cited by" enthält die Zitationszahl).
- Autoren-Zeile folgt dem Format `AUTOR1, AUTOR2 - VENUE, JAHR - PUBLISHER`. Parsing erfolgt durch den LLM aus dem `state`-Output.
- Kein API-Key, keine offizielle API. Scholar blockiert IPs nach Erkennung dauerhaft — vorsichtig einsetzen.
```

- [ ] **Step 2: `destatis.md` ersetzen**

```markdown
# Destatis — Navigation Guide

**URL:** https://www.destatis.de/DE/Themen/_inhalt.html
**Auth:** keine
**Max. Ergebnisse:** 15
**Anti-Scraping:** niedrig — deutsches Statistisches Bundesamt, keine Rate-Limits beobachtet.

## Hinweise

- Volltextsuche über die Lupe in der oberen rechten Ecke erreichbar.
- Ergebnisse sind oft PDF-Publikationen; Download-Link heißt "Publikation" oder "Tabellenband".
- Nur für statistische/amtliche Quellen geeignet — keine peer-reviewten Paper.
- Bei Zahlenreihen-Anfragen: direkter Weg über Themenbereich → Tabellen, nicht über Volltextsuche.
```

- [ ] **Step 3: `oecd.md` ersetzen**

```markdown
# OECD iLibrary — Navigation Guide

**URL:** https://www.oecd-ilibrary.org
**Auth:** keine für Abstracts; Volltext via Institution (falls Campus-Zugriff)
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig.

## Hinweise

- Suchleiste im Header; erweiterte Suche unter `/search-results?q=<QUERY>&option_quicksearch=...` nicht zuverlässig deep-link-bar — besser Suchleiste per `browser-use input`.
- Ergebnisliste enthält Working Papers, Policy Briefs, Statistiken. Filter "Content Type" nutzen, wenn der User nur Papers will.
- DOI-Link erscheint auf der Detailseite ganz unten im Metadaten-Block.
- PDF-Download: Button "PDF" sichtbar, wenn institutionelle Berechtigung besteht; sonst nur Abstract.
```

- [ ] **Step 4: `springer.md` ersetzen**

```markdown
# Springer Link — Navigation Guide

**URL:** https://link.springer.com
**Auth:** keine für Metadaten; Volltext je nach Lizenz (Open Access oder Campus-Zugriff)
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig — Springer ist kooperativ.

## Hinweise

- Suchleiste im Header; Direkt-URL `?query=<QUERY>&content-type=Article` für nur-Article-Ergebnisse.
- Jede Ergebniszeile enthält Open-Access-Indikator ("Open Access" als Badge) — bei `browser-use state` als Text sichtbar.
- DOI steht in der URL der Detailseite (`/article/10.xxxx/...`).
- Für Volltext-PDF: Button "Download PDF" auf Detailseite. Bei fehlender Berechtigung stattdessen "Access options"-Button.
```

- [ ] **Step 5: `repec.md` ersetzen**

```markdown
# RePEc / IDEAS — Navigation Guide

**URL:** https://ideas.repec.org
**Auth:** keine
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig.

## Hinweise

- Standardsuche unter `/cgi-bin/htsearch?q=<QUERY>` — manchmal bevorzugt Google-Suche via "`site:ideas.repec.org <query>`".
- Ergebnisse sind überwiegend Working Papers aus Volkswirtschaftslehre — für technische/informatische Themen meist nicht relevant.
- Jede Publikationsseite listet Co-Authors, Downloads (PDF-Link "Download full text"), und Handle-ID (`RePEc:xxx:yyy`).
- Citations (EconPapers/IDEAS-Zählung) auf der Paper-Seite im rechten Block.
```

- [ ] **Step 6: `han_login.md` ersetzen**

```markdown
# HAN-Login — Shared Auth-Guide für Leibniz FH

**URL:** https://han.leibniz-fh.de
**Purpose:** Zentrale Authentifizierung für EBSCOhost, ProQuest, OPAC und weitere lizenzierte Datenbanken der Leibniz FH.
**Credentials-Quelle:** `~/.academic-research/credentials.json` — Keys `han_user`, `han_password`. Falls Datei fehlt oder Keys leer, User informieren und Modul überspringen.

## Login-Flow

1. `browser-use open https://han.leibniz-fh.de`
2. `browser-use state` → Login-Formular finden (Felder meist "Benutzername"/"Username" und "Passwort"/"Password")
3. Benutzername eintippen: `browser-use input <idx_username> "<han_user>"`
4. Passwort eintippen: `browser-use input <idx_password> "<han_password>"`
5. "Login"-Button per Index klicken: `browser-use click <idx_login>`
6. Auf Weiterleitung warten, dann zur Zieldatenbank navigieren (meist Link in der HAN-Portal-Seite).

## Fehlerbehandlung

- Falsche Credentials → klare Fehlermeldung der HAN-Seite erkennbar in `state`-Output ("Anmeldung fehlgeschlagen" o. ä.). Abbrechen, User informieren.
- 2FA-Prompt → `browser-use screenshot`, User muss manuell bestätigen. Skill pausiert.
- Wartung-Ankündigung → Datenbank-Zugriff heute unmöglich. User informieren, API-Suche fortsetzen.

## Hinweise

- Eine Session reicht meist für alle Leibniz-FH-Datenbanken innerhalb eines Tages.
- Credentials niemals in Logs oder Commits schreiben — Dateipfad ist in `.gitignore`.
```

- [ ] **Step 7: `ebscohost.md` ersetzen**

```markdown
# EBSCOhost — Navigation Guide

**URL (über HAN):** https://han.leibniz-fh.de → EBSCOhost
**Auth:** HAN-Login (siehe `han_login.md`)
**Max. Ergebnisse:** 30
**Anti-Scraping:** niedrig (lizenzierter Zugriff), aber Timeout nach ~20 min Inaktivität.

## Hinweise

- Nach HAN-Login auf der Portal-Seite den Link "EBSCOhost" klicken.
- Suchoberfläche bietet "Advanced Search" im Hauptmenü — für strukturierte Suche meist besser als die Basissuche.
- Jede Ergebnisseite zeigt Badges: "Peer Reviewed", "Full Text", "Scholarly (Peer Reviewed) Journal". Im `browser-use state`-Output als Text erkennbar.
- Volltext-PDF via Button "PDF Full Text" (wenn verfügbar) oder "HTML Full Text".
- Filter im linken Panel: "Source Types", "Publication Date", "Subject: Thesaurus Term".

## Datenbanken innerhalb EBSCOhost

- Business Source Premier (Wirtschaft)
- Academic Search Complete (interdisziplinär)
- ERIC (Pädagogik)
- APA PsycInfo (Psychologie)

Auswahl im Dropdown "Choose Databases" oben rechts vor der Suche.

## Fehlerbehandlung

- "Service unavailable"-Meldung → später retry, einzelne Datenbanken manchmal offline.
- Session-Timeout → HAN-Login erneut durchführen, Command fortsetzen.
```

- [ ] **Step 8: `proquest.md` ersetzen**

```markdown
# ProQuest — Navigation Guide

**URL (über HAN):** https://han.leibniz-fh.de → ProQuest
**Auth:** HAN-Login (siehe `han_login.md`)
**Max. Ergebnisse:** 30
**Anti-Scraping:** niedrig (lizenzierter Zugriff).

## Hinweise

- Nach HAN-Login den Link "ProQuest" klicken.
- Basis-Suchfeld im Header, Advanced Search unter "Erweiterte Suche" oder "Advanced Search".
- Filter im linken Panel: "Source Type" (Scholarly Journals, Dissertations, Conference Papers, Trade Journals), "Publication Date", "Peer Reviewed".
- Volltext-PDF via "Full Text - PDF"-Link auf der Ergebnis- oder Detailseite.
- Dissertations & Theses Global als eigene Datenbank unter "Datenbanken" wählbar — für Masterarbeit-Recherche relevant.

## Datenbanken innerhalb ProQuest

- ABI/INFORM Collection (Business, Management)
- Dissertations & Theses Global
- ProQuest Central (interdisziplinär)

Auswahl über "Datenbanken ändern" oben.

## Fehlerbehandlung

- "Die Sitzung ist abgelaufen" → HAN-Login erneut, Command fortsetzen.
- CAPTCHA im Advanced-Search-Formular — selten, aber möglich. Screenshot, User informieren.
```

- [ ] **Step 9: `opac.md` ersetzen**

```markdown
# OPAC — Leibniz FH Bibliotheks-Katalog — Navigation Guide

**URL (über HAN):** https://han.leibniz-fh.de → OPAC (Bibliothek)
**Auth:** HAN-Login (siehe `han_login.md`) optional — OPAC ist teils ohne Login abfragbar; Volltexte und Fernleihe brauchen Login.
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig.

## Hinweise

- OPAC bildet den physischen und elektronischen Bestand der Leibniz-FH-Bibliothek ab. Für die meisten Themen weniger ergiebig als EBSCO/ProQuest, aber unverzichtbar für Bücher und institutionelle Schriftenreihen.
- Suchmaske ähnelt einem klassischen Bibliothekskatalog: Suchbegriff, Suchfeld (Titel/Autor/Schlagwort), Bool'sche Verknüpfung.
- Ergebnisse zeigen Verfügbarkeit und Signatur (z. B. "Nur vor Ort", "Ausleihbar", "Online-Zugang").
- Für Online-Zugang → Link "Zum elektronischen Volltext" — leitet oft über HAN auf externen Provider weiter.
- Fernleihe über "Anfordern"-Button nach Login. Nicht automatisiert auslösen — nur Metadaten extrahieren.

## Fehlerbehandlung

- "Keine Treffer" bei generischer Suche → Synonyme/alternative Schlagwörter versuchen.
- Server-Fehler → OPAC-Wartungsfenster prüfen (oft Sonntagnacht), später retry.
```

- [ ] **Step 10: Verifikation**

```bash
grep -rn "browser_snapshot\|browser_evaluate\|browser_navigate\|browser_click\|browser_type\|browser_press_key\|browser_wait_for" config/browser_guides/
grep -rn "\.gs_\|\.ebsco\|document\.querySelector" config/browser_guides/
```
Beide Commands: erwartete Ausgabe ist **leer**.

- [ ] **Step 11: Größen-Check**

```bash
wc -l config/browser_guides/*.md
```
Erwartet: no-auth-Guides um 15-30 Zeilen, auth-Guides um 40-60 Zeilen. Kein Guide > 80 Zeilen.

- [ ] **Step 12: Commit**

```bash
git add config/browser_guides/
git commit -m "$(cat <<'EOF'
refactor(browser-guides): rewrite all 9 guides for browser-use (no selectors)

Alle Playwright-Selektoren, JavaScript-Snippets und browser_*-Commands
raus. Neues Template: URL, Auth-Art, Anti-Scraping-Hinweise, datenbank-
spezifische Fallen. 40 KB → ~15 KB Gesamtgröße.

Closes #25.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: `excel.py` löschen, `commands/excel.md` auf xlsx-Skill umstellen

**Commit:** `refactor(excel): replace scripts/excel.py with document-skills:xlsx`

**Closes:** #27 (Teil 1)

**Files:**
- Delete: `scripts/excel.py`
- Modify: `commands/excel.md` (komplett neu)
- Modify: `scripts/requirements.txt` (`openpyxl` raus)

- [ ] **Step 1: excel.py löschen**

```bash
git rm scripts/excel.py
```

- [ ] **Step 2: `commands/excel.md` komplett ersetzen**

Neuer Inhalt:

```markdown
---
description: Generate or update a literature Excel spreadsheet via the document-skills:xlsx skill
disable-model-invocation: true
allowed-tools: Read, Write
argument-hint: [--papers papers.json] [--output literature.xlsx] [--context]
---

# Literature Excel Generator

Erstellt ein formatiertes Excel-Workbook aus gescorten Papers. Die eigentliche Excel-Generierung übernimmt der extern installierte `document-skills:xlsx`-Skill (siehe README-Prerequisites).

## Usage

- `/academic-research:excel` — Generate from latest session
- `/academic-research:excel --papers papers.json --output my_literature.xlsx`
- `/academic-research:excel --context` — Include chapter assignment from academic context

## Prerequisite

`document-skills:xlsx` muss installiert sein:

```
/plugin install document-skills@anthropic-agent-skills
```

Wenn nicht installiert: SessionStart-Hook warnt beim Start; dieser Command bricht klar ab, wenn der Skill beim Aufruf fehlt.

## Erwartete Sheets

1. **Literaturübersicht** — Full paper list with 5D scores, clusters, color-coded
2. **Cluster-Analyse** — Statistics per cluster with bar chart
3. **Kapitel-Zuordnung** — Papers assigned to outline chapters (requires `--context`)
4. **Datenblatt** — Raw data for programmatic access

## Implementation

### Step 1: Papers lokalisieren

```bash
if [ -z "$PAPERS" ]; then
  LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
  PAPERS=~/.academic-research/sessions/$LATEST/ranked.json
fi
```

### Step 2: xlsx-Skill-Verfügbarkeit prüfen

```bash
if [ ! -d "$HOME/.claude/plugins/cache/anthropic-agent-skills/document-skills" ]; then
  echo "❌ document-skills:xlsx nicht installiert."
  echo "   Install: /plugin install document-skills@anthropic-agent-skills"
  exit 1
fi
```

### Step 3: Input strukturieren

Lese die Paper-Daten aus `$PAPERS` (JSON-Array mit Feldern `title`, `authors`, `year`, `doi`, `total_score`, `cluster`, `relevance_score`, `recency_score`, `quality_score`, `authority_score`, `access_score`, `venue`, `source_module`).

Wenn `--context` gesetzt:
- Lese `academic_context.md` aus Memory; extrahiere `Gliederung`
- Berechne pro Paper die zugeordneten Kapitel (Keyword-Match zwischen `title`/`abstract` und Kapitelüberschriften)

### Step 4: xlsx-Skill aktivieren

Rufe den `document-skills:xlsx`-Skill mit klarer Input/Output-Spezifikation auf:

**Input:** Strukturierte Paper-Daten (siehe Step 3) plus Sheet-Spezifikation (welche Sheets, welche Spalten, welche Farbcodierung).

**Output:** `$OUTPUT` (Default: `~/.academic-research/sessions/$LATEST/literature.xlsx`).

**Sheet-Spezifikation:**

- **Literaturübersicht**: Spalten `Titel | Autoren | Jahr | Venue | DOI | Gesamt | Relevanz | Aktualität | Qualität | Autorität | Zugang | Cluster`. Farbcodierung je Cluster (Kern=grün, Ergänzung=blau, Hintergrund=grau, Methoden=gelb).
- **Cluster-Analyse**: Aggregatstatistik pro Cluster (Anzahl, Durchschnittsscore, Jahresverteilung) + eingebettetes Balkendiagramm.
- **Kapitel-Zuordnung** (nur bei `--context`): Mapping Kapitel → Papers.
- **Datenblatt**: Alle Rohdaten-Felder in flachem Tabellenformat.

### Step 5: Ergebnis präsentieren

Zeige Output-Pfad und Zusammenfassung (Anzahl Papers, Cluster-Verteilung, Dateigrösse).
```

- [ ] **Step 3: `scripts/requirements.txt` — `openpyxl` raus**

Aktueller Inhalt:

```
httpx>=0.25.0
PyPDF2>=3.0.0
openpyxl>=3.1.0
pyyaml>=6.0
```

Neuer Inhalt:

```
httpx>=0.25.0
PyPDF2>=3.0.0
pyyaml>=6.0
```

- [ ] **Step 4: `hooks/hooks.json` — openpyxl-Import-Check raus**

Der bestehende SessionStart-Hook importiert `openpyxl`. Da das Paket nicht mehr installiert wird, muss der Import-Check runter:

Ersetze den Bash-Command im bestehenden Hook:

```bash
bash -c 'VENV=~/.academic-research/venv; if [ ! -d "$VENV" ]; then echo "⚠️ academic-research: Python venv not found. Run /academic-research:setup"; exit 0; fi; $VENV/bin/python -c "import httpx, PyPDF2, openpyxl, yaml" 2>/dev/null && echo "✅ academic-research: Python environment ready" || echo "⚠️ academic-research: Missing dependencies. Run: $VENV/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"'
```

durch:

```bash
bash -c 'VENV=~/.academic-research/venv; if [ ! -d "$VENV" ]; then echo "⚠️ academic-research: Python venv not found. Run /academic-research:setup"; exit 0; fi; $VENV/bin/python -c "import httpx, PyPDF2, yaml" 2>/dev/null && echo "✅ academic-research: Python environment ready" || echo "⚠️ academic-research: Missing dependencies. Run: $VENV/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt"'
```

- [ ] **Step 5: Verifikation**

```bash
grep -n "excel\.py\|openpyxl" commands/ scripts/ hooks/ -r
```
Erwartet: keine Treffer.

- [ ] **Step 6: Commit**

```bash
git add -u scripts/excel.py commands/excel.md scripts/requirements.txt hooks/hooks.json
git commit -m "$(cat <<'EOF'
refactor(excel): replace scripts/excel.py with document-skills:xlsx

- scripts/excel.py gelöscht (14.5 KB)
- commands/excel.md neu geschrieben: Ruft extern installierten
  document-skills:xlsx-Skill auf, mit klarer Input/Output-Spezifikation
  und Vorab-Verfügbarkeitsprüfung.
- scripts/requirements.txt: openpyxl raus (wird vom externen Skill
  selbst mitgebracht)
- hooks/hooks.json: openpyxl-Import-Check aus dem Python-Environment-Hook

Closes #27 (Teil 1).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: SessionStart-Hook für document-skills-Warnung

**Commit:** `feat(hooks): warn on missing document-skills in SessionStart`

**Closes:** #28

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Zweiten SessionStart-Hook hinzufügen**

Aktuelles `hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'VENV=~/.academic-research/venv; ...'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Neu:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'VENV=~/.academic-research/venv; if [ ! -d \"$VENV\" ]; then echo \"⚠️ academic-research: Python venv not found. Run /academic-research:setup\"; exit 0; fi; $VENV/bin/python -c \"import httpx, PyPDF2, yaml\" 2>/dev/null && echo \"✅ academic-research: Python environment ready\" || echo \"⚠️ academic-research: Missing dependencies. Run: $VENV/bin/pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt\"'",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "bash -c '[ -d \"$HOME/.claude/plugins/cache/anthropic-agent-skills/document-skills\" ] || echo \"⚠️  academic-research: document-skills nicht installiert — /academic-research:excel benötigt: /plugin install document-skills@anthropic-agent-skills\"'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

Der zweite Hook schreibt **nur bei fehlendem Skill** eine Warnung; bei Erfolg stumm.

- [ ] **Step 2: JSON-Syntax prüfen**

```bash
python3 -c "import json; json.load(open('hooks/hooks.json'))"
```
Erwartet: kein Fehler (kein Output = ok).

- [ ] **Step 3: Manueller Session-Start-Test**

```bash
# Simuliere was der Hook macht:
bash -c '[ -d "$HOME/.claude/plugins/cache/anthropic-agent-skills/document-skills" ] || echo "⚠️  academic-research: document-skills nicht installiert — /academic-research:excel benötigt: /plugin install document-skills@anthropic-agent-skills"'
```
Erwartet: wenn `document-skills` installiert ist → kein Output. Wenn nicht → die Warnung.

- [ ] **Step 4: Commit**

```bash
git add hooks/hooks.json
git commit -m "$(cat <<'EOF'
feat(hooks): warn on missing document-skills in SessionStart

Zweiter SessionStart-Hook prüft per Pfad-Existenzcheck auf den
document-skills-Plugin-Cache. Stumm bei Erfolg, Warnung mit Install-
Befehl bei Fehlen.

Closes #28.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: README aktualisieren

**Commit:** `docs(readme): document browser-use + document-skills prerequisites`

**Closes:** #26 (Teil 2), #27 (Teil 2)

**Files:**
- Modify: `README.md` (Prerequisites, Skripte-Tabelle, Dateibaum, alle Playwright-Erwähnungen)

- [ ] **Step 1: Prerequisites-Block (Zeilen 22-35) ersetzen**

Suche:

```markdown
## Voraussetzungen

- **Python 3.9+** (empfohlen: 3.11+)
- **Claude Code** (CLI, aktuelle Version)
- **Node.js 18+** (für Playwright Browser-Module, optional)

### Python-Pakete

| Paket | Version | Zweck |
|-------|---------|-------|
| `httpx` | ≥0.25.0 | HTTP-Client für API-Suche |
| `PyPDF2` | ≥3.0.0 | PDF-Textextraktion |
| `openpyxl` | ≥3.1.0 | Excel-Generierung |
| `pyyaml` | ≥6.0 | YAML-Konfiguration |
```

ersetze durch:

```markdown
## Voraussetzungen

- **Python 3.10+** (empfohlen: 3.11+)
- **Claude Code** (CLI, aktuelle Version)
- **browser-use CLI** (für Browser-Suchmodule):
  ```bash
  uv tool install browser-use   # oder: pipx install browser-use
  browser-use doctor
  ```
  Zusätzlich muss der globale `browser-use`-Skill unter `~/.claude/skills/browser-use/` liegen (kommt mit dem CLI-Paket).
- **document-skills Plugin** (für `/academic-research:excel`):
  ```
  /plugin install document-skills@anthropic-agent-skills
  ```

### Python-Pakete

| Paket | Version | Zweck |
|-------|---------|-------|
| `httpx` | ≥0.25.0 | HTTP-Client für API-Suche |
| `PyPDF2` | ≥3.0.0 | PDF-Textextraktion |
| `pyyaml` | ≥6.0 | YAML-Konfiguration |
```

- [ ] **Step 2: Installations-Schritt 3 (Playwright) entfernen**

Suche:

```markdown
### 3. Playwright installieren (optional, für Browser-Module)

```bash
npx playwright install chromium --with-deps
```

Ohne Playwright funktionieren alle **API-basierten** Suchquellen (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv). Browser-Module (Google Scholar, Springer, OECD, RePEc, OPAC) erfordern Playwright.
```

und **ersetze den gesamten Abschnitt** durch:

```markdown
### 3. browser-use CLI installieren (für Browser-Suchmodule)

Siehe [Voraussetzungen](#voraussetzungen). Ohne `browser-use` funktionieren alle **API-basierten** Suchquellen (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv). Browser-Module (Google Scholar, Springer, OECD, RePEc, OPAC, EBSCOhost, ProQuest) erfordern `browser-use`.
```

- [ ] **Step 3: Nummerierung der Folge-Schritte anpassen**

Falls der "Permissions konfigurieren"-Schritt als `### 4.` weitergeht: bleibt Nummerierung konsistent (3 → 4). Falls der frühere "Playwright"-Schritt die Nummerierung verschoben hat: lasse die Nummerierung logisch durchlaufen.

- [ ] **Step 4: Skripte-Tabelle kürzen (Zeilen 270-277)**

Suche in `README.md` die Tabelle mit `ranking.py`, `citations.py`, `excel.py`, `style_analysis.py` und entferne diese vier Zeilen. Übrige Zeilen (search.py, dedup.py, pdf.py, text_utils.py, configure_permissions.py) bleiben.

- [ ] **Step 5: Dateibaum anpassen (Zeilen ~366-367)**

Suche:

```
│   ├── search.py, ranking.py, dedup.py, pdf.py
│   ├── citations.py, excel.py, style_analysis.py, text_utils.py
```

ersetze durch:

```
│   ├── search.py, dedup.py, pdf.py, text_utils.py
│   ├── configure_permissions.py, setup.sh, requirements.txt
```

- [ ] **Step 6: Restliche Playwright-Erwähnungen entfernen**

```bash
grep -n -i "playwright\|npx" README.md
```

Jede gefundene Zeile in `README.md` prüfen und entweder löschen oder durch einen browser-use-Äquivalent ersetzen. Insbesondere:
- Jeden Hinweis auf "Node.js" entfernen, falls kein anderer Grund für Node besteht (der Plugin-Workflow braucht kein Node mehr).
- `npx playwright install` → bereits entfernt in Step 2.

- [ ] **Step 7: Verifikation**

```bash
grep -i "playwright\|npx\|node\.js" README.md
grep "excel\.py\|citations\.py\|ranking\.py\|style_analysis\.py\|openpyxl" README.md
```
Beide: erwartete Ausgabe ist **leer**.

- [ ] **Step 8: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): document browser-use + document-skills prerequisites

- Prerequisites: Node.js-Eintrag raus, browser-use CLI + document-skills
  Plugin rein
- Python-Pakete-Tabelle: openpyxl raus
- Installations-Schritt "Playwright installieren" ersetzt durch
  "browser-use CLI installieren" mit Verweis auf Prerequisites
- Skripte-Tabelle: Einträge für gelöschte Skripte entfernt
- Dateibaum: gelöschte Skripte raus, configure_permissions/setup.sh/
  requirements.txt aufgenommen
- Alle weiteren Playwright-/npx-Erwähnungen entfernt

Closes #26 #27.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: CHANGELOG für v5.0.0

**Commit:** `docs: add v5.0.0 changelog`

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: CHANGELOG.md öffnen und neuen Block vor dem v4.0.1-Block einfügen**

Füge oben (nach der Einleitung, vor dem letzten Release-Block) diesen neuen Block ein:

```markdown
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
```

Falls die Datei mit `## [Unreleased]` beginnt, den neuen Block direkt darunter einfügen.

- [ ] **Step 2: Verifikation**

```bash
grep -n "\[5.0.0\]" CHANGELOG.md
```
Erwartet: genau eine Treffer-Zeile.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "$(cat <<'EOF'
docs: add v5.0.0 changelog

Changed, Removed und Migration dokumentiert. Breaking-Changes:
- Playwright → browser-use
- scripts/excel.py → document-skills:xlsx
- 3 weitere Skripte gelöscht (Logik in Skills/Agents/Commands)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Version-Bump v5.0.0

**Commit:** `chore(release): v5.0.0`

**Closes:** #29

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: `plugin.json` Version setzen**

Ändere `"version": "4.0.1"` zu `"version": "5.0.0"`.

- [ ] **Step 2: `marketplace.json` Version setzen**

Ändere `"version": "4.0.1"` zu `"version": "5.0.0"`.

- [ ] **Step 3: Verifikation**

```bash
grep -n '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Erwartet: beide Zeilen zeigen `5.0.0`.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "$(cat <<'EOF'
chore(release): v5.0.0

Closes #29.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Gesamt-Verifikation und PR

**Files:** keine Änderungen — nur Prüfung.

- [ ] **Step 1: Alle Verifikations-Greps**

```bash
cd /Users/j65674/Repos/academic-research

echo "=== 1. Gelöschte Skripte dürfen nirgends mehr referenziert werden (außer in Specs/CHANGELOG) ==="
grep -rn "citations\.py\|style_analysis\.py\|ranking\.py\|excel\.py" . \
  --exclude-dir=.git --exclude-dir=docs --exclude=CHANGELOG.md
# Erwartet: leer

echo ""
echo "=== 2. Playwright muss weg (außer in Specs/CHANGELOG) ==="
grep -rni "playwright\|mcp__playwright" . \
  --exclude-dir=.git --exclude-dir=docs --exclude=CHANGELOG.md
# Erwartet: leer

echo ""
echo "=== 3. Alte Playwright-Commands dürfen nicht mehr vorkommen ==="
grep -rn "browser_snapshot\|browser_evaluate\|browser_navigate\|browser_click\|browser_type\|browser_press_key\|browser_wait_for" . \
  --exclude-dir=.git --exclude-dir=docs --exclude=CHANGELOG.md
# Erwartet: leer

echo ""
echo "=== 4. browser-use muss an den erwarteten Stellen auftauchen ==="
grep -rn "browser-use" commands/ README.md scripts/configure_permissions.py config/browser_guides/
# Erwartet: Treffer in search.md, setup.md, README.md, configure_permissions.py,
# und in allen 9 Browser-Guides (zumindest indirekt über han_login.md-Referenz
# oder Anti-Scraping-Hinweise)

echo ""
echo "=== 5. Versionen ==="
grep '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
# Erwartet: beide 5.0.0
```

- [ ] **Step 2: `/setup`-Flow gedanklich/manuell durchspielen**

Zu Fuß nachvollziehen:
1. `commands/setup.md` Step 1-4 (mkdir, venv, pip install, verify) → funktionieren weiter (keine openpyxl-Prüfung mehr in Step 4 wenn wir das hier auch anpassen; Prüfungen in `setup.md` Step 4 decken httpx/PyPDF2/yaml ab — `openpyxl`-Check muss raus).

**Falls Step 4 in `setup.md` noch ein `openpyxl`-Import prüft: zusätzlichen Commit in Task 9 oder Nachtrag hier.**

Prüfen:

```bash
grep -n "openpyxl" commands/setup.md
```
Wenn Treffer → Zeile löschen, als Nachtrag committen:

```bash
git add commands/setup.md
git commit -m "fix(setup): remove openpyxl check from setup.md (moved to document-skills)"
```

2. Step 5 (browser-use-Install) → unser neuer Text.
3. Step 6 (configure_permissions) → unsere neue Liste.

- [ ] **Step 3: Plugin-Validator laufen lassen**

```bash
# Aus dem Plugin-Repo heraus
# (Plugin-Validator-Agent ist über das plugin-dev-Plugin verfügbar)
```

Dispatch über Agent-Tool mit `subagent_type="plugin-dev:plugin-validator"` und Bitten um vollständige Plugin-Validierung. Erwartet: keine Errors.

- [ ] **Step 4: Branch pushen**

```bash
git push -u origin refactor/e2-architecture
```

- [ ] **Step 5: PR erstellen**

```bash
gh pr create --repo jamski105/academic-research \
  --base main --head refactor/e2-architecture \
  --title "refactor: E2 architecture cleanup (v5.0.0)" \
  --body "$(cat <<'EOF'
## Summary

E2-Umsetzung laut Spec `docs/superpowers/specs/2026-04-23-academic-research-e2-architecture-design.md`.

**Breaking Changes:**
- Playwright-MCP → `browser-use`-CLI/-Skill
- `scripts/excel.py` → `document-skills:xlsx` Plugin
- `scripts/citations.py`, `style_analysis.py`, `ranking.py` gelöscht — Logik in Skills/Agents/Commands verlagert

Siehe `CHANGELOG.md` v5.0.0 für Migration.

## Commits

1. chore(scripts): delete citations.py, style_analysis.py, ranking.py + tests
2. refactor(commands): wire score.md and search.md to relevance-scorer agent
3. refactor(skills): remove deleted-script references
4. refactor: remove Playwright MCP, add browser-use permissions
5. refactor(search): migrate commands/search.md Step 4 to browser-use
6. refactor(browser-guides): rewrite all 9 guides for browser-use
7. refactor(excel): replace scripts/excel.py with document-skills:xlsx
8. feat(hooks): warn on missing document-skills in SessionStart
9. docs(readme): document browser-use + document-skills prerequisites
10. docs: add v5.0.0 changelog
11. chore(release): v5.0.0

## Test plan

- [ ] Alle Verifikations-Greps aus Task 12 Step 1 laufen sauber durch
- [ ] `/setup`-Command manuell durchspielen (venv + browser-use + permissions)
- [ ] `plugin-dev:plugin-validator`-Agent meldet keine Errors
- [ ] `rg "browser-use"` zeigt Treffer an allen erwarteten Stellen

Closes #9 #19 #20 #21 #22 #23 #24 #25 #26 #27 #28 #29.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 6: Auf User-Review warten**

Nach PR-Erstellung stoppen und den User um Review bitten. Erst nach Freigabe mergen und `v5.0.0`-Tag setzen (analog E1-Flow).

---

## Selbst-Review (Plan gegen Spec)

1. **Spec-Abdeckung:**
   - Block A (Skripte löschen) → Tasks 1, 2, 3, 7 ✓
   - Block B (Playwright → browser-use) → Tasks 4, 5, 6 ✓
   - Block C (xlsx-Integration) → Tasks 7, 8 ✓
   - Block D (Release) → Tasks 9, 10, 11 ✓
   - Verifikation aus Spec → Task 12 ✓
   - Rollback — Spec verweist auf Branch-Revert, kein expliziter Task nötig.

2. **Placeholder-Scan:** Alle Code-Blöcke vollständig, alle grep-Commands konkret, keine "TBD"/"TODO".

3. **Typ-Konsistenz:**
   - Agent-Name `relevance-scorer` ist in Task 2 und im Spec einheitlich.
   - Permission-Strings `Bash(browser-use:*)` und `Bash(browser-use *)` sind in Task 4 und Task 5 gleich.
   - SessionStart-Hook-Command in Task 7 Step 4 und Task 8 Step 1 ist exakt gleich formuliert (openpyxl raus, document-skills-Check dazu).
