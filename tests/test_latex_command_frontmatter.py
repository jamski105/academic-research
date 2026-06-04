"""Regressions-Test fuer commands/latex.md Frontmatter (Issue #167).

Prueft, dass commands/latex.md:
- mit --- beginnt (YAML-Frontmatter vorhanden),
- ein schliessendes --- hat,
- ein nicht-leeres description-Feld besitzt,
- ein argument-hint-Feld besitzt,
- ein allowed-tools-Feld besitzt.

Spiegelt den CI-Job frontmatter-coverage und die Akzeptanzkriterien aus Issue #167.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
COMMAND_FILE = REPO_ROOT / "commands" / "latex.md"


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML-Frontmatter aus einer Markdown-Datei."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    return yaml.safe_load("\n".join(lines[1:end])) or {}


# ---------------------------------------------------------------------------
# Test 1 — Datei existiert
# ---------------------------------------------------------------------------

def test_command_file_exists():
    assert COMMAND_FILE.exists(), f"commands/latex.md fehlt: {COMMAND_FILE}"


# ---------------------------------------------------------------------------
# Test 2 — Datei beginnt mit --- (Frontmatter vorhanden)
# ---------------------------------------------------------------------------

def test_frontmatter_starts_with_dashes():
    text = COMMAND_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", (
        "commands/latex.md beginnt nicht mit '---' — Frontmatter fehlt"
    )


# ---------------------------------------------------------------------------
# Test 3 — schliessendes --- vorhanden
# ---------------------------------------------------------------------------

def test_frontmatter_has_closing_dashes():
    text = COMMAND_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0].strip() == "---", "Kein oeffnendes ---"
    closing = next((i for i, l in enumerate(lines[1:], start=1) if l.strip() == "---"), None)
    assert closing is not None, "commands/latex.md hat kein schliessendes --- im Frontmatter"


# ---------------------------------------------------------------------------
# Test 4 — nicht-leeres description-Feld
# ---------------------------------------------------------------------------

def test_frontmatter_description_not_empty():
    fm = _parse_frontmatter(COMMAND_FILE)
    desc = fm.get("description", "")
    assert desc, (
        f"commands/latex.md: description fehlt oder ist leer (Frontmatter: {fm!r})"
    )


# ---------------------------------------------------------------------------
# Test 5 — argument-hint vorhanden
# ---------------------------------------------------------------------------

def test_frontmatter_argument_hint():
    fm = _parse_frontmatter(COMMAND_FILE)
    hint = fm.get("argument-hint", "")
    assert hint, (
        f"commands/latex.md: argument-hint fehlt oder ist leer (Frontmatter: {fm!r})"
    )


# ---------------------------------------------------------------------------
# Test 6 — allowed-tools vorhanden (Issue #167 Akzeptanzkriterium)
# ---------------------------------------------------------------------------

def test_frontmatter_allowed_tools():
    fm = _parse_frontmatter(COMMAND_FILE)
    allowed = fm.get("allowed-tools", "")
    assert allowed, (
        f"commands/latex.md: allowed-tools fehlt oder ist leer (Frontmatter: {fm!r})"
    )


# ---------------------------------------------------------------------------
# Test 7 — disable-model-invocation: true (Issue #167 Akzeptanzkriterium)
# ---------------------------------------------------------------------------

def test_frontmatter_disable_model_invocation():
    """Gold-Standard commands/excel.md setzt disable-model-invocation: true."""
    fm = _parse_frontmatter(COMMAND_FILE)
    assert fm.get("disable-model-invocation") is True, (
        "commands/latex.md: disable-model-invocation: true fehlt "
        f"(Frontmatter: {fm!r})"
    )
