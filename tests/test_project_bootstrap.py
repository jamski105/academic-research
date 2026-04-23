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
