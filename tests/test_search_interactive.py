"""Tests for Two-Phase Research Mode / Human-in-the-Loop (#105):
  - scripts/search.py exposes PRISMA counters
  - search.py --interactive flag handling via run_interactive_phase1()
  - Phase 1 returns preview dict with top papers + approval_options
  - --interactive=off behaves like today (no gate)
  - commands/search.md documents --interactive flag
  - skills/chapter-writer/SKILL.md documents Approval-Gate
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# ---------------------------------------------------------------------------
# PRISMA counter tracking in search.py
# ---------------------------------------------------------------------------

def test_search_has_prisma_counter_keys():
    """search.py must expose PRISMA_COUNTER_KEYS list."""
    from search import PRISMA_COUNTER_KEYS
    required = {"n_identified", "n_after_dedup", "n_excluded_screening",
                "n_excluded_eligibility", "n_included"}
    assert required.issubset(set(PRISMA_COUNTER_KEYS))


def test_build_prisma_counters_basic():
    """build_prisma_counters() returns dict with all required keys and correct values."""
    from search import build_prisma_counters
    counters = build_prisma_counters(
        n_identified=100,
        n_after_dedup=60,
        n_excluded_screening=30,
        n_excluded_eligibility=12,
        n_included=8,
    )
    assert counters["n_identified"] == 100
    assert counters["n_after_dedup"] == 60
    assert counters["n_excluded_screening"] == 30
    assert counters["n_excluded_eligibility"] == 12
    assert counters["n_included"] == 8


def test_build_prisma_counters_defaults_zero():
    """build_prisma_counters() defaults missing values to 0."""
    from search import build_prisma_counters
    counters = build_prisma_counters()
    for key in ("n_identified", "n_after_dedup", "n_excluded_screening",
                "n_excluded_eligibility", "n_included"):
        assert counters[key] == 0


def test_save_prisma_counters(tmp_path):
    """save_prisma_counters() writes counters.json to session_dir."""
    from search import build_prisma_counters, save_prisma_counters
    counters = build_prisma_counters(
        n_identified=100, n_after_dedup=60,
        n_excluded_screening=30, n_excluded_eligibility=12, n_included=8,
    )
    save_prisma_counters(str(tmp_path), counters)
    counters_file = tmp_path / "prisma_counters.json"
    assert counters_file.exists()
    import json
    loaded = json.loads(counters_file.read_text())
    assert loaded["n_identified"] == 100
    assert loaded["n_included"] == 8


# ---------------------------------------------------------------------------
# Interactive Phase 1
# ---------------------------------------------------------------------------

def test_search_has_run_interactive_phase1():
    """search.py must expose run_interactive_phase1()."""
    from search import run_interactive_phase1
    assert callable(run_interactive_phase1)


def test_run_interactive_phase1_returns_preview():
    """Phase 1 returns preview dict with top_papers list and approval_options."""
    from search import run_interactive_phase1

    sample_papers = [
        {
            "title": f"Paper {i}",
            "year": 2020 + i,
            "authors": ["Author A"],
            "score": 0.9 - i * 0.05,
            "abstract": f"Abstract for paper {i}",
        }
        for i in range(20)
    ]

    result = run_interactive_phase1(
        papers=sample_papers,
        query="DevOps Governance",
        n_preview=5,
    )

    assert "top_papers" in result
    assert len(result["top_papers"]) <= 10
    assert len(result["top_papers"]) >= 5
    assert "approval_options" in result
    # Must have the required 4 approval options
    options_text = str(result["approval_options"])
    assert "Weiter" in options_text
    assert "Anders" in options_text or "formulieren" in options_text
    assert "Quellen" in options_text or "Mehr" in options_text


def test_run_interactive_phase1_top_papers_ordered():
    """Phase 1 top papers must be ordered by score descending."""
    from search import run_interactive_phase1

    papers = [
        {"title": "Low", "score": 0.3, "year": 2020, "authors": [], "abstract": ""},
        {"title": "High", "score": 0.9, "year": 2021, "authors": [], "abstract": ""},
        {"title": "Mid", "score": 0.6, "year": 2019, "authors": [], "abstract": ""},
    ]
    result = run_interactive_phase1(papers=papers, query="test", n_preview=3)
    titles = [p["title"] for p in result["top_papers"]]
    assert titles[0] == "High"
    assert titles[-1] == "Low"


def test_run_interactive_phase1_no_papers():
    """Phase 1 handles empty paper list gracefully."""
    from search import run_interactive_phase1
    result = run_interactive_phase1(papers=[], query="test")
    assert "top_papers" in result
    assert result["top_papers"] == []


# ---------------------------------------------------------------------------
# commands/search.md documentation
# ---------------------------------------------------------------------------

def test_search_md_has_interactive_flag():
    """commands/search.md must document --interactive flag."""
    search_md = REPO_ROOT / "commands" / "search.md"
    content = search_md.read_text(encoding="utf-8")
    assert "--interactive" in content, "commands/search.md missing --interactive flag"


def test_search_md_interactive_off_documented():
    """commands/search.md must mention --interactive=off default."""
    search_md = REPO_ROOT / "commands" / "search.md"
    content = search_md.read_text(encoding="utf-8")
    assert "--interactive=off" in content or "interactive=off" in content.lower(), \
        "commands/search.md must document --interactive=off as default"


# ---------------------------------------------------------------------------
# chapter-writer SKILL.md approval gate
# ---------------------------------------------------------------------------

def test_chapter_writer_has_approval_gate():
    """skills/chapter-writer/SKILL.md must reference Approval-Gate."""
    skill_md = REPO_ROOT / "skills" / "chapter-writer" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    assert "Approval" in content or "approval" in content, \
        "chapter-writer/SKILL.md missing Approval-Gate documentation"


def test_chapter_writer_has_interactive_section():
    """skills/chapter-writer/SKILL.md must mention --interactive or interactive mode."""
    skill_md = REPO_ROOT / "skills" / "chapter-writer" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    assert "interactive" in content.lower(), \
        "chapter-writer/SKILL.md missing interactive mode documentation"
