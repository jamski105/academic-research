# academic-research

Modular academic research pipeline for Claude Code. Searches across 10+ academic databases, downloads PDFs via 6-tier resolution, extracts quotes, and manages citations — all from your terminal.

## Features

- **7-Phase Workflow**: Query generation → Modular search → Deduplication → 4D Ranking → PDF download → Quote extraction → Export
- **10+ Search Sources**: CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor (API) + Google Scholar, REPEC, OECD, Destatis (Browser)
- **HAN-Server Integration**: Access EBSCO, Springer, ProQuest via institutional proxy (Leibniz FH)
- **6-Tier PDF Resolution**: Unpaywall → CORE → Module OA → Direct URL → HAN-Browser (EBSCO/Springer/EZB) → ProQuest
- **Citation Manager**: Tags, notes, export (BibTeX), reading lists, search, merge
- **Literature Review Generator**: Auto-generate structured reviews from your research
- **Paper Recommender**: Co-citation analysis via Semantic Scholar
- **PDF Full-Text Search**: Local TF-IDF inverted index across all downloaded papers
- **Research History**: Browse and search past sessions
- **Browser Navigation Guides**: Pre-built guides for 8 databases to optimize Playwright agent efficiency

## Installation

```bash
# Install as Claude Code plugin (from GitHub)
claude plugin add <owner>/academic-research

# Or install from local directory (development)
claude --plugin-dir ./academic-research
```

## Quick Start

```bash
# 1. Install Python dependencies
/academic:setup

# 2. Set up your academic profile (optional)
/academic:context

# 3. Run your first research
/research "DevOps Governance in Large Enterprises"
```

## Commands

| Command | Description |
|---------|-------------|
| `/research "query"` | Run the full 7-phase research pipeline |
| `/academic:setup` | Install Python dependencies |
| `/academic:context` | Set up academic profile (university, citation style, language) |
| `/academic:history` | View past research sessions |
| `/academic:cite list` | List all collected papers |
| `/academic:cite export --format bibtex --output file` | Export bibliography |
| `/academic:review` | Generate a literature review draft |
| `/academic:recommend` | Get paper recommendations |
| `/academic:search-pdfs "query"` | Full-text search across PDFs |

## Research Modes

| Mode | Sources | Top N | Best For |
|------|---------|-------|----------|
| `--mode quick` | CrossRef, OpenAlex, Semantic Scholar | 15 | Known-item lookup, topic overview |
| `--mode standard` | All Tier 1 (6 API + 4 Browser) | 25 | Most research tasks |
| `--mode deep` | All tiers + HAN-Server | 40 | Systematic reviews |

## Search Modules

### Tier 1: Free, no authentication

| Module | Type | Description |
|--------|------|-------------|
| `crossref` | API | DOI registry, broad coverage |
| `openalex` | API | Open catalog of scholarly works |
| `semantic_scholar` | API | AI-powered search with citation graphs |
| `base` | API | Bielefeld Academic Search Engine, 400M+ docs |
| `econbiz` | API | ZBW economics/business search |
| `econstor` | API (OAI-PMH) | Open Access economics repository |
| `google_scholar` | Browser | Broad academic search |
| `repec` | Browser | Research Papers in Economics |
| `oecd` | Browser | OECD iLibrary policy research |
| `destatis` | Browser | German Federal Statistical Office |

### Tier 2: Requires HAN-Server login

| Module | Type | Description |
|--------|------|-------------|
| `ebsco` | Browser (HAN) | EBSCO databases |
| `springer` | Browser (HAN) | Springer Nature licensed content |
| `proquest` | Browser (HAN) | Dissertations and theses |
| `ezb` | Browser (HAN) | Electronic journal library |

## Examples

```bash
# Quick search with default settings
/research "machine learning software testing"

# Deep search with IEEE citation style
/research "DevOps Governance" --mode deep --style ieee

# Search specific modules only
/research "AI Ethics" --modules semantic_scholar,crossref,base

# Manage citations
/academic:cite tag paper_123 "important"
/academic:cite note paper_123 "Key reference for chapter 2"
/academic:cite export --format bibtex --output refs.bib

# Generate literature review from last session
/academic:review --style thematic

# Get paper recommendations
/academic:recommend
```

## Data Storage

All user data is stored locally in `~/.academic-research/`:

```
~/.academic-research/
├── config.local.md          # Academic profile
├── sessions/                # Research session data
│   └── <timestamp>/
│       ├── metadata.json    # Session metadata (query, mode, style)
│       ├── queries.json     # Expanded queries
│       ├── api_results.json # Raw search results
│       ├── deduped.json     # After deduplication
│       ├── ranked.json      # After 4D scoring
│       ├── papers.json      # Final paper selection (top N)
│       ├── pdf_status.json  # PDF download status per paper
│       ├── pdf_texts.json   # Extracted PDF text
│       ├── quotes.json      # Extracted quotes
│       ├── export.json      # Full export
│       ├── export.bib       # BibTeX export
│       ├── export.md        # Markdown report
│       └── pdfs/            # Downloaded PDFs
├── citations.bib            # Global BibTeX
├── annotations.json         # Tags and notes
├── fulltext_index.json      # PDF search index
└── venv/                    # Python virtual environment
```

## Architecture

```
/research "query"
    │
    ├── Phase 1: Setup (session dir, config, metadata)
    ├── Phase 2: Query Generation (Haiku agent)
    ├── Phase 3: Modular Search
    │   ├── 3A: API modules (parallel, Python)
    │   ├── 3B: Browser modules (Playwright MCP + guides)
    │   └── 3D: Dedup + Merge
    ├── Phase 4: 4D Ranking + Top-N Selection → papers.json
    ├── Phase 5: PDF Download (6-tier resolution)
    │   ├── Tier 1-4: Automated (pdf_resolver.py)
    │   ├── Tier 5: HAN → EBSCO/Springer/EZB
    │   └── Tier 6: HAN → ProQuest
    ├── Phase 6: Quote Extraction (Sonnet agents, batched)
    └── Phase 7: Export (JSON + BibTeX + Markdown) + Citation merge
```

## Dependencies

- **Claude Code** with Opus/Sonnet models
- **Python 3.10+** (auto-installed via `/academic:setup`)
- **Playwright MCP** (bundled — browser automation for Google Scholar etc.)
- **Python packages**: `httpx`, `PyPDF2` (auto-installed)

## License

MIT
