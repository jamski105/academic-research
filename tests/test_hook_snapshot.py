"""Tests fuer pre-compact.mjs Snapshot-Hook.

Der Hook wird als Node.js-Subprocess gestartet.
Eingabe: JSON auf stdin (Claude Code PreCompact-Format).
Der Hook schreibt academic_context.md, literature_state.md, writing_state.md
und einen Vault-Tarball nach ~/.academic-research/snapshots/<slug>/<ts>.tgz.
Exit 0 immer (fail-open).
"""
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "pre-compact.mjs"
WORKTREE_ROOT = Path(__file__).parent.parent


def run_hook(payload: dict, env_overrides: dict = None) -> subprocess.CompletedProcess:
    """Startet den Hook als Subprocess mit JSON-Eingabe auf stdin."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    return subprocess.run(
        ["node", str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_hook_exits_zero_on_empty_input():
    """Hook ist fail-open: exit 0 auch bei leerem Payload."""
    result = run_hook({})
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"


def test_hook_exits_zero_on_compact_event():
    """Hook laeuft bei PreCompact-Event durch (exit 0)."""
    payload = {
        "hook_event_name": "PreCompact",
        "trigger_reason": "manual",
    }
    result = run_hook(payload)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"


def test_hook_writes_snapshot_files(tmp_path):
    """Hook schreibt Snapshot-Dateien in SNAPSHOTS_DIR."""
    slug = "test-project"
    snapshots_dir = tmp_path / "snapshots"
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Erstelle Testdateien im Projekt-Verzeichnis
    (project_dir / "academic_context.md").write_text("# Kontext\nTestinhalt")
    (project_dir / "literature_state.md").write_text("# Literatur\nTestpaper")
    (project_dir / "writing_state.md").write_text("# Schreibstatus\nKapitel 1")

    payload = {
        "hook_event_name": "PreCompact",
        "trigger_reason": "auto",
    }

    env_overrides = {
        "ACADEMIC_SNAPSHOTS_DIR": str(snapshots_dir),
        "ACADEMIC_PROJECT_SLUG": slug,
        "CLAUDE_PROJECT_DIR": str(project_dir),
        "VAULT_DB_PATH": str(tmp_path / "nonexistent.db"),  # fail-open fuer Vault
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"

    # Snapshot-Verzeichnis muss existieren
    slug_dir = snapshots_dir / slug
    assert slug_dir.exists(), f"Snapshot-Verzeichnis {slug_dir} nicht erstellt"

    # Mindestens eine .tgz-Datei muss existieren
    tarballs = list(slug_dir.glob("*.tgz"))
    assert len(tarballs) >= 1, f"Keine .tgz-Dateien in {slug_dir}"


def test_hook_tarball_contains_state_files(tmp_path):
    """Tarball enthaelt academic_context.md, literature_state.md, writing_state.md."""
    slug = "test-project"
    snapshots_dir = tmp_path / "snapshots"
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    (project_dir / "academic_context.md").write_text("# Kontext\nTestinhalt")
    (project_dir / "literature_state.md").write_text("# Literatur\nTestpaper")
    (project_dir / "writing_state.md").write_text("# Schreibstatus\nKapitel 1")

    payload = {"hook_event_name": "PreCompact"}
    env_overrides = {
        "ACADEMIC_SNAPSHOTS_DIR": str(snapshots_dir),
        "ACADEMIC_PROJECT_SLUG": slug,
        "CLAUDE_PROJECT_DIR": str(project_dir),
        "VAULT_DB_PATH": str(tmp_path / "nonexistent.db"),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0

    slug_dir = snapshots_dir / slug
    tarballs = list(slug_dir.glob("*.tgz"))
    assert len(tarballs) >= 1

    # Tarball oeffnen und Inhalt pruefen
    with tarfile.open(tarballs[0], "r:gz") as tar:
        names = tar.getnames()

    # Mindestens state-Dateien muessen vorhanden sein
    assert any("academic_context.md" in n for n in names), f"academic_context.md nicht in Tarball: {names}"
    assert any("literature_state.md" in n for n in names), f"literature_state.md nicht in Tarball: {names}"
    assert any("writing_state.md" in n for n in names), f"writing_state.md nicht in Tarball: {names}"


def test_hook_failopen_when_project_dir_missing(tmp_path):
    """Hook ist fail-open wenn CLAUDE_PROJECT_DIR nicht existiert."""
    payload = {"hook_event_name": "PreCompact"}
    env_overrides = {
        "ACADEMIC_SNAPSHOTS_DIR": str(tmp_path / "snapshots"),
        "ACADEMIC_PROJECT_SLUG": "test",
        "CLAUDE_PROJECT_DIR": str(tmp_path / "nonexistent_project"),
        "VAULT_DB_PATH": str(tmp_path / "nonexistent.db"),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    # Immer fail-open
    assert result.returncode == 0, f"Erwartet 0 (fail-open), got {result.returncode}. stderr: {result.stderr}"
