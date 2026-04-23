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
