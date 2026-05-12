# Spec: #119 — evals: Vault-Interface-Migration

## Kontext

Wave 2 hat die Implementierungen migriert:
- `quote-extractor`: nimmt jetzt `paper_id` als Input statt `pdf_text`; persistiert Quotes via `vault.add_quote()` → gibt `vault_quote_id` zurück.
- `chapter-writer`: zieht Quellen via `vault.search()` + `vault.find_quotes()` statt inline-Quellenliste.
- `citation-extraction`: nutzt `vault.find_quotes(paper_id, query)` + `vault.get_quote(quote_id)`.

Die evals.json-Dateien referenzieren noch das alte PDF-Text-Interface. Dieses Ticket migriert die Eval-Cases auf das neue Vault-Interface und ergänzt Assertions auf Vault-spezifische Outputs.

---

## Designentscheidungen

### Mock-Vault

**Entscheidung: in-memory dict-stub in conftest.py**

Begründung:
- Kein echter ANTHROPIC_API_KEY vorhanden → Tests müssen ohne LLM-Call sammelbar sein.
- SQLite-tempDB wäre schwerer aufzusetzen und überdimensioniert für reine Input-Format-Validierung.
- Die bestehenden Tests nutzen `pytest.skip` via `require_api_key()` für alle LLM-Calls — Mock-Vault wird nur für die strukturellen Vault-Assertions genutzt.

**Mock-Vault-Fixture (in conftest.py):**
```python
@pytest.fixture
def mock_vault():
    """In-memory dict-stub, simuliert vault.add_quote / find_quotes / get_quote."""
    return MockVault()
```

`MockVault` hat:
- `add_quote(paper_id, verbatim, ...) → str` (gibt UUID zurück)
- `find_quotes(paper_id, query, k) → list[dict]`
- `get_quote(quote_id) → dict | None`
- `ensure_file(paper_id) → str` (gibt Fake-file_id zurück)

### vault_quote_id-Assertion

Die Eval-Cases für `quote-extractor` prüfen via `json_field`-Check, ob der Output ein `quotes[0].vault_quote_id`-Feld enthält (non_empty). Das ist die primäre Vault-Integration-Assertion.

### quote-extractor: paper_id-Input

Neue Input-Struktur:
```json
{
  "paper": {
    "paper_id": "devops2022",
    "title": "DevOps Governance Frameworks",
    "doi": "10.1109/MS.2022.1234567"
  },
  "research_query": "DevOps Governance",
  "max_quotes": 2,
  "max_words_per_quote": 25
}
```
`paper_id` zeigt auf ein Fake-Paper im mock_vault. Kein `pdf_text` mehr.

---

## Änderungen pro Datei

### evals/quote-extractor/evals.json

Alle 5 Cases umstellen:

| Case | Änderung |
|------|----------|
| qe-01 | Input: JSON mit `paper.paper_id="devops2022"`, kein `PDF-Text`. Expected: `json_field` auf `$.quotes[0].vault_quote_id` (non_empty). |
| qe-02 | Input: JSON mit `paper_id="zerotrust2024"`, `research_query="Zero Trust Prinzipien"`. Expected: Substring `vault_quote_id`. |
| qe-03 | Input: JSON mit `paper_id="mlops_scan_only"` (simuliert OCR-fail). Expected: bleibt `extraction_quality.*(failed|low)`. |
| qe-04 | Input: JSON mit `paper_id="agile2023"`, `research_query="SAFe Coordination"`. Expected: `json_field` auf `$.extraction_quality` exists. |
| qe-05 | Input: JSON mit `paper_id="quantum2021"`, `research_query="Post-Quantum Cryptography"`. Expected: bleibt `quotes.*\[\s*\]|total_quotes_extracted.*0`. |

### evals/chapter-writer/evals.json

3 bestehende Cases ersetzen inline-Quellenliste durch Vault-Search-Trigger.
2 neue Cases: Vault-Pfad (vault.search + vault.find_quotes).

| Case | Änderung |
|------|----------|
| cw-01 | Input: enthält `paper_ids: ["devops2022", "tanaka2024"]` statt inline-Quellenliste; instruction: "Zitiere Quellen aus dem Vault". Expected bleibt `Smith.*2023|\(Smith, 2023\)`. |
| cw-02 | Kein Vault-Bezug nötig (Übergang, keine Quellen). Unverändert. |
| cw-03 | Input: enthält `paper_ids: ["mayring2022"]`; instruction: Vault-Pfad nutzen. Expected bleibt `Mayring`. |
| cw-04 | Input: enthält `paper_ids: ["smith2023", "mueller2021"]`. Expected bleibt `(Smith|Mueller)`. |
| cw-05 | Kein Vault-Bezug (kein Quellenaufruf). Unverändert. |
| cw-vault-01 (neu) | Input: "Welche Quellen zu 'DevOps Governance' sind im Vault? Führe vault.search() aus." Expected: `json_field` auf `vault.search` call oder substring `vault_search`. |

Hinweis: Die Test-Struktur für cw (parametrize over `prompts`) bleibt erhalten. Kein Umbau von test_chapter_writer_evals.py nötig.

### evals/citation-extraction/evals.json

2 neue Workflow-Cases ergänzen (Vault als Quelle):

| Case | Beschreibung | Expected |
|------|-------------|---------|
| ce-vault-01 | `vault.find_quotes("devops2022", "DevOps Governance")` → APA7-Formatierung. Input enthält `quote_id: "q-fake-001"`. Expected: substring `Smith` + `2023`. |
| ce-vault-02 | `vault.get_quote("q-fake-001")` → Harvard-Format. Expected: regex `Smith.*2022\|Smith, J\.`. |

Die 5 bestehenden Cases bleiben unverändert (Metadaten-zu-Zitat-Workflow ist weiterhin valide lt. SKILL.md).

### tests/evals/conftest.py

Neue `mock_vault`-Fixture + `MockVault`-Klasse hinzufügen.

Fake-Papers im Mock:
- `devops2022`: title "DevOps Governance Frameworks", fake quotes.
- `zerotrust2024`: title "Zero Trust Networks".
- `mlops_scan_only`: simuliert OCR-fail.
- `agile2023`: title "Agile at Scale".
- `quantum2021`: title "Quantum Computing".
- `mayring2022`: title "Qualitative Inhaltsanalyse".
- `smith2023`, `mueller2021`, `tanaka2024`: Autor-Papers für chapter-writer.

### tests/evals/test_quote_extractor_evals.py

Neue Test-Funktion `test_quote_extractor_vault_mock(mock_vault)` ergänzen, die ohne API-Key läuft:
- Prüft, dass `mock_vault.add_quote()` eine UUID zurückgibt.
- Prüft, dass `mock_vault.find_quotes("devops2022", "governance")` nicht leer ist.

Diese Tests sind NICHT geskippt (kein API-Key nötig) — sie validieren nur den Mock selbst.

### tests/evals/test_chapter_writer_evals.py + test_citation_extraction_evals.py

Keine strukturellen Änderungen nötig — parametrize over `prompts` aus evals.json funktioniert automatisch mit den neuen Cases.

---

## Smoke-Validierung

Nach Implementierung:
1. `python -c "import json; json.load(open('evals/quote-extractor/evals.json'))"` — muss fehlerfrei.
2. `python -c "import json; json.load(open('evals/chapter-writer/evals.json'))"` — muss fehlerfrei.
3. `python -c "import json; json.load(open('evals/citation-extraction/evals.json'))"` — muss fehlerfrei.
4. `pytest tests/evals/ --collect-only -q` — muss fehlerfrei collecten.
5. `pytest tests/evals/test_quote_extractor_evals.py -k "vault_mock" -v` — muss PASS (kein API-Key nötig).

---

## Out of Scope

- Implementierungscode in agents/skills (fertig in PR #118).
- eval_runner.py umbau (kein strukturelles Refactor nötig).
- Echter LLM-Call in CI (bleibt hinter skipif ANTHROPIC_API_KEY).
