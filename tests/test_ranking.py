"""Tests for ranking.py — 5D scoring + cluster assignment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ranking import (
    score_relevance,
    score_recency,
    score_quality,
    score_authority,
    score_accessibility,
    score_phrase_bonus,
    assign_cluster,
    rank_papers,
    DEFAULT_CLUSTERS,
)


# -- Relevance --

def test_relevance_full_match():
    paper = {"title": "DevOps Governance Framework", "abstract": "This paper on DevOps governance..."}
    score = score_relevance(paper, ["devops", "governance"])
    assert score > 0.5


def test_relevance_no_match():
    paper = {"title": "Marine Biology", "abstract": "Coral reef analysis"}
    score = score_relevance(paper, ["devops", "governance"])
    assert score == 0.0


def test_relevance_partial_match():
    paper = {"title": "DevOps in Practice", "abstract": "No governance mentioned"}
    score = score_relevance(paper, ["devops", "governance"])
    assert 0.0 < score < 1.0


# -- Recency --

def test_recency_current_year():
    score = score_recency({"year": 2026}, 2026)
    assert score == 1.0


def test_recency_five_years_old():
    score = score_recency({"year": 2021}, 2026)
    assert abs(score - 0.5) < 0.01


def test_recency_no_year():
    score = score_recency({"year": None}, 2026)
    assert score == 0.5


# -- Quality --

def test_quality_high_citations():
    score = score_quality({"citations": 500, "year": 2021}, 2026)
    assert score > 0.5


def test_quality_no_citations():
    score = score_quality({"citations": 0, "year": 2024}, 2026)
    assert score == 0.0


# -- Authority --

def test_authority_top_venue():
    assert score_authority({"venue": "IEEE Transactions"}) == 1.0


def test_authority_mid_venue():
    assert score_authority({"venue": "Taylor & Francis Journal"}) == 0.7


def test_authority_unknown_venue():
    assert score_authority({"venue": "Unknown Journal"}) == 0.4


def test_authority_no_venue():
    assert score_authority({"venue": ""}) == 0.1


# -- Accessibility --

def test_accessibility_open_access():
    paper = {"oa_url": "https://example.com/paper.pdf", "doi": "10.1234/test"}
    assert score_accessibility(paper) == 1.0


def test_accessibility_arxiv():
    paper = {"source_module": "arxiv", "doi": "10.48550/arxiv.1234"}
    assert score_accessibility(paper) == 1.0


def test_accessibility_doi_known_publisher():
    paper = {"doi": "10.1109/test", "venue": "IEEE Transactions"}
    assert score_accessibility(paper) == 0.8


def test_accessibility_doi_only():
    paper = {"doi": "10.1234/test", "venue": ""}
    assert score_accessibility(paper) == 0.4


def test_accessibility_nothing():
    paper = {}
    assert score_accessibility(paper) == 0.0


# -- Phrase bonus --

def test_phrase_bonus_in_title():
    paper = {"title": "DevOps Governance in Large Organizations"}
    assert score_phrase_bonus(paper, "DevOps Governance") == 0.15


def test_phrase_bonus_in_abstract():
    paper = {"title": "A Framework", "abstract": "This paper on devops governance..."}
    assert score_phrase_bonus(paper, "DevOps Governance") == 0.08


def test_phrase_bonus_none():
    paper = {"title": "Marine Biology", "abstract": "Coral reef"}
    assert score_phrase_bonus(paper, "DevOps Governance") == 0.0


# -- Cluster assignment --

def test_cluster_kernliteratur():
    scores = {"total": 0.85, "relevance": 0.90}
    cluster = assign_cluster({}, scores, DEFAULT_CLUSTERS)
    assert cluster == "Kernliteratur"


def test_cluster_ergaenzung():
    scores = {"total": 0.60, "relevance": 0.55}
    cluster = assign_cluster({}, scores, DEFAULT_CLUSTERS)
    assert cluster == "Ergänzungsliteratur"


def test_cluster_hintergrund():
    scores = {"total": 0.35, "relevance": 0.20}
    cluster = assign_cluster({}, scores, DEFAULT_CLUSTERS)
    assert cluster == "Hintergrundliteratur"


def test_cluster_methodology():
    paper = {"title": "A Systematic Review of DevOps", "abstract": "This systematic review..."}
    scores = {"total": 0.85, "relevance": 0.90}
    cluster = assign_cluster(paper, scores, DEFAULT_CLUSTERS)
    assert cluster == "Methodenliteratur"


# -- Full ranking --

def test_rank_papers_basic():
    papers = [
        {"title": "DevOps Governance", "abstract": "About governance", "year": 2024, "citations": 10, "venue": "IEEE", "doi": "10.1109/test", "oa_url": "https://test.pdf"},
        {"title": "Marine Biology", "abstract": "Coral reef", "year": 2020, "citations": 0, "venue": "", "doi": None},
    ]
    ranked = rank_papers(papers, "DevOps Governance")
    assert len(ranked) == 2
    assert ranked[0]["scores"]["total"] > ranked[1]["scores"]["total"]
    assert "cluster" in ranked[0]
    assert "scores" in ranked[0]
    assert "accessibility" in ranked[0]["scores"]
