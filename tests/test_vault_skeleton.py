"""Smoke-Tests fuer den academic_vault MCP-Server (TDD-First Skelett)."""
import os
import sys
import sqlite3
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Worktree-Root zum PYTHONPATH hinzufuegen damit mcp.academic_vault importierbar ist
_WORKTREE_ROOT = Path(__file__).parent.parent
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

# Modul-Imports mit Guard: fehlen noch bis zur Implementierung
try:
    from mcp.academic_vault.db import VaultDB
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False

try:
    from mcp.academic_vault.files_api import FilesAPIClient
    _FILES_API_AVAILABLE = True
except ImportError:
    _FILES_API_AVAILABLE = False

try:
    from mcp.academic_vault import server as vault_server
    _SERVER_AVAILABLE = True
except ImportError:
    _SERVER_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def make_temp_db() -> tuple[str, "VaultDB"]:
    """Erstellt eine temporaere In-Memory-DB oder Datei-DB."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = VaultDB(tmp.name)
    db.init_schema()
    return tmp.name, db


# ---------------------------------------------------------------------------
# Task 2 aktiviert: test_schema_creates_tables
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_schema_creates_tables():
    """Alle 5 Tabellen + papers_fts existieren nach init_schema()."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','trigger') ORDER BY name"
        )
        names = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "papers" in names
        assert "quotes" in names
        assert "decisions" in names
        assert "notes" in names
        assert "papers_fts" in names
        assert "papers_ai" in names
        assert "papers_ad" in names
        assert "papers_au" in names
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 4 aktiviert: test_add_paper_and_get
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_add_paper_and_get():
    """add_paper + get_paper Round-Trip."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        csl = '{"title": "Test Paper", "abstract": "An abstract."}'
        db.add_paper("p1", csl, doi="10.1234/test")
        paper = db.get_paper("p1")
        assert paper is not None
        assert paper["paper_id"] == "p1"
        assert paper["doi"] == "10.1234/test"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 7 aktiviert: test_search_returns_results
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_search_returns_results():
    """vault.search(query) gibt >= 1 Ergebnis zurueck."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        csl = '{"title": "DevOps Governance Study", "abstract": "About DevOps in enterprise."}'
        db.add_paper("p-search", csl)

        from mcp.academic_vault.server import search_papers
        results = search_papers(db_path, "DevOps Governance", k=5)
        assert len(results) >= 1
        assert "paper_id" in results[0]
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 6 aktiviert: test_add_quote_requires_api_response_id
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_add_quote_requires_api_response_id():
    """vault.add_quote mit citations-api + kein api_response_id wirft ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        csl = '{"title": "Test Paper"}'
        db.add_paper("p-quote", csl)

        from mcp.academic_vault.server import add_quote
        with pytest.raises(ValueError, match="api_response_id"):
            add_quote(
                db_path=db_path,
                paper_id="p-quote",
                verbatim="Exact text from the paper.",
                extraction_method="citations-api",
                api_response_id=None,
            )
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 6 aktiviert: test_add_quote_manual_no_api_id
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_add_quote_manual_no_api_id():
    """vault.add_quote mit manual + kein api_response_id ist OK."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        csl = '{"title": "Test Paper"}'
        db.add_paper("p-manual", csl)

        from mcp.academic_vault.server import add_quote
        quote_id = add_quote(
            db_path=db_path,
            paper_id="p-manual",
            verbatim="Manually noted text.",
            extraction_method="manual",
            api_response_id=None,
        )
        assert quote_id is not None
        assert len(quote_id) > 0
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 5 aktiviert: test_ensure_file_caches
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _FILES_API_AVAILABLE, reason="files_api.py noch nicht implementiert")
@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_ensure_file_caches():
    """Zweiter Aufruf von ensure_file triggert kein Re-Upload."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    # Minimales temporaeres PDF-Dummy
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_f:
        pdf_path = pdf_f.name
        pdf_f.write(b"%PDF-1.4 fake content")
    try:
        db = VaultDB(db_path)
        db.init_schema()
        db.add_paper("p-file", '{"title": "File Paper"}', pdf_path=pdf_path)

        mock_upload = MagicMock()
        mock_upload.return_value = MagicMock(id="file-abc123")

        client = FilesAPIClient(anthropic_api_key="test-key", cache_db_path=db_path)

        with patch.object(client, "_upload_file", mock_upload):
            fid1 = client.ensure_file(pdf_path)
            fid2 = client.ensure_file(pdf_path)

        assert fid1 == fid2 == "file-abc123"
        mock_upload.assert_called_once()
    finally:
        os.unlink(db_path)
        os.unlink(pdf_path)


# ---------------------------------------------------------------------------
# Task 8 aktiviert: test_find_quotes
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_find_quotes():
    """find_quotes(paper_id) gibt vorher eingefuegte Quotes zurueck."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        db.add_paper("p-fq", '{"title": "Find Quotes Paper"}')

        from mcp.academic_vault.server import add_quote, find_quotes
        add_quote(
            db_path=db_path,
            paper_id="p-fq",
            verbatim="An important verbatim quote.",
            extraction_method="manual",
        )
        results = find_quotes(db_path, paper_id="p-fq")
        assert len(results) >= 1
        assert results[0]["paper_id"] == "p-fq"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 8 aktiviert: test_get_quote
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_get_quote():
    """get_quote(quote_id) gibt vollstaendigen Record zurueck."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        db.add_paper("p-gq", '{"title": "Get Quote Paper"}')

        from mcp.academic_vault.server import add_quote, get_quote
        quote_id = add_quote(
            db_path=db_path,
            paper_id="p-gq",
            verbatim="The verbatim text to retrieve.",
            extraction_method="manual",
        )
        record = get_quote(db_path, quote_id)
        assert record is not None
        assert record["quote_id"] == quote_id
        assert record["verbatim"] == "The verbatim text to retrieve."
        assert record["paper_id"] == "p-gq"
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 9 aktiviert: test_stats
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _FILES_API_AVAILABLE, reason="files_api.py noch nicht implementiert")
@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_stats():
    """vault.stats() gibt korrekte Counts + token_savings_estimate > 0 bei >=1 file_id."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = VaultDB(db_path)
        db.init_schema()
        db.add_paper("p-stats", '{"title": "Stats Paper"}')
        # file_id manuell setzen (wie nach ensure_file)
        db.set_file_id("p-stats", "file-xyz", expires_at=int(time.time()) + 3600)

        from mcp.academic_vault.server import add_quote
        add_quote(
            db_path=db_path,
            paper_id="p-stats",
            verbatim="A test quote for stats.",
            extraction_method="manual",
        )

        from mcp.academic_vault.files_api import FilesAPIClient
        stats = FilesAPIClient.get_stats(db_path)

        assert "paper_count" in stats
        assert "quote_count" in stats
        assert "cached_files" in stats
        assert "token_savings_estimate" in stats
        assert stats["paper_count"] >= 1
        assert stats["quote_count"] >= 1
        assert stats["cached_files"] >= 1
        assert stats["token_savings_estimate"] > 0
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 3 aktiviert: test_vec_fallback
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _DB_AVAILABLE, reason="db.py noch nicht implementiert")
def test_vec_fallback():
    """Wenn sqlite-vec nicht geladen -> vec_available=False, FTS5 funktioniert."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        # VaultDB ohne vec-Extension initialisieren (kein SQLITE_VEC_PATH gesetzt)
        env_backup = os.environ.pop("SQLITE_VEC_PATH", None)
        try:
            db = VaultDB(db_path)
            db.init_schema()
            # vec_available muss False sein (keine Extension im Test-Env)
            assert db.vec_available is False
            # FTS5 muss trotzdem funktionieren
            csl = '{"title": "Fallback Test Paper", "abstract": "Testing FTS5 fallback."}'
            db.add_paper("p-fallback", csl)
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT paper_id FROM papers_fts WHERE papers_fts MATCH 'Fallback'"
            ).fetchall()
            conn.close()
            assert len(rows) >= 1
        finally:
            if env_backup is not None:
                os.environ["SQLITE_VEC_PATH"] = env_backup
    finally:
        os.unlink(db_path)


# ---------------------------------------------------------------------------
# Task 10 aktiviert: test_migrate_help
# ---------------------------------------------------------------------------

def test_migrate_help():
    """migrate.py --help muss mit exit 0 laufen."""
    import subprocess
    migrate_path = str(_WORKTREE_ROOT / "mcp" / "academic_vault" / "migrate.py")
    result = subprocess.run(
        [sys.executable, migrate_path, "--help"],
        capture_output=True,
        timeout=10,
        cwd=str(_WORKTREE_ROOT),
    )
    assert result.returncode == 0
    assert b"--db" in result.stdout or b"--state" in result.stdout
