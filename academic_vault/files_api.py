"""FilesAPIClient — Anthropic Files-API-Cache fuer PDFs.

Gibt file_id zurueck (gecacht mit 1h-TTL in papers-Tabelle).
Fallback: bei fehlendem Upload wird Exception nach oben durchgereicht.
"""
import sqlite3
import time
from pathlib import Path
from typing import Optional

from .db import VaultDB

_TTL = 3600  # 1 Stunde in Sekunden
_AVG_BASE64_TOKENS_PER_PDF = 80_000   # Heuristik (Audit §4.1: 60–100k)
_FILE_ID_OVERHEAD = 20                # Token fuer file_id-Referenz


class FilesAPIClient:
    """Anthropic Files-API-Client mit TTL-Cache in der Vault-Datenbank."""

    def __init__(self, anthropic_api_key: str, cache_db_path: str) -> None:
        self.api_key = anthropic_api_key
        self.cache_db_path = cache_db_path
        self._client = None  # lazy init

    def _get_client(self):
        """Lazy-Init des Anthropic-Clients."""
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def _upload_file(self, pdf_path: str) -> str:
        """Laedt PDF hoch und gibt file_id zurueck.

        Nutzt anthropic.beta.files.upload mit Files-API-Beta-Header.
        Kann in Tests per patch.object gemockt werden.
        """
        client = self._get_client()
        with open(pdf_path, "rb") as fh:
            response = client.beta.files.upload(
                file=(Path(pdf_path).name, fh, "application/pdf"),
                extra_headers={"anthropic-beta": "files-api-2025-04-14"},
            )
        return response.id

    def ensure_file(self, pdf_path: str) -> str:
        """Gibt gecachte file_id zurueck, laedt hoch bei Cache-Miss.

        Prüft papers-Tabelle nach pdf_path. TTL = 3600s.
        Bei Ablauf oder fehlendem file_id wird re-uploaded.
        """
        now = int(time.time())

        conn = VaultDB._open(self.cache_db_path)
        try:
            row = conn.execute(
                "SELECT paper_id, file_id FROM papers "
                "WHERE pdf_path = ? AND file_id IS NOT NULL AND file_id_expires_at > ?",
                (pdf_path, now),
            ).fetchone()
            if row is not None:
                return row["file_id"]

            paper_row = conn.execute(
                "SELECT paper_id FROM papers WHERE pdf_path = ?", (pdf_path,)
            ).fetchone()
        finally:
            conn.close()

        # Cache-Miss: hochladen
        file_id = self._upload_file(pdf_path)
        if paper_row is not None:
            VaultDB(self.cache_db_path).set_file_id(
                paper_row["paper_id"], file_id, now + _TTL
            )
        return file_id

    @staticmethod
    def get_stats(db_path: str) -> dict:
        """Gibt Statistik-Dict zurueck: paper_count, quote_count, cached_files,
        token_savings_estimate.

        token_savings_estimate = cached_files * (AVG_BASE64_TOKENS_PER_PDF - FILE_ID_OVERHEAD)
        """
        now = int(time.time())
        conn = VaultDB._open(db_path)
        paper_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        quote_count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
        cached_files = conn.execute(
            "SELECT COUNT(*) FROM papers "
            "WHERE file_id IS NOT NULL AND file_id_expires_at > ?",
            (now,),
        ).fetchone()[0]
        conn.close()

        token_savings_estimate = cached_files * (_AVG_BASE64_TOKENS_PER_PDF - _FILE_ID_OVERHEAD)
        return {
            "paper_count": paper_count,
            "quote_count": quote_count,
            "cached_files": cached_files,
            "token_savings_estimate": token_savings_estimate,
        }
