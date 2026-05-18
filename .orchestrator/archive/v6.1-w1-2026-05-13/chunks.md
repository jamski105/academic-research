# v6.1 Wave 1 Decomposition

## Order

1. chunk-A (depends on: -)
2. chunk-B (depends on: A)
3. chunk-E (depends on: A)
4. chunk-F (depends on: A)
5. chunk-C (depends on: A, B)
6. chunk-D (depends on: A)
7. chunk-G (depends on: A, B, C, D, E, F)

Parallelization-Hinweis:
- B, E, F können nach A starten. E hat keine Vault-Überlappung (rein Citation-Skill-Files) → echte Parallelität zu B/F.
- B und F überlappen auf `mcp/academic_vault/{schema.sql,migrate.py,server.py}` → werden seriell ausgeführt (B vor F oder F vor B).
- C, D starten nach B fertig, parallel möglich (beide touchen nur `server.py` mit additiven Methoden).
- G ist Final-Validation, wartet auf alle.

## chunk-A: F2.1 book-handler Skill + ISBN-Resolution + Vault book/chapter type

- Tickets: #71
- Files (~12):
  - `skills/book-handler/SKILL.md` (create) — frontmatter + body mit DNB/OpenLibrary/DOAB/GoogleBooks-Pipeline-Beschreibung
  - `skills/book-handler/references/sources.md` (create) — API-Endpoints, ISBN-Regex
  - `scripts/book_resolve.py` (create) — DNB SRU + OpenLibrary + DOAB + GoogleBooks Clients
  - `scripts/requirements.txt` (modify) — neue Dependencies (requests, lxml für SRU)
  - `mcp/academic_vault/schema.sql` (modify) — `editor TEXT`, `chapter TEXT`, `page_first INTEGER`, `page_last INTEGER`, `container_title TEXT` Spalten an `papers`; CHECK constraint type ∈ ('article-journal','book','chapter')
  - `mcp/academic_vault/migrate.py` (modify) — neue Migration für obige Spalten
  - `mcp/academic_vault/server.py` (modify) — `add_paper(type=book|chapter, editor, chapter, page_first, page_last)` Support
  - `tests/test_book_resolve.py` (create) — DNB-/OL-/DOAB-Lookups (mit Mocks)
  - `tests/test_skills_manifest.py` (modify) — register book-handler im Manifest
  - `tests/test_vault_book_chapter.py` (create) — Vault add_paper für type=book + type=chapter
- Estimated LOC: ~450
- Estimated effort: ~6h
- Dependencies: none
- Notes: Foundation-Chunk. Setzt CSL-Types in DB + Skill-Trigger-Pattern. Acceptance-Probe ISBN `9783446461031` muss DNB-Treffer + CSL-JSON liefern.

## chunk-B: F2.2 chunk_pdf + Vault parent_paper_id

- Tickets: #72
- Files (~7):
  - `scripts/chunk_pdf.py` (create) — `--input book.pdf --chapter <n|toc|all> --output ...`, PyPDF2 outline-tree zuerst, Fallback TOC-Text-Extraction
  - `mcp/academic_vault/schema.sql` (modify) — `parent_paper_id TEXT REFERENCES papers(paper_id)` Spalte auf papers
  - `mcp/academic_vault/migrate.py` (modify) — Migration für parent_paper_id
  - `mcp/academic_vault/server.py` (modify) — `add_chapter(parent_paper_id, chapter_number, ...)` Helper; `add_paper` akzeptiert parent_paper_id
  - `skills/quote-extractor/SKILL.md` (modify) — Hinweis: läuft auf Kapitel-PDFs falls parent_paper_id gesetzt
  - `tests/test_chunk_pdf.py` (create) — PyPDF2-Outline-Parsing, TOC-Fallback, OA-Buch-Fixture
  - `tests/test_vault_parent.py` (create) — parent/child-Beziehung in Vault
- Estimated LOC: ~350
- Estimated effort: ~4h
- Dependencies: A
- Notes: AC-Probe: 1 OA-Buch ≥400 S. → 8 Kapitel-PDFs mit Token-Footprint <30k/API-Call. Fixture-PDF in `tests/fixtures/` (klein gehaltenes Sample-Buch).

## chunk-C: F2.3 page_offset Sanity-Check + printed_page-Mapping

- Tickets: #73
- Files (~5):
  - `scripts/page_offset.py` (create) — scannt erste 30 PDF-Seiten via Modell-Aufruf, ermittelt `page_offset = pdf_page - printed_page`, 2 Stichproben für Stabilitäts-Check
  - `mcp/academic_vault/server.py` (modify) — `set_page_offset(paper_id, offset)`, `get_printed_page(paper_id, pdf_page) -> int` (existing `page_offset` Spalte nutzen)
  - `skills/book-handler/SKILL.md` (modify) — Trigger page_offset-Berechnung beim ersten Buch-PDF-Add
  - `skills/citation-extraction/SKILL.md` (modify) — `printed_page = api.start_page_number - page_offset` in Citation-Output
  - `tests/test_page_offset.py` (create) — Eval mit 5 Büchern (ohne Vorwort, 10 Vorseiten, römische Ziffern, Doppelpaginierung)
- Estimated LOC: ~300
- Estimated effort: ~4h
- Dependencies: A, B
- Notes: `papers.page_offset` Spalte existiert bereits → keine Schema-Migration. Security-relevant (Halluzinations-Risiko bei Seitenangaben).

## chunk-D: F2.4 OCR-Detection + ocrmypdf-Workflow

- Tickets: #74
- Files (~5):
  - `scripts/pdf.py` (modify oder create falls fehlt) — `detect_needs_ocr(pdf_path) -> bool` (< 100 Zeichen pro Seite auf Stichprobe)
  - `scripts/ocr.py` (create) — `run_ocrmypdf(input, output)` Wrapper, prüft ob ocrmypdf installiert
  - `skills/book-handler/SKILL.md` (modify) — bei Detection-Flag: User-Prompt „OCR ausführen? (~30 s/Seite)"; nach OCR `set_ocr_done` + neuer pdf_path
  - `mcp/academic_vault/server.py` (modify) — `set_ocr_done(paper_id)`, `update_pdf_path(paper_id, new_path)` (existing `ocr_done` Spalte)
  - `README.md` (modify) — ocrmypdf als optionale Dep, Install-Hinweis
  - `tests/test_ocr_detection.py` (create) — Mock-PDFs mit und ohne Text-Layer
- Estimated LOC: ~250
- Estimated effort: ~3h
- Dependencies: A
- Notes: `papers.ocr_done` Spalte existiert bereits → keine Schema-Migration. ocrmypdf bleibt opt-in (Erstaufruf fragt).

## chunk-E: F2.5 CSL book/chapter Schema + DIN-1505-Variant

- Tickets: #75
- Files (~5):
  - `skills/citation-extraction/references/book-chapter-de.md` (create) — DIN 1505 / Harvard-de / APA-7 Sammelband-Beispiele
  - `skills/citation-extraction/references/din1505.md` (modify) — Bücher-Sektion (heute Article-Fokus)
  - `skills/citation-extraction/SKILL.md` (modify) — Variant-Selector wählt `book-chapter-de.md` bei type=chapter
  - `docs/literature-state-schema.md` (create) — type-Werte, container-title, editor[], chapter, page-first/last Felder dokumentieren
  - `tests/test_citation_book_chapter.py` (create) — 5 Sammelband-Zitate in DIN-1505 korrekt
- Estimated LOC: ~250
- Estimated effort: ~3-4h
- Dependencies: A
- Notes: Keine Vault-Überlappung mit B/C/D/F → echt parallelisierbar. AC-Probe: Variant-Selector schaltet automatisch.

## chunk-F: F19 VLM Figure/Table Verification

- Tickets: #99
- Files (~8):
  - `agents/figure-verifier.md` (create) — Sonnet-4.6 Vision-Subagent, Input PDF-Seite als Bild via Citations-API document-Param
  - `mcp/academic_vault/schema.sql` (modify) — neue Tabelle `figures(figure_id, paper_id, page, caption, vlm_description, data_extracted_json)`
  - `mcp/academic_vault/migrate.py` (modify) — Migration für figures-Tabelle
  - `mcp/academic_vault/server.py` (modify) — `add_figure(paper_id, page, caption, vlm_description, data_extracted)`
  - `hooks/verbatim-guard.mjs` (modify) — bei Bezugnahme „Abb. X.Y" / „Tab. X.Y": prüfe Caption-Quote gegen figures-Tabelle
  - `tests/test_figure_verifier.py` (create) — Agent-Smoke + Vault-Roundtrip
  - `tests/test_verbatim_figure_guard.py` (create) — Hook erkennt erfundene Figure-Verweise
  - `evals/figure-verifier/evals.json` (create) — 5 Bücher × 3 Figures = 15 Cases
- Estimated LOC: ~400
- Estimated effort: ~5h
- Dependencies: A
- Notes: Vault-Überlappung mit A/B (schema.sql, migrate.py) → seriell nach B.

## chunk-G: F15 Eval-Coverage Bücher + Token-Regression

- Tickets: #76
- Files (~12):
  - `evals/book-handler/evals.json` (create) — 5 Cases (1 OA-Buch DOAB, 2 ISBN-only, 1 Scan-PDF, 1 Sammelband)
  - `evals/book-handler/fixtures/` (create, ~3-5 files) — kleine PDFs <5 MB pro Datei + Metadaten-JSON für ISBN-only-Cases
  - `evals/humanizer-de-pipeline/drafts-after/draft-01-theorie.md` (create) — humanisierte Variante zum vorhandenen draft-01
  - `evals/humanizer-de-pipeline/drafts-after/draft-02-methodik.md` (create)
  - `evals/humanizer-de-pipeline/drafts-after/draft-03-diskussion.md` (create)
  - `evals/humanizer-de-pipeline/README.md` (modify) — Vorher/Nachher-Struktur dokumentieren
  - `tests/evals/eval_runner.py` (modify) — pro Case `tokens_in`/`tokens_out` aus API-Response erfassen
  - `tests/evals/test_token_regression.py` (create) — liest `tests/baselines/tokens.json`, vergleicht, bricht bei >+20 %
  - `tests/baselines/tokens.json` (create) — initial leer `{}`; erster Lauf schreibt, Folge-Läufe vergleichen
  - `tests/evals/test_book_handler_evals.py` (create) — pytest für `evals/book-handler/evals.json`
- Estimated LOC: ~500
- Estimated effort: ~5-6h
- Dependencies: A, B, C, D, E, F
- Notes: Tokens-Werte werden **nicht** in jedem `evals/*/evals.json` dupliziert. Stattdessen erfasst der Runner sie und vergleicht gegen `tests/baselines/tokens.json` (User-Entscheidung aus Phase 0.5). Schwelle: >+20 % auf `tokens_in` ODER `tokens_out`.
