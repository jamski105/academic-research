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


# Import will fail until Task 3 creates the module -- that's expected (RED)
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
        """Springer returns auth_required -> auth-helper called -> springer retried -> success."""
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
        """All OA + no licensed publishers -> generic-fetcher -> pickup_required with hint."""
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
