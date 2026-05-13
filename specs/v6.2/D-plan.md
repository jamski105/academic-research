# OA-Site-Subagenten (Chunk D) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vier OA-Site-Subagenten (`tib-fetcher`, `oapen-fetcher`, `doabooks-fetcher`, `kvk-fetcher`) als Markdown-Agent-Dateien implementieren, die per `browser-use` ohne direkten HTTP-Aufruf OA-Bücher fetchen und ein einheitliches Output-Schema liefern.

**Architecture:** Jeder Agent ist eine eigenständige `agents/<name>.md`-Datei mit YAML-Frontmatter (name, model, tools, maxTurns) und Markdown-System-Prompt. Tests validieren Frontmatter-Struktur, Output-Schema-Konformität und Verbots-Einhaltung via Python/pytest ohne Browser-Ausführung. Eval-Cases liegen als `evals/oa-fetchers/evals.json` vor.

**Tech Stack:** Python 3 / pytest (Tests), YAML-Frontmatter in Markdown (Agenten), JSON (Evals, Schema-Validierung)

---

## Datei-Übersicht

| Datei | Typ | Verantwortung |
|---|---|---|
| `agents/tib-fetcher.md` | NEU | TIB-Subagent: Suche + OA-Filter + Download |
| `agents/oapen-fetcher.md` | NEU | OAPEN-Subagent: reine OA-Plattform |
| `agents/doabooks-fetcher.md` | NEU | DOAB-Subagent: Aggregator → externer Volltext |
| `agents/kvk-fetcher.md` | NEU | KVK-Subagent: Meta-Katalog + Standort-Info |
| `tests/test_oa_fetchers.py` | NEU | Frontmatter + Schema + Verbots-Tests |
| `evals/oa-fetchers/evals.json` | NEU | 4 Eval-Cases (je 1 OA-Buch pro Platform) |

---

### Task 1: Failing Tests schreiben (TDD-RED)

**Files:**
- Create: `tests/test_oa_fetchers.py`

- [ ] **Schritt 1: Testdatei erstellen mit allen failing Tests**

```python
# tests/test_oa_fetchers.py
"""Frontmatter-Validierung, Output-Schema-Check und Verbots-Pruefung fuer OA-Fetcher-Subagenten."""
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
EVALS_PATH = REPO_ROOT / "evals" / "oa-fetchers" / "evals.json"

AGENT_NAMES = ["tib-fetcher", "oapen-fetcher", "doabooks-fetcher", "kvk-fetcher"]
VALID_STATUSES = {"success", "pickup_required", "captcha", "no_match", "metadata_only"}


# ─── Hilfsfunktion ───────────────────────────────────────────────────────────

def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parst YAML-Frontmatter aus einer Markdown-Datei ohne pyyaml-Abhaengigkeit.
    Gibt (frontmatter_dict, body) zurueck.
    """
    content = path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    assert fm_match is not None, f"Kein Frontmatter in {path.name}"
    fm_raw = fm_match.group(1)
    body = fm_match.group(2)
    # Minimaler YAML-Parser: nur Key: Value (kein nested, kein list-block)
    fm = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


# ─── Klasse 1: Frontmatter-Validierung ───────────────────────────────────────

class TestAgentFrontmatter:
    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_agent_file_exists(self, agent_name):
        """Jede Agent-Datei muss unter agents/<name>.md existieren."""
        path = AGENTS_DIR / f"{agent_name}.md"
        assert path.exists(), f"Agent-Datei fehlt: {path}"

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_frontmatter_has_name_field(self, agent_name):
        """name-Feld muss dem Dateinamen entsprechen."""
        path = AGENTS_DIR / f"{agent_name}.md"
        fm, _ = parse_frontmatter(path)
        assert "name" in fm, f"Kein 'name'-Feld in {agent_name}.md"
        assert fm["name"] == agent_name, (
            f"name='{fm['name']}' stimmt nicht mit Dateinamen '{agent_name}' ueberein"
        )

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_frontmatter_model_is_sonnet(self, agent_name):
        """model muss 'sonnet' sein."""
        path = AGENTS_DIR / f"{agent_name}.md"
        fm, _ = parse_frontmatter(path)
        assert "model" in fm, f"Kein 'model'-Feld in {agent_name}.md"
        assert fm["model"] == "sonnet", f"model='{fm['model']}' in {agent_name}.md — erwartet 'sonnet'"

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_frontmatter_has_max_turns(self, agent_name):
        """maxTurns muss gesetzt und eine positive Zahl sein."""
        path = AGENTS_DIR / f"{agent_name}.md"
        fm, _ = parse_frontmatter(path)
        assert "maxTurns" in fm, f"Kein 'maxTurns'-Feld in {agent_name}.md"
        assert fm["maxTurns"].isdigit(), f"maxTurns='{fm['maxTurns']}' ist keine Zahl in {agent_name}.md"
        assert int(fm["maxTurns"]) > 0, f"maxTurns muss > 0 sein in {agent_name}.md"

    def test_tib_fetcher_max_turns_is_15(self):
        """tib-fetcher muss maxTurns: 15 haben (laut Ticket-Spec)."""
        path = AGENTS_DIR / "tib-fetcher.md"
        fm, _ = parse_frontmatter(path)
        assert fm.get("maxTurns") == "15", (
            f"tib-fetcher maxTurns='{fm.get('maxTurns')}' — erwartet 15 (Ticket-Spec)"
        )

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_frontmatter_tools_contains_browser_use(self, agent_name):
        """tools-Zeile muss 'browser-use' enthalten."""
        path = AGENTS_DIR / f"{agent_name}.md"
        content = path.read_text(encoding="utf-8")
        # tools kann als YAML-Inline-Liste oder Multiline-Block vorliegen
        # Einfachster Check: 'browser-use' irgendwo im Frontmatter
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, f"Kein Frontmatter in {agent_name}.md"
        fm_raw = fm_match.group(1)
        assert "browser-use" in fm_raw, (
            f"'browser-use' fehlt im tools-Frontmatter von {agent_name}.md"
        )

    @pytest.mark.parametrize("agent_name, expected_guide", [
        ("tib-fetcher", "config/browser_guides/tib.md"),
        ("oapen-fetcher", "config/browser_guides/oapen.md"),
        ("doabooks-fetcher", "config/browser_guides/doab.md"),
        ("kvk-fetcher", "config/browser_guides/kvk.md"),
    ])
    def test_body_references_browser_guide(self, agent_name, expected_guide):
        """Agent-Body muss den kanonischen Browser-Guide-Pfad referenzieren."""
        path = AGENTS_DIR / f"{agent_name}.md"
        _, body = parse_frontmatter(path)
        assert expected_guide in body, (
            f"Browser-Guide-Referenz '{expected_guide}' fehlt im Body von {agent_name}.md"
        )


# ─── Klasse 2: Output-Schema-Validierung ─────────────────────────────────────

class TestOutputSchema:
    """Prueft, dass das gesperrte Output-Schema (5 Status-Werte) korrekt definiert ist."""

    def _validate_output(self, obj: dict, context: str = ""):
        """Gemeinsame Schema-Validierung fuer alle Status-Werte."""
        assert "status" in obj, f"{context}: 'status'-Feld fehlt"
        assert obj["status"] in VALID_STATUSES, (
            f"{context}: status='{obj['status']}' ist kein gueltiger Wert. "
            f"Erlaubt: {VALID_STATUSES}"
        )
        assert "source_subagent" in obj, f"{context}: 'source_subagent'-Feld fehlt"
        assert obj["source_subagent"] in AGENT_NAMES, (
            f"{context}: source_subagent='{obj['source_subagent']}' nicht in AGENT_NAMES"
        )

    def test_success_output_has_pdf_path(self):
        """success-Output muss pdf_path enthalten."""
        output = {
            "status": "success",
            "source_subagent": "tib-fetcher",
            "pdf_path": "/tmp/book.pdf",
        }
        self._validate_output(output, "success")
        assert "pdf_path" in output, "success-Output braucht pdf_path"
        assert output["pdf_path"], "pdf_path darf nicht leer sein"

    def test_metadata_only_output_has_url(self):
        """metadata_only-Output muss url enthalten."""
        output = {
            "status": "metadata_only",
            "source_subagent": "oapen-fetcher",
            "url": "https://library.oapen.org/handle/12345",
        }
        self._validate_output(output, "metadata_only")
        assert "url" in output, "metadata_only-Output braucht url"

    def test_pickup_required_output(self):
        """pickup_required-Output ist gueltiger Status."""
        output = {
            "status": "pickup_required",
            "source_subagent": "kvk-fetcher",
            "url": "https://kvk.bibliothek.kit.edu/...",
            "reason": "Standorte: BSB Muenchen, UB Berlin",
        }
        self._validate_output(output, "pickup_required")

    def test_captcha_output(self):
        """captcha-Output ist gueltiger Status."""
        output = {
            "status": "captcha",
            "source_subagent": "tib-fetcher",
            "reason": "CAPTCHA auf Detailseite erkannt",
        }
        self._validate_output(output, "captcha")

    def test_no_match_output(self):
        """no_match-Output ist gueltiger Status."""
        output = {
            "status": "no_match",
            "source_subagent": "doabooks-fetcher",
            "reason": "0 Treffer fuer ISBN 000-0-0000-0000-0",
        }
        self._validate_output(output, "no_match")

    def test_invalid_status_rejected(self):
        """Ungueltige Status-Werte sollen erkannt werden."""
        invalid = {
            "status": "unknown_status",
            "source_subagent": "tib-fetcher",
        }
        assert invalid["status"] not in VALID_STATUSES, (
            "unknown_status muss als ungueltig erkannt werden"
        )

    def test_all_five_statuses_are_defined(self):
        """Alle 5 gesperrten Status-Werte muessen in VALID_STATUSES enthalten sein."""
        expected = {"success", "pickup_required", "captcha", "no_match", "metadata_only"}
        assert VALID_STATUSES == expected, (
            f"VALID_STATUSES stimmt nicht: {VALID_STATUSES} vs {expected}"
        )


# ─── Klasse 3: Verbots-Check ─────────────────────────────────────────────────

class TestForbiddenPatterns:
    """Prueft, dass verbotene Muster (curl, wget, direkte HTTP-Calls) nicht in Agenten vorkommen."""

    FORBIDDEN_PATTERNS = [
        r"\bcurl\b",
        r"\bwget\b",
        r"requests\.get\b",
        r"requests\.post\b",
        r"urllib\.request\b",
        r"http\.get\b",
        r"fetch\((?!.*browser-use)",  # fetch() ohne browser-use Kontext
    ]

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_no_curl_in_agent(self, agent_name):
        """Agent darf kein 'curl' als Shell-Command enthalten."""
        path = AGENTS_DIR / f"{agent_name}.md"
        content = path.read_text(encoding="utf-8")
        # Suche nach curl als standalone-Befehl (nicht als Teil von 'browser-use ...')
        # Erlaubt: Erwaehnung als Verbot ("kein curl")
        matches = re.findall(r"(?<!kein )(?<!no )\bcurl\b(?! verboten)(?! ist verboten)", content, re.IGNORECASE)
        # Filtere Verbots-Hinweise heraus
        actual_forbidden = [m for m in matches if "verboten" not in m.lower() and "kein" not in m.lower()]
        # Vereinfachter Check: curl darf nur in Verbots-Kontext vorkommen
        curl_uses = re.findall(r"^\s*`?curl\b", content, re.MULTILINE)
        assert len(curl_uses) == 0, f"curl-Aufruf in {agent_name}.md gefunden: {curl_uses}"

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_no_wget_in_agent(self, agent_name):
        """Agent darf kein 'wget' als Shell-Command enthalten."""
        path = AGENTS_DIR / f"{agent_name}.md"
        content = path.read_text(encoding="utf-8")
        wget_uses = re.findall(r"^\s*`?wget\b", content, re.MULTILINE)
        assert len(wget_uses) == 0, f"wget-Aufruf in {agent_name}.md gefunden: {wget_uses}"

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_browser_use_mentioned_in_body(self, agent_name):
        """Agent-Body muss 'browser-use' als Werkzeug referenzieren."""
        path = AGENTS_DIR / f"{agent_name}.md"
        _, body = parse_frontmatter(path)
        assert "browser-use" in body, (
            f"'browser-use' nicht im Body von {agent_name}.md — Agent muss browser-use verwenden"
        )

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_forbidden_section_present(self, agent_name):
        """Agent-Body sollte einen 'Verbote'- oder 'Forbidden'-Abschnitt haben."""
        path = AGENTS_DIR / f"{agent_name}.md"
        _, body = parse_frontmatter(path)
        has_verbote = bool(re.search(r"##\s*(Verbote|Forbidden|Einschraenkungen)", body, re.IGNORECASE))
        assert has_verbote, (
            f"Kein 'Verbote'-Abschnitt in {agent_name}.md — Verbote muessen explizit dokumentiert sein"
        )


# ─── Klasse 4: Eval-Cases ────────────────────────────────────────────────────

class TestEvalCases:
    def test_evals_file_exists(self):
        """evals/oa-fetchers/evals.json muss existieren."""
        assert EVALS_PATH.exists(), f"Eval-Datei fehlt: {EVALS_PATH}"

    def test_evals_is_valid_json(self):
        """evals.json muss valides JSON sein."""
        data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, list), "evals.json muss ein JSON-Array sein"

    def test_evals_has_four_cases(self):
        """evals.json muss genau 4 Cases haben (je 1 pro Platform)."""
        data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        assert len(data) == 4, f"Erwartet 4 Eval-Cases, gefunden: {len(data)}"

    def test_eval_ids_are_correct(self):
        """Eval-IDs muessen oa-01 bis oa-04 sein."""
        data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        ids = [c["id"] for c in data]
        assert ids == ["oa-01", "oa-02", "oa-03", "oa-04"], (
            f"Falsche IDs: {ids}"
        )

    def test_each_eval_has_required_fields(self):
        """Jeder Eval-Case muss id, description, agent und expected enthalten."""
        data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        for case in data:
            assert "id" in case, f"id fehlt in Case: {case}"
            assert "description" in case, f"description fehlt in Case {case['id']}"
            assert "agent" in case, f"agent fehlt in Case {case['id']}"
            assert "expected" in case, f"expected fehlt in Case {case['id']}"
            assert case["agent"] in AGENT_NAMES, (
                f"agent='{case['agent']}' in Case {case['id']} nicht in AGENT_NAMES"
            )

    def test_one_eval_per_agent(self):
        """Jeder der 4 Agenten muss genau einen Eval-Case haben."""
        data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
        agents_in_evals = [c["agent"] for c in data]
        assert set(agents_in_evals) == set(AGENT_NAMES), (
            f"Nicht alle Agenten haben einen Eval-Case. "
            f"Vorhanden: {set(agents_in_evals)}, erwartet: {set(AGENT_NAMES)}"
        )
```

- [ ] **Schritt 2: Tests ausfuehren — alle muessen FAILED sein (RED-Phase)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-D
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -v 2>&1 | head -60
```

Erwartet: Alle Tests FAILED (Agent-Dateien fehlen noch).

---

### Task 2: tib-fetcher Agent implementieren

**Files:**
- Create: `agents/tib-fetcher.md`

- [ ] **Schritt 1: tib-fetcher.md erstellen**

```markdown
---
name: tib-fetcher
model: sonnet
description: |
  Holt OA-Buecher von tib.eu (TIB-Portal Hannover) per browser-use.
  Aufrufen mit ISBN, DOI oder Titel. Liefert lokalen PDF-Pfad oder
  strukturierten metadata_only-Status zurueck.
tools:
  - Bash(browser-use:*)
  - Read
  - Write
maxTurns: 15
browser-guide: config/browser_guides/tib.md
---

# tib-fetcher

Du bedienst tib.eu wie ein Mensch. Nur browser-use — kein curl, kein wget.

**Lies zuerst:** `config/browser_guides/tib.md`

## Eingabe

Du erhaeltst einen der folgenden Eingabe-Typen:
- `isbn: <ISBN-10 oder ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Standard-Flow

1. `browser-use open https://www.tib.eu/de/suchen?query=<URL-encoded-query>`
   (query = ISBN, DOI oder Titel, URL-encoded)
2. `browser-use state` → Treffer-Liste lesen
3. Plausibelsten Treffer waehlen: Titel + Autor + Jahr matcht Input
   - Bei 0 Treffern: `{"status": "no_match", "source_subagent": "tib-fetcher", "reason": "0 Treffer fuer <query>"}`
4. `browser-use click <idx>` auf Treffer-Titel → Detailseite
5. `browser-use state` → Detailseite pruefen:
   - "Open Access"-Badge sichtbar? → OA-Indiz vorhanden
   - "Volltext"-Block sichtbar? → Download moeglich
   - Kein OA-Indiz → `{"status": "metadata_only", "source_subagent": "tib-fetcher", "url": "<detailseite-url>"}`
6. Volltext-Link anklicken: `browser-use click <volltext-idx>`
7. Auf PDF-Download-Seite: `browser-use download <pdf-link-idx> --to <output_path>`
8. Validation:
   - Datei lesen: erste 4 Bytes muessen `%PDF` sein (Read tool)
   - Dateigröße > 10 KB pruefen (Write/Read)
   - Bei ungueltigem PDF: erneut versuchen oder `metadata_only` zurueckgeben

## OA-Filter-Logik

Ein Treffer ist OA-tauglich, wenn auf der Detailseite MINDESTENS EINES gilt:
- "Open Access"-Badge sichtbar
- "Volltext"-Block mit Download-Button vorhanden
- DOI-Link zeigt auf OAPEN, Zenodo oder aehnliche OA-Repositorien

Ohne OA-Indiz: NICHT versuchen herunterzuladen → sofort `metadata_only`.

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "tib-fetcher",
  "pdf_path": "<absoluter-pfad-zu-pdf>",
  "url": "<detailseite-url>"
}
```

Kein Volltext:
```json
{
  "status": "metadata_only",
  "source_subagent": "tib-fetcher",
  "url": "<detailseite-url>"
}
```

Kein Treffer:
```json
{
  "status": "no_match",
  "source_subagent": "tib-fetcher",
  "reason": "0 Treffer fuer <query>"
}
```

CAPTCHA erkannt:
```json
{
  "status": "captcha",
  "source_subagent": "tib-fetcher",
  "reason": "CAPTCHA auf Seite erkannt — Screenshot erstellt"
}
```

## Verbote

- Kein `curl`, kein `wget`, kein `requests.get`, keine direkten HTTP-Calls
- Keine API-Endpoints erraten oder direkt aufrufen
- Keine fingierten Treffer — wenn Suche leer ist, `no_match` zurueckgeben
- Kein Login-Versuch ohne explizit konfigurierte Credentials
- Keine Weiterleitungen zu anderen Sites ohne Pruefung (wenn Redirect zu Verlagsseite: `metadata_only`)

## Fallstricke (aus config/browser_guides/tib.md)

- TIB-Bestand vs. externe Verlinkung: ein Treffer bedeutet nicht, dass TIB den Volltext hostet
- Rate-Limiting bei >10 Downloads/Minute → 2-3 Sekunden Pause
- DOI-Resolver kann auf Verlags-Landing-Page statt Direktdownload weiterleiten
- Einige Titel nur als Print-Exemplar → `metadata_only` (kein `pickup_required` — das entscheidet der Master)
```

- [ ] **Schritt 2: Relevante Tests ausfuehren**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py::TestAgentFrontmatter::test_agent_file_exists[tib-fetcher] tests/test_oa_fetchers.py::TestAgentFrontmatter::test_frontmatter_model_is_sonnet[tib-fetcher] tests/test_oa_fetchers.py::TestAgentFrontmatter::test_tib_fetcher_max_turns_is_15 -v
```

Erwartet: 3 PASSED

- [ ] **Schritt 3: Alle tib-fetcher-Tests pruefen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -k "tib" -v
```

Erwartet: alle tib-bezogenen Tests PASSED

---

### Task 3: oapen-fetcher Agent implementieren

**Files:**
- Create: `agents/oapen-fetcher.md`

- [ ] **Schritt 1: oapen-fetcher.md erstellen**

```markdown
---
name: oapen-fetcher
model: sonnet
description: |
  Holt OA-Buecher von oapen.org per browser-use. Alle Inhalte auf
  OAPEN sind Open Access — kein Auth erforderlich. Liefert lokalen
  PDF-Pfad oder metadata_only-Status zurueck.
tools:
  - Bash(browser-use:*)
  - Read
  - Write
maxTurns: 12
browser-guide: config/browser_guides/oapen.md
---

# oapen-fetcher

Du bedienst oapen.org wie ein Mensch. Nur browser-use.

**Lies zuerst:** `config/browser_guides/oapen.md`

**OA-Invariante:** oapen.org hostet ausschliesslich Open-Access-Buecher.
Jeder gefundene Treffer ist per Definition OA — kein separater OA-Filter noetig.

## Eingabe

- `isbn: <ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Standard-Flow

1. `browser-use open https://www.oapen.org`
2. Suchfeld im Header: ISBN, DOI oder Titel eingeben
3. `browser-use state` → Suchergebnisse pruefen
   - DOI-Direktlink bevorzugen: `browser-use open https://doi.org/<doi>` (falls DOI gegeben)
   - Handle-URL: `browser-use open https://library.oapen.org/handle/<handle>`
   - Bei 0 Treffern: `{"status": "no_match", "source_subagent": "oapen-fetcher", "reason": "0 Treffer auf oapen.org"}`
4. Auf Treffer klicken → Detailseite
5. `browser-use state` → "Download PDF"-Button suchen
   - Button-Index identifizieren
6. `browser-use download <pdf-btn-idx> --to <output_path>`
7. Validation: erste 4 Bytes = `%PDF`, Groesse > 10 KB

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "oapen-fetcher",
  "pdf_path": "<absoluter-pfad>",
  "url": "<detailseite-url>"
}
```

Kein Download-Link (seltener Fehlerfall):
```json
{
  "status": "metadata_only",
  "source_subagent": "oapen-fetcher",
  "url": "<detailseite-url>"
}
```

Kein Treffer:
```json
{
  "status": "no_match",
  "source_subagent": "oapen-fetcher",
  "reason": "0 Treffer fuer <query>"
}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- Keine API-Endpoints direkt aufrufen (kein direkter OAPEN-API-Call)
- Keine fingierten Treffer
- Kein Login (OAPEN benoetigt kein Auth)

## Fallstricke (aus config/browser_guides/oapen.md)

- Handle-URLs und DOI-URLs koennen auf unterschiedliche Seiten zeigen — beide versuchen
- Verwaiste Handles (Buch entfernt) geben 404 → `no_match`
- Grosse PDFs (>50 MB) koennen Timeout ausloesen — Download-Fortschritt ueberwachen
```

- [ ] **Schritt 2: oapen-fetcher-Tests pruefen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -k "oapen" -v
```

Erwartet: alle oapen-bezogenen Tests PASSED

---

### Task 4: doabooks-fetcher Agent implementieren

**Files:**
- Create: `agents/doabooks-fetcher.md`

- [ ] **Schritt 1: doabooks-fetcher.md erstellen**

```markdown
---
name: doabooks-fetcher
model: sonnet
description: |
  Holt OA-Buecher ueber directory.doabooks.org per browser-use (kein
  REST-Direktaufruf). DOAB ist ein Metadaten-Aggregator — Volltexte
  liegen auf externen Providern. Liefert PDF-Pfad oder metadata_only.
tools:
  - Bash(browser-use:*)
  - Read
  - Write
maxTurns: 12
browser-guide: config/browser_guides/doab.md
---

# doabooks-fetcher

Du bedienst directory.doabooks.org wie ein Mensch. Nur browser-use.
Kein direkter REST-API-Aufruf — auch wenn DOAB eine REST-API hat, nutzt du nur den Browser.

**Lies zuerst:** `config/browser_guides/doab.md`

**OA-Invariante:** DOAB listet ausschliesslich OA-Buecher. Jeder Treffer ist OA.
ABER: Nicht alle Eintraege haben einen direkten Download-Link — manche haben nur Metadaten.

## Eingabe

- `isbn: <ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Standard-Flow

1. `browser-use open https://www.doabooks.org`
2. Suchfeld: ISBN (bevorzugt), DOI oder Titel eingeben
3. `browser-use state` → Suchergebnisse pruefen
   - Bei 0 Treffern: `{"status": "no_match", "source_subagent": "doabooks-fetcher", "reason": "0 Treffer auf DOAB"}`
4. Auf Treffer klicken → Metadaten-Detailseite
5. `browser-use state` → Volltext-Link suchen:
   - Felder: "PDF", "Download", "Publisher URL", externer Repository-Link
   - Kein Volltext-Link vorhanden → `{"status": "metadata_only", "source_subagent": "doabooks-fetcher", "url": "<detailseite-url>"}`
6. Volltext-Link anklicken → Navigation zum externen Provider
7. Provider-spezifischer Download:
   - OAPEN-Link → Download-Button auf OAPEN-Seite klicken
   - Springer/Verlag-Link → Download-Button auf Verlagsseite
   - Unbekannter Provider → DOM nach PDF-Link durchsuchen
8. `browser-use download <pdf-link-idx> --to <output_path>`
9. Validation: erste 4 Bytes = `%PDF`, Groesse > 10 KB

## OA-Filter-Logik

DOAB-Eintraege sind per Definition OA. Volltext-Verfuegbarkeit pruefen:
- Volltext-Link vorhanden → Download versuchen → bei Erfolg: `success`
- Volltext-Link zeigt auf Paywall → `metadata_only` (nicht `pickup_required`)
- Kein Link → `metadata_only`

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "doabooks-fetcher",
  "pdf_path": "<absoluter-pfad>",
  "url": "<doab-detailseite-url>"
}
```

Kein Volltext-Link:
```json
{
  "status": "metadata_only",
  "source_subagent": "doabooks-fetcher",
  "url": "<doab-detailseite-url>"
}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- Kein direkter DOAB-REST-API-Aufruf (auch wenn `directory.doabooks.org/rest/search` existiert — NICHT verwenden)
- Keine fingierten Treffer
- Keine automatische Fernleihe oder Bestellformulare ausfuellen

## Fallstricke (aus config/browser_guides/doab.md)

- DOAB ist Aggregator, nicht Repositorium — immer Weiterleitung zum Volltext
- Manche Eintraege haben nur Metadaten ohne Volltext-Link
- Link-Rot: aeltere Eintraege koennen auf geloeschte URLs zeigen → `metadata_only`
- DOI-Direktsuche bevorzugen wenn moeglich
```

- [ ] **Schritt 2: doabooks-fetcher-Tests pruefen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -k "doabooks" -v
```

Erwartet: alle doabooks-bezogenen Tests PASSED

---

### Task 5: kvk-fetcher Agent implementieren

**Files:**
- Create: `agents/kvk-fetcher.md`

- [ ] **Schritt 1: kvk-fetcher.md erstellen**

```markdown
---
name: kvk-fetcher
model: sonnet
description: |
  Meta-Suche ueber 80+ Bibliothekskataloge via kvk.bibliothek.kit.edu
  per browser-use. Identifiziert OA/Volltext-Treffer oder gibt Standort-Info
  fuer Pickup zurueck. Kein eigener Volltext-Host.
tools:
  - Bash(browser-use:*)
  - Read
  - Write
maxTurns: 12
browser-guide: config/browser_guides/kvk.md
---

# kvk-fetcher

Du bedienst kvk.bibliothek.kit.edu wie ein Mensch. Nur browser-use.

**Lies zuerst:** `config/browser_guides/kvk.md`

**Besonderheit:** KVK ist ein Meta-Katalog fuer 80+ Bibliotheken — kein OA-Only-Dienst.
Du musst aktiv nach Volltext-Links/OA-Indikatoren filtern.

## Eingabe

- `isbn: <ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Standard-Flow

1. `browser-use open https://kvk.bibliothek.kit.edu`
2. Suchformular ausfuellen: ISBN (bevorzugt), Titel oder Autor
3. Alle Datenbanken aktiviert lassen (Standard: HEIDI, BVB, GBV, SWB)
4. "Suchen"-Button klicken
5. `browser-use state` → Ergebnisliste lesen
   - Bei 0 Treffern: `{"status": "no_match", "source_subagent": "kvk-fetcher", "reason": "0 Treffer in KVK"}`
6. Ergebnisse nach OA/Volltext filtern:
   - "Online-Ressource"-Treffer mit externem Link → OA-Kandidat
   - "Volltext"-Link oder OA-Badge in Trefferliste → Download versuchen
   - Nur physische Bestands-Eintraege → Standort-Info notieren
7. Bei Volltext-Link gefunden:
   - `browser-use click <volltext-link-idx>` → externe Seite
   - Download-Versuch: `browser-use download <pdf-idx> --to <output_path>`
   - Validation: Magic-Bytes `%PDF`, Groesse > 10 KB
   - Erfolg: `{"status": "success", "source_subagent": "kvk-fetcher", "pdf_path": "..."}`
8. Nur Bibliotheks-Nachweis (kein Volltext):
   - Standorte sammeln: Bibliotheksname, Ort, Signatur
   - `{"status": "metadata_only", "source_subagent": "kvk-fetcher", "url": "...", "reason": "Standorte: <liste>"}`

## OA-Filter-Logik

KVK zeigt physische UND digitale Bestände gemischt. Priorisierung:
1. Suche nach "Volltext"-Links oder "Online-Zugriff"-Buttons zuerst
2. "Open Access" explizit markierte Treffer bevorzugen
3. "Online-Ressource" ohne Preisangabe = OA-Kandidat
4. Nur Print-Nachweis = `metadata_only` + Standort-Info im `reason`-Feld

## Standort-Info Format

Standort-Info wird im `reason`-Feld als kompakter String zurueckgegeben.
Der Master-Agent (#80) entscheidet, ob/wie er diese in die Pickup-Liste aufnimmt.

Beispiel:
```
"Standorte: BSB Muenchen (4 Ph.pr. 123, Lesesaal), UB Berlin (Ausleihe), HU Berlin (Fernleihe)"
```

## Output-Schema

Volltext-Erfolg:
```json
{
  "status": "success",
  "source_subagent": "kvk-fetcher",
  "pdf_path": "<absoluter-pfad>",
  "url": "<volltext-url>"
}
```

Nur Bibliotheks-Nachweis:
```json
{
  "status": "metadata_only",
  "source_subagent": "kvk-fetcher",
  "url": "<kvk-ergebnis-url>",
  "reason": "Standorte: <bibliothek-1 (signatur, ausleih-typ)>, <bibliothek-2>, ..."
}
```

Kein Treffer:
```json
{
  "status": "no_match",
  "source_subagent": "kvk-fetcher",
  "reason": "0 Treffer in KVK fuer <query>"
}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- Kein automatisches Ausloesen von Fernleihe oder Bestellformularen
- Keine fingierten Treffer oder erfundene Standorte
- Kein Login in Bibliotheks-Portale (nur Metadaten, kein Bestellen)

## Fallstricke (aus config/browser_guides/kvk.md)

- KVK zeigt physische UND digitale Bestände gemischt — aktiv filtern
- Nicht jede Bibliothek hat Online-Bestellung aktiviert
- Signatur-Format variiert stark — nur als Referenz zurueckgeben, nicht parsen
- Timeout bei sehr breiten Suchen → ggf. auf GBV + BVB einschraenken
- Ladezeiten >5 Sekunden pro Teilbibliothek — Geduld
```

- [ ] **Schritt 2: kvk-fetcher-Tests pruefen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -k "kvk" -v
```

Erwartet: alle kvk-bezogenen Tests PASSED

---

### Task 6: Eval-Cases erstellen

**Files:**
- Create: `evals/oa-fetchers/evals.json`

- [ ] **Schritt 1: evals/oa-fetchers/evals.json erstellen**

```json
[
  {
    "id": "oa-01",
    "description": "TIB-Fetcher: bekanntes OA-Buch via ISBN — erwartet success mit pdf_path",
    "agent": "tib-fetcher",
    "input": {
      "isbn": "978-3-86541-416-5",
      "title": "Open Access und Wissenschaftliches Publizieren",
      "output_path": "/tmp/eval-oa-01.pdf"
    },
    "expected": {
      "status": "success",
      "source_subagent": "tib-fetcher",
      "pdf_path_non_empty": true
    },
    "fallback_acceptable": "metadata_only"
  },
  {
    "id": "oa-02",
    "description": "OAPEN-Fetcher: OA-Buch via DOI — erwartet success (OAPEN ist reine OA-Plattform)",
    "agent": "oapen-fetcher",
    "input": {
      "doi": "10.26530/oapen_1002221",
      "title": "The Transformation of Research in the South",
      "output_path": "/tmp/eval-oa-02.pdf"
    },
    "expected": {
      "status": "success",
      "source_subagent": "oapen-fetcher",
      "pdf_path_non_empty": true
    },
    "fallback_acceptable": "metadata_only"
  },
  {
    "id": "oa-03",
    "description": "DOAB-Fetcher: OA-Buch via DOAB-Eintrag — erwartet success oder begruendetes metadata_only",
    "agent": "doabooks-fetcher",
    "input": {
      "isbn": "978-3-030-68953-1",
      "title": "Open Access in der Wissenschaft",
      "output_path": "/tmp/eval-oa-03.pdf"
    },
    "expected": {
      "status_in": ["success", "metadata_only"],
      "source_subagent": "doabooks-fetcher"
    },
    "note": "DOAB ist Aggregator — metadata_only ist akzeptabel wenn kein Volltext-Link vorhanden"
  },
  {
    "id": "oa-04",
    "description": "KVK-Fetcher: Buch mit Bibliotheks-Nachweis — erwartet metadata_only + Standort-Info",
    "agent": "kvk-fetcher",
    "input": {
      "isbn": "978-3-16-148410-0",
      "title": "Einfuehrung in die Rechtswissenschaft",
      "output_path": "/tmp/eval-oa-04.pdf"
    },
    "expected": {
      "status_in": ["metadata_only", "success"],
      "source_subagent": "kvk-fetcher",
      "reason_non_empty_if_metadata_only": true
    },
    "note": "KVK liefert Standort-Info in reason-Feld bei metadata_only"
  }
]
```

- [ ] **Schritt 2: Eval-Tests pruefen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py::TestEvalCases -v
```

Erwartet: alle 5 Eval-Tests PASSED

---

### Task 7: Alle Tests gruen — Vollstaendiger Run

- [ ] **Schritt 1: Vollstaendigen Test-Run ausfuehren**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_oa_fetchers.py -v
```

Erwartet: alle Tests PASSED (0 failures).

- [ ] **Schritt 2: Bestehende Tests nicht gebrochen**

```bash
/opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -20
```

Erwartet: keine neuen Fehler (pre-existierende Fehler aus `main` sind akzeptabel).

---

### Task 8: Commit

- [ ] **Schritt 1: Status pruefen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-D && git status
```

- [ ] **Schritt 2: Dateien stagen**

```bash
git add agents/tib-fetcher.md agents/oapen-fetcher.md agents/doabooks-fetcher.md agents/kvk-fetcher.md
git add tests/test_oa_fetchers.py evals/oa-fetchers/evals.json
git add specs/v6.2/D.md specs/v6.2/D-plan.md
```

- [ ] **Schritt 3: Commit**

```bash
git commit -m "$(cat <<'EOF'
feat: v6.2 D — OA-Site-Subagenten (tib, oapen, doabooks, kvk) + Tests + Evals (#81)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Code-Review + Status-Update

- [ ] **Schritt 1: Code-Review via superpowers:requesting-code-review**

- [ ] **Schritt 2: Status in .orchestrator/status.yaml auf implementation_complete setzen**

```yaml
# In /Users/j65674/Repos/academic-research/.orchestrator/status.yaml
# Chunk D:
phase: implementation_complete
last_signal_from_l1:
  kind: implementation_complete
  ts: "<ISO-Timestamp>"
  payload:
    last_commit: "<SHA>"
    tests_passed: <N>
    tests_failed_preexisting: <M>
    files_created: 6
```
