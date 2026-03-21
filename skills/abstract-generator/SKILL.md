---
name: Abstract Generator
description: This skill should be used when the user needs an abstract, summary, management summary, or keyword list for their academic paper. Triggers on "Abstract schreiben", "Zusammenfassung", "Keywords", "Management Summary", "Abstract generieren", "paper summary", "Schlagwoerter", "executive summary", or when the paper is finished and needs front matter text.
---

# Abstract Generator

Read a finished or near-finished academic paper and generate structured abstracts, summaries, and keyword lists. Produce output variants appropriate for the work type and university requirements.

## When This Skill Activates

- The user asks for an abstract (German or English)
- The user needs a Management Summary or executive summary
- The user needs a keyword list
- The user asks for a Zusammenfassung for their paper

## Memory Files

- Read `academic_context.md` for university, work type, language, research question, methodology, and formal requirements
- Read `writing_state.md` for chapter completion status and key findings identified during writing

## Deliverables

Generate one or more of the following based on user request. If the user asks generically for "Abstract", produce all deliverables that are required for their work type.

### 1. Abstract (German)

**Structure (IMRAD-based):**

1. **Kontext** (1-2 sentences) -- Situate the research topic and its relevance
2. **Fragestellung** (1 sentence) -- State the research question
3. **Methodik** (1-2 sentences) -- Describe the research approach
4. **Ergebnisse** (2-3 sentences) -- Summarize the key findings
5. **Schlussfolgerung** (1-2 sentences) -- State the main implication or contribution

**Constraints:**
- Length: 150-250 words (or as specified in `academic_context.md`)
- No citations in the abstract
- No abbreviations not spelled out
- No references to specific chapters, figures, or tables
- Use present tense for established facts, past tense for own research actions
- Write in third person or impersonal constructions (German convention)

### 2. Abstract (English)

**Structure:** Same IMRAD structure as the German version.

**Additional constraints:**
- Must be an independent translation, not a word-for-word rendering
- Adapt phrasing to English academic conventions
- Verify that technical terms have correct English equivalents
- Length: Match the German abstract within 10%

### 3. Management Summary

**When required:** Typically for Bachelorarbeiten and Masterarbeiten in BWL, Wirtschaftsinformatik, and related programs.

**Structure:**

1. **Ausgangslage** (1 paragraph) -- Business context and problem
2. **Zielsetzung** (1-2 sentences) -- What the paper aims to achieve
3. **Vorgehen** (1 paragraph) -- Methodology in accessible language (minimize jargon)
4. **Kernergebnisse** (1-2 paragraphs) -- Main findings with practical implications
5. **Handlungsempfehlungen** (bullet points) -- Actionable recommendations for practitioners

**Constraints:**
- Length: 300-500 words
- Accessible to non-academic readers (e.g., company supervisors)
- Focus on practical value, not theoretical contribution
- No citations

### 4. Keywords List

Generate two keyword sets:

**German Keywords (Schlagwoerter):**
- 5-8 keywords
- Mix of broad discipline terms and specific topic terms
- Include methodology keywords if distinctive
- Order: broad to specific

**English Keywords:**
- 5-8 keywords (not literal translations -- use established English terminology)
- Include terms commonly used in international databases (Scopus, Web of Science)
- Consider search discoverability

## Generation Workflow

1. Read `academic_context.md` for formal requirements and context
2. Read the complete paper text (or all available chapters)
3. Identify: research question, methodology, key findings, main contribution, limitations, implications
4. Determine which deliverables to generate based on work type:
   - Bachelorarbeit/Masterarbeit: Abstract (DE), Abstract (EN), Management Summary, Keywords
   - Hausarbeit/Seminararbeit: Abstract (DE), Keywords
   - Facharbeit: Abstract (DE) only (short version, 100-150 words)
5. Draft each deliverable following the structure and constraints above
6. Cross-check: ensure the abstract accurately reflects the paper's actual content (not the intended content from the outline)
7. Present all deliverables in structured output

## Output Format

```
## Abstract & Zusammenfassung

### Abstract (Deutsch)
[Generated abstract text]

**Wortanzahl:** [N]

### Abstract (English)
[Generated abstract text]

**Word count:** [N]

### Management Summary
[Generated summary text]

**Wortanzahl:** [N]

### Keywords
**Deutsch:** [Keyword 1], [Keyword 2], ...
**English:** [Keyword 1], [Keyword 2], ...
```

## Quality Checks

Before presenting the output, verify:

- [ ] Abstract does not contain information absent from the paper
- [ ] Abstract does not omit major findings present in the paper
- [ ] No citations, figure references, or chapter references in abstract
- [ ] Word count within specified range
- [ ] German abstract uses appropriate academic register (no colloquialisms)
- [ ] English abstract uses correct English academic conventions (not Germanisms)
- [ ] Keywords are not too generic ("Management", "Unternehmen") or too narrow
- [ ] Management Summary is understandable without reading the paper

## Important Rules

- Always read the actual paper content before generating -- never generate abstracts from the outline alone if text is available
- If the paper is incomplete, generate a preliminary abstract and clearly mark it as provisional
- Respect the word count limits strictly -- universities often enforce these
- The abstract must stand alone as a self-contained text
- Never include personal opinions or evaluative language beyond what the paper itself claims
- If `academic_context.md` specifies additional requirements (e.g., structured abstract format), follow those over the defaults
