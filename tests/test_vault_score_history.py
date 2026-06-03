"""Tests fuer Score-Trajectory-Tracking Daten-Layer (Ticket #102).

TDD-First: Tests definieren das erwuenschte Verhalten.
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path

import pytest

_WORKTREE_ROOT = Path(__file__).parent.parent
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

from academic_vault.db import VaultDB
from academic_vault import server as vault_server


def make_temp_db() -> tuple[str, VaultDB]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = VaultDB(tmp.name)
    db.init_schema()
    return tmp.name, db


def _seed_paper(db_path: str, paper_id: str = "p1") -> None:
    db = VaultDB(db_path)
    db.add_paper(paper_id, '{"title": "Test Paper", "type": "article-journal"}')


# ---------------------------------------------------------------------------
# Schema-Tests
# ---------------------------------------------------------------------------

def test_score_history_table_exists():
    """Nach init_schema() muss score_history-Tabelle vorhanden sein."""
    db_path, db = make_temp_db()
    try:
        conn = sqlite3.connect(db_path)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "score_history" in names
    finally:
        os.unlink(db_path)


def test_score_history_columns():
    """score_history hat paper_id, session_id, ts, scores_json."""
    db_path, db = make_temp_db()
    try:
        conn = sqlite3.connect(db_path)
        cols = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(score_history)"
            ).fetchall()
        }
        conn.close()
        assert "paper_id" in cols
        assert "session_id" in cols
        assert "ts" in cols
        assert "scores_json" in cols
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# add_score_snapshot
# ---------------------------------------------------------------------------

def test_add_score_snapshot_returns_snapshot_id():
    """add_score_snapshot gibt non-empty snapshot_id zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        snap_id = vault_server.add_score_snapshot(
            db_path=db_path,
            paper_id="p1",
            session_id="sess-001",
            scores={"relevance": 0.85, "quality": 0.7},
        )
        assert snap_id is not None
        assert len(snap_id) > 0
    finally:
        os.unlink(db_path)


def test_add_score_snapshot_persists_all_fields():
    """add_score_snapshot speichert paper_id, session_id, scores korrekt."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        scores = {"relevance": 0.9, "quality": 0.8, "novelty": 0.6}
        snap_id = vault_server.add_score_snapshot(
            db_path=db_path,
            paper_id="p1",
            session_id="sess-abc",
            scores=scores,
        )
        history = vault_server.get_score_history(db_path=db_path, paper_id="p1")
        assert len(history) == 1
        h = history[0]
        assert h["snapshot_id"] == snap_id
        assert h["paper_id"] == "p1"
        assert h["session_id"] == "sess-abc"
        assert h["ts"] > 0
        import json
        stored_scores = json.loads(h["scores_json"])
        assert stored_scores == scores
    finally:
        os.unlink(db_path)


def test_add_score_snapshot_accepts_dict_or_json():
    """add_score_snapshot akzeptiert dict als scores-Argument."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        vault_server.add_score_snapshot(db_path, "p1", "s1", {"r": 0.5})
        history = vault_server.get_score_history(db_path, paper_id="p1")
        assert len(history) == 1
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# get_score_history
# ---------------------------------------------------------------------------

def test_get_score_history_returns_most_recent_first():
    """get_score_history gibt Snapshots nach ts DESC sortiert zurueck."""
    import time
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        vault_server.add_score_snapshot(db_path, "p1", "s1", {"r": 0.5})
        vault_server.add_score_snapshot(db_path, "p1", "s2", {"r": 0.7})
        vault_server.add_score_snapshot(db_path, "p1", "s3", {"r": 0.9})

        history = vault_server.get_score_history(db_path, paper_id="p1")
        assert len(history) == 3
        assert history[0]["ts"] >= history[1]["ts"]
        assert history[1]["ts"] >= history[2]["ts"]
    finally:
        os.unlink(db_path)


def test_get_score_history_k_limits_results():
    """get_score_history(k=2) gibt maximal 2 Eintraege zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        for i in range(5):
            vault_server.add_score_snapshot(db_path, "p1", f"s{i}", {"r": i * 0.1})
        history = vault_server.get_score_history(db_path, paper_id="p1", k=2)
        assert len(history) == 2
    finally:
        os.unlink(db_path)


def test_get_score_history_empty_for_unknown_paper():
    """get_score_history gibt leere Liste fuer unbekanntes paper_id zurueck."""
    db_path, db = make_temp_db()
    try:
        history = vault_server.get_score_history(db_path, paper_id="unknown")
        assert history == []
    finally:
        os.unlink(db_path)


def test_get_score_history_multiple_papers_isolated():
    """get_score_history gibt nur Snapshots des angegebenen Papers zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        _seed_paper(db_path, "p2")
        vault_server.add_score_snapshot(db_path, "p1", "s1", {"r": 0.5})
        vault_server.add_score_snapshot(db_path, "p2", "s1", {"r": 0.9})

        h1 = vault_server.get_score_history(db_path, paper_id="p1")
        assert len(h1) == 1
        assert h1[0]["paper_id"] == "p1"
    finally:
        os.unlink(db_path)
