# Spec: Chunk G — Eval-Coverage Bücher + Token-Regression

**Ticket:** #76 — F15 Eval-Coverage für Bücher (5 Test-Cases) + Token-Regression  
**Chunk-ID:** G  
**Milestone:** v6.1 Wave 1  
**Erstellt:** 2026-05-13

---

## Ziel

Eval-Coverage für die v6.1 Buch-Handling-Pipeline herstellen und eine
Token-Regression-Baseline anlegen, die bei >+20 % Anstieg von `tokens_in`
oder `tokens_out` bricht.

---

## Acceptance Criteria

1. `evals/book-handler/evals.json` existiert mit genau 5 Cases:
   - `bh-01`: OA-Buch via DOAB (URL als Input, kein PDF benötigt)
   - `bh-02`: ISBN-only ohne PDF (nur Metadaten-JSON als Fixture)
   - `bh-03`: ISBN-only ohne PDF, zweiter ISBN-Format-Typ
   - `bh-04`: Scan-PDF (OCR-Pfad, minimales PDF-Fixture < 5 MB)
   - `bh-05`: Sammelband mit ≥ 3 Editor-Kapiteln (minimales PDF-Fixture)

2. `evals/humanizer-de-pipeline/drafts-after/` enthält 3 humanisierte
   Nachher-Drafts (`draft-01-theorie.md`, `draft-02-methodik.md`,
   `draft-03-diskussion.md`). Die Vorher-Drafts liegen bereits in
   `evals/humanizer-de-pipeline/drafts/`. README wird auf
   Vorher/Nachher-Struktur aktualisiert.

3. `tests/baselines/tokens.json` existiert als leer initialisiertes `{}`
   (wird vom eval_runner beim ersten echten API-Run befüllt).

4. `tests/evals/eval_runner.py` bekommt eine Funktion
   `call_claude_with_tokens()`, die zusätzlich `(text, tokens_in, tokens_out)`
   zurückgibt und `write_token_baseline()` / `read_token_baseline()` Helfer
   für `tests/baselines/tokens.json`. Ohne API-Key werden diese Funktionen
   übersprungen (vorhandenes Muster).

5. `tests/evals/test_token_regression.py` prüft:
   - Liest `tests/baselines/tokens.json`
   - Bei leerem Baseline: Test wird als SKIP markiert (noch keine Baseline)
   - Wenn Baseline vorhanden: Mock-Run mit gespeicherten Werten, prüft
     +20 %-Schwelle auf `tokens_in` und `tokens_out`
   - Simuliert einen "gestiegen"-Case: Test muss FAIL
   - Simuliert einen "stabil"-Case: Test muss PASS

6. `tests/evals/test_book_handler_evals.py` validiert die Struktur von
   `evals/book-handler/evals.json` (5 Cases, Pflichtfelder, Case-IDs).
   Kein API-Call — reines Schema-Validation.

7. `pytest tests/` ist grün.

---

## Nicht im Scope

- Echte API-Aufrufe gegen DOAB/DNB/OpenLibrary — nur Metadaten-JSON-Fixtures
- Änderungen an `book_resolve.py`, `chunk_pdf.py`, `page_offset.py`, `ocr.py`
  (read-only für Chunk G)
- Änderungen an anderen Skills/Agents außerhalb der File-Boundary

---

## Datenstrukturen

### evals/book-handler/evals.json

```json
{
  "component": "book-handler",
  "component_type": "skill",
  "cases": [
    {
      "id": "bh-01",
      "description": "OA-Buch via DOAB",
      "type": "book_resolve",
      "input": { "url": "https://directory.doab.org/..." },
      "fixture": null,
      "expected": { "type": "json_field", "path": "$.isbn", "check": "non_empty" }
    }
  ]
}
```

### tests/baselines/tokens.json (Schema)

```json
{
  "<eval-suite-name>": {
    "<case-id>": {
      "tokens_in": 1234,
      "tokens_out": 567
    }
  }
}
```

---

## Fixture-Strategie

- `bh-02`, `bh-03`: Metadaten-JSON-Datei (< 1 KB) in `fixtures/`
- `bh-04`: Minimales eingebettetes Text-PDF (Python-generiert, < 5 MB) oder
  vorhandenes Dummy-PDF aus Repo
- `bh-05`: Minimales Multi-Kapitel-PDF (Python-generiert mit PyPDF2/reportlab
  oder rohem PDF-Bytes); nur Inhaltsverzeichnis + 3 Kapitel-Header nötig
- Alle Fixtures werden im Repo eingecheckt

---

## Robustheit gegen fehlende API-Keys

- `test_token_regression.py` enthält kein `require_api_key()` — läuft ohne API
- Baseline-Vergleich basiert ausschließlich auf `tokens.json`-Daten
- Wenn `tokens.json` leer: `pytest.skip()`

---

## Abhängigkeiten

- Chunks A–F (book-handler, chunk_pdf, page_offset, ocr, csl, figure-verifier)
  können parallel laufen — Chunk G liest deren Outputs nicht, nur Struktur-
  Validierung gegen evals.json-Schema
