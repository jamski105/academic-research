"""Tests für skills/notebook-bundle.

TDD: Alle Tests schreiben BEVOR die Implementierung existiert.
"""
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
from PyPDF2 import PdfReader, PdfWriter

# Pfad zu scripts hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "notebook-bundle" / "scripts"))

# conftest.py aus fixtures einbinden (fixture_dir)
pytest_plugins = ["tests.fixtures.notebook_bundle.conftest"]


class TestBundleFivePapers:
    """AC: 5 Paper × 30 Seiten (hier Mock: 3 S. je) → Bundle hat ≥ 15 Seiten."""

    def test_bundle_5_papers_page_count(self, fixture_dir, tmp_path):
        """Bundle aus 5 Paper × 3 Seiten hat mindestens 15 Inhaltsseiten."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle.pdf"
        result = build_bundle(str(selection_path), str(output_path))

        assert result["status"] == "ok"
        reader = PdfReader(str(output_path))
        # 15 Inhaltsseiten + Cover + TOC = mindestens 17
        assert len(reader.pages) >= 15


class TestTOC:
    """TOC-Seite ist erste Seite und enthält alle Paper-Titel."""

    def test_toc_is_first_page(self, fixture_dir, tmp_path):
        """Erste Seite des Bundles enthält Inhaltsverzeichnis-Marker."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle_toc.pdf"
        build_bundle(str(selection_path), str(output_path))

        reader = PdfReader(str(output_path))
        first_page_text = reader.pages[0].extract_text() or ""
        assert (
            "Inhaltsverzeichnis" in first_page_text
            or "Table of Contents" in first_page_text
            or "TOC" in first_page_text
        )


class TestCoverPage:
    """Cover-PDF enthält alle Paper-Einträge (Titel + Autoren + Jahr)."""

    def test_cover_contains_all_papers(self, fixture_dir, tmp_path):
        """Cover-Seite enthält alle 5 Paper-Titel."""
        from cover_pdf import generate_cover

        selection_path = fixture_dir / "selection.json"
        selection = json.loads(Path(str(selection_path)).read_text())
        cover_path = tmp_path / "cover.pdf"
        generate_cover(selection["papers"], str(cover_path))

        reader = PdfReader(str(cover_path))
        full_text = " ".join(
            reader.pages[i].extract_text() or "" for i in range(len(reader.pages))
        )
        for paper in selection["papers"]:
            assert paper["title"] in full_text, f"Titel '{paper['title']}' nicht im Cover"


class TestSplitOver500MB:
    """Bundle >500MB wird in mehrere Dateien aufgeteilt."""

    def test_split_produces_multiple_files(self, fixture_dir, tmp_path):
        """Wenn size_limit_mb=0.001, werden mehrere Bundle-Dateien erzeugt."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle_split.pdf"
        result = build_bundle(
            str(selection_path), str(output_path), size_limit_mb=0.001
        )

        assert result["status"] == "split"
        assert len(result["output_files"]) > 1
        for f in result["output_files"]:
            assert Path(f).exists()


class TestMissingPDFSkipped:
    """Paper mit nicht-existenter PDF wird übersprungen, kein Exception."""

    def test_missing_pdf_skipped(self, tmp_path):
        """Paper mit fehlendem PDF wird übersprungen; restliche Paper im Bundle."""
        from bundle import build_bundle

        # Selection mit 1 existenter + 1 fehlender PDF
        good_pdf = tmp_path / "good.pdf"
        writer = PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=595, height=842)
        buf = io.BytesIO()
        writer.write(buf)
        good_pdf.write_bytes(buf.getvalue())

        selection = {
            "papers": [
                {
                    "id": "good",
                    "title": "Good Paper",
                    "authors": ["A. Good"],
                    "year": 2021,
                    "pdf_path": str(good_pdf),
                },
                {
                    "id": "missing",
                    "title": "Missing Paper",
                    "authors": ["B. Missing"],
                    "year": 2020,
                    "pdf_path": str(tmp_path / "nonexistent.pdf"),
                },
            ]
        }
        sel_path = tmp_path / "selection.json"
        sel_path.write_text(json.dumps(selection))
        output_path = tmp_path / "bundle_missing.pdf"

        result = build_bundle(str(sel_path), str(output_path))

        assert result["status"] in ("ok", "partial")
        assert "missing" in result.get("skipped_ids", []) or result.get("skipped_count", 0) > 0
        assert Path(output_path).exists()


class TestOutputFilenamePattern:
    """Output-Dateiname enthält 'notebook-bundle-' + Timestamp-Pattern."""

    def test_auto_output_filename(self, fixture_dir, tmp_path):
        """Wenn kein output_path angegeben, wird notebook-bundle-<ts>.pdf erzeugt."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        result = build_bundle(str(selection_path), output_dir=str(tmp_path))

        assert result["status"] in ("ok", "split")
        main_file = result["output_files"][0]
        filename = Path(main_file).name
        assert re.match(r"notebook-bundle-\d{8}T\d{6}.*\.pdf", filename), (
            f"Dateiname '{filename}' entspricht nicht dem Pattern notebook-bundle-<ts>.pdf"
        )
