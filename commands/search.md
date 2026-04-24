---
description: Search academic papers across multiple APIs (Semantic Scholar, CrossRef, OpenAlex, BASE, EconBiz, EconStor, arXiv)
disable-model-invocation: true
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Bash(browser-use:*), Bash(browser-use *), Agent(query-generator, relevance-scorer, quote-extractor)
argument-hint: "<query>" [--mode quick|standard|deep|metadata] [--modules crossref,openalex,...] [--limit N]
---

# Akademische Paper-Suche

Parallele Suche über 7 API-Quellen. Optional werden Queries mit dem `query-generator`-Agent erweitert.

## Verwendung

- `/academic-research:search "DevOps Governance"` — Standardsuche über alle API-Module
- `/academic-research:search "Machine Learning" --mode quick` — Schnelle Suche (4 Module)
- `/academic-research:search "IT Compliance" --mode deep` — Tiefensuche (alle Module + Portfolio-Anpassungen)
- `/academic-research:search "Cloud Computing" --modules crossref,semantic_scholar --limit 30`

## Argumente

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `query` | (erforderlich) | Suchanfrage |
| `--mode` | `standard` | quick (4 APIs), standard (7 APIs), deep (7 APIs + Portfolio), metadata (keine PDFs) |
| `--modules` | (aus Modus) | Override: kommagetrennte Modulnamen |
| `--limit` | `50` | Maximale Treffer pro Modul |
| `--no-expand` | false | `query-generator`-Agent überspringen, rohe Query nutzen |
| `--no-browser` | false | Browser-Module überspringen (nur APIs) |

## Modul-Auswahl nach Modus

- **quick**: crossref, openalex, semantic_scholar, arxiv
- **standard**: crossref, openalex, semantic_scholar, base, econbiz, econstor, arxiv
- **deep**: Alle 7 API-Module + Browser-Module (Google Scholar, Springer, OECD, RePEc, OPAC)
- **metadata**: Wie standard

## Umsetzung

### Schritt 1: Session-Verzeichnis anlegen

```bash
SESSION_DIR=~/.academic-research/sessions/$(date -u +%Y-%m-%dT%H-%M-%SZ)
mkdir -p "$SESSION_DIR/pdfs"
```

Metadaten sichern:
```json
{"query": "$QUERY", "mode": "$MODE", "timestamp": "$TIMESTAMP", "modules": [...]}
```

### Schritt 2: Query-Erweiterung (falls nicht `--no-expand`)

Den `query-generator`-Agent mit der User-Query und den Ziel-Modulen starten.
Ausgabe nach `$SESSION_DIR/queries.json` speichern.

### Schritt 3: API-Suche

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/search.py \
  --query "$QUERY" \
  --modules "$MODULES" \
  --limit $LIMIT \
  --queries-file "$SESSION_DIR/queries.json" \
  --output "$SESSION_DIR/api_results.json"
```

### Schritt 4: Browser-Suche (standard-/deep-Modus, falls nicht `--no-browser`)

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
   - CAPTCHA erkannt → `browser-use screenshot` machen, User informieren, Teilergebnisse behalten.
   - Login schlägt fehl → Modul überspringen, Warnung loggen, mit nächstem Modul weitermachen.
   - Rate-Limit → 30s Pause, einmal wiederholen, dann Modul überspringen.

Ergebnisse an `$SESSION_DIR/api_results.json` anhängen.

### Schritt 5: Deduplikation

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/dedup.py \
  --papers "$SESSION_DIR/api_results.json" \
  --output "$SESSION_DIR/deduped.json"
```

### Schritt 6: Ranking (5D-Scoring + Cluster)

Die Heuristik-Dimensionen (Aktualität, Qualität, Autorität, Zugang) werden direkt in diesem Command berechnet — siehe Formeln in `commands/score.md` → „4 weitere Dimensionen berechnen". Gesamtscore wie dort, Clusterzuweisung ebenfalls. Das Resultat in `$SESSION_DIR/ranked.json` schreiben.

### Schritt 7: LLM-Relevanz-Scoring

Den `relevance-scorer`-Agent in Batches von 10 Papers starten.
LLM-Scores ins Ranking einmischen. Top-N nach Modus wählen (quick=15, standard=25, deep=40).
Als `$SESSION_DIR/papers.json` speichern.

### Schritt 8: Ergebnisse anzeigen

Eine formatierte Tabelle mit Rang, Titel, Jahr, Score, Cluster und Quellmodul ausgeben.
Pfad des Session-Verzeichnisses melden.

Die Kontext-Datei `./literature_state.md` im Projekt-Ordner mit neuen Statistiken aktualisieren, falls akademischer Kontext vorliegt.
