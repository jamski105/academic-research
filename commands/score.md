---
description: Score and rank literature with 5D scoring system (Relevance, Recency, Quality, Authority, Accessibility)
disable-model-invocation: true
allowed-tools: Read, Agent(relevance-scorer)
argument-hint: [papers.json] [--query "..."] [--mode standard]
---

# Literatur-Scoring

Papers mithilfe des `relevance-scorer`-Agents neu scoren und ranken. Der Agent bewertet Titel + Abstract gegen die Query auf einer 0.0–1.0-Skala und liefert Reasoning und Confidence je Paper.

## Verwendung

- `/academic-research:score` — Papers aus der letzten Session scoren
- `/academic-research:score papers.json --query "DevOps"` — Bestimmte Datei scoren
- `/academic-research:score --mode deep` — Scoring mit zusätzlichem Confidence-Durchlauf

## 5D-Dimensionen (Referenz, Agent übernimmt 1D-Relevanz)

| Dimension | Gewicht | Quelle |
|-----------|---------|--------|
| Relevanz | 0.35 | `relevance-scorer`-Agent (Titel + Abstract-Match) |
| Aktualität | 0.20 | 5-Jahre-Halbwertszeit-Decay, berechnet aus `year`-Feld |
| Qualität | 0.15 | Zitationen pro Jahr mit Log-Skalierung, aus `citation_count` |
| Autorität | 0.15 | Venue-Heuristik aus `venue`/`source`-Feld |
| Zugang | 0.15 | Open Access > Institutional > DOI > URL > Nichts |

Die vier Nicht-Relevanz-Dimensionen werden direkt in der Command-Logik als arithmetische Funktionen berechnet (siehe Gewichtungen). Keine Python-Pipeline.

## Cluster

- **Kernliteratur** (grün): Total ≥ 0.75, Relevanz ≥ 0.80
- **Ergänzungsliteratur** (blau): Total ≥ 0.50, Relevanz ≥ 0.50
- **Hintergrundliteratur** (grau): Total ≥ 0.30
- **Methodenliteratur** (gelb): Methodologie-Schlüsselwörter in Titel/Abstract

## Umsetzung

### Schritt 1: Paper-Quelle finden

```bash
LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
PAPERS=~/.academic-research/sessions/$LATEST/deduped.json
```

Bei explizitem Argument: diesen Pfad verwenden.

### Schritt 2: Relevanz-Scoring via Agent

Papers in Batches à 10 an den `relevance-scorer`-Agent schicken. Input pro Batch:

```json
{
  "user_query": "<QUERY>",
  "papers": [
    {"doi": "...", "title": "...", "abstract": "...", "year": 2023}
  ]
}
```

Output-Feld `relevance_score` je Paper als 0.0–1.0-Float einsammeln.

### Schritt 3: 4 weitere Dimensionen berechnen

Je Paper:

- `recency = exp(-ln(2) * (current_year - year) / 5)` — exponentieller Decay, 5-Jahres-Halbwertszeit
- `quality = min(log10(citations / max(1, years_since_pub) + 1) / 2, 1.0)` — Log-skalierte Zitationen pro Jahr
- `authority` = 1.0 für bekannte Top-Venues (IEEE, ACM, Springer, Nature, Elsevier), 0.7 für indexierte Journals, 0.4 für Konferenzen, 0.2 sonst
- `access` = 1.0 für Open Access, 0.8 für DOI mit Institutional Access, 0.5 für nur DOI, 0.2 für nur URL

### Schritt 4: Gesamtscore und Cluster

```
total = 0.35 * relevance + 0.20 * recency + 0.15 * quality + 0.15 * authority + 0.15 * access
```

Cluster gemäß Threshold-Tabelle oben zuordnen.

### Schritt 5: Ausgabe

Papers nach Cluster sortiert als formatierte Markdown-Tabelle ausgeben. Als JSON in `ranked.json` im Session-Verzeichnis speichern.
