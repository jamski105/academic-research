---
name: Advisor
description: This skill should be used when the user wants to build or refine their thesis outline, create an Expose, or plan chapter structure. Triggers on "Gliederung", "Outline", "Expose", "Exposé", "Struktur", "Kapitelplanung", "thesis structure", "chapter planning", "Aufbau der Arbeit", or when the user needs help organizing their academic work into a coherent structure.
---

# Advisor — Outline & Expose Builder

Build, refine, and validate thesis outlines and expose documents through interactive dialog. Guide the user from an initial topic to a structured, well-justified chapter plan.

## When This Skill Activates

- The user wants to create or revise a thesis outline (Gliederung)
- The user needs to write an expose or research proposal
- The user asks about chapter structure, ordering, or logical flow
- The user wants to plan which topics belong in which chapter

## Memory Files

### Read

- `academic_context.md` — Thesis profile, research question, methodology, existing outline
- `literature_state.md` — Available sources and chapter assignments (to verify literature coverage)

### Write

- `academic_context.md` — Update the `## Gliederung` section after outline changes

## Core Workflow

### 1. Load Context

Read `academic_context.md` from memory. If it does not exist, inform the user and trigger the Academic Context skill to gather baseline information before proceeding.

Extract: work type, topic, research question, sub-questions, methodology, and any existing outline.

### 2. Interactive Outline Dialog

If no outline exists, guide the user through building one. Ask focused questions:

1. **Scope** — What is the central argument or thesis statement?
2. **Main sections** — What are the 3-5 major topics the work must cover?
3. **Logical order** — Which concepts build on each other?
4. **Methodology placement** — Where does the methodology chapter fit?
5. **Depth** — How many sub-sections per chapter?

Present a draft outline after initial answers. Use numbered hierarchy (1. / 1.1 / 1.1.1). Include estimated page ranges per chapter based on work type:

| Work Type | Total Pages | Intro | Theory | Method | Analysis | Conclusion |
|-----------|-------------|-------|--------|--------|----------|------------|
| Bachelorarbeit | 40-60 | 3-5 | 12-18 | 5-8 | 12-18 | 3-5 |
| Masterarbeit | 60-100 | 5-8 | 20-30 | 8-15 | 20-30 | 5-8 |
| Hausarbeit | 15-25 | 2-3 | 5-8 | 3-5 | 5-8 | 2-3 |

### 3. Outline Validation

After the user accepts a draft, validate it against common academic standards:

- **Red thread** (roter Faden) — Does every chapter contribute to answering the research question?
- **Balance** — Are chapters roughly proportional? Flag chapters that are too thin or too heavy.
- **Completeness** — Are introduction, theoretical framework, methodology, analysis/results, and conclusion present?
- **Sub-question mapping** — Can each sub-question be traced to at least one chapter?
- **No orphans** — Does every chapter connect logically to its neighbors?

Report issues as warnings with suggested fixes.

### 4. Literature Availability Check

If `literature_state.md` exists, cross-reference the outline with available sources. For each chapter, report:

- Number of assigned sources
- Whether peer-reviewed sources are present
- Gaps where no literature is assigned

If gaps are found, offer to trigger `/search` for specific chapters with targeted queries derived from chapter titles and key concepts.

### 5. Expose Generation

When the user requests an expose, use the template at `${CLAUDE_PLUGIN_ROOT}/templates/expose-template.md` as the base structure. Fill in sections from the academic context and outline:

- Problemstellung (problem statement)
- Zielsetzung (objective)
- Forschungsfrage und Unterfragen (research question and sub-questions)
- Theoretischer Rahmen (theoretical framework)
- Methodik (methodology)
- Vorläufige Gliederung (preliminary outline)
- Zeitplan (timeline)
- Vorläufige Literaturliste (preliminary bibliography)

Generate the timeline based on the deadline from `academic_context.md`. Work backwards from the deadline, allocating roughly: 20% research, 10% outline/expose, 50% writing, 10% revision, 10% buffer.

### 6. Save Updates

After the user confirms the outline or expose:

1. Read `academic_context.md` again (prevent stale overwrites)
2. Update only the `## Gliederung` section with the new outline
3. Update `## Fortschritt` if applicable

## Outline Refinement

When an outline already exists and the user wants changes:

- **Add chapter** — Insert at the correct position, renumber subsequent chapters
- **Remove chapter** — Confirm with the user, check if literature was assigned
- **Reorder** — Show before/after comparison, validate red thread
- **Split/merge** — Suggest appropriate sub-section structure
- **Rename** — Update title, check if it still matches the content scope

Always show the full updated outline after changes and ask for confirmation.

## Important Rules

- **Never auto-generate an outline without dialog** — Always involve the user in structural decisions
- **Respect existing work** — When refining, preserve what works and suggest targeted changes
- **German chapter titles by default** — Match the thesis language from academic context
- **Show reasoning** — Explain why a particular structure is recommended
- **One change at a time** — When multiple issues are found, address them sequentially
- **Confirm before saving** — Always get explicit approval before writing to memory
