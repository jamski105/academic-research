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
README_PATH = Path(__file__).parent.parent / "README.md"
VENDORED_SKILLS = {"xlsx", "_common", "humanizer-de"}
ALL_SKILLS = sorted(
    p for p in SKILLS_DIR.glob("*/SKILL.md") if p.parent.name not in VENDORED_SKILLS
)

PREAMBLE_PATTERN = "> **Gemeinsames Preamble laden:**"
BASELINES_PATH = Path(__file__).parent / "baselines" / "skill_sizes.json"
TOKEN_REDUCTION_MIN = 1400  # Zeichen ~ 350 Token (cl100k-Proxy)


def _description(path: Path) -> str:
    """Liefert die zusammengesetzte 'description' aus dem Frontmatter.

    Unterstuetzt sowohl Single-Line- als auch YAML-Block-Skalar (``>``)-Stil.
    """
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return ""
    fm = m.group(1)
    dm = re.search(r"^description:\s*(.*?)(?=^[a-zA-Z_][a-zA-Z0-9_-]*:|\Z)", fm, re.DOTALL | re.M)
    if not dm:
        return ""
    return " ".join(dm.group(1).split())


def _readme_skill_triggers() -> dict[str, list[str]]:
    """Parst die README-'Skills-Übersicht'-Tabelle.

    Liefert ``{skill_name: [trigger_phrase, ...]}`` aus der Spalte
    'Aktiviert bei'. Trigger stehen dort als kursive Phrasen in
    deutschen Anfuehrungszeichen, z.B. *„Kapitel schreiben"*.
    """
    text = README_PATH.read_text()
    start = text.index("## Skills-Übersicht")
    end = text.index("\n---", start)
    section = text[start:end]

    row_re = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|\s*(.+?)\s*\|", re.M)
    trig_re = re.compile(r'[„"]([^„""]+)["""]')

    triggers: dict[str, list[str]] = {}
    for m in row_re.finditer(section):
        skill = m.group(1)
        phrases = trig_re.findall(m.group(2))
        if phrases:
            triggers[skill] = phrases
    return triggers


# (skill, trigger)-Paare flach fuer parametrize, damit jede Drift einzeln
# als Test-Failure sichtbar wird (Issue #208).
README_TRIGGER_CASES = [
    (skill, trig)
    for skill, phrases in _readme_skill_triggers().items()
    for trig in phrases
]


@pytest.mark.parametrize(
    "skill_name,trigger",
    README_TRIGGER_CASES,
    ids=[f"{s}:{t}" for s, t in README_TRIGGER_CASES],
)
def test_readme_trigger_in_skill_description(skill_name: str, trigger: str) -> None:
    """Issue #208: Jede README-Trigger-Phrase muss in der SKILL.md-description stehen.

    Andernfalls verspricht das README eine Aktivierung, die der Skill nicht
    leistet (funktionale Desynchronisation). Match ist case-insensitiv als
    Substring — die description darf den Trigger einbetten (z.B. in einer
    'X / Y'-Umlaut-Variante).
    """
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    assert skill_path.exists(), f"README nennt Skill '{skill_name}', aber {skill_path} fehlt"
    desc = _description(skill_path)
    assert trigger.lower() in desc.lower(), (
        f"{skill_name}: README-Trigger '{trigger}' fehlt in SKILL.md-description "
        f"(funktional desynchron, Issue #208). description={desc[:200]!r}"
    )


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
