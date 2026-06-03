# Export-Formate — Zitat-Extraktion

Vom Skill `citation-extraction` bei Bedarf geladen (Progressive Disclosure).
Alle Formate werden inline von Claude aus den strukturierten Paper-Daten
generiert — keine externe Skript-Pipeline.

Claude erzeugt bei Bedarf: In-text-Zitat, Literaturverzeichnis-Eintrag,
BibTeX (`~/.academic-research/citations.bib`), Markdown-Bibliografie, JSON.
Details zu jedem Stil in der jeweiligen Variant-Referenz-Datei (siehe
Variant-Selector in `SKILL.md`).

## Unterstützte Output-Formate

- **BibTeX** — für LaTeX-Integration. Ziel-Datei:
  `~/.academic-research/citations.bib`.
- **Markdown** — für Review und manuelles Editieren.
- **JSON** — für die programmatische Nutzung durch andere Skills.

Seitenangaben stammen aus `citations[].start_page_number` /
`end_page_number` (siehe Citations-API in `SKILL.md`). Bei Büchern mit
Vorseiten: `printed_page = vault.get_printed_page(paper_id, pdf_page)`.
