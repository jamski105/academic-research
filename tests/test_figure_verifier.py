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


def test_add_and_get_figure(db_path, paper_id):
    """add_figure() legt Eintrag an; get_figure() gibt ihn zurueck."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    figure_id = db.add_figure(
        paper_id=paper_id,
        page=5,
        caption="Abb. 3.1: Uebersicht der Methoden",
        vlm_description="Ein Balkendiagramm zeigt Messwerte fuer fuenf Experimente.",
        data_extracted_json=None,
    )
    assert isinstance(figure_id, str) and len(figure_id) > 0

    record = db.get_figure(figure_id)
    assert record is not None
    assert record["paper_id"] == paper_id
    assert record["caption"] == "Abb. 3.1: Uebersicht der Methoden"
    assert record["page"] == 5


def test_list_figures_empty(db_path):
    """list_figures gibt leere Liste fuer unbekannte paper_id."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    result = db.list_figures("unknown-paper-xyz")
    assert result == []


def test_list_figures_ordered_by_page(db_path, paper_id):
    """list_figures gibt Eintraege nach page sortiert zurueck."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.add_figure(paper_id=paper_id, page=10, caption="Abb. 2", vlm_description="B", data_extracted_json=None)
    db.add_figure(paper_id=paper_id, page=3, caption="Abb. 1", vlm_description="A", data_extracted_json=None)
    figures = db.list_figures(paper_id)
    assert len(figures) == 2
    assert figures[0]["page"] == 3
    assert figures[1]["page"] == 10


def test_find_figures_by_caption(db_path, paper_id):
    """find_figures_by_caption findet passende Caption-Fragmente."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.add_figure(paper_id=paper_id, page=1, caption="Abb. 3.4: Ergebnisse", vlm_description="Desc", data_extracted_json=None)
    db.add_figure(paper_id=paper_id, page=2, caption="Tab. 5.1: Vergleich", vlm_description="Desc2", data_extracted_json=None)

    hits = db.find_figures_by_caption("Abb. 3.4")
    assert len(hits) == 1
    assert hits[0]["caption"] == "Abb. 3.4: Ergebnisse"

    # Kein Treffer bei unbekanntem Fragment
    no_hits = db.find_figures_by_caption("Abb. 99.99")
    assert no_hits == []


def test_find_figures_by_caption_with_paper_id_filter(db_path, paper_id):
    """find_figures_by_caption respektiert optionalen paper_id-Filter."""
    from mcp.academic_vault.db import VaultDB
    from mcp.academic_vault.server import add_paper
    db = VaultDB(db_path)

    # Zweites Paper anlegen
    add_paper(
        db_path=db_path,
        paper_id="other-paper",
        csl_json=json.dumps({"title": "Other", "type": "article-journal"}),
    )
    db.add_figure(paper_id=paper_id, page=1, caption="Abb. 3.4: Gemeinsam", vlm_description="D1", data_extracted_json=None)
    db.add_figure(paper_id="other-paper", page=1, caption="Abb. 3.4: Gemeinsam", vlm_description="D2", data_extracted_json=None)

    hits_all = db.find_figures_by_caption("Abb. 3.4")
    assert len(hits_all) == 2

    hits_filtered = db.find_figures_by_caption("Abb. 3.4", paper_id=paper_id)
    assert len(hits_filtered) == 1
    assert hits_filtered[0]["paper_id"] == paper_id
