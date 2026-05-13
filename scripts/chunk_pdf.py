#!/usr/bin/env python3
"""chunk_pdf.py — Zerlegt Buch-PDFs kapitelweise via PyPDF2 Outline-Tree.

CLI:
    python chunk_pdf.py --input book.pdf --chapter <n|toc|all> --output <pfad>

Kapitel-Erkennung (Prioritaet):
    1. PyPDF2 Outline-Tree (PdfReader.outline)
    2. Fallback: Textextraktion erste 20 Seiten, Regex-Kapitelsuche

Ausgabe:
    --chapter all  -> Alle Kapitel nach <output_dir>/<isbn>-ch<n>.pdf
    --chapter N    -> Kapitel N (1-basiert) nach <output>-Pfad
    --chapter toc  -> JSON-TOC auf stdout
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Optional

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import Destination


def _outline_page_number(reader: PdfReader, item) -> Optional[int]:
    """Gibt 0-indexed Seitennummer eines Outline-Items zurueck oder None."""
    try:
        if isinstance(item, Destination):
            return reader.get_destination_page_number(item)
        # Neuere PyPDF2-Versionen: item kann dict-aehnlich sein
        if hasattr(item, "page"):
            page_obj = item.page
            if hasattr(page_obj, "get_object"):
                page_obj = page_obj.get_object()
            for i, p in enumerate(reader.pages):
                if p.get_object() == page_obj:
                    return i
    except Exception:
        pass
    return None


def _flatten_outline(reader: PdfReader, outline, depth: int = 0) -> list[dict]:
    """Flacht den Outline-Tree auf Top-Level-Kapitel ab (Tiefe 0)."""
    result = []
    if outline is None:
        return result
    for item in outline:
        if isinstance(item, list):
            # Verschachtelte Liste: Sub-Ebene nur bei depth==0 aufnehmen
            if depth == 0:
                result.extend(_flatten_outline(reader, item, depth + 1))
        else:
            page_num = _outline_page_number(reader, item)
            title = getattr(item, "title", None) or str(item)
            if page_num is not None and title:
                result.append({"title": title, "start_page": page_num})
    return result


def _extract_via_outline(reader: PdfReader) -> list[dict]:
    """Extrahiert Kapitel aus PyPDF2 Outline-Tree. Gibt [] wenn kein Outline."""
    outline = reader.outline
    if not outline:
        return []
    chapters = _flatten_outline(reader, outline)
    # Duplikate entfernen und sortieren
    seen: set[tuple] = set()
    unique = []
    for ch in chapters:
        key = (ch["title"], ch["start_page"])
        if key not in seen:
            seen.add(key)
            unique.append(ch)
    unique.sort(key=lambda c: c["start_page"])
    return unique


def _extract_via_toc_text(reader: PdfReader) -> list[dict]:
    """Fallback: Sucht Kapitelzeilen in den ersten 20 Seiten per Regex."""
    patterns = [
        # "Kapitel 1: Titel .... 5" oder "Chapter 1 Title 5"
        re.compile(
            r"(?:Kapitel|Chapter)\s+(\d+)[.:)]\s*(.+?)\s+(\d+)\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        # "1. Titel     5"
        re.compile(
            r"^(\d+)\.\s+([A-Za-zÄÖÜäöüß][^\n]{3,60}?)\s{2,}(\d+)\s*$",
            re.MULTILINE,
        ),
    ]
    text_pages = min(20, len(reader.pages))
    full_text = ""
    for i in range(text_pages):
        try:
            full_text += (reader.pages[i].extract_text() or "") + "\n"
        except Exception:
            pass

    chapters: list[dict] = []
    for pat in patterns:
        for m in pat.finditer(full_text):
            try:
                num = int(m.group(1))
                title = m.group(2).strip()
                page = int(m.group(3)) - 1  # 1-indexed -> 0-indexed
                if 0 <= page < len(reader.pages):
                    chapters.append({
                        "title": f"Kapitel {num}: {title}",
                        "start_page": page,
                    })
            except (ValueError, IndexError):
                pass
        if chapters:
            break

    chapters.sort(key=lambda c: c["start_page"])
    # Duplikate entfernen
    seen_pages: set[int] = set()
    unique = []
    for ch in chapters:
        if ch["start_page"] not in seen_pages:
            seen_pages.add(ch["start_page"])
            unique.append(ch)
    return unique


def _assign_end_pages(chapters: list[dict], total_pages: int) -> list[dict]:
    """Berechnet end_page fuer jedes Kapitel (in-place)."""
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            ch["end_page"] = chapters[i + 1]["start_page"] - 1
        else:
            ch["end_page"] = total_pages - 1
    return chapters


def extract_chapters(pdf_path: str) -> list[dict]:
    """Extrahiert Kapitel-Metadaten aus PDF.

    Gibt [{title, start_page, end_page}] zurueck (0-indexed Seitennummern).
    Raises SystemExit(2) wenn weder Outline noch TOC-Text gefunden.
    """
    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    chapters = _extract_via_outline(reader)
    if not chapters:
        chapters = _extract_via_toc_text(reader)
    if not chapters:
        print(
            f"[chunk_pdf] Fehler: Kein Outline-Tree und kein TOC-Text in "
            f"'{pdf_path}' gefunden.",
            file=sys.stderr,
        )
        sys.exit(2)

    return _assign_end_pages(chapters, total)


def _write_chapter_from_reader(
    reader: PdfReader, chapter: dict, output_path: str
) -> None:
    """Schreibt Seiten eines Kapitels mit vorhandenem PdfReader-Objekt."""
    writer = PdfWriter()
    start = chapter["start_page"]
    end = chapter["end_page"]
    for page_num in range(start, end + 1):
        if 0 <= page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def write_chapter(pdf_path: str, chapter: dict, output_path: str) -> None:
    """Schreibt Seiten eines Kapitels als neues PDF nach output_path."""
    _write_chapter_from_reader(PdfReader(pdf_path), chapter, output_path)


def write_all_chapters(
    pdf_path: str,
    output_dir: str,
    isbn: str = "book",
) -> list[str]:
    """Schreibt alle Kapitel als separate PDFs. Gibt Liste der Pfade zurueck.

    Oeffnet das Quell-PDF einmalig fuer alle Kapitel (kein N+1-Overhead).
    """
    chapters = extract_chapters(pdf_path)
    reader = PdfReader(pdf_path)  # einmalig oeffnen
    os.makedirs(output_dir, exist_ok=True)
    safe_isbn = re.sub(r"[^a-zA-Z0-9_-]", "-", isbn)
    paths = []
    for i, ch in enumerate(chapters, start=1):
        fname = f"{safe_isbn}-ch{i}.pdf"
        out_path = os.path.join(output_dir, fname)
        _write_chapter_from_reader(reader, ch, out_path)
        paths.append(out_path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zerlegt Buch-PDFs kapitelweise (PyPDF2 Outline-Tree)."
    )
    parser.add_argument("--input", required=True, help="Eingabe-PDF")
    parser.add_argument(
        "--chapter",
        required=True,
        help="Kapitel-Nummer (1-basiert), 'all' oder 'toc'",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Ausgabe-Pfad oder Verzeichnis (bei --chapter all)",
    )
    parser.add_argument(
        "--isbn",
        default="book",
        help="ISBN fuer Dateinamen (bei --chapter all)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(
            f"[chunk_pdf] Eingabe-PDF nicht gefunden: {args.input}",
            file=sys.stderr,
        )
        return 1

    if args.chapter == "toc":
        chapters = extract_chapters(args.input)
        print(
            json.dumps(
                [
                    {
                        "title": c["title"],
                        "start_page": c["start_page"],
                        "end_page": c["end_page"],
                    }
                    for c in chapters
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.chapter == "all":
        paths = write_all_chapters(args.input, args.output, isbn=args.isbn)
        print(f"[chunk_pdf] {len(paths)} Kapitel geschrieben nach {args.output}")
        for p in paths:
            print(f"  {p}")
        return 0

    # Einzelnes Kapitel (1-basiert)
    try:
        n = int(args.chapter)
    except ValueError:
        print(
            f"[chunk_pdf] Ungueltige Kapitel-Angabe: {args.chapter!r}",
            file=sys.stderr,
        )
        return 1

    chapters = extract_chapters(args.input)
    if n < 1 or n > len(chapters):
        print(
            f"[chunk_pdf] Kapitel {n} nicht vorhanden (1-{len(chapters)}).",
            file=sys.stderr,
        )
        return 1

    write_chapter(args.input, chapters[n - 1], args.output)
    print(f"[chunk_pdf] Kapitel {n} geschrieben: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
