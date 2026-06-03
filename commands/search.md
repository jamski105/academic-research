---
description: Search academic papers across multiple APIs (Semantic Scholar, CrossRef, OpenAlex, BASE, EconBiz, EconStor, arXiv)
disable-model-invocation: true
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Bash(browser-use:*), Bash(browser-use *), Agent(query-generator, relevance-scorer, quote-extractor)
argument-hint: "<query>" [--mode quick|standard|deep|metadata] [--modules crossref,openalex,...] [--limit N] [--batch] [--interactive]
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
| `--batch` | false | Bei ≥50 Paper: relevance-scorer-Calls als Anthropic Message-Batches-API ausführen (50 % Discount, ~1 h Latenz). Job-ID in `$SESSION_DIR/batch.json` speichern. |
| `--interactive` | `off` | Two-Phase Research Mode: Phase 1 zeigt Query-Expansion + Top-5-10-Treffer-Preview, dann Approval-Gate. `--interactive=off` (default) verhält sich wie bisher. |

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

### Schritt 7: PRISMA-Zähler speichern

```bash
~/.academic-research/venv/bin/python -c "
import json, sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from search import build_prisma_counters, save_prisma_counters
counters = build_prisma_counters(
    n_identified=${N_IDENTIFIED},
    n_after_dedup=${N_AFTER_DEDUP},
    n_excluded_screening=${N_EXCLUDED_SCREENING},
    n_excluded_eligibility=${N_EXCLUDED_ELIGIBILITY},
    n_included=${N_INCLUDED},
)
save_prisma_counters('$SESSION_DIR', counters)
"
```

Die Zähler werden in `$SESSION_DIR/prisma_counters.json` gespeichert.

### Schritt 8: Relevanz-Scoring (Standard vs. Batch)

**Standard (< 50 Paper oder kein `--batch`):**  
Den `relevance-scorer`-Agent in Batches von 10 Papers starten.
LLM-Scores ins Ranking einmischen. Top-N nach Modus wählen (quick=15, standard=25, deep=40).
Als `$SESSION_DIR/papers.json` speichern.

**Batch-Modus (`--batch` und ≥ 50 Paper):**

```bash
~/.academic-research/venv/bin/python -c "
import json, sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from batch_api import submit_batch, save_batch_job
papers = json.load(open('$SESSION_DIR/ranked.json'))
job = submit_batch(papers, query='$QUERY')
save_batch_job('$SESSION_DIR', job)
print('Batch-Job eingereicht:', job['batch_id'])
print('Abholung via: /history --batch', job['batch_id'])
"
```

Job-ID wird in `$SESSION_DIR/batch.json` gespeichert. Abholung über
`/history --batch <id>` (sobald Batch-Status `ended` ist, ca. 1 h).

### Schritt 9: Interactive Mode — Phase 1 (nur bei `--interactive`)

Falls `--interactive=off` (Standard): diesen Schritt überspringen.

Bei `--interactive`:

```bash
~/.academic-research/venv/bin/python -c "
import json, sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts')
from search import run_interactive_phase1
papers = json.load(open('$SESSION_DIR/ranked.json'))
preview = run_interactive_phase1(papers, query='$QUERY', n_preview=5)
print(json.dumps(preview, ensure_ascii=False, indent=2))
"
```

Die Top-5-10-Treffer als formatierte Tabelle anzeigen, dann
**Approval-Gate via `AskUserQuestion`**:

Optionen:
1. **Weiter** — Phase 2 starten (Deep-Investigation)
2. **Anders formulieren** — neue Query eingeben und ab Schritt 2 wiederholen
3. **Mehr Quellen** — zusätzliche Module hinzufügen und ab Schritt 3 wiederholen
4. **Modul-Wahl ändern** — andere API-Module wählen und ab Schritt 3 wiederholen

Bei "Weiter": Phase 2 (Deep-Investigation) starten = vollständiges Scoring + Kapitelplanung.

### Schritt 10: Ergebnisse anzeigen

Eine formatierte Tabelle mit Rang, Titel, Jahr, Score, Cluster und Quellmodul ausgeben.
Pfad des Session-Verzeichnisses melden.

Die Kontext-Datei `./literature_state.md` im Projekt-Ordner mit neuen Statistiken aktualisieren, falls akademischer Kontext vorliegt.
