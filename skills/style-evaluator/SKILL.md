---
name: Style Evaluator
description: This skill should be used when the user wants to evaluate text quality, check for AI-detection patterns, or improve academic writing style. Triggers on "Text pruefen", "Stil-Check", "KI-Erkennung", "Text verbessern", "Qualitaetskontrolle", "menschlich klingen", "style check", "AI detection", "text quality", "improve writing", "human-like", or when text sounds too artificial or formulaic.
---

# Style Evaluator

Evaluate academic text for human-likeness, AI-detection vulnerability, coherence, duplication, and overall academic quality. Assign a composite score (0-100) across five dimensions and optionally rewrite flagged sections.

## When This Skill Activates

- The user submits text for quality or style evaluation
- The user suspects text sounds too AI-generated
- The user asks for text improvement or naturalness
- Another skill (e.g., Chapter Writer) requests a post-write quality gate

## Memory Files

- Read `writing_state.md` for current chapter context and previous scores
- Read `academic_context.md` for citation style, language, and work type
- Update `writing_state.md` with new evaluation scores after each run

## Metriken

Die quantitativen Metriken (Satzlängenverteilung, Übergangsfrequenz, Vokabular-Diversität, n-Gramm-Wiederholung) berechnet Claude direkt aus dem Eingabetext — keine externe Pipeline. Siehe Rubrik unten für konkrete Messvorschriften pro Dimension.

## Scoring Rubric (0-100)

Evaluate each dimension independently, then compute a weighted total.

### 1. Human-Likeness (weight: 0.30)

Assess whether the text reads as authentically human-written.

Indicators of LOW human-likeness (deduct points):
- Sentence length standard deviation below 4 words (too uniform)
- More than 30% of sentences starting with the same syntactic pattern
- Absence of hedging language, qualifiers, or tentative phrasing
- No rhetorical questions, asides, or first-person perspective where appropriate
- Paragraph lengths too uniform (all within 10% of average)

Indicators of HIGH human-likeness (award points):
- Natural variation in sentence length (short + long mixed)
- Occasional informal connectors alongside formal ones
- Topic sentences vary in structure across paragraphs
- Evidence of personal analytical voice

### 2. Anti-AI-Detection (weight: 0.25)

Flag patterns that AI-detection tools (GPTZero, Turnitin AI, Originality.ai) commonly identify.

Check for:
- **Uniform sentence lengths** -- Compute standard deviation; flag if below 5 words
- **Repetitive transitions** -- Flag if "Furthermore", "Moreover", "Additionally", "In conclusion" each appear more than twice per 1000 words
- **Missing personal voice** -- Flag if zero first-person pronouns in sections where methodology or opinion is expected
- **Overly perfect structure** -- Flag if every paragraph follows identical topic-evidence-analysis pattern
- **Lexical predictability** -- Flag if top-10 most frequent content words cover more than 15% of all content words
- **Burstiness score** -- Measure variation in perplexity across sentences; flag if too flat

### 3. Coherence (weight: 0.20)

Evaluate logical flow between sentences and paragraphs.

Check for:
- Topic continuity (each paragraph advances the argument)
- Logical connectors match actual logical relationships
- No orphaned claims (assertions without preceding context or following evidence)
- Smooth transitions between sections
- Consistent terminology (no unexplained synonym switching)

### 4. Duplication Detection (weight: 0.15)

Identify internal repetition within the text.

Check for:
- Repeated phrases (3+ word sequences appearing more than twice)
- Paraphrased duplicates (same idea restated in adjacent paragraphs)
- Redundant introductory/concluding sentences across sections
- Copy-paste artifacts

### 5. Academic Quality (weight: 0.10)

Evaluate formal academic standards.

Check for:
- Proper citation integration (not just parenthetical drops)
- Argument structure (claim, evidence, analysis)
- Register consistency (no colloquial breaks in formal text, no overly formal language in applied sections)
- Terminology precision
- Appropriate use of passive vs. active voice for the discipline

## Evaluation Workflow

1. Read the submitted text (full chapter, section, or paragraph)
2. Read `writing_state.md` and `academic_context.md` for context
3. Berechne quantitative Metriken inline aus dem Eingabetext (Satzlängen, Übergänge, n-Gramme, Vokabular-Diversität)
4. Score each dimension (0-100) using the rubric and script metrics
5. Compute weighted total: `total = 0.30*human + 0.25*anti_ai + 0.20*coherence + 0.15*duplication + 0.10*academic`
6. Present results in structured format (see output format below)
7. Update `writing_state.md` with the new scores

## Output Format

Present results as:

```
## Style Evaluation: [Section/Chapter Name]

| Dimension            | Score | Status |
|----------------------|-------|--------|
| Human-Likeness       | XX    | OK/WARN/FAIL |
| Anti-AI-Detection    | XX    | OK/WARN/FAIL |
| Coherence            | XX    | OK/WARN/FAIL |
| Duplication          | XX    | OK/WARN/FAIL |
| Academic Quality     | XX    | OK/WARN/FAIL |
| **Gesamt**           | **XX**| **STATUS** |

### Flagged Issues
[List each flagged issue with location and severity]

### Rewrite Suggestions
[Concrete rewrites for WARN/FAIL sections, preserving meaning]
```

Status thresholds: OK >= 75, WARN 50-74, FAIL < 50.

## Rewrite Mode

When the user requests rewriting of flagged sections:

1. Isolate the flagged passage
2. Preserve the exact argument and all citations
3. Vary sentence structure, length, and opening patterns
4. Introduce natural hedging where appropriate ("This suggests...", "It appears that...")
5. Break overly symmetric paragraph structures
6. Re-evaluate the rewritten passage and confirm score improvement

## Important Rules

- Never fabricate metrics -- berechne alle Werte nachvollziehbar aus dem Text und zeige die Rechenbasis, wenn der User danach fragt
- Always preserve the author's argument and citations during rewrites
- Score conservatively -- a perfect 100 is unrealistic for any text
- Flag but do not auto-rewrite without user consent
- Use German labels in output when `academic_context.md` specifies German as the language
- Track score history in `writing_state.md` to show improvement over time
