---
name: Submission Checker
description: This skill should be used when the user wants to verify formal requirements before submitting their academic paper. Triggers on "formale Pruefung", "Abgabe-Check", "Formatierung pruefen", "abgabefertig", "submission check", "formal requirements", "Deckblatt pruefen", "Eidesstattliche Erklaerung", "Seitenraender", "Formatvorlage", or when the user is preparing for final submission.
---

# Submission Checker

Validate that an academic paper meets all formal submission requirements: page count, formatting, source count, required sections (cover page, table of contents, declaration of authorship, appendix), and university-specific rules.

## When This Skill Activates

- The user asks to check if their paper is ready for submission
- The user wants to verify formatting or formal requirements
- Pre-submission quality assurance
- The user asks about specific formal elements (Deckblatt, Eidesstattliche Erklaerung, etc.)

## Memory and Reference Files

- Read `academic_context.md` for work type, university, program, and citation style
- Read `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` for university-specific formal requirements
- Read `writing_state.md` for current word counts and chapter completion status

## Checklist Dimensions

### 1. Required Sections

Verify presence of all mandatory sections in correct order:

**Front Matter:**
- [ ] Deckblatt (Cover Page) -- title, author, matriculation number, supervisor, submission date, university logo
- [ ] Abstract (if required by work type)
- [ ] Inhaltsverzeichnis (Table of Contents) -- with page numbers
- [ ] Abbildungsverzeichnis (List of Figures) -- if figures are present
- [ ] Tabellenverzeichnis (List of Tables) -- if tables are present
- [ ] Abkuerzungsverzeichnis (List of Abbreviations) -- if abbreviations are used

**Body:**
- [ ] Einleitung (Introduction) -- with research question, methodology overview, structure preview
- [ ] Hauptteil (Main chapters) -- as defined in outline
- [ ] Fazit/Schluss (Conclusion) -- with summary, limitations, outlook

**Back Matter:**
- [ ] Literaturverzeichnis (Bibliography) -- all cited sources, correctly formatted
- [ ] Anhang (Appendix) -- if referenced in text
- [ ] Eidesstattliche Erklaerung (Declaration of Authorship) -- signed statement of independent work

### 2. Page Count and Length

Check against requirements from `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md`:

| Work Type        | Typical Range (pages) |
|------------------|-----------------------|
| Bachelorarbeit   | 30-50                 |
| Masterarbeit     | 60-80                 |
| Hausarbeit       | 12-20                 |
| Seminararbeit    | 15-25                 |
| Facharbeit       | 8-15                  |

Verify:
- Total page count within allowed range
- Front matter and back matter excluded from page count (if university requires this)
- No chapter disproportionately long or short relative to others

### 3. Formatting

Check compliance with standard formatting rules:

**Typography:**
- Font: Times New Roman 12pt or Arial 11pt (per university requirement)
- Line spacing: 1.5
- Margins: left 3cm (binding), right 2.5cm, top 2.5cm, bottom 2cm
- Justified text (Blocksatz)
- Page numbers: Arabic numerals, starting from introduction (front matter with Roman numerals)

**Headings:**
- Consistent heading hierarchy (no skipped levels)
- Numbered headings (1, 1.1, 1.1.1 -- max 3 levels)
- No orphan headings (heading at bottom of page with text on next page)

**Paragraphs:**
- No single-sentence paragraphs
- Consistent paragraph indentation or spacing

### 4. Source Count and Citation Quality

Verify adequate source usage:

| Work Type        | Minimum Sources |
|------------------|-----------------|
| Bachelorarbeit   | 25-40           |
| Masterarbeit     | 40-60           |
| Hausarbeit       | 10-20           |
| Seminararbeit    | 15-25           |

Check:
- Total number of unique sources in bibliography
- All in-text citations have corresponding bibliography entry
- All bibliography entries are cited at least once in text
- Citation format matches style from `academic_context.md` (APA7, IEEE, Harvard, etc.)
- No chapter without any citations (except introduction structure preview and conclusion outlook)

### 5. Figures and Tables

If figures or tables are present:
- Each has a caption with number ("Abbildung 1:", "Tabelle 1:")
- Each is referenced in the text
- Numbering is sequential and consistent
- Source attribution below each figure/table
- List of figures/tables in front matter matches actual content

### 6. Declaration of Authorship (Eidesstattliche Erklaerung)

Verify:
- Present as last page (or per university placement rule)
- Contains required wording per `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md`
- Includes place and date fields
- Includes signature line

## Evaluation Workflow

1. Read `academic_context.md` to determine work type and university
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` for specific requirements
3. Read `writing_state.md` for current completion status
4. Analyze the paper structure against the checklist
5. Score each dimension as PASS, PARTIAL, or FAIL
6. Compile results in structured output
7. Prioritize fixes by severity

## Output Format

```
## Abgabe-Check: [Work Title]

**Typ:** [Work Type] | **Uni:** [University] | **Datum:** [Check Date]

### Ergebnis-Uebersicht

| Pruefbereich          | Status              | Details           |
|-----------------------|---------------------|-------------------|
| Pflichtabschnitte     | PASS/PARTIAL/FAIL   | [X/Y vorhanden]   |
| Seitenumfang          | PASS/PARTIAL/FAIL   | [N Seiten]        |
| Formatierung          | PASS/PARTIAL/FAIL   | [Issues count]    |
| Quellenanzahl         | PASS/PARTIAL/FAIL   | [N Quellen]       |
| Abbildungen/Tabellen  | PASS/PARTIAL/FAIL   | [Issues count]    |
| Eidesstattl. Erkl.    | PASS/PARTIAL/FAIL   | [vorhanden/fehlt] |

### Kritische Maengel (sofort beheben)
[List FAIL items with specific fix instructions]

### Empfehlungen (sollte behoben werden)
[List PARTIAL items with improvement suggestions]

### Bestanden
[List PASS items as confirmation]
```

## Important Rules

- Always check `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` first -- university-specific rules override general conventions
- If `${CLAUDE_PLUGIN_ROOT}/skills/submission-checker/leibniz-fh-requirements.md` is not available, use standard German academic conventions and note that university-specific verification was not possible
- Never assume formatting is correct without checking -- formatting errors are the most common reason for submission delays
- Distinguish between hard requirements (FAIL = cannot submit) and soft recommendations (PARTIAL = should fix)
- If the paper is not yet complete, run the check on available sections and note which checks are pending
- Present results in German when `academic_context.md` specifies German as language
