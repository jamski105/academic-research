"""Trigger-Evals: prueft, ob Skill-Descriptions Undertriggering/Overtriggering aufweisen."""
from __future__ import annotations

import json
import re

import pytest

from tests.evals.eval_runner import EVALS_ROOT, SKILLS_ROOT, call_claude

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
    assert evals is not None  # narrow fuer type checker
    prompts: list[str] = list(evals["should_trigger"])
    hits = sum(_classify(p) == skill for p in prompts)
    total = len(prompts)
    recall = hits / total
    assert recall >= 0.85, f"{skill}: recall={recall:.0%} ({hits}/{total}), Schwelle 85%"


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_should_not_trigger_fpr(skill: str):
    evals = _load_trigger_evals(skill)
    if not evals or not evals.get("should_not_trigger"):
        pytest.skip(f"Keine trigger_evals.json fuer {skill}")
    assert evals is not None  # narrow fuer type checker
    prompts: list[str] = list(evals["should_not_trigger"])
    false_pos = sum(_classify(p) == skill for p in prompts)
    total = len(prompts)
    fpr = false_pos / total
    assert fpr <= 0.10, f"{skill}: fpr={fpr:.0%} ({false_pos}/{total}), Schwelle 10%"
