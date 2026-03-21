---
name: Academic Context
description: This skill should be used when the user discusses their thesis, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit, or academic work. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", or when another skill needs context that doesn't exist yet. Manages the persistent academic context in Claude Memory.
---

# Academic Context Manager

Maintain a persistent academic context that other skills rely on. This skill reads and writes Claude Memory files to track the user's thesis topic, outline, research question, methodology, progress, and key concepts.

## When This Skill Activates

- The user mentions their thesis, paper, or academic work
- The user provides or updates their research topic, outline, or research question
- Another skill needs academic context but none exists yet
- The user explicitly asks to update their academic profile

## Memory Files

All context is stored in Claude Memory at the project's memory directory. Three files are managed:

### `academic_context.md` — Primary context file

Contains thesis profile (university, program, citation style), work details (type, topic, research question, methodology, supervisor, deadline), outline structure, key concepts, and progress tracking.

### `literature_state.md` — Literature status

Contains statistics about collected sources (total count, peer-reviewed percentage, type breakdown), chapter-to-source assignment, and identified gaps.

### `writing_state.md` — Writing progress

Contains current chapter being written, word counts, and latest style evaluation scores.

## Core Workflow

### First Activation (No Context Exists)

When no `academic_context.md` exists in memory, gather the following through conversation:

1. **University and program** — Default: Leibniz FH Hannover, BWL/Wirtschaftsinformatik
2. **Work type** — Bachelorarbeit, Masterarbeit, Hausarbeit, Seminararbeit, Facharbeit
3. **Topic** — Working title of the thesis
4. **Research question** — Main question and sub-questions
5. **Methodology** — Literature review, case study, empirical, mixed methods
6. **Citation style** — Default: APA7 (also supports IEEE, Harvard, Chicago, MLA)
7. **Language** — Default: Deutsch
8. **Supervisor** — Name (optional)
9. **Deadline** — Submission date (optional)
10. **Outline** — Chapter structure if already planned

Write the gathered information to `academic_context.md` using this structure:

```markdown
---
name: academic-context
description: Akademischer Kontext der aktuellen Abschlussarbeit
type: project
---

## Profil
- Universität: [...]
- Studiengang: [...]
- Zitationsstil: [...]
- Sprache: [...]

## Arbeit
- Typ: [...]
- Thema: [...]
- Forschungsfrage: [...]
- Unterfragen: [...]
- Methodik: [...]
- Betreuer: [...]
- Abgabetermin: [...]

## Gliederung
[Numbered outline if available]

## Schlüsselkonzepte
[Key concepts with brief descriptions]

## Fortschritt
[Checklist of completed/in-progress items]
```

### Update Activation (Context Exists)

When context already exists, read the current `academic_context.md` from memory. Identify what changed based on the conversation and update only the relevant sections. Preserve all existing data that wasn't explicitly changed.

Common updates:
- **Outline changes** — User refined chapter structure
- **Progress updates** — User completed a chapter or section
- **New concepts** — User introduced new key terms
- **Research question refinement** — User sharpened the focus
- **Methodology decision** — User chose or changed approach

### Cross-Skill Support

When another skill (Citation Extraction, Literature Gap Analysis, Advisor, etc.) needs context:

1. Check if `academic_context.md` exists in memory
2. If yes — read and use it
3. If no — inform the user that context is needed and offer to set it up
4. After setup, return control to the requesting workflow

## Important Rules

- **Never overwrite without reading first** — Always read the current state before writing updates
- **Preserve user data** — Never delete information the user didn't explicitly ask to remove
- **Use German for field labels** — The context files use German labels matching the user's language
- **Date format** — Use ISO dates (YYYY-MM-DD) for deadlines and timestamps
- **Incremental updates** — Update only changed sections, not the entire file
- **Confirm major changes** — Before restructuring the outline or changing the research question, confirm with the user
