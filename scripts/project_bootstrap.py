"""Project bootstrap for academic-research plugin.

Called at the end of setup.sh. Detects whether the current working directory
should be initialized as a facharbeit workspace, and if so, lays down the
minimal project structure and optionally migrates existing memory-based
context into project-local files.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

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


BOOTSTRAP_DIR = Path(__file__).parent / "bootstrap"

SUBDIRS = ("kapitel", "literatur", "pdfs")


def create_structure(cwd: Path, stub: bool) -> None:
    """Lay down the project skeleton, skipping files that already exist.

    Idempotent — never overwrites. With stub=True, copies academic_context.stub.md
    as academic_context.md (only if absent). With stub=False (idempotent re-run
    path from main), only nachzieht CLAUDE.md and the subdirs. Always ensures
    kapitel/, literatur/, pdfs/ exist with .gitkeep.
    """
    if stub and not (cwd / "academic_context.md").exists():
        stub_src = BOOTSTRAP_DIR / "academic_context.stub.md"
        (cwd / "academic_context.md").write_text(stub_src.read_text(encoding="utf-8"))

    claude_md = cwd / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text((BOOTSTRAP_DIR / "CLAUDE.md").read_text(encoding="utf-8"))

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
    fragment = (BOOTSTRAP_DIR / "gitignore.fragment").read_text(encoding="utf-8")
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


MEMORY_FILE_NAMES = ("academic_context.md", "literature_state.md", "writing_state.md")


def _cwd_slug(cwd: Path) -> str:
    """Claude replaces path separators with hyphens; match that convention."""
    return str(cwd).replace("/", "-")


def find_memory_files(home: Path, cwd: Path) -> list[Path]:
    """Return memory-side context files that exist for this cwd, in a stable order."""
    memory_dir = home / ".claude" / "projects" / _cwd_slug(cwd) / "memory"
    if not memory_dir.exists():
        return []
    return [memory_dir / name for name in MEMORY_FILE_NAMES if (memory_dir / name).exists()]


def copy_memory_files(sources: list[Path], cwd: Path) -> None:
    """Copy each source into cwd under its basename. Never overwrite existing targets."""
    for src in sources:
        target = cwd / src.name
        if target.exists():
            continue
        target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def init_git_repo(cwd: Path, env: Optional[dict] = None) -> bool:
    """git init + initial commit. Returns True on success, False on graceful skip.

    Args:
        cwd: Directory to initialise as a git repo.
        env: Optional environment dict passed to subprocess (useful in tests to
             supply GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL without a global gitconfig).
    """
    if shutil.which("git") is None:
        print("ℹ️  git nicht im PATH — git-Repo übersprungen")
        return False
    try:
        subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True, env=env)
        subprocess.run(
            ["git", "add", "academic_context.md", "CLAUDE.md", ".gitignore"],
            cwd=cwd,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: initial project setup via academic-research"],
            cwd=cwd,
            check=True,
            capture_output=True,
            env=env,
        )
        print(f"✅ git-Repo initialisiert und erster Commit angelegt: {cwd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  git init fehlgeschlagen: {e}")
        return False


def _prompt_yes_no(question: str, default_yes: bool = False) -> bool:
    """Interactive y/n prompt. Returns default_yes on non-interactive stdin."""
    import sys
    if not sys.stdin.isatty():
        return default_yes
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{question} {suffix} ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "yes", "j", "ja")


def main() -> None:
    cwd = Path.cwd()
    home = Path.home()
    mode = detect_mode(cwd)

    if mode == "code_repo" or mode == "skip":
        return

    if mode == "idempotent":
        # Facharbeit-Ordner bereits vorhanden — fehlende Artefakte nachziehen, keine Frage
        create_structure(cwd, stub=False)
        merge_gitignore(cwd)
        print(f"✅ Facharbeit-Arbeitsordner: Artefakte aktualisiert ({cwd})")
        return

    # mode == "fresh"
    if not _prompt_yes_no("Hier einen Facharbeit-Arbeitsordner initialisieren?", default_yes=False):
        return

    memory_files = find_memory_files(home, cwd)
    do_migrate = False
    if memory_files:
        names = ", ".join(p.name for p in memory_files)
        do_migrate = _prompt_yes_no(
            f"Bestehender Kontext in Claude-Memory gefunden ({names}). Kopieren?",
            default_yes=True,
        )

    create_structure(cwd, stub=not do_migrate)
    if do_migrate:
        copy_memory_files(memory_files, cwd)
        print(f"✅ Memory-Kontext kopiert nach {cwd} (Original bleibt als Backup)")
    merge_gitignore(cwd)
    print(f"✅ Facharbeit-Arbeitsordner initialisiert: {cwd}")
    if _prompt_yes_no("Git aktivieren?", default_yes=False):
        init_git_repo(cwd)


if __name__ == "__main__":
    main()
