---
description: Search academic papers across multiple APIs (Semantic Scholar, CrossRef, OpenAlex, BASE, EconBiz, EconStor, arXiv)
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Agent
argument-hint: "<query>" [--mode quick|standard|deep|metadata] [--modules crossref,openalex,...] [--limit N]
---

# Academic Paper Search

Search across 7 API sources in parallel. Optionally expand queries with the query-generator agent.

## Usage

- `/academic-research:search "DevOps Governance"` — Standard search across all API modules
- `/academic-research:search "Machine Learning" --mode quick` — Fast search (4 modules)
- `/academic-research:search "IT Compliance" --mode deep` — Deep search (all modules + portfolio adjustments)
- `/academic-research:search "Cloud Computing" --modules crossref,semantic_scholar --limit 30`

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `query` | (required) | Search query |
| `--mode` | `standard` | quick (4 APIs), standard (7 APIs), deep (7 APIs + portfolio), metadata (no PDFs) |
| `--modules` | (from mode) | Override: comma-separated module names |
| `--limit` | `50` | Max results per module |
| `--no-expand` | false | Skip query-generator agent, use raw query |
| `--no-browser` | false | Skip browser modules (API-only) |

## Module Selection by Mode

- **quick**: crossref, openalex, semantic_scholar, arxiv
- **standard**: crossref, openalex, semantic_scholar, base, econbiz, econstor, arxiv
- **deep**: All 7 API modules + browser modules (Google Scholar, Springer, OECD, RePEc, OPAC)
- **metadata**: Same as standard

## Implementation

### Step 1: Setup session directory

```bash
SESSION_DIR=~/.academic-research/sessions/$(date -u +%Y-%m-%dT%H-%M-%SZ)
mkdir -p "$SESSION_DIR/pdfs"
```

Save metadata:
```json
{"query": "$QUERY", "mode": "$MODE", "timestamp": "$TIMESTAMP", "modules": [...]}
```

### Step 2: Query expansion (unless --no-expand)

Spawn the `query-generator` agent with the user's query and target modules.
Save output to `$SESSION_DIR/queries.json`.

### Step 3: API search

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/search.py \
  --query "$QUERY" \
  --modules "$MODULES" \
  --limit $LIMIT \
  --queries-file "$SESSION_DIR/queries.json" \
  --output "$SESSION_DIR/api_results.json"
```

### Step 4: Browser search (standard/deep modes, unless --no-browser)

For browser modules (google_scholar, springer, oecd, repec, opac), use Playwright MCP directly.
Read the corresponding browser guide from `${CLAUDE_PLUGIN_ROOT}/config/browser_guides/`.
Append results to `$SESSION_DIR/api_results.json`.

Order: no-auth modules first (Google Scholar → Springer → OECD), then auth modules (EBSCO → ProQuest → OPAC).

### Step 5: Deduplication

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/dedup.py \
  --papers "$SESSION_DIR/api_results.json" \
  --output "$SESSION_DIR/deduped.json"
```

### Step 6: Ranking (5D scoring + clusters)

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py \
  --papers "$SESSION_DIR/deduped.json" \
  --query "$QUERY" \
  --mode "$MODE" \
  --scoring-config "${CLAUDE_PLUGIN_ROOT}/config/scoring.yaml" \
  --output "$SESSION_DIR/ranked.json"
```

### Step 7: LLM relevance scoring

Spawn `relevance-scorer` agent in batches of 10 papers.
Merge LLM scores into ranking. Select top-N based on mode (quick=15, standard=25, deep=40).
Save as `$SESSION_DIR/papers.json`.

### Step 8: Show results

Display a formatted table with: rank, title, year, score, cluster, source module.
Report session directory path.

Update memory file `literature_state.md` with new statistics if academic context exists.
