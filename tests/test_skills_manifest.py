"""Smoke-Test fuer Skill-Manifest-Struktur nach E3-Prompt-Quality-Refactor.

Prueft jede skills/*/SKILL.md auf:
- valides YAML-Frontmatter mit name + description
- Preamble-Reference (Blockquote-Pattern) statt inline-Sections
- >= 1 Umlaut-Paar ('X.../X...'-Muster mit Umlaut vor dem Slash) in description
- preamble.md existiert mit den 4 Pflicht-Sections
- Token-Reduktion >= 1400 Zeichen pro Skill vs. Baseline
"""

import json
import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
VENDORED_SKILLS = {"xlsx", "_common"}
ALL_SKILLS = sorted(
    p for p in SKILLS_DIR.glob("*/SKILL.md") if p.parent.name not in VENDORED_SKILLS
)

PREAMBLE_PATTERN = "> **Gemeinsames Preamble laden:**"
BASELINES_PATH = Path(__file__).parent / "baselines" / "skill_sizes.json"
TOKEN_REDUCTION_MIN = 1400  # Zeichen ~ 350 Token (cl100k-Proxy)


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
    """Preamble-Reference-Check: preamble.md enthaelt '## Keine Fabrikation'."""
    assert PREAMBLE_PATTERN in skill_path.read_text(), (
        f"{skill_path}: Preamble-Reference '{PREAMBLE_PATTERN}' fehlt"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_precondition_section(skill_path: Path) -> None:
    """Preamble-Reference-Check: preamble.md enthaelt '## Vorbedingungen'."""
    assert PREAMBLE_PATTERN in skill_path.read_text(), (
        f"{skill_path}: Preamble-Reference '{PREAMBLE_PATTERN}' fehlt"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_umlaut_variants_in_description(skill_path: Path) -> None:
    fm = _frontmatter(skill_path)
    desc = fm.get("description", "")
    pairs = re.findall(r'"[^"]*[äöüß][^"]*\s*/\s*[a-zA-Z][^"]*"', desc)
    assert len(pairs) >= 1, (
        f"{skill_path}: 0 Umlaut-Paare in description (gefunden: {desc[:160]}...)"
    )


def test_preamble_file_exists() -> None:
    """skills/_common/preamble.md existiert mit allen 4 Pflicht-Sections."""
    preamble = SKILLS_DIR / "_common" / "preamble.md"
    assert preamble.exists(), "skills/_common/preamble.md fehlt"
    text = preamble.read_text()
    for section in ["## Vorbedingungen", "## Keine Fabrikation", "## Aktivierung", "## Abgrenzung"]:
        assert section in text, f"preamble.md: Pflicht-Section '{section}' fehlt"


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_preamble_load_instruction(skill_path: Path) -> None:
    """Jedes SKILL.md enthaelt den Blockquote-Preamble-Ladeaufruf."""
    assert PREAMBLE_PATTERN in skill_path.read_text(), (
        f"{skill_path}: Preamble-Ladereferenz '{PREAMBLE_PATTERN}' fehlt"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_no_inline_vorbedingungen(skill_path: Path) -> None:
    """Kein SKILL.md darf '## Vorbedingungen' als eigene Section enthalten."""
    assert "\n## Vorbedingungen\n" not in skill_path.read_text(), (
        f"{skill_path}: inline '## Vorbedingungen' gefunden — muss entfernt werden"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_no_inline_fabrikation(skill_path: Path) -> None:
    """Kein SKILL.md darf '## Keine Fabrikation' als eigene Section enthalten."""
    assert "\n## Keine Fabrikation\n" not in skill_path.read_text(), (
        f"{skill_path}: inline '## Keine Fabrikation' gefunden — muss entfernt werden"
    )


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_token_reduction(skill_path: Path) -> None:
    """Jedes SKILL.md muss >= 1400 Zeichen (~ 350 Token) kleiner als Baseline sein."""
    assert BASELINES_PATH.exists(), f"Baseline-Datei fehlt: {BASELINES_PATH}"
    baselines = json.loads(BASELINES_PATH.read_text())
    skill_name = skill_path.parent.name
    assert skill_name in baselines, f"Skill '{skill_name}' nicht in Baseline"
    old_chars = baselines[skill_name]
    new_chars = len(skill_path.read_text())
    delta = old_chars - new_chars
    assert delta >= TOKEN_REDUCTION_MIN, (
        f"{skill_name}: Reduktion nur {delta} Zeichen "
        f"(erwartet >= {TOKEN_REDUCTION_MIN}). "
        f"alt={old_chars}, neu={new_chars}"
    )
