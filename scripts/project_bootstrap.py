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
