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


def test_server_add_figure_returns_figure_id(db_path, paper_id):
    """server.add_figure() gibt figure_id-String zurueck."""
    from mcp.academic_vault import server
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=7,
        caption="Fig. 2.3: Systemarchitektur",
        vlm_description="Blockdiagramm zeigt drei Schichten: UI, Logik, Daten.",
        data_extracted=None,
    )
    assert isinstance(fig_id, str) and len(fig_id) > 0


def test_server_get_figure(db_path, paper_id):
    """server.get_figure() gibt Record oder None zurueck."""
    from mcp.academic_vault import server
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=1,
        caption="Abb. 1.1: Einleitung",
        vlm_description="Foto eines Labors mit Messgeraeten.",
        data_extracted=None,
    )
    record = server.get_figure(db_path=db_path, figure_id=fig_id)
    assert record is not None
    assert record["caption"] == "Abb. 1.1: Einleitung"

    missing = server.get_figure(db_path=db_path, figure_id="does-not-exist")
    assert missing is None


def test_server_list_figures(db_path, paper_id):
    """server.list_figures() gibt Liste aller Figures fuer ein Paper."""
    from mcp.academic_vault import server
    server.add_figure(db_path=db_path, paper_id=paper_id, page=2, caption="Abb. A", vlm_description="X", data_extracted=None)
    server.add_figure(db_path=db_path, paper_id=paper_id, page=1, caption="Abb. B", vlm_description="Y", data_extracted=None)
    figures = server.list_figures(db_path=db_path, paper_id=paper_id)
    assert len(figures) == 2
    assert figures[0]["page"] == 1  # sortiert nach page


def test_server_find_figure_by_caption(db_path, paper_id):
    """server.find_figure_by_caption() gibt Vault-Lookup-Ergebnis."""
    from mcp.academic_vault import server
    server.add_figure(db_path=db_path, paper_id=paper_id, page=3, caption="Abb. 3.4: Messwerte", vlm_description="Grafik", data_extracted=None)

    hits = server.find_figure_by_caption(db_path=db_path, caption_fragment="Abb. 3.4")
    assert len(hits) == 1

    no_hits = server.find_figure_by_caption(db_path=db_path, caption_fragment="Abb. 99")
    assert no_hits == []


def test_data_extracted_json_valid(db_path, paper_id):
    """data_extracted_json wird als valides JSON gespeichert und zurueckgelesen."""
    from mcp.academic_vault import server
    table_data = json.dumps([{"col1": "A", "val": 1}, {"col1": "B", "val": 2}])
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=9,
        caption="Tab. 2.1: Ergebnisse",
        vlm_description="Tabelle mit zwei Spalten und zwei Zeilen.",
        data_extracted=table_data,
    )
    record = server.get_figure(db_path=db_path, figure_id=fig_id)
    assert record is not None
    parsed = json.loads(record["data_extracted_json"])
    assert isinstance(parsed, list)
    assert parsed[0]["col1"] == "A"


def test_evals_json_valid():
    """evals/figure-verifier/evals.json muss valides JSON mit 5 Cases sein."""
    evals_path = Path(__file__).parent.parent / "evals" / "figure-verifier" / "evals.json"
    assert evals_path.exists(), f"evals.json fehlt: {evals_path}"
    with open(evals_path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "evals.json muss ein JSON-Array sein"
    assert len(data) == 5, f"Erwartet 5 Cases, gefunden: {len(data)}"
    ids = [c["id"] for c in data]
    assert ids == ["fv-01", "fv-02", "fv-03", "fv-04", "fv-05"]


def test_figure_verifier_agent_frontmatter():
    """figure-verifier.md muss valides Frontmatter mit Pflichtfeldern haben."""
    import re
    agent_path = Path(__file__).parent.parent / "agents" / "figure-verifier.md"
    assert agent_path.exists(), f"Agent-Datei fehlt: {agent_path}"

    content = agent_path.read_text(encoding="utf-8")
    # Frontmatter zwischen --- ... ---
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match is not None, "Kein YAML-Frontmatter gefunden"

    fm = fm_match.group(1)
    assert "name: figure-verifier" in fm
    assert "model: sonnet" in fm
    assert "vault.add_figure" in content
    assert "vault.list_figures" in content
