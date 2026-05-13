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
