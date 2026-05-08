"""Tests for vendored humanizer-de skill artefacts.

Checks file presence, valid YAML frontmatter, and pattern count.
No LLM calls required.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
SKILL_MD = REPO_ROOT / "skills/humanizer-de/SKILL.md"
PATTERNS = REPO_ROOT / "skills/humanizer-de/references/patterns.md"
LICENSE_FILE = REPO_ROOT / "skills/humanizer-de/LICENSE"


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter delimited by '---' lines."""
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
# Test 1 — SKILL.md exists
# ---------------------------------------------------------------------------

def test_skill_md_exists():
    assert SKILL_MD.exists(), f"Missing: {SKILL_MD}"


# ---------------------------------------------------------------------------
# Test 2 — SKILL.md frontmatter valid
# ---------------------------------------------------------------------------

def test_skill_md_frontmatter_valid():
    fm = _parse_frontmatter(SKILL_MD)
    assert fm.get("name") == "humanizer-de", (
        f"Expected name='humanizer-de', got {fm.get('name')!r}"
    )
    allowed = fm.get("allowed-tools", [])
    assert "Read" in allowed, f"'Read' not in allowed-tools: {allowed}"


# ---------------------------------------------------------------------------
# Test 3 — patterns.md exists
# ---------------------------------------------------------------------------

def test_patterns_md_exists():
    assert PATTERNS.exists(), f"Missing: {PATTERNS}"


# ---------------------------------------------------------------------------
# Test 4 — patterns.md contains exactly 45 patterns
# ---------------------------------------------------------------------------

def test_patterns_contains_45_patterns():
    text = PATTERNS.read_text(encoding="utf-8")
    matches = re.findall(r"^#### \d+\.", text, re.MULTILINE)
    assert len(matches) == 45, (
        f"Expected 45 patterns (#### N. headings), found {len(matches)}"
    )


# ---------------------------------------------------------------------------
# Test 5 — LICENSE exists
# ---------------------------------------------------------------------------

def test_license_exists():
    assert LICENSE_FILE.exists(), f"Missing: {LICENSE_FILE}"


# ---------------------------------------------------------------------------
# Test 6 — LICENSE mentions upstream
# ---------------------------------------------------------------------------

def test_license_mentions_upstream():
    text = LICENSE_FILE.read_text(encoding="utf-8")
    assert "marmbiz/humanizer-de" in text, (
        "LICENSE does not mention upstream 'marmbiz/humanizer-de'"
    )
