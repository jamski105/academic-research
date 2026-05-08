"""VaultDB — SQLite-Datenbankschicht fuer academic_vault.

Context-Manager-Klasse mit sqlite-vec-Fallback und FTS5-Volltext-Suche.
"""
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class VaultDB:
    """SQLite-Datenbankzugriff fuer den academic_vault MCP-Server."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.vec_available: bool = False
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Context-Manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "VaultDB":
        self._conn = self._open(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn is None:
            return
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn.close()
        self._conn = None

    # ------------------------------------------------------------------
    # Schema-Initialisierung
    # ------------------------------------------------------------------

    @staticmethod
    def _open(db_path: str) -> sqlite3.Connection:
        """Oeffnet eine neue Verbindung mit Standard-Pragmas."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _get_conn(self) -> sqlite3.Connection:
        """Gibt bestehende oder neue Verbindung zurueck."""
        if self._conn is not None:
            return self._conn
        return self._open(self.db_path)

    def load_vec_extension(self, conn: Optional[sqlite3.Connection] = None) -> bool:
        """Versucht sqlite_vec Extension zu laden. Gibt True bei Erfolg zurueck."""
        vec_path = os.environ.get("SQLITE_VEC_PATH", "")
        target = conn if conn is not None else self._get_conn()
        target.enable_load_extension(True)
        try:
            if vec_path:
                target.load_extension(vec_path)
            else:
                target.load_extension("sqlite_vec")
            self.vec_available = True
        except Exception:
            self.vec_available = False
        finally:
            target.enable_load_extension(False)
        return self.vec_available

    def init_schema(self) -> None:
        """Erstellt alle Tabellen gemaess schema.sql. Versucht vec0 zu erstellen."""
        ddl = _SCHEMA_PATH.read_text(encoding="utf-8")
        conn = self._get_conn()
        own_conn = self._conn is None

        # vec-Extension auf derselben Connection laden (optional)
        self.load_vec_extension(conn)

        # Basis-Schema ausfuehren (ohne vec0-Block — der ist auskommentiert)
        conn.executescript(ddl)

        # quote_embeddings via vec0 versuchen (nur wenn Extension geladen)
        if self.vec_available:
            try:
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS quote_embeddings "
                    "USING vec0(quote_id TEXT PRIMARY KEY, embedding FLOAT[384])"
                )
            except sqlite3.OperationalError:
                self.vec_available = False

        if own_conn:
            conn.commit()
            conn.close()

    # ------------------------------------------------------------------
    # Papers CRUD
    # ------------------------------------------------------------------

    def add_paper(
        self,
        paper_id: str,
        csl_json: str,
        doi: Optional[str] = None,
        isbn: Optional[str] = None,
        pdf_path: Optional[str] = None,
        page_offset: int = 0,
    ) -> None:
        """Upsert eines Papers in die papers-Tabelle."""
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO papers
              (paper_id, csl_json, doi, isbn, pdf_path, page_offset, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET
              csl_json   = excluded.csl_json,
              doi        = excluded.doi,
              isbn       = excluded.isbn,
              pdf_path   = excluded.pdf_path,
              page_offset= excluded.page_offset,
              updated_at = excluded.updated_at
            """,
            (paper_id, csl_json, doi, isbn, pdf_path, page_offset, now, now),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def get_paper(self, paper_id: str) -> Optional[dict]:
        """Gibt Paper-Record als dict zurueck oder None."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT * FROM papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        if row is None:
            return None
        return dict(row)

    def set_file_id(
        self, paper_id: str, file_id: str, expires_at: int
    ) -> None:
        """Setzt file_id und file_id_expires_at fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET file_id = ?, file_id_expires_at = ?, updated_at = ? "
            "WHERE paper_id = ?",
            (file_id, expires_at, int(time.time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    # ------------------------------------------------------------------
    # Quotes CRUD
    # ------------------------------------------------------------------

    def add_quote(
        self,
        quote_id: str,
        paper_id: str,
        verbatim: str,
        extraction_method: str,
        api_response_id: Optional[str] = None,
        pdf_page: Optional[int] = None,
        printed_page: Optional[int] = None,
        section: Optional[str] = None,
        context_before: Optional[str] = None,
        context_after: Optional[str] = None,
    ) -> None:
        """INSERT eines Quotes in die quotes-Tabelle."""
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO quotes
              (quote_id, paper_id, verbatim, pdf_page, printed_page,
               section, context_before, context_after,
               extraction_method, api_response_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quote_id, paper_id, verbatim, pdf_page, printed_page,
                section, context_before, context_after,
                extraction_method, api_response_id, now,
            ),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def get_quote(self, quote_id: str) -> Optional[dict]:
        """Gibt Quote-Record als dict zurueck oder None."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT * FROM quotes WHERE quote_id = ?", (quote_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        return dict(row) if row is not None else None

    def find_quotes(
        self,
        paper_id: str,
        query: Optional[str] = None,
        k: int = 10,
    ) -> list[dict]:
        """Suche Quotes fuer ein Paper, optional per verbatim-LIKE-Filter."""
        conn = self._get_conn()
        own_conn = self._conn is None
        if query:
            rows = conn.execute(
                "SELECT * FROM quotes WHERE paper_id = ? AND verbatim LIKE ? LIMIT ?",
                (paper_id, f"%{query}%", k),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM quotes WHERE paper_id = ? LIMIT ?",
                (paper_id, k),
            ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]
