"""
Regressionstest fuer Issue #172.

commands/pickup.md fehlten `allowed-tools` und `argument-hint`,
commands/setup.md fehlte `argument-hint`.

Ohne `argument-hint` zeigt Claude Code keinen Argument-Vorschlag im UI;
ohne `allowed-tools` laeuft pickup ungebremst (Permission-Prompts statt Whitelist).

Reine Unit-Tests auf das Frontmatter — kein LLM-/Netzwerk-Call.

Hinweis: Das Frontmatter wird zeilenbasiert geparst (wie der CI-Check
`frontmatter-coverage` in .github/workflows/ci.yml), nicht via yaml.safe_load.
Die `argument-hint`-Werte beginnen konventionsgemaess mit `[` und enthalten
`<...>`/`|` (siehe commands/excel.md, search.md, score.md) — das ist gueltige
Plugin-Konvention, aber kein gueltiges YAML-Flow-Sequence.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PICKUP_FILE = REPO_ROOT / "commands/pickup.md"
SETUP_FILE = REPO_ROOT / "commands/setup.md"


def _parse_frontmatter(path: Path) -> dict:
    """Zeilenbasiertes Frontmatter-Parsing (analog CI-frontmatter-coverage).

    Liest jedes 'key: value'-Paar aus dem '---'-begrenzten Block. Robust
    gegenueber argument-hint-Werten mit '[', '<', '|' (kein YAML-Flow).
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}
    fm: dict = {}
    for line in lines[1:end]:
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


# ---------------------------------------------------------------------------
# Command-Dateien existieren
# ---------------------------------------------------------------------------

def test_pickup_file_exists():
    assert PICKUP_FILE.exists(), f"Missing: {PICKUP_FILE}"


def test_setup_file_exists():
    assert SETUP_FILE.exists(), f"Missing: {SETUP_FILE}"


# ---------------------------------------------------------------------------
# pickup.md — allowed-tools vorhanden mit Read/Write/Bash(python3 *)
# ---------------------------------------------------------------------------

def test_pickup_allowed_tools_present():
    fm = _parse_frontmatter(PICKUP_FILE)
    allowed = str(fm.get("allowed-tools", ""))
    assert allowed, "pickup.md: allowed-tools fehlt oder leer"
    for tool in ("Read", "Write", "Bash(python3 *)"):
        assert tool in allowed, (
            f"pickup.md: '{tool}' nicht in allowed-tools: {allowed!r}"
        )


# ---------------------------------------------------------------------------
# pickup.md — argument-hint vorhanden mit --filter / --output
# ---------------------------------------------------------------------------

def test_pickup_argument_hint_present():
    fm = _parse_frontmatter(PICKUP_FILE)
    hint = str(fm.get("argument-hint", ""))
    assert hint, "pickup.md: argument-hint fehlt oder leer"
    assert "--filter" in hint, f"pickup.md: '--filter' fehlt in argument-hint: {hint!r}"
    assert "--output" in hint, f"pickup.md: '--output' fehlt in argument-hint: {hint!r}"


# ---------------------------------------------------------------------------
# pickup.md — bestehende Felder bleiben erhalten
# ---------------------------------------------------------------------------

def test_pickup_description_nonempty():
    fm = _parse_frontmatter(PICKUP_FILE)
    desc = str(fm.get("description", "")).strip()
    assert len(desc) > 10, f"pickup.md: description fehlt oder zu kurz: {desc!r}"


# ---------------------------------------------------------------------------
# setup.md — argument-hint vorhanden mit --uni / --skip-browser / --enable-scihub
# ---------------------------------------------------------------------------

def test_setup_argument_hint_present():
    fm = _parse_frontmatter(SETUP_FILE)
    hint = str(fm.get("argument-hint", ""))
    assert hint, "setup.md: argument-hint fehlt oder leer"
    for token in ("--uni", "--skip-browser", "--enable-scihub"):
        assert token in hint, (
            f"setup.md: '{token}' fehlt in argument-hint: {hint!r}"
        )


# ---------------------------------------------------------------------------
# setup.md — bestehende Felder bleiben erhalten
# ---------------------------------------------------------------------------

def test_setup_allowed_tools_preserved():
    fm = _parse_frontmatter(SETUP_FILE)
    allowed = str(fm.get("allowed-tools", ""))
    assert "Bash(python3 *)" in allowed, (
        f"setup.md: allowed-tools verloren: {allowed!r}"
    )


def test_setup_description_nonempty():
    fm = _parse_frontmatter(SETUP_FILE)
    desc = str(fm.get("description", "")).strip()
    assert len(desc) > 10, f"setup.md: description fehlt oder zu kurz: {desc!r}"
