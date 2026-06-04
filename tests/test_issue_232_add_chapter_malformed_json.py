"""Regressionstest fuer Issue #232.

add_chapter() fing fehlerhaftes csl_json mit ``except Exception: pass`` ab,
sodass das originale (malformed) JSON unveraendert an add_paper() durchgereicht
und dort still als ``article-journal`` klassifiziert wurde -- ein Buchkapitel
landete so mit falschem Typ im Vault und die Typ-Validierung war unterlaufen.

Akzeptanzkriterium: Malformed csl_json an add_chapter fuehrt zu einem klaren
Error statt stiller Fehlklassifikation.
"""
import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_vault import server
from academic_vault.db import VaultDB


PARENT_ID = "buch_2024"


def _make_db_path() -> str:
    """Erstellt temporaere DB-Datei, initialisiert Schema und legt Parent-Buch an.

    Der Parent muss existieren, weil chapter.parent_paper_id eine FOREIGN-KEY-
    Referenz auf papers(paper_id) traegt. So bleibt als einzige Fehlerquelle in
    den Malformed-Tests tatsaechlich nur das fehlerhafte csl_json.
    """
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tf.name
    tf.close()
    db = VaultDB(db_path)
    db.init_schema()
    db.add_paper(
        paper_id=PARENT_ID,
        csl_json=json.dumps({"type": "book", "title": "Testbuch"}),
    )
    return db_path


def test_add_chapter_malformed_json_raises():
    """Malformed csl_json -> klarer ValueError statt stiller Fehlklassifikation."""
    db_path = _make_db_path()
    malformed = '{"type": "chapter", "title": "Kaputt"'  # fehlende schliessende Klammer
    with pytest.raises(ValueError, match="csl_json"):
        server.add_chapter(
            db_path=db_path,
            parent_paper_id=PARENT_ID,
            chapter_number=3,
            csl_json=malformed,
        )


def test_add_chapter_malformed_json_not_stored_as_article():
    """Bei malformed csl_json darf KEIN Kapitel still als article-journal landen."""
    db_path = _make_db_path()
    malformed = "das ist gar kein json"
    paper_id = "buch_2024-ch3"
    with pytest.raises(ValueError):
        server.add_chapter(
            db_path=db_path,
            parent_paper_id=PARENT_ID,
            chapter_number=3,
            csl_json=malformed,
            paper_id=paper_id,
        )
    # Es darf nichts (insb. kein article-journal) persistiert worden sein.
    assert server.get_paper(db_path, paper_id) is None


def test_add_chapter_valid_json_still_works():
    """Gueltiges csl_json wird weiterhin korrekt als chapter gespeichert."""
    db_path = _make_db_path()
    csl = json.dumps({"title": "Kapitel 3: Methoden"})  # type fehlt absichtlich
    paper_id = server.add_chapter(
        db_path=db_path,
        parent_paper_id=PARENT_ID,
        chapter_number=3,
        csl_json=csl,
    )
    paper = server.get_paper(db_path, paper_id)
    assert paper is not None
    assert paper["type"] == "chapter"
