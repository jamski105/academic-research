"""Regressionstest fuer Issue #195: SciHub-Provenance-Tag in DB-Schema persistiert.

Akzeptanzkriterien (siehe Issue #195):
- schema.sql: papers.provenance TEXT DEFAULT NULL (mit Migration fuer bestehende DBs)
- migrate.py: ALTER TABLE fuer Upgrade (idempotent)
- vault.add_paper(...provenance="scihub") setzt das Feld
- vault.list_papers_by_provenance("scihub") fuer Audit
- Persistenz-Check: Provenance-Tag wird gespeichert und wieder ausgelesen
"""
import json
import os
import sqlite3
import tempfile

import pytest

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from academic_vault.db import VaultDB

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(REPO_ROOT, "academic_vault", "schema.sql")


# ---------------------------------------------------------------------------
# Schema-Ebene: provenance-Spalte existiert
# ---------------------------------------------------------------------------

class TestProvenanceSchema:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        self.db = VaultDB(self.db_path)
        self.db.init_schema()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_schema_sql_declares_provenance_column(self):
        """schema.sql deklariert papers.provenance TEXT DEFAULT NULL."""
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            ddl = f.read()
        assert "provenance" in ddl, "schema.sql muss provenance-Spalte deklarieren"

    def test_provenance_column_exists_in_papers(self):
        """papers-Tabelle hat provenance-Spalte nach init_schema."""
        conn = sqlite3.connect(self.db_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        conn.close()
        assert "provenance" in cols, "papers-Tabelle muss provenance-Spalte haben"

    def test_provenance_default_null(self):
        """provenance ist NULL wenn nicht gesetzt (Default fuer bestehende Eintraege)."""
        self.db.add_paper(
            paper_id="no-prov",
            csl_json=json.dumps({"type": "article-journal", "title": "Artikel"}),
        )
        paper = self.db.get_paper("no-prov")
        assert paper is not None
        assert paper["provenance"] is None


# ---------------------------------------------------------------------------
# Persistenz: add_paper(provenance=...) speichert + liest aus
# ---------------------------------------------------------------------------

class TestProvenancePersistence:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        self.db = VaultDB(self.db_path)
        self.db.init_schema()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_paper_persists_scihub_provenance(self):
        """add_paper(provenance='scihub') wird gespeichert und ausgelesen."""
        self.db.add_paper(
            paper_id="scihub-paper",
            csl_json=json.dumps({"type": "article-journal", "title": "SciHub Paper"}),
            doi="10.1234/scihub",
            provenance="scihub",
        )
        paper = self.db.get_paper("scihub-paper")
        assert paper is not None
        assert paper["provenance"] == "scihub"

    def test_provenance_survives_upsert_without_value(self):
        """Upsert ohne provenance-Argument ueberschreibt bestehenden Tag nicht stillschweigend mit Muell."""
        self.db.add_paper(
            paper_id="p1",
            csl_json=json.dumps({"type": "article-journal", "title": "T"}),
            provenance="scihub",
        )
        # zweiter Aufruf setzt provenance explizit erneut
        self.db.add_paper(
            paper_id="p1",
            csl_json=json.dumps({"type": "article-journal", "title": "T2"}),
            provenance="scihub",
        )
        paper = self.db.get_paper("p1")
        assert paper["provenance"] == "scihub"


# ---------------------------------------------------------------------------
# Audit: list_papers_by_provenance
# ---------------------------------------------------------------------------

class TestListPapersByProvenance:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        self.db = VaultDB(self.db_path)
        self.db.init_schema()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_list_papers_by_provenance_returns_only_matching(self):
        """list_papers_by_provenance('scihub') gibt nur SciHub-Papers zurueck."""
        self.db.add_paper(
            paper_id="oa-1",
            csl_json=json.dumps({"type": "article-journal", "title": "OA"}),
            provenance="oa",
        )
        self.db.add_paper(
            paper_id="sci-1",
            csl_json=json.dumps({"type": "article-journal", "title": "Sci1"}),
            provenance="scihub",
        )
        self.db.add_paper(
            paper_id="sci-2",
            csl_json=json.dumps({"type": "article-journal", "title": "Sci2"}),
            provenance="scihub",
        )
        self.db.add_paper(
            paper_id="none-1",
            csl_json=json.dumps({"type": "article-journal", "title": "None"}),
        )
        rows = self.db.list_papers_by_provenance("scihub")
        ids = {r["paper_id"] for r in rows}
        assert ids == {"sci-1", "sci-2"}, f"Erwartet nur SciHub-Papers, bekam: {ids}"

    def test_list_papers_by_provenance_empty_when_none(self):
        """Keine SciHub-Papers -> leere Liste."""
        self.db.add_paper(
            paper_id="oa-only",
            csl_json=json.dumps({"type": "article-journal", "title": "OA"}),
            provenance="oa",
        )
        rows = self.db.list_papers_by_provenance("scihub")
        assert rows == []


# ---------------------------------------------------------------------------
# Migration: bestehende DB ohne provenance-Spalte
# ---------------------------------------------------------------------------

class TestProvenanceMigration:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        # Altes Schema ohne provenance simulieren
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE papers (
                paper_id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'article-journal',
                csl_json TEXT NOT NULL,
                added_at INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            "INSERT INTO papers (paper_id, csl_json, added_at, updated_at) "
            "VALUES ('legacy', '{}', 0, 0)"
        )
        conn.commit()
        conn.close()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_provenance_column_adds_column(self):
        """Migration fuegt provenance-Spalte zu bestehender DB hinzu."""
        from academic_vault.migrate import add_provenance_column

        add_provenance_column(self.db_path)
        conn = sqlite3.connect(self.db_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        # Default-Wert fuer Bestandseintrag bleibt NULL
        legacy_prov = conn.execute(
            "SELECT provenance FROM papers WHERE paper_id = 'legacy'"
        ).fetchone()[0]
        conn.close()
        assert "provenance" in cols
        assert legacy_prov is None

    def test_add_provenance_column_idempotent(self):
        """Migration ist idempotent (zweiter Lauf wirft keinen Fehler)."""
        from academic_vault.migrate import add_provenance_column

        add_provenance_column(self.db_path)
        add_provenance_column(self.db_path)  # darf nicht scheitern
        conn = sqlite3.connect(self.db_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        conn.close()
        assert "provenance" in cols
