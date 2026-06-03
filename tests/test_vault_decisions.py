"""Tests fuer Decision-Log und Memory im Vault (Ticket #90).

TDD-First: Tests definieren das erwuenschte Verhalten bevor die Implementierung
in db.py / server.py hinzugefuegt wird.
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_temp_db() -> tuple[str, VaultDB]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = VaultDB(tmp.name)
    db.init_schema()
    return tmp.name, db


# ---------------------------------------------------------------------------
# Schema-Tests
# ---------------------------------------------------------------------------

def test_decisions_table_exists():
    """Nach init_schema() muss decisions-Tabelle vorhanden sein."""
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
        assert "decisions" in names
    finally:
        os.unlink(db_path)


def test_glossary_table_exists():
    """Nach init_schema() muss glossary-Tabelle vorhanden sein."""
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
        assert "glossary" in names
    finally:
        os.unlink(db_path)


def test_style_overrides_table_exists():
    """Nach init_schema() muss style_overrides-Tabelle vorhanden sein."""
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
        assert "style_overrides" in names
    finally:
        os.unlink(db_path)


def test_excluded_sources_table_exists():
    """Nach init_schema() muss excluded_sources-Tabelle vorhanden sein."""
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
        assert "excluded_sources" in names
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# add_decision / list_decisions
# ---------------------------------------------------------------------------

def test_add_decision_returns_id():
    """add_decision gibt non-empty decision_id zurueck."""
    db_path, db = make_temp_db()
    try:
        decision_id = vault_server.add_decision(
            db_path=db_path,
            category="methodology",
            text="Nur RCTs einschliessen.",
            rationale="Hoechste Evidenzqualitaet.",
        )
        assert decision_id is not None
        assert len(decision_id) > 0
    finally:
        os.unlink(db_path)


def test_add_decision_persists_fields():
    """add_decision speichert category, text und rationale korrekt."""
    db_path, db = make_temp_db()
    try:
        decision_id = vault_server.add_decision(
            db_path=db_path,
            category="scope",
            text="Nur Studien ab 2010.",
            rationale="Relevanz.",
        )
        decisions = vault_server.list_decisions(db_path=db_path)
        assert len(decisions) == 1
        d = decisions[0]
        assert d["decision_id"] == decision_id
        assert d["category"] == "scope"
        assert d["text"] == "Nur Studien ab 2010."
        assert d["rationale"] == "Relevanz."
    finally:
        os.unlink(db_path)


def test_list_decisions_filter_by_category():
    """list_decisions(category='x') gibt nur Decisions der Kategorie x zurueck."""
    db_path, db = make_temp_db()
    try:
        vault_server.add_decision(db_path, "scope", "Decision A", "R1")
        vault_server.add_decision(db_path, "methodology", "Decision B", "R2")
        vault_server.add_decision(db_path, "scope", "Decision C", "R3")

        scope_decisions = vault_server.list_decisions(db_path=db_path, category="scope")
        assert len(scope_decisions) == 2
        for d in scope_decisions:
            assert d["category"] == "scope"

        method_decisions = vault_server.list_decisions(db_path=db_path, category="methodology")
        assert len(method_decisions) == 1
        assert method_decisions[0]["text"] == "Decision B"
    finally:
        os.unlink(db_path)


def test_list_decisions_active_only():
    """list_decisions(active_only=True) filtert superseded Decisions heraus."""
    db_path, db = make_temp_db()
    try:
        id1 = vault_server.add_decision(db_path, "scope", "Old Decision", "Old")
        id2 = vault_server.add_decision(db_path, "scope", "New Decision", "New")

        # Erste Decision superseden
        vault_server.supersede_decision(db_path=db_path, decision_id=id1, superseded_by=id2)

        all_decisions = vault_server.list_decisions(db_path=db_path, active_only=False)
        assert len(all_decisions) == 2

        active = vault_server.list_decisions(db_path=db_path, active_only=True)
        assert len(active) == 1
        assert active[0]["decision_id"] == id2
    finally:
        os.unlink(db_path)


def test_list_decisions_no_args_returns_all_active():
    """list_decisions() ohne Argumente gibt alle aktiven Decisions zurueck."""
    db_path, db = make_temp_db()
    try:
        vault_server.add_decision(db_path, "scope", "A", "R")
        vault_server.add_decision(db_path, "methodology", "B", "R")
        decisions = vault_server.list_decisions(db_path=db_path)
        assert len(decisions) == 2
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# excluded_sources
# ---------------------------------------------------------------------------

def test_add_excluded_source_persists():
    """add_excluded_source speichert paper_id und reason."""
    db_path, db = make_temp_db()
    try:
        vault_server.add_excluded_source(
            db_path=db_path,
            paper_id="p-excluded",
            reason="Off-topic",
        )
        excluded = vault_server.list_excluded_sources(db_path=db_path)
        assert len(excluded) == 1
        assert excluded[0]["paper_id"] == "p-excluded"
        assert excluded[0]["reason"] == "Off-topic"
    finally:
        os.unlink(db_path)


def test_is_excluded_returns_true_for_excluded_paper():
    """is_excluded(paper_id) gibt True zurueck wenn paper_id in excluded_sources."""
    db_path, db = make_temp_db()
    try:
        vault_server.add_excluded_source(db_path, "p-ex", "Duplicate")
        assert vault_server.is_excluded(db_path=db_path, paper_id="p-ex") is True
        assert vault_server.is_excluded(db_path=db_path, paper_id="p-other") is False
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Migration-Idempotenz
# ---------------------------------------------------------------------------

def test_add_v64_tables_idempotent():
    """add_v64_tables() kann mehrfach aufgerufen werden ohne Fehler."""
    db_path, db = make_temp_db()
    try:
        from academic_vault.migrate import add_v64_tables
        # Zweiter Aufruf (erster ist implizit via init_schema in make_temp_db)
        add_v64_tables(db_path)
        add_v64_tables(db_path)
        # Kein Fehler = bestanden
    finally:
        os.unlink(db_path)
