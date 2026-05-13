#!/usr/bin/env python3
"""Erzeugt minimale Test-Fixture-PDFs fuer OCR-Tests."""
import os
import sys

from PyPDF2 import PdfWriter


def create_empty_pdf(path: str, pages: int = 3) -> None:
    """PDF mit leeren Seiten (kein Text-Layer)."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def create_text_pdf(path: str) -> None:
    """PDF mit Text-Inhalt via reportlab (Fallback: leeres PDF wenn reportlab fehlt)."""
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(path)
        c.drawString(100, 750, "Dies ist ein Test-Dokument mit ausreichend Text-Inhalt.")
        c.drawString(100, 700, "Zweite Zeile mit weiterem Text fuer die OCR-Erkennung.")
        c.drawString(100, 650, "Dritte Zeile mit noch mehr Text damit die Erkennung klappt.")
        c.save()
    except ImportError:
        # Fallback: leeres PDF (wird in Tests ohnehin gemockt)
        create_empty_pdf(path, pages=2)


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    create_empty_pdf(os.path.join(base, "scan_no_text.pdf"), pages=5)
    create_text_pdf(os.path.join(base, "text_document.pdf"))
    print("Fixtures erstellt.")
