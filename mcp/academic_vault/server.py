"""academic_vault MCP-Server.

Stellt MCP-Tools vault.search/get_paper/add_paper/ensure_file/
add_quote/find_quotes/get_quote/stats bereit.

Start via: python -m mcp.academic_vault.server
"""
import json
import os
from uuid import uuid4
from typing import Optional

from .db import VaultDB
from .files_api import FilesAPIClient

# VAULT_DB_PATH aus Env; Fallback auf vault.db im CWD
_DEFAULT_DB = os.environ.get("VAULT_DB_PATH", "vault.db")
_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ---------------------------------------------------------------------------
# Reine Funktionen (testbar ohne MCP-Framework)
# ---------------------------------------------------------------------------

def add_quote(
    db_path: str,
    paper_id: str,
    verbatim: str,
    extraction_method: str,
    api_response_id: Optional[str] = None,
    pdf_page: Optional[int] = None,
    printed_page: Optional[int] = None,
    section: Optional[str] = None,
    context_before: Optional[str] = None,
    context_after: Optional[str] = None,
) -> str:
    """Fuegt Quote in Vault ein. Gibt quote_id zurueck.

    Halluzinationsschutz: extraction_method='citations-api' erfordert
    api_response_id. Bei Fehlen wird ValueError geworfen.
    """
    if extraction_method == "citations-api" and not api_response_id:
        raise ValueError(
            "vault.add_quote: api_response_id required for extraction_method='citations-api'"
        )
    quote_id = str(uuid4())
    db = VaultDB(db_path)
    db.add_quote(
        quote_id=quote_id,
        paper_id=paper_id,
        verbatim=verbatim,
        extraction_method=extraction_method,
        api_response_id=api_response_id,
        pdf_page=pdf_page,
        printed_page=printed_page,
        section=section,
        context_before=context_before,
        context_after=context_after,
    )
    return quote_id


def get_quote(db_path: str, quote_id: str) -> Optional[dict]:
    """Gibt vollstaendigen Quote-Record als dict zurueck oder None."""
    db = VaultDB(db_path)
    return db.get_quote(quote_id)


def search_papers(
    db_path: str,
    query: str,
    type_filter: Optional[str] = None,
    k: int = 5,
) -> list[dict]:
    """FTS5-Suche in papers_fts. Gibt [{paper_id, snippet, score}] zurueck."""
    conn = VaultDB._open(db_path)
    try:
        if type_filter:
            rows = conn.execute(
                """
                SELECT f.paper_id,
                       snippet(papers_fts, 1, '<b>', '</b>', '...', 10) AS snippet,
                       rank AS score
                FROM papers_fts f
                JOIN papers p ON p.paper_id = f.paper_id
                WHERE papers_fts MATCH ?
                  AND p.type = ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, type_filter, k),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT paper_id,
                       snippet(papers_fts, 1, '<b>', '</b>', '...', 10) AS snippet,
                       rank AS score
                FROM papers_fts
                WHERE papers_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, k),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def search_quote_text(db_path: str, verbatim: str, k: int = 5) -> list[dict]:
    """LIKE-Suche in quotes.verbatim. Gibt [{quote_id, verbatim, paper_id}] zurueck."""
    db = VaultDB(db_path)
    return db.search_quote_text(verbatim, k)


def find_quotes(
    db_path: str,
    paper_id: str,
    query: Optional[str] = None,
    k: int = 10,
) -> list[dict]:
    """Gibt Quotes fuer ein Paper zurueck, optional per verbatim-Filter."""
    db = VaultDB(db_path)
    return db.find_quotes(paper_id, query, k)


def add_paper(
    db_path: str,
    paper_id: str,
    csl_json: str,
    pdf_path: Optional[str] = None,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
    page_offset: int = 0,
    editor: Optional[str] = None,
    chapter: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
    container_title: Optional[str] = None,
    parent_paper_id: Optional[str] = None,
) -> None:
    """Upsert eines Papers in den Vault. Unterstuetzt type=book|chapter."""
    db = VaultDB(db_path)
    db.init_schema()
    db.add_paper(
        paper_id, csl_json,
        doi=doi, isbn=isbn, pdf_path=pdf_path, page_offset=page_offset,
        editor=editor, chapter=chapter,
        page_first=page_first, page_last=page_last,
        container_title=container_title,
        parent_paper_id=parent_paper_id,
    )


def add_chapter(
    db_path: str,
    parent_paper_id: str,
    chapter_number: int,
    csl_json: str,
    paper_id: Optional[str] = None,
    pdf_path: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
) -> str:
    """Legt ein Kapitel als Kind-Paper in den Vault. Gibt paper_id zurueck.

    Setzt type=chapter automatisch falls nicht in csl_json angegeben.
    """
    if paper_id is None:
        paper_id = f"{parent_paper_id}-ch{chapter_number}"
    # Sicherstellen dass type=chapter in csl_json gesetzt ist
    try:
        csl = json.loads(csl_json)
        csl.setdefault("type", "chapter")
        csl_json = json.dumps(csl, ensure_ascii=False)
    except Exception:
        pass
    add_paper(
        db_path=db_path,
        paper_id=paper_id,
        csl_json=csl_json,
        pdf_path=pdf_path,
        chapter=str(chapter_number),
        page_first=page_first,
        page_last=page_last,
        parent_paper_id=parent_paper_id,
    )
    return paper_id


def get_paper(db_path: str, paper_id: str) -> Optional[dict]:
    """Gibt Paper-Metadata als dict zurueck oder None."""
    db = VaultDB(db_path)
    return db.get_paper(paper_id)


def ensure_file(db_path: str, paper_id: str, api_key: str = "") -> str:
    """Delegiert an FilesAPIClient.ensure_file(). Gibt file_id zurueck."""
    paper = get_paper(db_path, paper_id)
    if paper is None:
        raise ValueError(f"Paper '{paper_id}' nicht gefunden.")
    pdf_path = paper.get("pdf_path")
    if not pdf_path:
        raise ValueError(f"Paper '{paper_id}' hat keinen pdf_path.")
    client = FilesAPIClient(
        anthropic_api_key=api_key or _ANTHROPIC_KEY,
        cache_db_path=db_path,
    )
    return client.ensure_file(pdf_path)


def get_stats(db_path: str) -> dict:
    """Delegiert an FilesAPIClient.get_stats()."""
    return FilesAPIClient.get_stats(db_path)


def set_ocr_done(db_path: str, paper_id: str, value: int = 1) -> None:
    """Setzt ocr_done-Flag fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.set_ocr_done(paper_id, value)


def update_pdf_path(db_path: str, paper_id: str, new_path: str) -> None:
    """Aktualisiert pdf_path fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.update_pdf_path(paper_id, new_path)


def set_page_offset(db_path: str, paper_id: str, offset: int) -> None:
    """Setzt page_offset fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.set_page_offset(paper_id, offset)


def get_printed_page(db_path: str, paper_id: str, pdf_page: int) -> int:
    """Berechnet gedruckte Seitenzahl: printed_page = pdf_page - page_offset.

    Args:
        db_path: Pfad zur Vault-DB.
        paper_id: Paper-ID im Vault.
        pdf_page: Seitenzahl aus Citations-API (1-basiert ab erster PDF-Seite).

    Returns:
        Gedruckte Seitenzahl (>= 1).
    """
    db = VaultDB(db_path)
    offset = db.get_page_offset(paper_id)
    printed = pdf_page - offset
    return max(1, printed)  # Nie kleiner als 1


# ---------------------------------------------------------------------------
# MCP-Server (optional: nur wenn mcp-SDK verfuegbar)
# ---------------------------------------------------------------------------

def _build_mcp_server():
    """Erstellt FastMCP-Server-Instanz. Gibt None zurueck wenn mcp nicht installiert."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    mcp = FastMCP("academic-vault")
    db_path = _DEFAULT_DB

    @mcp.tool(name="vault.search")
    def _vault_search(query: str, type: str = None, k: int = 5) -> list[dict]:
        """FTS5-Suche in papers. Gibt [{paper_id, snippet, score}] zurueck."""
        return search_papers(db_path, query, type_filter=type, k=k)

    @mcp.tool(name="vault.get_paper")
    def _vault_get_paper(paper_id: str) -> Optional[dict]:
        """Paper-Metadata + pdf_status."""
        return get_paper(db_path, paper_id)

    @mcp.tool(name="vault.add_paper")
    def _vault_add_paper(
        paper_id: str,
        csl_json: str,
        pdf_path: str = None,
        doi: str = None,
        isbn: str = None,
        page_offset: int = 0,
        editor: str = None,
        chapter: str = None,
        page_first: int = None,
        page_last: int = None,
        container_title: str = None,
        parent_paper_id: str = None,
    ) -> None:
        """Upsert eines Papers. type aus csl_json; book|chapter|article-journal erlaubt."""
        add_paper(
            db_path, paper_id, csl_json,
            pdf_path=pdf_path, doi=doi, isbn=isbn, page_offset=page_offset,
            editor=editor, chapter=chapter,
            page_first=page_first, page_last=page_last,
            container_title=container_title,
            parent_paper_id=parent_paper_id,
        )

    @mcp.tool(name="vault.add_chapter")
    def _vault_add_chapter(
        parent_paper_id: str,
        chapter_number: int,
        csl_json: str,
        paper_id: str = None,
        pdf_path: str = None,
        page_first: int = None,
        page_last: int = None,
    ) -> str:
        """Legt Kapitel als Kind-Paper an. Gibt paper_id zurueck."""
        return add_chapter(
            db_path=db_path,
            parent_paper_id=parent_paper_id,
            chapter_number=chapter_number,
            csl_json=csl_json,
            paper_id=paper_id,
            pdf_path=pdf_path,
            page_first=page_first,
            page_last=page_last,
        )

    @mcp.tool(name="vault.ensure_file")
    def _vault_ensure_file(paper_id: str) -> str:
        """Gibt gecachte file_id zurueck oder laedt PDF hoch."""
        return ensure_file(db_path, paper_id, api_key=_ANTHROPIC_KEY)

    @mcp.tool(name="vault.add_quote")
    def _vault_add_quote(
        paper_id: str,
        verbatim: str,
        extraction_method: str,
        api_response_id: str = None,
        pdf_page: int = None,
        printed_page: int = None,
        section: str = None,
        context_before: str = None,
        context_after: str = None,
    ) -> str:
        """Fuegt Quote ein. extraction_method='citations-api' erfordert api_response_id."""
        return add_quote(
            db_path=db_path,
            paper_id=paper_id,
            verbatim=verbatim,
            extraction_method=extraction_method,
            api_response_id=api_response_id,
            pdf_page=pdf_page,
            printed_page=printed_page,
            section=section,
            context_before=context_before,
            context_after=context_after,
        )

    @mcp.tool(name="vault.search_quote_text")
    def _vault_search_quote_text(verbatim: str, k: int = 5) -> list[dict]:
        """LIKE-Suche in quotes.verbatim. Prueft ob ein Zitat im Vault existiert."""
        return search_quote_text(db_path, verbatim, k)

    @mcp.tool(name="vault.find_quotes")
    def _vault_find_quotes(paper_id: str, query: str = None, k: int = 10) -> list[dict]:
        """Gibt Quotes fuer ein Paper zurueck."""
        return find_quotes(db_path, paper_id, query=query, k=k)

    @mcp.tool(name="vault.get_quote")
    def _vault_get_quote(quote_id: str) -> Optional[dict]:
        """Gibt vollstaendigen Quote-Record zurueck."""
        return get_quote(db_path, quote_id)

    @mcp.tool(name="vault.stats")
    def _vault_stats() -> dict:
        """Counts + Token-Ersparnis-Schaetzung."""
        return get_stats(db_path)

    @mcp.tool(name="vault.set_ocr_done")
    def _vault_set_ocr_done(paper_id: str, value: int = 1) -> None:
        """Setzt ocr_done-Flag (1=OCR durchgefuehrt) fuer ein Paper."""
        set_ocr_done(db_path, paper_id, value)

    @mcp.tool(name="vault.update_pdf_path")
    def _vault_update_pdf_path(paper_id: str, new_path: str) -> None:
        """Aktualisiert den PDF-Pfad nach OCR."""
        update_pdf_path(db_path, paper_id, new_path)

    @mcp.tool(name="vault.set_page_offset")
    def _vault_set_page_offset(paper_id: str, offset: int) -> None:
        """Setzt page_offset fuer ein Paper (Buecher mit Vorseiten/Vorwort)."""
        set_page_offset(db_path, paper_id, offset)

    @mcp.tool(name="vault.get_printed_page")
    def _vault_get_printed_page(paper_id: str, pdf_page: int) -> int:
        """Berechnet gedruckte Seitenzahl: printed_page = pdf_page - page_offset."""
        return get_printed_page(db_path, paper_id, pdf_page)

    return mcp


mcp = _build_mcp_server()


if __name__ == "__main__":
    if mcp is None:
        raise RuntimeError(
            "mcp SDK nicht installiert. "
            "Bitte 'pip install mcp>=1.0' ausfuehren."
        )
    mcp.run()
