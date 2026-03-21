"""Tests for dedup.py — paper deduplication."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from dedup import deduplicate, merge_group
from text_utils import normalize_doi


def test_normalize_doi_basic():
    assert normalize_doi("10.1109/TEST.2023") == "10.1109/test.2023"


def test_normalize_doi_with_url():
    assert normalize_doi("https://doi.org/10.1109/TEST") == "10.1109/test"


def test_normalize_doi_none():
    assert normalize_doi(None) is None


def test_normalize_doi_empty():
    assert normalize_doi("") is None


def test_dedup_by_doi():
    papers = [
        {"doi": "10.1109/TEST", "title": "Paper A", "authors": ["Alice"], "citations": 5},
        {"doi": "https://doi.org/10.1109/test", "title": "Paper A (copy)", "authors": ["Bob"], "citations": 10},
    ]
    result = deduplicate(papers)
    assert len(result) == 1
    assert result[0]["citations"] == 10
    assert "Alice" in result[0]["authors"]
    assert "Bob" in result[0]["authors"]


def test_dedup_by_title_similarity():
    papers = [
        {"doi": None, "title": "DevOps Governance in Large Organizations", "authors": ["Alice"], "citations": 5},
        {"doi": None, "title": "DevOps Governance in Large Organisations", "authors": ["Alice"], "citations": 5},
    ]
    result = deduplicate(papers)
    assert len(result) == 1


def test_dedup_different_papers():
    papers = [
        {"doi": "10.1109/A", "title": "Paper A", "authors": ["Alice"]},
        {"doi": "10.1109/B", "title": "Paper B", "authors": ["Bob"]},
    ]
    result = deduplicate(papers)
    assert len(result) == 2


def test_merge_group_oa_urls():
    group = [
        {"title": "Paper", "authors": [], "oa_url": None, "open_access_pdf": None, "citations": 5},
        {"title": "Paper", "authors": [], "oa_url": "https://test.pdf", "open_access_pdf": None, "citations": 3},
    ]
    merged = merge_group(group)
    assert merged["oa_url"] == "https://test.pdf"
    assert merged["citations"] == 5


def test_dedup_preserves_source_modules():
    papers = [
        {"doi": "10.1109/X", "title": "Same Paper", "source_module": "crossref", "citations": 5},
        {"doi": "10.1109/X", "title": "Same Paper", "source_module": "openalex", "citations": 10},
    ]
    result = deduplicate(papers)
    assert len(result) == 1
    assert "source_modules" in result[0]
    assert set(result[0]["source_modules"]) == {"crossref", "openalex"}
