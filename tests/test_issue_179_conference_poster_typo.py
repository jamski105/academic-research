"""Regressionstest fuer Issue #179.

skills/conference-poster/SKILL.md:3 enthielt einen Tippfehler in der
Description: "Poster fuer Konferenz create" (englisches Wort + ASCII-Ersatz
mitten im deutschen Trigger-String).

Akzeptanzkriterien (Issue #179):
- "create" -> "erstellen"
- Umlaut-Restoration "fuer" -> "für"
"""

import re
from pathlib import Path

SKILL_MD = (
    Path(__file__).parent.parent
    / "skills"
    / "conference-poster"
    / "SKILL.md"
)


def _description() -> str:
    text = SKILL_MD.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, "kein YAML-Frontmatter in conference-poster/SKILL.md"
    fm = m.group(1)
    desc_lines: list[str] = []
    capturing = False
    for line in fm.splitlines():
        if line.startswith("description:"):
            capturing = True
            desc_lines.append(line.partition(":")[2].strip())
        elif capturing and line.startswith("  "):
            desc_lines.append(line.strip())
        elif capturing:
            break
    return " ".join(desc_lines)


def test_no_konferenz_create_typo() -> None:
    """Der englische Tippfehler 'Konferenz create' darf nicht mehr vorkommen."""
    desc = _description()
    assert "Konferenz create" not in desc, (
        "Tippfehler 'Konferenz create' weiterhin in der Description vorhanden"
    )


def test_korrekter_deutscher_trigger() -> None:
    """Der Trigger lautet korrekt 'Poster für Konferenz erstellen'."""
    desc = _description()
    assert "Poster für Konferenz erstellen" in desc, (
        "korrekter Trigger 'Poster für Konferenz erstellen' fehlt"
    )


def test_keine_fuer_ascii_ersatz_im_trigger() -> None:
    """Die ASCII-Ersatzform 'fuer Konferenz' darf nicht mehr vorkommen."""
    desc = _description()
    assert "fuer Konferenz" not in desc, (
        "ASCII-Ersatz 'fuer Konferenz' weiterhin vorhanden — 'für' erwartet"
    )
