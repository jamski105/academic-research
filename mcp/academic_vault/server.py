"""academic_vault MCP-Server.

Stellt MCP-Tools vault.search/get_paper/add_paper/ensure_file/
add_quote/find_quotes/get_quote/stats bereit.

Start via: python -m mcp.academic_vault.server
"""
import json
import os
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Figure-Funktionen (rein, testbar ohne MCP-Framework)
# ---------------------------------------------------------------------------

def add_figure(
    db_path: str,
    paper_id: str,
    page: Optional[int],
    caption: Optional[str],
    vlm_description: Optional[str],
    data_extracted: Optional[str],
) -> str:
    """Fuegt Figure in Vault ein. Gibt figure_id zurueck."""
    db = VaultDB(db_path)
    return db.add_figure(
        paper_id=paper_id,
        page=page,
        caption=caption,
        vlm_description=vlm_description,
        data_extracted_json=data_extracted,
    )


def get_figure(db_path: str, figure_id: str) -> Optional[dict]:
    """Gibt vollstaendigen Figure-Record als dict oder None."""
    db = VaultDB(db_path)
    return db.get_figure(figure_id)


def list_figures(db_path: str, paper_id: str) -> list[dict]:
    """Gibt alle Figures fuer ein Paper, nach page sortiert."""
    db = VaultDB(db_path)
    return db.list_figures(paper_id)


def find_figure_by_caption(
    db_path: str,
    caption_fragment: str,
    paper_id: Optional[str] = None,
) -> list[dict]:
    """LIKE-Suche in figures.caption. Kein MCP-Tool-Dekorator.

    Wird ausschliesslich aus dem verbatim-guard-Hook via Python-Subprocess
    aufgerufen (analog zu search_quote_text).
    """
    db = VaultDB(db_path)
    return db.find_figures_by_caption(caption_fragment, paper_id=paper_id)


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


# ---------------------------------------------------------------------------
# Decision-Log Funktionen (v6.4, #90)
# ---------------------------------------------------------------------------

def add_decision(
    db_path: str,
    category: Optional[str],
    text: str,
    rationale: Optional[str] = None,
) -> str:
    """Fuegt Decision in Vault ein. Gibt decision_id zurueck."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.add_decision(category=category, text=text, rationale=rationale)


def list_decisions(
    db_path: str,
    category: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    """Gibt Decisions zurueck. Optionaler Kategorie-Filter und active_only-Flag."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.list_decisions(category=category, active_only=active_only)


def supersede_decision(db_path: str, decision_id: str, superseded_by: str) -> None:
    """Markiert eine Decision als superseded."""
    db = VaultDB(db_path)
    db.init_schema()
    db.supersede_decision(decision_id=decision_id, superseded_by=superseded_by)


def add_excluded_source(
    db_path: str,
    paper_id: str,
    reason: Optional[str] = None,
) -> None:
    """Fuegt paper_id zu excluded_sources hinzu."""
    db = VaultDB(db_path)
    db.init_schema()
    db.add_excluded_source(paper_id=paper_id, reason=reason)


def list_excluded_sources(db_path: str) -> list[dict]:
    """Gibt alle excluded_sources zurueck."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.list_excluded_sources()


def is_excluded(db_path: str, paper_id: str) -> bool:
    """Gibt True zurueck wenn paper_id in excluded_sources ist."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.is_excluded(paper_id=paper_id)


# ---------------------------------------------------------------------------
# Risk-of-Bias Funktionen (v6.4, #100)
# ---------------------------------------------------------------------------

def add_risk_of_bias(
    db_path: str,
    paper_id: str,
    study_type: str,
    domain_scores: "dict | str",
) -> str:
    """Fuegt RoB-Assessment in Vault ein. Gibt assessment_id zurueck.

    domain_scores: dict oder JSON-String mit Bewertungen pro Domaene.
    """
    if isinstance(domain_scores, dict):
        domain_scores_json = json.dumps(domain_scores, ensure_ascii=False)
    else:
        domain_scores_json = str(domain_scores)
    db = VaultDB(db_path)
    db.init_schema()
    return db.add_risk_of_bias(
        paper_id=paper_id,
        study_type=study_type,
        domain_scores_json=domain_scores_json,
    )


def list_risk_of_bias(
    db_path: str,
    paper_id: Optional[str] = None,
) -> list[dict]:
    """Gibt RoB-Assessments zurueck, optional nach paper_id gefiltert."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.list_risk_of_bias(paper_id=paper_id)


# ---------------------------------------------------------------------------
# Score-History Funktionen (v6.4, #102)
# ---------------------------------------------------------------------------

def add_score_snapshot(
    db_path: str,
    paper_id: str,
    session_id: str,
    scores: "dict | str",
) -> str:
    """Fuegt Score-Snapshot in Vault ein. Gibt snapshot_id zurueck.

    scores: dict oder JSON-String mit Score-Werten.
    """
    if isinstance(scores, dict):
        scores_json = json.dumps(scores, ensure_ascii=False)
    else:
        scores_json = str(scores)
    db = VaultDB(db_path)
    db.init_schema()
    return db.add_score_snapshot(
        paper_id=paper_id,
        session_id=session_id,
        scores_json=scores_json,
    )


def get_score_history(
    db_path: str,
    paper_id: str,
    k: Optional[int] = None,
) -> list[dict]:
    """Gibt Score-History fuer ein Paper zurueck (neueste zuerst)."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.get_score_history(paper_id=paper_id, k=k)


# ---------------------------------------------------------------------------
# Material Passport / Vault Lock Funktionen (v6.4, #104)
# ---------------------------------------------------------------------------

def lock_passport(db_path: str, slug: str) -> None:
    """Setzt Vault-Lock fuer Slug. Vault wird read-only."""
    db = VaultDB(db_path)
    db.init_schema()
    db.lock_vault(slug=slug)


def is_locked(db_path: str, slug: str) -> bool:
    """Gibt True zurueck wenn Vault fuer Slug gelockt ist."""
    db = VaultDB(db_path)
    db.init_schema()
    return db.is_locked(slug=slug)


def export_material_passport(
    db_path: str,
    slug: str,
    output_dir: str = ".",
    score_algo_version: str = "1.0",
    plugin_version: str = "6.4",
    model_versions: Optional[dict] = None,
    per_uni_profile_hash: Optional[str] = None,
) -> str:
    """Exportiert Material-Passport als material-passport.json.

    Gibt den Pfad zur erzeugten Datei zurueck.
    """
    from .material_passport import build_passport, validate_passport

    db = VaultDB(db_path)
    db.init_schema()

    conn = VaultDB._open(db_path)
    try:
        paper_rows = conn.execute(
            "SELECT paper_id, doi, csl_json FROM papers ORDER BY paper_id"
        ).fetchall()
    finally:
        conn.close()

    paper_ids = [r["paper_id"] for r in paper_rows]
    dois = [r["doi"] for r in paper_rows if r["doi"]]
    decisions = db.list_decisions(active_only=True)

    scores_5d: dict = {}
    for pid in paper_ids:
        history = db.get_score_history(pid, k=1)
        if history:
            scores_5d[pid] = json.loads(history[0]["scores_json"])

    pdf_hashes = _compute_pdf_hashes(db_path)

    passport = build_passport(
        slug=slug,
        paper_ids=paper_ids,
        dois=dois,
        scores_5d=scores_5d,
        score_algo_version=score_algo_version,
        plugin_version=plugin_version,
        model_versions=model_versions or {},
        per_uni_profile_hash=per_uni_profile_hash,
        decisions_snapshot=decisions,
        pdf_hashes=pdf_hashes,
    )

    validate_passport(passport)

    out_path = str(Path(output_dir) / "material-passport.json")
    Path(out_path).write_text(
        json.dumps(passport, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


def _compute_pdf_hashes(db_path: str) -> dict:
    """SHA-256-Hashes aller vorhandenen PDFs. Gibt {paper_id: hex_hash} zurueck."""
    import hashlib
    conn = VaultDB._open(db_path)
    try:
        rows = conn.execute(
            "SELECT paper_id, pdf_path FROM papers WHERE pdf_path IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()

    hashes = {}
    for row in rows:
        pdf_path = row["pdf_path"]
        if pdf_path and Path(pdf_path).exists():
            sha = hashlib.sha256()
            with open(pdf_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
            hashes[row["paper_id"]] = sha.hexdigest()
    return hashes


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

    @mcp.tool(name="vault.add_figure")
    def _vault_add_figure(
        paper_id: str,
        page: int = None,
        caption: str = None,
        vlm_description: str = None,
        data_extracted_json: str = None,
    ) -> str:
        """Fuegt Figure/Tabelle in Vault ein. Gibt figure_id zurueck."""
        return add_figure(db_path, paper_id, page, caption, vlm_description, data_extracted_json)

    @mcp.tool(name="vault.get_figure")
    def _vault_get_figure(figure_id: str) -> Optional[dict]:
        """Gibt Figure-Record zurueck oder None."""
        return get_figure(db_path, figure_id)

    @mcp.tool(name="vault.list_figures")
    def _vault_list_figures(paper_id: str) -> list[dict]:
        """Gibt alle Figures fuer ein Paper, nach page sortiert."""
        return list_figures(db_path, paper_id)

    # -----------------------------------------------------------------------
    # v6.4: Decision-Log Tools (#90)
    # -----------------------------------------------------------------------

    @mcp.tool(name="vault.add_decision")
    def _vault_add_decision(
        category: str = None,
        text: str = "",
        rationale: str = None,
    ) -> str:
        """Fuegt Decision in den Vault ein. Gibt decision_id zurueck."""
        return add_decision(db_path, category=category, text=text, rationale=rationale)

    @mcp.tool(name="vault.list_decisions")
    def _vault_list_decisions(
        category: str = None,
        active_only: bool = True,
    ) -> list[dict]:
        """Gibt Decisions zurueck. Optionaler category-Filter, active_only-Flag."""
        return list_decisions(db_path, category=category, active_only=active_only)

    @mcp.tool(name="vault.add_excluded_source")
    def _vault_add_excluded_source(paper_id: str, reason: str = None) -> None:
        """Fuegt paper_id zu excluded_sources hinzu (verhindert Re-Vorschlag)."""
        add_excluded_source(db_path, paper_id=paper_id, reason=reason)

    @mcp.tool(name="vault.is_excluded")
    def _vault_is_excluded(paper_id: str) -> bool:
        """Prueft ob paper_id in excluded_sources ist."""
        return is_excluded(db_path, paper_id=paper_id)

    # -----------------------------------------------------------------------
    # v6.4: Risk-of-Bias Tools (#100)
    # -----------------------------------------------------------------------

    @mcp.tool(name="vault.add_risk_of_bias")
    def _vault_add_risk_of_bias(
        paper_id: str,
        study_type: str,
        domain_scores: str,
    ) -> str:
        """Fuegt RoB-Assessment ein. domain_scores als JSON-String. Gibt assessment_id zurueck."""
        return add_risk_of_bias(db_path, paper_id=paper_id, study_type=study_type, domain_scores=domain_scores)

    @mcp.tool(name="vault.list_risk_of_bias")
    def _vault_list_risk_of_bias(paper_id: str = None) -> list[dict]:
        """Gibt RoB-Assessments zurueck, optional nach paper_id gefiltert."""
        return list_risk_of_bias(db_path, paper_id=paper_id)

    # -----------------------------------------------------------------------
    # v6.4: Score-Trajectory Tools (#102)
    # -----------------------------------------------------------------------

    @mcp.tool(name="vault.add_score_snapshot")
    def _vault_add_score_snapshot(
        paper_id: str,
        session_id: str,
        scores: str,
    ) -> str:
        """Fuegt Score-Snapshot ein. scores als JSON-String. Gibt snapshot_id zurueck."""
        return add_score_snapshot(db_path, paper_id=paper_id, session_id=session_id, scores=scores)

    @mcp.tool(name="vault.get_score_history")
    def _vault_get_score_history(paper_id: str, k: int = None) -> list[dict]:
        """Gibt Score-History fuer ein Paper zurueck (neueste zuerst)."""
        return get_score_history(db_path, paper_id=paper_id, k=k)

    # -----------------------------------------------------------------------
    # v6.4: Material Passport Tools (#104)
    # -----------------------------------------------------------------------

    @mcp.tool(name="vault.export_material_passport")
    def _vault_export_material_passport(
        slug: str,
        output_dir: str = ".",
        score_algo_version: str = "1.0",
        plugin_version: str = "6.4",
    ) -> str:
        """Exportiert material-passport.json. Gibt Dateipfad zurueck."""
        return export_material_passport(
            db_path, slug=slug, output_dir=output_dir,
            score_algo_version=score_algo_version, plugin_version=plugin_version,
        )

    @mcp.tool(name="vault.lock_passport")
    def _vault_lock_passport(slug: str) -> None:
        """Setzt Vault-Lock fuer Slug (macht Vault read-only)."""
        lock_passport(db_path, slug=slug)

    @mcp.tool(name="vault.is_locked")
    def _vault_is_locked(slug: str) -> bool:
        """Prueft ob Vault fuer Slug gelockt ist."""
        return is_locked(db_path, slug=slug)

    return mcp


mcp = _build_mcp_server()


if __name__ == "__main__":
    if mcp is None:
        raise RuntimeError(
            "mcp SDK nicht installiert. "
            "Bitte 'pip install mcp>=1.0' ausfuehren."
        )
    mcp.run()
