"""Regression-Test fuer Issue #177.

Trigger-Konflikt humanizer-de vs style-evaluator (KI-Erkennung):
Die User-Phrase "Pruef den Text auf KI-Muster" koennte beide Skills aktivieren.
Dieser Test fixiert die Disambiguierung in beiden SKILL.md-Descriptions:

- style-evaluator: Detektion-only ohne Revision; fuer Korrektur -> humanizer-de;
  triggert auf "Score" / "Audit".
- humanizer-de: inkludiert Korrektur; fuer reine Detektion -> style-evaluator;
  triggert auf "humanisieren" / "umschreiben" / "weniger KI-haft".
"""
from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _description(skill: str) -> str:
    """Liest das description-Feld aus dem YAML-Frontmatter (inkl. Block-Scalar)."""
    text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, f"{skill}: kein YAML-Frontmatter"
    fm = m.group(1)
    desc_m = re.search(
        r"^description:\s*\|?>?\s*(.+?)(?=^[a-zA-Z_-]+:|\Z)", fm, re.M | re.S
    )
    assert desc_m, f"{skill}: kein description-Feld"
    # Mehrzeilige Block-Scalars zu einer Zeile zusammenfuehren.
    return re.sub(r"\s+", " ", desc_m.group(1)).strip()


def test_style_evaluator_detektion_only_verweis_auf_humanizer() -> None:
    desc = _description("style-evaluator").lower()
    assert "detektion" in desc, "style-evaluator: 'Detektion' fehlt in description"
    assert "humanizer-de" in desc, (
        "style-evaluator: Verweis auf humanizer-de fuer Korrektur fehlt"
    )


def test_style_evaluator_score_und_audit_trigger() -> None:
    desc = _description("style-evaluator").lower()
    assert "score" in desc, "style-evaluator: Trigger 'Score' fehlt in description"
    assert "audit" in desc, "style-evaluator: Trigger 'Audit' fehlt in description"


def test_humanizer_inkludiert_korrektur_verweis_auf_style_evaluator() -> None:
    desc = _description("humanizer-de").lower()
    assert "korrektur" in desc, "humanizer-de: 'Korrektur' fehlt in description"
    assert "style-evaluator" in desc, (
        "humanizer-de: Verweis auf style-evaluator fuer reine Detektion fehlt"
    )


def test_humanizer_humanisieren_und_umschreiben_trigger() -> None:
    desc = _description("humanizer-de").lower()
    assert "humanisieren" in desc, (
        "humanizer-de: Trigger 'humanisieren' fehlt in description"
    )
    assert "umschreiben" in desc, (
        "humanizer-de: Trigger 'umschreiben' fehlt in description"
    )
    assert "weniger ki-haft" in desc, (
        "humanizer-de: Trigger 'weniger KI-haft' fehlt in description"
    )
