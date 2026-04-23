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
