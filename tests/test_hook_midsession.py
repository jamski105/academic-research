"""Tests fuer mid-session-reinforcement.mjs Notification-Hook.

Der Hook ist nicht-blockierend (Notification-Hook).
Trigger: nach jeder 20. User-Message oder nach Compaction.
Liest Top-5 aktive Decisions aus Vault und erinnert Modell als System-Hint.
Max 1× pro 20 Messages.
Exit 0 immer.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "mid-session-reinforcement.mjs"
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
    """Hook ist immer exit 0 (Notification-Hook, nie blockierend)."""
    result = run_hook({})
    assert result.returncode == 0


def test_hook_exits_zero_on_notification_event():
    """Hook verarbeitet Notification-Event ohne Fehler."""
    payload = {
        "hook_event_name": "Notification",
        "message_count": 20,
    }
    result = run_hook(payload)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"


def test_hook_outputs_hint_at_message_20(tmp_path):
    """Hook gibt System-Hint aus wenn message_count == 20."""
    # Erstelle Vault mit Decisions
    sys.path.insert(0, str(WORKTREE_ROOT))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_decision

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()

    add_decision(db_path, category="Zitierstil", text="APA 7th Edition verwenden", rationale="Fachbereich-Standard")
    add_decision(db_path, category="Methodik", text="Systematisches Review nach PRISMA", rationale="Qualitaetsanforderung")

    state_file = tmp_path / "reinforcement_state.json"

    payload = {
        "hook_event_name": "Notification",
        "message_count": 20,
    }
    env_overrides = {
        "VAULT_DB_PATH": db_path,
        "ACADEMIC_REINFORCEMENT_STATE": str(state_file),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"

    # Hook soll Reminder ausgeben (stdout oder stderr)
    combined = result.stdout + result.stderr
    # Hint soll Decisions enthalten
    assert "APA" in combined or "PRISMA" in combined or "Decision" in combined or "Aktive" in combined, \
        f"Kein Decision-Hint in Ausgabe: stdout={result.stdout!r}, stderr={result.stderr!r}"


def test_hook_no_output_at_message_10(tmp_path):
    """Hook gibt keinen Hint aus wenn message_count < 20."""
    sys.path.insert(0, str(WORKTREE_ROOT))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_decision

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_decision(db_path, category="test", text="Testdecision", rationale=None)

    state_file = tmp_path / "reinforcement_state.json"

    payload = {
        "hook_event_name": "Notification",
        "message_count": 10,
    }
    env_overrides = {
        "VAULT_DB_PATH": db_path,
        "ACADEMIC_REINFORCEMENT_STATE": str(state_file),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0
    # Bei < 20 Messages: kein Reminder
    combined = result.stdout + result.stderr
    assert "Aktive Decisions" not in combined, f"Unerwarteter Hint bei 10 Messages: {combined}"


def test_hook_fires_max_once_per_20_messages(tmp_path):
    """Hook loest max 1× pro 20 Messages aus (State-Datei verhindert Duplikate)."""
    sys.path.insert(0, str(WORKTREE_ROOT))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_decision

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_decision(db_path, category="test", text="Entscheidung A", rationale=None)

    state_file = tmp_path / "reinforcement_state.json"
    env_overrides = {
        "VAULT_DB_PATH": db_path,
        "ACADEMIC_REINFORCEMENT_STATE": str(state_file),
    }

    # Erster Aufruf bei message_count=20 -> Hint
    payload = {"hook_event_name": "Notification", "message_count": 20}
    result1 = run_hook(payload, env_overrides=env_overrides)
    assert result1.returncode == 0
    combined1 = result1.stdout + result1.stderr

    # Zweiter Aufruf bei message_count=20 (gleiche Runde) -> kein Hint
    result2 = run_hook(payload, env_overrides=env_overrides)
    assert result2.returncode == 0
    combined2 = result2.stdout + result2.stderr

    # Erster Aufruf hat Hint; zweiter Aufruf nicht
    has_hint1 = "Aktive Decisions" in combined1 or "Entscheidung" in combined1
    has_hint2 = "Aktive Decisions" in combined2 or "Entscheidung" in combined2

    assert has_hint1, f"Erster Aufruf sollte Hint haben: {combined1!r}"
    assert not has_hint2, f"Zweiter Aufruf sollte keinen Hint haben: {combined2!r}"


def test_hook_triggers_after_compaction(tmp_path):
    """Hook gibt Hint aus nach Compaction-Event unabhaengig von message_count."""
    sys.path.insert(0, str(WORKTREE_ROOT))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_decision

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_decision(db_path, category="Methodik", text="Qualitative Analyse", rationale=None)

    state_file = tmp_path / "reinforcement_state.json"

    payload = {
        "hook_event_name": "PostCompact",
        "message_count": 5,  # < 20, aber Compaction
    }
    env_overrides = {
        "VAULT_DB_PATH": db_path,
        "ACADEMIC_REINFORCEMENT_STATE": str(state_file),
    }

    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0, f"Erwartet 0, got {result.returncode}. stderr: {result.stderr}"

    combined = result.stdout + result.stderr
    assert "Qualitative" in combined or "Aktive" in combined or "Decision" in combined, \
        f"Kein Hint nach Compaction: stdout={result.stdout!r}, stderr={result.stderr!r}"


def test_hook_failopen_when_vault_missing():
    """Hook ist fail-open wenn Vault-DB nicht existiert."""
    payload = {
        "hook_event_name": "Notification",
        "message_count": 20,
    }
    env_overrides = {
        "VAULT_DB_PATH": "/nonexistent/vault.db",
        "ACADEMIC_REINFORCEMENT_STATE": "/tmp/test_state_nonexistent.json",
    }
    result = run_hook(payload, env_overrides=env_overrides)
    assert result.returncode == 0, f"Erwartet 0 (fail-open), got {result.returncode}. stderr: {result.stderr}"
