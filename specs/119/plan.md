# Plan: #119 — evals: Vault-Interface-Migration

## Commit-Sequenz

### Commit 1: MockVault-Fixture (TDD: Failing Test → Implementation)

**Failing test first:**
Neue Datei `tests/evals/test_quote_extractor_evals.py` — Funktion `test_quote_extractor_vault_mock` ruft `mock_vault.add_quote()` auf → ImportError / fixture-not-found bevor conftest.py angepasst.

**Tasks:**
1. In `tests/evals/test_quote_extractor_evals.py` `test_quote_extractor_vault_mock`-Funktion ergänzen (ruft `mock_vault`-Fixture auf).
2. Run: `pytest tests/evals/test_quote_extractor_evals.py -k vault_mock` → FAIL (fixture unknown).
3. In `tests/evals/conftest.py` `MockVault`-Klasse + `mock_vault`-Fixture ergänzen.
4. Run: `pytest tests/evals/test_quote_extractor_evals.py -k vault_mock` → GREEN.

**Commit-Message:** `test(evals): MockVault-Fixture in conftest.py`

---

### Commit 2: quote-extractor evals.json — Vault-Interface

**Tasks:**
1. `evals/quote-extractor/evals.json` — alle 5 Cases auf `paper_id`-Input umstellen + vault_quote_id-Assertions.
2. JSON-Syntax-Check: `python -c "import json; json.load(open(...))"`.
3. `pytest tests/evals/test_quote_extractor_evals.py --collect-only` → fehlerfrei.

**Commit-Message:** `feat(evals): quote-extractor evals.json auf Vault-Interface migrieren`

---

### Commit 3: chapter-writer evals.json — Vault-Pfad

**Tasks:**
1. `evals/chapter-writer/evals.json` — cw-01/03/04 auf `paper_ids`-Input; cw-vault-01 neu.
2. JSON-Syntax-Check.
3. `pytest tests/evals/test_chapter_writer_evals.py --collect-only` → fehlerfrei.

**Commit-Message:** `feat(evals): chapter-writer evals.json Vault-Pfad ergänzen`

---

### Commit 4: citation-extraction evals.json — Vault-Cases

**Tasks:**
1. `evals/citation-extraction/evals.json` — ce-vault-01 und ce-vault-02 ergänzen.
2. JSON-Syntax-Check.
3. `pytest tests/evals/test_citation_extraction_evals.py --collect-only` → fehlerfrei.

**Commit-Message:** `feat(evals): citation-extraction evals.json Vault-Cases ergänzen`

---

### Commit 5: Smoke-Validation + ggf. Korrekturen

**Tasks:**
1. `pytest tests/evals/ --collect-only -q` — alle 3 Suites fehlerfrei.
2. `pytest tests/evals/test_quote_extractor_evals.py -k vault_mock -v` — PASS.
3. Finale Bereinigung.

**Commit-Message:** `test(evals): Smoke-Validation alle drei Vault-Eval-Suites`
