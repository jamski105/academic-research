"""Evals fuer quote-extractor-Agent (Block B + A)."""
import json
import re
from pathlib import Path

import pytest

from tests.evals.eval_runner import (
    EVALS_ROOT,
    call_claude,
    check_expected,
    load_agent_content,
)

_EVALS_PATH: Path = EVALS_ROOT / "quote-extractor" / "evals.json"
pytestmark = pytest.mark.skipif(
    not _EVALS_PATH.exists(),
    reason=f"evals-Datei fehlt: {_EVALS_PATH}",
)
EVALS: dict = json.loads(_EVALS_PATH.read_text()) if _EVALS_PATH.exists() else {"prompts": []}


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


# ---------------------------------------------------------------------------
# Vault-Mock-Tests (kein API-Key benoetigt)
# ---------------------------------------------------------------------------

def test_quote_extractor_evals_use_paper_id_input():
    """Alle qe-Prompts muessen paper_id im Input haben (Vault-Interface, kein pdf_text)."""
    for prompt in EVALS["prompts"]:
        inp = prompt["input"]
        assert '"paper_id"' in inp or "'paper_id'" in inp, (
            f"Prompt {prompt['id']} enthaelt noch kein paper_id-Feld im Input: {inp[:100]}"
        )


def test_mock_vault_add_quote_returns_uuid(mock_vault):
    """mock_vault.add_quote() gibt eine nicht-leere UUID-artige Zeichenkette zurueck."""
    quote_id = mock_vault.add_quote(
        paper_id="devops2022",
        verbatim="Governance frameworks ensure DevOps compliance.",
        extraction_method="citations-api",
        api_response_id="resp-fake-001",
        pdf_page=3,
        section="Introduction",
    )
    assert quote_id, "quote_id darf nicht leer sein"
    assert isinstance(quote_id, str)
    # UUID-Format (8-4-4-4-12 Hex)
    assert re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        quote_id,
    ), f"Kein UUID-Format: {quote_id!r}"


def test_mock_vault_find_quotes_returns_list(mock_vault):
    """mock_vault.find_quotes() gibt eine Liste mit vordefinierten Fake-Quotes zurueck."""
    quotes = mock_vault.find_quotes("devops2022", "governance", k=5)
    assert isinstance(quotes, list)
    assert len(quotes) > 0, "Fake-Paper 'devops2022' sollte vordefinierte Quotes haben"
    assert "verbatim" in quotes[0]
    assert "quote_id" in quotes[0]


def test_mock_vault_get_quote_returns_dict(mock_vault):
    """mock_vault.get_quote() gibt den gespeicherten Quote-Record zurueck."""
    quote_id = mock_vault.add_quote(
        paper_id="devops2022",
        verbatim="Test verbatim text.",
        extraction_method="manual",
    )
    result = mock_vault.get_quote(quote_id)
    assert result is not None
    assert result["verbatim"] == "Test verbatim text."
    assert result["paper_id"] == "devops2022"


def test_mock_vault_ensure_file_returns_fake_file_id(mock_vault):
    """mock_vault.ensure_file() gibt eine nicht-leere Fake-file_id zurueck."""
    file_id = mock_vault.ensure_file("devops2022")
    assert file_id, "file_id darf nicht leer sein"
    assert file_id.startswith("file-fake-")
