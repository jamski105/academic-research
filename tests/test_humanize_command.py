"""Smoke tests for /humanize command.

Tests command file existence, frontmatter, and pure-logic helpers.
No LLM calls required.
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
COMMAND_FILE = REPO_ROOT / "commands/humanize.md"


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
# Pure-logic helpers (inline — no import dependency on command markdown)
# ---------------------------------------------------------------------------

def derive_output_paths(input_path: str, mode: str) -> tuple[str, str]:
    """Return (humanized_path, diff_path) for a given input path."""
    p = Path(input_path)
    stem = p.stem
    parent = p.parent
    humanized = str(parent / f"{stem}.humanized.md")
    diff = str(parent / f"{stem}.diff.md")
    return humanized, diff


def voice_samples_path(slug: str) -> Path:
    """Return expected voice-samples directory for a project slug."""
    return Path.home() / ".academic-research" / "projects" / slug / "voice-samples"


def parse_mode(args: list[str]) -> str:
    """Parse --mode from args list; default is 'normal'."""
    try:
        idx = args.index("--mode")
        return args[idx + 1]
    except (ValueError, IndexError):
        return "normal"


SEVERITY_SECTIONS = ["## Critical", "## High", "## Medium", "## Low"]


def generate_diff_md(input_file: str, mode: str, voice_calibrated: bool) -> str:
    """Generate a minimal diff markdown template with all four severity sections."""
    voice_str = "ja" if voice_calibrated else "nein"
    lines = [
        f"# Humanize-Diff: {input_file}",
        "",
        f"Modus: {mode} | Voice-Kalibrierung: {voice_str} | Datum: 2026-05-08",
        "",
    ]
    for section in SEVERITY_SECTIONS:
        lines += [
            section,
            "",
            "| # | Original | Humanisiert |",
            "|---|----------|-------------|",
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Test 1 — command file exists
# ---------------------------------------------------------------------------

def test_command_file_exists():
    assert COMMAND_FILE.exists(), f"Missing: {COMMAND_FILE}"


# ---------------------------------------------------------------------------
# Test 2 — frontmatter contains Skill(humanizer-de) in allowed-tools
# ---------------------------------------------------------------------------

def test_command_frontmatter_has_skill():
    fm = _parse_frontmatter(COMMAND_FILE)
    allowed = fm.get("allowed-tools", "")
    assert "Skill(humanizer-de)" in str(allowed), (
        f"'Skill(humanizer-de)' not found in allowed-tools: {allowed!r}"
    )


# ---------------------------------------------------------------------------
# Test 3 — frontmatter has argument-hint
# ---------------------------------------------------------------------------

def test_command_frontmatter_argument_hint():
    fm = _parse_frontmatter(COMMAND_FILE)
    hint = fm.get("argument-hint", "")
    assert hint, "argument-hint missing or empty in frontmatter"
    assert "kapitel-pfad" in hint or "kapitel_pfad" in hint or "<" in hint, (
        f"argument-hint does not look like a path placeholder: {hint!r}"
    )


# ---------------------------------------------------------------------------
# Test 4 — output filenames for normal mode
# ---------------------------------------------------------------------------

def test_output_filenames_normal():
    humanized, diff = derive_output_paths("kapitel/3.md", "normal")
    assert humanized == "kapitel/3.humanized.md"
    assert diff == "kapitel/3.diff.md"


# ---------------------------------------------------------------------------
# Test 5 — output filenames for deep mode
# ---------------------------------------------------------------------------

def test_output_filenames_deep():
    humanized, diff = derive_output_paths("kapitel/3.md", "deep")
    assert humanized == "kapitel/3.humanized.md"
    assert diff == "kapitel/3.diff.md"


# ---------------------------------------------------------------------------
# Test 6 — diff markdown contains all four severity sections
# ---------------------------------------------------------------------------

def test_diff_md_structure():
    content = generate_diff_md("kapitel/3.md", "normal", False)
    for section in SEVERITY_SECTIONS:
        assert section in content, f"Missing section '{section}' in diff output"


# ---------------------------------------------------------------------------
# Test 7 — voice samples path derivation
# ---------------------------------------------------------------------------

def test_voice_samples_path():
    expected = Path.home() / ".academic-research/projects/meine-diss/voice-samples"
    result = voice_samples_path("meine-diss")
    assert result == expected


# ---------------------------------------------------------------------------
# Test 8 — default mode is 'normal'
# ---------------------------------------------------------------------------

def test_mode_default_is_normal():
    assert parse_mode(["kapitel/3.md"]) == "normal"


# ---------------------------------------------------------------------------
# Test 9 — command file documents default mode = normal
# ---------------------------------------------------------------------------

def test_command_documents_default_normal():
    text = COMMAND_FILE.read_text(encoding="utf-8")
    assert "normal" in text.lower(), "Command file does not mention 'normal' mode"
    # Must also document default explicitly
    assert "default" in text.lower(), "Command file does not document default mode"
