"""Tests fuer scripts/chunk_pdf.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Skript direkt laden (kein Package)
_SCRIPT = Path(__file__).parent.parent / "scripts" / "chunk_pdf.py"

# Lazy-load: Modul erst importieren wenn benoetigt, damit fehlende Datei
# nicht alle Tests blockiert.
_chunk_pdf = None


def _get_module():
    global _chunk_pdf
    if _chunk_pdf is None:
        spec = importlib.util.spec_from_file_location("chunk_pdf", _SCRIPT)
        _chunk_pdf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_chunk_pdf)
    return _chunk_pdf


FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_book.pdf"


class TestOutlineParsing:
    def test_extract_chapters_from_outline(self):
        """Outline-Tree mit 4 Kapiteln korrekt parsen."""
        m = _get_module()
        chapters = m.extract_chapters(str(FIXTURE_PDF))
        assert len(chapters) == 4
        assert chapters[0]["title"] == "Kapitel 1: Einleitung"
        assert chapters[0]["start_page"] == 2  # 0-indexed
        assert chapters[1]["start_page"] == 4
        assert chapters[2]["start_page"] == 6
        assert chapters[3]["start_page"] == 8

    def test_chapter_end_page_derived_from_next_start(self):
        """end_page = naechstes Kapitel start - 1."""
        m = _get_module()
        chapters = m.extract_chapters(str(FIXTURE_PDF))
        assert chapters[0]["end_page"] == 3
        assert chapters[1]["end_page"] == 5
        assert chapters[2]["end_page"] == 7
        # Letztes Kapitel endet auf letzter Seite des PDFs (0-indexed: Seite 9)
        assert chapters[3]["end_page"] == 9  # 10 Seiten insgesamt


class TestWriteChapter:
    def test_write_single_chapter_creates_pdf(self):
        """write_chapter schreibt ein gueltiges PDF."""
        from PyPDF2 import PdfReader
        m = _get_module()
        chapters = m.extract_chapters(str(FIXTURE_PDF))
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "ch1.pdf")
            m.write_chapter(str(FIXTURE_PDF), chapters[0], out_path)
            assert os.path.exists(out_path)
            reader = PdfReader(out_path)
            assert len(reader.pages) == 2  # Seiten 2-3 (0-indexed)

    def test_write_all_chapters(self):
        """write_all_chapters erzeugt 4 Dateien."""
        m = _get_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = m.write_all_chapters(
                str(FIXTURE_PDF), tmpdir, isbn="test-isbn"
            )
            assert len(paths) == 4
            for p in paths:
                assert os.path.exists(p)
                assert "test-isbn" in os.path.basename(p)


class TestTOCFallback:
    def test_toc_fallback_for_pdf_without_outline(self, tmp_path):
        """PDF ohne Outline-Tree: Fallback liefert leere Liste oder SystemExit(2)."""
        from PyPDF2 import PdfWriter
        m = _get_module()
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        pdf_path = str(tmp_path / "no_outline.pdf")
        with open(pdf_path, "wb") as f:
            writer.write(f)
        # Kein Outline vorhanden -> Fallback -> kein TOC-Text -> SystemExit(2)
        try:
            chapters = m.extract_chapters(pdf_path)
            # Falls Fallback greift und nichts findet: leere Liste unmoeglich
            # (extract_chapters muss SystemExit werfen oder chapters zurueckgeben)
            assert isinstance(chapters, list)
        except SystemExit as e:
            assert e.code == 2  # Kein TOC gefunden -> Exit 2


class TestCLI:
    def test_cli_toc_mode_returns_json(self):
        """--chapter toc gibt JSON-TOC auf stdout aus."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(FIXTURE_PDF),
             "--chapter", "toc",
             "--output", "/dev/null"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        toc = json.loads(result.stdout)
        assert len(toc) == 4
        assert toc[0]["title"] == "Kapitel 1: Einleitung"

    def test_cli_chapter_n(self, tmp_path):
        """--chapter 1 schreibt eine Datei."""
        out_path = str(tmp_path / "ch1.pdf")
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(FIXTURE_PDF),
             "--chapter", "1",
             "--output", out_path],
            capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out_path)

    def test_cli_chapter_all(self, tmp_path):
        """--chapter all schreibt alle 4 Kapitel."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(FIXTURE_PDF),
             "--chapter", "all",
             "--output", str(tmp_path),
             "--isbn", "978-3-test"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        pdfs = list(tmp_path.glob("*.pdf"))
        assert len(pdfs) == 4

    def test_cli_missing_input_returns_error(self, tmp_path):
        """Nicht-existente Eingabedatei -> returncode 1."""
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(tmp_path / "nope.pdf"),
             "--chapter", "1",
             "--output", str(tmp_path / "out.pdf")],
            capture_output=True, text=True
        )
        assert result.returncode == 1


LARGE_BOOK_PDF = Path(__file__).parent / "fixtures" / "large_book.pdf"


class TestLargeBook:
    def test_write_all_chapters_400_pages_8_chapters(self):
        """AC1: 1 OA-Buch >= 400 Seiten -> 8 Kapitel-PDFs (8 x 55 = 440 Seiten)."""
        from PyPDF2 import PdfReader

        m = _get_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            isbn = "978-3-large-test"
            paths = m.write_all_chapters(
                str(LARGE_BOOK_PDF), tmpdir, isbn=isbn
            )
            # Genau 8 Output-Dateien
            assert len(paths) == 8, f"Erwartet 8 Kapitel, erhalten: {len(paths)}"

            # Namenskonvention: <isbn>-ch<n>.pdf (n=1..8)
            safe_isbn = "978-3-large-test"
            for i, p in enumerate(paths, start=1):
                basename = os.path.basename(p)
                assert basename == f"{safe_isbn}-ch{i}.pdf", (
                    f"Unerwarteter Dateiname: {basename}"
                )
                assert os.path.exists(p), f"Datei existiert nicht: {p}"

            # Gesamtseitenanzahl >= 400
            total_pages = sum(
                len(PdfReader(p).pages) for p in paths
            )
            assert total_pages >= 400, (
                f"Gesamtseitenanzahl zu niedrig: {total_pages}"
            )
