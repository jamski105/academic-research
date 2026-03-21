#!/usr/bin/env python3
"""5D paper ranking with cluster assignment — v4 rewrite.

Dimensions: Relevance (0.35), Recency (0.20), Quality (0.15), Authority (0.15), Accessibility (0.15)
Clusters: Kernliteratur, Ergänzungsliteratur, Hintergrundliteratur, Methodenliteratur

Usage:
  python ranking.py --papers deduped.json --query "DevOps Governance" --output ranked.json
  python ranking.py --papers deduped.json --query "..." --scoring-config config/scoring.yaml
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import math
import re
import sys
from typing import Any

from text_utils import load_json, save_json, tokenize

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default scoring config (overridable via --scoring-config YAML)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "relevance": 0.35,
    "recency": 0.20,
    "quality": 0.15,
    "authority": 0.15,
    "accessibility": 0.15,
}

DEFAULT_CLUSTERS = {
    "kernliteratur": {"min_total": 0.75, "min_relevance": 0.80},
    "ergaenzungsliteratur": {"min_total": 0.50, "min_relevance": 0.50},
    "hintergrundliteratur": {"min_total": 0.30},
    "methodenliteratur": {
        "keywords": [
            "systematic review", "literature review", "meta-analysis",
            "case study", "grounded theory", "qualitative", "quantitative",
            "mixed methods", "research design", "methodology", "research method",
            "empirical study", "survey design", "interview", "content analysis",
            "forschungsmethode", "forschungsdesign", "literaturanalyse",
        ]
    },
}

TOP_AUTHORITY = ["ieee", "acm", "springer", "elsevier", "nature", "science", "wiley"]
MID_AUTHORITY = ["taylor & francis", "oxford university press", "cambridge university press", "sage", "emerald"]


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _fraction_keywords(text: str | None, keywords: list[str]) -> float:
    """Keyword hit fraction for a text."""
    if not keywords:
        return 0.0
    haystack = (text or "").lower()
    matches = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", haystack))
    return matches / len(keywords)


def score_relevance(paper: dict[str, Any], keywords: list[str]) -> float:
    """Score relevance by title/abstract keyword coverage."""
    title_score = _fraction_keywords(paper.get("title"), keywords)
    abstract_score = _fraction_keywords(paper.get("abstract"), keywords)
    return 0.7 * title_score + 0.3 * abstract_score


def score_phrase_bonus(paper: dict[str, Any], query: str) -> float:
    """Bonus for exact query phrase in title or abstract."""
    if not query or len(query) < 4:
        return 0.0
    q = query.lower()
    if q in (paper.get("title") or "").lower():
        return 0.15
    if q in (paper.get("abstract") or "").lower():
        return 0.08
    return 0.0


def score_recency(paper: dict[str, Any], current_year: int) -> float:
    """Exponential decay with 5-year half-life."""
    year = paper.get("year")
    if year is None:
        return 0.5
    try:
        delta = max(0, current_year - int(year))
        return 2 ** (-(delta / 5.0))
    except (ValueError, TypeError):
        return 0.5


def score_quality(paper: dict[str, Any], current_year: int) -> float:
    """Citations-per-year with log scaling."""
    citations = max(0, int(paper.get("citations") or 0))
    year = paper.get("year")
    if year is not None:
        try:
            age = max(1, current_year - int(year))
            cpy = citations / age
        except (ValueError, TypeError):
            cpy = citations
    else:
        cpy = citations
    return min(1.0, math.log(cpy + 1) / math.log(201))


def score_authority(paper: dict[str, Any]) -> float:
    """Venue authority heuristic."""
    venue = (paper.get("venue") or "").strip().lower()
    if not venue:
        return 0.1
    if any(v in venue for v in TOP_AUTHORITY):
        return 1.0
    if any(v in venue for v in MID_AUTHORITY):
        return 0.7
    return 0.4


def score_accessibility(paper: dict[str, Any]) -> float:
    """Score how easily the full text can be obtained.

    1.0 = Open Access PDF available
    0.8 = Institutional access likely (known publisher + DOI)
    0.6 = DOI + known publisher (interlibrary loan possible)
    0.4 = DOI but unknown/paywalled
    0.2 = URL only, no DOI
    0.0 = Metadata only
    """
    has_oa = bool(paper.get("oa_url") or paper.get("open_access_pdf"))
    has_doi = bool(paper.get("doi"))
    has_url = bool(paper.get("url"))
    venue = (paper.get("venue") or "").lower()
    source = (paper.get("source_module") or "").lower()

    # arXiv is always open access
    if source == "arxiv" or "arxiv" in venue:
        return 1.0
    if has_oa:
        return 1.0
    if has_doi:
        # Known publishers with institutional access
        if any(v in venue for v in TOP_AUTHORITY + MID_AUTHORITY):
            return 0.8
        return 0.6 if venue else 0.4
    if has_url:
        return 0.2
    return 0.0


# ---------------------------------------------------------------------------
# Cluster assignment
# ---------------------------------------------------------------------------

def _is_methodology_paper(paper: dict[str, Any], keywords: list[str]) -> bool:
    """Check if paper is about research methodology."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    return any(kw in text for kw in keywords)


def assign_cluster(
    paper: dict[str, Any],
    scores: dict[str, float],
    cluster_config: dict[str, Any],
) -> str:
    """Assign paper to one cluster. Priority: Methoden → Kern → Ergänzung → Hintergrund."""
    # 1. Methodology check (keyword-based, highest priority)
    method_cfg = cluster_config.get("methodenliteratur", {})
    if _is_methodology_paper(paper, method_cfg.get("keywords", [])):
        return "Methodenliteratur"

    total = scores.get("total", 0)
    relevance = scores.get("relevance", 0)

    # 2. Kernliteratur
    kern_cfg = cluster_config.get("kernliteratur", {})
    if total >= kern_cfg.get("min_total", 0.75) and relevance >= kern_cfg.get("min_relevance", 0.80):
        return "Kernliteratur"

    # 3. Ergänzungsliteratur
    erg_cfg = cluster_config.get("ergaenzungsliteratur", {})
    if total >= erg_cfg.get("min_total", 0.50) and relevance >= erg_cfg.get("min_relevance", 0.50):
        return "Ergänzungsliteratur"

    # 4. Hintergrundliteratur (default for everything else with min score)
    bg_cfg = cluster_config.get("hintergrundliteratur", {})
    if total >= bg_cfg.get("min_total", 0.30):
        return "Hintergrundliteratur"

    return "Hintergrundliteratur"


# ---------------------------------------------------------------------------
# Portfolio adjustments (deep mode)
# ---------------------------------------------------------------------------

def apply_portfolio_penalty(scored: list[dict[str, Any]]) -> None:
    """Venue concentration penalty (deep mode)."""
    venue_counts: dict[str, int] = {}
    for paper in scored:
        venue = (paper.get("venue") or "").strip().lower()
        if not venue:
            continue
        count = venue_counts.get(venue, 0)
        if count >= 3:
            paper["scores"]["total"] -= 0.05
        venue_counts[venue] = count + 1


def apply_source_diversity_bonus(scored: list[dict[str, Any]]) -> None:
    """Boost papers from underrepresented source modules (deep mode)."""
    source_counts: dict[str, int] = {}
    for paper in scored:
        src = paper.get("source_module", "")
        source_counts[src] = source_counts.get(src, 0) + 1
    if not source_counts:
        return
    avg = sum(source_counts.values()) / len(source_counts)
    for paper in scored:
        src = paper.get("source_module", "")
        if source_counts.get(src, 0) < avg * 0.5:
            paper["scores"]["total"] += 0.03


# ---------------------------------------------------------------------------
# Main ranking function
# ---------------------------------------------------------------------------

def rank_papers(
    papers: list[dict[str, Any]],
    query: str,
    mode: str = "standard",
    weights: dict[str, float] | None = None,
    cluster_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Rank papers with 5D scoring and cluster assignment.

    Returns scored and sorted list with 'scores' and 'cluster' fields.
    """
    w = weights or DEFAULT_WEIGHTS
    clusters = cluster_config or DEFAULT_CLUSTERS
    keywords = tokenize(query)
    current_year = dt.datetime.now().year

    scored: list[dict[str, Any]] = []
    for paper in papers:
        rel = score_relevance(paper, keywords)
        rec = score_recency(paper, current_year)
        qual = score_quality(paper, current_year)
        auth = score_authority(paper)
        acc = score_accessibility(paper)
        phrase = score_phrase_bonus(paper, query)

        total = min(1.0, (
            w.get("relevance", 0.35) * rel
            + w.get("recency", 0.20) * rec
            + w.get("quality", 0.15) * qual
            + w.get("authority", 0.15) * auth
            + w.get("accessibility", 0.15) * acc
            + phrase
        ))

        scores = {
            "total": round(total, 4),
            "relevance": round(rel, 4),
            "recency": round(rec, 4),
            "quality": round(qual, 4),
            "authority": round(auth, 4),
            "accessibility": round(acc, 4),
        }

        enriched = dict(paper)
        enriched["scores"] = scores
        enriched["cluster"] = assign_cluster(paper, scores, clusters)
        scored.append(enriched)

    scored.sort(key=lambda p: p["scores"]["total"], reverse=True)

    if mode == "deep":
        apply_portfolio_penalty(scored)
        apply_source_diversity_bonus(scored)
        scored.sort(key=lambda p: p["scores"]["total"], reverse=True)

    return scored


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank academic papers (5D)")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", choices=["quick", "standard", "deep"], default="standard")
    parser.add_argument("--output")
    parser.add_argument("--scoring-config", help="YAML with weights and cluster thresholds")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        papers = load_json(args.papers)
    except Exception:
        log.exception("Failed to load papers")
        return 1

    weights = None
    cluster_config = None
    if args.scoring_config:
        try:
            from text_utils import load_yaml
            cfg = load_yaml(args.scoring_config)
            weights = cfg.get("weights", None)
            cluster_config = cfg.get("clusters", None)
        except Exception:
            log.exception("Failed to load scoring config")

    scored = rank_papers(papers, args.query, args.mode, weights, cluster_config)
    log.info("Ranked %d papers", len(scored))

    output_text = json.dumps(scored, ensure_ascii=False, indent=2)
    if args.output:
        save_json(scored, args.output)
    else:
        sys.stdout.write(output_text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
