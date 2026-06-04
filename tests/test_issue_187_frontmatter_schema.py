"""Regression test fuer Issue #187: Einheitliches Frontmatter-Schema.

Akzeptanzkriterien (aus dem Issue):
- Alle nicht-vendorten SKILL.md haben `license` (Default `MIT`).
- Alle nicht-vendorten SKILL.md haben `allowed-tools` als YAML-Liste.
- Das nicht-offizielle `triggers:`-Feld ist in `reading-list-import`
  und `material-passport` entfernt (Trigger gehoeren in `description`).
- Beim Entfernen darf `description` nicht zerstoert werden
  (Name + Beschreibung bleiben nicht-leer).

`xlsx` (proprietaer/vendored) und `_common` (kein Skill) sind ausgenommen.
`humanizer-de` traegt `license: MIT` plus `vendored_from`/upstream-Felder
und ist daher beim Pflichtfeld-Check enthalten (license vorhanden), wird
aber nicht auf einen bestimmten License-Wert festgenagelt.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# xlsx hat eine eigene proprietaere LICENSE.txt + eigene Konventionen,
# _common ist kein Skill (nur geteilte Fragmente).
EXEMPT = {"xlsx", "_common"}

NON_EXEMPT_SKILLS = sorted(
    p
    for p in SKILLS_DIR.glob("*/SKILL.md")
    if p.parent.name not in EXEMPT
)

# Issue benennt diese beiden Skills explizit fuer die triggers-Entfernung.
TRIGGERS_TO_REMOVE = ["reading-list-import", "material-passport"]


def _load_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"Missing frontmatter in {skill_md}"
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end])


def test_non_exempt_skills_found() -> None:
    # Sanity: wir pruefen tatsaechlich Skills (kein leerer Glob).
    assert len(NON_EXEMPT_SKILLS) >= 26, NON_EXEMPT_SKILLS


@pytest.mark.parametrize(
    "skill_md", NON_EXEMPT_SKILLS, ids=lambda p: p.parent.name
)
def test_license_present(skill_md: Path) -> None:
    fm = _load_frontmatter(skill_md)
    assert fm.get("license"), f"{skill_md}: Pflichtfeld 'license' fehlt"


@pytest.mark.parametrize(
    "skill_md", NON_EXEMPT_SKILLS, ids=lambda p: p.parent.name
)
def test_allowed_tools_is_list(skill_md: Path) -> None:
    fm = _load_frontmatter(skill_md)
    at = fm.get("allowed-tools")
    assert at is not None, f"{skill_md}: Pflichtfeld 'allowed-tools' fehlt"
    assert isinstance(at, list), (
        f"{skill_md}: 'allowed-tools' muss eine YAML-Liste sein, ist {type(at)}"
    )
    assert len(at) >= 1, f"{skill_md}: 'allowed-tools' ist leer"
    assert all(isinstance(t, str) and t for t in at), (
        f"{skill_md}: 'allowed-tools' enthaelt nicht-leere Strings: {at}"
    )


@pytest.mark.parametrize("skill_name", TRIGGERS_TO_REMOVE)
def test_triggers_field_removed(skill_name: str) -> None:
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    fm = _load_frontmatter(skill_md)
    assert "triggers" not in fm, (
        f"{skill_md}: nicht-offizielles 'triggers'-Feld muss entfernt sein "
        f"(Trigger gehoeren in description)"
    )


@pytest.mark.parametrize("skill_name", TRIGGERS_TO_REMOVE)
def test_description_intact_after_trigger_removal(skill_name: str) -> None:
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    fm = _load_frontmatter(skill_md)
    assert fm.get("name") == skill_name, f"{skill_md}: name beschaedigt"
    desc = fm.get("description") or ""
    assert len(desc.strip()) >= 40, (
        f"{skill_md}: description leer/zerstoert nach triggers-Entfernung"
    )
