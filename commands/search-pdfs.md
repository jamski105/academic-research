---
description: Full-text search across all downloaded PDFs
allowed-tools: Read, Bash(~/.academic-research/venv/bin/python *)
argument-hint: [search query]
---

# PDF Full-Text Search

Search across all downloaded PDFs using the local full-text index.

## Usage

- `/academic-research:search-pdfs "machine learning"` — Search all PDFs
- `/academic-research:search-pdfs "governance" --limit 20` — Limit results

## Implementation

```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/fulltext_index.py \
  --action search --query "$ARGUMENTS" --limit 10
```

## Output Format

```
🔍 PDF Search: "machine learning"

Found 7 matches across 4 papers:

  1. Smith et al. (2023) — DevOps Governance Framework
     📄 Page 5: "...integrating machine learning models into the governance
        pipeline enables automated compliance checking..."
     Relevance: ★★★★☆

  2. Doe (2022) — AI-Driven Software Quality
     📄 Page 2: "...machine learning approaches have shown promise in
        predicting deployment failures..."
     📄 Page 8: "...our machine learning classifier achieved 92%
        accuracy on the test set..."
     Relevance: ★★★★★

Total: 7 matches in 4 papers
```

If the index doesn't exist yet, build it first:
```bash
~/.academic-research/venv/bin/python ${CLAUDE_PLUGIN_ROOT}/scripts/fulltext_index.py \
  --action index --pdf-dir ~/.academic-research/pdfs/
```
