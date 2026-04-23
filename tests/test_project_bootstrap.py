"""Tests for scripts/project_bootstrap.py — detection logic."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
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


def test_detect_mode_idempotent_beats_code_repo(tmp_path):
    """academic_context.md short-circuits the code-repo check — order matters."""
    (tmp_path / "academic_context.md").write_text("# thesis")
    (tmp_path / "package.json").write_text("{}")
    assert pb.detect_mode(tmp_path) == "idempotent"


TEMPLATES = Path(__file__).resolve().parent.parent / "scripts" / "templates"


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


def test_create_structure_second_run_is_noop(tmp_path, monkeypatch):
    """Calling create_structure twice must not error or change anything."""
    monkeypatch.setattr(pb, "TEMPLATES_DIR", TEMPLATES)
    pb.create_structure(tmp_path, stub=True)
    stamp_before = (tmp_path / "academic_context.md").stat().st_mtime_ns
    pb.create_structure(tmp_path, stub=True)
    stamp_after = (tmp_path / "academic_context.md").stat().st_mtime_ns
    assert stamp_before == stamp_after


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


def test_find_memory_files_returns_empty_when_absent(tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    assert pb.find_memory_files(fake_home, tmp_path / "cwd") == []


def test_find_memory_files_picks_up_context(tmp_path):
    """Claude-memory layout: ~/.claude/projects/<cwd-slug>/memory/academic_context.md"""
    fake_home = tmp_path / "home"
    cwd = tmp_path / "thesis"
    cwd.mkdir()
    # Use the real slug function to construct the expected path
    slug = pb._cwd_slug(cwd)
    memory = fake_home / ".claude" / "projects" / slug / "memory"
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
