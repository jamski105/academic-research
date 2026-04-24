"""Regression guard: Keine Title-Case-Skill-Namen in Prosa."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TITLE_CASE_NAMES = [
    "Abstract Generator",
    "Academic Context",
    "Chapter Writer",
    "Citation Extraction",
    "Literature Gap Analysis",
    "Source Quality Audit",
    "Research Question Refiner",
    "Submission Checker",
    "Style Evaluator",
    "Title Generator",
    "Methodology Advisor",
    "Plagiarism Check",
]
SCAN_DIRS = ["skills", "agents", "commands"]
SCAN_FILES = ["README.md"]


def _iter_files():
    for d in SCAN_DIRS:
        yield from (REPO_ROOT / d).rglob("*.md")
    for f in SCAN_FILES:
        yield REPO_ROOT / f


def test_no_title_case_skill_names_in_prose():
    patterns = [re.compile(rf"\b{re.escape(name)}\b") for name in TITLE_CASE_NAMES]
    violations = []
    for path in _iter_files():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for name, pattern in zip(TITLE_CASE_NAMES, patterns):
            for match in pattern.finditer(text):
                line_num = text[: match.start()].count("\n") + 1
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line_num}: '{name}'")
    assert not violations, (
        "Title-Case-Skill-Namen in Prosa gefunden:\n"
        + "\n".join(violations[:20])
        + (f"\n... und {len(violations) - 20} mehr" if len(violations) > 20 else "")
    )
