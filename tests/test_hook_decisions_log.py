"""Tests fuer post-tool-use-decisions.mjs Hook.

Der Hook wird als Node.js-Subprocess gestartet.
Bei Write-Events mit *.md im Projekt-Verzeichnis schreibt er eine Zeile in decisions.log.
Format: ISO-Timestamp + Skill/Tool-Name + Δ-Summary
Exit 0 immer (fail-open, kein Block).
"""
import json
import os
import subprocess
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "post-tool-use-decisions.mjs"
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
        timeout=15,
    )


def test_hook_exits_zero_always():
    """Hook ist nie blockierend: exit 0 immer."""
    result = run_hook({})
    assert result.returncode == 0


def test_hook_ignores_non_write_tool():
    """Hook ignoriert Nicht-Write-Events."""
    payload = {
        "tool_name": "Read",
        "tool_input": {"file_path": "kapitel/kap1.md"},
    }
    result = run_hook(payload)
    assert result.returncode == 0


def test_hook_ignores_non_md_file(tmp_path):
    """Hook ignoriert Write-Events auf Nicht-MD-Dateien."""
    log_file = tmp_path / "decisions.log"
    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(tmp_path / "somefile.txt"),
            "content": "nicht relevant",
        },
    }
    env_overrides = {
        "ACADEMIC_DECISIONS_LOG": str(log_file),
        "CLAUDE_PROJECT_DIR": str(tmp_path),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0
    # Kein Log-Eintrag erwartet
    assert not log_file.exists() or log_file.read_text() == ""


def test_hook_logs_md_write(tmp_path):
    """Hook schreibt eine Log-Zeile bei Write auf *.md im Projekt."""
    log_file = tmp_path / "decisions.log"
    md_file = tmp_path / "notes.md"

    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(md_file),
            "content": "# Test\nNeuer Inhalt",
        },
    }
    env_overrides = {
        "ACADEMIC_DECISIONS_LOG": str(log_file),
        "CLAUDE_PROJECT_DIR": str(tmp_path),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"

    assert log_file.exists(), "decisions.log wurde nicht erstellt"
    log_content = log_file.read_text()
    assert len(log_content.strip()) > 0, "decisions.log ist leer"

    # Eine Zeile im Log
    lines = [l for l in log_content.strip().splitlines() if l.strip()]
    assert len(lines) >= 1, f"Erwartet mindestens 1 Log-Zeile, got {len(lines)}"


def test_hook_log_line_format(tmp_path):
    """Log-Zeile enthaelt Timestamp und Dateinamen."""
    log_file = tmp_path / "decisions.log"
    md_file = tmp_path / "kapitel" / "kap1.md"
    md_file.parent.mkdir(parents=True)

    payload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": str(md_file),
            "content": "# Kapitel 1\nErster Abschnitt",
        },
    }
    env_overrides = {
        "ACADEMIC_DECISIONS_LOG": str(log_file),
        "CLAUDE_PROJECT_DIR": str(tmp_path),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) >= 1

    # Log-Zeile soll ISO-Timestamp enthalten (Format: YYYY-MM-DD)
    first_line = lines[0]
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2}', first_line), f"Kein Timestamp in: {first_line}"
    # Und den Dateinamen
    assert "kap1.md" in first_line or "Write" in first_line, f"Dateiname/Tool fehlt in: {first_line}"


def test_hook_appends_multiple_writes(tmp_path):
    """Mehrere Write-Events haengen mehrere Zeilen an."""
    log_file = tmp_path / "decisions.log"
    project_dir = tmp_path

    for i in range(3):
        md_file = project_dir / f"doc{i}.md"
        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(md_file),
                "content": f"# Dokument {i}\nInhalt hier",
            },
        }
        env_overrides = {
            "ACADEMIC_DECISIONS_LOG": str(log_file),
            "CLAUDE_PROJECT_DIR": str(project_dir),
        }
        result = run_hook(payload, env_overrides=env_overrides)
        assert result.returncode == 0

    lines = [l for l in log_file.read_text().strip().splitlines() if l.strip()]
    assert len(lines) >= 3, f"Erwartet 3 Log-Zeilen, got {len(lines)}: {lines}"
