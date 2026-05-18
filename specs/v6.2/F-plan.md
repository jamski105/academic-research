# generic-fetcher Subagent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementiert `agents/generic-fetcher.md` als Fallback-Discovery-Subagent mit DOM-Heuristiken (PDF-Link, Paywall, Captcha, Titelabgleich) und validiert Frontmatter + Output-Schema via pytest.

**Architecture:** Reine Markdown-Agent-Datei (kein Python-Code im Produktivsystem); Tests prüfen YAML-Frontmatter-Vollständigkeit, System-Prompt-Inhalt (DOM-Heuristik-Keywords) und simulierte Output-Schema-Konformität gegen drei HTML-Fixtures. Keine echten Browser-Calls in Tests.

**Tech Stack:** Python 3, pytest, pyyaml, python-Levenshtein (nur Test-Dependency), Markdown (Agent-Datei)

---

## File Map

| Pfad | Aktion | Verantwortung |
|---|---|---|
| `agents/generic-fetcher.md` | CREATE | Agent-Frontmatter + System-Prompt mit DOM-Heuristiken |
| `tests/fixtures/dom_heuristics/pdf_link.html` | CREATE | HTML-Fixture: klarer PDF-Download-Link |
| `tests/fixtures/dom_heuristics/paywall.html` | CREATE | HTML-Fixture: Paywall/Access-Banner |
| `tests/fixtures/dom_heuristics/ambiguous.html` | CREATE | HTML-Fixture: kein PDF-Link, keine Paywall |
| `tests/test_generic_fetcher.py` | CREATE | Frontmatter-Validierung, Schema-Validierung, DOM-Keyword-Checks |
| `specs/v6.2/F.md` | DONE | Spec (bereits erstellt) |
| `specs/v6.2/F-plan.md` | DONE | Dieser Plan |

---

### Task 1: HTML-Fixtures anlegen

**Files:**
- Create: `tests/fixtures/dom_heuristics/pdf_link.html`
- Create: `tests/fixtures/dom_heuristics/paywall.html`
- Create: `tests/fixtures/dom_heuristics/ambiguous.html`

- [ ] **Step 1: Fixtures-Verzeichnis erstellen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.2-F/tests/fixtures/dom_heuristics
```

- [ ] **Step 2: pdf_link.html schreiben**

Datei `tests/fixtures/dom_heuristics/pdf_link.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Article: Advanced Topics in AI</title></head>
<body>
  <h1>Advanced Topics in AI</h1>
  <p>Authors: Smith, J.; Jones, A. (2023)</p>
  <div class="download-section">
    <a href="/files/advanced-topics-ai.pdf" class="btn-primary">Download PDF</a>
    <a href="/preview/advanced-topics-ai" class="btn-secondary">Vorschau</a>
  </div>
</body>
</html>
```

- [ ] **Step 3: paywall.html schreiben**

Datei `tests/fixtures/dom_heuristics/paywall.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Article: Machine Learning Methods</title></head>
<body>
  <h1>Machine Learning Methods</h1>
  <p>Authors: Brown, K. (2022)</p>
  <div class="access-section">
    <div class="paywall-banner">
      <p>Get Access to read the full article.</p>
      <a href="/subscribe" class="btn-access">Subscribe</a>
      <a href="/purchase/ml-methods" class="btn-buy">Purchase</a>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 4: ambiguous.html schreiben**

Datei `tests/fixtures/dom_heuristics/ambiguous.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Article: Quantum Computing Overview</title></head>
<body>
  <h1>Quantum Computing Overview</h1>
  <p>Authors: Lee, M. (2021)</p>
  <div class="content">
    <p>Abstract: This article provides an overview of quantum computing...</p>
    <div class="related-links">
      <a href="/related/quantum-1">Related Article 1</a>
      <a href="/related/quantum-2">Related Article 2</a>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 5: Dateien prüfen**

```bash
ls /Users/j65674/Repos/academic-research-v6.2-F/tests/fixtures/dom_heuristics/
```

Erwartet: `ambiguous.html  paywall.html  pdf_link.html`

---

### Task 2: Failing Tests schreiben (RED)

**Files:**
- Create: `tests/test_generic_fetcher.py`

- [ ] **Step 1: Test-Datei schreiben**

Datei `tests/test_generic_fetcher.py`:

```python
"""Tests for agents/generic-fetcher.md

Strategy:
- No real browser calls — all tests operate on:
  1. YAML frontmatter from agents/generic-fetcher.md
  2. System-prompt text (string checks for DOM heuristic keywords)
  3. Simulated output dicts validated against the canonical schema

Output schema (OQ9 canonical):
  {status, source, file_path?, reason?, tries[]}
"""

import os
import re
import pytest

AGENT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "agents", "generic-fetcher.md"
)
FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "fixtures", "dom_heuristics"
)


# ---------------------------------------------------------------------------
# Helper: parse frontmatter + body from agent markdown
# ---------------------------------------------------------------------------

def _parse_agent_md(path: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text) from a --- fenced markdown file."""
    import yaml

    with open(path, encoding="utf-8") as fh:
        content = fh.read()

    # Expect frontmatter between first two '---' fences
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    fm = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return fm, body


# ---------------------------------------------------------------------------
# Schema validator
# ---------------------------------------------------------------------------

VALID_STATUSES = {"success", "pickup_required", "captcha", "no_match"}


def _validate_output_schema(output: dict) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors = []

    if "status" not in output:
        errors.append("missing 'status' field")
    elif output["status"] not in VALID_STATUSES:
        errors.append(f"invalid status: {output['status']!r}")

    if "source" not in output:
        errors.append("missing 'source' field")
    elif output["source"] != "generic-fetcher":
        errors.append(f"source must be 'generic-fetcher', got {output['source']!r}")

    if "tries" not in output:
        errors.append("missing 'tries' field")
    elif not isinstance(output["tries"], list):
        errors.append("'tries' must be a list")

    if output.get("status") == "success" and "file_path" not in output:
        errors.append("status=success requires 'file_path'")

    return errors


# ---------------------------------------------------------------------------
# Task 2.1 — Frontmatter validation
# ---------------------------------------------------------------------------

class TestFrontmatter:
    """agents/generic-fetcher.md must have all required frontmatter fields."""

    def test_agent_file_exists(self):
        assert os.path.isfile(AGENT_FILE), (
            f"agents/generic-fetcher.md not found at {AGENT_FILE}"
        )

    def test_frontmatter_name(self):
        fm, _ = _parse_agent_md(AGENT_FILE)
        assert fm.get("name") == "generic-fetcher"

    def test_frontmatter_model(self):
        fm, _ = _parse_agent_md(AGENT_FILE)
        assert fm.get("model") == "sonnet"

    def test_frontmatter_max_turns(self):
        fm, _ = _parse_agent_md(AGENT_FILE)
        assert fm.get("maxTurns") == 20

    def test_frontmatter_tools_contains_browser_use(self):
        fm, _ = _parse_agent_md(AGENT_FILE)
        tools = fm.get("tools", [])
        tool_str = " ".join(str(t) for t in tools)
        assert "browser-use" in tool_str, (
            f"tools must reference browser-use, got: {tools}"
        )

    def test_frontmatter_tools_contains_read_write(self):
        fm, _ = _parse_agent_md(AGENT_FILE)
        tools = fm.get("tools", [])
        tool_str = " ".join(str(t) for t in tools)
        assert "Read" in tool_str and "Write" in tool_str, (
            f"tools must include Read and Write, got: {tools}"
        )


# ---------------------------------------------------------------------------
# Task 2.2 — DOM heuristic keyword checks in system prompt
# ---------------------------------------------------------------------------

class TestDOMHeuristics:
    """System prompt must contain all required DOM heuristic keywords."""

    POSITIVE_PDF_INDICATORS = [
        "Download PDF",
        "PDF herunterladen",
        "Get PDF",
        "Volltext (PDF)",
        "Full Text",
        "View PDF",
    ]

    NEGATIVE_PDF_INDICATORS = [
        "Vorschau",
        "Preview",
        "Sample Chapter",
    ]

    PAYWALL_SIGNALS = [
        "Get Access",
        "Purchase",
        "Subscribe",
        "Sign in to view",
        "Anmelden für Volltext",
    ]

    def test_positive_pdf_indicators_present(self):
        _, body = _parse_agent_md(AGENT_FILE)
        missing = [kw for kw in self.POSITIVE_PDF_INDICATORS if kw not in body]
        assert not missing, (
            f"System prompt missing positive PDF indicators: {missing}"
        )

    def test_negative_pdf_indicators_present(self):
        _, body = _parse_agent_md(AGENT_FILE)
        missing = [kw for kw in self.NEGATIVE_PDF_INDICATORS if kw not in body]
        assert not missing, (
            f"System prompt missing negative PDF indicators: {missing}"
        )

    def test_paywall_signals_present(self):
        _, body = _parse_agent_md(AGENT_FILE)
        missing = [kw for kw in self.PAYWALL_SIGNALS if kw not in body]
        assert not missing, (
            f"System prompt missing paywall signals: {missing}"
        )

    def test_captcha_detection_present(self):
        _, body = _parse_agent_md(AGENT_FILE)
        assert "captcha" in body.lower() or "reCAPTCHA" in body, (
            "System prompt must mention captcha detection"
        )

    def test_levenshtein_threshold_mentioned(self):
        _, body = _parse_agent_md(AGENT_FILE)
        assert "30" in body and ("levenshtein" in body.lower() or "Levenshtein" in body), (
            "System prompt must mention Levenshtein threshold of 30%"
        )

    def test_pickup_required_safety_boundary(self):
        _, body = _parse_agent_md(AGENT_FILE)
        assert "pickup_required" in body, (
            "System prompt must mention pickup_required as safety-boundary default"
        )

    def test_distinguishes_a_vs_button(self):
        _, body = _parse_agent_md(AGENT_FILE)
        assert "<a>" in body or "<a " in body, "System prompt must distinguish <a> elements"
        assert "<button>" in body or "<button " in body, (
            "System prompt must distinguish <button> elements"
        )


# ---------------------------------------------------------------------------
# Task 2.3 — Output schema validation (3 simulated cases)
# ---------------------------------------------------------------------------

class TestOutputSchema:
    """Three simulated agent outputs must conform to canonical output schema."""

    def test_case_success_pdf_link(self):
        """Site with clear PDF download link -> status: success."""
        output = {
            "status": "success",
            "source": "generic-fetcher",
            "file_path": "/tmp/advanced-topics-ai.pdf",
            "reason": "Found 'Download PDF' link, downloaded successfully.",
            "tries": ["Navigated to page", "Found Download PDF anchor", "Downloaded PDF"],
        }
        errors = _validate_output_schema(output)
        assert not errors, f"Schema errors: {errors}"

    def test_case_pickup_required_paywall(self):
        """Site with paywall, no matching profile -> status: pickup_required."""
        output = {
            "status": "pickup_required",
            "source": "generic-fetcher",
            "reason": "Paywall detected ('Get Access'), no matching library profile.",
            "tries": ["Navigated to page", "Detected 'Get Access' banner"],
        }
        errors = _validate_output_schema(output)
        assert not errors, f"Schema errors: {errors}"

    def test_case_pickup_required_ambiguous(self):
        """Ambiguous page (no PDF link, no paywall) -> status: pickup_required (safety boundary)."""
        output = {
            "status": "pickup_required",
            "source": "generic-fetcher",
            "reason": "No clear PDF link and no paywall signal; applying safety boundary.",
            "tries": ["Navigated to page", "No PDF button found", "No paywall detected"],
        }
        errors = _validate_output_schema(output)
        assert not errors, f"Schema errors: {errors}"

    def test_all_three_cases_are_schema_valid(self):
        """All three canonical test cases must be schema-valid (meta-test)."""
        cases = [
            {
                "status": "success",
                "source": "generic-fetcher",
                "file_path": "/tmp/test.pdf",
                "tries": [],
            },
            {
                "status": "pickup_required",
                "source": "generic-fetcher",
                "tries": [],
            },
            {
                "status": "pickup_required",
                "source": "generic-fetcher",
                "tries": [],
            },
        ]
        for i, case in enumerate(cases):
            errors = _validate_output_schema(case)
            assert not errors, f"Case {i+1} schema errors: {errors}"

    def test_invalid_status_rejected(self):
        """Unknown status values must be rejected by schema validator."""
        bad_output = {
            "status": "unknown_status",
            "source": "generic-fetcher",
            "tries": [],
        }
        errors = _validate_output_schema(bad_output)
        assert any("invalid status" in e for e in errors)

    def test_missing_file_path_on_success_rejected(self):
        """status=success without file_path must be rejected."""
        bad_output = {
            "status": "success",
            "source": "generic-fetcher",
            "tries": [],
        }
        errors = _validate_output_schema(bad_output)
        assert any("file_path" in e for e in errors)


# ---------------------------------------------------------------------------
# Task 2.4 — HTML fixture content checks
# ---------------------------------------------------------------------------

class TestHTMLFixtures:
    """HTML fixtures must exist and contain expected DOM patterns."""

    def test_pdf_link_fixture_has_download_pdf(self):
        path = os.path.join(FIXTURES_DIR, "pdf_link.html")
        assert os.path.isfile(path), f"Fixture not found: {path}"
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "Download PDF" in content

    def test_paywall_fixture_has_get_access(self):
        path = os.path.join(FIXTURES_DIR, "paywall.html")
        assert os.path.isfile(path), f"Fixture not found: {path}"
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        assert "Get Access" in content or "Subscribe" in content

    def test_ambiguous_fixture_has_no_pdf_link_and_no_paywall(self):
        path = os.path.join(FIXTURES_DIR, "ambiguous.html")
        assert os.path.isfile(path), f"Fixture not found: {path}"
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        # Must NOT have PDF download indicator
        assert "Download PDF" not in content
        assert "Get PDF" not in content
        # Must NOT have paywall signal
        assert "Get Access" not in content
        assert "Subscribe" not in content
        assert "Purchase" not in content
```

- [ ] **Step 2: Tests laufen lassen (RED-Phase)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-F && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_generic_fetcher.py -v 2>&1 | head -60
```

Erwartet: FEHLER/FAIL — `agents/generic-fetcher.md` existiert noch nicht.
Wichtig: `TestHTMLFixtures` und `TestOutputSchema` sollten bereits grün sein (Fixtures + Schema-Validator unabhängig von Agent-Datei).

---

### Task 3: Agent-Datei implementieren (GREEN)

**Files:**
- Create: `agents/generic-fetcher.md`

- [ ] **Step 1: Agent-Datei schreiben**

Datei `agents/generic-fetcher.md`:

```markdown
---
name: generic-fetcher
model: sonnet
description: |
  Fallback-Subagent für die F16-Beschaffungspipeline. Bedient eine beliebige
  wissenschaftliche Site per browser-use, ohne vorgegebenen Site-Guide.
  Entscheidet anhand von DOM-Heuristiken (PDF-Button, Access-Banner, Login-Wall),
  ob ein Download möglich ist oder pickup_required gemeldet wird.
  Wird vom Master-Agent book-fetcher aufgerufen, wenn alle spezialisierten
  Subagenten fehlschlagen oder die URL keiner bekannten Site entspricht.
tools:
  - Bash(browser-use:*)
  - Bash(browser-use *)
  - Read
  - Write
maxTurns: 20
levenshtein_threshold: 30
---

# generic-fetcher — Discovery-Modus

Du bist ein Fallback-Discovery-Agent ohne Site-spezifischen Guide. Du navigierst
beliebige wissenschaftliche Seiten via browser-use und entscheidest ausschließlich
anhand von DOM-Heuristiken, ob ein PDF-Download möglich ist.

## Input-Format

Du erhältst einen JSON-Input:

```json
{
  "url": "https://example.com/article/12345",
  "title": "Advanced Topics in AI",
  "doi": "10.1000/xyz123",
  "isbn": null
}
```

`doi` und `isbn` sind optional. `title` wird für den Titelabgleich (Falscher-Treffer-
Check) verwendet.

## DOM-Heuristiken (Few-Shot-Regeln)

### 1. PDF-Link-Detection

Suche im browser-use state nach Elementen mit folgenden Texten:

**Positive Indikatoren (PDF-Download wahrscheinlich):**
- "Download PDF"
- "PDF herunterladen"
- "Get PDF"
- "Volltext (PDF)"
- "Full Text"
- "View PDF"

**Negative Indikatoren (kein echter Download):**
- "Vorschau"
- "Preview"
- "Sample Chapter"

**Element-Typen:**
- `<a href="...pdf">` oder `<a>` mit PDF-Text → href direkt als Download-URL verwenden
- `<button>` mit PDF-Text → Click auslösen, anschließende Navigation beobachten

Wenn ein positiver Indikator ohne negativen Indikator gefunden wird → Download ausführen.

### 2. Paywall-Erkennung (Volltext-Container)

Signale im browser-use state:
- "Get Access"
- "Purchase"
- "Buy"
- "Subscribe"
- "Sign in to view"
- "Anmelden für Volltext"

**Aktion bei Paywall:** Prüfe, ob ein Per-Uni-Profil für diese Site vorhanden ist
(Datei `~/.academic-research/library-profiles/active.yaml`). Wenn kein Profil oder
kein Lizenz-Treffer → `status: pickup_required` melden.

**Wichtig:** Du rufst `auth-helper` NICHT selbst auf. Auth-Dispatch ist Aufgabe
des Master-Agents `book-fetcher`. Du meldest nur `pickup_required`.

### 3. Captcha-Erkennung

Signale:
- "I'm not a robot"
- "Please verify"
- "reCAPTCHA"
- Sichtbares Captcha-Bild/Widget im DOM

**Aktion:** Screenshot speichern, sofort abbrechen mit `status: captcha`.
Du versuchst NICHT, das Captcha zu lösen.

### 4. Falscher-Treffer-Erkennung (Levenshtein)

Vergleiche den Seitentitel (aus DOM `<title>` oder `<h1>`) mit dem Input-`title`.
Berechne die Zeichenabweichung (Levenshtein-Distanz in % der Input-Länge).

- Abweichung ≤ 30 % → Treffer akzeptieren (Standard-Schwelle: `levenshtein_threshold: 30`)
- Abweichung > 30 % → Falscher Treffer → zurück zur Trefferliste, nächster Eintrag

Wenn kein weiterer Treffer vorhanden → `status: no_match`.

## Entscheidungsbaum

```
Seite geladen?
  Nein (Timeout/Error) → status: no_match

Captcha erkannt?
  Ja → Screenshot + status: captcha

PDF-Link mit positivem Indikator (ohne negativen)?
  Ja → Download ausführen → status: success + file_path

Paywall erkannt (kein Profil-Treffer)?
  Ja → status: pickup_required

Kein eindeutiger PDF-Link UND kein eindeutiges Paywall-Signal?
  → status: pickup_required  ← Safety-Boundary: bei Unsicherheit immer pickup_required
```

**Safety-Boundary:** Bei Unsicherheit — kein eindeutiger PDF-Link, kein eindeutiger
Paywall-Hinweis — melde `pickup_required`. Kein spekulativer Download-Versuch.

## Output-Format

Antworte ausschließlich mit einem JSON-Objekt:

```json
{
  "status": "success",
  "source": "generic-fetcher",
  "file_path": "/path/to/downloaded.pdf",
  "reason": "Found 'Download PDF' link, downloaded successfully.",
  "tries": [
    "Navigated to https://example.com/article/12345",
    "Found 'Download PDF' anchor element",
    "Downloaded file to /tmp/..."
  ]
}
```

**Feldbeschreibung:**
- `status`: Einer von `"success"`, `"pickup_required"`, `"captcha"`, `"no_match"`
- `source`: Immer `"generic-fetcher"`
- `file_path`: Nur bei `status: "success"` — absoluter Pfad zur heruntergeladenen PDF
- `reason`: Optional — kurze Erläuterung der Entscheidung
- `tries`: Liste der durchgeführten Schritte (für Debugging und Master-Agent-Logging)

## Beispiele

### Beispiel 1: Erfolgreicher Download

Input: `{"url": "https://journal.example.com/art/42", "title": "Deep Learning Survey"}`

browser-use state enthält:
```
<a href="/files/deep-learning-survey.pdf">Download PDF</a>
```

Output:
```json
{
  "status": "success",
  "source": "generic-fetcher",
  "file_path": "/tmp/deep-learning-survey.pdf",
  "reason": "Found 'Download PDF' link.",
  "tries": ["Loaded page", "Found Download PDF anchor", "Downloaded PDF"]
}
```

### Beispiel 2: Paywall

Input: `{"url": "https://publisher.com/book/9780123", "title": "ML Methods"}`

browser-use state enthält:
```
<div class="access-gate"><p>Get Access</p><a>Subscribe</a></div>
```

Output:
```json
{
  "status": "pickup_required",
  "source": "generic-fetcher",
  "reason": "Paywall detected ('Get Access'), no matching library profile.",
  "tries": ["Loaded page", "Detected 'Get Access' access gate"]
}
```

### Beispiel 3: Unsicherer Fall (Safety-Boundary)

Input: `{"url": "https://unknown-publisher.net/quantum-overview", "title": "Quantum Overview"}`

browser-use state: Seite geladen, mehrere Links, kein PDF-Hinweis, kein Paywall-Banner.

Output:
```json
{
  "status": "pickup_required",
  "source": "generic-fetcher",
  "reason": "No clear PDF link and no paywall signal; applying safety boundary.",
  "tries": ["Loaded page", "Scanned DOM for PDF indicators", "No match found"]
}
```

## Abgrenzung

- Du rufst `auth-helper` NICHT auf — das ist Aufgabe des Master-Agents
- Du löst Captchas NICHT
- Du verwendest KEINE direkten HTTP-Calls (curl, requests) — nur browser-use
- Du folgst KEINEM site-spezifischen Guide — das leisten dedizierte Subagenten
```

- [ ] **Step 2: Tests erneut ausführen (GREEN-Phase)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-F && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_generic_fetcher.py -v 2>&1
```

Erwartet: Alle Tests PASS. Insbesondere:
- `TestFrontmatter` — 6 Tests grün
- `TestDOMHeuristics` — 7 Tests grün
- `TestOutputSchema` — 6 Tests grün
- `TestHTMLFixtures` — 3 Tests grün

- [ ] **Step 3: Commit (nach GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-F && git add agents/generic-fetcher.md tests/test_generic_fetcher.py tests/fixtures/dom_heuristics/ && git commit -m "feat: F16.4 generic-fetcher Subagent mit DOM-Heuristiken + Tests"
```

---

### Task 4: Spec committen

**Files:**
- Commit: `specs/v6.2/F.md`, `specs/v6.2/F-plan.md`

- [ ] **Step 1: Spec-Dateien committen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-F && git add specs/v6.2/F.md specs/v6.2/F-plan.md && git commit -m "docs: Spec + Plan für Chunk F (generic-fetcher)"
```

---

### Task 5: Vollständige Test-Suite prüfen

- [ ] **Step 1: Alle Tests ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-F && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -20
```

Erwartet: Keine neuen Fehler. `test_generic_fetcher.py` — alle Tests grün.

- [ ] **Step 2: Status.yaml aktualisieren**

```bash
# L0 notifizieren: phase auf implementation_complete setzen
# (via chunks[idx=F].phase in .orchestrator/status.yaml im Haupt-Repo)
```

---

## Self-Review (Plan gegen Spec)

| Spec-Anforderung | Task |
|---|---|
| `agents/generic-fetcher.md` mit Frontmatter | Task 3 |
| DOM-Heuristik PDF-Link (Positive + Negative) | Task 3 (Agent body) + Task 2 (Tests) |
| Download-Button `<a>` vs `<button>` | Task 3 (Agent body) + Task 2 (Tests) |
| Paywall-Signale → pickup_required | Task 3 (Agent body) + Task 2 (Tests) |
| Safety-Boundary: Unsicherheit → pickup_required | Task 3 (Agent body) + Task 2 (Tests) |
| Output-Schema (OQ9 konform) | Task 2 (Schema-Validator + 3 Cases) |
| 3 Test-Cases (1 success, 2 pickup_required) | Task 2 (TestOutputSchema) |
| HTML-Fixtures | Task 1 |
| Spec + Plan | Tasks 1–4 (bereits erstellt) |
