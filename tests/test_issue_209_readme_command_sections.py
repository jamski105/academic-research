"""Regressionstest fuer Issue #209.

Befund: In README.md hatten nur `/search` und `/fetch` eine eigene
Syntax-/Args-Sektion. Die uebrigen 7 Slash-Commands (setup, history, pickup,
score, humanize, excel, latex) fehlten — inklusive des v6.5-Neu-Commands
`/latex`.

Akzeptanzkriterien (aus dem Issue):
- README-Sektion "Commands" je Command:
  - Syntax mit `argument-hint`
  - Mindestens 1 Beispiel
  - Verweis auf zugrundeliegende Skills/Agents
- `/academic-research:latex`-Sektion prioritaer (v6.5-Feature)
- Konsistenz mit `commands/<name>.md`-Frontmatter
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
COMMANDS_DIR = REPO_ROOT / "commands"

# Alle 9 Slash-Commands des Plugins (Dateiname == Command-Slug).
ALL_COMMANDS = sorted(p.stem for p in COMMANDS_DIR.glob("*.md"))

# Schluesselbegriffe, die einen Verweis auf zugrundeliegende Skills/Agents
# belegen. Mindestens einer muss in der jeweiligen Command-Sektion vorkommen.
SKILL_AGENT_HINTS = ("Skill", "skill", "Agent", "agent")


def _commands_section() -> str:
    """Liefert den Text der README-Sektion 'Commands / Slash-Commands'."""
    text = README.read_text(encoding="utf-8")
    start = text.index("## Commands / Slash-Commands")
    # Die naechste Top-Level-Sektion beendet den Block.
    rest = text[start + len("## Commands / Slash-Commands"):]
    m = re.search(r"\n## ", rest)
    end = m.start() if m else len(rest)
    return rest[:end]


def _command_subsection(section_text: str, name: str) -> str:
    """Liefert den Text der `### `/academic-research:<name>``-Subsektion."""
    heading = f"### `/academic-research:{name}`"
    if heading not in section_text:
        return ""
    start = section_text.index(heading) + len(heading)
    rest = section_text[start:]
    m = re.search(r"\n### ", rest)
    end = m.start() if m else len(rest)
    return rest[:end]


def test_all_nine_commands_present_in_commands_dir() -> None:
    """Sanity: genau die im Issue genannten 9 Commands existieren."""
    assert set(ALL_COMMANDS) == {
        "excel",
        "fetch",
        "history",
        "humanize",
        "latex",
        "pickup",
        "score",
        "search",
        "setup",
    }, f"Unerwartete Command-Liste: {ALL_COMMANDS}"


@pytest.mark.parametrize("name", ALL_COMMANDS)
def test_command_has_readme_subsection(name: str) -> None:
    """Jeder Command hat eine eigene `### `/academic-research:<name>``-Sektion."""
    section = _commands_section()
    heading = f"### `/academic-research:{name}`"
    assert heading in section, (
        f"README Commands-Sektion fehlt Subsektion fuer '{name}' "
        f"(erwartet Heading: {heading})"
    )


@pytest.mark.parametrize("name", ALL_COMMANDS)
def test_command_subsection_has_syntax(name: str) -> None:
    """Jede Command-Sektion enthaelt eine 'Syntax:'-Zeile mit dem Command-Slug."""
    sub = _command_subsection(_commands_section(), name)
    assert sub, f"Subsektion fuer '{name}' nicht gefunden"
    assert "Syntax:" in sub, f"'{name}': 'Syntax:'-Zeile fehlt"
    assert f"/academic-research:{name}" in sub, (
        f"'{name}': Command-Slug fehlt in der Syntax-Sektion"
    )


@pytest.mark.parametrize("name", ALL_COMMANDS)
def test_command_subsection_has_example(name: str) -> None:
    """Jede Command-Sektion enthaelt mindestens 1 Beispiel (Beispiel-Aufruf).

    Ein Beispiel ist eine weitere Erwaehnung des Command-Slugs ausserhalb der
    reinen Syntax-Definition (z.B. unter 'Beispiel'/'Beispiele' oder als
    konkreter Aufruf in einem Codeblock).
    """
    sub = _command_subsection(_commands_section(), name)
    assert sub, f"Subsektion fuer '{name}' nicht gefunden"
    # Mindestens zwei Vorkommen des Slugs: einmal Syntax, einmal Beispiel.
    occurrences = sub.count(f"/academic-research:{name}")
    assert occurrences >= 2, (
        f"'{name}': zu wenige Aufruf-Beispiele "
        f"({occurrences} Vorkommen, erwartet >= 2)"
    )
    assert ("Beispiel" in sub) or ("```" in sub), (
        f"'{name}': weder 'Beispiel'-Hinweis noch Codeblock gefunden"
    )


@pytest.mark.parametrize("name", ALL_COMMANDS)
def test_command_subsection_references_skill_or_agent(name: str) -> None:
    """Jede Command-Sektion verweist auf zugrundeliegende Skills/Agents."""
    sub = _command_subsection(_commands_section(), name)
    assert sub, f"Subsektion fuer '{name}' nicht gefunden"
    assert any(hint in sub for hint in SKILL_AGENT_HINTS), (
        f"'{name}': kein Verweis auf Skill/Agent in der README-Sektion"
    )


def test_latex_section_present_priority() -> None:
    """v6.5-Neu: `/latex` MUSS eine eigene Sektion mit Syntax + Beispiel haben."""
    sub = _command_subsection(_commands_section(), "latex")
    assert sub, "README: `/academic-research:latex`-Sektion fehlt (v6.5-Feature)"
    assert "Syntax:" in sub, "latex: Syntax-Zeile fehlt"
    assert ".tex" in sub and ".bib" in sub, (
        "latex: Verweis auf .tex/.bib-Ausgabe fehlt"
    )
