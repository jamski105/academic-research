# E5 Project-Bootstrap + Context-Migration (v5.3.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `/academic-research:setup` into a project-aware bootstrap that lays down a git-versionable academic workspace, generates a `CLAUDE.md` with skill-delegation hints, and migrates the per-thesis context from Claude-Memory to project-local files — shipped as v5.3.0 (breaking change for memory-based users).

**Architecture:** Detection and bootstrap logic live in a new `scripts/project_bootstrap.py` (testable Python, not inline bash). `setup.sh` becomes a thin orchestrator that appends `python3 project_bootstrap.py` at the end. All 13 skills and 1 agent get their `academic_context.md`-references rewritten from "memory" to "project-local" — a mechanical but skill-specific text migration. A migration helper in the bootstrap detects existing Memory files and offers a one-time copy.

**Tech Stack:** Python 3.10+, bash (setup.sh), pytest (new tests), markdown (all SKILL.md + docs).

---

## Spec reference

`docs/superpowers/specs/2026-04-23-e5-project-bootstrap-design.md`

## File Structure

**Created:**

| Path | Responsibility |
|---|---|
| `scripts/templates/academic_context.stub.md` | Template stub with TODO placeholders. Copied verbatim into fresh projects. |
| `scripts/templates/CLAUDE.md` | Constant CLAUDE.md content (skill delegation hints, conventions). Copied verbatim. |
| `scripts/templates/gitignore.fragment` | Lines to merge into existing `.gitignore` or create fresh. |
| `scripts/project_bootstrap.py` | All detection, creation, and migration logic. Testable. Single entry point: `main()`. |
| `tests/test_project_bootstrap.py` | Pytest tests for detection, stub creation, gitignore merging, migration helper. |

**Modified:**

| Path | Change |
|---|---|
| `scripts/setup.sh` | Append `python3 "$SCRIPT_DIR/project_bootstrap.py"` as step 7. |
| `commands/setup.md` | Document new behavior (detection, bootstrap, migration). |
| `skills/academic-context/SKILL.md` | Rewrite memory-language; writer-skill, primary migration. |
| `skills/{12 others}/SKILL.md` | Rewrite memory-references to project-local path. |
| `agents/query-generator.md` | Rewrite `academic_context.md`-references to project-local path. |
| `README.md` | New "Overhead reduzieren"-section; update Quickstart. |
| `CHANGELOG.md` | New `[5.3.0]` block with BREAKING note + migration steps. |
| `.claude-plugin/plugin.json` | Version `5.2.0` → `5.3.0`. |
| `.claude-plugin/marketplace.json` | Version `5.2.0` → `5.3.0`. |

## Migration rules (shared by all skill-migration tasks)

All SKILL.md files and the `query-generator.md` agent must stop referring to "Memory" / "Claude-Memory" as the storage location of `academic_context.md`, `literature_state.md`, `writing_state.md`. The files now live in the current working directory. Apply these rules consistently:

| Before | After |
|---|---|
| `## Memory-Dateien` | `## Kontext-Dateien` |
| `aus dem Memory` | `aus dem Projekt-Ordner` |
| `ins Memory schreiben` | `in den Projekt-Ordner schreiben` |
| `Claude-Memory` | `Projekt-Ordner` (wenn im Fließtext) |
| `Memory-Precondition` | `Kontext-Datei-Precondition` |
| `academic_context.md im Memory` | `academic_context.md im Projekt-Ordner` |
| `Lies academic_context.md` *(ohne Pfad)* | `Lies ./academic_context.md` *(explizit relativ)* |

If a SKILL.md references Memory-semantics that don't map 1:1 (e.g., "Claude erinnert sich sessionübergreifend"), replace with "ist git-versionierbar und wächst mit der Arbeit mit." Keep the skill's overall structure intact; don't rewrite anything beyond the memory-language.

---

## Phase 1 — Templates

### Task 1: Create `academic_context.stub.md` template

**Files:**
- Create: `scripts/templates/academic_context.stub.md`

- [ ] **Step 1: Create template directory**

```bash
mkdir -p scripts/templates
```

- [ ] **Step 2: Write the stub template**

File: `scripts/templates/academic_context.stub.md`

```markdown
---
name: academic-context
description: Akademischer Kontext der aktuellen Abschlussarbeit
type: project
---

## Profil
- Universität: TODO (Default: Leibniz FH Hannover)
- Studiengang: TODO
- Zitationsstil: TODO (Default: APA7)
- Sprache: TODO (Default: Deutsch)

## Arbeit
- Typ: TODO (Bachelorarbeit/Masterarbeit/Hausarbeit/Facharbeit)
- Thema: TODO
- Forschungsfrage: TODO
- Methodik: TODO
- Betreuer: TODO
- Abgabetermin: TODO

## Gliederung
TODO

## Schlüsselkonzepte
TODO

## Fortschritt
- [ ] Thema festgelegt
- [ ] Forschungsfrage formuliert
- [ ] Gliederung steht
- [ ] Literatur gesammelt
- [ ] Kapitel geschrieben
- [ ] Abgabe
```

- [ ] **Step 3: Verify file exists and is readable**

Run:
```bash
test -f scripts/templates/academic_context.stub.md && head -3 scripts/templates/academic_context.stub.md
```
Expected: Shows the frontmatter lines `---`, `name: academic-context`, `description: ...`

- [ ] **Step 4: Commit**

```bash
git add scripts/templates/academic_context.stub.md
git commit -m "feat(e5): add academic_context.md stub template"
```

---

### Task 2: Create `CLAUDE.md` template

**Files:**
- Create: `scripts/templates/CLAUDE.md`

- [ ] **Step 1: Write the CLAUDE.md template**

File: `scripts/templates/CLAUDE.md`

```markdown
# Facharbeit — Arbeitsordner

Dieser Ordner enthält eine akademische Arbeit, die mit dem `academic-research`-Plugin bearbeitet wird.

## Single Source of Truth

`./academic_context.md` — Thema, Gliederung, Forschungsfrage, Methodik, Fortschritt.
Bei jeder inhaltlichen Frage zur Arbeit zuerst lesen.

## Delegations-Hinweise

Verfügbare Skills (aktivieren sich durch Konversation — nicht manuell aufrufen):

| Thema | Zuständiger Skill |
|-------|-------------------|
| Thema/Gliederung pflegen | `academic-context` |
| Forschungsfrage schärfen | `research-question-refiner` |
| Methodenwahl begründen | `methodology-advisor` |
| Exposé/Gliederungsentwurf | `advisor` |
| Kapitel schreiben | `chapter-writer` |
| Zitate aus PDFs extrahieren | `citation-extraction` |
| Quellenqualität prüfen | `source-quality-audit` |
| Literatur-Lücken finden | `literature-gap-analysis` |
| KI-Stil-Check / Textqualität | `style-evaluator` |
| Paraphrasen-Check | `plagiarism-check` |
| Formale Abgabe-Prüfung | `submission-checker` |
| Titelvorschläge | `title-generator` |
| Abstract/Management Summary | `abstract-generator` |

Slash-Commands (explizit aufrufen):

- `/academic-research:search "query"` — Literatur über 7 APIs
- `/academic-research:score` — Re-Scoring vorhandener Paper
- `/academic-research:excel` — Excel-Export
- `/academic-research:history` — Vergangene Sessions

## Ordner-Konventionen

- `kapitel/` — Kapitel-Drafts
- `literatur/` — Notizen, Exzerpte, Synthese
- `pdfs/` — User-eigene PDFs (nicht committen — ist in `.gitignore`)

Vom Plugin gedownloadete Papers liegen global in `~/.academic-research/pdfs/` (Cache, nicht im Projekt).

## Regel: Keine Fabrikation

Zitate und Paraphrasen nur aus real vorhandenen Quellen. Wenn `citation-extraction` eine Stelle nicht findet, lieber sagen "nicht auffindbar" als raten. Quellenangaben immer verifizieren, bevor sie im Text landen.
```

- [ ] **Step 2: Verify file exists**

Run:
```bash
test -f scripts/templates/CLAUDE.md && wc -l scripts/templates/CLAUDE.md
```
Expected: Prints line count (around 45 lines).

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/CLAUDE.md
git commit -m "feat(e5): add CLAUDE.md template for generated project-level guidance"
```

---

### Task 3: Create `.gitignore` fragment

**Files:**
- Create: `scripts/templates/gitignore.fragment`

- [ ] **Step 1: Write the fragment**

File: `scripts/templates/gitignore.fragment`

```
# academic-research
pdfs/*
!pdfs/.gitkeep
.DS_Store
.claude/settings.local.json
```

- [ ] **Step 2: Verify**

Run:
```bash
cat scripts/templates/gitignore.fragment
```
Expected: Five lines as shown above (comment + 4 rules).

- [ ] **Step 3: Commit**

```bash
git add scripts/templates/gitignore.fragment
git commit -m "feat(e5): add .gitignore fragment for bootstrap merge"
```

---

## Phase 2 — Python Bootstrap Module

### Task 4: Implement detection logic (TDD)

**Files:**
- Create: `scripts/project_bootstrap.py`
- Create: `tests/test_project_bootstrap.py`

- [ ] **Step 1: Write failing tests for detection**

File: `tests/test_project_bootstrap.py`

```python
"""Tests for scripts/project_bootstrap.py — detection logic."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import project_bootstrap as pb  # noqa: E402


def test_detect_mode_on_code_repo(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert pb.detect_mode(tmp_path) == "code_repo"


def test_detect_mode_on_python_project(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    assert pb.detect_mode(tmp_path) == "code_repo"


def test_detect_mode_on_plugin_dir(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text("{}")
    assert pb.detect_mode(tmp_path) == "code_repo"


def test_detect_mode_on_existing_thesis(tmp_path):
    (tmp_path / "academic_context.md").write_text("# thesis")
    assert pb.detect_mode(tmp_path) == "idempotent"


def test_detect_mode_on_empty_dir(tmp_path):
    assert pb.detect_mode(tmp_path) == "fresh"


def test_detect_mode_on_dir_with_only_dotfiles(tmp_path):
    (tmp_path / ".DS_Store").write_text("")
    (tmp_path / ".hidden").write_text("")
    assert pb.detect_mode(tmp_path) == "fresh"


def test_detect_mode_on_dir_with_user_files(tmp_path):
    (tmp_path / "notes.txt").write_text("some notes")
    assert pb.detect_mode(tmp_path) == "skip"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py -v
```
Expected: ModuleNotFoundError or `AttributeError: module 'project_bootstrap' has no attribute 'detect_mode'`.

- [ ] **Step 3: Implement detection**

File: `scripts/project_bootstrap.py`

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py -v
```
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_bootstrap.py tests/test_project_bootstrap.py
git commit -m "feat(e5): add project_bootstrap detect_mode with tests"
```

---

### Task 5: Implement structure creation (TDD)

**Files:**
- Modify: `scripts/project_bootstrap.py`
- Modify: `tests/test_project_bootstrap.py`

- [ ] **Step 1: Add failing tests for structure creation**

Append to `tests/test_project_bootstrap.py`:

```python
TEMPLATES = Path(__file__).parent.parent / "scripts" / "templates"


def test_create_structure_stub_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    pb.create_structure(tmp_path, stub=True)
    assert (tmp_path / "academic_context.md").exists()
    assert "Universität: TODO" in (tmp_path / "academic_context.md").read_text()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "kapitel" / ".gitkeep").exists()
    assert (tmp_path / "literatur" / ".gitkeep").exists()
    assert (tmp_path / "pdfs" / ".gitkeep").exists()


def test_create_structure_skips_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    (tmp_path / "academic_context.md").write_text("USER CONTENT — do not overwrite")
    pb.create_structure(tmp_path, stub=True)
    assert (tmp_path / "academic_context.md").read_text() == "USER CONTENT — do not overwrite"
    assert (tmp_path / "CLAUDE.md").exists()


def test_create_structure_no_stub_when_stub_false(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    pb.create_structure(tmp_path, stub=False)
    assert not (tmp_path / "academic_context.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py::test_create_structure_stub_mode -v
```
Expected: FAIL with `AttributeError: module 'project_bootstrap' has no attribute 'create_structure'`.

- [ ] **Step 3: Implement `create_structure`**

Append to `scripts/project_bootstrap.py`:

```python
TEMPLATES_DIR = Path(__file__).parent / "templates"

SUBDIRS = ("kapitel", "literatur", "pdfs")


def create_structure(cwd: Path, stub: bool) -> None:
    """Lay down the project skeleton, skipping files that already exist.

    If stub=True, also copy academic_context.stub.md as academic_context.md
    (only if the target file doesn't exist — idempotent).
    """
    if stub and not (cwd / "academic_context.md").exists():
        stub_src = TEMPLATES_DIR / "academic_context.stub.md"
        (cwd / "academic_context.md").write_text(stub_src.read_text(encoding="utf-8"))

    claude_md = cwd / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text((TEMPLATES_DIR / "CLAUDE.md").read_text(encoding="utf-8"))

    for sub in SUBDIRS:
        (cwd / sub).mkdir(exist_ok=True)
        gitkeep = cwd / sub / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py -v
```
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_bootstrap.py tests/test_project_bootstrap.py
git commit -m "feat(e5): add create_structure for project skeleton (with .gitkeep)"
```

---

### Task 6: Implement gitignore merging (TDD)

**Files:**
- Modify: `scripts/project_bootstrap.py`
- Modify: `tests/test_project_bootstrap.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_project_bootstrap.py`:

```python
def test_merge_gitignore_creates_new(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    pb.merge_gitignore(tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert "pdfs/*" in content
    assert "!pdfs/.gitkeep" in content
    assert ".DS_Store" in content


def test_merge_gitignore_appends_missing_lines(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    (tmp_path / ".gitignore").write_text("node_modules/\n.DS_Store\n")
    pb.merge_gitignore(tmp_path)
    lines = (tmp_path / ".gitignore").read_text().splitlines()
    assert "node_modules/" in lines
    assert ".DS_Store" in lines
    assert lines.count(".DS_Store") == 1  # not duplicated
    assert "pdfs/*" in lines


def test_merge_gitignore_preserves_order_of_existing(tmp_path, monkeypatch):
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    (tmp_path / ".gitignore").write_text("first\nsecond\n")
    pb.merge_gitignore(tmp_path)
    lines = (tmp_path / ".gitignore").read_text().splitlines()
    assert lines[0] == "first"
    assert lines[1] == "second"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py::test_merge_gitignore_creates_new -v
```
Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement `merge_gitignore`**

Append to `scripts/project_bootstrap.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py -v
```
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_bootstrap.py tests/test_project_bootstrap.py
git commit -m "feat(e5): add .gitignore merge that preserves existing entries"
```

---

### Task 7: Implement memory migration helper (TDD)

**Files:**
- Modify: `scripts/project_bootstrap.py`
- Modify: `tests/test_project_bootstrap.py`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_project_bootstrap.py`:

```python
def test_find_memory_files_returns_empty_when_absent(tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    assert pb.find_memory_files(fake_home, tmp_path / "cwd") == []


def test_find_memory_files_picks_up_context(tmp_path):
    """Claude-memory layout: ~/.claude/projects/<cwd-slug>/memory/academic_context.md"""
    fake_home = tmp_path / "home"
    cwd = tmp_path / "thesis"
    cwd.mkdir()
    memory = fake_home / ".claude" / "projects" / "-thesis" / "memory"
    memory.mkdir(parents=True)
    (memory / "academic_context.md").write_text("from memory")
    (memory / "literature_state.md").write_text("lit")

    found = pb.find_memory_files(fake_home, cwd)
    names = sorted(p.name for p in found)
    assert names == ["academic_context.md", "literature_state.md"]


def test_copy_memory_files_to_cwd(tmp_path):
    cwd = tmp_path / "thesis"
    cwd.mkdir()
    source = tmp_path / "memory"
    source.mkdir()
    (source / "academic_context.md").write_text("CONTEXT")
    (source / "literature_state.md").write_text("LIT")

    pb.copy_memory_files([source / "academic_context.md", source / "literature_state.md"], cwd)
    assert (cwd / "academic_context.md").read_text() == "CONTEXT"
    assert (cwd / "literature_state.md").read_text() == "LIT"
    # Source files untouched (backup)
    assert (source / "academic_context.md").exists()


def test_copy_memory_files_skips_existing(tmp_path):
    cwd = tmp_path / "thesis"
    cwd.mkdir()
    (cwd / "academic_context.md").write_text("ALREADY HERE")
    source = tmp_path / "memory"
    source.mkdir()
    (source / "academic_context.md").write_text("FROM MEMORY")

    pb.copy_memory_files([source / "academic_context.md"], cwd)
    assert (cwd / "academic_context.md").read_text() == "ALREADY HERE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py::test_find_memory_files_returns_empty_when_absent -v
```
Expected: FAIL with `AttributeError`.

- [ ] **Step 3: Implement migration functions**

Append to `scripts/project_bootstrap.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_project_bootstrap.py -v
```
Expected: 17 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_bootstrap.py tests/test_project_bootstrap.py
git commit -m "feat(e5): add find_memory_files + copy_memory_files migration helpers"
```

---

### Task 8: Wire up `main()` and integrate into `setup.sh`

**Files:**
- Modify: `scripts/project_bootstrap.py`
- Modify: `scripts/setup.sh`
- Modify: `commands/setup.md`

- [ ] **Step 1: Add `main()` to `project_bootstrap.py`**

Append to `scripts/project_bootstrap.py`:

```python
def _prompt_yes_no(question: str, default_yes: bool = False) -> bool:
    """Interactive y/n prompt. Returns False on non-interactive stdin."""
    import sys
    if not sys.stdin.isatty():
        return default_yes
    suffix = "[Y/n]" if default_yes else "[y/N]"
    answer = input(f"{question} {suffix} ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "yes", "j", "ja")


def main() -> None:
    import sys
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


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Integrate into `setup.sh`**

Modify `scripts/setup.sh`. Append after the block that ends with `python3 "$SCRIPT_DIR/configure_permissions.py"` (before the final `echo "Setup complete: $BASE"`):

```bash
# ---------------------------------------------------------------------------
# 7. Projekt-Bootstrap (Auto-Detect)
# ---------------------------------------------------------------------------

"$BASE/venv/bin/python" "$SCRIPT_DIR/project_bootstrap.py"
```

- [ ] **Step 3: Update `commands/setup.md`**

Replace the section `Das Skript übernimmt in sechs Schritten:` with `Das Skript übernimmt in sieben Schritten:` and append as step 7:

```
7. **Projekt-Bootstrap (Auto-Detect).** Wenn das aktuelle Verzeichnis ein leerer Ordner ist, fragt `/setup` `"Hier einen Facharbeit-Arbeitsordner initialisieren?"`. Bei `y` werden `academic_context.md` (Stub), `CLAUDE.md`, `.gitignore`, sowie `kapitel/`, `literatur/`, `pdfs/` angelegt. In einem bestehenden Facharbeit-Ordner (mit `academic_context.md`) werden nur fehlende Artefakte nachgezogen — idempotent, keine Rückfrage. In Code-Repos (erkannt an `package.json`, `pyproject.toml`, …) oder nicht-leeren fremden Verzeichnissen: keine Aktion. Findet der Bootstrap zusätzlich bestehenden Kontext in Claude-Memory, bietet er an, ihn einmalig ins Projekt zu kopieren; die Memory-Dateien bleiben als Backup liegen.
```

Also add to the existing table:

```
| ✅ Facharbeit-Arbeitsordner initialisiert | Projekt-Struktur wurde im aktuellen Verzeichnis angelegt |
```

- [ ] **Step 4: Manual smoke test**

```bash
# Test fresh-dir flow
mkdir /tmp/facharbeit-test && cd /tmp/facharbeit-test
echo "y" | ~/.academic-research/venv/bin/python ~/Repos/academic-research/scripts/project_bootstrap.py
ls -la
```
Expected: `academic_context.md`, `CLAUDE.md`, `.gitignore`, `kapitel/`, `literatur/`, `pdfs/` exist.

```bash
# Test idempotent re-run
~/.academic-research/venv/bin/python ~/Repos/academic-research/scripts/project_bootstrap.py
```
Expected: `✅ Facharbeit-Arbeitsordner: Artefakte aktualisiert` (no prompt).

```bash
# Clean up
rm -rf /tmp/facharbeit-test
cd ~/Repos/academic-research
```

- [ ] **Step 5: Commit**

```bash
git add scripts/project_bootstrap.py scripts/setup.sh commands/setup.md
git commit -m "feat(e5): wire project_bootstrap main into setup.sh step 7"
```

---

## Phase 3 — Skill migration

**Migration rules reminder:** Apply the table at the top of this document to every SKILL.md below. The goal is to rewrite any mention of "Memory" as the storage location. Skills should say the context files live in the project directory (cwd), are read/written via relative paths like `./academic_context.md`.

Verify each skill with:

```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" skills/<name>/SKILL.md
```
Expected after migration: no output.

---

### Task 9: Migrate `academic-context` SKILL (primary writer)

**Files:**
- Modify: `skills/academic-context/SKILL.md`

- [ ] **Step 1: Read current file**

Read `skills/academic-context/SKILL.md` in full.

- [ ] **Step 2: Rewrite memory-language**

Apply these specific edits:

a) Replace section heading `## Memory-Dateien` with `## Kontext-Dateien`.

b) Replace introductory paragraph under `## Memory-Dateien` (currently describes "Claude-Memory des Projekt-Memory-Verzeichnisses") with:

```markdown
Der gesamte Kontext liegt im aktuellen Projekt-Ordner (cwd). Drei Dateien werden verwaltet:
```

c) Under `### Erstaktivierung`, replace `Existiert keine academic_context.md im Memory` with `Existiert keine ./academic_context.md im Projekt-Ordner`.

d) Under `### Unterstützung anderer Skills`, replace `Prüfe, ob academic_context.md im Memory existiert` with `Prüfe, ob ./academic_context.md im Projekt-Ordner existiert`.

e) Under `## Wichtige Regeln`, leave generic rules intact but ensure `Nie ohne vorheriges Lesen überschreiben` still makes sense in the project-file context (it does).

f) If the file still contains the string `Memory` anywhere outside of auto-memory-related discussion (check with grep), replace with `Projekt-Ordner`.

- [ ] **Step 3: Grep verification**

Run:
```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory|Memory des Projekt)" skills/academic-context/SKILL.md
```
Expected: no output.

- [ ] **Step 4: Smoke test (existing manifest test)**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_skills_manifest.py -v -k academic_context
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/academic-context/SKILL.md
git commit -m "refactor(e5): migrate academic-context SKILL to project-local context"
```

---

### Task 10: Migrate `advisor` and `methodology-advisor` SKILLs

**Files:**
- Modify: `skills/advisor/SKILL.md`
- Modify: `skills/methodology-advisor/SKILL.md`

- [ ] **Step 1: Read both files**

Read `skills/advisor/SKILL.md` and `skills/methodology-advisor/SKILL.md`.

- [ ] **Step 2: Apply migration rules**

For each file, apply the rules from the migration table at the top:

- `## Memory-Dateien` → `## Kontext-Dateien`
- `academic_context.md im Memory` → `academic_context.md im Projekt-Ordner`
- `aus dem Memory` → `aus dem Projekt-Ordner`
- `Lies academic_context.md aus dem Memory` → `Lies ./academic_context.md aus dem Projekt-Ordner`
- Any other `Memory`-references as fits the context

For `advisor/SKILL.md` specifically: line 179 `Vor dem Speichern bestätigen lassen — Immer explizite Freigabe einholen, bevor ins Memory geschrieben wird` becomes `Vor dem Speichern bestätigen lassen — Immer explizite Freigabe einholen, bevor in ./academic_context.md geschrieben wird`.

- [ ] **Step 3: Grep verification**

Run:
```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" skills/advisor/SKILL.md skills/methodology-advisor/SKILL.md
```
Expected: no output.

- [ ] **Step 4: Smoke test**

Run:
```bash
~/.academic-research/venv/bin/python -m pytest tests/test_skills_manifest.py -v -k "advisor or methodology_advisor"
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/advisor/SKILL.md skills/methodology-advisor/SKILL.md
git commit -m "refactor(e5): migrate advisor + methodology-advisor to project-local context"
```

---

### Task 11: Migrate `research-question-refiner`, `literature-gap-analysis`, `source-quality-audit`

**Files:**
- Modify: `skills/research-question-refiner/SKILL.md`
- Modify: `skills/literature-gap-analysis/SKILL.md`
- Modify: `skills/source-quality-audit/SKILL.md`

- [ ] **Step 1: Read all three**

- [ ] **Step 2: Apply migration rules** (same as Task 10, tailored per file)

- [ ] **Step 3: Grep verification**

Run:
```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" \
  skills/research-question-refiner/SKILL.md \
  skills/literature-gap-analysis/SKILL.md \
  skills/source-quality-audit/SKILL.md
```
Expected: no output.

- [ ] **Step 4: Smoke test**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_skills_manifest.py -v -k "research_question or literature_gap or source_quality"
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/research-question-refiner/SKILL.md \
  skills/literature-gap-analysis/SKILL.md \
  skills/source-quality-audit/SKILL.md
git commit -m "refactor(e5): migrate 3 analysis skills to project-local context"
```

---

### Task 12: Migrate `chapter-writer`, `abstract-generator`, `title-generator`

**Files:**
- Modify: `skills/chapter-writer/SKILL.md`
- Modify: `skills/abstract-generator/SKILL.md`
- Modify: `skills/title-generator/SKILL.md`

- [ ] **Step 1: Read all three**

- [ ] **Step 2: Apply migration rules**

For `abstract-generator/SKILL.md` specifically:
- Line 94 `## Memory-Dateien` → `## Kontext-Dateien`
- Line 96 `Lies academic_context.md` — stays as-is since no path qualifier was used; add `./` to make relative: `Lies ./academic_context.md`
- Line 166 `Lies academic_context.md` → `Lies ./academic_context.md`

For `chapter-writer/SKILL.md` and `title-generator/SKILL.md`: apply the same rules to every occurrence.

- [ ] **Step 3: Grep verification**

```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" \
  skills/chapter-writer/SKILL.md \
  skills/abstract-generator/SKILL.md \
  skills/title-generator/SKILL.md
```
Expected: no output.

- [ ] **Step 4: Smoke test**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_skills_manifest.py -v -k "chapter_writer or abstract_generator or title_generator"
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/chapter-writer/SKILL.md skills/abstract-generator/SKILL.md skills/title-generator/SKILL.md
git commit -m "refactor(e5): migrate 3 writing skills to project-local context"
```

---

### Task 13: Migrate `citation-extraction`, `plagiarism-check`, `style-evaluator`, `submission-checker`

**Files:**
- Modify: `skills/citation-extraction/SKILL.md`
- Modify: `skills/plagiarism-check/SKILL.md`
- Modify: `skills/style-evaluator/SKILL.md`
- Modify: `skills/submission-checker/SKILL.md`

- [ ] **Step 1: Read all four**

- [ ] **Step 2: Apply migration rules** (tailored per file)

- [ ] **Step 3: Grep verification**

```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" \
  skills/citation-extraction/SKILL.md \
  skills/plagiarism-check/SKILL.md \
  skills/style-evaluator/SKILL.md \
  skills/submission-checker/SKILL.md
```
Expected: no output.

- [ ] **Step 4: Smoke test**

```bash
~/.academic-research/venv/bin/python -m pytest tests/test_skills_manifest.py -v -k "citation_extraction or plagiarism or style_evaluator or submission_checker"
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/citation-extraction/SKILL.md skills/plagiarism-check/SKILL.md skills/style-evaluator/SKILL.md skills/submission-checker/SKILL.md
git commit -m "refactor(e5): migrate 4 verification skills to project-local context"
```

---

### Task 14: Migrate `query-generator` agent

**Files:**
- Modify: `agents/query-generator.md`

- [ ] **Step 1: Read file**

- [ ] **Step 2: Apply migration rules**

Specific for this agent: line 143 `academic_context.md, um zu entscheiden:` stays unchanged (no path qualifier), but add `./` prefix: `./academic_context.md, um zu entscheiden:`. The `academic_context`-JSON-key references (lines 46, 54, 92) stay as-is — those describe a JSON schema, not a file path.

- [ ] **Step 3: Grep verification**

```bash
grep -niE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory)" agents/query-generator.md
```
Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add agents/query-generator.md
git commit -m "refactor(e5): migrate query-generator agent to project-local context"
```

---

### Task 15: Final grep verification across all skills + agents

**Files:**
- No changes expected (verification only)

- [ ] **Step 1: Run comprehensive grep**

```bash
grep -rniE "(aus dem Memory|ins Memory|Memory-Datei|Claude-Memory|\bMemory des Projekt\b)" skills/ agents/
```
Expected: no output.

- [ ] **Step 2: Run full smoke test**

```bash
~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals
```
Expected: 51+ passed (manifest + bootstrap tests), evals skipped without API key.

- [ ] **Step 3: If anything is found in step 1, fix inline**

For each file with leftover memory-reference, open it, apply the migration rule, commit with a focused message:

```bash
git add <file>
git commit -m "refactor(e5): clean up leftover memory reference in <file>"
```

---

## Phase 4 — Documentation

### Task 16: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add "Overhead reduzieren" section after Installation**

After the `### 3. document-skills installieren` section (around line 129), add:

```markdown
### Overhead in anderen Projekten reduzieren

Das Plugin wird global installiert — das ist vom Claude-Code-Plugin-System so vorgesehen. Wenn du den Plugin-Overhead (Skills, SessionStart-Hooks, Permissions) nur im Facharbeit-Ordner haben willst, schalte es in anderen Projekten per `.claude/settings.local.json` explizit ab:

\`\`\`json
{
  "enabledPlugins": {
    "academic-research@academic-research": false
  }
}
\`\`\`

Die Datei ist `.gitignored` (persönliche Override, kein Team-Effekt). Im Facharbeit-Ordner bleibt das Plugin per Default aktiv — keine Extra-Konfiguration nötig.

**Bestehenden Ordner nachträglich zur Facharbeit machen:** `touch academic_context.md` im Zielordner, dann `/academic-research:setup` aufrufen. Die Detection erkennt die Datei und ergänzt `CLAUDE.md`, `.gitignore`, Ordner — ohne Rückfrage, ohne vorhandene Daten zu überschreiben.
```

- [ ] **Step 2: Update Quickstart to mention bootstrap**

In the `## Quick Start` section (around line 132), prepend a step 0:

```markdown
# 0. Neuen Facharbeit-Ordner aufsetzen (einmalig)
mkdir ~/Facharbeit-XY && cd ~/Facharbeit-XY
/academic-research:setup
# → fragt "Hier einen Facharbeit-Arbeitsordner initialisieren?" → y
# → legt academic_context.md, CLAUDE.md, .gitignore, kapitel/, literatur/, pdfs/ an
```

- [ ] **Step 3: Update "Was /setup automatisch installiert" table**

In the `### Was /setup automatisch installiert` table (around line 51), add a row:

```
| Projekt-Struktur | `academic_context.md`, `CLAUDE.md`, `.gitignore`, `kapitel/`, `literatur/`, `pdfs/` im aktuellen Facharbeit-Ordner |
```

- [ ] **Step 4: Update Memory-System section**

Replace the `## Memory-System` section (around line 352) with:

```markdown
## Kontext-Dateien (projekt-lokal ab v5.3.0)

Der akademische Kontext liegt git-versionierbar im Projekt-Ordner:

| Datei | Inhalt |
|-------|--------|
| `./academic_context.md` | Thesis-Profil, Gliederung, Forschungsfrage, Fortschritt |
| `./literature_state.md` | Literatur-Statistik, Kapitelzuordnung, Lücken (lazy von `citation-extraction` angelegt) |
| `./writing_state.md` | Aktuelles Kapitel, Wortzahl, Style-Scores (lazy von `chapter-writer` angelegt) |

Vor v5.3.0 lagen diese Dateien in Claude-Memory — die v5.3.0-Migration kopiert sie in den Projekt-Ordner. Siehe CHANGELOG.
```

- [ ] **Step 5: Verify markdown renders**

Run:
```bash
head -60 README.md
```
Expected: Normal markdown, no broken fenced code blocks.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs(e5): add overhead-reduction section + update context docs for v5.3.0"
```

---

### Task 17: Update `CHANGELOG.md`

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Prepend new v5.3.0 block**

Insert after the header (line 6, before `## [5.2.0]`):

```markdown
## [5.3.0] — 2026-04-23

### ⚠️ BREAKING — Kontext-Ablage geändert

Der akademische Kontext wandert von Claude-Memory (`~/.claude/projects/<hash>/memory/`) in projekt-lokale Dateien (`./academic_context.md` im Arbeitsordner). Alle 13 Skills und der `query-generator`-Agent lesen jetzt aus dem Projekt-Ordner, nicht mehr aus Memory.

**Migration:**

1. In deinen Facharbeit-Ordner wechseln: `cd ~/Pfad/zur/Arbeit`
2. `/academic-research:setup` aufrufen
3. Auf die Rückfrage *"Bestehenden Kontext in Claude-Memory gefunden. Kopieren?"* mit `y` antworten

Die Memory-Dateien bleiben als Backup liegen — sie werden nur nicht mehr gelesen.
Wenn du neu anfängst (keine Memory-Dateien): `/setup` im leeren Ordner aufrufen und *"Facharbeit initialisieren?"* bejahen.

### Added

- `/academic-research:setup` erweitert um Projekt-Bootstrap mit Auto-Detect: in leerem Ordner fragt das Setup nach Facharbeit-Init; in existierenden Facharbeit-Ordnern werden fehlende Artefakte idempotent nachgezogen; in Code-Repos bleibt es bei reinem Environment-Setup.
- Minimale Projekt-Struktur beim Bootstrap: `academic_context.md` (Template-Stub mit TODO-Platzhaltern), `CLAUDE.md` (generierte Plugin-Anleitung), `.gitignore` (merge-sicher), Ordner `kapitel/`, `literatur/`, `pdfs/` mit `.gitkeep`.
- Generierte `CLAUDE.md` mit Skill-Delegations-Tabelle, Slash-Command-Übersicht, Ordner-Konventionen und Anti-Fabrikations-Regel.
- Migrations-Helper: `/setup` erkennt Memory-basierten Kontext und bietet einmaligen Copy ins Projekt an.
- README-Sektion *Overhead in anderen Projekten reduzieren* erklärt projekt-spezifisches Deaktivieren via `.claude/settings.local.json`.
- `scripts/project_bootstrap.py` (Python-Modul für Detection/Creation/Migration, voll getestet via `tests/test_project_bootstrap.py`).
- `scripts/templates/` — Templates für Stub, CLAUDE.md, gitignore-Fragment.

### Changed

- Alle 13 Skills + der `query-generator`-Agent lesen Kontext aus `./academic_context.md` im Projekt-Ordner statt aus Memory. Sektionsheadings `## Memory-Dateien` → `## Kontext-Dateien`; Formulierungen `aus dem Memory` → `aus dem Projekt-Ordner`.

### Migration

Siehe Breaking-Block oben. Memory-Dateien bleiben unangetastet (Backup). `/setup` ist idempotent und mehrfach aufrufbar.

```

- [ ] **Step 2: Verify**

Run:
```bash
head -50 CHANGELOG.md
```
Expected: New `[5.3.0]` block appears above `[5.2.0]`.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(e5): add v5.3.0 CHANGELOG block with breaking-change migration"
```

---

## Phase 5 — Release prep

### Task 18: Version bump to 5.3.0

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump plugin.json**

In `.claude-plugin/plugin.json`, change:

```json
"version": "5.2.0",
```

to:

```json
"version": "5.3.0",
```

- [ ] **Step 2: Bump marketplace.json**

In `.claude-plugin/marketplace.json`, change the version inside the `plugins[0]` object:

```json
"version": "5.2.0"
```

to:

```json
"version": "5.3.0"
```

- [ ] **Step 3: Verify consistency**

Run:
```bash
grep -n '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
```
Expected: Both show `"version": "5.3.0"`.

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(e5): bump version to 5.3.0"
```

---

### Task 19: Final smoke test and PR prep

**Files:** None (verification + PR)

- [ ] **Step 1: Run full test suite**

```bash
~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals
```
Expected: All tests pass (manifest smoke + bootstrap tests = ~68+ passed).

- [ ] **Step 2: Manual smoke test checklist**

Run each scenario:

1. **Fresh flow:**
   ```bash
   mkdir /tmp/fa-fresh && cd /tmp/fa-fresh
   bash ~/Repos/academic-research/scripts/setup.sh   # answer 'y' to init prompt
   ls -la
   ```
   Expected: All 6 artefacts (`academic_context.md`, `CLAUDE.md`, `.gitignore`, `kapitel/`, `literatur/`, `pdfs/`) present. `academic_context.md` contains "Universität: TODO".

2. **Idempotent re-run:**
   ```bash
   cd /tmp/fa-fresh
   bash ~/Repos/academic-research/scripts/setup.sh   # no prompt, just ✅ Artefakte aktualisiert
   ```
   Expected: No overwrites; `academic_context.md` unchanged.

3. **Code-repo skip:**
   ```bash
   mkdir /tmp/fa-code && cd /tmp/fa-code
   echo '{}' > package.json
   bash ~/Repos/academic-research/scripts/setup.sh
   ls -la
   ```
   Expected: Only `package.json` — no bootstrap artefacts created.

4. **Non-empty-dir skip:**
   ```bash
   mkdir /tmp/fa-random && cd /tmp/fa-random
   echo "notes" > random.txt
   bash ~/Repos/academic-research/scripts/setup.sh
   ls -la
   ```
   Expected: No bootstrap artefacts; `random.txt` untouched; no prompt.

5. **Retrofit via `touch`:**
   ```bash
   cd /tmp/fa-random
   touch academic_context.md
   bash ~/Repos/academic-research/scripts/setup.sh
   ls -la
   ```
   Expected: `CLAUDE.md`, `.gitignore`, `kapitel/`, `literatur/`, `pdfs/` appear; `random.txt` and empty `academic_context.md` untouched; no prompt.

6. **Cleanup:**
   ```bash
   rm -rf /tmp/fa-fresh /tmp/fa-code /tmp/fa-random
   cd ~/Repos/academic-research
   ```

- [ ] **Step 3: Push branch and open PR**

```bash
git push -u origin e5-project-bootstrap
gh pr create --title "refactor: E5 Project-Bootstrap + Context-Migration (v5.3.0)" \
  --body "$(cat <<'EOF'
## Summary

- Extends `/academic-research:setup` with auto-detected project-bootstrap: lays down `academic_context.md` (stub), `CLAUDE.md`, `.gitignore`, and `kapitel/`/`literatur/`/`pdfs/` in empty directories.
- Migrates the academic-context storage from Claude-Memory to project-local files (breaking change).
- Adds a migration helper that offers a one-time copy of existing memory files into the project.
- Rewrites all 13 skills + `query-generator` agent to read context from the project directory.
- Adds `README.md` section on how to disable the plugin in non-academic projects.

## Test plan

- [x] `pytest tests/ -v --ignore=tests/evals` — passes
- [x] Manual smoke: fresh flow (y → structure created)
- [x] Manual smoke: idempotent re-run (no prompt, no overwrite)
- [x] Manual smoke: code-repo skip (package.json present → no bootstrap)
- [x] Manual smoke: non-empty-dir skip (no prompt, no changes)
- [x] Manual smoke: retrofit via `touch academic_context.md` (idempotent mode)
- [x] Grep verification: no skill references Memory anymore

## Breaking change

Context files move from Claude-Memory to `./academic_context.md` (cwd). Migration: run `/setup` in thesis folder, say `y` to the copy prompt. See CHANGELOG v5.3.0 block.
EOF
)"
```

Expected: PR URL printed.

- [ ] **Step 4: Done** — report PR URL to the user for review before merge.

---

## Self-Review

**Spec coverage check:**

| Spec section | Implemented in |
|---|---|
| D1 `/setup` extension, no new command | Task 8 (setup.sh wires up project_bootstrap) |
| D2 Auto-Detect + interactive prompt | Task 4 (detect_mode) + Task 8 (main with _prompt_yes_no) |
| D3 Minimal structure | Task 5 (create_structure — only 6 artefacts) |
| D4 Template-Stub (no wizard) | Task 1 (stub template) + Task 5 (copies it) |
| D5 Context project-local | Tasks 9-14 (all SKILL.md + agent migrations) |
| D6 Full migration 13 skills + 3 agents | Tasks 9-14 covers 13 skills + 1 agent (`query-generator`). `quote-extractor` and `relevance-scorer` have no memory references per grep — no task needed. ✅ |
| D7 Migration helper | Task 7 (find_memory_files, copy_memory_files) + Task 8 (wired in main) |
| D8 Project-local PDFs only for user files | Task 2 (CLAUDE.md explains) + Task 16 (README) |
| README section "Overhead reduzieren" | Task 16 step 1 |
| Breaking-change CHANGELOG | Task 17 |
| Version bump 5.3.0 | Task 18 |
| Detection heuristic: 4 modes | Task 4 (detect_mode returns one of four strings) |
| Edge case: retrofit via `touch` | Task 19 smoke test scenario 5 + README Task 16 step 1 |
| `.gitignore` merge-sicher | Task 6 (merge_gitignore preserves existing) |

No spec gaps.

**Placeholder scan:** No `TBD`, `TODO` outside the intentional stub template, no "implement later", no "similar to Task N". All code blocks complete.

**Type consistency:** `detect_mode` returns strings `"idempotent"` / `"code_repo"` / `"fresh"` / `"skip"` — used consistently in Task 4 tests, Task 5 (via stub flag), and Task 8 main. `create_structure(cwd, stub: bool)` signature consistent across Tasks 5 and 8. `find_memory_files(home, cwd) -> list[Path]` and `copy_memory_files(sources, cwd)` match their callers in Task 8 main.
