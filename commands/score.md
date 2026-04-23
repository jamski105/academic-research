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
