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

    @pytest.mark.parametrize("agent_name", AGENT_NAMES)
    def test_no_curl_in_agent(self, agent_name):
        """Agent darf kein 'curl' als Shell-Command enthalten."""
        path = AGENTS_DIR / f"{agent_name}.md"
        content = path.read_text(encoding="utf-8")
        # Suche nach curl als standalone-Befehl (Zeilenanfang + optionaler Backtick)
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
