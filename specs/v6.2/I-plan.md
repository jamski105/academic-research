# Plan: Chunk I — `/academic-research:pickup`

**Reihenfolge:** TDD-strikt — jede Aufgabe: failing test → impl → passing test → commit.

---

## Task 1 — Fixtures anlegen

**Keine Tests nötig (reine Daten).**

Erstelle `tests/fixtures/pickup/`:
- `book_vor_ort.json`
- `book_fernleihe.json`
- `paper_online_oa.json`
- `paper_lizenz.json`
- `thesis_no_status.json`

Commit: `feat(I): add pickup test fixtures (5 sources)`

---

## Task 2 — `barcode.py`: Code128-PNG-Generierung

**RED:** `test_barcode_generates_png` und `test_barcode_invalid_isbn` schreiben
(im noch nicht existierenden `tests/test_pickup_excel.py`).
Beide Tests importieren `from scripts.barcode import generate_isbn_barcode` —
`scripts/barcode.py` existiert noch nicht → ImportError → RED.

**GREEN:** `scripts/barcode.py` mit `generate_isbn_barcode(isbn, output_path=None)`.
- Nutzt `python-barcode` (Code128).
- Schreibt PNG in `output_path` oder `tempfile.mktemp(".png")`.
- Gibt Pfad zurück; bei fehlendem Lib oder leerer ISBN → `None`.

**Commit:** `feat(I): barcode.py — Code128 PNG generation (TDD)`

---

## Task 3 — Sheet-Zuordnung (`assign_sheet`)

**RED:** `test_sheet_assignment` + `test_no_status_defaults_to_lizenz` in
`tests/test_pickup_excel.py`.
Importiert `from scripts.barcode import assign_sheet` — nicht vorhanden → RED.

**GREEN:** `assign_sheet(entry: dict) -> str` in `scripts/barcode.py`.
- Liest `entry.get("availability_status")`.
- Mapping: `vor_ort_verfuegbar` → `Vor Ort verfügbar`, `fernleihe` → `Fernleihe`,
  `online_oa` → `Online OA`, alles andere / kein Wert → `Lizenz nötig`.

**Commit:** `feat(I): assign_sheet() — availability_status → Sheet-Mapping (TDD)`

---

## Task 4 — Integration-Test (`test_pickup_command_integration`)

**RED:** `test_pickup_command_integration` in `tests/test_pickup_excel.py`.
Ruft `build_pickup_sheets(entries)` auf (noch nicht existiert) — RED.
Test prüft: Rückgabe ist Dict mit 4 Keys = Sheet-Namen; alle 5 Fixtures landen je
im korrekten Sheet.

**GREEN:** `build_pickup_sheets(entries: list[dict]) -> dict[str, list[dict]]`
in `scripts/barcode.py`. Iteriert Entries, ruft `assign_sheet(e)` auf, gruppiert.

**Commit:** `feat(I): build_pickup_sheets() — groups entries by sheet (TDD)`

---

## Task 5 — `commands/pickup.md` Slash-Command

Kein pytest-Test (Markdown-Command-Definition).
Definiert:
- Command-Name, Beschreibung, Input-Schema.
- Workflow-Schritte: Vault-Entries lesen → barcode.py → document-skills:xlsx Skill
  aufrufen.
- Dependency-Hinweis: `python-barcode`, `document-skills:xlsx`-Skill.
- Graceful-Error-Handling wenn Skill nicht verfügbar.

**Commit:** `feat(I): commands/pickup.md — slash command definition`

---

## Task 6 — Phase 4 Polish + Code-Review

1. `code-simplifier`-Plugin auf Diff vs. `origin/main` anwenden.
2. `pytest tests/ -v --ignore=tests/evals --ignore=tests/test_book_resolve.py` — alle grün.
3. Bei Fehlern nach Simplifier: file-by-file revert.
4. Commit: `chore: code-simplifier polish`.
5. `/code-review` (local, no `--comment`). Findings ≥80: fix, re-test, commit. Cap 3.

---

## Abhängigkeiten / Risiko-Notizen

- `python-barcode` muss in `~/.academic-research/venv` verfügbar sein → prüfen in Task 2.
- `document-skills:xlsx` Skill wird in `commands/pickup.md` referenziert, aber in
  Tests gemockt (kein echter Skill-Aufruf in pytest).
- ISBN-Normalisierung: `python-barcode` akzeptiert ISBN-13 direkt; ISBN-10 → ISBN-13
  Konvertierung optional (nice-to-have, kein AC).
