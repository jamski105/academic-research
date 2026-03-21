---
name: Plagiarism Check
description: This skill should be used when the user wants to check text for unintentional plagiarism, too-close paraphrases, or source proximity. Triggers on "Plagiat pruefen", "Textaehnlichkeit", "Paraphrase checken", "plagiarism", "zu nah am Original", "Plagiatspruefung", "source similarity", "text similarity check", or when the user is concerned about paraphrasing quality.
---

# Plagiarism Check

Check academic text for unintentional proximity to source material. Detect too-close paraphrases, insufficiently reworded passages, and missing attributions using n-gram overlap detection. Suggest reformulations for flagged passages.

## When This Skill Activates

- The user submits text to check against their sources
- The user is paraphrasing a source and wants verification
- Pre-submission quality assurance before final hand-in
- Another skill (e.g., Chapter Writer) requests a plagiarism gate

## Memory Files

- Read `academic_context.md` for citation style and language
- Read `literature_state.md` for the list of sources used per chapter
- Read `writing_state.md` for current writing progress context

## Scripts

Use `${CLAUDE_PLUGIN_ROOT}/scripts/text_utils.py` for tokenization (`tokenize()` function) and text normalization utilities.

## Detection Methods

### 1. N-Gram Overlap Detection

Compare the user's text against source texts (PDF extracts from the session).

**Procedure:**
1. Tokenize both user text and source text into lowercase word sequences
2. Generate n-grams for n = 3, 4, 5, 6, 7
3. Compute overlap ratio: `overlap = matching_ngrams / total_ngrams_in_user_text`
4. Apply thresholds per n-gram size:
   - 3-grams: flag if overlap > 40% (common phrases tolerated)
   - 4-grams: flag if overlap > 25%
   - 5-grams: flag if overlap > 15%
   - 6-grams: flag if overlap > 8%
   - 7-grams: flag if overlap > 5% (near-verbatim)

### 2. Sentence-Level Similarity

For each sentence in the user's text:
1. Compare against all sentences in available source material
2. Use sequence matching (difflib SequenceMatcher) for similarity ratio
3. Flag sentences with similarity > 0.70 to any single source sentence
4. Mark as critical if similarity > 0.85

### 3. Structural Mimicry Detection

Check whether the user's text follows the source's argument structure too closely:
- Same sequence of claims in the same order
- Paragraph-by-paragraph correspondence with a single source
- Identical example progression

## Source Material Handling

### Available Sources

Check for source texts in this priority order:
1. PDF texts extracted during the current session (stored in working context)
2. Source snippets referenced in `literature_state.md`
3. User-provided original text for direct comparison

### When No Source Text Is Available

If no source PDFs or texts are accessible:
1. Inform the user that comparison is limited to internal analysis
2. Still perform internal duplication checks (repeated passages within the text)
3. Flag passages that exhibit signs of close paraphrasing (stilted phrasing, unusual vocabulary choices inconsistent with surrounding text)
4. Offer to compare if the user provides the original text

## Evaluation Workflow

1. Receive the user's text (chapter, section, or specific passage)
2. Identify available source material for comparison
3. Tokenize all texts using `text_utils.tokenize()`
4. Run n-gram overlap detection per source
5. Run sentence-level similarity per source
6. Run structural mimicry check
7. Compile flagged passages with severity ratings
8. Generate reformulation suggestions for flagged passages
9. Present results in structured format

## Output Format

```
## Plagiarism Check: [Section/Chapter Name]

**Quellen verglichen:** [N sources]
**Saetze analysiert:** [N sentences]
**Gesamtergebnis:** [OK / WARNUNG / KRITISCH]

### Flagged Passages

#### 1. [Severity: HOCH/MITTEL/NIEDRIG]
- **Position:** [Paragraph X, Sentence Y]
- **User Text:** "[flagged passage]"
- **Source:** [Author (Year), Title]
- **Similarity:** [X%]
- **Type:** [Verbatim / Close Paraphrase / Structural]
- **Reformulation:** "[suggested alternative phrasing]"

#### 2. ...

### Summary
| Severity | Count |
|----------|-------|
| HOCH     | X     |
| MITTEL   | X     |
| NIEDRIG  | X     |

### Recommendations
[Actionable steps to address flagged passages]
```

## Reformulation Guidelines

When suggesting reformulations for flagged passages:

1. **Preserve meaning** -- The academic content and argument must remain identical
2. **Change structure** -- Restructure the sentence (active/passive, clause order, emphasis shift)
3. **Replace vocabulary** -- Use discipline-appropriate synonyms (not random thesaurus substitutions)
4. **Integrate citations** -- Ensure proper attribution is part of the reformulation
5. **Maintain register** -- Keep the same academic tone and formality level
6. **Respect language** -- Reformulate in the same language as the original (German or English)

## Severity Classification

- **HOCH (High):** 7-gram overlap > 5% or sentence similarity > 0.85 -- likely verbatim copy
- **MITTEL (Medium):** 5-gram overlap > 15% or sentence similarity 0.70-0.85 -- close paraphrase
- **NIEDRIG (Low):** 4-gram overlap > 25% -- minor phrasing similarity, may be acceptable with proper citation

## Important Rules

- This is a supportive tool, not a replacement for institutional plagiarism software (Turnitin, PlagScan)
- Always recommend running institutional tools before final submission
- Never accuse the user of intentional plagiarism -- frame all findings as opportunities to improve paraphrasing
- Common academic phrases ("in this context", "the results show") generate expected overlap -- exclude standard academic collocations from flagging
- Direct quotes with proper citation are not plagiarism -- exclude properly cited quotations from analysis
- Maintain a list of discipline-specific standard phrases to reduce false positives
