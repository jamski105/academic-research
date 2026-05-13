"""Tests fuer Vault add_paper mit type=book und type=chapter."""
import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.academic_vault.db import VaultDB


def _make_db() -> tuple:
    """Erstellt temporaere DB-Datei und initialisiert Schema."""
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tf.name
    tf.close()
    db = VaultDB(db_path)
    db.init_schema()
    return db_path, db


def test_add_paper_type_book():
    """add_paper mit type=book, editor -> get_paper gibt alle Felder zurueck."""
    db_path, db = _make_db()
    editors = json.dumps([{"family": "Mueller", "given": "Hans"}])
    csl = json.dumps({
        "type": "book",
        "title": "Testbuch",
        "editor": [{"family": "Mueller", "given": "Hans"}],
        "publisher": "Hanser",
    })
    db.add_paper(
        paper_id="testbuch_2024",
        csl_json=csl,
        isbn="9783446461031",
        editor=editors,
    )
    paper = db.get_paper("testbuch_2024")
    assert paper is not None
    assert paper["editor"] == editors


def test_add_paper_type_chapter():
    """add_paper mit type=chapter, container_title, page_first, page_last."""
    db_path, db = _make_db()
    csl = json.dumps({
        "type": "chapter",
        "title": "Kapitel 3: Methoden",
        "container-title": "Handbuch der Forschung",
    })
    db.add_paper(
        paper_id="kapitel3_2024",
        csl_json=csl,
        chapter="3",
        page_first=45,
        page_last=78,
        container_title="Handbuch der Forschung",
    )
    paper = db.get_paper("kapitel3_2024")
    assert paper is not None
    assert paper["chapter"] == "3"
    assert paper["page_first"] == 45
    assert paper["page_last"] == 78
    assert paper["container_title"] == "Handbuch der Forschung"


def test_add_paper_invalid_type():
    """Ungueltiger type-Wert -> ValueError."""
    db_path, db = _make_db()
    csl = json.dumps({"type": "unknown-type", "title": "Test"})
    with pytest.raises(ValueError, match="Ungueltiger type"):
        db.add_paper(paper_id="bad_type", csl_json=csl)


def test_migration_idempotent():
    """add_book_columns() kann mehrfach aufgerufen werden ohne Fehler."""
    from mcp.academic_vault.migrate import add_book_columns
    db_path, _ = _make_db()
    add_book_columns(db_path)  # Erster Aufruf
    add_book_columns(db_path)  # Zweiter Aufruf -- darf nicht scheitern


def test_old_paper_still_readable():
    """Bestehende article-journal-Papers funktionieren weiterhin."""
    db_path, db = _make_db()
    csl = json.dumps({"type": "article-journal", "title": "Alter Artikel"})
    db.add_paper(paper_id="alter_artikel", csl_json=csl, doi="10.1234/test")
    paper = db.get_paper("alter_artikel")
    assert paper is not None
    assert paper["doi"] == "10.1234/test"
