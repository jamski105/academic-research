"""Regressions-Guard fuer Issue #206 — README-Skills-Coverage.

Die README-Skills-Tabelle (Sektion "Skills-Uebersicht") muss JEDEN
plugin-eigenen Skill (skills/*/SKILL.md, ohne reine Vendor-Skills wie xlsx)
dokumentieren. Ausserdem muessen Badge und TOC-Eintrag den korrekten Count
(28 inkl. xlsx-Vendor) tragen.

Befund vor dem Fix: book-handler, cluster-visualizer, latex-export und
notebook-bundle fehlten komplett, Badge stand auf 23+, TOC auf "23+".
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
SKILLS_DIR = REPO_ROOT / "skills"

# Reiner Vendor-Skill (Claude-eigener document-skill), nicht plugin-eigen.
VENDORED_SKILLS = {"xlsx", "_common"}

# Skills, deren Fehlen Issue #206 explizit benennt.
ISSUE_206_SKILLS = {
    "book-handler",
    "cluster-visualizer",
    "latex-export",
    "notebook-bundle",
}


def _plugin_own_skills() -> set[str]:
    return {
        p.parent.name
        for p in SKILLS_DIR.glob("*/SKILL.md")
        if p.parent.name not in VENDORED_SKILLS
    }


def test_all_plugin_skills_documented_in_readme():
    text = README.read_text(encoding="utf-8")
    # Tabellen-Zeilen referenzieren Skills als `name` in Backticks.
    missing = sorted(s for s in _plugin_own_skills() if f"`{s}`" not in text)
    assert not missing, (
        "Plugin-eigene Skills fehlen in der README-Skills-Tabelle: "
        + ", ".join(missing)
    )


def test_issue_206_named_skills_documented():
    text = README.read_text(encoding="utf-8")
    missing = sorted(s for s in ISSUE_206_SKILLS if f"`{s}`" not in text)
    assert not missing, (
        "Von Issue #206 benannte Skills weiterhin undokumentiert: "
        + ", ".join(missing)
    )


def test_skills_badge_count_is_28():
    text = README.read_text(encoding="utf-8")
    assert re.search(r"img\.shields\.io/badge/skills-28", text), (
        "Skills-Badge muss auf 'skills-28' stehen (28 SKILL.md inkl. xlsx-Vendor)."
    )


def test_toc_entry_says_28_selbstaktivierend():
    text = README.read_text(encoding="utf-8")
    assert "Skills (28 selbstaktivierend)" in text, (
        "TOC-Eintrag muss 'Skills (28 selbstaktivierend)' lauten."
    )
