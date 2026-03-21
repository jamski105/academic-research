---
name: Literature Gap Analysis
description: This skill should be used when the user wants to analyze literature coverage, find missing sources, or identify gaps in their research base. Triggers on "Literaturlücken", "Coverage", "fehlende Quellen", "Gap Analysis", "Quellenabdeckung", "literature gaps", "missing sources", "Abdeckung prüfen", or when another skill detects that chapters lack sufficient source support.
---

# Literature Gap Analysis

Analyze the thesis outline against the existing literature collection to produce a per-chapter coverage report. Identify well-covered topics, missing sources, missing counter-arguments, and methodological gaps. Offer targeted search to fill gaps.

## When This Skill Activates

- The user asks to check literature coverage or completeness
- The user wants to know which chapters need more sources
- Another skill (Advisor, Chapter Writer, Citation Extraction) flags insufficient sources
- The user is preparing for a supervisor meeting and wants a status overview

## Memory Files

### Read

- `academic_context.md` — Outline structure, research question, sub-questions, key concepts
- `literature_state.md` — Source inventory, chapter assignments, PDF status, citation counts

### Write

- `literature_state.md` — Update gap analysis results and coverage scores

## Prerequisites

Both `academic_context.md` (with an outline) and `literature_state.md` (with at least some sources) must exist. If either is missing:

- No academic context — trigger the Academic Context skill
- No literature state — suggest running `/search` first to build a source base

## Core Workflow

### 1. Load and Cross-Reference

Read both memory files. Build a matrix:

- **Rows** — Chapters and sub-sections from the outline
- **Columns** — Coverage dimensions (see below)

### 2. Coverage Dimensions

Evaluate each chapter along these dimensions:

#### Source Count
- 0 sources — CRITICAL: no coverage
- 1-2 sources — WARNING: thin coverage
- 3-5 sources — OK for sub-sections
- 5+ sources — Good for main chapters

#### Source Quality
- Percentage of peer-reviewed sources per chapter
- Presence of seminal/foundational works
- Recency — percentage of sources from the last 5 years
- Source diversity — multiple authors, not just one research group

#### Argument Balance
- Are supporting AND opposing viewpoints represented?
- Are alternative theories or frameworks mentioned?
- Is there at least one source that challenges the main argument?

#### Methodological Alignment
- Do methodology chapters reference established method literature?
- Is the chosen method justified by cited precedents?
- Are limitations of the method discussed with source support?

### 3. Generate Coverage Report

Produce a structured report with the following format:

```
## Literatur-Coverage-Report

### Gesamtbewertung
- Quellen gesamt: [N]
- Peer-reviewed: [N]%
- Durchschnittsalter: [N] Jahre
- Kapitel ohne Quellen: [N]
- Gesamtabdeckung: [SCORE]%

### Kapitelweise Analyse

#### [Chapter Title]
- Zugewiesene Quellen: [N]
- Peer-reviewed: [N]%
- Status: [KRITISCH / LÜCKE / AUSREICHEND / GUT]
- Fehlend: [specific gap description]
- Empfehlung: [targeted action]
```

### 4. Gap Classification

Classify each identified gap:

| Gap Type | Description | Priority |
|----------|-------------|----------|
| CRITICAL | Chapter has zero sources | Immediate |
| STRUCTURAL | Missing foundational/seminal work | High |
| BALANCE | No counter-arguments or alternative views | High |
| RECENCY | All sources older than 5 years | Medium |
| DEPTH | Too few sources for chapter scope | Medium |
| DIVERSITY | All sources from same author/group | Low |

### 5. Search Recommendations

For each gap, generate a targeted search recommendation:

- **Search query** — Derived from chapter title, key concepts, and gap type
- **Suggested modules** — Which search modules are most likely to yield results
- **Suggested mode** — quick for minor gaps, deep for critical gaps
- **Expected source type** — Journal article, conference paper, book chapter, report

Example:
```
GAP: Kapitel 3.2 "DevOps Governance Modelle" — keine Gegenargumente
QUERY: "DevOps governance challenges limitations criticism"
MODULE: semantic_scholar, crossref
MODE: standard
EXPECTED: Journal articles discussing governance limitations
```

### 6. Automated Gap Filling

When the user approves, trigger `/search` for each gap with the recommended queries. After search completes:

1. Review new results against the gap requirements
2. Suggest chapter assignments for new sources
3. Update the coverage report
4. Re-evaluate coverage scores

### 7. Update Literature State

After analysis:

1. Read `literature_state.md` (prevent stale overwrites)
2. Write gap analysis results: per-chapter coverage scores, identified gaps, recommendations
3. Update timestamp of last analysis

## Comparison with Similar Works

When evaluating completeness, consider:

- **Standard references** — Are commonly cited foundational works in the field present?
- **Recent surveys** — Has the user included recent literature reviews or meta-analyses?
- **Methodological references** — Are standard methodology textbooks cited?
- **Institutional requirements** — Does the source count meet the minimum expected for the work type?

Typical minimums by work type:

| Work Type | Minimum Sources | Peer-reviewed Minimum |
|-----------|-----------------|-----------------------|
| Bachelorarbeit | 25-35 | 60% |
| Masterarbeit | 40-60 | 70% |
| Hausarbeit | 10-20 | 50% |

## Important Rules

- **Report facts, not judgments** — Present coverage data objectively; let the user decide priorities
- **Suggest, do not auto-execute** — Always ask before triggering searches for gaps
- **Acknowledge limitations** — Gap analysis depends on correct chapter assignments in literature state
- **Re-run after changes** — Suggest re-running analysis after new literature is added
- **No false positives** — Only flag gaps where the outline clearly requires source support
