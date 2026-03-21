"""Tests for excel.py — Excel generation."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from excel import generate_excel


SAMPLE_PAPERS = [
    {
        "title": "DevOps Governance Framework",
        "authors": ["Alice Smith", "Bob Jones"],
        "year": 2024,
        "venue": "IEEE Transactions on Software Engineering",
        "doi": "10.1109/TSE.2024.001",
        "citations": 42,
        "source_module": "crossref",
        "oa_url": "https://example.com/paper.pdf",
        "scores": {"total": 0.85, "relevance": 0.90, "recency": 0.95, "quality": 0.70, "authority": 1.0, "accessibility": 1.0},
        "cluster": "Kernliteratur",
    },
    {
        "title": "A Systematic Review of CI/CD Practices",
        "authors": ["Carol White"],
        "year": 2022,
        "venue": "ACM Computing Surveys",
        "doi": "10.1145/12345",
        "citations": 15,
        "source_module": "semantic_scholar",
        "scores": {"total": 0.72, "relevance": 0.60, "recency": 0.80, "quality": 0.50, "authority": 1.0, "accessibility": 0.8},
        "cluster": "Methodenliteratur",
    },
    {
        "title": "Cloud Computing Fundamentals",
        "authors": ["Dave Brown"],
        "year": 2019,
        "venue": "Springer",
        "doi": "10.1007/test",
        "citations": 100,
        "source_module": "openalex",
        "scores": {"total": 0.45, "relevance": 0.30, "recency": 0.40, "quality": 0.80, "authority": 0.7, "accessibility": 0.6},
        "cluster": "Hintergrundliteratur",
    },
]


def test_generate_excel_basic():
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        output = f.name
    try:
        result = generate_excel(SAMPLE_PAPERS, output)
        assert result == output
        assert os.path.exists(output)
        assert os.path.getsize(output) > 1000  # Should be a real Excel file
    finally:
        os.unlink(output)


def test_generate_excel_with_context():
    context = {
        "chapters": [
            {"name": "2.1 DevOps Grundlagen", "keywords": ["DevOps", "CI/CD"]},
            {"name": "2.2 Cloud Computing", "keywords": ["Cloud"]},
        ]
    }
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        output = f.name
    try:
        result = generate_excel(SAMPLE_PAPERS, output, context)
        assert os.path.exists(result)
    finally:
        os.unlink(output)


def test_generate_excel_empty():
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        output = f.name
    try:
        generate_excel([], output)
        assert os.path.exists(output)
    finally:
        os.unlink(output)


def test_generate_excel_has_four_sheets():
    import openpyxl
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        output = f.name
    try:
        generate_excel(SAMPLE_PAPERS, output)
        wb = openpyxl.load_workbook(output)
        sheet_names = wb.sheetnames
        assert "Literaturübersicht" in sheet_names
        assert "Cluster-Analyse" in sheet_names
        assert "Kapitel-Zuordnung" in sheet_names
        assert "Datenblatt" in sheet_names
        assert len(sheet_names) == 4
        wb.close()
    finally:
        os.unlink(output)
