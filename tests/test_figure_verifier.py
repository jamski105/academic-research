"""Tests fuer figure-verifier Vault-Schicht."""
import json
import sqlite3
import time
import pytest
from pathlib import Path


@pytest.fixture
def db_path(tmp_path):
    """Temporaere SQLite-DB mit vollstaendigem Schema."""
    from mcp.academic_vault.db import VaultDB
    path = str(tmp_path / "test_vault.db")
    db = VaultDB(path)
    db.init_schema()
    return path


@pytest.fixture
def paper_id(db_path):
    """Legt Test-Paper an und gibt paper_id zurueck."""
    from mcp.academic_vault.server import add_paper
    pid = "test-paper-001"
    add_paper(
        db_path=db_path,
        paper_id=pid,
        csl_json=json.dumps({"title": "Test Paper", "type": "article-journal"}),
    )
    return pid


def test_figures_table_exists(db_path):
    """figures-Tabelle muss nach init_schema() existieren."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='figures'"
    ).fetchone()
    conn.close()
    assert row is not None, "figures-Tabelle nicht gefunden"


def test_add_figures_table_idempotent(tmp_path):
    """add_figures_table() darf mehrfach ausgefuehrt werden."""
    from mcp.academic_vault.db import VaultDB
    from mcp.academic_vault.migrate import add_figures_table

    path = str(tmp_path / "migrate_test.db")
    db = VaultDB(path)
    db.init_schema()

    # Erste Ausfuehrung
    add_figures_table(path)
    # Zweite Ausfuehrung — darf keinen Fehler werfen
    add_figures_table(path)

    conn = sqlite3.connect(path)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='figures'"
    ).fetchone()
    conn.close()
    assert row is not None
