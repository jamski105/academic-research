"""Tests for PRISMA-Flow (#92):
  - render_flow.py renders correct Mermaid block from counters
  - Counters shape (n_identified, n_after_dedup, n_excluded_screening,
    n_excluded_eligibility, n_included)
  - 100 → 60 → 30 → 12 → 8 pipeline produces correct Mermaid
  - prisma-flow skill files exist
  - prisma-checklist.md has 27 items
  - skill_sizes.json contains prisma-flow entry
"""

import json
import sys
from pathlib import Path

# Adjust sys.path to find render_flow
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "prisma-flow" / "scripts"))


def _get_counters(n_identified, n_after_dedup, n_excluded_screening,
                  n_excluded_eligibility, n_included):
    return {
        "n_identified": n_identified,
        "n_after_dedup": n_after_dedup,
        "n_excluded_screening": n_excluded_screening,
        "n_excluded_eligibility": n_excluded_eligibility,
        "n_included": n_included,
    }


# ---------------------------------------------------------------------------
# render_flow.py tests
# ---------------------------------------------------------------------------

def test_render_flow_returns_mermaid_block():
    """render_flow produces a Mermaid code block."""
    from render_flow import render_prisma_flow
    counters = _get_counters(100, 60, 30, 12, 8)
    result = render_prisma_flow(counters)
    assert "```mermaid" in result
    assert "```" in result[result.index("```mermaid") + 9:]


def test_render_flow_contains_all_counts():
    """All counter values appear in the rendered Mermaid diagram."""
    from render_flow import render_prisma_flow
    counters = _get_counters(100, 60, 30, 12, 8)
    result = render_prisma_flow(counters)
    assert "100" in result
    assert "60" in result
    assert "30" in result
    assert "12" in result
    assert "8" in result


def test_render_flow_pipeline_100_60_30_12_8():
    """Standard pipeline: 100 identified → 60 dedup → 30 screening → 12 eligibility → 8 included."""
    from render_flow import render_prisma_flow
    counters = _get_counters(100, 60, 30, 12, 8)
    result = render_prisma_flow(counters)
    # Mermaid block must be present
    assert "```mermaid" in result
    # flowchart or graph direction marker
    assert any(marker in result for marker in ["flowchart", "graph TD", "graph LR"])
    # n_identified shown
    assert "100" in result
    # n_included shown
    assert "8" in result


def test_render_flow_excluded_screening_count():
    """Excluded screening = n_after_dedup - n_excluded_eligibility - n_included (or explicit)."""
    from render_flow import render_prisma_flow
    # 60 after dedup; 30 excluded at screening; 12 go to eligibility; 12-8=4 excluded at eligibility
    counters = _get_counters(100, 60, 30, 12, 4)
    result = render_prisma_flow(counters)
    assert "30" in result
    assert "4" in result


def test_render_flow_custom_output_path(tmp_path):
    """render_flow can write output to a file path."""
    from render_flow import render_prisma_flow
    counters = _get_counters(100, 60, 30, 12, 8)
    out_file = tmp_path / "flow.md"
    render_prisma_flow(counters, output_path=str(out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert "```mermaid" in content


# ---------------------------------------------------------------------------
# Skill file existence tests
# ---------------------------------------------------------------------------

def test_skill_md_exists():
    """skills/prisma-flow/SKILL.md must exist."""
    skill_md = REPO_ROOT / "skills" / "prisma-flow" / "SKILL.md"
    assert skill_md.exists(), f"Missing: {skill_md}"


def test_prisma_checklist_exists():
    """skills/prisma-flow/references/prisma-checklist.md must exist."""
    checklist = REPO_ROOT / "skills" / "prisma-flow" / "references" / "prisma-checklist.md"
    assert checklist.exists(), f"Missing: {checklist}"


def test_prisma_checklist_has_27_items():
    """prisma-checklist.md must have at least 27 checklist items."""
    checklist = REPO_ROOT / "skills" / "prisma-flow" / "references" / "prisma-checklist.md"
    content = checklist.read_text(encoding="utf-8")
    # Count checkbox items: lines starting with "- [ ]" or "- [x]"
    items = [l for l in content.splitlines() if l.strip().startswith(("- [ ]", "- [x]", "* [ ]", "* [x]"))]
    assert len(items) >= 27, f"Expected >=27 checklist items, got {len(items)}"


def test_render_flow_script_exists():
    """skills/prisma-flow/scripts/render_flow.py must exist."""
    script = REPO_ROOT / "skills" / "prisma-flow" / "scripts" / "render_flow.py"
    assert script.exists(), f"Missing: {script}"


# ---------------------------------------------------------------------------
# Documented Python-API import path (#225)
# ---------------------------------------------------------------------------

def _extract_python_blocks(markdown: str):
    """Return the contents of all ```python fenced code blocks."""
    blocks = []
    lines = markdown.splitlines()
    in_block = False
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_block and stripped.startswith("```python"):
            in_block = True
            buf = []
            continue
        if in_block and stripped.startswith("```"):
            in_block = False
            blocks.append("\n".join(buf))
            continue
        if in_block:
            buf.append(line)
    return blocks


def test_skill_md_documents_no_broken_package_import():
    """SKILL.md must not document the non-importable `skills.prisma_flow` path (#225).

    The directory is `skills/prisma-flow` (hyphen) without `__init__.py`, so
    `from skills.prisma_flow.scripts.render_flow import ...` raises
    ModuleNotFoundError. The documented import must use the actual module name.
    """
    skill_md = REPO_ROOT / "skills" / "prisma-flow" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    assert "skills.prisma_flow" not in content, (
        "SKILL.md documents the non-importable package path 'skills.prisma_flow' "
        "(directory has a hyphen and no __init__.py)"
    )


def test_skill_md_python_api_import_is_executable():
    """The documented Python-API import block in SKILL.md must actually work (#225)."""
    skill_md = REPO_ROOT / "skills" / "prisma-flow" / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")

    import_lines = [
        line.strip()
        for block in _extract_python_blocks(content)
        for line in block.splitlines()
        if "render_prisma_flow" in line and line.strip().startswith(("from ", "import "))
    ]
    assert import_lines, "SKILL.md no longer documents a render_prisma_flow import"

    # Execute the documented import statement(s) with the scripts dir on the path
    # (mirrors the ${CLAUDE_PLUGIN_ROOT}/skills/prisma-flow/scripts convention).
    scripts_dir = REPO_ROOT / "skills" / "prisma-flow" / "scripts"
    namespace: dict = {}
    for stmt in import_lines:
        prev = list(sys.path)
        sys.path.insert(0, str(scripts_dir))
        try:
            exec(compile(stmt, "<skill-md>", "exec"), namespace)
        finally:
            sys.path[:] = prev
    assert callable(namespace.get("render_prisma_flow"))


# ---------------------------------------------------------------------------
# skill_sizes.json test
# ---------------------------------------------------------------------------

def test_skill_sizes_has_prisma_flow():
    """tests/baselines/skill_sizes.json must have a prisma-flow entry."""
    sizes_path = REPO_ROOT / "tests" / "baselines" / "skill_sizes.json"
    sizes = json.loads(sizes_path.read_text(encoding="utf-8"))
    assert "prisma-flow" in sizes, "skill_sizes.json missing prisma-flow entry"
    assert sizes["prisma-flow"] > 0
