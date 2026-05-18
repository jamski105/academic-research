"""Tests fuer Material Passport / Repro-Lock (Ticket #104).

TDD-First: Tests definieren das erwuenschte Verhalten.
"""
import hashlib
import json
import os
import sys
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


def _seed_paper(db_path: str, paper_id: str = "p1", doi: str = "10.1234/test") -> None:
    db = VaultDB(db_path)
    db.add_paper(
        paper_id,
        f'{{"title": "Test Paper", "type": "article-journal", "DOI": "{doi}"}}',
        doi=doi,
    )


# ---------------------------------------------------------------------------
# Schema-Tests: vault_locked_status
# ---------------------------------------------------------------------------

def test_vault_locked_status_table_exists():
    """Nach init_schema() muss vault_locked_status-Tabelle vorhanden sein."""
    db_path, db = make_temp_db()
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "vault_locked_status" in names
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# lock_passport / is_locked
# ---------------------------------------------------------------------------

def test_is_locked_returns_false_by_default():
    """is_locked(slug) gibt False zurueck wenn kein Lock gesetzt wurde."""
    db_path, db = make_temp_db()
    try:
        result = vault_server.is_locked(db_path=db_path, slug="my-project")
        assert result is False
    finally:
        os.unlink(db_path)


def test_lock_passport_sets_locked():
    """lock_passport(slug) setzt is_locked(slug) auf True."""
    db_path, db = make_temp_db()
    try:
        vault_server.lock_passport(db_path=db_path, slug="my-project")
        assert vault_server.is_locked(db_path=db_path, slug="my-project") is True
    finally:
        os.unlink(db_path)


def test_lock_passport_idempotent():
    """lock_passport kann mehrfach aufgerufen werden ohne Fehler."""
    db_path, db = make_temp_db()
    try:
        vault_server.lock_passport(db_path=db_path, slug="proj")
        vault_server.lock_passport(db_path=db_path, slug="proj")
        assert vault_server.is_locked(db_path=db_path, slug="proj") is True
    finally:
        os.unlink(db_path)


def test_lock_is_per_slug():
    """Locks sind slug-spezifisch — anderer Slug bleibt unlocked."""
    db_path, db = make_temp_db()
    try:
        vault_server.lock_passport(db_path=db_path, slug="proj-A")
        assert vault_server.is_locked(db_path=db_path, slug="proj-A") is True
        assert vault_server.is_locked(db_path=db_path, slug="proj-B") is False
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# export_material_passport
# ---------------------------------------------------------------------------

def test_export_material_passport_creates_file(tmp_path):
    """export_material_passport schreibt material-passport.json in output_dir."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="test-project",
            output_dir=str(tmp_path),
        )
        passport_file = tmp_path / "material-passport.json"
        assert passport_file.exists(), "material-passport.json wurde nicht erstellt"
    finally:
        os.unlink(db_path)


def test_export_material_passport_valid_json(tmp_path):
    """export_material_passport schreibt gueltiges JSON."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="test-project",
            output_dir=str(tmp_path),
        )
        passport_file = tmp_path / "material-passport.json"
        data = json.loads(passport_file.read_text())
        assert isinstance(data, dict)
    finally:
        os.unlink(db_path)


def test_export_material_passport_required_fields(tmp_path):
    """material-passport.json enthaelt alle Pflichtfelder."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1", doi="10.9999/abc")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="test-project",
            output_dir=str(tmp_path),
        )
        data = json.loads((tmp_path / "material-passport.json").read_text())
        # Pflichtfelder gemaess Ticket #104
        assert "slug" in data
        assert "paper_ids" in data
        assert "dois" in data
        assert "score_algo_version" in data
        assert "plugin_version" in data
        assert "decisions_snapshot" in data
        assert "passport_hash" in data
        assert "created_at" in data
    finally:
        os.unlink(db_path)


def test_export_material_passport_contains_paper_ids(tmp_path):
    """material-passport.json enthaelt alle paper_ids aus dem Vault."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1", doi="10.1/a")
        _seed_paper(db_path, "p2", doi="10.2/b")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="multi-paper",
            output_dir=str(tmp_path),
        )
        data = json.loads((tmp_path / "material-passport.json").read_text())
        assert "p1" in data["paper_ids"]
        assert "p2" in data["paper_ids"]
    finally:
        os.unlink(db_path)


def test_export_material_passport_decisions_snapshot(tmp_path):
    """material-passport.json enthaelt aktuelle Decisions als Snapshot."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        vault_server.add_decision(db_path, "scope", "Nur RCTs", "Qualitaet")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="proj",
            output_dir=str(tmp_path),
        )
        data = json.loads((tmp_path / "material-passport.json").read_text())
        assert len(data["decisions_snapshot"]) == 1
        assert data["decisions_snapshot"][0]["text"] == "Nur RCTs"
    finally:
        os.unlink(db_path)


def test_export_material_passport_passport_hash_is_sha256(tmp_path):
    """passport_hash ist ein gueltiger SHA-256 Hex-String (64 Zeichen)."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="proj",
            output_dir=str(tmp_path),
        )
        data = json.loads((tmp_path / "material-passport.json").read_text())
        h = data["passport_hash"]
        assert len(h) == 64
        int(h, 16)  # wirft ValueError wenn kein gueltiger Hex-String
    finally:
        os.unlink(db_path)


def test_export_material_passport_schema_validates(tmp_path):
    """material-passport.json besteht JSON-Schema-Validierung."""
    db_path, db = make_temp_db()
    try:
        _seed_paper(db_path, "p1")
        vault_server.export_material_passport(
            db_path=db_path,
            slug="proj",
            output_dir=str(tmp_path),
        )
        from mcp.academic_vault.material_passport import validate_passport
        data = json.loads((tmp_path / "material-passport.json").read_text())
        # validate_passport wirft bei Fehler
        validate_passport(data)
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Migration-Idempotenz
# ---------------------------------------------------------------------------

def test_v64_migration_idempotent_for_passport():
    """add_v64_tables() ist idempotent bezueglich vault_locked_status."""
    db_path, db = make_temp_db()
    try:
        from mcp.academic_vault.migrate import add_v64_tables
        add_v64_tables(db_path)
        add_v64_tables(db_path)
    finally:
        os.unlink(db_path)
