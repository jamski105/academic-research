"""Evals fuer citation-extraction-Skill."""
import json
from pathlib import Path

import pytest

from tests.evals.eval_runner import (
    EVALS_ROOT,
    call_claude,
    check_expected,
    load_skill_content,
)

_EVALS_PATH: Path = EVALS_ROOT / "citation-extraction" / "evals.json"
pytestmark = pytest.mark.skipif(
    not _EVALS_PATH.exists(),
    reason=f"evals-Datei fehlt: {_EVALS_PATH}",
)
EVALS: dict = json.loads(_EVALS_PATH.read_text()) if _EVALS_PATH.exists() else {"prompts": []}


@pytest.mark.parametrize("prompt", EVALS["prompts"], ids=lambda p: p["id"])
@pytest.mark.parametrize("mode", ["with_skill", "without_skill"])
def test_citation_extraction_eval(prompt, mode):
    if prompt["mode"] not in ("both", mode):
        pytest.skip(f"Prompt {prompt['id']} nicht fuer Mode {mode}")
    system = load_skill_content("citation-extraction") if mode == "with_skill" else ""
    output = call_claude(system=system, user=prompt["input"])
    assert check_expected(output, prompt["expected"]), (
        f"[{mode}] {prompt['id']}: expected={prompt['expected']} actual={output[:200]}"
    )
