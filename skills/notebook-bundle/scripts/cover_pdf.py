"""Erzeugt Bibliographie-Cover-PDF aus einer Paper-Liste.

Nutzt PyPDF2-Stream-Injection (kein reportlab, kein fpdf).
Jede Zeile wird als PDF-Content-Stream in eine Blank-Page injiziert.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

# Seitengröße A4 in Punkten
PAGE_WIDTH = 595
PAGE_HEIGHT = 842

# Schriftgrößen (nur Helvetica — eingebettet in PDF-Spec, kein Font-Embedding nötig)
FONT_TITLE = 16
FONT_BODY = 11
FONT_SMALL = 9

# Zeilenabstand
LINE_HEIGHT_BODY = 20
LINE_HEIGHT_TITLE = 30


def _add_font_resources(page: DictionaryObject, writer: PdfWriter) -> None:
    """Fügt Helvetica-Font-Resource zur Seite hinzu."""
    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = writer._add_object(font_dict)

    resources = DictionaryObject()
    font_resources = DictionaryObject()
    font_resources[NameObject("/Helvetica")] = font_ref
    resources[NameObject("/Font")] = font_resources
    page[NameObject("/Resources")] = resources


def _safe_pdf_string(text: str) -> str:
    """Bereinigt Text für PDF-Literal-String (escaped Klammern, Backslash)."""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def _make_text_page_bytes(text_entries: list[tuple[str, int, int, int]]) -> bytes:
    """Erzeugt eine PDF-Seite mit Text via Content-Stream.

    Args:
        text_entries: Liste von (text, x, y, font_size).
                      Koordinaten in Punkten (0,0 = unten links A4).

    Returns:
        Serialisiertes PDF (eine Seite) als bytes.

    Note:
        add_blank_page() gibt ein transientes Objekt zurück; die tatsächliche
        persistierte Seite im Writer ist writer.pages[-1]. Mutation muss am
        persistierten Objekt erfolgen, damit write() die Änderungen serialisiert.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    # Persistiertes Seiten-Objekt (nicht den Rückgabewert von add_blank_page)
    page = writer.pages[-1]

    stream_parts = ["BT"]
    for text, x, y, size in text_entries:
        safe = _safe_pdf_string(text)
        stream_parts.append(f"/Helvetica {size} Tf")
        stream_parts.append(f"{x} {y} Td")
        stream_parts.append(f"({safe}) Tj")
        stream_parts.append("0 0 Td")
    stream_parts.append("ET")

    stream_data = "\n".join(stream_parts).encode("latin-1", errors="replace")
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(stream_data)
    stream_ref = writer._add_object(stream_obj)
    page[NameObject("/Contents")] = stream_ref
    _add_font_resources(page, writer)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_cover(papers: List[Dict[str, Any]], output_path: str) -> None:
    """Erzeugt Bibliographie-Cover-PDF mit allen Paper-Einträgen.

    Args:
        papers: Liste von Paper-Dicts mit keys: title, authors, year, id.
        output_path: Ausgabepfad für die Cover-PDF.
    """
    writer = PdfWriter()
    MARGIN_LEFT = 50
    PAPERS_PER_PAGE = 25

    # Seiten aufbauen
    page_entries: list[tuple[str, int, int, int]] = []
    y = PAGE_HEIGHT - 60

    # Kopfzeile
    page_entries.append(("Bibliographie -- NotebookLM Bundle", MARGIN_LEFT, y, FONT_TITLE))
    y -= LINE_HEIGHT_TITLE
    page_entries.append(
        (
            "HINWEIS: NotebookLM-Antworten sind NICHT verbatim-garantiert.",
            MARGIN_LEFT,
            y,
            FONT_SMALL,
        )
    )
    y -= LINE_HEIGHT_BODY

    papers_on_current_page = 0

    for i, paper in enumerate(papers):
        if papers_on_current_page >= PAPERS_PER_PAGE:
            # Aktuelle Seite flushen, neue beginnen
            page_bytes = _make_text_page_bytes(page_entries)
            page_reader = PdfReader(io.BytesIO(page_bytes))
            writer.add_page(page_reader.pages[0])
            page_entries = []
            y = PAGE_HEIGHT - 60
            papers_on_current_page = 0

        title = paper.get("title", "(kein Titel)")
        authors = paper.get("authors", [])
        year = paper.get("year", "")
        authors_str = "; ".join(str(a) for a in authors)
        entry = f"[{i + 1}] {title} -- {authors_str} ({year})"

        page_entries.append((entry, MARGIN_LEFT, y, FONT_BODY))
        y -= LINE_HEIGHT_BODY
        papers_on_current_page += 1

    # Letzte / einzige Seite flushen
    if page_entries:
        page_bytes = _make_text_page_bytes(page_entries)
        page_reader = PdfReader(io.BytesIO(page_bytes))
        writer.add_page(page_reader.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)
