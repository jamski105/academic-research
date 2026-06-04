"""Eval-Coverage-Guard (Issue #198).

Stellt sicher, dass JEDER projekteigene Skill unter ``skills/*/SKILL.md`` sowohl
``evals/<skill>/trigger_evals.json`` als auch ``evals/<skill>/evals.json`` besitzt
und dass diese die im SCHEMA.md dokumentierten Mindestanforderungen erfuellen.

Vor Issue #198 wurden fehlende ``evals/``-Verzeichnisse von ``test_triggers.py`` und
``test_rest_evals.py`` stillschweigend uebersprungen (``if not path.exists(): continue``
bzw. ``pytest.skip``). Dieser Test macht die Luecke CI-sichtbar: fehlende oder
strukturell unvollstaendige Eval-Dateien sind ein FAIL, kein Skip.
"""
from __future__ import annotations

import json

import pytest

from tests.evals.eval_runner import EVALS_ROOT, SKILLS_ROOT

# Skills, die KEINE projekteigenen Evals brauchen:
# - ``_common``: geteilter Code, kein eigenstaendiger Skill (kein SKILL.md-Trigger).
# - ``xlsx``: vendorter, proprietaerer Anthropic-Document-Skill (LICENSE.txt), wird
#   nicht vom Projekt gepflegt und ist daher von der Eval-Pflicht ausgenommen.
EXEMPT_SKILLS = {"_common", "xlsx"}

# Mindestanforderungen aus evals/SCHEMA.md / Issue #198.
# Der Floor ist bewusst am bestehenden Repo-Baseline ausgerichtet (alle Trigger-
# Dateien haben 10/10, alle Quality-Dateien mindestens 2 Prompts), damit der Guard
# die Coverage-Luecke schliesst, ohne unbeteiligte Altdateien zu brechen. Neu
# angelegte Skills (Issue #198) erfuellen die obere Schema-Vorgabe (5-10 Trigger /
# 3-5 Quality).
MIN_TRIGGER_CASES = 5  # 5-10 Trigger-Test-Cases (positive)
MIN_NEGATIVE_CASES = 5  # negative Cases
MIN_QUALITY_CASES = 2  # >= 2 Quality-Cases (Baseline); Neuzugaenge liefern 3-5


def _project_skills() -> list[str]:
    return sorted(
        p.parent.name
        for p in SKILLS_ROOT.glob("*/SKILL.md")
        if p.parent.name not in EXEMPT_SKILLS
    )


PROJECT_SKILLS = _project_skills()


@pytest.mark.parametrize("skill", PROJECT_SKILLS)
def test_skill_has_trigger_evals(skill: str) -> None:
    path = EVALS_ROOT / skill / "trigger_evals.json"
    assert path.exists(), (
        f"Skill '{skill}' hat keine trigger_evals.json unter {path} "
        f"(Eval-Coverage-Luecke, Issue #198)."
    )
    data = json.loads(path.read_text())
    assert data.get("component") == skill, (
        f"{path}: component='{data.get('component')}' != Verzeichnisname '{skill}'"
    )
    should = data.get("should_trigger", [])
    should_not = data.get("should_not_trigger", [])
    assert len(should) >= MIN_TRIGGER_CASES, (
        f"{skill}: nur {len(should)} should_trigger-Cases, "
        f"mindestens {MIN_TRIGGER_CASES} gefordert."
    )
    assert len(should_not) >= MIN_NEGATIVE_CASES, (
        f"{skill}: nur {len(should_not)} should_not_trigger-Cases, "
        f"mindestens {MIN_NEGATIVE_CASES} gefordert."
    )
    assert all(isinstance(p, str) and p.strip() for p in should + should_not), (
        f"{skill}: trigger-Cases muessen nicht-leere Strings sein."
    )


@pytest.mark.parametrize("skill", PROJECT_SKILLS)
def test_skill_has_quality_evals(skill: str) -> None:
    path = EVALS_ROOT / skill / "evals.json"
    assert path.exists(), (
        f"Skill '{skill}' hat keine evals.json unter {path} "
        f"(Eval-Coverage-Luecke, Issue #198)."
    )
    data = json.loads(path.read_text())
    assert data.get("component") == skill, (
        f"{path}: component='{data.get('component')}' != Verzeichnisname '{skill}'"
    )
    assert data.get("component_type") in ("skill", "agent"), (
        f"{path}: component_type fehlt oder ungueltig ({data.get('component_type')})."
    )
    prompts = data.get("prompts", [])
    assert len(prompts) >= MIN_QUALITY_CASES, (
        f"{skill}: nur {len(prompts)} Quality-Cases, "
        f"mindestens {MIN_QUALITY_CASES} gefordert."
    )
    seen_ids: set[str] = set()
    for p in prompts:
        pid = p.get("id")
        assert pid and pid not in seen_ids, f"{skill}: doppelte/fehlende prompt-id {pid!r}."
        seen_ids.add(pid)
        assert p.get("input", "").strip(), f"{skill}/{pid}: leeres input-Feld."
        assert p.get("mode") in ("with_skill", "without_skill", "both"), (
            f"{skill}/{pid}: ungueltiger mode {p.get('mode')!r}."
        )
        expected = p.get("expected", {})
        assert expected.get("type") in ("substring", "regex", "json_field"), (
            f"{skill}/{pid}: ungueltiger expected.type {expected.get('type')!r}."
        )
