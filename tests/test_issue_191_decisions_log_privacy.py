"""Regressionstests fuer Issue #191.

Security-Audit Round-2 Finding H2 (CWE-532): Insertion of Sensitive
Information into Log File.

`hooks/post-tool-use-decisions.mjs` schrieb bei jedem Write auf eine `.md`-Datei
die ersten 60 Zeichen der ersten Zeile (Content-Snippet) im Klartext in
`~/.academic-research/decisions.log`. Das Log hatte keine 0600-Permissions und
keine Rotation.

Akzeptanzkriterien (aus dem Issue):
- `delta`-Feld entfernen oder durch SHA-256-Hash ersetzen (Idempotenz-Check)
- Log mit 0600-Permissions erstellen
- Rotation: max 10 MB pro Logfile, dann `decisions.log.1`
- README-Sektion "Privacy/Logs" anlegen
"""
import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "post-tool-use-decisions.mjs"
README_PATH = Path(__file__).parent.parent / "README.md"


def run_hook(payload: dict, env_overrides: dict = None) -> subprocess.CompletedProcess:
    """Startet den Hook als Node.js-Subprocess mit JSON-Eingabe auf stdin."""
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


def _write_md(tmp_path, log_file, content):
    md_file = tmp_path / "notes.md"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(md_file), "content": content},
    }
    env_overrides = {
        "ACADEMIC_DECISIONS_LOG": str(log_file),
        "CLAUDE_PROJECT_DIR": str(tmp_path),
    }
    return run_hook(payload, env_overrides=env_overrides)


def test_log_does_not_leak_content_snippet(tmp_path):
    """Das Log darf KEIN Klartext-Content-Snippet enthalten (CWE-532)."""
    log_file = tmp_path / "decisions.log"
    # Geheimnis kurz genug, dass es bei <=60 Zeichen Snippet komplett geleakt wuerde.
    secret = "GEHEIM-PII-Mustermann"
    content = f"# {secret} Klartext-Zitat\nweiterer Inhalt"

    result = _write_md(tmp_path, log_file, content)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    log_content = log_file.read_text()
    assert secret not in log_content, (
        f"Content-Snippet im Klartext geleakt: {log_content!r}"
    )


def test_log_contains_sha256_hash(tmp_path):
    """Statt Content-Snippet steht ein SHA-256-Hash (Idempotenz-Check)."""
    log_file = tmp_path / "decisions.log"
    result = _write_md(tmp_path, log_file, "# Titel\nInhalt")
    assert result.returncode == 0, f"stderr: {result.stderr}"

    line = log_file.read_text().strip().splitlines()[0]
    # 64 Hex-Zeichen irgendwo in der Zeile (SHA-256)
    assert re.search(r"[0-9a-f]{64}", line), (
        f"Kein SHA-256-Hash in Log-Zeile: {line!r}"
    )


def test_log_hash_is_stable_for_same_content(tmp_path):
    """Gleicher Inhalt -> gleicher Hash (Idempotenz)."""
    log_file = tmp_path / "decisions.log"
    _write_md(tmp_path, log_file, "# Stabil\nGleicher Inhalt")
    _write_md(tmp_path, log_file, "# Stabil\nGleicher Inhalt")

    lines = [l for l in log_file.read_text().strip().splitlines() if l.strip()]
    assert len(lines) >= 2
    hashes = [re.search(r"[0-9a-f]{64}", l).group(0) for l in lines[:2]]
    assert hashes[0] == hashes[1], "Hash nicht stabil fuer gleichen Inhalt"


def test_log_file_has_0600_permissions(tmp_path):
    """decisions.log muss mit 0600-Permissions erstellt werden."""
    log_file = tmp_path / "decisions.log"
    result = _write_md(tmp_path, log_file, "# Titel\nInhalt")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert log_file.exists()

    mode = stat.S_IMODE(log_file.stat().st_mode)
    assert mode == 0o600, f"Erwartet 0600, got {oct(mode)}"


def test_log_rotation_at_10mb(tmp_path):
    """Bei >10 MB wird zu decisions.log.1 rotiert."""
    log_file = tmp_path / "decisions.log"
    # Pre-fill ueber 10 MB
    log_file.write_text("X" * (11 * 1024 * 1024))

    result = _write_md(tmp_path, log_file, "# Neu\nInhalt")
    assert result.returncode == 0, f"stderr: {result.stderr}"

    rotated = tmp_path / "decisions.log.1"
    assert rotated.exists(), "Rotation hat decisions.log.1 nicht erzeugt"
    # Neues Log enthaelt nur den neuen (kleinen) Eintrag
    assert log_file.stat().st_size < 1024 * 1024


def test_readme_has_privacy_logs_section():
    """README enthaelt eine Privacy/Logs-Sektion."""
    text = README_PATH.read_text()
    assert re.search(r"^#+\s*Privacy", text, re.MULTILINE | re.IGNORECASE), (
        "Keine Privacy/Logs-Sektion in README.md gefunden"
    )
    # Erwaehnt decisions.log und 0600
    assert "decisions.log" in text
    assert "0600" in text
