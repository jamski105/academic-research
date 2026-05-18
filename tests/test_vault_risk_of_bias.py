"""Tests fuer risk_of_bias Daten-Layer (Ticket #100).

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

from mcp.academic_vault.db import VaultDB
from mcp.academic_vault import server as vault_server


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

def test_risk_of_bias_table_exists():
    """Nach init_schema() muss risk_of_bias_assessments-Tabelle vorhanden sein."""
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
        assert "risk_of_bias_assessments" in names
    finally:
        os.unlink(db_path)


def test_risk_of_bias_table_columns():
    """risk_of_bias_assessments hat paper_id, study_type, domain_scores_json, ts."""
    db_path, db = make_temp_db()
    try:
        conn = sqlite3.connect(db_path)
        cols = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(risk_of_bias_assessments)"
            ).fetchall()
        }
        conn.close()
        assert "paper_id" in cols
        assert "study_type" in cols
        assert "domain_scores_json" in cols
        assert "ts" in cols
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# add_risk_of_bias
# ---------------------------------------------------------------------------

def test_add_risk_of_bias_returns_assessment_id():
    """add_risk_of_bias gibt non-empty assessment_id zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        assessment_id = vault_server.add_risk_of_bias(
            db_path=db_path,
            paper_id="p1",
            study_type="RCT",
            domain_scores={"D1": "Low", "D2": "High"},
        )
        assert assessment_id is not None
        assert len(assessment_id) > 0
    finally:
        os.unlink(db_path)


def test_add_risk_of_bias_persists_data():
    """add_risk_of_bias speichert alle Felder korrekt."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        scores = {"D1": "Low", "D2": "Some concerns", "overall": "Low"}
        assessment_id = vault_server.add_risk_of_bias(
            db_path=db_path,
            paper_id="p1",
            study_type="RCT",
            domain_scores=scores,
        )
        results = vault_server.list_risk_of_bias(db_path=db_path, paper_id="p1")
        assert len(results) == 1
        r = results[0]
        assert r["assessment_id"] == assessment_id
        assert r["paper_id"] == "p1"
        assert r["study_type"] == "RCT"
        import json
        stored_scores = json.loads(r["domain_scores_json"])
        assert stored_scores == scores
        assert r["ts"] > 0
    finally:
        os.unlink(db_path)


def test_add_risk_of_bias_accepts_dict_or_json_string():
    """add_risk_of_bias akzeptiert sowohl dict als auch JSON-String fuer domain_scores."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        import json
        scores_dict = {"D1": "Low"}
        vault_server.add_risk_of_bias(db_path, "p1", "observational", scores_dict)
        results = vault_server.list_risk_of_bias(db_path, paper_id="p1")
        stored = json.loads(results[0]["domain_scores_json"])
        assert stored == scores_dict
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# list_risk_of_bias
# ---------------------------------------------------------------------------

def test_list_risk_of_bias_filter_by_paper():
    """list_risk_of_bias(paper_id) gibt nur Assessments des Papers zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        _seed_paper(db_path, "p2")

        vault_server.add_risk_of_bias(db_path, "p1", "RCT", {"D1": "Low"})
        vault_server.add_risk_of_bias(db_path, "p2", "observational", {"D1": "High"})

        p1_results = vault_server.list_risk_of_bias(db_path, paper_id="p1")
        assert len(p1_results) == 1
        assert p1_results[0]["paper_id"] == "p1"
    finally:
        os.unlink(db_path)


def test_list_risk_of_bias_all_without_filter():
    """list_risk_of_bias() ohne paper_id gibt alle Assessments zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        _seed_paper(db_path, "p2")
        vault_server.add_risk_of_bias(db_path, "p1", "RCT", {"D1": "Low"})
        vault_server.add_risk_of_bias(db_path, "p2", "RCT", {"D1": "High"})

        all_results = vault_server.list_risk_of_bias(db_path)
        assert len(all_results) == 2
    finally:
        os.unlink(db_path)


def test_list_risk_of_bias_ordered_by_ts_desc():
    """list_risk_of_bias gibt Ergebnisse nach ts DESC sortiert zurueck."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path)
        vault_server.add_risk_of_bias(db_path, "p1", "RCT", {"D1": "Low"})
        vault_server.add_risk_of_bias(db_path, "p1", "RCT", {"D1": "High"})

        results = vault_server.list_risk_of_bias(db_path, paper_id="p1")
        assert len(results) == 2
        # Neuester zuerst
        assert results[0]["ts"] >= results[1]["ts"]
    finally:
        os.unlink(db_path)
