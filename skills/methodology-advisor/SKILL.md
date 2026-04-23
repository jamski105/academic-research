---
name: Methodology Advisor
description: This skill should be used when the user needs help choosing, justifying, or refining their research methodology. Triggers on "Methodik", "Forschungsdesign", "Methodenwahl", "Vorgehensmodell", "research design", "methodology", "qualitative vs quantitative", "Forschungsmethode", or when the user is unsure how to approach their research systematically.
---

# Methodology Advisor

Help choose, justify, and document the research methodology for the thesis. Compare approaches, evaluate fit with the research question, and produce methodology text that meets academic standards.

## When This Skill Activates

- The user needs to choose a research methodology
- The user wants to compare qualitative vs. quantitative approaches
- The user needs to justify their chosen method for a supervisor or expose
- The user is writing the methodology chapter and needs structural guidance

## Memory Files

### Read

- `academic_context.md` — Research question, sub-questions, work type, topic, existing methodology choice

### Write

- `academic_context.md` — Update the methodology field after a decision is made

## Reference

Consult the methodology catalog at `${CLAUDE_PLUGIN_ROOT}/skills/methodology-advisor/methodology-catalog.md` for detailed descriptions, strengths, weaknesses, and use cases of each methodology type.

## Core Workflow

### 1. Load Context

Read `academic_context.md`. If it does not exist, trigger the Academic Context skill first. Extract: research question, sub-questions, work type, topic, and any preliminary methodology choice.

### 2. Assess Research Question Type

Classify the research question to narrow down suitable methodologies:

| Question Type | Indicators | Suitable Methods |
|---------------|------------|------------------|
| Exploratory | "How does...", "What factors..." | Qualitative, Case Study, Grounded Theory |
| Descriptive | "What is the state of...", "How is...structured" | Literature Review, Survey, Content Analysis |
| Explanatory | "Why does...", "What causes..." | Quantitative, Experiment, Regression |
| Evaluative | "How effective...", "What impact..." | Mixed Methods, Case Study, Comparative |
| Design-oriented | "How can...be designed" | Design Science, Action Research |

Present the classification and reasoning to the user for confirmation.

### 3. Methodology Comparison

Based on the question type, present 2-3 candidate methodologies. For each, cover:

#### Systematic Literature Review (SLR)
- **When:** Synthesizing existing research on a well-defined topic
- **Strengths:** Reproducible, comprehensive, no primary data needed
- **Weaknesses:** Limited to published work, time-intensive search phase
- **Fit for:** Bachelorarbeit (common), Masterarbeit (as foundation)
- **Key references:** Kitchenham (2004), Webster & Watson (2002), Tranfield et al. (2003)

#### Qualitative Research
- **When:** Understanding perspectives, experiences, or processes
- **Subtypes:** Interviews, Focus Groups, Ethnography, Grounded Theory
- **Strengths:** Rich data, context-sensitive, emergent findings
- **Weaknesses:** Small samples, subjectivity, not generalizable
- **Fit for:** Masterarbeit, exploratory Bachelorarbeit
- **Key references:** Mayring (2015), Flick (2022), Yin (2018)

#### Quantitative Research
- **When:** Measuring, testing hypotheses, establishing correlations
- **Subtypes:** Survey, Experiment, Secondary Data Analysis
- **Strengths:** Generalizable, statistical rigor, reproducible
- **Weaknesses:** Requires sufficient sample size, may miss context
- **Fit for:** Masterarbeit, data-driven Bachelorarbeit
- **Key references:** Bortz & Döring (2006), Field (2018)

#### Mixed Methods
- **When:** Research question requires both breadth and depth
- **Subtypes:** Sequential Explanatory, Sequential Exploratory, Convergent
- **Strengths:** Comprehensive, triangulation, compensates weaknesses
- **Weaknesses:** Complex, time-intensive, requires dual competence
- **Fit for:** Masterarbeit
- **Key references:** Creswell & Creswell (2018), Tashakkori & Teddlie (2010)

#### Case Study
- **When:** Investigating a phenomenon in its real-world context
- **Subtypes:** Single Case, Multiple Case, Embedded
- **Strengths:** In-depth analysis, real-world relevance
- **Weaknesses:** Limited generalizability, selection bias
- **Fit for:** Bachelorarbeit, Masterarbeit
- **Key references:** Yin (2018), Eisenhardt (1989), Stake (1995)

#### Design Science Research (DSR)
- **When:** Creating and evaluating an artifact (framework, model, tool)
- **Strengths:** Practical contribution, iterative refinement
- **Weaknesses:** Evaluation criteria must be defined upfront
- **Fit for:** Wirtschaftsinformatik, engineering-oriented works
- **Key references:** Hevner et al. (2004), Peffers et al. (2007)

### 4. Interactive Decision

Guide the user to a decision through targeted questions:

1. **Data availability** — Does primary data collection require ethics approval, access, or time?
2. **Skills and tools** — Is the user comfortable with statistical software, interview techniques, etc.?
3. **Supervisor expectations** — Has the supervisor indicated a preference?
4. **Time constraints** — How much time is available for data collection and analysis?
5. **Work type fit** — Is the method realistic for the scope of the work?

Present a recommendation with clear reasoning. Let the user decide.

### 5. Methodology Justification

After the user chooses a method, help formulate the justification text:

- **Why this method** — Connect to the research question type
- **Why not alternatives** — Brief reasoning for rejecting other options
- **Precedent** — Reference published studies in the same field using this method
- **Limitations** — Acknowledge known limitations and mitigation strategies

This justification can be used directly in the expose or methodology chapter.

### 6. Methodology Chapter Structure

Provide a recommended structure for the methodology chapter:

1. **Forschungsdesign** — Overview of the chosen approach
2. **Begründung der Methodenwahl** — Justification (from step 5)
3. **Datenerhebung** — How data is collected (or how literature is searched)
4. **Datenanalyse** — How data is analyzed (coding, statistics, comparison)
5. **Gütekriterien** — Quality criteria (validity, reliability, or trustworthiness)
6. **Limitationen** — Methodological limitations

### 7. Save Decision

After the user confirms:

1. Read `academic_context.md` (prevent stale overwrites)
2. Update the `Methodik` field with the chosen methodology
3. Add key methodology references to `## Schlüsselkonzepte` if not already present

## Important Rules

- **Never choose for the user** — Present options with clear trade-offs, let the user decide
- **Match scope to work type** — Do not recommend complex mixed methods for a Hausarbeit
- **Cite methodology literature** — Every recommended method should reference established sources
- **Be honest about limitations** — Every method has weaknesses; present them transparently
- **Consider supervisor preferences** — If mentioned, factor them into the recommendation
- **Revisit if needed** — Methodology can be refined as the work progresses; note this to the user
