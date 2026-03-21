"""Tests for search.py — module registry and utilities."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from search import MODULES
from text_utils import normalize_paper, Paper


def test_all_modules_registered():
    expected = {"crossref", "openalex", "semantic_scholar", "base", "econbiz", "econstor", "arxiv"}
    assert set(MODULES.keys()) == expected


def test_all_modules_callable():
    for name, fn in MODULES.items():
        assert callable(fn), f"Module {name} is not callable"


def test_normalize_paper_basic():
    data = {
        "doi": "10.1109/TEST",
        "title": "Test Paper",
        "authors": ["Alice", "Bob"],
        "year": 2024,
        "abstract": "An abstract.",
        "venue": "IEEE",
        "citations": 42,
        "url": "https://example.com",
    }
    result = normalize_paper(data, "crossref")
    assert result["doi"] == "10.1109/TEST"
    assert result["source_module"] == "crossref"
    assert result["citations"] == 42
    assert result["authors"] == ["Alice", "Bob"]


def test_normalize_paper_missing_fields():
    result = normalize_paper({}, "test")
    assert result["doi"] is None
    assert result["title"] is None
    assert result["authors"] == []
    assert result["citations"] == 0
    assert result["source_module"] == "test"


def test_paper_dataclass():
    p = Paper(doi="10.1109/X", title="Test", year=2024, source_module="crossref")
    d = p.to_dict()
    assert d["doi"] == "10.1109/X"
    assert d["source_module"] == "crossref"


def test_paper_from_dict():
    data = {"doi": "10.1109/X", "title": "Test", "year": 2024, "extra_field": "ignored"}
    p = Paper.from_dict(data)
    assert p.doi == "10.1109/X"
    assert p.year == 2024
