"""Tests fuer OCR-Detection und ocrmypdf-Workflow."""
import os
import sys
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# scripts/ im Suchpfad
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "ocr")


# ---------------------------------------------------------------------------
# detect_needs_ocr
# ---------------------------------------------------------------------------

class TestDetectNeedsOcr:
    """Tests fuer scripts.pdf.detect_needs_ocr."""

    def test_text_pdf_returns_false(self):
        """PDF mit viel Text → False (kein OCR noetig)."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 200  # 200 Zeichen pro Seite

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 10

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is False

    def test_scan_pdf_returns_true(self):
        """PDF ohne Text-Layer → True (OCR benoetigt)."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # kein Text

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 10

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is True

    def test_mixed_pdf_returns_true(self):
        """Mischung: wenige Seiten mit Text, viele leer → True (Durchschnitt < 100)."""
        from pdf import detect_needs_ocr

        pages = []
        # 2 Seiten mit etwas Text (50 Zeichen), 8 Seiten leer
        # Durchschnitt aus 5 Stichproben-Seiten wird < 100
        for _ in range(2):
            p = MagicMock()
            p.extract_text.return_value = "A" * 50
            pages.append(p)
        for _ in range(8):
            p = MagicMock()
            p.extract_text.return_value = ""
            pages.append(p)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        # Mit festem Seed sicherstellen dass Sample die leeren Seiten trifft
        import random
        with patch("pdf.PdfReader", return_value=mock_reader):
            with patch("random.sample", return_value=[2, 4, 6, 7, 9]):
                result = detect_needs_ocr("dummy.pdf", sample_pages=5, threshold=100)

        assert result is True

    def test_empty_pdf_returns_true(self):
        """PDF ohne Seiten → True."""
        from pdf import detect_needs_ocr

        mock_reader = MagicMock()
        mock_reader.pages = []

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is True

    def test_sample_pages_capped_at_total(self):
        """Wenn sample_pages > Gesamtseiten, werden alle Seiten benutzt."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 50  # unter threshold

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 3  # nur 3 Seiten

        with patch("pdf.PdfReader", return_value=mock_reader):
            # sample_pages=10 > 3 Seiten — soll nicht crashen
            result = detect_needs_ocr("dummy.pdf", sample_pages=10, threshold=100)

        assert result is True  # 50 < 100


# ---------------------------------------------------------------------------
# run_ocrmypdf
# ---------------------------------------------------------------------------

class TestRunOcrmypdf:
    """Tests fuer scripts.ocr.run_ocrmypdf."""

    def test_ocrmypdf_not_found_raises_runtime_error(self):
        """subprocess.which gibt None → RuntimeError mit Install-Hinweis."""
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="ocrmypdf nicht gefunden"):
                run_ocrmypdf("input.pdf", "output.pdf")

    def test_ocrmypdf_success(self):
        """Erfolgreicher Aufruf — kein Fehler."""
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("shutil.which", return_value="/usr/local/bin/ocrmypdf"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                run_ocrmypdf("input.pdf", "output.pdf")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "ocrmypdf" in call_args[0]
        assert "input.pdf" in call_args
        assert "output.pdf" in call_args

    def test_ocrmypdf_failure_raises_runtime_error(self):
        """Prozess endet mit Exit-Code != 0 → RuntimeError."""
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"OCR failed"

        with patch("shutil.which", return_value="/usr/local/bin/ocrmypdf"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(RuntimeError, match="ocrmypdf"):
                    run_ocrmypdf("input.pdf", "output.pdf")


# ---------------------------------------------------------------------------
# Vault-Setter
# ---------------------------------------------------------------------------

class TestVaultOcrSetters:
    """Tests fuer set_ocr_done und update_pdf_path in Vault."""

    @pytest.fixture
    def tmp_db(self, tmp_path):
        db_file = str(tmp_path / "vault.db")
        from mcp.academic_vault.db import VaultDB
        db = VaultDB(db_file)
        db.init_schema()
        db.add_paper(
            paper_id="test-paper-ocr",
            csl_json='{"type":"book","title":"Scan Test"}',
            pdf_path="/tmp/scan.pdf",
        )
        return db_file

    def test_set_ocr_done(self, tmp_db):
        """set_ocr_done setzt ocr_done=1 im Vault."""
        from mcp.academic_vault.server import set_ocr_done, get_paper

        set_ocr_done(tmp_db, "test-paper-ocr")
        paper = get_paper(tmp_db, "test-paper-ocr")

        assert paper is not None
        assert paper["ocr_done"] == 1

    def test_update_pdf_path(self, tmp_db):
        """update_pdf_path aktualisiert pdf_path im Vault."""
        from mcp.academic_vault.server import update_pdf_path, get_paper

        update_pdf_path(tmp_db, "test-paper-ocr", "/tmp/scan_ocr.pdf")
        paper = get_paper(tmp_db, "test-paper-ocr")

        assert paper is not None
        assert paper["pdf_path"] == "/tmp/scan_ocr.pdf"
