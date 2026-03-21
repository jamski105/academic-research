---
name: Research Question Refiner
description: This skill should be used when the user wants to formulate, sharpen, or evaluate their research question. Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung", "Forschungsfrage", "Forschungsfrage schärfen", "research question refine", "Fragestellung präzisieren", or when another skill identifies that the research question is too broad, too narrow, or not answerable.
---

# Research Question Refiner

Help precision-craft the main research question and sub-questions. Evaluate whether a question is too broad, too narrow, or unanswerable. Compare with similar works to ensure originality and feasibility.

## When This Skill Activates

- The user wants to formulate a new research question
- The user wants to refine or sharpen an existing research question
- The user is unsure if their question is good enough
- A supervisor has flagged the research question as problematic
- Another skill (Advisor, Academic Context) identifies a weak research question

## Memory Files

### Read

- `academic_context.md` — Current research question, topic, work type, methodology, outline

### Write

- `academic_context.md` — Update the research question and sub-questions after refinement

## Core Workflow

### 1. Load Context

Read `academic_context.md`. If it does not exist, trigger the Academic Context skill to gather baseline information. Extract: topic, current research question (if any), sub-questions, work type, and methodology.

### 2. Assess Current Question

If a research question already exists, evaluate it against these criteria:

#### Specificity
- **Too broad:** "How does digitalization affect companies?" — Cannot be answered in one thesis
- **Too narrow:** "How did Company X's Q3 2024 cloud migration affect ticket count?" — Too specific to generalize
- **Good:** "How does cloud migration affect IT service management processes in mid-sized German companies?"

#### Answerability
- Can the question be answered with the chosen methodology?
- Is the required data accessible?
- Is the scope realistic for the work type and timeline?

#### Relevance
- Does the question address a real gap in the literature?
- Is the answer useful for academia or practice?
- Does the topic have sufficient existing literature to build on?

#### Structure
- Is it a single, clear question (not a compound question)?
- Does it avoid yes/no answers (open-ended)?
- Does it contain the key variables or concepts?

Present the assessment with a score per criterion:

```
## Bewertung der Forschungsfrage

Aktuelle Frage: "[...]"

| Kriterium | Bewertung | Kommentar |
|-----------|-----------|-----------|
| Spezifität | [gut/zu breit/zu eng] | [...] |
| Beantwortbarkeit | [ja/eingeschränkt/nein] | [...] |
| Relevanz | [hoch/mittel/gering] | [...] |
| Struktur | [gut/verbesserbar] | [...] |
```

### 3. Refinement Dialog

Based on the assessment, guide the user through targeted improvements:

#### If Too Broad
- Add constraints: time period, geography, industry, company size
- Narrow the phenomenon: instead of "digitalization," specify "cloud migration" or "AI adoption"
- Focus on a specific relationship between variables
- Propose 2-3 narrower alternatives

#### If Too Narrow
- Remove overly specific constraints
- Generalize from a single case to a category
- Broaden the context while keeping the core phenomenon
- Propose 2-3 broader alternatives

#### If Not Answerable
- Adjust to match available data and methods
- Reframe from causal ("Why does...") to descriptive ("How does...") if causal evidence is not obtainable
- Break into answerable sub-questions
- Suggest alternative approaches

#### If Structurally Weak
- Rewrite as an open-ended question
- Separate compound questions into main + sub-questions
- Ensure key concepts are named explicitly
- Remove ambiguous terms

### 4. Sub-Question Development

After the main question is refined, develop 2-4 sub-questions that:

1. **Decompose** the main question into manageable parts
2. **Map to chapters** — Each sub-question corresponds to a section of the thesis
3. **Build on each other** — Sub-questions follow a logical sequence
4. **Cover the scope** — Together, answering all sub-questions answers the main question

Present the sub-question structure:

```
Hauptfrage: [Main Research Question]

Unterfragen:
1. [Sub-question 1] → Kapitel [N]: [Chapter Title]
2. [Sub-question 2] → Kapitel [N]: [Chapter Title]
3. [Sub-question 3] → Kapitel [N]: [Chapter Title]
```

### 5. Comparison with Similar Works

Search for existing research with similar questions to evaluate:

- **Originality** — Has this exact question been answered already? If yes, what angle makes this work unique?
- **Feasibility** — Have others successfully answered similar questions with comparable methods?
- **Positioning** — Where does this question fit in the field? What does it add?

If the question overlaps significantly with published work, suggest differentiators:
- Different context (industry, country, time period)
- Different methodology
- Different theoretical lens
- Extended scope (adding variables or perspectives)

### 6. Final Formulation

Present the refined research question and sub-questions for user approval. Include:

- The final main question
- 2-4 sub-questions with chapter mapping
- Brief justification of why this formulation works
- Comparison with the original question (if one existed)

### 7. Save Updates

After the user confirms:

1. Read `academic_context.md` (prevent stale overwrites)
2. Update `Forschungsfrage` with the new main question
3. Update `Unterfragen` with the new sub-questions
4. If sub-questions map to chapters, update the `## Gliederung` section accordingly

## Research Question Templates

Provide these templates as starting points when the user has no question yet:

| Template | Example |
|----------|---------|
| Explorative | "Welche Faktoren beeinflussen [Phänomen] in [Kontext]?" |
| Deskriptive | "Wie ist [Phänomen] in [Kontext] gestaltet?" |
| Kausale | "Welchen Einfluss hat [Variable A] auf [Variable B] in [Kontext]?" |
| Evaluative | "Wie effektiv ist [Maßnahme] zur [Zielsetzung] in [Kontext]?" |
| Gestaltungsorientierte | "Wie kann [Artefakt] zur [Zielsetzung] in [Kontext] gestaltet werden?" |

## Important Rules

- **Never impose a question** — Guide the user to their own formulation
- **Show alternatives** — Always present 2-3 options, not just one
- **Be honest about weaknesses** — If a question is problematic, explain why clearly
- **Respect the user's topic** — Refine within their chosen domain, do not redirect to a different topic
- **Connect to methodology** — Ensure the refined question is answerable with the chosen or available methods
- **Confirm before saving** — Always get explicit approval before updating memory files
