---
description: Get paper recommendations based on your research history
allowed-tools: Read, Agent, Bash(~/.academic-research/venv/bin/python *), Bash(cat ~/.academic-research/*)
argument-hint: [optional: session ID]
---

# Paper Recommender

Recommend related papers based on your collected research using citation graph analysis.

## Usage

- `/academic-research:recommend` — Based on all sessions
- `/academic-research:recommend SESSION_ID` — Based on specific session

## Algorithm

1. Collect all DOIs from session(s)
2. For each DOI, query Semantic Scholar API:
   - `GET https://api.semanticscholar.org/graph/v1/paper/{paperId}/references?fields=title,authors,year,abstract,citationCount,openAccessPdf`
   - `GET https://api.semanticscholar.org/graph/v1/paper/{paperId}/citations?fields=title,authors,year,abstract,citationCount,openAccessPdf`
3. Find papers that are cited by OR cite multiple of your papers (co-citation analysis)
4. Filter out papers already in your collection
5. Rank by: co-citation count × citation count
6. Show top 10

## Output Format

```
🔮 Paper Recommendations

Based on XX papers from your research on "DevOps Governance":

  1. ⭐ "Title of Recommended Paper" (2024)
     Authors: Smith, J. et al.
     Citations: 156
     Reason: Cited by 4 of your papers, highly relevant
     DOI: 10.1109/...
     PDF: Available ✅

  2. "Another Recommended Paper" (2023)
     ...

💡 To add a paper to your collection:
   /academic-research:cite add 10.1109/...
```
