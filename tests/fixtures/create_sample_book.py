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


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).parent / "sample_book.pdf"
    )
    create_sample_book(out)
