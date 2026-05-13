"""Tests fuer parent_paper_id in Vault (schema, migration, db, server)."""
import json
import os
import sqlite3
import tempfile

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.academic_vault.db import VaultDB


class TestParentPaperIdSchema:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        self.db = VaultDB(self.db_path)
        self.db.init_schema()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_parent_paper_id_column_exists(self):
        """papers-Tabelle hat parent_paper_id-Spalte."""
        conn = sqlite3.connect(self.db_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        conn.close()
        assert "parent_paper_id" in cols

    def test_add_paper_with_parent_paper_id(self):
        """add_paper akzeptiert parent_paper_id."""
        # Eltern-Buch anlegen
        self.db.add_paper(
            paper_id="book-parent",
            csl_json=json.dumps({"type": "book", "title": "Elternbuch"}),
        )
        # Kapitel mit parent_paper_id
        self.db.add_paper(
            paper_id="chapter-child",
            csl_json=json.dumps({"type": "chapter", "title": "Kapitel 1"}),
            parent_paper_id="book-parent",
        )
        paper = self.db.get_paper("chapter-child")
        assert paper is not None
        assert paper["parent_paper_id"] == "book-parent"

    def test_parent_paper_id_nullable(self):
        """parent_paper_id ist NULL wenn nicht gesetzt."""
        self.db.add_paper(
            paper_id="standalone",
            csl_json=json.dumps({"type": "article-journal", "title": "Artikel"}),
        )
        paper = self.db.get_paper("standalone")
        assert paper["parent_paper_id"] is None


class TestMigrateParentPaperId:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        # Altes Schema ohne parent_paper_id simulieren
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE papers (
                paper_id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'article-journal',
                csl_json TEXT NOT NULL,
                added_at INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_parent_paper_id_column_idempotent(self):
        """Migration fuegt Spalte hinzu; zweiter Lauf wirft keinen Fehler."""
        from mcp.academic_vault.migrate import add_parent_paper_id_column
        # Erster Lauf
        add_parent_paper_id_column(self.db_path)
        cols = [
            row[1] for row in
            sqlite3.connect(self.db_path).execute("PRAGMA table_info(papers)").fetchall()
        ]
        assert "parent_paper_id" in cols
        # Zweiter Lauf: kein Fehler
        add_parent_paper_id_column(self.db_path)


class TestServerAddChapter:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_chapter_via_server(self):
        """server.add_chapter() legt Kapitel mit parent_paper_id an."""
        from mcp.academic_vault import server as vault_server
        # Elternbuch anlegen
        vault_server.add_paper(
            self.db_path, "buch-001",
            csl_json=json.dumps({"type": "book", "title": "Grundlagen"}),
        )
        # Kapitel via add_chapter
        vault_server.add_chapter(
            db_path=self.db_path,
            parent_paper_id="buch-001",
            chapter_number=1,
            csl_json=json.dumps({"type": "chapter", "title": "Einleitung"}),
            paper_id="buch-001-ch1",
        )
        paper = vault_server.get_paper(self.db_path, "buch-001-ch1")
        assert paper is not None
        assert paper["parent_paper_id"] == "buch-001"
        assert paper["type"] == "chapter"

    def test_server_add_paper_accepts_parent_paper_id(self):
        """server.add_paper() akzeptiert parent_paper_id."""
        from mcp.academic_vault import server as vault_server
        vault_server.add_paper(
            self.db_path, "root-book",
            csl_json=json.dumps({"type": "book", "title": "Root"}),
        )
        vault_server.add_paper(
            self.db_path, "ch-2",
            csl_json=json.dumps({"type": "chapter", "title": "Kap 2"}),
            parent_paper_id="root-book",
        )
        paper = vault_server.get_paper(self.db_path, "ch-2")
        assert paper["parent_paper_id"] == "root-book"

    def test_add_chapter_auto_sets_chapter_type(self):
        """add_chapter setzt type=chapter automatisch wenn nicht in csl_json."""
        from mcp.academic_vault import server as vault_server
        vault_server.add_paper(
            self.db_path, "buch-002",
            csl_json=json.dumps({"type": "book", "title": "Buch Zwei"}),
        )
        paper_id = vault_server.add_chapter(
            db_path=self.db_path,
            parent_paper_id="buch-002",
            chapter_number=2,
            csl_json=json.dumps({"title": "Kap Zwei"}),  # kein type
        )
        paper = vault_server.get_paper(self.db_path, paper_id)
        assert paper is not None
        assert paper["type"] == "chapter"
        assert paper["parent_paper_id"] == "buch-002"
