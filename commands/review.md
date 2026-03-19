---
description: Generate a literature review draft from research sessions
allowed-tools: Read, Write, Agent, Bash(~/.academic-research/venv/bin/python *), Bash(cat ~/.academic-research/*), Bash(ls ~/.academic-research/*)
argument-hint: [optional: session ID or --sessions "id1,id2"]
---

# Literature Review Generator

Generate a structured literature review draft from one or more research sessions.

## Usage

- `/academic:review` — Generate from most recent session
- `/academic:review SESSION_ID` — From specific session
- `/academic:review --sessions "2026-03-17,2026-03-15"` — Combine multiple sessions
- `/academic:review --style narrative|systematic|thematic` — Review style (default: narrative)

## Implementation

1. Load session data (papers, quotes, query) from session directory
2. Load citation style from config
3. Spawn `review-writer` agent (Opus) with:
   - All papers + their quotes
   - Research query
   - Review style
   - Citation style
   - Output language
4. Save generated review to session directory as `literature_review.md`
5. Show the review to the user

## Agent Prompt

```
IGNORE ALL PRIOR CONVERSATION CONTEXT.
You are a focused subagent with ONE task: writing a literature review.
Read ${CLAUDE_PLUGIN_ROOT}/agents/review-writer.md and follow it exactly.

Input data:
{
  "research_query": "...",
  "papers": [...],
  "review_style": "narrative",
  "citation_style": "apa7",
  "language": "deutsch"
}
```
