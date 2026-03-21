---
name: Citation Extraction
description: This skill should be used when the user wants to extract, format, or manage citations and quotes from academic PDFs. Triggers on "Zitate finden", "zitieren", "Quellenarbeit", "Belege suchen", "citations", "Zitate extrahieren", "quote extraction", "Literaturverzeichnis", "bibliography", or when another skill identifies that citation data is needed for a chapter.
---

# Citation Extraction

Extract relevant quotes from academic PDFs, format citations in the required style, and organize citation data by chapter. Uses the quote-extractor agent for extraction and `citations.py` for formatting and export.

## When This Skill Activates

- The user wants to extract quotes or citations from downloaded PDFs
- The user needs to format a bibliography or reference list
- The user wants to find supporting evidence for a specific claim or chapter
- The user asks to organize citations by chapter or topic

## Memory Files

### Read

- `academic_context.md` — Outline structure, citation style, research question
- `literature_state.md` — Available sources, PDF download status, chapter assignments

### Write

- `literature_state.md` — Update citation counts and extraction status per source

## Prerequisites

If `academic_context.md` does not exist, inform the user and trigger the Academic Context skill first. Citation style must be known before formatting.

## Core Workflow

### 1. Identify Extraction Scope

Determine what the user needs:

- **Full extraction** — Process all downloaded PDFs in the session
- **Chapter-targeted** — Extract quotes relevant to a specific chapter
- **Source-targeted** — Extract from one or more specific papers
- **Topic-targeted** — Find quotes about a specific concept across all sources

### 2. Locate PDFs

Read `literature_state.md` to identify which papers have downloaded PDFs. PDFs are stored in session directories under `~/.academic-research/sessions/*/pdfs/`.

If the user references papers that have no PDFs, offer to trigger `/search` to find and download them.

### 3. Quote Extraction

For each PDF, spawn the `quote-extractor` agent (defined at `${CLAUDE_PLUGIN_ROOT}/agents/quote-extractor.md`). Provide:

```json
{
  "paper": {
    "title": "Paper Title",
    "doi": "10.xxxx/xxxxx",
    "pdf_text": "...extracted PDF text..."
  },
  "research_query": "derived from chapter title or user query",
  "max_quotes": 3,
  "max_words_per_quote": 25
}
```

When doing chapter-targeted extraction, derive the `research_query` from the chapter title and key concepts in the outline. Use the TOC structure from `academic_context.md` to match papers to chapters.

### 4. Quality Check

After extraction, review results:

- Discard quotes with `extraction_quality: "failed"`
- Flag papers with `possible_pdf_mismatch: true` for manual review
- Check that quotes are relevant to the target chapter/topic
- Remove duplicates across papers (same idea, different wording)

Present extracted quotes to the user grouped by source, showing:

- Quote text
- Page number (if available)
- Section of origin
- Relevance score
- Paper title and authors

### 5. Citation Formatting

Use `${CLAUDE_PLUGIN_ROOT}/scripts/citations.py` to format citations in the configured style.

#### Supported Styles

| Style | In-text Example | Use Case |
|-------|----------------|----------|
| APA7 | (Müller, 2023, S. 45) | Default, most German universities |
| IEEE | [1, p. 45] | Engineering, Computer Science |
| Harvard | (Müller 2023, p. 45) | Business, Social Sciences |
| Chicago | (Müller 2023, 45) | Humanities |

#### Format Commands

```bash
# Format all papers in a session
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py \
  --action format \
  --papers "$SESSION_DIR/papers.json" \
  --style apa7

# Export bibliography
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py \
  --action export \
  --session-dir "$SESSION_DIR" \
  --format bibtex,markdown

# Merge citations from multiple sessions
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py \
  --action merge \
  --session-dir "$SESSION_DIR"
```

### 6. Chapter Assignment

When quotes are extracted for a specific chapter:

1. Group quotes by relevance to chapter sub-sections
2. Suggest placement within the chapter structure
3. Identify which sub-sections still lack supporting evidence
4. If gaps are found, offer to search for additional literature

### 7. Update Literature State

After extraction and formatting:

1. Read `literature_state.md` (prevent stale overwrites)
2. Update per-source fields: quote count, extraction quality, assigned chapters
3. Update aggregate statistics: total quotes extracted, coverage percentage

## Gap Detection

During extraction, watch for these patterns:

- **Chapters with zero quotes** — Flag as needing literature
- **One-source chapters** — Flag as potentially under-supported
- **Missing counter-arguments** — If all quotes support the same position, suggest looking for opposing views
- **Outdated sources** — Flag quotes from sources older than 10 years unless they are seminal works

When gaps are detected, offer to trigger `/search` with targeted queries or trigger the Literature Gap Analysis skill for a comprehensive review.

## Export Formats

Support these output formats via `citations.py`:

- **BibTeX** — For LaTeX integration
- **Markdown** — For review and manual editing
- **JSON** — For programmatic use by other skills

## Important Rules

- **Never fabricate quotes** — Only use text extracted directly from PDFs
- **Preserve exact wording** — Quotes must be verbatim from the source
- **Include page numbers** — Always include page numbers when available
- **Respect citation style** — Use the style configured in academic context consistently
- **Flag mismatches** — If PDF content does not match the expected paper, report it
- **User confirms assignments** — Let the user approve chapter-to-quote assignments before saving
