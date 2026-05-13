"""Erzeugt 5 synthetische PDF-Fixtures fuer page_offset-Tests.

Aufruf: python tests/fixtures/page_offset/create_fixtures.py
Benoetigt: reportlab (pip install reportlab)
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


OUT = Path(__file__).parent


def create_no_preface(path: Path) -> None:
    """Buch ohne Vorwort: gedruckte Seite 1 auf PDF-Seite 1 (offset=0)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))  # Seitenzahl unten
        c.drawString(72, 750, f"Inhalt Seite {printed}")
        c.showPage()
    c.save()


def create_ten_prefaces(path: Path) -> None:
    """10 Vorseiten (unnummeriert), dann gedruckte Seite 1 (offset=10)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(10):
        c.drawString(72, 750, f"Vorwort Seite {i + 1}")
        # keine Seitenzahl unten
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Kapitel Inhalt {printed}")
        c.showPage()
    c.save()


def create_roman_numerals(path: Path) -> None:
    """Seiten i-vi (roemisch), dann arabisch ab 1 auf PDF-Seite 7 (offset=6)."""
    roman = ["i", "ii", "iii", "iv", "v", "vi"]
    c = canvas.Canvas(str(path), pagesize=A4)
    for r in roman:
        c.drawString(72, 40, r)
        c.drawString(72, 750, f"Vorbemerkung {r}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Kapitel {printed}")
        c.showPage()
    c.save()


def create_double_pagination(path: Path) -> None:
    """5 unnummerierte Seiten (Deckblatt etc.), dann arabisch ab 1 (offset=5)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(5):
        c.drawString(72, 750, f"Frontmatter {i + 1}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Text {printed}")
        c.showPage()
    c.save()


def create_large_offset(path: Path) -> None:
    """25 Vorseiten, arabische 1 auf PDF-Seite 26 (offset=25)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(25):
        c.drawString(72, 750, f"Frontmatter {i + 1}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Inhalt {printed}")
        c.showPage()
    c.save()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    create_no_preface(OUT / "no_preface.pdf")
    create_ten_prefaces(OUT / "ten_prefaces.pdf")
    create_roman_numerals(OUT / "roman_numerals.pdf")
    create_double_pagination(OUT / "double_pagination.pdf")
    create_large_offset(OUT / "large_offset.pdf")
    print(f"5 Fixtures erstellt in {OUT}")
