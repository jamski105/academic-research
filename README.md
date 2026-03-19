# academic-research

Modular academic research pipeline for Claude Code. Searches across 14 academic databases, downloads PDFs via 6-tier resolution, extracts quotes, and manages citations — all from your terminal.

## Features

- **7-Phase Workflow**: Query generation → Modular search → Deduplication → 4D Ranking → PDF download → Quote extraction → Export
- **14 Search Sources**: CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor (API) + Google Scholar, RePEc, OECD, EBSCO, Springer, OPAC (Browser) + Destatis, ProQuest (disabled by default) — 12 active by default
- **Institutional Access**: OPAC library gateway + HAN proxy for licensed full-text (Springer e-books, ProQuest dissertations)
- **6-Tier PDF Resolution**: Automated API (Unpaywall → CORE → Module OA → Direct URL) + Browser fallback (EBSCO/Springer/EZB → ProQuest) — [extensible](docs/adding-browser-modules.md)
- **Citation Manager**: Tags, notes, export (BibTeX), reading lists, search, merge
- **Literature Review Generator**: Auto-generate structured reviews from your research
- **Paper Recommender**: Co-citation analysis via Semantic Scholar
- **PDF Full-Text Search**: Local TF-IDF inverted index across all downloaded papers
- **Research History**: Browse and search past sessions
- **Browser Navigation Guides**: Pre-built guides for 9 sources (8 databases + HAN login) to optimize Playwright agent efficiency

## Installation

```bash
# Install as Claude Code plugin
claude plugin install academic-research

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
| `/academic:setup` | Install Python dependencies ([Setup Guide](docs/setup-guide.md)) |
| `/academic:context` | Set up academic profile (university, citation style, language) |
| `/academic:cite` | Manage citations (list, search, export, add, tag, note) |
| `/academic:history` | View past research sessions |
| `/academic:review` | Generate a literature review draft |
| `/academic:recommend` | Get paper recommendations |
| `/academic:search-pdfs` | Full-text search across PDFs |

Full reference with all flags and syntax: [Command Reference](docs/command-reference.md)

## Research Modes

Four modes control search depth, source selection, and PDF handling. Use `--no-pdfs` with any mode to skip PDF download and quote extraction.

| Mode | Top N | Best For |
|------|-------|----------|
| `--mode quick` | 15 | Known-item lookup, topic overview |
| `--mode standard` | 25 | Most research tasks (default) |
| `--mode deep` | 40 | Systematic reviews |
| `--mode metadata` | 25 | Fast literature list without PDFs |

Details (source selection, time limits, flags): [Command Reference](docs/command-reference.md#research-modes)

## Examples

```bash
# Quick search with default settings
/research "machine learning software testing"

# Deep search with IEEE citation style
/research "DevOps Governance" --mode deep --style ieee

# Metadata-only (no PDF download, fast)
/research "Cloud Computing" --mode metadata

# Search specific modules only
/research "AI Ethics" --modules semantic_scholar,crossref,base

# Skip PDFs in any mode
/research "Governance Frameworks" --mode standard --no-pdfs

# Manage citations
/academic:cite tag paper_123 "important"
/academic:cite note paper_123 "Key reference for chapter 2"
/academic:cite export --format bibtex --output refs.bib

# Generate literature review from last session
/academic:review --style thematic

# Get paper recommendations
/academic:recommend
```

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup-guide.md) | System requirements, installation, Playwright MCP, troubleshooting |
| [Architecture](docs/ARCHITECTURE.md) | Technical architecture, data flow, and module registry |
| [Command Reference](docs/command-reference.md) | All commands, flags, and syntax |
| [Adding Browser Modules](docs/adding-browser-modules.md) | How to add new search sources |

## Dependencies

- **Claude Code** with Opus/Sonnet models
- **Python 3.10+** with `httpx`, `PyPDF2` — auto-installed via `/academic:setup`
- **Node.js 18+** — required for browser search modules (Google Scholar, EBSCO, Springer); API-only search works without it
- **Playwright MCP** — auto-installed via `npx` when Claude Code starts; Chromium browser installed by `/academic:setup`

For detailed system requirements, Playwright MCP explanation, and troubleshooting: [Setup Guide](docs/setup-guide.md)

## License

MIT
