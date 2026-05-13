"""Erstellt sample_book.pdf mit PyPDF2 fuer Tests.

Erzeugt ein minimales PDF mit 4 Kapiteln im Outline-Tree.
Aufruf: python tests/fixtures/create_sample_book.py
"""
import os
import sys
from pathlib import Path


def create_sample_book(output_path: str) -> None:
    from PyPDF2 import PdfWriter

    writer = PdfWriter()

    # 10 Seiten: 2 Titelseiten + je 2 Seiten pro Kapitel (4 Kapitel)
    for i in range(10):
        writer.add_blank_page(width=595, height=842)

    # Outline-Eintraege: 4 Kapitel (0-indexed Seitennummern)
    chapters = [
        ("Kapitel 1: Einleitung", 2),
        ("Kapitel 2: Grundlagen", 4),
        ("Kapitel 3: Methodik", 6),
        ("Kapitel 4: Ergebnisse", 8),
    ]
    for title, page_num in chapters:
        writer.add_outline_item(title, page_num)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Erstellt: {output_path} ({os.path.getsize(output_path)} Bytes)")


def create_large_book(output_path: str, num_chapters: int = 8, pages_per_chapter: int = 55) -> None:
    """Erstellt synthetisches PDF mit num_chapters Kapiteln und pages_per_chapter Seiten je Kapitel.

    8 x 55 = 440 Seiten, Outline-Tree korrekt gesetzt.
    """
    from PyPDF2 import PdfWriter

    writer = PdfWriter()

    total_pages = num_chapters * pages_per_chapter
    for _ in range(total_pages):
        writer.add_blank_page(width=595, height=842)

    # Outline-Eintraege: num_chapters Kapitel (0-indexed Seitennummern)
    for i in range(num_chapters):
        title = f"Kapitel {i + 1}: Abschnitt {i + 1}"
        start_page = i * pages_per_chapter
        writer.add_outline_item(title, start_page)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"Erstellt: {output_path} ({os.path.getsize(output_path)} Bytes, {total_pages} Seiten, {num_chapters} Kapitel)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).parent / "sample_book.pdf"
    )
    create_sample_book(out)
    large_out = str(Path(__file__).parent / "large_book.pdf")
    create_large_book(large_out)
