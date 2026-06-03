"""VaultDB — SQLite-Datenbankschicht fuer academic_vault.

Context-Manager-Klasse mit sqlite-vec-Fallback und FTS5-Volltext-Suche.
"""
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

VALID_PAPER_TYPES = frozenset({"article-journal", "book", "chapter"})


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
        """Versucht sqlite_vec Extension zu laden. Gibt True bei Erfolg zurueck.

        Python-Builds ohne ``--enable-loadable-sqlite-extensions`` (z.B. das
        macOS-System-Python und die macOS-Builds von actions/setup-python)
        haben ``enable_load_extension`` nicht bzw. werfen beim Aufruf. Dann ist
        die Vektor-Suche schlicht nicht verfuegbar (optionales Feature) und
        ``vec_available`` bleibt False — der Rest des Vault funktioniert weiter.
        """
        vec_path = os.environ.get("SQLITE_VEC_PATH", "")
        target = conn if conn is not None else self._get_conn()

        if not hasattr(target, "enable_load_extension"):
            self.vec_available = False
            return False

        try:
            target.enable_load_extension(True)
        except (AttributeError, sqlite3.OperationalError, sqlite3.NotSupportedError):
            self.vec_available = False
            return False

        try:
            if vec_path:
                target.load_extension(vec_path)
            else:
                target.load_extension("sqlite_vec")
            self.vec_available = True
        except Exception:
            self.vec_available = False
        finally:
            try:
                target.enable_load_extension(False)
            except Exception:
                pass
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
        editor: Optional[str] = None,
        chapter: Optional[str] = None,
        page_first: Optional[int] = None,
        page_last: Optional[int] = None,
        container_title: Optional[str] = None,
        parent_paper_id: Optional[str] = None,
    ) -> None:
        """Upsert eines Papers in die papers-Tabelle.

        type wird aus csl_json extrahiert. Erlaubte Werte: article-journal, book, chapter.
        """
        try:
            csl = json.loads(csl_json)
            paper_type = csl.get("type", "article-journal")
        except Exception:
            paper_type = "article-journal"

        if paper_type not in VALID_PAPER_TYPES:
            raise ValueError(
                f"Ungueltiger type '{paper_type}' -- erlaubt: {sorted(VALID_PAPER_TYPES)}"
            )

        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO papers
              (paper_id, type, csl_json, doi, isbn, pdf_path, page_offset,
               editor, chapter, page_first, page_last, container_title,
               parent_paper_id,
               added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET
              type            = excluded.type,
              csl_json        = excluded.csl_json,
              doi             = excluded.doi,
              isbn            = excluded.isbn,
              pdf_path        = excluded.pdf_path,
              page_offset     = excluded.page_offset,
              editor          = excluded.editor,
              chapter         = excluded.chapter,
              page_first      = excluded.page_first,
              page_last       = excluded.page_last,
              container_title = excluded.container_title,
              parent_paper_id = excluded.parent_paper_id,
              updated_at      = excluded.updated_at
            """,
            (
                paper_id, paper_type, csl_json, doi, isbn, pdf_path, page_offset,
                editor, chapter, page_first, page_last, container_title,
                parent_paper_id,
                now, now,
            ),
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

    def set_page_offset(self, paper_id: str, offset: int) -> None:
        """Setzt page_offset fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET page_offset = ?, updated_at = ? WHERE paper_id = ?",
            (offset, int(time.time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def get_page_offset(self, paper_id: str) -> int:
        """Gibt page_offset fuer ein Paper zurueck. Fallback: 0."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT page_offset FROM papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        if row is None:
            return 0
        return int(row["page_offset"] or 0)

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

    def search_quote_text(self, verbatim: str, k: int = 5) -> list[dict]:
        """LIKE-Suche in quotes.verbatim. Gibt [{quote_id, verbatim, paper_id}] zurueck."""
        conn = self._get_conn()
        own_conn = self._conn is None
        rows = conn.execute(
            "SELECT quote_id, verbatim, paper_id FROM quotes WHERE verbatim LIKE ? LIMIT ?",
            (f"%{verbatim}%", k),
        ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

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

    def set_ocr_done(self, paper_id: str, value: int = 1) -> None:
        """Setzt ocr_done-Flag fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET ocr_done = ?, updated_at = ? WHERE paper_id = ?",
            (value, int(time.time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def update_pdf_path(self, paper_id: str, new_path: str) -> None:
        """Aktualisiert pdf_path fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET pdf_path = ?, updated_at = ? WHERE paper_id = ?",
            (new_path, int(time.time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    # ------------------------------------------------------------------
    # Figures CRUD
    # ------------------------------------------------------------------

    def add_figure(
        self,
        paper_id: str,
        page: Optional[int],
        caption: Optional[str],
        vlm_description: Optional[str],
        data_extracted_json: Optional[str],
    ) -> str:
        """INSERT einer Figure. Gibt figure_id (UUID) zurueck."""
        figure_id = str(uuid4())
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO figures
              (figure_id, paper_id, page, caption, vlm_description, data_extracted_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (figure_id, paper_id, page, caption, vlm_description, data_extracted_json, now),
        )
        if own_conn:
            conn.commit()
            conn.close()
        return figure_id

    def get_figure(self, figure_id: str) -> Optional[dict]:
        """Gibt Figure-Record als dict zurueck oder None."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT * FROM figures WHERE figure_id = ?", (figure_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        return dict(row) if row is not None else None

    def list_figures(self, paper_id: str) -> list[dict]:
        """Alle Figures fuer ein Paper, nach page sortiert."""
        conn = self._get_conn()
        own_conn = self._conn is None
        rows = conn.execute(
            "SELECT * FROM figures WHERE paper_id = ? ORDER BY page",
            (paper_id,),
        ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    def find_figures_by_caption(
        self,
        caption_fragment: str,
        paper_id: Optional[str] = None,
    ) -> list[dict]:
        """LIKE-Suche in figures.caption. Optionaler paper_id-Filter."""
        conn = self._get_conn()
        own_conn = self._conn is None
        if paper_id is not None:
            rows = conn.execute(
                "SELECT * FROM figures WHERE caption LIKE ? AND paper_id = ?",
                (f"%{caption_fragment}%", paper_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM figures WHERE caption LIKE ?",
                (f"%{caption_fragment}%",),
            ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Decisions CRUD (v6.4)
    # ------------------------------------------------------------------

    def add_decision(
        self,
        category: Optional[str],
        text: str,
        rationale: Optional[str] = None,
    ) -> str:
        """INSERT einer Decision. Gibt decision_id (UUID) zurueck."""
        decision_id = str(uuid4())
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO decisions (decision_id, category, text, rationale, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (decision_id, category, text, rationale, now),
        )
        if own_conn:
            conn.commit()
            conn.close()
        return decision_id

    def supersede_decision(self, decision_id: str, superseded_by: str) -> None:
        """Setzt superseded_by fuer eine Decision."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE decisions SET superseded_by = ? WHERE decision_id = ?",
            (superseded_by, decision_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def list_decisions(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        """Gibt Decisions zurueck, optional nach Kategorie und/oder active gefiltert."""
        conn = self._get_conn()
        own_conn = self._conn is None
        clauses = []
        params: list = []
        if category is not None:
            clauses.append("category = ?")
            params.append(category)
        if active_only:
            clauses.append("superseded_by IS NULL")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM decisions {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Excluded Sources (v6.4)
    # ------------------------------------------------------------------

    def add_excluded_source(self, paper_id: str, reason: Optional[str] = None) -> None:
        """INSERT or REPLACE eines excluded_source-Eintrags."""
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT OR REPLACE INTO excluded_sources (paper_id, reason, excluded_at)
            VALUES (?, ?, ?)
            """,
            (paper_id, reason, now),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def list_excluded_sources(self) -> list[dict]:
        """Gibt alle excluded_sources zurueck."""
        conn = self._get_conn()
        own_conn = self._conn is None
        rows = conn.execute("SELECT * FROM excluded_sources ORDER BY excluded_at DESC").fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    def is_excluded(self, paper_id: str) -> bool:
        """Prueft ob paper_id in excluded_sources ist."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT 1 FROM excluded_sources WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        return row is not None

    # ------------------------------------------------------------------
    # Risk-of-Bias Assessments (v6.4)
    # ------------------------------------------------------------------

    def add_risk_of_bias(
        self,
        paper_id: str,
        study_type: str,
        domain_scores_json: str,
    ) -> str:
        """INSERT eines RoB-Assessments. Gibt assessment_id (UUID) zurueck."""
        assessment_id = str(uuid4())
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO risk_of_bias_assessments
              (assessment_id, paper_id, study_type, domain_scores_json, ts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (assessment_id, paper_id, study_type, domain_scores_json, now),
        )
        if own_conn:
            conn.commit()
            conn.close()
        return assessment_id

    def list_risk_of_bias(
        self,
        paper_id: Optional[str] = None,
    ) -> list[dict]:
        """Gibt RoB-Assessments zurueck, optional nach paper_id gefiltert."""
        conn = self._get_conn()
        own_conn = self._conn is None
        if paper_id is not None:
            rows = conn.execute(
                "SELECT * FROM risk_of_bias_assessments WHERE paper_id = ? ORDER BY ts DESC",
                (paper_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM risk_of_bias_assessments ORDER BY ts DESC"
            ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Score History (v6.4)
    # ------------------------------------------------------------------

    def add_score_snapshot(
        self,
        paper_id: str,
        session_id: str,
        scores_json: str,
    ) -> str:
        """INSERT eines Score-Snapshots. Gibt snapshot_id (UUID) zurueck."""
        snapshot_id = str(uuid4())
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO score_history (snapshot_id, paper_id, session_id, ts, scores_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (snapshot_id, paper_id, session_id, now, scores_json),
        )
        if own_conn:
            conn.commit()
            conn.close()
        return snapshot_id

    def get_score_history(
        self,
        paper_id: str,
        k: Optional[int] = None,
    ) -> list[dict]:
        """Gibt Score-History fuer ein Paper zurueck, nach ts DESC sortiert."""
        conn = self._get_conn()
        own_conn = self._conn is None
        if k is not None:
            rows = conn.execute(
                "SELECT * FROM score_history WHERE paper_id = ? ORDER BY ts DESC LIMIT ?",
                (paper_id, k),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM score_history WHERE paper_id = ? ORDER BY ts DESC",
                (paper_id,),
            ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Vault Lock (v6.4)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Chunk Embeddings (v6.5 — Contextual Retrieval #109)
    # ------------------------------------------------------------------

    def add_chunk_embedding(
        self,
        paper_id: str,
        chunk_text: str,
        context_sentence: str,
        embedding_text: str,
        embedding_vector: Optional[bytes],
    ) -> str:
        """INSERT eines Chunk-Embeddings. Gibt chunk_id (UUID) zurueck.

        Args:
            paper_id: Referenz auf papers.paper_id.
            chunk_text: Originaler Chunk-Text.
            context_sentence: 1-Satz-Kontext generiert via Anthropic API.
            embedding_text: Kombinierter Text (context_sentence + chunk_text).
            embedding_vector: Serialisierter Embedding-Vektor (bytes) oder None.
        """
        chunk_id = str(uuid4())
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT INTO chunk_embeddings
              (chunk_id, paper_id, chunk_text, context_sentence, embedding_text,
               embedding_vector, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (chunk_id, paper_id, chunk_text, context_sentence, embedding_text,
             embedding_vector, now),
        )
        if own_conn:
            conn.commit()
            conn.close()
        return chunk_id

    def get_chunk_embeddings(self, paper_id: str) -> list[dict]:
        """Gibt alle Chunk-Embeddings fuer ein Paper zurueck."""
        conn = self._get_conn()
        own_conn = self._conn is None
        rows = conn.execute(
            "SELECT * FROM chunk_embeddings WHERE paper_id = ? ORDER BY created_at",
            (paper_id,),
        ).fetchall()
        if own_conn:
            conn.close()
        return [dict(r) for r in rows]

    def lock_vault(self, slug: str) -> None:
        """Setzt Vault-Lock fuer einen Slug. Idempotent."""
        now = int(time.time())
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            """
            INSERT OR REPLACE INTO vault_locked_status (slug, locked_at)
            VALUES (?, ?)
            """,
            (slug, now),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def is_locked(self, slug: str) -> bool:
        """Prueft ob Vault-Lock fuer Slug gesetzt ist."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT 1 FROM vault_locked_status WHERE slug = ?", (slug,)
        ).fetchone()
        if own_conn:
            conn.close()
        return row is not None
