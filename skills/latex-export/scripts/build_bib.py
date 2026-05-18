"""build_bib.py — Vault -> .bib (biblatex, DIN-1505-Stil).

Liest alle Papers aus dem Vault und erzeugt eine .bib-Datei
im biblatex-Format mit DIN-1505-konformen Feldern.

Oeffentliche API:
  paper_to_bibtex(paper: dict) -> str
  build_bib_from_vault(db_path: str, output_path: str) -> None
  format_authors_bibtex(authors: list[dict]) -> str
  get_all_papers(db_path: str) -> list[dict]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Vault-Zugriff
# ---------------------------------------------------------------------------

def get_all_papers(db_path: str) -> list[dict]:
    """Gibt alle Papers aus dem Vault als Liste von dicts zurueck.

    Jedes Dict hat mindestens: paper_id, csl_json
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "mcp"))
    try:
        from academic_vault.db import VaultDB
    except ImportError:
        # Fallback fuer Tests ohne vollstaendigen Vault
        return []

    db = VaultDB(db_path)
    conn = db._open(db_path)
    rows = conn.execute("SELECT paper_id, csl_json FROM papers").fetchall()
    conn.close()
    return [{"paper_id": row[0], "csl_json": row[1]} for row in rows]


# ---------------------------------------------------------------------------
# Autoren-Formatierung
# ---------------------------------------------------------------------------

def format_authors_bibtex(authors: list[dict]) -> str:
    """Formatiert CSL-Autoren-Liste im BibTeX-Format.

    Format: "Last, First and Last2, First2"
    DIN-1505: Nachname, Vorname-Reihenfolge.

    Args:
        authors: Liste von CSL-Autoren-Dicts mit 'family' und 'given'

    Returns:
        BibTeX-Autoren-String
    """
    parts = []
    for author in authors:
        family = author.get("family", "")
        given = author.get("given", "")
        if given:
            parts.append(f"{family}, {given}")
        else:
            parts.append(family)
    return " and ".join(parts)


# ---------------------------------------------------------------------------
# BibTeX-Entry-Generierung
# ---------------------------------------------------------------------------

def _get_year(csl: dict) -> str:
    """Extrahiert Jahr aus CSL issued-Feld."""
    issued = csl.get("issued", {})
    date_parts = issued.get("date-parts", [[]])
    if date_parts and date_parts[0]:
        return str(date_parts[0][0])
    return ""


def _entry_type(csl_type: str) -> str:
    """Mappt CSL-Typ auf BibTeX-Entry-Typ."""
    mapping = {
        "article-journal": "article",
        "article-magazine": "article",
        "article-newspaper": "article",
        "book": "book",
        "chapter": "incollection",
        "entry-encyclopedia": "inreference",
        "thesis": "thesis",
        "report": "report",
        "paper-conference": "inproceedings",
        "webpage": "online",
    }
    return mapping.get(csl_type, "misc")


def paper_to_bibtex(paper: dict) -> str:
    """Konvertiert einen Vault-Paper-Record in einen BibTeX-Entry-String.

    DIN-1505-konforme Felder:
    - author, title, year
    - fuer article: journal, volume, number, pages, doi
    - fuer book: publisher, address, edition
    - fuer incollection: booktitle, editor, publisher, address, pages

    Args:
        paper: dict mit 'paper_id' und 'csl_json'

    Returns:
        BibTeX-Entry-String
    """
    try:
        csl = json.loads(paper.get("csl_json", "{}"))
    except json.JSONDecodeError:
        csl = {}

    paper_id = paper.get("paper_id", "unknown")
    csl_type = csl.get("type", "misc")
    entry_type = _entry_type(csl_type)

    lines = [f"@{entry_type}{{{paper_id},"]

    # --- Pflichtfelder ---
    authors = csl.get("author", [])
    if authors:
        lines.append(f"  author = {{{format_authors_bibtex(authors)}}},")

    title = csl.get("title", "")
    if title:
        lines.append(f"  title = {{{title}}},")

    year = _get_year(csl)
    if year:
        lines.append(f"  year = {{{year}}},")

    # --- Typ-spezifische Felder ---
    if entry_type == "article":
        journal = csl.get("container-title", "")
        if journal:
            lines.append(f"  journal = {{{journal}}},")
        volume = csl.get("volume", "")
        if volume:
            lines.append(f"  volume = {{{volume}}},")
        issue = csl.get("issue", "")
        if issue:
            lines.append(f"  number = {{{issue}}},")
        pages = csl.get("page", "")
        if pages:
            lines.append(f"  pages = {{{pages}}},")

    elif entry_type in ("book",):
        publisher = csl.get("publisher", "")
        if publisher:
            lines.append(f"  publisher = {{{publisher}}},")
        place = csl.get("publisher-place", "")
        if place:
            lines.append(f"  address = {{{place}}},")
        edition = csl.get("edition", "")
        if edition:
            lines.append(f"  edition = {{{edition}}},")

    elif entry_type == "incollection":
        booktitle = csl.get("container-title", "")
        if booktitle:
            lines.append(f"  booktitle = {{{booktitle}}},")
        editors = csl.get("editor", [])
        if editors:
            lines.append(f"  editor = {{{format_authors_bibtex(editors)}}},")
        publisher = csl.get("publisher", "")
        if publisher:
            lines.append(f"  publisher = {{{publisher}}},")
        place = csl.get("publisher-place", "")
        if place:
            lines.append(f"  address = {{{place}}},")
        pages = csl.get("page", "")
        if pages:
            lines.append(f"  pages = {{{pages}}},")

    # --- DOI (alle Typen) ---
    doi = csl.get("DOI", "") or csl.get("doi", "")
    if doi:
        lines.append(f"  doi = {{{doi}}},")

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Oeffentliche Build-Funktion
# ---------------------------------------------------------------------------

def build_bib_from_vault(db_path: str, output_path: str) -> None:
    """Liest alle Papers aus dem Vault und schreibt .bib-Datei.

    Args:
        db_path: Pfad zur Vault-DB
        output_path: Pfad fuer die .bib-Ausgabedatei
    """
    papers = get_all_papers(db_path)
    entries = []
    for paper in papers:
        try:
            entry = paper_to_bibtex(paper)
            entries.append(entry)
        except Exception as e:
            # Einzelnes fehlerhaftes Paper soll die Generierung nicht stoppen
            import sys as _sys
            print(f"[build_bib] Warnung: Paper '{paper.get('paper_id', '?')}' uebersprungen: {e}",
                  file=_sys.stderr)

    bib_content = "\n\n".join(entries) + "\n" if entries else ""

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(bib_content, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: build_bib.py <vault.db> <output.bib>", file=sys.stderr)
        sys.exit(1)
    build_bib_from_vault(sys.argv[1], sys.argv[2])
