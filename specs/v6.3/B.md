# Spec: Chunk B — NotebookLM-Bundle Skill (F9, #89)

## Kontext

Bücher >600 PDF-Seiten überschreiten Anthropic-Limits. NotebookLM (Gemini, 2M-Token-Source-Grounding) dient als Triage-Tool. **Kein automatischer Upload** — der User lädt das Bundle manuell hoch.

**WICHTIGE ABGRENZUNG:** NotebookLM ersetzt nicht den Vault-Zitat-Pfad. Antworten aus NotebookLM sind NICHT verbatim-garantiert und dürfen NICHT als zitierfähige Quellen verwendet werden. Der Skill warnt den User explizit und prominent.

---

## Akzeptanzkriterien

1. 5 Paper × 30 Seiten → 1 Bundle-PDF mit allen Inhalten (seitenweise korrekt konkateniert)
2. Bundle enthält Bibliographie-Cover-PDF als erste Seite(n)
3. Bundle enthält TOC (Inhaltsverzeichnis) mit Paper-Titeln + Seitennummern
4. Output: `<projekt>/notebook-bundle-<ts>.pdf`
5. Wenn Gesamt-Dateigröße >500MB: Split in mehrere Bundles (Multi-Bundle)
6. Fehlende PDFs werden geloggt und übersprungen (kein Crash)
7. User-Doku enthält Schritt-für-Schritt NotebookLM-Upload-Flow mit Verbatim-Warning ganz oben

---

## Dateigrenzen (file boundary)

```
skills/notebook-bundle/SKILL.md
skills/notebook-bundle/scripts/bundle.py
skills/notebook-bundle/scripts/cover_pdf.py
tests/test_notebook_bundle.py
tests/fixtures/notebook_bundle/      (Mock-PDFs + selection.json)
docs/skills/notebook-bundle.md       (optional, User-Doku)
```

---

## Architektur

### Komponenten

#### 1. `skills/notebook-bundle/SKILL.md`
- Skill-Frontmatter (name, description, Trigger-Phrasen)
- Loads preamble via `skills/_common/preamble.md`
- **Prominente Verbatim-Warning** (Block ganz oben)
- Workflow: Selection laden → Bundle bauen → Output melden

#### 2. `skills/notebook-bundle/scripts/bundle.py`
Hauptskript. CLI: `python bundle.py <selection_json> [--output <dir>] [--size-limit-mb <N>]`

Schritte:
1. Selection-JSON einlesen (Schema: `{papers: [{id, title, authors, year, pdf_path}, ...]}`)
2. Für jedes Paper: PDF-Existenz prüfen; fehlende loggen + überspringen
3. `cover_pdf.py` aufrufen → Cover-PDF (Bibliographie)
4. Alle PDFs per PyPDF2 konkatenieren (Cover + Dokumente in TOC-Reihenfolge)
5. TOC-Seite als erste Seite einsetzen (plain-text via PyPDF2-Trick)
6. Größenprüfung: wenn >500MB → Split in Bundles
7. Output: `notebook-bundle-<ts>.pdf` (oder `-part1.pdf`, `-part2.pdf`)

#### 3. `skills/notebook-bundle/scripts/cover_pdf.py`
Erzeugt Bibliographie-Cover als PDF-Seite(n):
- Nutzt **PyPDF2-Text-Page-Trick** (kein reportlab, kein fpdf) — Constraint aus Ticket
- Erstellt eine PDF-Seite mit plaintext: Titel, Autoren, Jahr, je Paper
- Fallback: wenn PyPDF2-Textseiten-Erzeugung nicht möglich → minimale PDF-Rohbytes (1.4-kompatibel, hardcoded template)

#### 4. `tests/test_notebook_bundle.py`
Mindestens 6 Tests (TDD-First):

| Test | Beschreibung |
|------|-------------|
| `test_bundle_5_papers_30_pages` | 5 Mock-PDFs à 3 Seiten → Bundle hat ≥15 Seiten |
| `test_toc_present` | TOC-Seite ist erste Seite, enthält Paper-Titel |
| `test_cover_page_present` | Cover-PDF enthält alle 5 Paper-Einträge |
| `test_split_over_500mb` | Wenn Gesamt >500MB → 2 Output-Dateien |
| `test_missing_pdf_skipped` | Paper mit nicht-existenter PDF → wird übersprungen, kein Exception |
| `test_output_filename_pattern` | Output-Dateiname enthält `notebook-bundle-` + Timestamp-Pattern |

#### 5. `tests/fixtures/notebook_bundle/`
- 5 kleine Mock-PDFs (3 Seiten je, ~10KB) erzeugt per PyPDF2 in `conftest.py` oder als echte Fixtures
- `selection.json` mit 5 Paper-Einträgen

---

## Selection-JSON Schema

```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Example Paper Title",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2020,
      "pdf_path": "/absolute/or/relative/path/to/smith2020.pdf"
    }
  ]
}
```

Optional: `cluster_id` und `query` als Metadaten-Felder (werden im Cover verwendet).

---

## Constraints (Umsetzung)

- **PyPDF2-only** für Merge (PyPDF2>=3.0.0 ist in requirements.txt)
- Cover-PDF: PyPDF2-Text-Page-Trick oder minimales PDF-Template (kein reportlab, kein fpdf)
- 500MB-Limit: Prüfung nach Konkatenation jedes Papers (akkumulierte Größe)
- Tests laufen mit Mock-PDFs (3-5 Seiten, keine echten Paper)
- Kein automatischer NotebookLM-Upload

---

## User-Warning (verbatim, in SKILL.md und Doku)

```
⚠️  WICHTIGER HINWEIS — KEINE VERBATIM-GARANTIE:
NotebookLM (Gemini) ist ein Triage-Tool. Antworten aus NotebookLM sind
NICHT verbatim aus den Quellen zitiert und dürfen NICHT als zitierfähige
Quellen in wissenschaftlichen Arbeiten verwendet werden.
Dieses Bundle dient der Orientierung und Übersicht — nicht als Zitat-Pfad.
Für verbatim-gesicherte Zitate: Vault-Zitat-Pfad (vault.add_quote) nutzen.
```

---

## Offene Fragen (keine Blocker)

- Vault-API für Paper-Lookup: `search_papers(db_path, query)` ist verfügbar; für Selection-Input wird `pdf_path` direkt aus JSON gelesen (kein Vault-DB-Lookup nötig für Bundle-Bau)
- TOC-Erzeugung per PyPDF2: nutzt `PdfWriter.add_page()` mit einer manuell erstellten leeren Seite + Overlay-Text (bekannter Trick via `add_blank_page` + direktem PDF-Stream-Injection)

---

## Lieferumfang

| Datei | Status |
|-------|--------|
| `skills/notebook-bundle/SKILL.md` | Neu |
| `skills/notebook-bundle/scripts/bundle.py` | Neu |
| `skills/notebook-bundle/scripts/cover_pdf.py` | Neu |
| `tests/test_notebook_bundle.py` | Neu |
| `tests/fixtures/notebook_bundle/` | Neu |
| `docs/skills/notebook-bundle.md` | Neu (optional aber empfohlen) |
