# E4 Cookbook-Adoption (v5.2.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adopt Anthropic-Cookbook patterns across the plugin (native Citations API, pytest-based evals suite, pushy descriptions + trigger evals, quality-reviewer agent, domain-organized references, prompt caching) and release as v5.2.0.

**Architecture:** Plan is phased in 7 stages: (1) Evals-Infrastruktur zuerst, damit alles Folgende testbar ist. (2) Citations-API-Migration. (3) Pushy Descriptions + Trigger-Evals. (4) Quality-Reviewer-Agent. (5) Domain-References. (6) Prompt-Caching. (7) Release. Jede Phase endet mit thematischem Commit; am Schluss squash-merge als `v5.2.0`.

**Tech Stack:** Python 3.11+, pytest (existing `tests/`), Anthropic Python SDK (`anthropic>=0.40` für Citations + Caching), Markdown-Skill-Files, YAML-Frontmatter. Keine neuen Dependencies außer `anthropic` in `scripts/requirements.txt`.

**Spec:** [`docs/superpowers/specs/2026-04-23-academic-research-e4-cookbook-design.md`](../specs/2026-04-23-academic-research-e4-cookbook-design.md)

---

## Datei-Struktur (neu und geändert)

**Neue Verzeichnisse:**
- `tests/evals/` — pytest-Suites für Skills/Agents
- `evals/<component>/` — JSON-Datenbank pro Skill/Agent (`evals.json`, `trigger_evals.json`)
- `docs/evals/` — Markdown-Reports der zuletzt gelaufenen Evals

**Neue Dateien:**
- `agents/quality-reviewer.md` — Evaluator-Optimizer-Agent
- `tests/evals/__init__.py`
- `tests/evals/conftest.py` — Fixtures: `claude_client`, `skill_loader`, `mode_param`
- `tests/evals/eval_runner.py` — Shared helper (load JSON, call API, check expectation)
- `tests/evals/test_quote_extractor_evals.py`
- `tests/evals/test_citation_extraction_evals.py`
- `tests/evals/test_abstract_generator_evals.py`
- `tests/evals/test_source_quality_audit_evals.py`
- `tests/evals/test_chapter_writer_evals.py`
- `tests/evals/test_rest_evals.py` — parametrized über die 8 restlichen Skills + 2 restlichen Agents
- `tests/evals/test_triggers.py` — Trigger-Eval-Runner parametrized über alle 13 Skills
- `evals/<component>/evals.json` — pro Skill/Agent (16 Dateien)
- `evals/<component>/trigger_evals.json` — pro Skill (13 Dateien)
- `skills/citation-extraction/references/{apa,harvard,chicago,din1505}.md` (4)
- `skills/style-evaluator/references/{academic-de,academic-en}.md` (2)
- `skills/submission-checker/references/{fh-leibniz,uni-general,journal-ieee,journal-acm}.md` (4)
- `docs/evals/2026-04-23-<component>.md` — pro Skill/Agent (16 Reports)

**Geänderte Dateien:**
- `agents/quote-extractor.md` — Pre-Execution-Guard raus, Citations-API + Cache-Breakpoint rein
- `agents/relevance-scorer.md` — Cache-Breakpoint rein
- `skills/citation-extraction/SKILL.md` — Citations-API-Workflow, Variant-Selector
- `skills/chapter-writer/SKILL.md` — Citations-API-Einbindung, Quality-Reviewer-Aufruf
- `skills/abstract-generator/SKILL.md` — Quality-Reviewer-Aufruf
- `skills/advisor/SKILL.md` — Quality-Reviewer-Aufruf
- `skills/style-evaluator/SKILL.md` — Variant-Selector
- `skills/submission-checker/SKILL.md` — Variant-Selector, Inline-Formalia nach `fh-leibniz.md`
- Alle 13 `skills/*/SKILL.md` — Pushy Description (imperativer Einstieg + 3–4 Trigger-Beispiele)
- `scripts/requirements.txt` — `anthropic>=0.40` ergänzen
- `tests/test_skills_manifest.py` — ggf. Variant-Selector-Check ergänzen
- `.claude-plugin/plugin.json` — Version 5.1.1 → 5.2.0
- `.claude-plugin/marketplace.json` — Version 5.1.1 → 5.2.0
- `CHANGELOG.md` — Block `[5.2.0]` ergänzen
- `README.md` — Abschnitt "Evals" ergänzen

---

## Phase 1 — Evals-Infrastruktur (Block B, Grundgerüst)

### Task 1: Evals-Verzeichnisstruktur und Schema-Dokumentation

**Files:**
- Create: `evals/.gitkeep`
- Create: `evals/SCHEMA.md`
- Create: `tests/evals/__init__.py`
- Create: `tests/evals/conftest.py`
- Create: `tests/evals/eval_runner.py`

- [ ] **Step 1: Verzeichnisse anlegen**

```bash
mkdir -p evals tests/evals docs/evals
touch evals/.gitkeep tests/evals/__init__.py
```

- [ ] **Step 2: Schema-Dokumentation schreiben**

Datei `evals/SCHEMA.md`:

````markdown
# Evals-Schema

## `evals/<component>/evals.json`

Quality-Evals pro Skill oder Agent, nach Cookbook-Pattern `skill-creator`.

```json
{
  "component": "quote-extractor",
  "component_type": "agent",
  "prompts": [
    {
      "id": "qe-01",
      "input": "Extrahiere aus <pdf_path> zwei Zitate zum Thema 'DevOps Governance'.",
      "expected": {
        "type": "json_field",
        "path": "$.quotes[0].text",
        "check": "non_empty"
      },
      "mode": "both"
    }
  ]
}
```

**Felder:**
- `component`: Name des Skills/Agents (entspricht Verzeichnisname unter `evals/`)
- `component_type`: `"skill"` oder `"agent"`
- `prompts[].id`: Stabile ID (`<component-prefix>-NN`)
- `prompts[].input`: User-Prompt, der Claude geschickt wird
- `prompts[].expected.type`: `"substring"` | `"regex"` | `"json_field"`
- `prompts[].expected.value`: erwarteter Substring oder Regex (bei Typ `substring`/`regex`)
- `prompts[].expected.path`: JSONPath zum geprüften Feld (bei Typ `json_field`)
- `prompts[].expected.check`: `"exists"` | `"non_empty"` | `"equals:<wert>"` (bei Typ `json_field`)
- `prompts[].mode`: `"with_skill"` | `"without_skill"` | `"both"`

## `evals/<component>/trigger_evals.json`

Trigger-Evals pro Skill (Block C).

```json
{
  "component": "research-question-refiner",
  "should_trigger": [
    "Kannst du meine Forschungsfrage schärfen?",
    "Meine Fragestellung ist zu breit, hilf mir bitte."
  ],
  "should_not_trigger": [
    "Wie richte ich meinen akademischen Kontext ein?",
    "Welche Methodik passt zu meiner Fallstudie?"
  ]
}
```

**Schwellen:**
- Quality-Evals: Baseline-Gap `PASS_rate(with_skill) - PASS_rate(without_skill) >= 20` Prozentpunkte
- Trigger-Evals: `recall_should_trigger >= 0.85`, `false_positive_should_not_trigger <= 0.10`
````

- [ ] **Step 3: Shared Eval-Runner schreiben**

Datei `tests/evals/eval_runner.py`:

```python
"""Shared helpers fuer Evals-Suites.

Laedt Eval-JSON-Dateien, ruft die Claude-API auf und prueft Expectations.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

EVALS_ROOT = Path(__file__).parent.parent.parent / "evals"
SKILLS_ROOT = Path(__file__).parent.parent.parent / "skills"
AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


def load_eval_file(component: str, filename: str) -> dict[str, Any]:
    path = EVALS_ROOT / component / filename
    if not path.exists():
        pytest.skip(f"Eval-Datei fehlt: {path}")
    return json.loads(path.read_text())


def load_skill_content(skill: str) -> str:
    return (SKILLS_ROOT / skill / "SKILL.md").read_text()


def load_agent_content(agent: str) -> str:
    return (AGENTS_ROOT / f"{agent}.md").read_text()


def require_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY nicht gesetzt — Eval uebersprungen")
    return key


def call_claude(system: str, user: str, model: str = "claude-sonnet-4-6") -> str:
    if anthropic is None:
        pytest.skip("anthropic-Package nicht installiert")
    key = require_api_key()
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        block.text for block in resp.content if hasattr(block, "text")
    )


def check_expected(output: str, expected: dict[str, Any]) -> bool:
    t = expected.get("type")
    if t == "substring":
        return expected["value"] in output
    if t == "regex":
        return bool(re.search(expected["value"], output))
    if t == "json_field":
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            return False
        return _jsonpath_check(parsed, expected)
    raise ValueError(f"Unbekannter expected.type: {t}")


def _jsonpath_check(obj: Any, expected: dict[str, Any]) -> bool:
    path = expected.get("path", "$")
    check = expected.get("check", "exists")
    # Minimaler JSONPath: $.a.b[0].c — kein Full-Feature JSONPath noetig
    current: Any = obj
    for seg in re.findall(r"\.(\w+)|\[(\d+)\]", path):
        key, idx = seg
        if key:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        elif idx:
            if not isinstance(current, list) or int(idx) >= len(current):
                return False
            current = current[int(idx)]
    if check == "exists":
        return current is not None
    if check == "non_empty":
        return bool(current)
    if check.startswith("equals:"):
        return str(current) == check.split(":", 1)[1]
    raise ValueError(f"Unbekannter check: {check}")
```

- [ ] **Step 4: conftest-Fixtures schreiben**

Datei `tests/evals/conftest.py`:

```python
"""Shared Fixtures fuer Evals-Suites."""
from __future__ import annotations

import pytest

from tests.evals.eval_runner import (
    load_agent_content,
    load_eval_file,
    load_skill_content,
)


@pytest.fixture
def skill_loader():
    return load_skill_content


@pytest.fixture
def agent_loader():
    return load_agent_content


@pytest.fixture
def eval_loader():
    return load_eval_file
```

- [ ] **Step 5: Smoke-Test fuer den Runner**

Datei `tests/evals/test_runner_smoke.py`:

```python
"""Smoke-Test fuer eval_runner.check_expected."""
from tests.evals.eval_runner import check_expected


def test_substring_match():
    assert check_expected("hello world", {"type": "substring", "value": "world"})


def test_substring_miss():
    assert not check_expected("hello", {"type": "substring", "value": "xyz"})


def test_regex_match():
    assert check_expected("abc123", {"type": "regex", "value": r"\d+"})


def test_json_field_exists():
    assert check_expected(
        '{"a": {"b": "x"}}',
        {"type": "json_field", "path": ".a.b", "check": "exists"},
    )


def test_json_field_non_empty_empty():
    assert not check_expected(
        '{"a": ""}',
        {"type": "json_field", "path": ".a", "check": "non_empty"},
    )
```

- [ ] **Step 6: Smoke-Test laufen lassen**

Run: `pytest tests/evals/test_runner_smoke.py -v`
Expected: PASS 5/5

- [ ] **Step 7: Commit**

```bash
git add evals/ tests/evals/ docs/evals/
git commit -m "$(cat <<'EOF'
feat(evals): evals infrastructure skeleton (schema, runner, fixtures)

- evals/SCHEMA.md documents JSON schema for quality and trigger evals
- tests/evals/eval_runner.py provides load/call/check helpers
- tests/evals/conftest.py exposes fixtures
- tests/evals/test_runner_smoke.py validates check_expected logic

No API calls yet; Phase 2 onwards uses the runner.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Anthropic SDK als Abhängigkeit

**Files:**
- Modify: `scripts/requirements.txt`
- Test: Verify venv install

- [ ] **Step 1: Dependency ergaenzen**

`scripts/requirements.txt` lesen, dann `anthropic>=0.40` anhaengen (falls noch nicht vorhanden).

- [ ] **Step 2: Venv neu bauen (lokal, informativ)**

Run: `rm -rf ~/.academic-research/venv && scripts/setup.sh`
Expected: venv created, `anthropic` installiert. Bei Fehler: Root-Cause fixen, nicht skip.

- [ ] **Step 3: Import-Smoke-Test**

Run: `python -c "import anthropic; print(anthropic.__version__)"`
Expected: Version `>=0.40` ausgegeben.

- [ ] **Step 4: Commit**

```bash
git add scripts/requirements.txt
git commit -m "chore(deps): anthropic>=0.40 for citations api and prompt caching"
```

---

### Task 3: Docs-Evals-Report-Template

**Files:**
- Create: `docs/evals/TEMPLATE.md`
- Create: `docs/evals/README.md`

- [ ] **Step 1: Report-Template schreiben**

Datei `docs/evals/TEMPLATE.md`:

````markdown
# Eval-Report — `<component>`

**Datum:** YYYY-MM-DD
**Komponente:** `<component>` (`skill` | `agent`)
**Modell:** `claude-sonnet-4-6` (oder vom Runner abgefragt)
**Anzahl Prompts:** N (M with_skill + K without_skill)

## Quality-Ergebnisse

| ID | Input (gekuerzt) | Mode | Expected | Actual | PASS |
|----|------------------|------|----------|--------|------|
| qe-01 | ... | both | `$.quotes[0].text` non_empty | `"..."` | ✅ / ❌ |

### Baseline-Gap

- PASS-Rate `with_skill`: X %
- PASS-Rate `without_skill`: Y %
- **Delta:** `X - Y` pp (Schwelle: ≥ 20 pp)

## Trigger-Ergebnisse (falls Skill)

| Prompt (gekuerzt) | Soll | Ist | PASS |
|-------------------|------|-----|------|
| "Forschungsfrage schaerfen" | trigger | trigger | ✅ |

- Recall `should_trigger`: X/10 = Y % (Schwelle: ≥ 85 %)
- False-Positive `should_not_trigger`: A/10 = B % (Schwelle: ≤ 10 %)

## Notizen

- Beobachtungen zu spezifischen Prompt-Failures
- Empfehlungen fuer Skill-Anpassung
````

- [ ] **Step 2: README fuer docs/evals schreiben**

Datei `docs/evals/README.md`:

```markdown
# Evals-Reports

Dieses Verzeichnis enthaelt die Eval-Reports der Release-Kandidaten.

## Konvention

- `2026-04-23-<component>.md` — Report fuer eine einzelne Komponente, generiert vor Release v5.2.0
- `TEMPLATE.md` — Leeres Report-Template

## Ausfuehrung

```
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/evals/ -v
```

Reports entstehen manuell auf Basis der pytest-Ausgabe. Kein automatischer Report-Generator (YAGNI — Reports werden nur ein paar Mal pro Release geschrieben).
```

- [ ] **Step 3: Commit**

```bash
git add docs/evals/
git commit -m "docs(evals): add report template and readme"
```

---

## Phase 2 — Citations-API (Block A)

### Task 4: Citations-API in `quote-extractor` einbauen

**Files:**
- Modify: `agents/quote-extractor.md`
- Create: `evals/quote-extractor/evals.json`
- Create: `tests/evals/test_quote_extractor_evals.py`

- [ ] **Step 1: Failing-Test fuer quote-extractor-Eval schreiben**

Datei `tests/evals/test_quote_extractor_evals.py`:

```python
"""Evals fuer quote-extractor-Agent (Block B + A)."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_agent_content,
    load_eval_file,
)

EVALS = load_eval_file("quote-extractor", "evals.json") if (
    __import__("pathlib").Path(__file__).parent.parent.parent
    / "evals" / "quote-extractor" / "evals.json"
).exists() else {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_quote_extractor_eval(prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip(f"Prompt {prompt['id']} nicht fuer Mode {mode}")
    system = load_agent_content("quote-extractor") if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

- [ ] **Step 2: Test ausfuehren — FAIL (keine evals.json)**

Run: `pytest tests/evals/test_quote_extractor_evals.py -v`
Expected: Tests werden skipped (keine evals.json). Runner bestaetigt, dass die Skip-Logik greift.

- [ ] **Step 3: evals.json mit 5 Beispielprompts erstellen**

Datei `evals/quote-extractor/evals.json`:

```json
{
  "component": "quote-extractor",
  "component_type": "agent",
  "prompts": [
    {
      "id": "qe-01",
      "input": "Paper-Title: 'DevOps Governance Frameworks'. PDF-Text: 'Governance frameworks ensure DevOps compliance across distributed teams. This requires clear policy definition and shared accountability...' Extrahiere 2 verbatime Zitate, max 25 Woerter.",
      "expected": {"type": "regex", "value": "\"quotes\"\\s*:\\s*\\["},
      "mode": "both"
    },
    {
      "id": "qe-02",
      "input": "Paper-Title: 'Zero Trust Networks'. PDF-Text: 'Zero trust assumes no implicit trust. Every access request is verified regardless of origin.' Extrahiere 2 Zitate zur Query 'Zero Trust Prinzipien', max 25 Woerter pro Zitat.",
      "expected": {"type": "substring", "value": "Zero trust"},
      "mode": "with_skill"
    },
    {
      "id": "qe-03",
      "input": "Paper-Title: 'Machine Learning Ops'. PDF-Text: '[FEHLER] scanned image'. Extrahiere Zitate zur Query 'MLOps'.",
      "expected": {"type": "regex", "value": "extraction_quality.*failed|Extraktions-Fehler"},
      "mode": "with_skill"
    },
    {
      "id": "qe-04",
      "input": "Paper-Title: 'Agile at Scale'. PDF-Text: 'Scaled agile frameworks coordinate multiple teams through quarterly planning increments.' Query: 'SAFe Coordination'. Extrahiere 1 Zitat.",
      "expected": {"type": "substring", "value": "quarterly"},
      "mode": "both"
    },
    {
      "id": "qe-05",
      "input": "Paper-Title: 'Quantum Computing'. PDF-Text: 'Lorem ipsum dolor sit amet.' Query: 'Post-Quantum Cryptography'. Keine relevanten Zitate erwartet.",
      "expected": {"type": "regex", "value": "\"quotes\"\\s*:\\s*\\[\\s*\\]|total_quotes_extracted.*0"},
      "mode": "with_skill"
    }
  ]
}
```

- [ ] **Step 4: Mit API-Key laufen lassen (lokal)**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_quote_extractor_evals.py -v`
Expected: Alle 5 Prompts im `with_skill`-Mode PASS. `without_skill`-Mode zeigt mindestens 2 FAIL (Delta ≥ 20 pp demonstrierbar).

- [ ] **Step 5: quote-extractor.md auf Citations-API umstellen**

In `agents/quote-extractor.md` den Abschnitt `## Vorpruefung` (Zeilen ~45–58) ersetzen durch:

```markdown
## Quellen-Bindung via Citations-API

**Statt Heuristik-Guard:** Der Agent erhaelt PDFs ueber den `documents`-Parameter der Claude-API. Die API erzwingt, dass jede Antwort `citations[]` enthaelt, die auf `page_location` (PDF) oder `char_location` (Text) zeigen.

**API-Call-Schema (Input):**
```json
{
  "model": "claude-sonnet-4-6",
  "system": "[Dieser Agent-Prompt]",
  "documents": [
    {
      "type": "document",
      "source": {"type": "base64", "media_type": "application/pdf", "data": "<base64>"},
      "title": "DevOps Governance Frameworks",
      "citations": {"enabled": true}
    }
  ],
  "messages": [{"role": "user", "content": "Extrahiere 2 Zitate zur Query '<query>', max 25 Woerter pro Zitat."}]
}
```

**Output mit Citations:** Jeder `content`-Block mit `text` enthaelt ein `citations[]`-Array mit Objekten wie:
```json
{"type": "page_location", "cited_text": "Governance frameworks ensure DevOps compliance", "document_index": 0, "document_title": "...", "start_page_number": 3, "end_page_number": 3}
```

**Fallback:** Ist die Quelle kein PDF (HTML, Markdown), `source.type: "text"` mit `char_location`.

**Qualitaetsfilter (Prompt-seitig, nicht API):**
- Zitat-Laenge ≤ 25 Woerter (Agent zaehlt im Output-Block)
- Verbatim-Match gegen `cited_text` (API garantiert das bereits)
- Pro Paper max 3 Zitate
```

Und den Abschnitt `## Output-Format` erweitern um den `citations`-Unterblock:

```markdown
Jedes Zitat-Objekt enthaelt zusaetzlich das `citations[]`-Array aus der API-Antwort. Das ermoeglicht dem nachgelagerten `citation-extraction`-Skill, die zitierte Stelle seitengenau nachzuschlagen.
```

Pre-Execution-Guard-Text (Wortzahl ≥ 500, Fehler-Marker, Mindest-Seitenzahl) entfernen — API uebernimmt die Quellen-Bindung.

- [ ] **Step 6: Test erneut laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_quote_extractor_evals.py::test_quote_extractor_eval -v`
Expected: PASS Rate `with_skill` ≥ 4/5, Delta ≥ 20 pp.

- [ ] **Step 7: Commit**

```bash
git add agents/quote-extractor.md evals/quote-extractor/ tests/evals/test_quote_extractor_evals.py
git commit -m "$(cat <<'EOF'
feat(agents): adopt native Citations API in quote-extractor

- Replaces Pre-Execution-Guard (word count, error marker, page count) with
  Anthropic Citations API. API enforces source binding on the wire level.
- Uses page_location for PDFs, char_location fallback for text sources.
- Adds evals/quote-extractor/evals.json with 5 baseline prompts.
- Adds tests/evals/test_quote_extractor_evals.py with with_skill vs
  without_skill parametrization.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Citations-API in `citation-extraction` einbauen

**Files:**
- Modify: `skills/citation-extraction/SKILL.md`
- Create: `evals/citation-extraction/evals.json`
- Create: `tests/evals/test_citation_extraction_evals.py`

- [ ] **Step 1: Failing-Test schreiben**

Datei `tests/evals/test_citation_extraction_evals.py`:

```python
"""Evals fuer citation-extraction-Skill."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_eval_file,
    load_skill_content,
)

try:
    EVALS = load_eval_file("citation-extraction", "evals.json")
except Exception:
    EVALS = {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_citation_extraction_eval(prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip(f"{prompt['id']}: Mode {mode} nicht vorgesehen")
    system = load_skill_content("citation-extraction") if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

- [ ] **Step 2: evals.json mit 5 Beispielprompts erstellen**

Datei `evals/citation-extraction/evals.json`:

```json
{
  "component": "citation-extraction",
  "component_type": "skill",
  "prompts": [
    {
      "id": "ce-01",
      "input": "Autor: Smith, J. Jahr: 2023. Titel: 'DevOps Governance'. Journal: 'IEEE Software'. Band 40, Heft 3, Seiten 42-50. Erzeuge einen APA7-Eintrag.",
      "expected": {"type": "substring", "value": "Smith, J. (2023)"},
      "mode": "both"
    },
    {
      "id": "ce-02",
      "input": "DOI: 10.1109/MS.2022.1234567. Autor: Müller, A. und Meier, B. Jahr: 2022. Titel: 'Agile Entscheidungsfindung'. Erzeuge einen Harvard-Eintrag.",
      "expected": {"type": "regex", "value": "Müller.*2022|Müller, A\\."},
      "mode": "both"
    },
    {
      "id": "ce-03",
      "input": "Autor: Tanaka, Y. Jahr: 2024. Buch: 'Machine Learning Ops'. Verlag: Springer. Erzeuge einen Chicago-Eintrag (Author-Date).",
      "expected": {"type": "substring", "value": "Tanaka"},
      "mode": "with_skill"
    },
    {
      "id": "ce-04",
      "input": "Zitat 'Governance frameworks ensure DevOps compliance' aus Seite 42 des Papers von Smith (2023, IEEE Software). APA7-Inline-Zitat mit Seitenangabe.",
      "expected": {"type": "regex", "value": "\\(Smith, 2023, S\\. 42\\)|\\(Smith, 2023, p\\. 42\\)"},
      "mode": "with_skill"
    },
    {
      "id": "ce-05",
      "input": "Mehrere Autoren: Smith, Jones, Taylor, Brown, Davis (2023). APA7-Erstzitat im Text.",
      "expected": {"type": "regex", "value": "Smith et al\\., 2023|Smith, Jones, Taylor, Brown, & Davis"},
      "mode": "with_skill"
    }
  ]
}
```

- [ ] **Step 3: citation-extraction/SKILL.md Citations-API-Abschnitt ergaenzen**

In `skills/citation-extraction/SKILL.md` einen neuen Abschnitt `## Citations-API` direkt nach `## Aktivierung dieses Skills` einfuegen:

```markdown
## Citations-API

Wenn Quellen-PDFs im Session-Kontext liegen, nutze den `documents`-Parameter der Claude-API statt Prompt-basierter Zitation. Vorteil: Zitate sind seitengenau, die API erzwingt die Quellenbindung.

**Wann verwenden:**
- Mindestens 1 PDF im Session-Pfad
- Zitierstil-Konversion aus echtem Quelltext (nicht aus Metadaten)

**Wann nicht:**
- Reiner Metadaten-zu-Zitat-Workflow (User gibt Autor/Jahr/Titel) → weiter mit Prompt-basierter Formatierung nach Variant-References.

**Output-Integration:** Die `citations[]`-Array-Eintraege der API enthalten `start_page_number` / `end_page_number` direkt — uebernimm sie in die Seitenangabe des Zitats (`S. X–Y`).
```

- [ ] **Step 4: Tests laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_citation_extraction_evals.py -v`
Expected: `with_skill`-PASS ≥ 4/5, Delta ≥ 20 pp.

- [ ] **Step 5: Commit**

```bash
git add skills/citation-extraction/SKILL.md evals/citation-extraction/ tests/evals/test_citation_extraction_evals.py
git commit -m "feat(skills): citation-extraction uses Citations API when PDFs present"
```

---

### Task 6: Citations-API in `chapter-writer` einbauen

**Files:**
- Modify: `skills/chapter-writer/SKILL.md`
- Create: `evals/chapter-writer/evals.json`
- Create: `tests/evals/test_chapter_writer_evals.py`

- [ ] **Step 1: evals.json erstellen**

Datei `evals/chapter-writer/evals.json`:

```json
{
  "component": "chapter-writer",
  "component_type": "skill",
  "prompts": [
    {
      "id": "cw-01",
      "input": "Schreibe die Einleitung des Kapitels 'Grundlagen DevOps' (ca. 200 Woerter). Quellenliste: Smith (2023), Tanaka (2024). Inline-Zitate nach APA7.",
      "expected": {"type": "regex", "value": "Smith.*2023|\\(Smith, 2023\\)"},
      "mode": "both"
    },
    {
      "id": "cw-02",
      "input": "Schreibe einen 150-Woerter-Uebergang zwischen dem Kapitel 'Theorie' und 'Empirische Befunde'. Keine neuen Quellen.",
      "expected": {"type": "regex", "value": "(Theorie|vorangegangen|empirisch)"},
      "mode": "with_skill"
    },
    {
      "id": "cw-03",
      "input": "Schreibe eine Zusammenfassung eines Methodik-Kapitels ueber 'Qualitative Inhaltsanalyse nach Mayring'. 100 Woerter. Zitat: Mayring (2022).",
      "expected": {"type": "substring", "value": "Mayring"},
      "mode": "both"
    },
    {
      "id": "cw-04",
      "input": "Schreibe einen Diskussionsabsatz, der das Ergebnis 'DevOps Governance reduziert Incidents um 30%' kritisch einordnet. Quellen: Smith (2023), Mueller (2021).",
      "expected": {"type": "regex", "value": "(Smith|Mueller)"},
      "mode": "with_skill"
    },
    {
      "id": "cw-05",
      "input": "Schreibe 80 Woerter zu einem konstruktivistischen Wissenschaftsverstaendnis.",
      "expected": {"type": "substring", "value": "konstruktivistisch"},
      "mode": "with_skill"
    }
  ]
}
```

- [ ] **Step 2: Test-Datei erstellen**

Datei `tests/evals/test_chapter_writer_evals.py`:

```python
"""Evals fuer chapter-writer-Skill."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_eval_file,
    load_skill_content,
)

try:
    EVALS = load_eval_file("chapter-writer", "evals.json")
except Exception:
    EVALS = {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_chapter_writer_eval(prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip(f"{prompt['id']}: Mode {mode} nicht vorgesehen")
    system = load_skill_content("chapter-writer") if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

- [ ] **Step 3: chapter-writer/SKILL.md Citations-API-Abschnitt ergaenzen**

Neuer Abschnitt `## Zitat-Einbindung via Citations-API` vor dem letzten `## Wichtige Regeln`-Abschnitt einfuegen:

```markdown
## Zitat-Einbindung via Citations-API

Beim Einweben von Zitaten in Kapitel-Prosa: Quellen-PDFs im `documents`-Parameter an Claude uebergeben, damit die API die Quellenbindung erzwingt. Jedes Paraphrase-Segment mit einem `citations[]`-Eintrag nachweisbar.

**Workflow:**
1. `literature_state.md` lesen — welche PDFs liegen im Session-Pfad?
2. API-Call mit `documents[]`-Anhaengen, `citations.enabled: true`
3. Output-Text enthaelt `citations[]`-Bloecke — diese im Kapitel-Text als Inline-Zitate nach Variant-Zitierstil (aus `academic_context.md`) rendern.

**Fallback:** Sind keine PDFs verfuegbar (nur Metadaten), nutze den herkoemmlichen Prompt-Workflow aus dem vorangehenden Abschnitt.
```

- [ ] **Step 4: Tests laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_chapter_writer_evals.py -v`
Expected: `with_skill`-PASS ≥ 4/5, Delta ≥ 20 pp.

- [ ] **Step 5: Commit**

```bash
git add skills/chapter-writer/SKILL.md evals/chapter-writer/ tests/evals/test_chapter_writer_evals.py
git commit -m "feat(skills): chapter-writer uses Citations API for source binding"
```

---

## Phase 3 — Pushy Descriptions + Trigger-Evals (Block C)

### Task 7: Trigger-Eval-Runner schreiben

**Files:**
- Create: `tests/evals/test_triggers.py`

- [ ] **Step 1: Test-Datei erstellen**

Datei `tests/evals/test_triggers.py`:

```python
"""Trigger-Evals: prueft, ob Skill-Descriptions Undertriggering/Overtriggering aufweisen."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import pytest

from tests.evals.eval_runner import call_claude

EVALS_ROOT = Path(__file__).parent.parent.parent / "evals"
SKILLS_ROOT = Path(__file__).parent.parent.parent / "skills"
ALL_SKILLS = sorted(p.parent.name for p in SKILLS_ROOT.glob("*/SKILL.md"))


def _load_all_descriptions() -> str:
    parts: list[str] = []
    for skill in ALL_SKILLS:
        content = (SKILLS_ROOT / skill / "SKILL.md").read_text()
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        name_m = re.search(r"^name:\s*(.+)$", fm, re.M)
        desc_m = re.search(r"^description:\s*\|?\s*(.+?)(?=^[a-z_]+:|\Z)", fm, re.M | re.S)
        if name_m and desc_m:
            parts.append(f"- **{name_m.group(1).strip()}**: {desc_m.group(1).strip()[:500]}")
    return "\n".join(parts)


def _load_trigger_evals(skill: str) -> dict | None:
    path = EVALS_ROOT / skill / "trigger_evals.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


TRIGGER_SYSTEM_TEMPLATE = (
    "Du bist ein Skill-Dispatcher. Gegeben eine Liste verfuegbarer Skills und "
    "einen User-Prompt, antworte ausschliesslich mit dem Skill-Namen, der "
    "aktiviert werden sollte, oder 'none' falls keiner passt.\n\n"
    "Verfuegbare Skills:\n{descriptions}\n\n"
    "Antworte nur mit dem Skill-Namen oder 'none'. Keine Erklaerung."
)


def _classify(user_prompt: str) -> str:
    system = TRIGGER_SYSTEM_TEMPLATE.format(descriptions=_load_all_descriptions())
    output = call_claude(system=system, user=user_prompt, model="claude-haiku-4-5-20251001")
    return output.strip().lower().split()[0] if output.strip() else "none"


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_should_trigger_recall(skill: str):
    evals = _load_trigger_evals(skill)
    if not evals or not evals.get("should_trigger"):
        pytest.skip(f"Keine trigger_evals.json fuer {skill}")
    hits = sum(_classify(p) == skill for p in evals["should_trigger"])
    total = len(evals["should_trigger"])
    recall = hits / total
    assert recall >= 0.85, f"{skill}: recall={recall:.0%} ({hits}/{total}), Schwelle 85%"


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_should_not_trigger_fpr(skill: str):
    evals = _load_trigger_evals(skill)
    if not evals or not evals.get("should_not_trigger"):
        pytest.skip(f"Keine trigger_evals.json fuer {skill}")
    false_pos = sum(_classify(p) == skill for p in evals["should_not_trigger"])
    total = len(evals["should_not_trigger"])
    fpr = false_pos / total
    assert fpr <= 0.10, f"{skill}: fpr={fpr:.0%} ({false_pos}/{total}), Schwelle 10%"
```

- [ ] **Step 2: Runner-Smoke ohne trigger_evals.json ausfuehren**

Run: `pytest tests/evals/test_triggers.py -v`
Expected: 26 Tests (13 Skills × 2), alle mit skip (keine trigger_evals.json vorhanden).

- [ ] **Step 3: Commit**

```bash
git add tests/evals/test_triggers.py
git commit -m "feat(evals): trigger-eval runner (recall>=85%, fpr<=10%)"
```

---

### Task 8: Pushy Descriptions für alle 13 Skills + Trigger-Evals

**Files:**
- Modify: `skills/*/SKILL.md` (alle 13)
- Create: `evals/<skill>/trigger_evals.json` (13 Dateien)

Dieser Task ist gebatcht, weil das Pattern fuer alle 13 Skills identisch ist und Batching eine konsistente Durchsicht erlaubt.

**Pushy-Pattern (einheitlich):**

Jede `description:` im Frontmatter wird umformuliert nach dem Schema:

```
Use this skill when the user <Trigger-Situation>. Triggers on "<trigger-term-1>", "<trigger-term-2>", "<trigger-term-3 / umlaut-variant>", "<trigger-term-4>", or when <Nachbar-Skill-Context>. <Abgrenzungs-Satz aus E3/E3-Followup>.
```

**Trigger-Evals-Pattern:**

Pro Skill eine JSON-Datei mit genau 10 `should_trigger` und 10 `should_not_trigger` Prompts.

- [ ] **Step 1: research-question-refiner aktualisieren**

Description-Ersatz im Frontmatter von `skills/research-question-refiner/SKILL.md`:

```yaml
description: Use this skill when the user wants to refine, sharpen or evaluate their research question. Triggers on "Forschungsfrage formulieren", "Research Question", "Fragestellung / Fragestellung präzisieren", "Forschungsfrage schärfen / Forschungsfrage schaerfen", "research question refine", "Fragestellung präzisieren / Fragestellung praezisieren", or when another skill detects a question that is too broad, too narrow, or unanswerable. Fokus auf Verfeinerung bestehender Fragen; Erstanlage von Forschungsfrage, Thema oder Methodik übernimmt `academic-context`.
```

Datei `evals/research-question-refiner/trigger_evals.json`:

```json
{
  "component": "research-question-refiner",
  "should_trigger": [
    "Kannst du meine Forschungsfrage schärfen?",
    "Meine Fragestellung ist zu breit, hilf mir beim Präzisieren",
    "Ist meine Research Question gut genug?",
    "Bitte bewerte meine Hauptfrage",
    "Ich brauche Unterfragen zu meiner Forschungsfrage",
    "Wie formuliere ich eine nicht-falsifizierbare Frage um?",
    "Meine Betreuerin meint, meine Frage sei mehrdimensional",
    "Fragestellung praezisieren fuer Master-Thesis",
    "Forschungsfrage schaerfen, bitte",
    "Welche Frage passt zu meinem Literatur-Review?"
  ],
  "should_not_trigger": [
    "Welche Methodik passt zu meinem Thema?",
    "Wie richte ich meinen academic_context ein?",
    "Schreib mir ein Kapitel zu Theorie X",
    "Pruefe die Formatierung meiner Abgabe",
    "Suche mir Literatur zu Zero Trust",
    "Erzeuge ein Abstract fuer meine Arbeit",
    "Welche Autoren sollte ich lesen?",
    "Pruefe meine Quellenabdeckung",
    "Wie lautet die Gliederung?",
    "Welcher Titel passt zu meiner Arbeit?"
  ]
}
```

- [ ] **Step 2: academic-context aktualisieren**

Description-Ersatz im Frontmatter:

```yaml
description: Use this skill whenever the user starts or updates a thesis, Bachelorarbeit, Masterarbeit, Hausarbeit, Facharbeit or academic paper. Triggers on "meine Arbeit", "mein Thema", "Forschungsfrage", "Gliederung", "thesis context", "academic profile", "akademischer Kontext prüfen / akademischer Kontext pruefen", or when another skill needs context that does not yet exist. Fokus auf Erstanlage und Verwaltung des Kontexts; Schärfung einer bestehenden Forschungsfrage übernimmt `research-question-refiner`.
```

Datei `evals/academic-context/trigger_evals.json`:

```json
{
  "component": "academic-context",
  "should_trigger": [
    "Ich fange gerade mit meiner Bachelorarbeit an",
    "Lass uns mein Thema festhalten",
    "Akademischen Kontext pruefen, bitte",
    "Ich habe ein neues Thema gewaehlt",
    "Setze meinen thesis context auf",
    "Ich bin an der FH Leibniz, BWL, Bachelor",
    "Lass uns meine Gliederung aufsetzen",
    "Mein Abgabetermin ist in 3 Monaten",
    "Update mein academic profile",
    "Ich schreibe eine Hausarbeit zu Agile"
  ],
  "should_not_trigger": [
    "Kannst du meine Forschungsfrage schärfen?",
    "Suche mir 20 Paper zu Zero Trust",
    "Schreib mir das Methodikkapitel",
    "Pruefe meine Zitationen",
    "Finde Luecken in meiner Literatur",
    "Gib mir einen Titel-Vorschlag",
    "Erzeuge Abstract + Keywords",
    "Bewerte meinen Schreibstil",
    "Pruefe auf Plagiate",
    "Welche Methode passt zu meiner Fallstudie?"
  ]
}
```

- [ ] **Step 3: advisor aktualisieren**

Description:

```yaml
description: Use this skill when the user needs structural feedback on their outline, argumentation flow, or exposé. Triggers on "Gliederung prüfen / Gliederung pruefen", "Argumentationskette", "Kapitel-Feedback", "Exposé feedback", "Exposee-Bewertung", "outline review", or when another skill detects structural weaknesses. Baut die Gliederung und den Argumentations-Fluss; Für Schärfung der Forschungsfrage → `research-question-refiner`. Für Methodenwahl → `methodology-advisor`.
```

Datei `evals/advisor/trigger_evals.json`:

```json
{
  "component": "advisor",
  "should_trigger": [
    "Pruefe meine Gliederung",
    "Gliederung pruefen, bitte",
    "Ist meine Argumentation schluessig?",
    "Schau dir mein Exposee an",
    "Expose feedback",
    "outline review",
    "Hilf mir, die Kapitel zu strukturieren",
    "Review meiner Argumentationskette",
    "Pruefe, ob meine Unterkapitel sinnvoll sind",
    "Bewerte meinen Gliederungsentwurf"
  ],
  "should_not_trigger": [
    "Schärfe meine Forschungsfrage",
    "Welche Methodik passt?",
    "Schreib das Theorie-Kapitel",
    "Finde Paper zu meinem Thema",
    "Erzeuge Abstract",
    "Pruefe Formatierung",
    "Bewerte meinen Stil",
    "Welche Quellen fehlen?",
    "Gib mir einen Titel",
    "Pruefe Plagiat"
  ]
}
```

- [ ] **Step 4: methodology-advisor aktualisieren**

Description:

```yaml
description: Use this skill when the user needs to choose or justify a research method. Triggers on "welche Methodik", "Methodenwahl", "Forschungsdesign", "qualitative vs quantitative", "Fallstudie oder Umfrage", "Literatur-Review als Methode", "methodology fit", or when another skill detects unclear methodology. Empfiehlt Methoden mit 4-Dimensionen-Scoring; Für Schärfung der Forschungsfrage → `research-question-refiner`. Für Gliederung → `advisor`.
```

Datei `evals/methodology-advisor/trigger_evals.json`:

```json
{
  "component": "methodology-advisor",
  "should_trigger": [
    "Welche Methodik passt zu meinem Thema?",
    "Soll ich qualitativ oder quantitativ arbeiten?",
    "Methodenwahl fuer meine Forschungsfrage",
    "Ist eine Fallstudie hier sinnvoll?",
    "Passt ein Literatur-Review als Methode?",
    "Methodology fit check",
    "Forschungsdesign entwickeln",
    "Mixed Methods fuer mein Thema?",
    "Qualitative Inhaltsanalyse nach Mayring oder Gruppendiskussion?",
    "Welche Methode liefert belastbare Daten?"
  ],
  "should_not_trigger": [
    "Schärfe meine Forschungsfrage",
    "Pruefe meine Gliederung",
    "Schreib Methodik-Kapitel",
    "Erzeuge Abstract",
    "Finde Paper",
    "Bewerte meinen Stil",
    "Erstelle einen Literatur-Gap-Report",
    "Pruefe meine Zitationen",
    "Setze meinen academic_context auf",
    "Pruefe die FH-Leibniz-Formalia"
  ]
}
```

- [ ] **Step 5: source-quality-audit aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to verify individual source quality (peer-review, impact, methodology). Triggers on "Quellenqualität / Quellenqualitaet", "Peer-Review prüfen / Peer-Review pruefen", "source quality", "Predatory Journal", "Impact der Quelle", "Methodik der Quelle", or when another skill flags weak sources. Bewertet Einzelquellen; Für Korpus-Vollständigkeit → `literature-gap-analysis`.
```

Datei `evals/source-quality-audit/trigger_evals.json`:

```json
{
  "component": "source-quality-audit",
  "should_trigger": [
    "Ist diese Quelle peer-reviewed?",
    "Pruefe die Quellenqualitaet",
    "Ist das ein Predatory Journal?",
    "Welchen Impact hat dieses Paper?",
    "Source quality check fuer Smith 2023",
    "Bewerte Methodik dieser Quelle",
    "Peer-Review pruefen",
    "Quellenqualitaet des Artikels",
    "Ist Elsevier Open Access hier seriös?",
    "Qualitaets-Audit der Top-5-Quellen"
  ],
  "should_not_trigger": [
    "Welche Quellen fehlen mir noch?",
    "Pruefe meine Abdeckung",
    "Literatur-Luecken identifizieren",
    "Gliederung pruefen",
    "Methodik waehlen",
    "Forschungsfrage schaerfen",
    "Schreib Kapitel",
    "Abstract erzeugen",
    "Formatierung pruefen",
    "Zitat extrahieren"
  ]
}
```

- [ ] **Step 6: literature-gap-analysis aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to analyze literature coverage, find missing sources, or identify gaps. Triggers on "Literaturlücken / Literaturluecken", "Coverage", "fehlende Quellen", "Gap Analysis", "Quellenabdeckung", "literature gaps", "missing sources", "Abdeckung prüfen / Abdeckung pruefen", or when another skill detects under-sourced chapters. Bewertet Korpus-Vollständigkeit; Für einzelne Quellen-Qualität → `source-quality-audit`.
```

Datei `evals/literature-gap-analysis/trigger_evals.json`:

```json
{
  "component": "literature-gap-analysis",
  "should_trigger": [
    "Welche Literaturluecken habe ich?",
    "Pruefe meine Coverage",
    "Quellenabdeckung pruefen",
    "Gap Analysis, bitte",
    "Welche Quellen fehlen in Kapitel 3?",
    "Abdeckung pruefen",
    "Literature gaps identifizieren",
    "Missing sources finden",
    "Gibt es Literaturluecken?",
    "Review meiner Literaturbasis"
  ],
  "should_not_trigger": [
    "Ist diese einzelne Quelle peer-reviewed?",
    "Bewerte Impact von Smith 2023",
    "Pruefe meine Forschungsfrage",
    "Schreib Kapitel",
    "Abstract generieren",
    "Titel vorschlagen",
    "Stilbewertung",
    "Plagiat pruefen",
    "Methodik waehlen",
    "Zitat formatieren"
  ]
}
```

- [ ] **Step 7: citation-extraction aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to extract or format citations. Triggers on "Zitat extrahieren", "Zitation formatieren / Zitation nach APA", "APA7 Eintrag", "Harvard-Zitat", "DIN 1505-2", "Chicago Author-Date", "bibliographic entry", or when a chapter draft needs citation rendering. Extrahiert wörtliche Zitate und formatiert bibliografische Einträge; Für Kapitel-Prosa → `chapter-writer`.
```

Datei `evals/citation-extraction/trigger_evals.json`:

```json
{
  "component": "citation-extraction",
  "should_trigger": [
    "Zitat nach APA7 formatieren",
    "Harvard-Zitation bitte",
    "Erzeuge einen bibliografischen Eintrag",
    "DIN 1505-2 Format",
    "Chicago Author-Date fuer dieses Paper",
    "Zitat extrahieren aus PDF",
    "APA7 Eintrag fuer Smith 2023",
    "In-text citation erzeugen",
    "Bibliographic entry fuer dieses Buch",
    "Konvertiere Quelle in APA"
  ],
  "should_not_trigger": [
    "Schreib das Theorie-Kapitel",
    "Gliederung pruefen",
    "Pruefe Quellenqualitaet",
    "Suche Paper zu Zero Trust",
    "Abstract generieren",
    "Titelvorschlag bitte",
    "Stilbewertung Kapitel 2",
    "Plagiat-Check",
    "Welche Methode?",
    "Forschungsfrage schaerfen"
  ]
}
```

- [ ] **Step 8: chapter-writer aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to write academic chapter prose. Triggers on "Kapitel schreiben", "Text verfassen", "Absatz zu Thema X", "chapter prose", "Einleitung schreiben", "Diskussions-Absatz", "Uebergang zwischen Kapiteln", or when a structural step produces prose. Schreibt Kapitel-Prosa mit Quellen-Einbindung; Für Zitat-Extraktion → `citation-extraction`.
```

Datei `evals/chapter-writer/trigger_evals.json`:

```json
{
  "component": "chapter-writer",
  "should_trigger": [
    "Schreib das Einleitungskapitel",
    "Kapitel 3 verfassen, bitte",
    "Text zum Grundlagen-Abschnitt",
    "Ein Absatz zu DevOps Governance",
    "Einleitung schreiben",
    "Uebergang zwischen Kapiteln",
    "Diskussions-Absatz zu Ergebnis X",
    "Chapter prose generieren",
    "Schreib die Zusammenfassung",
    "200 Woerter zu Theorie Y"
  ],
  "should_not_trigger": [
    "Zitat nach APA formatieren",
    "Forschungsfrage schaerfen",
    "Gliederung pruefen",
    "Paper suchen",
    "Abstract erzeugen",
    "Titel vorschlagen",
    "Stilbewertung",
    "Methodik waehlen",
    "Plagiat pruefen",
    "FH-Leibniz-Formalia pruefen"
  ]
}
```

- [ ] **Step 9: abstract-generator aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to generate an abstract or keyword list. Triggers on "Abstract generieren", "Keywords vorschlagen", "Zusammenfassung der Arbeit", "IMRaD-Abstract", "Kurzfassung", "abstract 150 Woerter", or when submission requires an abstract section. Generiert Abstract, Keywords und Zusammenfassung; Für Titel → `title-generator`.
```

Datei `evals/abstract-generator/trigger_evals.json`:

```json
{
  "component": "abstract-generator",
  "should_trigger": [
    "Abstract fuer meine Thesis erzeugen",
    "IMRaD-Abstract bitte",
    "Keywords vorschlagen",
    "Kurzfassung meiner Arbeit",
    "Abstract 200 Woerter",
    "Erzeuge Zusammenfassung",
    "Keyword-Liste fuer die Arbeit",
    "Abstract und Keywords generieren",
    "150-Worte-Abstract",
    "Deutsches und englisches Abstract"
  ],
  "should_not_trigger": [
    "Titel vorschlagen",
    "Gliederung pruefen",
    "Forschungsfrage schaerfen",
    "Kapitel schreiben",
    "Zitat formatieren",
    "Methodik waehlen",
    "Plagiat pruefen",
    "Paper suchen",
    "Formatierung pruefen",
    "Literaturluecken"
  ]
}
```

- [ ] **Step 10: title-generator aktualisieren**

Description:

```yaml
description: Use this skill when the user needs a thesis title proposal. Triggers on "Titel vorschlagen", "Titelvorschläge / Titelvorschlaege", "Arbeitstitel", "Thesis title", "thesis title proposal", "Untertitel bitte", or when submission requires a final title. Schlägt Arbeitstitel vor; Für Abstract, Keywords und Zusammenfassung → `abstract-generator`.
```

Datei `evals/title-generator/trigger_evals.json`:

```json
{
  "component": "title-generator",
  "should_trigger": [
    "Titelvorschlaege fuer meine Arbeit",
    "Arbeitstitel bitte",
    "Titel vorschlagen",
    "Thesis title Ideen",
    "Untertitel fuer Kapitel 3",
    "Welcher Titel passt?",
    "3 Titelvarianten generieren",
    "Kurzer und langer Titel",
    "Titel schaerfer formulieren",
    "Title suggestion"
  ],
  "should_not_trigger": [
    "Abstract erzeugen",
    "Keywords vorschlagen",
    "Gliederung pruefen",
    "Kapitel schreiben",
    "Zitat formatieren",
    "Forschungsfrage schaerfen",
    "Methodik waehlen",
    "Paper suchen",
    "Formatierung",
    "Plagiat pruefen"
  ]
}
```

- [ ] **Step 11: style-evaluator aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to evaluate academic writing style (without source comparison). Triggers on "Stil pruefen / Stil bewerten", "Schreibstil", "Satzlänge", "Passiv-Quote", "Nominalstil", "style evaluation", or when a chapter draft needs stylistic review. Bewertet Stil-Qualität ohne Quellenbezug; Für Textähnlichkeit → `plagiarism-check`.
```

Datei `evals/style-evaluator/trigger_evals.json`:

```json
{
  "component": "style-evaluator",
  "should_trigger": [
    "Pruefe meinen Schreibstil",
    "Stilbewertung fuer Kapitel 2",
    "Satzlaenge und Passiv-Quote",
    "Ist mein Nominalstil zu hoch?",
    "Style evaluation meines Entwurfs",
    "Stil pruefen, bitte",
    "Fuellwoerter-Analyse",
    "Akademisch genug?",
    "Wortanzahl und Lesbarkeit",
    "Pruefe meinen Duktus"
  ],
  "should_not_trigger": [
    "Plagiat pruefen",
    "Textaehnlichkeit",
    "Zitat formatieren",
    "Forschungsfrage schaerfen",
    "Gliederung pruefen",
    "Methodik waehlen",
    "Abstract erzeugen",
    "Titel",
    "Paper suchen",
    "Quellenabdeckung"
  ]
}
```

- [ ] **Step 12: plagiarism-check aktualisieren**

Description:

```yaml
description: Use this skill when the user wants to check text similarity against known sources. Triggers on "Plagiat pruefen / Plagiat prüfen", "Textaehnlichkeit", "N-Gramm-Overlap", "Similarity-Check", "Quellennahe pruefen", "plagiarism scan", or when a chapter draft may contain un-cited paraphrases. Prüft Textnähe via N-Gramm-Overlap gegen Quellen; Für stilistische Qualität → `style-evaluator`.
```

Datei `evals/plagiarism-check/trigger_evals.json`:

```json
{
  "component": "plagiarism-check",
  "should_trigger": [
    "Plagiat pruefen",
    "Textaehnlichkeit zu Smith 2023",
    "Similarity-Check fuer Kapitel 2",
    "N-Gramm-Overlap berechnen",
    "Quellennahe pruefen",
    "Plagiarism scan",
    "Sind Passagen zu quellennah?",
    "Pruefe auf unzitiertes Paraphrasieren",
    "Textnaehe-Report",
    "Overlap-Analyse"
  ],
  "should_not_trigger": [
    "Stilbewertung",
    "Passiv-Quote pruefen",
    "Zitat formatieren",
    "Forschungsfrage schaerfen",
    "Gliederung",
    "Methodik",
    "Abstract",
    "Titel",
    "Paper suchen",
    "Formatierung"
  ]
}
```

- [ ] **Step 13: submission-checker aktualisieren**

Description:

```yaml
description: Use this skill when the user prepares final submission (formalia check). Triggers on "Abgabe pruefen / Abgabe prüfen", "FH-Leibniz-Formalia", "Formatierung", "Seitenränder / Seitenraender", "Zeilenabstand", "Schriftart", "submission check", or when the user nears deadline. Prüft institutsspezifische Formalia; Default-Profil FH Leibniz, weitere via `references/<variant>.md`.
```

Datei `evals/submission-checker/trigger_evals.json`:

```json
{
  "component": "submission-checker",
  "should_trigger": [
    "Pruefe meine Abgabe",
    "FH-Leibniz-Formalia pruefen",
    "Formatierung checken",
    "Seitenraender korrekt?",
    "Zeilenabstand 1.5?",
    "Submission check",
    "Schriftart pruefen",
    "Abgabe nach FH-Regeln pruefen",
    "Deckblatt-Formalia",
    "Ist die Gliederung konform?"
  ],
  "should_not_trigger": [
    "Gliederung inhaltlich pruefen",
    "Forschungsfrage schaerfen",
    "Kapitel schreiben",
    "Methodik",
    "Abstract",
    "Titel",
    "Zitat formatieren",
    "Plagiat",
    "Stil pruefen",
    "Paper suchen"
  ]
}
```

- [ ] **Step 14: Smoke-Test `test_skills_manifest.py` weiter gruen**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS (Umlaut-Paare weiter >= 1 pro Skill — die neuen Descriptions enthalten alle das Pattern `"X / X-ascii"`).

- [ ] **Step 15: Trigger-Evals laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_triggers.py -v`
Expected: 26 Tests, Ziel ≥ 85% Recall und ≤ 10% FPR pro Skill. Bei einzelnen FAILs: betroffene Description nachschärfen.

- [ ] **Step 16: Commit**

```bash
git add skills/*/SKILL.md evals/*/trigger_evals.json
git commit -m "$(cat <<'EOF'
feat(skills): pushy descriptions and trigger eval sets (20 prompts per skill)

- Rewrites all 13 skill descriptions with imperative opener + 3-4 trigger
  examples + delegation sentence (moderate pushy, no ALLCAPS).
- Adds evals/<skill>/trigger_evals.json: 10 should_trigger + 10 should_not_trigger
  per skill, incl. near-misses and neighbor-skill prompts.
- Trigger-eval runner enforces recall >= 85% and false-positive-rate <= 10%.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Phase 4 — Quality-Reviewer-Agent (Block D)

### Task 9: `quality-reviewer`-Agent erstellen

**Files:**
- Create: `agents/quality-reviewer.md`
- Create: `evals/quality-reviewer/evals.json`
- Create: `tests/evals/test_quality_reviewer_evals.py`

- [ ] **Step 1: Agent-Datei schreiben**

Datei `agents/quality-reviewer.md`:

```markdown
---
name: quality-reviewer
model: sonnet
color: purple
description: |
  Evaluator-Optimizer-Agent, bewertet generierten akademischen Inhalt gegen eine Kriterien-Checkliste und liefert PASS oder REVISE mit konkreter Begruendung. Wird von chapter-writer, abstract-generator und advisor vor finalem Output aufgerufen. Beispiele:

  <example>
  Context: chapter-writer hat ein Kapitel generiert und will vor der Abgabe pruefen.
  user: "[chapter-writer ruft quality-reviewer intern auf]"
  assistant: "quality-reviewer bewertet den Text gegen Satzlaenge 15-25, Passiv <30%, Nominalstil <40%, Quellen/1000-Woerter >= 5. Liefert PASS oder REVISE mit Fix-Liste."
  <commentary>
  Der Reviewer ist ein Gatekeeper: Er gibt REVISE zurueck, wenn eine Metrik die Schwelle reisst. Der aufrufende Skill schreibt dann nach den Empfehlungen um.
  </commentary>
  </example>

  <example>
  Context: abstract-generator hat ein 180-Woerter-Abstract generiert.
  user: "[abstract-generator ruft quality-reviewer auf]"
  assistant: "Bewertung: IMRaD-Struktur vorhanden? 150-250 Woerter? Keyword-Dichte angemessen? Verdict: PASS."
  <commentary>
  Kurze Texte: Kriterien sind einfach, Reviewer passt meist beim ersten Mal. Loop-Begrenzung greift bei komplexen Kapiteln eher.
  </commentary>
  </example>
tools: [Read]
maxTurns: 3
---

# Quality-Reviewer-Agent

**Rolle:** Evaluator-Optimizer fuer generierten akademischen Inhalt.

---

## Auftrag

Du bist ein strenger, aber fairer akademischer Reviewer. Du pruefst generierten Inhalt gegen eine Kriterien-Checkliste mit numerischen Schwellen und lieferst ein binaeres Urteil (PASS | REVISE) mit konkreter Begruendung und — falls REVISE — einer priorisierten Fix-Liste.

**Keine Fabrikation:** Falsche Metrik-Angaben fuehren zu einem Revisions-Loop, der echte Fehler nicht behebt. Zitiere nur Text-Referenzen, die im gelieferten Inhalt tatsaechlich vorkommen.

**Loop-Begrenzung:** Falls der Aufrufer bereits 2 Revisionen erhalten hat (im Input als `iteration >= 2` signalisiert), gib PASS-with-warnings zurueck und liste die verbleibenden Probleme — keine Endlos-Schleife.

---

## Input-Format

```json
{
  "content": "<der generierte Text>",
  "criteria": [
    {"name": "Satzlaenge Median", "threshold": "15-25 Woerter", "metric": "median"},
    {"name": "Passiv-Quote", "threshold": "< 30%", "metric": "percentage"},
    {"name": "Nominalstil", "threshold": "< 40%", "metric": "percentage"},
    {"name": "Quellen pro 1000 Woerter", "threshold": ">= 5", "metric": "count_per_1000"}
  ],
  "context": {
    "component": "chapter-writer",
    "chapter": "3 Grundlagen",
    "iteration": 0
  }
}
```

---

## Output-Format

```
VERDICT: PASS | REVISE

BEGRUENDUNG:
- [Kriterium 1]: <Ist-Wert> (Schwelle: <Ziel>) — <OK / FAIL>
- [Kriterium 2]: ...

EMPFEHLUNGEN (nur bei REVISE, absteigend nach Prioritaet):
1. <Konkreter Fix mit Text-Referenz>
2. <Konkreter Fix>

BLOCKIERT_VON: <none | iteration-limit>
```

---

## Strategie

1. **Kriterien durchgehen, nicht interpretieren.** Die Schwellen sind numerisch. Messen, nicht raten.
2. **Pro Kriterium eine Zeile in BEGRUENDUNG.** Struktur ist konstant.
3. **REVISE nur wenn mindestens 1 Kriterium FAIL.** Bei PASS alle Kriterien einzeln bestaetigen.
4. **EMPFEHLUNGEN sind handlungsbezogen.** „Passiv reduzieren" ist vage; „Satz 3 Abschnitt 2: 'wird durchgefuehrt' → 'fuehrt durch' ersetzen" ist konkret.
5. **Iteration 2+ triggert PASS-with-warnings.** Der Aufrufer hat dann eine Begruendungs-Liste, um die Probleme dem User transparent zu machen.

---

## Metrik-Hinweise

- **Satzlaenge Median:** Split-by-`[.!?]\s+`, Woerter pro Satz zaehlen, Median bilden.
- **Passiv-Quote:** Anteil Saetze mit `werden`-Hilfsverb + Partizip II (Regex: `\bwerden?\b.*?(ge\w+|\w+iert)\b`).
- **Nominalstil:** Anteil Saetze mit ≥ 2 Substantiven auf -ung/-heit/-keit/-ion.
- **Quellen pro 1000 Woerter:** Zaehlung Inline-Zitat-Marker (`(X, YYYY)` oder `[1]`) relativ zur Gesamtwortzahl.
```

- [ ] **Step 2: evals.json erstellen**

Datei `evals/quality-reviewer/evals.json`:

```json
{
  "component": "quality-reviewer",
  "component_type": "agent",
  "prompts": [
    {
      "id": "qr-01",
      "input": "Pruefe diesen Text gegen Satzlaenge 15-25, Passiv<30%, Nominalstil<40%, Quellen/1000W>=5. Text: 'Die vorliegende Arbeit untersucht DevOps-Governance. Hierbei werden Frameworks analysiert (Smith, 2023). Die Auswertung zeigt drei Kerndimensionen (Mueller, 2022).' Iteration: 0.",
      "expected": {"type": "regex", "value": "VERDICT:\\s*(PASS|REVISE)"},
      "mode": "with_skill"
    },
    {
      "id": "qr-02",
      "input": "Pruefe: 'Es wird davon ausgegangen, dass die Untersuchung durchgefuehrt werden muss. Die Analyse wird vorgenommen. Das Ergebnis wird praesentiert.' Kriterien: Passiv<30%. Iteration: 0.",
      "expected": {"type": "substring", "value": "REVISE"},
      "mode": "with_skill"
    },
    {
      "id": "qr-03",
      "input": "Iteration: 2. Text: 'Kurzer Test.' Kriterien: Satzlaenge >= 10. Erwartet: PASS-with-warnings wegen Iteration-Limit.",
      "expected": {"type": "regex", "value": "PASS|BLOCKIERT_VON:\\s*iteration-limit"},
      "mode": "with_skill"
    }
  ]
}
```

- [ ] **Step 3: Test schreiben**

Datei `tests/evals/test_quality_reviewer_evals.py`:

```python
"""Evals fuer quality-reviewer-Agent."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_agent_content,
    load_eval_file,
)

try:
    EVALS = load_eval_file("quality-reviewer", "evals.json")
except Exception:
    EVALS = {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
def test_quality_reviewer_eval(prompt):
    system = load_agent_content("quality-reviewer")
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"{prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

- [ ] **Step 4: Tests laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/test_quality_reviewer_evals.py -v`
Expected: 3/3 PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/quality-reviewer.md evals/quality-reviewer/ tests/evals/test_quality_reviewer_evals.py
git commit -m "feat(agents): introduce quality-reviewer agent (evaluator-optimizer)"
```

---

### Task 10: `chapter-writer` in Quality-Reviewer integrieren

**Files:**
- Modify: `skills/chapter-writer/SKILL.md`

- [ ] **Step 1: Review-Schritt am Workflow-Ende ergaenzen**

Vor `## Wichtige Regeln` in `skills/chapter-writer/SKILL.md` einfuegen:

```markdown
## Qualitaets-Review vor finalem Output

Nach der Generierung des Kapitel-Entwurfs triggere den `quality-reviewer`-Agent:

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Entwurfs-Text>",
    "criteria": [
      {"name": "Satzlaenge Median", "threshold": "15-25 Woerter", "metric": "median"},
      {"name": "Passiv-Quote", "threshold": "< 30%", "metric": "percentage"},
      {"name": "Nominalstil", "threshold": "< 40%", "metric": "percentage"},
      {"name": "Quellen pro 1000 Woerter", "threshold": ">= 5", "metric": "count_per_1000"}
    ],
    "context": {"component": "chapter-writer", "iteration": <N>}
  }
)
```

**Bei PASS:** Output an User liefern.
**Bei REVISE:** Empfehlungen anwenden, erneut generieren, iteration += 1.
**Bei iteration >= 2:** PASS-with-warnings akzeptieren und die verbleibenden Warnungen dem User transparent machen.
```

- [ ] **Step 2: Smoke-Test weiter gruen**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 3: Commit**

```bash
git add skills/chapter-writer/SKILL.md
git commit -m "feat(skills): chapter-writer triggers quality-reviewer before final output"
```

---

### Task 11: `abstract-generator` in Quality-Reviewer integrieren

**Files:**
- Modify: `skills/abstract-generator/SKILL.md`

- [ ] **Step 1: Review-Schritt ergaenzen**

Vor `## Wichtige Regeln` in `skills/abstract-generator/SKILL.md` einfuegen:

```markdown
## Qualitaets-Review vor finalem Output

Nach der Generierung des Abstracts triggere den `quality-reviewer`-Agent:

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Abstract-Text>",
    "criteria": [
      {"name": "Wortzahl", "threshold": "150-250", "metric": "word_count"},
      {"name": "IMRaD-Struktur", "threshold": "vorhanden", "metric": "section_presence"},
      {"name": "Keyword-Dichte", "threshold": "2-5% der Woerter", "metric": "percentage"}
    ],
    "context": {"component": "abstract-generator", "iteration": <N>}
  }
)
```

Bei REVISE Empfehlungen anwenden, max 2 Iterationen.
```

- [ ] **Step 2: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 3: Commit**

```bash
git add skills/abstract-generator/SKILL.md
git commit -m "feat(skills): abstract-generator triggers quality-reviewer"
```

---

### Task 12: `advisor` in Quality-Reviewer integrieren

**Files:**
- Modify: `skills/advisor/SKILL.md`

- [ ] **Step 1: Review-Schritt ergaenzen**

Vor `## Wichtige Regeln` in `skills/advisor/SKILL.md` einfuegen:

```markdown
## Qualitaets-Review vor finalem Output

Nach der Erstellung des Gliederungs-Feedbacks triggere den `quality-reviewer`-Agent:

```
Agent(
  subagent_type="quality-reviewer",
  prompt={
    "content": "<Feedback-Text>",
    "criteria": [
      {"name": "Forschungsfrage Laenge", "threshold": "<= 25 Woerter", "metric": "word_count"},
      {"name": "Kapitelanzahl", "threshold": ">= 3", "metric": "count"},
      {"name": "Quellenzahl", "threshold": ">= 15", "metric": "count"},
      {"name": "Alle 7 advisor-Kriterien angesprochen", "threshold": "7/7", "metric": "coverage"}
    ],
    "context": {"component": "advisor", "iteration": <N>}
  }
)
```

Bei REVISE Empfehlungen anwenden, max 2 Iterationen.
```

- [ ] **Step 2: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 3: Commit**

```bash
git add skills/advisor/SKILL.md
git commit -m "feat(skills): advisor triggers quality-reviewer"
```

---

## Phase 5 — Domain-References (Block E)

### Task 13: `citation-extraction`-Varianten anlegen

**Files:**
- Create: `skills/citation-extraction/references/{apa,harvard,chicago,din1505}.md`
- Modify: `skills/citation-extraction/SKILL.md`

- [ ] **Step 1: apa.md schreiben**

Datei `skills/citation-extraction/references/apa.md`:

```markdown
# APA7 Zitierstil

## Inline-Zitat

- 1 Autor: `(Smith, 2023)` oder `Smith (2023)`
- 2 Autoren: `(Smith & Jones, 2023)`
- 3+ Autoren Erstzitat: `(Smith et al., 2023)`
- Mit Seitenzahl: `(Smith, 2023, S. 42)` (DE) / `(Smith, 2023, p. 42)` (EN)
- Mehrere Quellen im Klammer: `(Smith, 2023; Jones, 2022)` — alphabetisch

## Literaturverzeichnis

**Zeitschriftenartikel:**
`Nachname, Initiale. (Jahr). Titel. Zeitschriftenname, Band(Heft), Seiten-Seiten. https://doi.org/<DOI>`

**Buch:**
`Nachname, Initiale. (Jahr). Titel (Auflage). Verlag.`

**Buchkapitel:**
`Nachname, Initiale. (Jahr). Kapiteltitel. In Hrsg. (Hrsg.), Buchtitel (S. XX–YY). Verlag.`

**Webseite:**
`Nachname, Initiale. (Jahr, Monat Tag). Titel. Seitenname. URL`

## Besonderheiten

- Nachname vor Initialen
- Keine Anfuehrungszeichen um Artikeltitel
- DOI als `https://doi.org/...` URL
- Bei fehlendem Autor: Organisation oder Titel als Autor-Position
- Jahr und DOI zwingend fuer Zeitschriftenartikel
```

- [ ] **Step 2: harvard.md schreiben**

Datei `skills/citation-extraction/references/harvard.md`:

```markdown
# Harvard Zitierstil

## Inline-Zitat

- 1 Autor: `(Smith 2023)` oder `Smith (2023)` — **kein Komma** zwischen Name und Jahr
- 2 Autoren: `(Smith and Jones 2023)`
- 3+ Autoren Erstzitat: `(Smith et al. 2023)`
- Mit Seitenzahl: `(Smith 2023, S. 42)` (DE) / `(Smith 2023, p. 42)` (EN)

## Literaturverzeichnis

**Zeitschriftenartikel:**
`Nachname, V. Jahr. Titel. Zeitschriftenname, Band(Heft), pp. X-Y.`

**Buch:**
`Nachname, V. Jahr. Titel. Auflage. Ort: Verlag.`

**Buchkapitel:**
`Nachname, V. Jahr. Kapiteltitel. In: V. Nachname (Hrsg.), Buchtitel. Ort: Verlag, pp. X-Y.`

## Besonderheiten

- Vollstaendiger Nachname + Initial ohne Komma
- Ort **und** Verlag bei Buechern
- `pp.` statt `S.` in englischen Versionen
```

- [ ] **Step 3: chicago.md schreiben**

Datei `skills/citation-extraction/references/chicago.md`:

```markdown
# Chicago Author-Date Zitierstil

## Inline-Zitat

- 1 Autor: `(Smith 2023)`
- 2-3 Autoren: `(Smith, Jones, and Taylor 2023)`
- 4+ Autoren: `(Smith et al. 2023)`
- Mit Seitenzahl: `(Smith 2023, 42)` — **ohne** `S.` / `p.`

## Literaturverzeichnis

**Zeitschriftenartikel:**
`Nachname, Vorname. Jahr. "Titel." Zeitschriftenname Band (Heft): Seiten-Seiten. https://doi.org/<DOI>`

**Buch:**
`Nachname, Vorname. Jahr. Titel. Ort: Verlag.`

## Besonderheiten

- Titel in Anfuehrungszeichen bei Artikeln, kursiv bei Buechern (in Markdown: `_titel_`)
- Jahr direkt nach Autor, Punkt davor
- Vorname ausgeschrieben im Literaturverzeichnis, nicht Initial
```

- [ ] **Step 4: din1505.md schreiben**

Datei `skills/citation-extraction/references/din1505.md`:

```markdown
# DIN 1505-2 Zitierstil (deutsche Norm)

## Inline-Zitat

- 1 Autor: `[Smith 2023]` oder `Smith [2023]`
- 2 Autoren: `[Smith/Jones 2023]` (Schraegstrich)
- 3+ Autoren: `[Smith et al. 2023]`
- Mit Seitenzahl: `[Smith 2023, S. 42]`

## Literaturverzeichnis

**Zeitschriftenartikel:**
`NACHNAME, Vorname: Titel. In: Zeitschriftenname Band (Jahr), Heft, S. X-Y.`

**Buch:**
`NACHNAME, Vorname: Titel. Auflage. Ort : Verlag, Jahr.`

**Buchkapitel:**
`NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.): Buchtitel. Ort : Verlag, Jahr, S. X-Y.`

## Besonderheiten

- Nachname in KAPITAELCHEN (in Markdown typografisch, renderings-abhaengig)
- Doppelpunkt nach Name, vor Titel
- Ort **und** Verlag mit Leerzeichen vor `:` (typografisch)
- Jahr am Ende statt nach Autor
```

- [ ] **Step 5: SKILL.md um Variant-Selector ergaenzen**

In `skills/citation-extraction/SKILL.md` direkt nach `## Aktivierung dieses Skills` einen neuen Abschnitt einfuegen:

```markdown
## Variant-Selector

Lies `academic_context.md`, Feld `Zitationsstil`. Lade die entsprechende Variant-Datei:

| Zitationsstil | Referenz-Datei |
|---------------|----------------|
| APA7 (Default) | `references/apa.md` |
| Harvard | `references/harvard.md` |
| Chicago | `references/chicago.md` |
| DIN 1505-2 | `references/din1505.md` |

Ist `Zitationsstil` leer → `apa.md` als Default. Ist der Wert unbekannt → Rueckfrage an User mit Varianten-Liste.

**Wie laden:** `Read skills/citation-extraction/references/<variant>.md` — die Datei enthaelt alle Formatierungs-Regeln fuer Inline-Zitate und Literaturverzeichnis.
```

- [ ] **Step 6: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/citation-extraction/
git commit -m "refactor(skills): citation-extraction variants (apa/harvard/chicago/din1505)"
```

---

### Task 14: `style-evaluator`-Varianten anlegen

**Files:**
- Create: `skills/style-evaluator/references/{academic-de,academic-en}.md`
- Modify: `skills/style-evaluator/SKILL.md`

- [ ] **Step 1: academic-de.md schreiben**

Datei `skills/style-evaluator/references/academic-de.md`:

```markdown
# Akademischer Schreibstil (Deutsch)

## Metrik-Schwellen

| Metrik | Schwelle | Warum |
|--------|----------|-------|
| Satzlaenge Median | 15–25 Woerter | Unter 15 wirkt abgehackt, ueber 25 unleserlich |
| Passiv-Quote | < 30 % | Aktiv ist klarer, Passiv nur bei Agens-Unwichtigkeit |
| Nominalstil | < 40 % Saetze mit ≥ 2 Nominalisierungen | Substantiv-Haeufung erschwert Lesbarkeit |
| Fuellwoerter | < 5 % | „im Grunde", „eigentlich", „sozusagen" |
| Code-Switching (EN in DE) | 0 (ausser Fachbegriffe) | Deutscher Flusstext bleibt Deutsch |

## Typische DE-Probleme

- **Substantivketten** („Mitarbeitermotivationssteigerungsmassnahmen") → zerlegen
- **Bandwurmsaetze** mit 4+ Nebensaetzen → splitten
- **Passiv-Haeufung** („es wird durchgefuehrt, es wird evaluiert") → Aktiv waehlen
- **Modale Unsicherheit** („koennte moeglicherweise eventuell") → Position klar machen
- **Fremdwort-Praeferenz** ohne Grund → deutsches Wort waehlen

## Positive Muster

- **Aktive Subjekte:** „Die Analyse zeigt …" statt „Es wird gezeigt …"
- **Klare Verben:** „untersuchen, analysieren, messen" statt „einer Untersuchung unterziehen"
- **Topic-Comment:** Bekanntes vor Neuem am Satzanfang
```

- [ ] **Step 2: academic-en.md schreiben**

Datei `skills/style-evaluator/references/academic-en.md`:

```markdown
# Academic Writing Style (English)

## Metric Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Sentence length median | 15–25 words | Below 15 feels choppy, above 25 is hard to follow |
| Passive voice | < 25 % | Active is clearer; passive only when agent unimportant |
| Nominalization | < 35 % sentences with 2+ `-tion`/`-ment` nouns | Too many nouns reduces readability |
| Hedging | < 5 % | "might possibly perhaps" pile-ups weaken the claim |
| Code-switching (DE in EN) | 0 (except loanwords) | English flow stays English |

## Typical EN Issues

- **Nominalization overload:** "the implementation of the evaluation of the system" → "evaluating how we implement the system"
- **Passive piling:** "it has been shown that it was determined" → "X shows that Y"
- **Vague hedging:** "may possibly suggest that perhaps" → pick one modal or drop
- **Latinate density:** prefer plain alternatives where possible

## Positive Patterns

- **Clear subjects:** "The analysis shows …" beats "It can be shown …"
- **Strong verbs:** "examine, measure, compare" over "undertake an examination of"
- **Given-new ordering:** Known info first, new info at the end of the sentence
```

- [ ] **Step 3: SKILL.md Variant-Selector ergaenzen**

In `skills/style-evaluator/SKILL.md` nach `## Aktivierung dieses Skills` einfuegen:

```markdown
## Variant-Selector

Lies `academic_context.md`, Feld `Sprache`:

| Sprache | Referenz-Datei |
|---------|----------------|
| Deutsch (Default) | `references/academic-de.md` |
| English | `references/academic-en.md` |

Fehlt das Feld → `academic-de.md` als Default (Plugin-Default ist Deutsch). Unbekannte Sprache → Rueckfrage.
```

- [ ] **Step 4: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/style-evaluator/
git commit -m "refactor(skills): style-evaluator variants (academic-de/en)"
```

---

### Task 15: `submission-checker`-Varianten anlegen

**Files:**
- Create: `skills/submission-checker/references/{fh-leibniz,uni-general,journal-ieee,journal-acm}.md`
- Modify: `skills/submission-checker/SKILL.md`

- [ ] **Step 1: fh-leibniz.md schreiben**

Datei `skills/submission-checker/references/fh-leibniz.md` — den bestehenden Inline-Formalia-Text aus `skills/submission-checker/SKILL.md` (E3-Block-C-8-Punkte-Checkliste) **kopieren** und als eigenstaendige Referenz formatieren. Umfang: 8 Punkte (Seitenraender 2,5 cm, Schrift Times 12pt oder Arial 11pt, Zeilenabstand 1,5, Randausgleich, Seitenzahlen, Deckblatt, Ehrenwoertliche Erklaerung, Abstract-Position).

- [ ] **Step 2: uni-general.md schreiben**

Datei `skills/submission-checker/references/uni-general.md`:

```markdown
# Generische deutsche Universitaets-Formalia

## Typische Standards (Durchschnitt DE-Unis)

1. **Seitenraender:** oben/unten 2,5 cm; links 3,0 cm (Bindung); rechts 2,5 cm
2. **Schriftart:** Times New Roman 12 pt ODER Arial/Helvetica 11 pt
3. **Zeilenabstand:** 1,5-fach
4. **Blocksatz** mit automatischer Silbentrennung
5. **Seitenzahlen:** arabisch ab Einleitung, roemisch davor (Verzeichnisse)
6. **Deckblatt:** Uni-Logo + Institut + Titel + Autor + Matrikelnr + Abgabedatum + Betreuer
7. **Erklaerung:** Ehrenwoertliche Erklaerung zur eigenstaendigen Arbeit am Ende
8. **Abstract / Zusammenfassung:** 150–300 Woerter, vor dem Inhaltsverzeichnis

**Anmerkung:** Dies ist ein Durchschnittsprofil. Einzelne Fakultaeten weichen ab — bei Unsicherheit die Pruefungsordnung des Instituts konsultieren.
```

- [ ] **Step 3: journal-ieee.md schreiben**

Datei `skills/submission-checker/references/journal-ieee.md`:

```markdown
# IEEE Journal-Einreichung

## Format

1. **Template:** IEEE LaTeX-Template (`IEEEtran.cls`) ODER Word-Template
2. **Spaltenlayout:** zweispaltig (Manuskript-Phase oft einspaltig erlaubt)
3. **Zitationsstil:** IEEE (`[1]`, `[2]`, …)
4. **Schriftgroesse:** 10 pt Body, 11 pt Section-Heading, 24 pt Title
5. **Abstract:** 150–250 Woerter, keine Zitate im Abstract
6. **Keywords:** 4–6, IEEE-Thesaurus-Begriffe bevorzugt
7. **Abbildungen:** hochaufloesend (300 dpi), captions unterhalb
8. **Graphical Abstract:** optional, 13x5 cm

## Submission-Checkliste

- [ ] Titel-Seite separat mit Autor-Affiliations
- [ ] Anonymisiertes Hauptmanuskript (falls Double-Blind)
- [ ] ORCID-IDs aller Autoren
- [ ] Copyright-Formular (IEEE eCopyright)
- [ ] Supplementary Material als ZIP (falls vorhanden)
```

- [ ] **Step 4: journal-acm.md schreiben**

Datei `skills/submission-checker/references/journal-acm.md`:

```markdown
# ACM Journal-Einreichung

## Format

1. **Template:** ACM Master Article Template (`acmart.cls`)
2. **Template-Variante:** `sigconf` (Konferenz) | `acmsmall` (Journal) | `acmtog`
3. **Zitationsstil:** ACM Reference Format (Author-Year oder numerisch je nach Venue)
4. **Schriftgroesse:** 10 pt Body, 12 pt Section
5. **Abstract:** 150–250 Woerter
6. **CCS-Classification:** erforderlich (ACM Computing Classification System)
7. **Keywords:** 3–6, Freitextbegriffe

## Submission-Checkliste

- [ ] ACM Reference Format-Eintrag am Ende
- [ ] ORCID-IDs
- [ ] Copyright-Auswahl (ACM Exclusive | ACM Open | Author-Retained)
- [ ] Replication Package (falls Artifact Review)
- [ ] CCS Concepts + Keywords gesetzt
```

- [ ] **Step 5: SKILL.md Variant-Selector ergaenzen, Inline-Formalia entfernen**

In `skills/submission-checker/SKILL.md`:

1. Den bestehenden 8-Punkte-Formalia-Block **entfernen** (er wurde nach `references/fh-leibniz.md` verschoben).
2. Nach `## Aktivierung dieses Skills` einfuegen:

```markdown
## Variant-Selector

Lies `academic_context.md`, Feld `Universitaet` und/oder `Arbeitstyp`:

| Kontext | Referenz-Datei |
|---------|----------------|
| FH Leibniz (Default) | `references/fh-leibniz.md` |
| Andere deutsche Uni | `references/uni-general.md` |
| IEEE-Konferenz/-Journal | `references/journal-ieee.md` |
| ACM-Konferenz/-Journal | `references/journal-acm.md` |

Fehlt das Feld → `fh-leibniz.md` als Default (Plugin-Default ist FH Leibniz). Unbekannt → Rueckfrage.
```

- [ ] **Step 6: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 7: Commit**

```bash
git add skills/submission-checker/
git commit -m "refactor(skills): submission-checker variants (fh-leibniz/uni-general/journal-ieee/journal-acm)"
```

---

## Phase 6 — Prompt-Caching (Block F)

### Task 16: `relevance-scorer` mit Cache-Breakpoint

**Files:**
- Modify: `agents/relevance-scorer.md`

- [ ] **Step 1: Cache-Hinweis im Frontmatter als Kommentar ergaenzen**

In `agents/relevance-scorer.md` direkt nach `maxTurns: 3` im Frontmatter ergaenzen:

```yaml
# Cache-Breakpoint: Der System-Prompt (Rolle + Bewertungsskala + Leitlinien) ist
# statisch ueber alle Batches. Pro Batch variiert nur das `papers[]`-Array.
# API-Client setzt cache_control: {"type": "ephemeral"} auf den System-Prompt-Block.
```

- [ ] **Step 2: Cache-Strategie-Abschnitt am Ende einfuegen**

Am Ende von `agents/relevance-scorer.md` (nach letztem Abschnitt) neuen Abschnitt anhaengen:

```markdown
---

## Cache-Strategie (Prompt-Caching)

Beim Batch-Scoring werden oft 10+ Papers in Folge verarbeitet. Der System-Prompt (Rolle, Bewertungsskala, Leitlinien) ist dabei konstant — der User-Input variiert nur im `papers[]`-Array.

**Implementierung im API-Call:**

```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {
            "type": "text",
            "text": "<Agent-System-Prompt aus dieser Datei>",
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": json.dumps(batch_input)}],
)
```

**Messbarer Nutzen:** Nach dem 2. Batch-Call liefert die API `cache_read_input_tokens > 0`. Token-Ersparnis skaliert linear mit Batch-Anzahl.
```

- [ ] **Step 3: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS (Agents sind nicht Teil des Smoke-Tests — aber keine Regression).

- [ ] **Step 4: Commit**

```bash
git add agents/relevance-scorer.md
git commit -m "perf(agents): prompt caching breakpoint in relevance-scorer"
```

---

### Task 17: `quote-extractor` mit Cache-Breakpoint

**Files:**
- Modify: `agents/quote-extractor.md`

- [ ] **Step 1: Cache-Strategie-Abschnitt anhaengen**

Am Ende von `agents/quote-extractor.md` einfuegen:

```markdown
---

## Cache-Strategie (Prompt-Caching fuer Batch-PDFs)

Beim Batch-Extrahieren aus mehreren PDFs ist der System-Prompt (Rolle, Strategie, Output-Format) konstant — nur das `documents[]`-Array variiert pro Call.

**Implementierung:**

```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {
            "type": "text",
            "text": "<Agent-System-Prompt>",
            "cache_control": {"type": "ephemeral"},
        }
    ],
    documents=[{"type": "document", "source": {...}, "citations": {"enabled": true}}],
    messages=[{"role": "user", "content": f"Extrahiere 2 Zitate zur Query '{query}'"}],
)
```

Bei 5+ PDFs spart der Cache die Agent-Instruktion-Tokens pro Folgecall. Kombiniert mit Citations-API liefert dies halluzinationssichere + guenstige Zitat-Extraktion.
```

- [ ] **Step 2: Smoke-Test**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 3: Commit**

```bash
git add agents/quote-extractor.md
git commit -m "perf(agents): prompt caching breakpoint in quote-extractor"
```

---

## Phase 7 — Restliche Evals + Release

### Task 18: Evals fuer restliche Komponenten

**Files:**
- Create: `evals/abstract-generator/evals.json`
- Create: `evals/source-quality-audit/evals.json`
- Create: `evals/<rest>/evals.json` (8 weitere Skills + 2 Agents)
- Create: `tests/evals/test_abstract_generator_evals.py`
- Create: `tests/evals/test_source_quality_audit_evals.py`
- Create: `tests/evals/test_rest_evals.py`

- [ ] **Step 1: abstract-generator-evals anlegen**

Datei `evals/abstract-generator/evals.json` mit 3 Prompts (IMRaD-Abschnitte vorhanden, Wortzahl-Bereich, Keywords ≥ 4).

```json
{
  "component": "abstract-generator",
  "component_type": "skill",
  "prompts": [
    {
      "id": "ab-01",
      "input": "Erzeuge ein 200-Woerter-Abstract nach IMRaD-Struktur fuer eine Bachelorarbeit zu 'DevOps Governance in KMU'. Forschungsfrage: 'Welche Faktoren erklaeren DevOps-Adoption?'. Methode: qualitative Interviews.",
      "expected": {"type": "regex", "value": "(Ziel|Methode|Ergebnis).*\\b(Methode|Ergebnis|Diskussion)\\b"},
      "mode": "both"
    },
    {
      "id": "ab-02",
      "input": "Erzeuge 5 Keywords fuer die vorherige Arbeit.",
      "expected": {"type": "regex", "value": "(DevOps|Governance|KMU|Adoption|Interview)"},
      "mode": "with_skill"
    },
    {
      "id": "ab-03",
      "input": "Generiere Abstract + Keywords auf Deutsch UND Englisch fuer eine Masterarbeit zu 'Zero Trust Security'. 200 Woerter pro Sprache.",
      "expected": {"type": "regex", "value": "(Zero Trust|zero trust)"},
      "mode": "both"
    }
  ]
}
```

- [ ] **Step 2: source-quality-audit-evals anlegen**

Datei `evals/source-quality-audit/evals.json`:

```json
{
  "component": "source-quality-audit",
  "component_type": "skill",
  "prompts": [
    {
      "id": "sq-01",
      "input": "Bewerte: Paper 'DevOps Governance', Journal 'IEEE Software', Autor Smith 2023. Ist das peer-reviewed?",
      "expected": {"type": "substring", "value": "peer"},
      "mode": "both"
    },
    {
      "id": "sq-02",
      "input": "Ist das Journal 'International Journal of Advanced Science' ein Predatory Journal?",
      "expected": {"type": "regex", "value": "(Predatory|verdaechtig|Beall|prestige)"},
      "mode": "with_skill"
    },
    {
      "id": "sq-03",
      "input": "Welchen Impact Factor hat IEEE Software?",
      "expected": {"type": "regex", "value": "(Impact|Quartil|JCR)"},
      "mode": "with_skill"
    }
  ]
}
```

- [ ] **Step 3: Test-Dateien schreiben**

Datei `tests/evals/test_abstract_generator_evals.py`:

```python
"""Evals fuer abstract-generator-Skill."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_eval_file,
    load_skill_content,
)

try:
    EVALS = load_eval_file("abstract-generator", "evals.json")
except Exception:
    EVALS = {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_abstract_generator_eval(prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip()
    system = load_skill_content("abstract-generator") if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

Datei `tests/evals/test_source_quality_audit_evals.py` analog (Skill `source-quality-audit`).

- [ ] **Step 4: Rest-Evals minimal stub**

Datei `tests/evals/test_rest_evals.py`:

```python
"""Evals fuer die restlichen 8 Skills + 2 Agents (minimale Baseline)."""
import pytest

from tests.evals.eval_runner import (
    call_claude,
    check_expected,
    load_eval_file,
    load_skill_content,
    load_agent_content,
)

REST_SKILLS = [
    "academic-context",
    "research-question-refiner",
    "advisor",
    "methodology-advisor",
    "literature-gap-analysis",
    "style-evaluator",
    "plagiarism-check",
    "title-generator",
    "submission-checker",
]
REST_AGENTS = ["query-generator"]  # relevance-scorer hat eigene Cache-Tests; quote-extractor hat eigene Evals.


def _collect_prompts():
    items = []
    for c in REST_SKILLS + REST_AGENTS:
        try:
            evals = load_eval_file(c, "evals.json")
        except Exception:
            continue
        for p in evals.get("prompts", []):
            items.append((c, p))
    return items


PROMPTS = _collect_prompts()


@pytest.mark.parametrize("component,prompt", PROMPTS, ids=lambda v: f"{v[0]}-{v[1]['id']}" if isinstance(v, tuple) else str(v))
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_rest_eval(component, prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip()
    if component in REST_SKILLS:
        system = load_skill_content(component) if mode == "with_skill" else ""
    else:
        system = load_agent_content(component) if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{component}/{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
```

- [ ] **Step 5: Je 2 Beispielprompts fuer jeden Rest-Skill/-Agent anlegen**

Pro Komponente eine `evals/<component>/evals.json` mit 2 minimalen Prompts (ID-Praefix, Input, Expected). Template:

```json
{
  "component": "<component>",
  "component_type": "skill",
  "prompts": [
    {"id": "<prefix>-01", "input": "<konkreter Prompt 1>", "expected": {"type": "substring", "value": "<keyword>"}, "mode": "both"},
    {"id": "<prefix>-02", "input": "<konkreter Prompt 2>", "expected": {"type": "regex", "value": "<regex>"}, "mode": "with_skill"}
  ]
}
```

Beispiele fuer die Komponenten (ID-Praefix in Klammern):

- `academic-context` (ac): "Setze meinen Context auf FH Leibniz BWL Bachelor" → substring `Leibniz`; "Aktualisiere Abgabe auf 2026-06-30" → regex `2026-06-30`
- `research-question-refiner` (rq): "Forschungsfrage 'Wie beeinflusst KI die Gesellschaft' — bewerte" → substring `zu breit`; "Praezisiere 'DevOps in KMU'" → substring `KMU`
- `advisor` (ad): "Gliederung: 1 Einleitung, 2 Grundlagen, 3 Fazit — bewerte" → substring `Methodik` (fehlt); "Forschungsfrage '...' — decke sie die Kapitel ab?" → substring `Kapitel`
- `methodology-advisor` (mt): "Thema DevOps-Adoption, Zeitrahmen 3 Monate — welche Methode?" → regex `(Fallstudie|Umfrage|Literatur-Review)`; "qualitative vs quantitative fuer Zero Trust" → substring `qualitativ`
- `literature-gap-analysis` (lg): "Kapitel 3.2 hat 0 Quellen — Report?" → substring `KRITISCH`; "Coverage 60%, Recency 20% ab 2020 — Empfehlung?" → substring `Empfehl`
- `style-evaluator` (se): "Text: 'Es wird durchgefuehrt und es wird analysiert.' — Passiv-Quote?" → substring `Passiv`; "Satz-Median fuer 'Kurz. Auch kurz. Sehr kurz.'" → regex `Median|abgehackt`
- `plagiarism-check` (pc): "Text X vs Quelle Y — N-Gramm-Overlap?" → substring `Overlap`; "Ist dieser Satz aus Quelle A?" → regex `(quellennah|paraphras)`
- `title-generator` (tg): "Thema DevOps Governance KMU — 3 Titel" → regex `(Titel|DevOps)`; "Titel mit Untertitel bitte" → substring `:`
- `submission-checker` (sc): "FH Leibniz, 2,5 cm Raender, Times 12pt, Zeilenabstand 1,5 — OK?" → substring `PASS`; "Fehlt Ehrenwoertliche Erklaerung — FAIL?" → substring `Erklaerung`
- `query-generator` (qg): "Thema DevOps Governance — 3 Suchqueries" → regex `(DevOps|Governance|compliance)`; "Engere Query zu Zero Trust Healthcare" → substring `Zero Trust`

- [ ] **Step 6: Alle Evals laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/ -v`
Expected: Mehrheit PASS, einzelne FAIL notieren.

- [ ] **Step 7: Commit**

```bash
git add evals/ tests/evals/
git commit -m "$(cat <<'EOF'
feat(evals): baseline evals for all skills and agents

- Adds evals.json for remaining 10 components (8 skills + 2 agents) with 2 prompts each.
- Adds test_abstract_generator_evals.py, test_source_quality_audit_evals.py,
  test_rest_evals.py (parametrized over rest).

Baseline numbers go into docs/evals/ in the release commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 19: Eval-Reports in `docs/evals/`

**Files:**
- Create: `docs/evals/2026-04-23-<component>.md` pro Komponente (optional, zusammenfassend)
- Create: `docs/evals/2026-04-23-summary.md`

- [ ] **Step 1: Evals ein letztes Mal laufen lassen**

Run: `ANTHROPIC_API_KEY=sk-ant-... pytest tests/evals/ -v > docs/evals/raw-output.txt`

- [ ] **Step 2: Summary-Report schreiben**

Datei `docs/evals/2026-04-23-summary.md`:

```markdown
# Evals-Summary v5.2.0

**Datum:** 2026-04-23
**Runner:** `pytest tests/evals/ -v`
**Modell:** `claude-sonnet-4-6`

## Quality-Evals (Baseline-Gap)

| Komponente | with_skill PASS | without_skill PASS | Delta (pp) | Schwelle | Status |
|------------|-----------------|--------------------|-----------:|---------:|--------|
| quote-extractor | X/5 | Y/5 | Δ | 20 | ✅/⚠️ |
| citation-extraction | X/5 | Y/5 | Δ | 20 | ✅/⚠️ |
| chapter-writer | X/5 | Y/5 | Δ | 20 | ✅/⚠️ |
| abstract-generator | X/3 | Y/3 | Δ | 20 | ✅/⚠️ |
| source-quality-audit | X/3 | Y/3 | Δ | 20 | ✅/⚠️ |
| … (Rest) | | | | 20 | |

## Trigger-Evals

| Skill | Recall should_trigger | FPR should_not_trigger | Status |
|-------|-----------------------|------------------------|--------|
| research-question-refiner | X/10 | Y/10 | ✅/⚠️ |
| academic-context | X/10 | Y/10 | ✅/⚠️ |
| … (13 Skills gesamt) | | | |

## Prompt-Caching

- `relevance-scorer` Batch-Test: `cache_read_input_tokens = <N>` nach 2. Call → bestaetigt.
- `quote-extractor` Batch-Test: analog.

## Beobachtungen / Next Actions

- Skills, die die Schwelle reissen: <Liste mit Empfehlungen>
- Raw pytest output: `raw-output.txt`
```

- [ ] **Step 3: Raw-Output committen**

```bash
git add docs/evals/
git commit -m "docs(evals): v5.2.0 baseline summary report"
```

---

### Task 20: Version-Bumps + CHANGELOG + README

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: plugin.json Version bumpen**

In `.claude-plugin/plugin.json` das Feld `"version"` von `"5.1.1"` auf `"5.2.0"` aendern.

- [ ] **Step 2: marketplace.json Version bumpen**

In `.claude-plugin/marketplace.json` im Eintrag fuer academic-research die Version auf `"5.2.0"` setzen.

- [ ] **Step 3: CHANGELOG-Block schreiben**

In `CHANGELOG.md` direkt unter dem `# Changelog`-Header plus Praeambel-Block einfuegen (vor `## [5.1.1]`):

```markdown
## [5.2.0] — 2026-04-23

### Added

- **Native Citations-API** in `quote-extractor`, `citation-extraction`, `chapter-writer` (Block A). Ersetzt Heuristik-Pre-Execution-Guards. Zitate sind jetzt seitengenau (`page_location`) und von der API erzwungen quellengebunden.
- **Evals-Suite** pro Skill/Agent via pytest (`tests/evals/`). `evals/<component>/evals.json` liefert Test-Prompts mit `substring` / `regex` / `json_field` Expectations. Baseline-Vergleich `with_skill` vs `without_skill`. Schwelle: Δ ≥ 20 pp PASS-Rate. Reports unter `docs/evals/`.
- **Trigger-Evals** pro Skill (Block C) — 10 should_trigger + 10 should_not_trigger Prompts je Skill. Runner in `tests/evals/test_triggers.py` mit Schwellen Recall ≥ 85 % / FPR ≤ 10 %.
- **`quality-reviewer`-Agent** (`agents/quality-reviewer.md`, Sonnet-Modell). Evaluator-Optimizer-Pattern: Input = Text + Kriterien-Checkliste, Output = `PASS | REVISE` + Fix-Liste. Wird von `chapter-writer`, `abstract-generator`, `advisor` vor finalem Output aufgerufen.
- **Domain-organized References** (Block E) in 3 Skills: `citation-extraction/references/{apa,harvard,chicago,din1505}.md`, `style-evaluator/references/{academic-de,academic-en}.md`, `submission-checker/references/{fh-leibniz,uni-general,journal-ieee,journal-acm}.md`. SKILL.md laedt nur die Kontext-passende Variante.
- **Prompt-Caching** in `relevance-scorer` und `quote-extractor` (Block F). Cache-Breakpoint auf System-Prompt + Scoring-Rubrik/Extraktions-Instruktionen. `cache_read_input_tokens > 0` ab 2. Batch-Call.

### Changed

- **Alle 13 Skill-Descriptions** auf Pushy-Stil umformuliert (Block C): imperativer Einstieg `Use this skill when …`, 3–4 konkrete Trigger-Beispiele mit Umlaut-Paaren, Delegations-Satz an Nachbar-Skill. Kein ALLCAPS.
- `skills/submission-checker/SKILL.md`: bestehende 8-Punkte-FH-Leibniz-Formalia nach `references/fh-leibniz.md` verschoben. SKILL.md enthaelt jetzt nur Workflow + Variant-Selector.

### Dependencies

- `scripts/requirements.txt`: `anthropic>=0.40` ergaenzt (fuer Citations-API und Prompt-Caching).

### Migration

**Fuer End-User:** Keine Action noetig. Neue Features aktivieren sich automatisch nach Plugin-Update.

**Fuer Eval-Nutzer:**
1. `pip install anthropic>=0.40` (oder `rm -rf ~/.academic-research/venv && /academic-research:setup`)
2. `export ANTHROPIC_API_KEY=sk-ant-...`
3. `pytest tests/evals/` — laeuft lokal, kein CI-Trigger.
```

- [ ] **Step 4: README Evals-Abschnitt ergaenzen**

In `README.md` nach dem bestehenden Testing-Abschnitt (oder vor "Contributing") einfuegen:

```markdown
## Evals

Pro Skill und Agent gibt es eine Evals-Suite unter `tests/evals/` mit zugehoerigen JSON-Daten in `evals/<component>/`.

**Lokaler Lauf:**

```
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/evals/ -v
```

**Quality-Evals** vergleichen `with_skill` vs `without_skill` und erwarten ≥ 20 Prozentpunkte PASS-Rate-Delta (sonst rechtfertigt das Skill seine Existenz nicht).

**Trigger-Evals** pruefen Undertriggering (Recall ≥ 85 %) und Overtriggering (FPR ≤ 10 %) mit 20 Prompts pro Skill.

**Kein CI-Trigger** — Evals laufen lokal vor jedem Release, Reports werden manuell unter `docs/evals/` committet (API-Kosten vermeiden).
```

- [ ] **Step 5: Smoke-Test weiter gruen**

Run: `pytest tests/test_skills_manifest.py -v`
Expected: 51/51 PASS.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md README.md
git commit -m "chore(release): v5.2.0"
```

---

### Task 21: PR erstellen

**Files:**
- None (nur Git-Operationen)

- [ ] **Step 1: Branch pushen**

```bash
git push -u origin refactor/e4-cookbook
```

- [ ] **Step 2: PR erstellen**

```bash
gh pr create --base main --head refactor/e4-cookbook --title "refactor: E4 Cookbook Adoption (v5.2.0)" --body "$(cat <<'EOF'
## Summary

- Implementiert die 6 Bloecke (A-F) aus der E4-Cookbook-Spec als gebuendelten Minor v5.2.0
- 3 Agents + 13 Skills betroffen + 1 neuer Agent (quality-reviewer)
- Neue Evals-Infrastruktur (pytest-basiert, lokal-only)

## Bloecke

- **A Citations-API**: quote-extractor, citation-extraction, chapter-writer
- **B Evals-Suite**: `tests/evals/` + `evals/<component>/evals.json`
- **C Pushy Descriptions**: alle 13 Skill-Descriptions + `trigger_evals.json`
- **D Quality-Reviewer**: neuer Agent, integriert in chapter-writer/abstract-generator/advisor
- **E Domain-References**: 10 Varianten-Dateien in 3 Skills
- **F Prompt-Caching**: relevance-scorer + quote-extractor

## Spec

[`docs/superpowers/specs/2026-04-23-academic-research-e4-cookbook-design.md`](../blob/main/docs/superpowers/specs/2026-04-23-academic-research-e4-cookbook-design.md)

## Test plan

- [x] Smoke-Test tests/test_skills_manifest.py 51/51 gruen
- [x] Evals lokal mit ANTHROPIC_API_KEY=... gelaufen
- [x] Quality-Evals Baseline-Gap >= 20 pp fuer priorisierte Komponenten
- [x] Trigger-Evals Recall >= 85 %, FPR <= 10 %
- [x] Prompt-Caching: cache_read_input_tokens > 0 nach 2. Batch-Call
- [x] CHANGELOG [5.2.0] geschrieben
- [x] Version-Bumps in plugin.json + marketplace.json
- [x] docs/evals/2026-04-23-summary.md generiert

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Nach Review mergen**

```bash
gh pr merge <PR-Nr> --squash --delete-branch
```

- [ ] **Step 4: Tag setzen**

```bash
git checkout main
git pull --ff-only
git tag -a v5.2.0 -m "Release v5.2.0 — E4 Cookbook Adoption"
git push origin v5.2.0
```

---

## Zusammenfassung

**21 Tasks** in **7 Phasen** implementieren die E4-Cookbook-Adoption als gebuendelten v5.2.0-Release.

**Phase-Abhaengigkeit:**
- Phase 1 (Evals-Infrastruktur) ist Voraussetzung fuer Phase 2, 3, 4, 7 (alles was testbar sein soll).
- Phasen 2, 4, 5, 6 sind untereinander unabhaengig — koennen parallel von Subagenten bearbeitet werden.
- Phase 3 (Pushy + Trigger-Evals) braucht Phase 1 (Trigger-Runner).
- Phase 7 (Release) erfordert alle vorangegangenen Phasen.

**Subagent-Driven-Empfehlung:** Phase 1 sequentiell (Infrastruktur), dann Phasen 2/4/5/6 parallel je 1 Subagent, Phase 3 sequentiell nach Phase 1, Phase 7 abschliessend.

**Kritische Checkpoints:**
- Nach Phase 1: Runner-Smoke muss gruen laufen.
- Nach Phase 2: Quality-Evals der 3 Citations-Komponenten zeigen Baseline-Gap.
- Nach Phase 3: Trigger-Evals zeigen Recall ≥ 85 %.
- Nach Phase 7: `pytest tests/` laeuft komplett gruen.
