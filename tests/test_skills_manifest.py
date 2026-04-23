"""Smoke-Test fuer Skill-Manifest-Struktur nach E3-Prompt-Quality-Refactor.

Prueft jede skills/*/SKILL.md auf:
- valides YAML-Frontmatter mit name + description
- '## Vorbedingungen'-Sektion (ausser academic-context)
- '## Keine Fabrikation'-Sektion (alle 13)
- >= 1 Umlaut-Paar ('X.../X...'-Muster mit Umlaut vor dem Slash) in description
"""

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
ALL_SKILLS = sorted(SKILLS_DIR.glob("*/SKILL.md"))
SKILLS_WITH_PRECONDITION = [p for p in ALL_SKILLS if p.parent.name != "academic-context"]


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    current_key: str | None = None
    for line in m.group(1).splitlines():
        if re.match(r"^[a-zA-Z_-]+:\s*", line):
            key, _, val = line.partition(":")
            current_key = key.strip()
            fm[current_key] = val.strip()
        elif current_key and line.startswith("  "):
            fm[current_key] += " " + line.strip()
    return fm


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_frontmatter_valid(skill_path: Path) -> None:
    fm = _frontmatter(skill_path)
    assert fm.get("name"), f"{skill_path}: name fehlt"
    assert fm.get("description"), f"{skill_path}: description fehlt"


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_no_fabrication_section(skill_path: Path) -> None:
    assert "\n## Keine Fabrikation\n" in skill_path.read_text(), (
        f"{skill_path}: '## Keine Fabrikation' fehlt"
    )


@pytest.mark.parametrize("skill_path", SKILLS_WITH_PRECONDITION, ids=lambda p: p.parent.name)
def test_precondition_section(skill_path: Path) -> None:
    assert "\n## Vorbedingungen\n" in skill_path.read_text(), (
        f"{skill_path}: '## Vorbedingungen' fehlt"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_umlaut_variants_in_description(skill_path: Path) -> None:
    fm = _frontmatter(skill_path)
    desc = fm.get("description", "")
    pairs = re.findall(r'"[^"]*[äöüß][^"]*\s*/\s*[a-zA-Z][^"]*"', desc)
    assert len(pairs) >= 1, (
        f"{skill_path}: 0 Umlaut-Paare in description (gefunden: {desc[:160]}...)"
    )
