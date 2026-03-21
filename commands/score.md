---
description: Score and rank literature with 5D scoring system (Relevance, Recency, Quality, Authority, Accessibility)
allowed-tools: Read, Bash(~/.academic-research/venv/bin/python *)
argument-hint: [papers.json] [--query "..."] [--mode standard] [--scoring-config path]
---

# Literature Scoring

Re-score and rank papers using the 5D scoring system with cluster assignment.

## Usage

- `/academic-research:score` — Score papers from latest session
- `/academic-research:score papers.json --query "DevOps"` — Score specific file
- `/academic-research:score --mode deep` — Score with portfolio adjustments

## 5D Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Relevanz | 0.35 | Keyword match in title (70%) + abstract (30%) + phrase bonus |
| Aktualität | 0.20 | 5-year half-life exponential decay |
| Qualität | 0.15 | Citations-per-year with log scaling |
| Autorität | 0.15 | Venue reputation heuristic |
| Zugang | 0.15 | Open Access > Institutional > DOI > URL > Nothing |

## Clusters

- **Kernliteratur** (green): Total ≥ 0.75, Relevance ≥ 0.80
- **Ergänzungsliteratur** (blue): Total ≥ 0.50, Relevance ≥ 0.50
- **Hintergrundliteratur** (gray): Total ≥ 0.30
- **Methodenliteratur** (yellow): Methodology keywords in title/abstract

## Implementation

Find the latest session or use provided file:

```bash
# Find latest session
LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
PAPERS=~/.academic-research/sessions/$LATEST/deduped.json
```

Run ranking:

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py \
  --papers "$PAPERS" \
  --query "$QUERY" \
  --mode "$MODE" \
  --scoring-config "${CLAUDE_PLUGIN_ROOT}/config/scoring.yaml" \
  --output "$OUTPUT"
```

Display results as formatted table grouped by cluster.
