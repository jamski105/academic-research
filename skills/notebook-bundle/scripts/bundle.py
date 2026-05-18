"""NotebookLM-Bundle — konkateniert PDFs zu einem Bundle für manuellen Upload.

CLI:
    python bundle.py <selection_json> [--output <path>] [--output-dir <dir>]
                     [--size-limit-mb <N>]

Rückgabe von build_bundle():
    {
        "status": "ok" | "split" | "partial",
        "output_files": ["/path/to/bundle.pdf"],
        "skipped_ids": ["paper_id", ...],
        "skipped_count": N,
        "total_pages": N,
    }
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

# cover_pdf aus demselben scripts/-Verzeichnis importieren
_SCRIPTS_DIR = Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from cover_pdf import generate_cover, _add_font_resources, _safe_pdf_string  # noqa: E402

# Standard-Größenlimit: 500 MB
DEFAULT_SIZE_LIMIT_MB = 500


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _timestamp() -> str:
    """Gibt aktuellen Zeitstempel im Format YYYYMMDDTHHmmss zurück."""
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def _make_toc_bytes(papers: List[Dict[str, Any]], page_numbers: List[int]) -> bytes:
    """Erzeugt TOC-Seite als PDF-Bytes.

    Args:
        papers:       Paper-Dicts (title, year).
        page_numbers: Seitennummer (1-basiert) jedes Papers im finalen Bundle.

    Returns:
        PDF-Bytes der TOC-Seite.

    Note:
        Nutzt writer.pages[-1] für Stream-Injection (PyPDF2-Quirk:
        add_blank_page() gibt transientes Objekt zurück).
    """
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    page = writer.pages[-1]

    PAGE_HEIGHT = 842
    MARGIN_LEFT = 50

    stream_parts = ["BT"]
    y = PAGE_HEIGHT - 60

    # Überschrift
    stream_parts.append("/Helvetica 16 Tf")
    stream_parts.append(f"{MARGIN_LEFT} {y} Td")
    stream_parts.append("(Inhaltsverzeichnis) Tj")
    stream_parts.append("0 0 Td")
    y -= 40

    for i, (paper, pnum) in enumerate(zip(papers, page_numbers)):
        title = paper.get("title", "(kein Titel)")
        year = paper.get("year", "")
        safe_entry = _safe_pdf_string(f"{i + 1}. {title} ({year}) ............ S. {pnum}")
        stream_parts.append("/Helvetica 11 Tf")
        stream_parts.append(f"{MARGIN_LEFT} {y} Td")
        stream_parts.append(f"({safe_entry}) Tj")
        stream_parts.append("0 0 Td")
        y -= 18
        if y < 60:
            break  # TOC zu lang — truncieren (genug für ~40 Paper)

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


def _flush_writer(writer: PdfWriter, path: str) -> None:
    """Schreibt PdfWriter-Inhalt in Datei."""
    with open(path, "wb") as f:
        writer.write(f)


# ---------------------------------------------------------------------------
# Haupt-API
# ---------------------------------------------------------------------------

def build_bundle(
    selection_json: str,
    output_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    size_limit_mb: float = DEFAULT_SIZE_LIMIT_MB,
) -> Dict[str, Any]:
    """Erzeugt NotebookLM-Bundle-PDF(s) aus einer Paper-Selektion.

    Args:
        selection_json: Pfad zur selection.json.
        output_path:    Expliziter Ausgabepfad (optional).
                        Wenn None, wird auto-Name unter output_dir generiert.
        output_dir:     Ausgabeverzeichnis für auto-generierten Dateinamen.
                        Default: aktuelles Verzeichnis.
        size_limit_mb:  Maximale Dateigröße pro Bundle in MB (default: 500).

    Returns:
        Dict mit:
            status:       "ok" | "split" | "partial"
            output_files: Liste der erzeugten PDF-Pfade
            skipped_ids:  IDs der übersprungenen Paper (fehlende PDFs)
            skipped_count: Anzahl übersprungener Paper
            total_pages:  Gesamtseitenzahl über alle Output-Dateien
    """
    size_limit_bytes = size_limit_mb * 1024 * 1024
    ts = _timestamp()

    selection_text = Path(selection_json).read_text(encoding="utf-8")
    selection = json.loads(selection_text)
    papers: List[Dict[str, Any]] = selection.get("papers", [])

    valid_papers: List[Dict[str, Any]] = []
    skipped_ids: List[str] = []
    for paper in papers:
        pdf_path = paper.get("pdf_path", "")
        if pdf_path and Path(pdf_path).exists():
            valid_papers.append(paper)
        else:
            skipped_ids.append(paper.get("id", "unknown"))

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_cover_path = tmp.name
    try:
        generate_cover(valid_papers, tmp_cover_path)
        cover_reader = PdfReader(tmp_cover_path)
        cover_pages_count = len(cover_reader.pages)

        paper_readers: List[tuple[Dict[str, Any], PdfReader]] = []
        for paper in valid_papers:
            try:
                reader = PdfReader(paper["pdf_path"])
                paper_readers.append((paper, reader))
            except Exception:
                skipped_ids.append(paper.get("id", "unknown"))

        # Seite 1 = TOC, Seiten 2..(1+cover_pages_count) = Cover, dann Paper
        page_numbers: List[int] = []
        current_page = 2 + cover_pages_count  # 1 (TOC) + cover_pages
        for _, reader in paper_readers:
            page_numbers.append(current_page)
            current_page += len(reader.pages)

        toc_papers = [p for p, _ in paper_readers]
        toc_bytes = _make_toc_bytes(toc_papers, page_numbers)
        toc_reader = PdfReader(io.BytesIO(toc_bytes))

        def _make_out_path(part: Optional[int] = None) -> str:
            if output_path is not None and part is None:
                return output_path
            base = output_dir or os.getcwd()
            if part is None:
                return str(Path(base) / f"notebook-bundle-{ts}.pdf")
            else:
                return str(Path(base) / f"notebook-bundle-{ts}-part{part}.pdf")

        # 8. Bundle(s) aufbauen
        output_files: List[str] = []
        need_split = False
        part = 1
        total_pages = 0  # während Build akkumuliert (kein Re-Read nötig)

        writer = PdfWriter()
        # TOC + Cover immer in ersten Bundle
        for p in toc_reader.pages:
            writer.add_page(p)
        for p in cover_reader.pages:
            writer.add_page(p)
        total_pages += len(toc_reader.pages) + cover_pages_count

        # Akkumulierte Byte-Summe für Größenschätzung (O(1) pro Paper)
        current_size_bytes: int = Path(tmp_cover_path).stat().st_size

        for paper, reader in paper_readers:
            paper_pdf_path = paper["pdf_path"]
            paper_size = Path(paper_pdf_path).stat().st_size
            # Größenprüfung: würde dieses Paper das Limit überschreiten?
            if current_size_bytes + paper_size > size_limit_bytes and writer.pages:
                out = _make_out_path(part)
                _flush_writer(writer, out)
                output_files.append(out)
                part += 1
                need_split = True
                writer = PdfWriter()
                current_size_bytes = 0

            for page in reader.pages:
                writer.add_page(page)
            total_pages += len(reader.pages)
            current_size_bytes += paper_size

        # Letzten Writer flushen
        if writer.pages:
            out = _make_out_path(part if need_split else None)
            _flush_writer(writer, out)
            output_files.append(out)

    finally:
        try:
            os.unlink(tmp_cover_path)
        except OSError:
            pass

    status = "split" if need_split else ("partial" if skipped_ids else "ok")

    return {
        "status": status,
        "output_files": output_files,
        "skipped_ids": skipped_ids,
        "skipped_count": len(skipped_ids),
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI-Einstiegspunkt für notebook-bundle."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "NotebookLM-Bundle: Konkateniert PDFs für manuellen Upload.\n\n"
            "WICHTIG: NotebookLM-Antworten sind NICHT verbatim-garantiert.\n"
            "Für Zitate: Vault-Zitat-Pfad (vault.add_quote) nutzen."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("selection_json", help="Pfad zur selection.json")
    parser.add_argument("--output", help="Expliziter Ausgabepfad")
    parser.add_argument("--output-dir", dest="output_dir", help="Ausgabeverzeichnis (auto-Name)")
    parser.add_argument(
        "--size-limit-mb",
        dest="size_limit_mb",
        type=float,
        default=DEFAULT_SIZE_LIMIT_MB,
        help=f"Max. Bundle-Größe in MB (default: {DEFAULT_SIZE_LIMIT_MB})",
    )
    args = parser.parse_args()

    result = build_bundle(
        args.selection_json,
        output_path=args.output,
        output_dir=args.output_dir,
        size_limit_mb=args.size_limit_mb,
    )

    print(f"Status: {result['status']}")
    print("Output-Dateien:")
    for f in result["output_files"]:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        num_pages = len(PdfReader(f).pages)
        print(f"  {f}  ({size_mb:.2f} MB, {num_pages} Seiten)")
    if result["skipped_ids"]:
        print(
            f"Übersprungen ({result['skipped_count']}): "
            f"{', '.join(result['skipped_ids'])}"
        )
    print()
    print(
        "⚠️  Erinnerung: NotebookLM-Antworten sind NICHT verbatim-garantiert.\n"
        "    Für Zitate: Vault-Zitat-Pfad nutzen."
    )


if __name__ == "__main__":
    main()
