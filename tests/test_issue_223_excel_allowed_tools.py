"""
Regressionstest fuer Issue #223 — commands/excel.md: Bash(ls) + Skill(xlsx) fehlen in allowed-tools.

Problem:
  commands/excel.md listet nur `allowed-tools: Read, Write`. Der Workflow fuehrt
  jedoch in Schritt 1 ein `ls ~/.academic-research/sessions/` per Bash aus (Zeile 35)
  und aktiviert in Schritt 3 den vendorierten `xlsx`-Skill (Zeile 50). Ohne die
  passenden Permissions scheitern Session-Lookup und Excel-Generierung.

Akzeptanzkriterium:
  `/academic-research:excel` findet die letzte Session und erzeugt die Excel-Datei
  ohne Permission-Fehler -> `allowed-tools` muss eine Bash-Permission fuer den
  Sessions-Lookup und `Skill(xlsx)` enthalten.

Hinweis zum Parsing:
  Der `argument-hint`-Wert enthaelt eckige Klammern und ist daher kein valides
  YAML-Flow-Mapping. Wie der CI-Frontmatter-Coverage-Check wird das `allowed-tools`-
  Feld deshalb zeilenbasiert extrahiert (kein voller YAML-Parse).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
COMMAND_FILE = REPO_ROOT / "commands/excel.md"


def _frontmatter_lines(path: Path) -> list[str]:
    """Liefert die Zeilen des '---'-begrenzten Frontmatter-Blocks."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    out: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        out.append(line)
    return out


def _frontmatter_field(path: Path, field: str) -> str:
    """Extrahiert den Wert eines Top-Level-Frontmatter-Feldes zeilenbasiert."""
    prefix = f"{field}:"
    for line in _frontmatter_lines(path):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def test_command_file_exists():
    assert COMMAND_FILE.exists(), f"Missing: {COMMAND_FILE}"


def test_frontmatter_has_bash_sessions_permission():
    """allowed-tools muss eine Bash-Permission fuer den Sessions-Lookup enthalten."""
    allowed = _frontmatter_field(COMMAND_FILE, "allowed-tools")
    # Schritt 1 ruft `ls -t ~/.academic-research/sessions/` ueber Bash auf.
    assert re.search(r"Bash\([^)]*sessions", allowed), (
        f"Keine Bash-Permission fuer ~/.academic-research/sessions/ "
        f"in allowed-tools: {allowed!r}"
    )


def test_frontmatter_has_skill_xlsx_permission():
    """allowed-tools muss Skill(xlsx) fuer die Excel-Generierung enthalten."""
    allowed = _frontmatter_field(COMMAND_FILE, "allowed-tools")
    # Schritt 3 aktiviert den vendorierten xlsx-Skill.
    assert "Skill(xlsx)" in allowed, (
        f"'Skill(xlsx)' nicht in allowed-tools: {allowed!r}"
    )


def test_frontmatter_keeps_read_and_write():
    """Read und Write bleiben weiterhin erlaubt (keine Regression)."""
    allowed = _frontmatter_field(COMMAND_FILE, "allowed-tools")
    assert "Read" in allowed, f"'Read' nicht in allowed-tools: {allowed!r}"
    assert "Write" in allowed, f"'Write' nicht in allowed-tools: {allowed!r}"


def test_frontmatter_description_nonempty():
    """description bleibt vorhanden und nicht leer (CI-Frontmatter-Coverage)."""
    desc = _frontmatter_field(COMMAND_FILE, "description")
    assert desc and len(desc.strip()) > 10, (
        f"description fehlt oder zu kurz: {desc!r}"
    )
