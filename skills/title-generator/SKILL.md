---
name: Title Generator
description: This skill should be used when the user needs title suggestions for their academic paper. Triggers on "Titel suchen", "Titelvorschlaege", "Arbeitstitel", "title suggestions", "Titel finden", "paper title", "Ueberschrift", or when the user has finished writing and needs a final title.
---

# Title Generator

Analyze a finished or near-finished academic paper and generate 5-7 title options with rationale. Provide a mix of academic, creative, and descriptive variants tailored to the discipline and work type.

## When This Skill Activates

- The user asks for title suggestions or wants to change their working title
- The user has completed a draft and needs a final title
- The user is brainstorming thesis titles during the planning phase

## Memory Files

- Read `academic_context.md` for work type, discipline, research question, methodology, language, and university requirements
- Read `writing_state.md` for completed chapters and key arguments identified during writing

## Analysis Phase

Before generating titles, analyze the paper along these dimensions:

### 1. Content Structure

- Identify the central argument or thesis statement
- Extract the main theoretical framework or model
- Note the scope (single case study, comparative, industry-wide)
- Identify the dependent and independent variables or key concepts

### 2. Key Arguments

- Extract the 3-5 strongest claims made in the paper
- Identify the most novel contribution or finding
- Note any unexpected results or contrarian positions

### 3. Methodology Signature

- Identify the research approach (qualitative, quantitative, mixed, literature review)
- Note specific methods that distinguish the work (e.g., Delphi method, SLR, grounded theory)
- Check if the methodology itself is noteworthy enough for the title

### 4. Keywords and Terminology

- Extract domain-specific keywords from the paper
- Identify the most frequently used technical terms
- Note any coined terms or framework names

## Title Generation

Generate exactly 5-7 title options across these categories:

### Category A: Classic Academic (2 titles)

Structure: `[Topic]: [Subtitle with scope/method]`

Characteristics:
- Formal, descriptive, unambiguous
- Contains the core topic and methodology or scope
- Typical for German Abschlussarbeiten
- Example pattern: "Digitale Transformation im Mittelstand: Eine qualitative Analyse der Erfolgsfaktoren"

### Category B: Question-Based (1-2 titles)

Structure: Title formulated as the research question or a provocative question.

Characteristics:
- Engages the reader immediately
- Reflects the research question from `academic_context.md`
- Appropriate for exploratory or argumentative work

### Category C: Conceptual / Creative (1-2 titles)

Structure: Short, memorable phrase with academic subtitle.

Characteristics:
- Uses a metaphor, paradox, or striking phrase
- Always paired with a clarifying subtitle
- More common in social sciences and humanities
- Must remain professionally appropriate

### Category D: Result-Oriented (1 title)

Structure: Title that hints at or states the main finding.

Characteristics:
- Previews the conclusion
- Appropriate when the finding is strong and clear
- Less common in German academic tradition but increasingly accepted

## Output Format

Present each title with:

```
## Titelvorschlaege

### 1. [Title] — Kategorie: Klassisch-Akademisch
**Rationale:** [Why this title works -- what it emphasizes, how it positions the work]
**Staerke:** [Key advantage]
**Einschraenkung:** [Potential drawback or limitation]

### 2. [Title] — Kategorie: ...
...

---

**Empfehlung:** [Which title best fits the work type and university context, with brief justification]
```

## Title Quality Criteria

Verify each generated title against:

- **Accuracy** -- Does the title faithfully represent the paper's content?
- **Specificity** -- Is the scope clear (not too broad, not too narrow)?
- **Searchability** -- Does it contain keywords that aid discoverability?
- **Length** -- Aim for 8-15 words (including subtitle); flag if exceeding 20
- **Convention** -- Does it match typical title patterns for the work type and discipline?
- **Language** -- Match the paper's language; if German paper, generate German titles (optionally add one English variant)

## Important Rules

- Read the actual paper content before generating titles -- never generate titles from the outline alone if text is available
- Respect the language specified in `academic_context.md`
- Never suggest clickbait or sensationalist phrasing
- Avoid titles that overstate the findings
- Include the recommendation with reasoning tied to the specific university and work type
- If no paper text is available yet, generate preliminary titles from the outline and research question, and mark them as provisional
