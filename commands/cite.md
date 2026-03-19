---
description: Manage citations, tags, notes, and export bibliography
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *)
argument-hint: [action: list|search|export|add|tag|note]
---

# Citation Manager

Manage your collected academic citations across all research sessions.

## Usage

- `/academic-research:cite list` — List all papers
- `/academic-research:cite list --tag important` — Filter by tag
- `/academic-research:cite list --status unread` — Filter by reading status
- `/academic-research:cite search "keyword"` — Search through citations
- `/academic-research:cite export --format bibtex` — Export bibliography
- `/academic-research:cite add DOI` — Manually add a paper by DOI
- `/academic-research:cite tag PAPER_ID "important"` — Add tag to paper
- `/academic-research:cite note PAPER_ID "Interesting approach for chapter 3"` — Add note

## Implementation

Run the citation manager script:
```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/citation_manager.py \
  --action $ACTION [--doi DOI] [--tag TAG] [--note "NOTE"] [--format FORMAT] [--output FILE]
```

### Actions:

**list**: Show all papers with tags/notes
```
📚 Citations (47 papers)

  1. Smith et al. (2023) — DevOps Governance Framework
     DOI: 10.1109/ICSE.2023.00042
     Tags: [important] [read]
     Note: "Key reference for chapter 2"

  2. Doe & Johnson (2022) — CI/CD Compliance...
```

**search**: Full-text search across titles, abstracts, notes

**export**: Generate formatted bibliography
- `--format bibtex` → .bib file
- `--format apa7` → formatted APA text
- `--format ieee` → formatted IEEE text

**add**: Look up DOI via CrossRef/OpenAlex, add to citations

**tag**: Assign tags (important, read, unread, todo, questionable, etc.)

**note**: Attach free-text notes to papers

Storage files:
- `~/.academic-research/citations.bib` — Global BibTeX
- `~/.academic-research/annotations.json` — Tags + notes
