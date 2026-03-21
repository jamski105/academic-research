---
name: Source Quality Audit
description: This skill should be used when the user wants to evaluate the quality, balance, and adequacy of their literature base. Triggers on "Quellenqualitaet", "Quellen-Check", "Literaturqualitaet pruefen", "Source audit", "Quellenbewertung", "literature quality", "Quellenmix", "peer-reviewed Anteil", or when the user is unsure whether their sources are sufficient for submission.
---

# Source Quality Audit

Evaluate the overall quality, balance, recency, and diversity of the literature base for an academic paper. Score each dimension (0-100), identify weaknesses, and provide concrete recommendations for improvement.

## When This Skill Activates

- The user asks to evaluate their source quality or literature base
- The user is unsure whether their sources are adequate
- Pre-submission quality gate for literature
- After a literature search session, to assess the collected pool

## Memory Files

- Read `literature_state.md` for the current source inventory (total count, type breakdown, chapter assignments, identified gaps)
- Read `academic_context.md` for work type, discipline, research question, and citation style

## Scripts

Use `${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py` for source metadata analysis (venue authority scoring via `score_authority()`, recency scoring via `score_recency()`).

## Scoring Dimensions

Evaluate each dimension on a 0-100 scale.

### 1. Peer-Review Ratio (weight: 0.25)

Assess the proportion of peer-reviewed sources in the total literature base.

**Scoring:**
- 90-100: >70% peer-reviewed journal articles or conference papers
- 70-89: 50-70% peer-reviewed
- 50-69: 30-50% peer-reviewed
- 30-49: 15-30% peer-reviewed
- 0-29: <15% peer-reviewed

**Classification of source types:**
- Peer-reviewed: Journal articles (impact factor journals), peer-reviewed conference proceedings
- Semi-academic: Working papers, preprints, institutional reports, dissertations
- Non-academic: Websites, blog posts, news articles, company publications, Wikipedia

Flag if non-academic sources exceed 20% of total.

### 2. Recency (weight: 0.20)

Assess whether the literature base is current enough.

**Scoring:**
- 90-100: >60% of sources from the last 5 years, key sources current
- 70-89: >40% from last 5 years
- 50-69: >25% from last 5 years
- 30-49: Mostly older sources, few recent additions
- 0-29: Literature base is outdated

**Exceptions:**
- Foundational/seminal works are exempt from recency requirements (flag as "Grundlagenwerk")
- Historical or philosophical topics have relaxed recency expectations
- Methodological texts may be older without penalty

Use `score_recency()` from `${CLAUDE_PLUGIN_ROOT}/scripts/ranking.py` for per-source recency computation.

### 3. Source Diversity (weight: 0.20)

Assess whether the literature comes from varied perspectives and publication venues.

**Check for:**
- **Author diversity** -- Flag if more than 3 sources from the same author (over-reliance)
- **Venue diversity** -- Flag if more than 5 sources from the same journal or publisher
- **Geographic diversity** -- Flag if all sources come from one country or language
- **Perspective diversity** -- Flag if all sources support the same position (confirmation bias)
- **Type diversity** -- Mix of journals, books, conference papers, reports

**Scoring:**
- 90-100: Diverse across all sub-dimensions
- 70-89: Good diversity with minor concentration in one area
- 50-69: Notable concentration in 2+ sub-dimensions
- 30-49: Heavy reliance on narrow source pool
- 0-29: Almost all sources from same venue, author, or perspective

### 4. Web Source Proportion (weight: 0.15)

Assess the balance between web-only sources and traditional academic publications.

**Scoring:**
- 90-100: Web sources <10%, all with clear institutional backing
- 70-89: Web sources 10-20%, mostly institutional (Statista, government sites, NGOs)
- 50-69: Web sources 20-30%, some non-institutional
- 30-49: Web sources 30-50%, several unverifiable
- 0-29: Web sources >50%, many without institutional authority

**Acceptable web sources:** Government statistics (destatis.de), official reports (EU, OECD, WHO), established data providers (Statista), corporate annual reports.

**Problematic web sources:** Personal blogs, undated pages, pages without clear authorship, Wikipedia as primary source.

### 5. Topical Coverage (weight: 0.20)

Assess whether all major aspects of the research question are backed by literature.

**Procedure:**
1. Extract key concepts from the research question and outline (via `academic_context.md`)
2. Map each concept to available sources
3. Identify concepts with insufficient source coverage (<2 sources per key concept)
4. Check that each main chapter has adequate literature support

**Scoring:**
- 90-100: All key concepts covered by 3+ sources, no gaps
- 70-89: Most concepts covered, 1-2 minor gaps
- 50-69: Several concepts undercovered
- 30-49: Major gaps in central topics
- 0-29: Core research question insufficiently supported by literature

## Evaluation Workflow

1. Read `literature_state.md` for the source inventory
2. Read `academic_context.md` for research context
3. Classify each source by type (peer-reviewed, semi-academic, non-academic, web)
4. Score each of the 5 dimensions
5. Compute weighted total: `total = 0.25*peer_review + 0.20*recency + 0.20*diversity + 0.15*web_ratio + 0.20*coverage`
6. Generate specific recommendations for each dimension scoring below 70
7. Present results in structured format

## Output Format

```
## Quellen-Audit: [Work Title]

**Quellen gesamt:** [N] | **Typ:** [Work Type] | **Ziel:** [min required sources]

### Ergebnis-Uebersicht

| Dimension              | Score | Status         |
|------------------------|-------|----------------|
| Peer-Review-Anteil     | XX    | OK/WARN/FAIL   |
| Aktualitaet            | XX    | OK/WARN/FAIL   |
| Quellen-Diversitaet    | XX    | OK/WARN/FAIL   |
| Web-Quellen-Anteil     | XX    | OK/WARN/FAIL   |
| Thematische Abdeckung  | XX    | OK/WARN/FAIL   |
| **Gesamt**             | **XX**| **STATUS**     |

### Quellenverteilung
- Peer-reviewed Journals: [N] ([X%])
- Buecher/Monographien: [N] ([X%])
- Konferenzbeitraege: [N] ([X%])
- Berichte/Working Papers: [N] ([X%])
- Web-Quellen: [N] ([X%])
- Sonstige: [N] ([X%])

### Identifizierte Luecken
[List specific topic areas or concepts lacking source coverage]

### Empfehlungen
[Prioritized, actionable recommendations]
1. [Most critical action]
2. [Second priority]
...
```

Status thresholds: OK >= 70, WARN 50-69, FAIL < 50.

## Important Rules

- Base the audit on actual source data from `literature_state.md`, not assumptions
- If `literature_state.md` is incomplete, ask the user to provide their source list
- Use `score_authority()` from `ranking.py` for venue classification when metadata is available
- Never dismiss web sources categorically -- evaluate each on institutional authority
- Foundational works (e.g., Porter 1985, Rogers 2003) should be flagged as "Grundlagenwerk" and exempted from recency penalties
- Recommendations must be specific ("Add 2-3 peer-reviewed sources on [specific topic]") not generic ("Find more sources")
- Consider discipline norms: computer science values conference papers highly; business studies value journal articles; law values commentaries and court decisions
- Update `literature_state.md` with audit results and identified gaps
