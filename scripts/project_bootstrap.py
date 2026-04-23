"""Project bootstrap for academic-research plugin.

Called at the end of setup.sh. Detects whether the current working directory
should be initialized as a facharbeit workspace, and if so, lays down the
minimal project structure and optionally migrates existing memory-based
context into project-local files.
"""
from __future__ import annotations

from pathlib import Path

CODE_REPO_SIGNATURES = (
    "package.json",
    "Cargo.toml",
    "pyproject.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    ".claude-plugin/plugin.json",
)


def detect_mode(cwd: Path) -> str:
    """Classify the current directory for bootstrap purposes.

    Returns one of:
      - "idempotent": academic_context.md already exists — fill missing artefacts, no prompt
      - "code_repo": looks like source code — skip bootstrap entirely
      - "fresh": empty or dot-files only — prompt user
      - "skip": non-empty unknown directory — skip without prompting
    """
    if (cwd / "academic_context.md").exists():
        return "idempotent"
    for sig in CODE_REPO_SIGNATURES:
        if (cwd / sig).exists():
            return "code_repo"
    visible = [p for p in cwd.iterdir() if not p.name.startswith(".")]
    if not visible:
        return "fresh"
    return "skip"


TEMPLATES_DIR = Path(__file__).parent / "templates"

SUBDIRS = ("kapitel", "literatur", "pdfs")


def create_structure(cwd: Path, stub: bool) -> None:
    """Lay down the project skeleton, skipping files that already exist.

    Idempotent — never overwrites. With stub=True, copies academic_context.stub.md
    as academic_context.md (only if absent). With stub=False (idempotent re-run
    path from main), only nachzieht CLAUDE.md and the subdirs. Always ensures
    kapitel/, literatur/, pdfs/ exist with .gitkeep.
    """
    if stub and not (cwd / "academic_context.md").exists():
        stub_src = TEMPLATES_DIR / "academic_context.stub.md"
        (cwd / "academic_context.md").write_text(stub_src.read_text(encoding="utf-8"))

    claude_md = cwd / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text((TEMPLATES_DIR / "CLAUDE.md").read_text(encoding="utf-8"))

    for sub in SUBDIRS:
        (cwd / sub).mkdir(parents=True, exist_ok=True)
        gitkeep = cwd / sub / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()


def merge_gitignore(cwd: Path) -> None:
    """Ensure every line from the gitignore fragment is present in .gitignore.

    Preserves existing content; appends only missing lines, in fragment order.
    Creates the file if it doesn't exist.
    """
    fragment = (TEMPLATES_DIR / "gitignore.fragment").read_text(encoding="utf-8")
    fragment_lines = [ln for ln in fragment.splitlines() if ln.strip()]

    target = cwd / ".gitignore"
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        existing_lines = existing.splitlines()
    else:
        existing = ""
        existing_lines = []

    missing = [ln for ln in fragment_lines if ln not in existing_lines]
    if not missing:
        return

    separator = "" if existing.endswith("\n") or not existing else "\n"
    target.write_text(existing + separator + "\n".join(missing) + "\n", encoding="utf-8")
