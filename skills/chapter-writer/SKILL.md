---
name: Chapter Writer
description: This skill should be used when the user wants to write, draft, or compose a thesis chapter or section. Triggers on "Kapitel schreiben", "verfassen", "entwerfen", "Abschnitt schreiben", "write chapter", "draft section", "Kapitel formulieren", "Textarbeit", or when the user asks for help composing academic prose for a specific part of their work.
---

# Chapter Writer

Draft individual thesis chapters and sections using the research context, outline, available literature, and citations. Produce academic prose that the user reviews, edits, and approves section by section.

## When This Skill Activates

- The user wants to write or draft a specific chapter or section
- The user asks for help formulating academic text for their thesis
- The user wants to expand bullet points or notes into full prose
- The user needs help with transitions between sections

## Memory Files

### Read

- `academic_context.md` — Thesis profile, research question, outline, key concepts
- `literature_state.md` — Available sources, chapter-to-source assignments
- `writing_state.md` — Current writing progress, word counts, style scores

### Write

- `writing_state.md` — Update word counts, current chapter, and progress after writing

## Core Workflow

### 1. Load Context

Read all three memory files. If `academic_context.md` does not exist, inform the user and trigger the Academic Context skill first. If no outline exists, suggest triggering the Advisor skill to create one before writing.

Extract: target chapter from the outline, assigned sources from literature state, citation style, thesis language, and any existing drafts.

### 2. Identify Target Chapter

Ask the user which chapter or section to write if not already clear. Confirm:

- Chapter number and title from the outline
- Scope — What should this chapter accomplish?
- Available sources assigned to this chapter
- Expected length (page estimate from outline)

### 3. Chapter Planning

Before writing, create a brief internal plan:

1. **Section breakdown** — Sub-sections with 2-3 sentence descriptions of content
2. **Source mapping** — Which sources support which sections
3. **Argument flow** — How the chapter builds toward its contribution to the research question
4. **Key definitions** — Terms that need to be introduced or referenced

Present the plan to the user for approval before drafting.

### 4. Drafting

Write the chapter section by section. For each section:

1. Draft the text in the thesis language (default: German)
2. Embed in-text citations using the configured citation style (default: APA7)
3. Use formal academic register — no colloquialisms, no first person unless methodology requires it
4. Connect to the research question explicitly where appropriate
5. Present the draft to the user for review

#### Writing Guidelines

- **Paragraph structure** — Topic sentence, elaboration, evidence, synthesis
- **Citation density** — At least one citation per substantive claim in theory chapters; less in methodology/analysis
- **Transitions** — Each section ends with a bridge to the next
- **Hedging language** — Use appropriate hedging for claims ("suggests", "indicates", "according to")
- **No filler** — Every sentence must contribute to the argument

#### Source Integration

When citing sources, use the citation data from `${CLAUDE_PLUGIN_ROOT}/scripts/citations.py` output. Reference papers by their formatted citation. Support these integration patterns:

- **Direct quote** — Exact wording in quotation marks with page number
- **Paraphrase** — Restate in own words with citation
- **Summary** — Condense a source's argument with citation
- **Synthesis** — Combine multiple sources to support a point

### 5. User Review Cycle

After presenting each section draft:

- Wait for user feedback before proceeding
- Accept edits, rewrites, or approval
- Incorporate feedback into the next section
- Never proceed to the next section without user confirmation

If the user provides their own notes or bullet points, expand them into academic prose while preserving the user's intended meaning.

### 6. Chapter Assembly

After all sections are reviewed and approved:

1. Combine sections into the complete chapter
2. Check internal consistency (terminology, argument flow)
3. Verify all citations are present and correctly formatted
4. Add chapter introduction (if not the thesis introduction) and chapter summary
5. Report final word count

### 7. Update Writing State

After the user approves the chapter:

1. Read `writing_state.md` (prevent stale overwrites)
2. Update current chapter, word count, and progress status
3. Mark the chapter as "draft complete" in progress tracking

## Special Chapter Types

### Introduction (Einleitung)

Follow this structure: topic relevance, problem statement, research question, methodology overview, outline preview. Write last or revise after all other chapters are done.

### Theoretical Framework (Theoretischer Rahmen)

Heavy citation density. Define all key concepts. Compare perspectives from different authors. Build toward the analytical framework used later.

### Methodology (Methodik)

Justify the chosen approach. Describe data collection and analysis methods. Address limitations. Reference methodology literature.

### Analysis / Results (Analyse / Ergebnisse)

Apply the theoretical framework to the data. Present findings structured by sub-questions or themes. Use evidence from primary or secondary sources.

### Conclusion (Fazit)

Summarize findings per sub-question. Answer the main research question. Discuss limitations and future research. No new sources.

## Important Rules

- **Never write without user review** — Present each section for feedback before continuing
- **Never fabricate citations** — Only use sources that exist in the literature state
- **Preserve user voice** — When the user provides notes, respect their phrasing and intent
- **Match thesis language** — Write in the language specified in academic context
- **Track progress** — Always update writing_state.md after approved drafts
- **Flag gaps** — If a section needs a source that is not available, flag it and offer to trigger `/search`
