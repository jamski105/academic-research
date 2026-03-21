---
description: Generate or update a literature Excel spreadsheet with 5D scoring, clusters, and chapter assignment
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *)
argument-hint: [--papers papers.json] [--output literature.xlsx] [--context]
---

# Literature Excel Generator

Create a professionally formatted Excel workbook from scored papers.

## Usage

- `/academic-research:excel` — Generate from latest session
- `/academic-research:excel --papers papers.json --output my_literature.xlsx`
- `/academic-research:excel --context` — Include chapter assignment from academic context

## Sheets

1. **Literaturübersicht** — Full paper list with 5D scores, clusters, color-coded
2. **Cluster-Analyse** — Statistics per cluster with bar chart
3. **Kapitel-Zuordnung** — Papers assigned to outline chapters (requires academic context)
4. **Datenblatt** — Hidden raw data sheet for programmatic access

## Implementation

Find papers from latest session or provided file:

```bash
LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
PAPERS=~/.academic-research/sessions/$LATEST/ranked.json
```

Run Excel generation:

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/excel.py \
  --papers "$PAPERS" \
  --output "$OUTPUT" \
  --scoring-config "${CLAUDE_PLUGIN_ROOT}/config/scoring.yaml"
```

If `--context` flag is set, read the academic context from memory to enable chapter assignment.
The excel.py script accepts `--context` with a JSON file containing the outline structure.

Display the output path and summary statistics.
