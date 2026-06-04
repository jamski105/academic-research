"""Regressionstest fuer Issue #213.

vault.add_paper darf bei malformed-JSON oder fehlendem Pflichtfeld 'type'
NICHT still einen Default 'article-journal' setzen, sondern muss einen
ValueError werfen (Halluzinationsschutz / Security Round-2 M3).
"""
import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_vault import server as vault_server
from academic_vault.db import VaultDB


def _make_db_path() -> str:
    """Erstellt temporaere DB-Datei mit initialisiertem Schema.

    Schema wird vorab angelegt, damit ein 'kein Eintrag entstanden'-Assert
    auch dann greift, wenn die Validierung erst nach init_schema zuschlaegt
    bzw. ueberhaupt keine Tabelle anlegen soll.
    """
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tf.name
    tf.close()
    db = VaultDB(db_path)
    db.init_schema()
    return db_path


# ---------------------------------------------------------------------------
# Entry-Point: server.add_paper (das ist der MCP-Eingang fuer Skills)
# ---------------------------------------------------------------------------

def test_server_add_paper_missing_type_raises():
    """Fehlendes Pflichtfeld 'type' -> ValueError, kein silent insert."""
    db_path = _make_db_path()
    csl = json.dumps({"title": "Ein Buchkapitel ohne type"})
    with pytest.raises(ValueError):
        vault_server.add_paper(db_path, "no_type_2024", csl)
    # Es darf KEIN (faelschlich als article-journal getaggter) Eintrag entstehen.
    assert vault_server.get_paper(db_path, "no_type_2024") is None


def test_server_add_paper_malformed_json_raises():
    """Kaputtes JSON -> ValueError, kein silent default 'article-journal'."""
    db_path = _make_db_path()
    malformed = '{"type": "book", "title": "abgeschnitten'  # ungueltiges JSON
    with pytest.raises(ValueError):
        vault_server.add_paper(db_path, "broken_json_2024", malformed)
    assert vault_server.get_paper(db_path, "broken_json_2024") is None


def test_server_add_paper_invalid_type_raises():
    """Unbekannter type-Wert -> ValueError (keine stillschweigende Korrektur)."""
    db_path = _make_db_path()
    csl = json.dumps({"type": "blog-post", "title": "Kein gueltiger CSL-Typ"})
    with pytest.raises(ValueError):
        vault_server.add_paper(db_path, "bad_type_2024", csl)
    assert vault_server.get_paper(db_path, "bad_type_2024") is None


def test_server_add_paper_valid_chapter_still_works():
    """Gueltiges Buchkapitel wird korrekt mit type=chapter persistiert."""
    db_path = _make_db_path()
    csl = json.dumps({"type": "chapter", "title": "Kapitel 1"})
    vault_server.add_paper(db_path, "ok_chapter_2024", csl, page_first=1, page_last=20)
    paper = vault_server.get_paper(db_path, "ok_chapter_2024")
    assert paper is not None
    assert paper["type"] == "chapter"


# ---------------------------------------------------------------------------
# DB-Layer: malformed JSON darf nicht mehr stillschweigend defaulten
# ---------------------------------------------------------------------------

def test_db_add_paper_malformed_json_raises():
    """db.add_paper: kaputtes JSON -> ValueError statt silent article-journal."""
    db_path = _make_db_path()
    db = VaultDB(db_path)
    db.init_schema()
    with pytest.raises(ValueError):
        db.add_paper("broken_db_2024", '{"type": "book"')  # abgeschnittenes JSON
    assert db.get_paper("broken_db_2024") is None
