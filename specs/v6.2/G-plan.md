# book-fetcher Master-Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `agents/book-fetcher.md` — the orchestrator agent that routes book
fetch requests through OA subagents, publisher subagents, auth-helper, and generic-fetcher
sequentially, and returns a structured output with `tries` array.

**Architecture:** The agent is a Markdown file with YAML frontmatter defining model/tools/maxTurns.
The body is the agent prompt describing input parsing, routing logic, and output schema.
Tests use `unittest.mock` to patch `agents/book_fetcher_logic.py` — a thin Python test-helper
module that parses the agent's YAML/Markdown and simulates subagent dispatch for unit testing.

**Tech Stack:** Python 3.x, pytest, `unittest.mock`, `PyYAML`, agent Markdown format (existing pattern in `agents/*.md`)

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `agents/book-fetcher.md` | CREATE | Master-Agent definition (frontmatter + prompt) |
| `tests/test_book_fetcher.py` | CREATE | pytest test suite (5 test cases) |
| `tests/fixtures/book_fetcher_mocks/doabooks_success.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/oa_metadata_only.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/springer_auth_required.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/auth_helper_authenticated.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/springer_success.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/captcha.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/generic_pickup.json` | CREATE | Mock response fixture |
| `tests/fixtures/book_fetcher_mocks/active_profile_springer.yaml` | CREATE | Mock profile fixture |
| `tests/fixtures/book_fetcher_mocks/active_profile_no_licensed.yaml` | CREATE | Mock profile fixture |
| `tests/helpers/book_fetcher_router.py` | CREATE | Python routing logic extracted for testing |

---

## Strategy for Testing Agent Markdown

Since `agents/book-fetcher.md` is a Markdown prompt (not a Python module), we cannot
import it directly. Instead:

1. Extract the routing logic into `tests/helpers/book_fetcher_router.py` — a pure Python
   module that mirrors the agent's routing algorithm.
2. `tests/test_book_fetcher.py` imports and tests `book_fetcher_router.py`.
3. The agent's YAML frontmatter is validated by checking the Markdown file directly.

This pattern is consistent with how other agents in this repo are structured — the agent
Markdown is the deployment artifact, the Python helper is the testable unit.

---

## Task 1: Mock Fixtures

**Files:**
- Create: `tests/fixtures/book_fetcher_mocks/doabooks_success.json`
- Create: `tests/fixtures/book_fetcher_mocks/oa_metadata_only.json`
- Create: `tests/fixtures/book_fetcher_mocks/springer_auth_required.json`
- Create: `tests/fixtures/book_fetcher_mocks/auth_helper_authenticated.json`
- Create: `tests/fixtures/book_fetcher_mocks/springer_success.json`
- Create: `tests/fixtures/book_fetcher_mocks/captcha.json`
- Create: `tests/fixtures/book_fetcher_mocks/generic_pickup.json`
- Create: `tests/fixtures/book_fetcher_mocks/active_profile_springer.yaml`
- Create: `tests/fixtures/book_fetcher_mocks/active_profile_no_licensed.yaml`

- [ ] **Step 1.1: Write fixture files**

`tests/fixtures/book_fetcher_mocks/doabooks_success.json`:
```json
{
  "status": "success",
  "source_subagent": "doabooks-fetcher",
  "pdf_path": "/tmp/test_book.pdf",
  "url": "https://www.doabooks.org/handle/11514/12345"
}
```

`tests/fixtures/book_fetcher_mocks/oa_metadata_only.json`:
```json
{
  "status": "metadata_only",
  "source_subagent": "doabooks-fetcher",
  "url": "https://www.doabooks.org/handle/11514/12345"
}
```

`tests/fixtures/book_fetcher_mocks/springer_auth_required.json`:
```json
{
  "status": "auth_required",
  "source_subagent": "springer-book",
  "url": "https://link.springer.com/book/10.1007/978-3-662-54347-6"
}
```

`tests/fixtures/book_fetcher_mocks/auth_helper_authenticated.json`:
```json
{
  "status": "authenticated",
  "auth_type": "Shibboleth",
  "uni": "tum",
  "session_context": "browser-use:active:tum"
}
```

`tests/fixtures/book_fetcher_mocks/springer_success.json`:
```json
{
  "status": "success",
  "source_subagent": "springer-book",
  "pdf_path": "/tmp/springer_book.pdf",
  "url": "https://link.springer.com/book/10.1007/978-3-662-54347-6"
}
```

`tests/fixtures/book_fetcher_mocks/captcha.json`:
```json
{
  "status": "captcha",
  "source_subagent": "doabooks-fetcher"
}
```

`tests/fixtures/book_fetcher_mocks/generic_pickup.json`:
```json
{
  "status": "pickup_required",
  "source_subagent": "generic-fetcher",
  "reason": "Keine OA- oder lizenzierte Quelle gefunden"
}
```

`tests/fixtures/book_fetcher_mocks/active_profile_springer.yaml`:
```yaml
uni: tum
auth_type: Shibboleth
auth_url: https://login.tum.de/idp/
licensed_sites:
  - link.springer.com
  - degruyter.com
bib_pickup_url: https://www.ub.tum.de/fernleihe
```

`tests/fixtures/book_fetcher_mocks/active_profile_no_licensed.yaml`:
```yaml
uni: test-uni
auth_type: oa-only
auth_url: ""
licensed_sites: []
bib_pickup_url: https://lib.test-uni.de/fernleihe
```

- [ ] **Step 1.2: Verify fixtures are valid JSON/YAML**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -c "
import json, yaml, pathlib
d = pathlib.Path('tests/fixtures/book_fetcher_mocks')
for f in d.glob('*.json'):
    json.loads(f.read_text())
    print(f'OK: {f.name}')
for f in d.glob('*.yaml'):
    yaml.safe_load(f.read_text())
    print(f'OK: {f.name}')
"
```

Expected: Each fixture file prints `OK: <filename>` with no errors.

- [ ] **Step 1.3: Commit fixtures**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && git add tests/fixtures/book_fetcher_mocks/ && git commit -m "test(G): add mock fixtures for book-fetcher tests"
```

---

## Task 2: Python Router Helper (RED — write tests first, then implementation)

**Files:**
- Create: `tests/helpers/__init__.py`
- Create: `tests/helpers/book_fetcher_router.py`
- Test: `tests/test_book_fetcher.py`

### Step 2.1 — Write failing tests (RED)

- [ ] **Step 2.1: Create test file with all 5 failing tests**

`tests/test_book_fetcher.py`:
```python
"""
Tests for book-fetcher Master-Agent routing logic.

Tests validate the routing algorithm in tests/helpers/book_fetcher_router.py,
which mirrors the agent prompt in agents/book-fetcher.md.
"""
import json
import pathlib
import unittest
from unittest.mock import MagicMock, patch, call
import yaml

# Path to fixtures
FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "book_fetcher_mocks"


def _load_json(name):
    return json.loads((FIXTURES / name).read_text())


def _load_yaml(name):
    return yaml.safe_load((FIXTURES / name).read_text())


# Import will fail until Task 3 creates the module — that's expected (RED)
from tests.helpers.book_fetcher_router import BookFetcherRouter


class TestBookFetcherInputParsing(unittest.TestCase):
    """Test that ISBN, DOI, URL, and free-text inputs are correctly classified."""

    def setUp(self):
        profile = _load_yaml("active_profile_springer.yaml")
        self.router = BookFetcherRouter(profile=profile)

    def test_isbn_13_detected(self):
        t, v = self.router.parse_input("isbn: 978-3-16-148410-0")
        self.assertEqual(t, "isbn")
        self.assertEqual(v, "978-3-16-148410-0")

    def test_isbn_bare_detected(self):
        t, v = self.router.parse_input("978-3-662-54347-6")
        self.assertEqual(t, "isbn")

    def test_doi_detected(self):
        t, v = self.router.parse_input("10.1007/978-3-662-54347-6")
        self.assertEqual(t, "doi")

    def test_url_detected(self):
        t, v = self.router.parse_input("https://link.springer.com/book/10.1007/978")
        self.assertEqual(t, "url")

    def test_freetext_fallback(self):
        t, v = self.router.parse_input("Advanced Topics in Machine Learning")
        self.assertEqual(t, "title")


class TestBookFetcherRouting(unittest.TestCase):
    """Test the full routing chain with mocked subagent dispatch."""

    def _make_router(self, profile_file="active_profile_springer.yaml"):
        profile = _load_yaml(profile_file)
        return BookFetcherRouter(profile=profile)

    def test_isbn_routes_to_doabooks_first(self):
        """ISBN input: doabooks-fetcher is first subagent called; on success, returns immediately."""
        router = self._make_router()
        doabooks_resp = _load_json("doabooks_success.json")

        with patch.object(router, "dispatch_subagent", return_value=doabooks_resp) as mock_dispatch:
            result = router.fetch("978-3-16-148410-0", output_path="/tmp/out.pdf")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "doabooks-fetcher")
        self.assertEqual(result["tries"][0]["subagent"], "doabooks-fetcher")
        self.assertEqual(result["tries"][0]["status"], "success")
        # Only one subagent call (success on first try)
        self.assertEqual(mock_dispatch.call_count, 1)
        first_call_args = mock_dispatch.call_args_list[0]
        self.assertEqual(first_call_args[0][0], "doabooks-fetcher")

    def test_all_oa_metadata_only_then_springer_success(self):
        """OA subagents all return metadata_only; Springer (licensed) returns success."""
        router = self._make_router("active_profile_springer.yaml")
        meta_only = {"status": "metadata_only", "source_subagent": "doabooks-fetcher",
                     "url": "https://example.com"}
        springer_success = _load_json("springer_success.json")

        call_count = [0]
        oa_subagents = {"doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"}

        def side_effect(subagent, payload):
            call_count[0] += 1
            if subagent in oa_subagents:
                return dict(meta_only, source_subagent=subagent)
            if subagent == "springer-book":
                return springer_success
            raise AssertionError(f"Unexpected subagent call: {subagent}")

        with patch.object(router, "dispatch_subagent", side_effect=side_effect):
            result = router.fetch("978-3-662-54347-6", output_path="/tmp/springer.pdf")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source"], "springer-book")
        # tries must show all 4 OA subagents first, then springer-book
        subagent_sequence = [t["subagent"] for t in result["tries"]]
        self.assertEqual(subagent_sequence[:4],
                         ["doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"])
        self.assertIn("springer-book", subagent_sequence)

    def test_auth_required_triggers_auth_helper_then_retry(self):
        """Springer returns auth_required → auth-helper called → springer retried → success."""
        router = self._make_router("active_profile_springer.yaml")
        meta_only = {"status": "metadata_only", "source_subagent": "x", "url": "https://x.com"}
        auth_req = _load_json("springer_auth_required.json")
        auth_ok = _load_json("auth_helper_authenticated.json")
        springer_ok = _load_json("springer_success.json")
        oa_subagents = {"doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"}
        springer_calls = [0]

        def side_effect(subagent, payload):
            if subagent in oa_subagents:
                return dict(meta_only, source_subagent=subagent)
            if subagent == "springer-book":
                springer_calls[0] += 1
                if springer_calls[0] == 1:
                    return auth_req
                return springer_ok
            if subagent == "auth-helper":
                return auth_ok
            raise AssertionError(f"Unexpected: {subagent}")

        with patch.object(router, "dispatch_subagent", side_effect=side_effect):
            result = router.fetch("978-3-662-54347-6", output_path="/tmp/springer.pdf")

        self.assertEqual(result["status"], "success")
        subagent_names = [t["subagent"] for t in result["tries"]]
        # auth-helper must appear in tries
        self.assertIn("auth-helper", subagent_names)
        # springer-book must appear twice
        self.assertEqual(subagent_names.count("springer-book"), 2)

    def test_captcha_propagates_immediately(self):
        """If any subagent returns captcha, master returns captcha immediately."""
        router = self._make_router()
        captcha_resp = _load_json("captcha.json")

        with patch.object(router, "dispatch_subagent", return_value=captcha_resp):
            result = router.fetch("978-3-16-148410-0", output_path="/tmp/out.pdf")

        self.assertEqual(result["status"], "captcha")

    def test_all_fail_then_generic_fetcher_pickup_required(self):
        """All OA + no licensed publishers → generic-fetcher → pickup_required with hint."""
        router = self._make_router("active_profile_no_licensed.yaml")
        no_match = {"status": "no_match", "source_subagent": "doabooks-fetcher",
                    "reason": "0 results"}
        generic_resp = _load_json("generic_pickup.json")
        oa_subagents = {"doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"}

        def side_effect(subagent, payload):
            if subagent in oa_subagents:
                return dict(no_match, source_subagent=subagent)
            if subagent == "generic-fetcher":
                return generic_resp
            raise AssertionError(f"Unexpected: {subagent}")

        with patch.object(router, "dispatch_subagent", side_effect=side_effect):
            result = router.fetch("Advanced Topics in AI", output_path="/tmp/out.pdf")

        self.assertEqual(result["status"], "pickup_required")
        self.assertIn("pickup_hint", result)
        self.assertIn("bib_pickup_url", result["pickup_hint"])
        self.assertIn("identifier", result["pickup_hint"])
        # generic-fetcher must be last in tries
        self.assertEqual(result["tries"][-1]["subagent"], "generic-fetcher")


class TestBookFetcherAgentMarkdown(unittest.TestCase):
    """Validate the agent Markdown file has correct frontmatter."""

    def test_agent_file_exists(self):
        agent_path = pathlib.Path("agents/book-fetcher.md")
        self.assertTrue(agent_path.exists(), "agents/book-fetcher.md not found")

    def test_frontmatter_fields(self):
        agent_path = pathlib.Path("agents/book-fetcher.md")
        content = agent_path.read_text()
        # Extract YAML frontmatter between --- delimiters
        lines = content.split("\n")
        self.assertEqual(lines[0].strip(), "---", "Agent must start with ---")
        end = lines.index("---", 1)
        fm_text = "\n".join(lines[1:end])
        fm = yaml.safe_load(fm_text)
        self.assertEqual(fm.get("name"), "book-fetcher")
        self.assertIn("sonnet", fm.get("model", "").lower(),
                      "model must be sonnet")
        self.assertIsInstance(fm.get("tools"), list,
                              "tools must be a list")
        self.assertGreaterEqual(fm.get("maxTurns", 0), 8,
                                "maxTurns must be >= 8")

    def test_no_bash_in_tools(self):
        agent_path = pathlib.Path("agents/book-fetcher.md")
        content = agent_path.read_text()
        lines = content.split("\n")
        end = lines.index("---", 1)
        fm_text = "\n".join(lines[1:end])
        fm = yaml.safe_load(fm_text)
        tools = fm.get("tools", [])
        bash_tools = [t for t in tools if "Bash" in str(t)]
        self.assertEqual(bash_tools, [],
                         f"Master agent must NOT have Bash tools, found: {bash_tools}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2.2: Run tests to confirm they fail (RED)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_book_fetcher.py -v 2>&1 | head -40
```

Expected: `ModuleNotFoundError: No module named 'tests.helpers.book_fetcher_router'`
(or similar import error). This confirms RED state.

- [ ] **Step 2.3: Commit failing test**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && git add tests/test_book_fetcher.py && git commit -m "test(G): add failing tests for book-fetcher routing (RED)"
```

---

## Task 3: Router Implementation (GREEN)

**Files:**
- Create: `tests/helpers/__init__.py`
- Create: `tests/helpers/book_fetcher_router.py`

- [ ] **Step 3.1: Create helpers __init__.py**

`tests/helpers/__init__.py`:
```python
# Test helpers package
```

- [ ] **Step 3.2: Implement BookFetcherRouter**

`tests/helpers/book_fetcher_router.py`:
```python
"""
BookFetcherRouter — testbarer Python-Spiegel der Routing-Logik aus agents/book-fetcher.md.

Dieser Modul implementiert dieselbe Routing-Logik, die der Agent-Prompt beschreibt,
damit wir sie mit unittest.mock testen koennen ohne echte Subagenten aufzurufen.
"""
import re
import datetime
from typing import Any


# Subagent-Reihenfolgen (aus L0-Notes und Spec G.md)
OA_SUBAGENTS = ["doabooks-fetcher", "oapen-fetcher", "tib-fetcher", "kvk-fetcher"]

PUBLISHER_DOMAIN_MAP = {
    "link.springer.com": "springer-book",
    "degruyter.com": "degruyter",
    "nationallizenzen.de": "nationallizenzen",
    "ebookcentral.proquest.com": "ebook-central",
}


class BookFetcherRouter:
    """
    Simuliert die Routing-Logik des book-fetcher Master-Agenten.

    dispatch_subagent() kann in Tests gepatch werden, um echte Subagenten-
    Aufrufe zu simulieren.
    """

    def __init__(self, profile: dict):
        """
        Args:
            profile: Geparste active.yaml (dict mit licensed_sites, bib_pickup_url etc.)
        """
        self.profile = profile
        self.licensed_sites = set(profile.get("licensed_sites", []))
        self.bib_pickup_url = profile.get("bib_pickup_url", "")

    # ------------------------------------------------------------------
    # Input Parsing
    # ------------------------------------------------------------------

    def parse_input(self, raw: str) -> tuple[str, str]:
        """
        Erkennt den Eingabe-Typ und gibt (typ, normalisierter_wert) zurueck.

        Typen: 'isbn', 'doi', 'url', 'title'
        """
        text = raw.strip()

        # Explizites 'isbn:'-Prefix
        if text.lower().startswith("isbn:"):
            val = text[5:].strip()
            return ("isbn", val)

        # URL
        if text.startswith("http://") or text.startswith("https://"):
            return ("url", text)

        # DOI (beginnt mit 10.)
        if re.match(r"10\.\d{4,}/", text):
            return ("doi", text)

        # ISBN-13 (mit oder ohne Bindestriche)
        if re.match(r"^97[89][- ]?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?\d$", text):
            return ("isbn", text)

        # ISBN-10
        if re.match(r"^\d{9}[\dX]$", text.replace("-", "")):
            return ("isbn", text)

        # Freitext / Titel
        return ("title", text)

    # ------------------------------------------------------------------
    # Subagent Dispatch (real implementation uses Agent(...) tool)
    # ------------------------------------------------------------------

    def dispatch_subagent(self, subagent_name: str, payload: dict) -> dict:
        """
        Wird in Tests durch unittest.mock.patch.object ersetzt.
        In Produktion wuerde der Agent-Prompt hier Agent(...) aufrufen.
        """
        raise NotImplementedError(
            "dispatch_subagent must be patched in tests or overridden for production"
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _ts(self) -> str:
        return datetime.datetime.utcnow().isoformat() + "Z"

    def _try_entry(self, subagent: str, status: str) -> dict:
        return {"subagent": subagent, "status": status, "ts": self._ts()}

    def fetch(self, identifier_raw: str, output_path: str) -> dict:
        """
        Haupt-Routing-Funktion. Gibt das Master-Output-Schema zurueck.

        Args:
            identifier_raw: Rohe Eingabe (ISBN, DOI, URL oder Titel)
            output_path: Zielpfad fuer die heruntergeladene PDF-Datei

        Returns:
            dict mit Keys: status, source, file_path?, reason?, tries, pickup_hint?
        """
        id_type, id_value = self.parse_input(identifier_raw)
        payload_base = {
            "output_path": output_path,
            id_type: id_value,
        }
        tries = []
        best_metadata_url = None  # Beste bekannte URL aus metadata_only-Responses

        # ----------------------------------------------------------
        # Schritt 1: OA-Subagenten
        # ----------------------------------------------------------
        oa_any_metadata_only = False
        for subagent in OA_SUBAGENTS:
            resp = self.dispatch_subagent(subagent, payload_base)
            status = resp.get("status", "no_match")
            tries.append(self._try_entry(subagent, status))

            if status == "success":
                return {
                    "status": "success",
                    "source": subagent,
                    "file_path": resp.get("pdf_path"),
                    "tries": tries,
                }

            if status == "captcha":
                return {
                    "status": "captcha",
                    "source": subagent,
                    "reason": resp.get("reason", "CAPTCHA erkannt"),
                    "tries": tries,
                }

            if status == "metadata_only":
                oa_any_metadata_only = True
                if resp.get("url") and not best_metadata_url:
                    best_metadata_url = resp["url"]
                # Weiter mit naechstem OA-Subagenten

            # no_match: einfach weiter

        # ----------------------------------------------------------
        # Schritt 2: Verlags-Subagenten (nur wenn OA metadata_only und lizenziert)
        # ----------------------------------------------------------
        if oa_any_metadata_only:
            publisher_subagents = self._get_licensed_publisher_subagents()
            for pub_subagent in publisher_subagents:
                result = self._try_publisher(pub_subagent, payload_base, tries)
                if result is not None:
                    return result

        # ----------------------------------------------------------
        # Schritt 3: Fallback generic-fetcher
        # ----------------------------------------------------------
        generic_payload = dict(payload_base)
        if best_metadata_url:
            generic_payload["url"] = best_metadata_url

        resp = self.dispatch_subagent("generic-fetcher", generic_payload)
        status = resp.get("status", "no_match")
        tries.append(self._try_entry("generic-fetcher", status))

        if status == "success":
            return {
                "status": "success",
                "source": "generic-fetcher",
                "file_path": resp.get("pdf_path"),
                "tries": tries,
            }

        if status == "captcha":
            return {
                "status": "captcha",
                "source": "generic-fetcher",
                "reason": resp.get("reason", "CAPTCHA erkannt"),
                "tries": tries,
            }

        # pickup_required oder no_match → immer pickup_required mit Hinweis
        return {
            "status": "pickup_required",
            "source": "generic-fetcher",
            "reason": resp.get("reason", "Keine downloadbare Quelle gefunden"),
            "tries": tries,
            "pickup_hint": {
                "bib_pickup_url": self.bib_pickup_url,
                "identifier": id_value,
                "identifier_type": id_type,
            },
        }

    def _get_licensed_publisher_subagents(self) -> list[str]:
        """Gibt die Verlags-Subagenten zurueck, deren Host in licensed_sites ist."""
        result = []
        for domain, subagent in PUBLISHER_DOMAIN_MAP.items():
            if domain in self.licensed_sites:
                result.append(subagent)
        return result

    def _try_publisher(self, pub_subagent: str, payload_base: dict,
                       tries: list) -> dict | None:
        """
        Versucht einen Verlags-Subagenten. Handhabt auth_required mit auth-helper-Retry.

        Gibt das finale Ergebnis zurueck wenn erfolgreich/captcha, sonst None.
        """
        resp = self.dispatch_subagent(pub_subagent, payload_base)
        status = resp.get("status", "no_match")
        tries.append(self._try_entry(pub_subagent, status))

        if status == "success":
            return {
                "status": "success",
                "source": pub_subagent,
                "file_path": resp.get("pdf_path"),
                "tries": tries,
            }

        if status == "captcha":
            return {
                "status": "captcha",
                "source": pub_subagent,
                "reason": resp.get("reason", "CAPTCHA erkannt"),
                "tries": tries,
            }

        if status == "auth_required":
            # Auth-Helper aufrufen
            target_url = resp.get("url", "")
            auth_resp = self.dispatch_subagent("auth-helper", {
                "target_url": target_url,
                "profile_path": "~/.academic-research/library-profiles/active.yaml",
            })
            auth_status = auth_resp.get("status", "auth_failed")
            tries.append(self._try_entry("auth-helper", auth_status))

            if auth_status == "captcha":
                return {
                    "status": "captcha",
                    "source": "auth-helper",
                    "reason": "CAPTCHA beim Login",
                    "tries": tries,
                }

            if auth_status == "authenticated":
                # Einmaliger Retry
                retry_resp = self.dispatch_subagent(pub_subagent, payload_base)
                retry_status = retry_resp.get("status", "no_match")
                tries.append(self._try_entry(pub_subagent, retry_status))

                if retry_status == "success":
                    return {
                        "status": "success",
                        "source": pub_subagent,
                        "file_path": retry_resp.get("pdf_path"),
                        "tries": tries,
                    }

                if retry_status == "captcha":
                    return {
                        "status": "captcha",
                        "source": pub_subagent,
                        "reason": "CAPTCHA nach Auth-Retry",
                        "tries": tries,
                    }

            # auth_failed oder retry fehlgeschlagen → naechsten Verlags-Subagenten
            return None

        # metadata_only oder no_match → naechsten Verlags-Subagenten
        return None
```

- [ ] **Step 3.3: Run tests to verify GREEN**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_book_fetcher.py -v 2>&1
```

Expected:
```
tests/test_book_fetcher.py::TestBookFetcherInputParsing::test_isbn_13_detected PASSED
tests/test_book_fetcher.py::TestBookFetcherInputParsing::test_isbn_bare_detected PASSED
tests/test_book_fetcher.py::TestBookFetcherInputParsing::test_doi_detected PASSED
tests/test_book_fetcher.py::TestBookFetcherInputParsing::test_url_detected PASSED
tests/test_book_fetcher.py::TestBookFetcherInputParsing::test_freetext_fallback PASSED
tests/test_book_fetcher.py::TestBookFetcherRouting::test_isbn_routes_to_doabooks_first PASSED
tests/test_book_fetcher.py::TestBookFetcherRouting::test_all_oa_metadata_only_then_springer_success PASSED
tests/test_book_fetcher.py::TestBookFetcherRouting::test_auth_required_triggers_auth_helper_then_retry PASSED
tests/test_book_fetcher.py::TestBookFetcherRouting::test_captcha_propagates_immediately PASSED
tests/test_book_fetcher.py::TestBookFetcherRouting::test_all_fail_then_generic_fetcher_pickup_required PASSED
```

Note: `TestBookFetcherAgentMarkdown` tests will FAIL until Task 4 creates `agents/book-fetcher.md`.
That's expected at this stage.

- [ ] **Step 3.4: Commit router implementation**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && git add tests/helpers/ && git commit -m "feat(G): implement BookFetcherRouter — routing logic for book-fetcher master agent"
```

---

## Task 4: Agent Markdown (`agents/book-fetcher.md`)

**Files:**
- Create: `agents/book-fetcher.md`

- [ ] **Step 4.1: Write the agent definition**

`agents/book-fetcher.md`:
```markdown
---
name: book-fetcher
model: sonnet
description: |
  Master-Orchestrator fuer den Universal Book Fetcher (F16). Koordiniert
  OA-Subagenten (doabooks-fetcher, oapen-fetcher, tib-fetcher, kvk-fetcher),
  Verlags-Subagenten (springer-book, degruyter, nationallizenzen, ebook-central),
  auth-helper und generic-fetcher strikt sequentiell.
  Kein eigener Browser-Aufruf. Gibt strukturierten Output mit tries-Array zurueck.
tools:
  - Read
  - Write
  - "Agent(doabooks-fetcher)"
  - "Agent(oapen-fetcher)"
  - "Agent(tib-fetcher)"
  - "Agent(kvk-fetcher)"
  - "Agent(springer-book)"
  - "Agent(degruyter)"
  - "Agent(nationallizenzen)"
  - "Agent(ebook-central)"
  - "Agent(auth-helper)"
  - "Agent(generic-fetcher)"
maxTurns: 8
---

# book-fetcher — Master-Orchestrator

Du bist der Master-Orchestrator des Universal-Book-Fetcher-Systems. Du machst
KEINE eigenen Browser-Aufrufe. Deine einzige Aufgabe: Subagenten koordinieren.

**Kein Bash. Kein direkter HTTP-Zugriff. Nur Read, Write und Agent(...).**

---

## Input

Du erhaeltst eine Anfrage in einem dieser Formate:

```
isbn: 978-3-16-148410-0
doi: 10.1007/978-3-662-54347-6
https://link.springer.com/book/10.1007/...
Advanced Topics in Machine Learning
output_path: /tmp/book.pdf
```

`output_path` ist der Zielpfad fuer die heruntergeladene PDF-Datei (erforderlich).

---

## Schritt 1: Input parsen

Erkenne den Eingabe-Typ:

- **ISBN:** Beginnt mit `isbn:` ODER hat Format `978-...` (13 Ziffern) ODER 10 Ziffern/X
- **DOI:** Beginnt mit `10.` gefolgt von Ziffern und `/`
- **URL:** Beginnt mit `http://` oder `https://`
- **Freitext/Titel:** Alles andere

Speichere intern: `identifier_type` (isbn/doi/url/title) und `identifier_value`.

---

## Schritt 2: Profil lesen

Lese mit dem Read-Tool:
```
~/.academic-research/library-profiles/active.yaml
```

Extrahiere `licensed_sites` (Liste der lizenzierten Hosts) und `bib_pickup_url`.

Falls die Datei nicht existiert: Verwende leere `licensed_sites = []`.

---

## Schritt 3: OA-Subagenten (sequentiell)

Rufe diese Subagenten in **genau dieser Reihenfolge** auf, einer nach dem anderen:

1. `Agent(doabooks-fetcher)`
2. `Agent(oapen-fetcher)`
3. `Agent(tib-fetcher)`
4. `Agent(kvk-fetcher)`

Payload fuer jeden OA-Subagenten:
```json
{
  "<identifier_type>": "<identifier_value>",
  "output_path": "<output_path>"
}
```

**Nach jedem Aufruf:** Notiere das Ergebnis im `tries`-Array:
```json
{"subagent": "<name>", "status": "<status>", "ts": "<ISO-8601>"}
```

**Entscheidungslogik pro OA-Subagent:**
- `status: success` → **SOFORT stoppen**, Ergebnis zurueckgeben (kein weiterer Subagent)
- `status: captcha` → **SOFORT stoppen**, `{status: captcha}` zurueckgeben
- `status: metadata_only` → Merken (`oa_had_metadata_only = true`), naechsten OA-Subagenten versuchen
- `status: no_match` → Naechsten OA-Subagenten versuchen

---

## Schritt 4: Verlags-Subagenten (nur wenn OA metadata_only + lizenziert)

**Aktivierungsbedingung:** `oa_had_metadata_only == true`

Pruefe fuer jeden Verlags-Subagenten: Ist der zugehoerige Host in `licensed_sites`?

| Subagent | Host |
|----------|------|
| `Agent(springer-book)` | `link.springer.com` |
| `Agent(degruyter)` | `degruyter.com` |
| `Agent(nationallizenzen)` | `nationallizenzen.de` |
| `Agent(ebook-central)` | `ebookcentral.proquest.com` |

Rufe nur lizenzierte Verlags-Subagenten auf (sequentiell in der Tabellenreihenfolge).

**Auth-Retry-Logik bei `auth_required`:**
1. Trage `{subagent: <name>, status: auth_required}` in `tries` ein
2. Rufe `Agent(auth-helper)` auf mit:
   ```json
   {
     "target_url": "<url aus auth_required-Response>",
     "profile_path": "~/.academic-research/library-profiles/active.yaml"
   }
   ```
3. Trage auth-helper-Ergebnis in `tries` ein
4. Bei `{status: authenticated}`: Selben Verlags-Subagenten **einmalig** nochmals aufrufen
5. Bei `{status: captcha}`: **SOFORT stoppen**, `{status: captcha}` zurueckgeben
6. Bei `{status: auth_failed}`: Naechsten Verlags-Subagenten versuchen

---

## Schritt 5: Fallback generic-fetcher

Wenn weder OA- noch Verlags-Subagenten `success` geliefert haben:

Rufe `Agent(generic-fetcher)` auf:
```json
{
  "<identifier_type>": "<identifier_value>",
  "url": "<beste URL aus metadata_only-Responses, falls vorhanden>",
  "output_path": "<output_path>"
}
```

Trage Ergebnis in `tries` ein.

---

## Output-Schema (IMMER dieses Format zurueckgeben)

```json
{
  "status": "success | pickup_required | captcha | no_match",
  "source": "<subagent-name der den Endstatus lieferte>",
  "file_path": "<absoluter PDF-Pfad, nur bei success>",
  "reason": "<optionale Beschreibung>",
  "tries": [
    {"subagent": "<name>", "status": "<status>", "ts": "<ISO-8601>"}
  ]
}
```

**Bei `pickup_required`:** Zusaetzlich `pickup_hint` hinzufuegen:
```json
{
  "pickup_hint": {
    "bib_pickup_url": "<aus active.yaml>",
    "identifier": "<identifier_value>",
    "identifier_type": "<identifier_type>"
  }
}
```

---

## Status-Entscheidungsbaum

```
OA-Subagenten:
  └─ Einer gibt success → status: success
  └─ Einer gibt captcha → status: captcha (sofort)
  └─ Alle no_match (kein metadata_only) → weiter zu generic-fetcher
  └─ Mindestens einer metadata_only → weiter zu Verlags-Subagenten

Verlags-Subagenten:
  └─ Einer gibt success → status: success
  └─ Einer gibt captcha → status: captcha (sofort)
  └─ auth_required → auth-helper → retry → ggf. success
  └─ Alle fehlgeschlagen → weiter zu generic-fetcher

generic-fetcher:
  └─ success → status: success
  └─ pickup_required → status: pickup_required + pickup_hint
  └─ captcha → status: captcha
  └─ no_match → status: no_match (kein Treffer in allen Quellen)
```

---

## Wichtige Regeln

1. **Strikt sequentiell:** Nie zwei Subagenten gleichzeitig. Warte auf jede Antwort.
2. **Kein Bash:** Verwende nur Read und Write fuer Dateizugriffe.
3. **Kein direkter HTTP:** Alle Netzwerk-Aktionen gehen durch Subagenten.
4. **tries vollstaendig:** Jeder Subagenten-Aufruf (inkl. auth-helper und Retries) erscheint im tries-Array.
5. **Sofort-Stop bei captcha:** Bei captcha sofort zurueckgeben, nicht weiter versuchen.
6. **Einmaliger Retry:** Nach auth-helper → success nur EIN weiterer Versuch pro Verlags-Subagent.
```

- [ ] **Step 4.2: Run all tests (including agent markdown tests) — should now be fully GREEN**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_book_fetcher.py -v 2>&1
```

Expected: ALL tests pass, including `TestBookFetcherAgentMarkdown`.

- [ ] **Step 4.3: Commit agent definition**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && git add agents/book-fetcher.md && git commit -m "feat(G): add agents/book-fetcher.md master orchestrator agent"
```

---

## Task 5: Full Test Suite Verification

- [ ] **Step 5.1: Run full project test suite to ensure no regressions**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -30
```

Expected: All pre-existing tests still pass. New `test_book_fetcher.py` tests pass.

- [ ] **Step 5.2: Confirm test count**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && /opt/homebrew/opt/python@3.14/bin/python3 -m pytest tests/test_book_fetcher.py -v 2>&1 | grep -E "passed|failed|error"
```

Expected: `13 passed` (5 input parsing + 5 routing + 3 agent markdown validation), 0 failed, 0 error.

- [ ] **Step 5.3: Commit spec files**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-G && git add specs/v6.2/ && git commit -m "docs(G): add spec and plan for book-fetcher master agent"
```

---

## Self-Review Checklist

### Spec Coverage
- [x] `agents/book-fetcher.md` mit Frontmatter → Task 4
- [x] Tool-Restriction (kein Bash) → Task 4 + TestBookFetcherAgentMarkdown
- [x] Input-Parser (ISBN, DOI, URL, Freitext) → Task 3 + TestBookFetcherInputParsing
- [x] Routing OA → Verlags → generic → Task 3 (router) + Task 4 (agent)
- [x] auth_required → auth-helper → Retry → Task 3 + test_auth_required_triggers_auth_helper_then_retry
- [x] Profil lesen → Task 3 (router init) + Task 4 (agent step 2)
- [x] Output-Schema mit tries-Array → Task 3 router.fetch() return values
- [x] pickup_required + pickup_hint → test_all_fail_then_generic_fetcher_pickup_required
- [x] Sequentiell (nicht parallel) → router: jeder Aufruf wartet auf Antwort
- [x] Test ISBN → doabooks-fetcher zuerst → test_isbn_routes_to_doabooks_first
- [x] Test Verlagsbuch ohne OA → test_all_oa_metadata_only_then_springer_success

### No Placeholders
- Alle Schritte haben konkrete Code-Blöcke
- Alle erwarteten Test-Outputs sind spezifisch
- Keine TBD/TODO-Marker

### Type Consistency
- `BookFetcherRouter.fetch()` gibt immer dict mit `status`, `source`, `tries` zurück
- `dispatch_subagent(subagent_name: str, payload: dict) -> dict` konsistent in Tests und Impl.
- `_try_entry()` gibt `{"subagent", "status", "ts"}` zurück — konsistent mit Output-Schema
