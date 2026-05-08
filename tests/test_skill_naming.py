"""Regression guard: Skill-Namen sind kebab-case und stimmen mit Ordnernamen überein."""
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
KEBAB_CASE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
VENDORED_SKILLS = {"xlsx", "_common"}


def _load_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"Missing frontmatter in {skill_md}"
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end])


def test_all_skill_names_are_kebab_case():
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in VENDORED_SKILLS:
            continue
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists(), f"Missing SKILL.md in {skill_dir}"
        fm = _load_frontmatter(skill_md)
        name = fm.get("name")
        assert name is not None, f"Missing name in {skill_md}"
        assert KEBAB_CASE.match(name), f"{skill_md}: name='{name}' is not kebab-case"


def test_skill_name_matches_directory():
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name in VENDORED_SKILLS:
            continue
        skill_md = skill_dir / "SKILL.md"
        fm = _load_frontmatter(skill_md)
        assert fm["name"] == skill_dir.name, (
            f"{skill_md}: name='{fm['name']}' != dir='{skill_dir.name}'"
        )
