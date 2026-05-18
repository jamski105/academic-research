# Coverage Report — Chunk A: #88 F7 Zotero-Import
Iteration: 1 | PR: 143 | Date: 2026-05-18

---

## AC1: Test mit Zotero-Group-Library (50 Items): alle 50 in Vault

**Verdict: PASS**

Implementation:
- `skills/zotero-import/scripts/zotero_pull.py`: `run_import()` ruft `zot.everything(zot.items())` auf und iteriert über alle Items; `add_paper()` wird für jedes neue Item aufgerufen (zotero_pull.py Zeilen ~270–330).
- `tests/fixtures/zotero_library.json`: 50-Item-Fixture angelegt (PR diff bestätigt `assert len(items) == 50`).
- `zotero_library_type: "group"` ist als Config-Feld in SKILL.md und zotero_pull.py dokumentiert; der Mock-Test verwendet die gleiche Library-Struktur.

Test:
- `tests/test_zotero_import.py::TestBulkImport::test_50_items_all_imported`
  - Lädt die 50-Item-Fixture, mockt pyzotero vollständig
  - Asserts: `result.imported == 50`, `result.skipped == 0`, `result.errors == []`

Evidence: PR diff Zeile 3106–3129 (test body), Zeile 125–488 (zotero_pull.py implementation).

---

## AC2: Re-Run führt nicht zu Duplikaten

**Verdict: PASS**

Implementation:
- `_paper_exists_in_vault()` in zotero_pull.py prüft DOI (normalisiert lowercase) und ISBN (Bindestriche entfernt) gegen `papers`-Tabelle.
- `_normalize_doi()` und `_normalize_isbn()` stellen konsistente Normalisierung sicher.
- Im Haupt-Loop: `if _paper_exists_in_vault(db_path, doi, isbn): result.skipped += 1; continue`

Test:
- `tests/test_zotero_import.py::TestDedup::test_rerun_no_duplicates`
  - Führt `run_import()` zweimal mit identischer 50-Item-Library durch
  - Run 1: `result_1.imported == 50`
  - Run 2: `result_2.skipped == items_with_id` (49 Items mit DOI/ISBN werden dedupliziert), `result_2.imported == items_without_id` (1 Item ohne Identifier, Spec-konformes Verhalten)
  - Kein doppelter Vault-Eintrag für DOI/ISBN-Items

Hinweis: Items ohne DOI und ISBN (1 in der Fixture) werden laut Spec immer importiert — Dedup-Test deckt das korrekt ab und ist Spec-konform (Spec A.md: "Items ohne DOI und ISBN werden **immer** importiert").

Evidence: PR diff Zeile 3130–3172 (test body), zotero_pull.py `_paper_exists_in_vault` und Dedup-Block.

---

## AC3: PDFs in Files-API hochgeladen, file_ids gecached

**Verdict: PASS**

Implementation:
- Nach `add_paper()` mit `pdf_path`: `ensure_file(db_path=db_path, paper_id=paper_id, api_key="")` wird aufgerufen (zotero_pull.py ~Zeilen 300–320).
- `file_id` wird an `result.file_ids` angehängt.
- `ensure_file` ist bereits in `mcp/academic_vault/server.py` vorhanden (kein neuer Code nötig, Spec bestätigt dies).

Test:
- `tests/test_zotero_import.py::TestPDFAttachment::test_pdf_attachment_uploaded_file_id_cached`
  - Mockt pyzotero mit einem Item + PDF-Attachment-Child
  - Mockt `_download_attachment` → gibt lokalen Pfad zurück
  - Mockt `ensure_file` mit `return_value="file_mock_id_abc"`
  - Asserts:
    - `mock_ef.assert_called_once()` — ensure_file wurde aufgerufen
    - `len(result.file_ids) >= 1` — file_id gecached
    - `"file_mock_id_abc" in result.file_ids` — korrekter Wert

Evidence: PR diff Zeile 3210–3264 (test body), zotero_pull.py PDF-Attachment-Block.

---

## Zusammenfassung

| AC | Status | Test |
|----|--------|------|
| AC1: 50-Item Group-Library → alle in Vault | PASS | `TestBulkImport::test_50_items_all_imported` |
| AC2: Re-Run keine Duplikate | PASS | `TestDedup::test_rerun_no_duplicates` |
| AC3: PDFs in Files-API, file_ids gecached | PASS | `TestPDFAttachment::test_pdf_attachment_uploaded_file_id_cached` |

Alle 3 ACs implementiert und getestet. 7 Tests in PR (smoke, bulk-50, dedup-rerun, missing-doi, pdf/file_id, perm-0644, perm-0600).
