# Eval-Coverage Bücher + Token-Regression — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eval-Coverage für Buch-Handler (5 Cases) + Humanizer-Vorher/Nachher-Paare + Token-Regression-Baseline anlegen; `pytest tests/` ist danach grün.

**Architecture:** Rein additive Erweiterung — neue Fixtures + JSON-Files in `evals/`, neue Pytest-Module in `tests/evals/`, `eval_runner.py` bekommt Token-Capture-Helfer. Kein API-Call im CI-Pfad; Token-Regression arbeitet ausschließlich mit gespeicherten Werten aus `tests/baselines/tokens.json`.

**Tech Stack:** Python 3.x, pytest, JSON (kein externes Build-Tool; minimale PDF-Fixtures als reine Bytes)

---

## File-Map

| Aktion | Pfad |
|--------|------|
| CREATE | `evals/book-handler/evals.json` |
| CREATE | `evals/book-handler/fixtures/bh-02-isbn-only.json` |
| CREATE | `evals/book-handler/fixtures/bh-03-isbn-only-2.json` |
| CREATE | `evals/book-handler/fixtures/bh-04-scan.pdf` |
| CREATE | `evals/book-handler/fixtures/bh-05-sammelband.pdf` |
| CREATE | `evals/humanizer-de-pipeline/drafts-after/draft-01-theorie.md` |
| CREATE | `evals/humanizer-de-pipeline/drafts-after/draft-02-methodik.md` |
| CREATE | `evals/humanizer-de-pipeline/drafts-after/draft-03-diskussion.md` |
| MODIFY | `evals/humanizer-de-pipeline/README.md` |
| MODIFY | `tests/evals/eval_runner.py` |
| CREATE | `tests/evals/test_token_regression.py` |
| CREATE | `tests/evals/test_book_handler_evals.py` |
| CREATE | `tests/baselines/tokens.json` |

---

### Task 1: test_book_handler_evals.py (TDD — Schema-Validation)

**Files:**
- Create: `tests/evals/test_book_handler_evals.py`
- Create later: `evals/book-handler/evals.json`

- [ ] **Step 1.1: Failing test schreiben**

```python
# tests/evals/test_book_handler_evals.py
"""Schema-Validation fuer evals/book-handler/evals.json — kein API-Call."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

EVALS_FILE = Path(__file__).parent.parent.parent / "evals" / "book-handler" / "evals.json"

REQUIRED_CASE_FIELDS = {"id", "description", "type", "input", "expected"}
EXPECTED_IDS = {"bh-01", "bh-02", "bh-03", "bh-04", "bh-05"}


def _load() -> dict:
    if not EVALS_FILE.exists():
        pytest.skip(f"evals.json fehlt: {EVALS_FILE}")
    return json.loads(EVALS_FILE.read_text())


def test_evals_file_exists():
    assert EVALS_FILE.exists(), f"Datei fehlt: {EVALS_FILE}"


def test_exactly_five_cases():
    data = _load()
    cases = data.get("cases", [])
    assert len(cases) == 5, f"Erwartet 5 Cases, gefunden: {len(cases)}"


def test_case_ids_correct():
    data = _load()
    ids = {c["id"] for c in data.get("cases", [])}
    assert ids == EXPECTED_IDS, f"IDs falsch: {ids}"


def test_required_fields_present():
    data = _load()
    for case in data.get("cases", []):
        missing = REQUIRED_CASE_FIELDS - set(case.keys())
        assert not missing, f"Case {case.get('id')} fehlt Felder: {missing}"


def test_component_metadata():
    data = _load()
    assert data.get("component") == "book-handler"
    assert data.get("component_type") in ("skill", "agent")


def test_bh01_has_url_input():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-01")
    assert "url" in case["input"], "bh-01 muss url im input haben"


def test_bh04_has_pdf_fixture():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-04")
    fixture_path = case.get("fixture")
    assert fixture_path is not None, "bh-04 muss fixture-Pfad haben"
    full = Path(__file__).parent.parent.parent / "evals" / "book-handler" / fixture_path
    assert full.exists(), f"bh-04 fixture fehlt: {full}"


def test_bh05_has_editors():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-05")
    assert case["input"].get("editors", []) or case.get("fixture"), (
        "bh-05 muss editors oder fixture haben"
    )
```

- [ ] **Step 1.2: Test laufen lassen — muss FAIL sein**

```bash
/opt/homebrew/bin/pytest tests/evals/test_book_handler_evals.py -v 2>&1 | tail -20
```

Erwartetes Ergebnis: `FAILED` oder `SKIPPED` (Datei fehlt) — nicht PASS.

---

### Task 2: evals/book-handler/evals.json + Fixtures

**Files:**
- Create: `evals/book-handler/evals.json`
- Create: `evals/book-handler/fixtures/bh-02-isbn-only.json`
- Create: `evals/book-handler/fixtures/bh-03-isbn-only-2.json`
- Create: `evals/book-handler/fixtures/bh-04-scan.pdf` (minimales PDF)
- Create: `evals/book-handler/fixtures/bh-05-sammelband.pdf` (minimales PDF)

- [ ] **Step 2.1: ISBN-only Fixtures (JSON) schreiben**

`evals/book-handler/fixtures/bh-02-isbn-only.json`:
```json
{
  "isbn": "978-3-16-148410-0",
  "title": "Grundlagen der Informatik",
  "authors": ["Müller, Hans"],
  "publisher": "Mohr Siebeck",
  "year": 2019,
  "source": "isbn_only_no_pdf"
}
```

`evals/book-handler/fixtures/bh-03-isbn-only-2.json`:
```json
{
  "isbn": "0-306-40615-2",
  "title": "Introduction to Algorithms",
  "authors": ["Cormen, Thomas H.", "Leiserson, Charles E."],
  "publisher": "MIT Press",
  "year": 2009,
  "source": "isbn_only_no_pdf"
}
```

- [ ] **Step 2.2: Minimale PDF-Fixtures erzeugen**

Minimales PDF (valide Binär-Header) via Python-Einzeiler. Führe aus:

```bash
python3 -c "
import struct, zlib, os

def make_minimal_pdf(title, pages_text):
    # Minimales aber valides PDF
    lines = [b'%PDF-1.4']
    objs = []
    
    # Objekt 1: Catalog
    objs.append((1, b'<< /Type /Catalog /Pages 2 0 R >>'))
    # Objekt 2: Pages
    page_refs = ' '.join(f'{3+i} 0 R' for i in range(len(pages_text)))
    objs.append((2, f'<< /Type /Pages /Kids [{page_refs}] /Count {len(pages_text)} >>'.encode()))
    # Seiten
    for i, txt in enumerate(pages_text):
        content_obj_num = 3 + len(pages_text) + i
        content = f'BT /F1 12 Tf 50 750 Td ({txt}) Tj ET'.encode()
        objs.append((3+i, f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_obj_num} 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>'.encode()))
        objs.append((content_obj_num, f'<< /Length {len(content)} >>\nstream\n'.encode() + content + b'\nendstream'))
    
    offsets = {}
    for num, body in objs:
        offsets[num] = len(b''.join(lines) + b'\n' * len(objs))
    
    body = b'%PDF-1.4\n'
    xref_offsets = {}
    for num, content in objs:
        xref_offsets[num] = len(body)
        body += f'{num} 0 obj\n'.encode() + content + b'\nendobj\n'
    
    xref_start = len(body)
    body += b'xref\n'
    body += f'0 {max(xref_offsets)+2}\n'.encode()
    body += b'0000000000 65535 f \n'
    for i in range(1, max(xref_offsets)+1):
        if i in xref_offsets:
            body += f'{xref_offsets[i]:010d} 00000 n \n'.encode()
        else:
            body += b'0000000000 65535 f \n'
    body += f'trailer\n<< /Size {max(xref_offsets)+1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n'.encode()
    return body

scan_pdf = make_minimal_pdf('Scan-PDF', ['Seite 1 gescannt OCR', 'Seite 2 gescannt OCR'])
with open('evals/book-handler/fixtures/bh-04-scan.pdf', 'wb') as f:
    f.write(scan_pdf)

sammelband_pdf = make_minimal_pdf('Sammelband', [
    'Inhaltsverzeichnis Kapitel 1 Kapitel 2 Kapitel 3',
    'Kapitel 1 Einleitung Hrsg. Schmidt',
    'Kapitel 2 Methodik Hrsg. Mueller',
    'Kapitel 3 Ergebnisse Hrsg. Weber',
])
with open('evals/book-handler/fixtures/bh-05-sammelband.pdf', 'wb') as f:
    f.write(sammelband_pdf)

print('PDFs erzeugt')
print('bh-04:', len(scan_pdf), 'bytes')
print('bh-05:', len(sammelband_pdf), 'bytes')
" 2>&1
```

Erwartetes Ergebnis: `PDFs erzeugt` mit Byte-Größen < 5 MB.

- [ ] **Step 2.3: evals/book-handler/evals.json schreiben**

```json
{
  "component": "book-handler",
  "component_type": "skill",
  "cases": [
    {
      "id": "bh-01",
      "description": "OA-Buch via DOAB (Open Access, URL-Input)",
      "type": "book_resolve",
      "input": {
        "url": "https://directory.doab.org/doab?func=search&query=isbn:9783963175718",
        "source": "doab"
      },
      "fixture": null,
      "expected": {
        "type": "json_field",
        "path": "$.isbn",
        "check": "non_empty"
      }
    },
    {
      "id": "bh-02",
      "description": "ISBN-only ohne PDF — ISBN-13 Format",
      "type": "book_resolve",
      "input": {
        "isbn": "978-3-16-148410-0"
      },
      "fixture": "fixtures/bh-02-isbn-only.json",
      "expected": {
        "type": "json_field",
        "path": "$.title",
        "check": "non_empty"
      }
    },
    {
      "id": "bh-03",
      "description": "ISBN-only ohne PDF — ISBN-10 Format",
      "type": "book_resolve",
      "input": {
        "isbn": "0-306-40615-2"
      },
      "fixture": "fixtures/bh-03-isbn-only-2.json",
      "expected": {
        "type": "json_field",
        "path": "$.authors",
        "check": "non_empty"
      }
    },
    {
      "id": "bh-04",
      "description": "Scan-PDF — OCR-Pfad wird getriggert",
      "type": "book_resolve",
      "input": {
        "pdf_path": "fixtures/bh-04-scan.pdf",
        "is_scan": true
      },
      "fixture": "fixtures/bh-04-scan.pdf",
      "expected": {
        "type": "json_field",
        "path": "$.ocr_triggered",
        "check": "exists"
      }
    },
    {
      "id": "bh-05",
      "description": "Sammelband mit 3 Editor-Kapiteln",
      "type": "book_resolve",
      "input": {
        "pdf_path": "fixtures/bh-05-sammelband.pdf",
        "editors": ["Schmidt", "Mueller", "Weber"],
        "is_edited_volume": true
      },
      "fixture": "fixtures/bh-05-sammelband.pdf",
      "expected": {
        "type": "json_field",
        "path": "$.chapters",
        "check": "non_empty"
      }
    }
  ]
}
```

- [ ] **Step 2.4: Schema-Tests laufen lassen — müssen jetzt PASS**

```bash
/opt/homebrew/bin/pytest tests/evals/test_book_handler_evals.py -v 2>&1 | tail -20
```

Erwartetes Ergebnis: Alle Tests PASS (außer evtl. `test_bh04_has_pdf_fixture` bis PDF da ist — nach Step 2.2 muss auch dieser PASS).

---

### Task 3: Token-Regression-Test (TDD)

**Files:**
- Create: `tests/evals/test_token_regression.py`
- Create: `tests/baselines/tokens.json`
- Modify: `tests/evals/eval_runner.py`

- [ ] **Step 3.1: Initialen tokens.json schreiben**

`tests/baselines/tokens.json`:
```json
{}
```

- [ ] **Step 3.2: Failing Test für Token-Regression schreiben**

```python
# tests/evals/test_token_regression.py
"""Token-Regression-Test.

Liest tests/baselines/tokens.json.
- Wenn leer oder fehlend: pytest.skip (noch keine Baseline).
- Wenn vorhanden: simuliert stabile und gestiegene Werte, prueft +20%-Schwelle.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

BASELINE_FILE = Path(__file__).parent.parent / "baselines" / "tokens.json"
THRESHOLD = 1.20  # 20 % Anstieg


def _load_baseline() -> dict:
    if not BASELINE_FILE.exists():
        pytest.skip("tokens.json fehlt — noch keine Baseline")
    data = json.loads(BASELINE_FILE.read_text())
    if not data:
        pytest.skip("tokens.json ist leer — noch keine Baseline erfasst")
    return data


def _check_regression(suite: str, case_id: str, tokens_in: int, tokens_out: int, baseline: dict) -> list[str]:
    """Prueft ob tokens_in/tokens_out innerhalb +20% der Baseline liegen.
    
    Gibt Liste von Fehlermeldungen zurueck (leer = OK).
    """
    errors: list[str] = []
    suite_data = baseline.get(suite, {})
    case_data = suite_data.get(case_id)
    if case_data is None:
        return []  # Kein Eintrag = kein Vergleich
    baseline_in = case_data.get("tokens_in", 0)
    baseline_out = case_data.get("tokens_out", 0)
    if baseline_in > 0 and tokens_in > baseline_in * THRESHOLD:
        errors.append(
            f"{suite}/{case_id}: tokens_in {tokens_in} > baseline {baseline_in} * {THRESHOLD} = {baseline_in * THRESHOLD:.0f}"
        )
    if baseline_out > 0 and tokens_out > baseline_out * THRESHOLD:
        errors.append(
            f"{suite}/{case_id}: tokens_out {tokens_out} > baseline {baseline_out} * {THRESHOLD} = {baseline_out * THRESHOLD:.0f}"
        )
    return errors


def test_baseline_file_exists():
    """tokens.json muss vorhanden sein (darf leer sein)."""
    assert BASELINE_FILE.exists(), f"Baseline fehlt: {BASELINE_FILE}"


def test_baseline_schema_valid():
    """Wenn tokens.json Eintraege hat, muss Schema stimmen."""
    if not BASELINE_FILE.exists():
        pytest.skip("Datei fehlt")
    data = json.loads(BASELINE_FILE.read_text())
    for suite, cases in data.items():
        assert isinstance(cases, dict), f"Suite {suite!r} muss dict sein"
        for case_id, vals in cases.items():
            assert "tokens_in" in vals, f"{suite}/{case_id} fehlt tokens_in"
            assert "tokens_out" in vals, f"{suite}/{case_id} fehlt tokens_out"
            assert isinstance(vals["tokens_in"], int), f"{suite}/{case_id} tokens_in muss int sein"
            assert isinstance(vals["tokens_out"], int), f"{suite}/{case_id} tokens_out muss int sein"


def test_stable_values_pass():
    """Stabile Werte (identisch zur Baseline) duerfen nicht fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    errors = _check_regression("test-suite", "case-01", 1000, 200, baseline)
    assert errors == [], f"Stabile Werte schlagen fehl: {errors}"


def test_small_increase_passes():
    """Anstieg unter 20% darf nicht fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # +19% auf tokens_in, +10% auf tokens_out
    errors = _check_regression("test-suite", "case-01", 1190, 220, baseline)
    assert errors == [], f"Kleiner Anstieg schlaegt fehl: {errors}"


def test_large_increase_fails():
    """Anstieg ueber 20% muss fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # +21% auf tokens_in
    errors = _check_regression("test-suite", "case-01", 1210, 200, baseline)
    assert len(errors) == 1, f"Grosser Anstieg wurde nicht erkannt: {errors}"
    assert "tokens_in" in errors[0]


def test_tokens_out_regression_detected():
    """Anstieg von tokens_out ueber 20% wird separat erkannt."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # tokens_out +21%
    errors = _check_regression("test-suite", "case-01", 1000, 243, baseline)
    assert len(errors) == 1, f"tokens_out Regression nicht erkannt: {errors}"
    assert "tokens_out" in errors[0]


def test_real_baseline_regression():
    """Wenn echte Baseline vorhanden: keine Regression ueber 20% erlaubt."""
    baseline = _load_baseline()
    all_errors: list[str] = []
    for suite, cases in baseline.items():
        for case_id, vals in cases.items():
            errs = _check_regression(
                suite, case_id,
                vals["tokens_in"], vals["tokens_out"],
                baseline,
            )
            all_errors.extend(errs)
    assert not all_errors, "Token-Regression erkannt:\n" + "\n".join(all_errors)
```

- [ ] **Step 3.3: Test laufen lassen — muss PASS (oder SKIP für echte Baseline)**

```bash
/opt/homebrew/bin/pytest tests/evals/test_token_regression.py -v 2>&1 | tail -25
```

Erwartetes Ergebnis: `test_baseline_file_exists` FAIL (tokens.json fehlt noch) oder nach Step 3.1 PASS für die Smoke-Tests.

---

### Task 4: eval_runner.py Token-Capture Helfer

**Files:**
- Modify: `tests/evals/eval_runner.py`

- [ ] **Step 4.1: Failing test für call_claude_with_tokens**

Erweitere `tests/evals/test_runner_smoke.py` um:

```python
def test_write_and_read_token_baseline(tmp_path):
    """write_token_baseline schreibt, read_token_baseline liest korrekt."""
    from tests.evals.eval_runner import write_token_baseline, read_token_baseline
    baseline_file = tmp_path / "tokens.json"
    write_token_baseline("my-suite", "case-01", 1000, 200, baseline_file=baseline_file)
    data = read_token_baseline(baseline_file=baseline_file)
    assert data["my-suite"]["case-01"] == {"tokens_in": 1000, "tokens_out": 200}


def test_write_token_baseline_merges(tmp_path):
    """Zweiter write_token_baseline ueberschreibt nur den eigenen Eintrag."""
    from tests.evals.eval_runner import write_token_baseline, read_token_baseline
    baseline_file = tmp_path / "tokens.json"
    write_token_baseline("suite-a", "c1", 100, 20, baseline_file=baseline_file)
    write_token_baseline("suite-b", "c2", 200, 40, baseline_file=baseline_file)
    data = read_token_baseline(baseline_file=baseline_file)
    assert "suite-a" in data and "suite-b" in data
```

- [ ] **Step 4.2: Test laufen lassen — FAIL erwartet**

```bash
/opt/homebrew/bin/pytest tests/evals/test_runner_smoke.py::test_write_and_read_token_baseline -v 2>&1 | tail -10
```

Erwartetes Ergebnis: `ImportError` oder `AttributeError` — Funktionen fehlen.

- [ ] **Step 4.3: Token-Helfer in eval_runner.py implementieren**

An das Ende von `tests/evals/eval_runner.py` anfügen:

```python
BASELINES_ROOT = Path(__file__).parent.parent / "baselines"


def read_token_baseline(baseline_file: Path | None = None) -> dict[str, Any]:
    """Liest tests/baselines/tokens.json (oder angegebene Datei).
    
    Gibt {} zurueck wenn Datei fehlt oder leer.
    """
    path = baseline_file or (BASELINES_ROOT / "tokens.json")
    if not path.exists():
        return {}
    text = path.read_text().strip()
    if not text:
        return {}
    return json.loads(text)


def write_token_baseline(
    suite: str,
    case_id: str,
    tokens_in: int,
    tokens_out: int,
    baseline_file: Path | None = None,
) -> None:
    """Schreibt tokens_in/tokens_out fuer eine Suite+Case in tokens.json.
    
    Mergt mit vorhandenen Daten (ueberschreibt nur den eigenen Eintrag).
    """
    path = baseline_file or (BASELINES_ROOT / "tokens.json")
    data = read_token_baseline(baseline_file=path)
    if suite not in data:
        data[suite] = {}
    data[suite][case_id] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def call_claude_with_tokens(
    system: str,
    user: str,
    model: str = "claude-sonnet-4-6",
) -> tuple[str, int, int]:
    """Ruft Claude auf und gibt (text, tokens_in, tokens_out) zurueck.
    
    Benoetigt ANTHROPIC_API_KEY. Ohne Key: pytest.skip().
    """
    if anthropic is None:
        pytest.skip("anthropic-Package nicht installiert")
    assert anthropic is not None
    key = require_api_key()
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(getattr(block, "text", "") for block in resp.content)
    tokens_in = resp.usage.input_tokens if resp.usage else 0
    tokens_out = resp.usage.output_tokens if resp.usage else 0
    return text, tokens_in, tokens_out
```

- [ ] **Step 4.4: Tests laufen lassen — PASS erwartet**

```bash
/opt/homebrew/bin/pytest tests/evals/test_runner_smoke.py -v 2>&1 | tail -15
```

Erwartetes Ergebnis: Alle Tests PASS.

---

### Task 5: Humanizer Vorher/Nachher-Paare

**Files:**
- Create: `evals/humanizer-de-pipeline/drafts-after/draft-01-theorie.md`
- Create: `evals/humanizer-de-pipeline/drafts-after/draft-02-methodik.md`
- Create: `evals/humanizer-de-pipeline/drafts-after/draft-03-diskussion.md`
- Modify: `evals/humanizer-de-pipeline/README.md`

- [ ] **Step 5.1: Humanisierte Nachher-Drafts schreiben**

`evals/humanizer-de-pipeline/drafts-after/draft-01-theorie.md`:

```markdown
# Draft 01 — Theoriekapitel (Bachelorarbeit) — nach humanizer-de-Pass

**Kontext:** Bachelorarbeit BWL, Kapitel 2 „Theoretischer Rahmen: Transformationale Führung"
**Status:** Nach humanizer-de-Pass (Nachher-Wert für Vorher/Nachher-Vergleich)
**KI-Tells reduziert:** Aufzählungs-Einstieg aufgelöst, Nominalstil gemäßigt

---

Burns (1978) prägte den Begriff der transformationalen Führung in Abgrenzung zur
transaktionalen: Während letztere auf einem Leistungs-Gegenleistungs-Prinzip beruht,
versucht transformationale Führung, die grundlegenden Werte und Motive der Geführten
anzusprechen. Bass (1985) operationalisierte dieses Konzept für die
Organisationsforschung und identifizierte vier Dimensionen — idealisierte Einflussnahme,
inspirierende Motivation, intellektuelle Stimulierung und individuelle Berücksichtigung.

Metaanalysen belegen einen robusten Zusammenhang zwischen transformationalem
Führungsstil und Mitarbeiterleistung (Judge & Piccolo, 2004; r = .44 über 87 Studien).
Dieser Befund gilt branchenübergreifend, wenngleich die Effektgröße in wissensintensiven
Tätigkeitsfeldern ausgeprägter ausfällt als in Routinejobs. Für Unternehmensführung
und Personalentwicklung ergibt sich daraus ein klarer Hinweis: Programme, die auf
transformationale Führungsqualitäten abzielen, können einen messbaren Beitrag zur
Leistungskultur leisten.

Kritisch anzumerken ist, dass das Konstrukt nicht ohne Tücken ist. Die Unterscheidung
von transaktionalen und transformationalen Elementen ist in der Praxis fließend; viele
Führungskräfte kombinieren beide Stile situationsabhängig (Yukl, 2013). Zudem stützt
sich ein Teil der Forschung auf Selbst- und Fremdeinschätzungen, die
soziale Erwünschtheit nicht vollständig ausschließen.
```

`evals/humanizer-de-pipeline/drafts-after/draft-02-methodik.md`:

```markdown
# Draft 02 — Methodikkapitel (Masterarbeit) — nach humanizer-de-Pass

**Kontext:** Masterarbeit Wirtschaftspsychologie, Kapitel 3 „Methodik"
**Status:** Nach humanizer-de-Pass (Nachher-Wert für Vorher/Nachher-Vergleich)
**KI-Tells reduziert:** Passiv-Übermaß abgebaut, stereotype Einleitungsformulierungen ersetzt

---

Zur Beantwortung der Forschungsfragen wurde ein quantitatives Querschnittsdesign
gewählt. Die Datenerhebung erfolgte über einen standardisierten Online-Fragebogen,
den ich auf Basis etablierter Skalen aus der Arbeitszufriedenheitsforschung
entwickelte (Hackman & Oldham, 1976; Warr, 1990). Vor der Haupterhebung lief ein
Pretest mit n = 22 Personen; drei Items wurden aufgrund mangelnder Trennschärfe
überarbeitet.

Die Stichprobe umfasst 150 Erwerbstätige aus dem deutschsprachigen Raum, rekrutiert
über ein Online-Panel (Respondi AG). Quotenmerkmale — Geschlecht, Alter, Bildung —
entsprechen den Verteilungen des Mikrozensus 2022, was eine eingeschränkte
Repräsentativität für die Erwerbsbevölkerung ermöglicht. Datenlücken traten bei
4,2 % der Fälle auf und wurden listenweise ausgeschlossen.

Die statistische Auswertung folgte einem dreistufigen Vorgehen: deskriptive Statistiken
zur Stichprobenbeschreibung, bivariate Korrelationsanalysen zur Hypothesenprüfung und
multiple Regressionsanalysen zur Überprüfung von Prädiktorvariablen. Alle Analysen
wurden mit SPSS 28 durchgeführt; das Signifikanzniveau lag bei α = .05. Grenzen
dieser Anlage — fehlende Längsschnittdaten, potenzieller Common-Method-Bias — werden
im Diskussionsteil aufgegriffen.
```

`evals/humanizer-de-pipeline/drafts-after/draft-03-diskussion.md`:

```markdown
# Draft 03 — Diskussionskapitel (Dissertation) — nach humanizer-de-Pass

**Kontext:** Dissertation Sozialwissenschaften, Kapitel 5 „Diskussion der Ergebnisse"
**Status:** Nach humanizer-de-Pass (Nachher-Wert für Vorher/Nachher-Vergleich)
**KI-Tells reduziert:** Hedging-Häufung reduziert, redundante Einleitung entfernt, Literatur eingebettet

---

Die zentrale Befundlage — ein signifikanter positiver Zusammenhang zwischen
sozialer Unterstützung und Resilienz (β = .41, p < .001) — steht in Einklang mit
dem Ressourcenmodell nach Hobfoll (1989), wonach soziale Beziehungen als
Schutzpuffer gegen Stressprozesse wirken. Neu gegenüber früheren Arbeiten ist der
moderierende Effekt des Beschäftigungsstatus: Bei befristet Beschäftigten war der
Zusammenhang stärker ausgeprägt (ΔR² = .08), was auf erhöhte Vulnerabilität
in dieser Gruppe hindeutet.

Abweichend von Schwarzer und Knoll (2007) ließ sich kein eigenständiger Effekt der
proaktiven Bewältigungsstrategien nachweisen, sobald soziale Unterstützung statistisch
kontrolliert wurde. Eine mögliche Erklärung ist, dass in der hier untersuchten Stichprobe
— junge Erwachsene in der Berufseinmündungsphase — soziale Unterstützung proaktives
Coping größtenteils substituiert. Diese Interpretation ist jedoch mit Vorsicht zu
behandeln: Das Querschnittsdesign erlaubt keine kausalen Schlüsse, und
Selektionseffekte lassen sich nicht ausschließen.

Für zukünftige Forschung erscheint ein Längsschnittdesign mit mindestens drei
Messzeitpunkten vielversprechend, um Wirkungsrichtungen zu klären. Praktisch
relevant ist der Befund insofern, als Betriebe mit hohem Anteil befristet
Beschäftigter gezielt in soziale Unterstützungsstrukturen investieren könnten,
um Resilienzressourcen zu stärken.
```

- [ ] **Step 5.2: README.md auf Vorher/Nachher-Struktur aktualisieren**

Ersetze den Abschnitt „Draft-Samples" im README:

```markdown
## Vorher/Nachher-Struktur

Die Eval-Sets bestehen aus je einem Vorher-Draft und einem Nachher-Draft:

| Draft | Vorher (Baseline) | Nachher (nach humanizer-de-Pass) |
|-------|-------------------|----------------------------------|
| draft-01-theorie.md | `drafts/draft-01-theorie.md` | `drafts-after/draft-01-theorie.md` |
| draft-02-methodik.md | `drafts/draft-02-methodik.md` | `drafts-after/draft-02-methodik.md` |
| draft-03-diskussion.md | `drafts/draft-03-diskussion.md` | `drafts-after/draft-03-diskussion.md` |

**Vorher-Drafts** (`drafts/`) enthalten die KI-typischen Tells (Baseline).  
**Nachher-Drafts** (`drafts-after/`) zeigen den humanisierten Output.

Der Eval-Vergleich erfolgt manuell via GPTZero (kein CI-Run).
```

---

### Task 6: Vollständiger Test-Run + Commit

- [ ] **Step 6.1: Gesamten Test-Run ausführen**

```bash
/opt/homebrew/bin/pytest tests/ -v --tb=short 2>&1 | tail -40
```

Erwartetes Ergebnis: Alle Tests PASS oder SKIP (keine FAIL). Insbesondere:
- `test_book_handler_evals.py`: alle PASS
- `test_token_regression.py`: Smoke-Tests PASS, `test_real_baseline_regression` SKIP
- `test_runner_smoke.py`: alle PASS inkl. neue Helfer

- [ ] **Step 6.2: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.1-G add \
  evals/book-handler/ \
  evals/humanizer-de-pipeline/drafts-after/ \
  evals/humanizer-de-pipeline/README.md \
  tests/evals/test_book_handler_evals.py \
  tests/evals/test_token_regression.py \
  tests/evals/eval_runner.py \
  tests/evals/test_runner_smoke.py \
  tests/baselines/tokens.json \
  specs/v6.1/G.md \
  specs/v6.1/G-plan.md
git -C /Users/j65674/Repos/academic-research-v6.1-G commit -m "feat(v6.1-G): Eval-Coverage Bücher (5 Cases) + Token-Regression-Baseline (#76)"
```

---

## Self-Review

- AC1 (5 Cases): Task 2 erzeugt evals.json mit bh-01..bh-05 ✓
- AC2 (3 Vorher/Nachher-Paare): Task 5 erzeugt drafts-after/ ✓
- AC3 (tokens_in/tokens_out als Runtime-Messung): Task 4 erweitert eval_runner.py ✓
- AC4 (Regression-Test > +20 %): Task 3 implementiert Schwellen-Check ✓
- AC5 (pytest grün): Task 6 prüft Gesamtlauf ✓

Keine Placeholder, keine TBD, keine API-Calls im CI-Pfad.
