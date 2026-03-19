---
description: View past research sessions and their results
allowed-tools: Read, Bash(cat ~/.academic-research/*), Bash(ls ~/.academic-research/*), Bash(~/.academic-research/venv/bin/python *)
argument-hint: [optional: search query or date]
---

# Research History

View past research sessions stored in `~/.academic-research/sessions/`.

## Usage

- `/academic:history` — List all sessions
- `/academic:history "DevOps"` — Search sessions by query
- `/academic:history 2026-03-17` — Show specific session details
- `/academic:history stats` — Show aggregate statistics

## Implementation

1. Read session index: `cat ~/.academic-research/sessions/index.json`
2. If argument provided:
   - If it's a date → find session from that date, show details
   - If it's "stats" → show aggregate stats
   - Otherwise → search sessions by query text
3. Display results as formatted table:

```
📚 Research History

| # | Date       | Query                  | Papers | PDFs  | Mode     |
|---|------------|------------------------|--------|-------|----------|
| 1 | 2026-03-17 | DevOps Governance      | 47     | 42/47 | standard |
| 2 | 2026-03-15 | AI Ethics              | 32     | 28/32 | deep     |
| 3 | 2026-03-10 | ML in Healthcare       | 25     | 20/25 | quick    |

Total: 3 sessions, 104 papers, 90 PDFs
```

For detail view, show: papers list, quote count, module breakdown, file locations.
