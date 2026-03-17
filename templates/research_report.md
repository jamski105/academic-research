# Recherche-Ergebnis: {{RESEARCH_QUERY}}

**Session:** {{SESSION_ID}}
**Datum:** {{DATE}}
**Modus:** {{MODE}}
**Dauer:** {{DURATION}}

---

## Zusammenfassung

- **Papers gefunden:** {{PAPER_COUNT}}
- **PDFs heruntergeladen:** {{PDF_COUNT}}/{{PAPER_COUNT}} ({{PDF_RATE}}%)
- **Zitate extrahiert:** {{QUOTE_COUNT}}
- **Genutzte Module:** {{MODULES_USED}}

---

## Top Papers (nach Relevanz)

{{#PAPERS}}
### {{RANK}}. {{TITLE}} ({{YEAR}})

**Autoren:** {{AUTHORS}}
**DOI:** {{DOI}}
**Quelle:** {{SOURCE_MODULE}}
**Relevanz-Score:** {{RELEVANCE_SCORE}} / 1.0
**Zitationen:** {{CITATION_COUNT}}
**PDF:** {{PDF_STATUS}}

{{#QUOTES}}
> "{{QUOTE_TEXT}}" (S. {{PAGE}})
{{/QUOTES}}

---

{{/PAPERS}}

## Modul-Statistiken

| Modul | Treffer | Unique | Ø Relevanz |
|-------|---------|--------|------------|
{{#MODULE_STATS}}
| {{MODULE}} | {{HITS}} | {{UNIQUE}} | {{AVG_RELEVANCE}} |
{{/MODULE_STATS}}

## Dateien

- **Session-Daten:** `~/.academic-research/sessions/{{SESSION_ID}}.json`
- **BibTeX:** `~/.academic-research/citations.bib`
- **PDFs:** `~/.academic-research/pdfs/`
