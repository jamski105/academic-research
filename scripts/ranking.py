#!/usr/bin/env python3
"""Rank papers using a four-dimension score."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import math
import re
import sys
from typing import Any


TOP_AUTHORITY = ["ieee", "acm", "springer", "elsevier", "nature", "science"]
MID_AUTHORITY = ["wiley", "taylor & francis", "oxford university press", "cambridge university press"]


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def fraction_keywords_found(text: str | None, keywords: list[str]) -> float:
    """Compute keyword hit fraction for a text."""
    if not keywords:
        return 0.0
    haystack = (text or "").lower()
    matches = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', haystack))
    return matches / len(keywords)


def score_relevance(paper: dict[str, Any], keywords: list[str]) -> float:
    """Score relevance by title/abstract keyword coverage."""
    title_score = fraction_keywords_found(paper.get("title"), keywords)
    abstract_score = fraction_keywords_found(paper.get("abstract"), keywords)
    return 0.7 * title_score + 0.3 * abstract_score


def score_recency(paper: dict[str, Any], current_year: int) -> float:
    """Score recency with 5-year half-life."""
    year = paper.get("year")
    if year is None:
        return 0.5
    try:
        delta = max(0, current_year - int(year))
        return 2 ** (-(delta / 5.0))
    except Exception:
        logging.exception("Invalid year in paper: %s", paper.get("title"))
        return 0.5


def score_quality(paper: dict[str, Any], current_year: int) -> float:
    """Score quality from citations-per-year using log scaling."""
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
    """Score venue authority with heuristics."""
    venue = (paper.get("venue") or "").strip().lower()
    if not venue:
        return 0.1
    if any(v in venue for v in TOP_AUTHORITY):
        return 1.0
    if any(v in venue for v in MID_AUTHORITY):
        return 0.7
    return 0.4


def apply_portfolio_penalty(scored: list[dict[str, Any]]) -> None:
    """Apply deep-mode venue concentration penalty in-place."""
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
    """Boost papers from underrepresented source modules."""
    source_counts: dict[str, int] = {}
    for paper in scored:
        src = paper.get("source_module", "")
        source_counts[src] = source_counts.get(src, 0) + 1
    if not source_counts:
        return
    avg = sum(source_counts.values()) / len(source_counts)
    for paper in scored:
        src = paper.get("source_module", "")
        count = source_counts.get(src, 0)
        if count < avg * 0.5:
            paper["scores"]["total"] += 0.03


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Rank academic papers")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", choices=["quick", "standard", "deep"], default="standard")
    parser.add_argument("--output")
    parser.add_argument("--w-relevance", type=float, default=0.4)
    parser.add_argument("--w-recency", type=float, default=0.2)
    parser.add_argument("--w-quality", type=float, default=0.2)
    parser.add_argument("--w-authority", type=float, default=0.2)
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        with open(args.papers, "r", encoding="utf-8") as fh:
            papers = json.load(fh)
    except Exception:
        logging.exception("Failed to load papers file")
        return 1

    keywords = tokenize(args.query)
    current_year = dt.datetime.now().year
    scored: list[dict[str, Any]] = []
    for paper in papers:
        relevance = score_relevance(paper, keywords)
        recency = score_recency(paper, current_year)
        quality = score_quality(paper, current_year)
        authority = score_authority(paper)
        total = (args.w_relevance * relevance + args.w_recency * recency
                 + args.w_quality * quality + args.w_authority * authority)
        enriched = dict(paper)
        enriched["scores"] = {
            "total": total,
            "relevance": relevance,
            "recency": recency,
            "quality": quality,
            "authority": authority,
        }
        scored.append(enriched)

    scored.sort(key=lambda p: p["scores"]["total"], reverse=True)
    if args.mode == "deep":
        apply_portfolio_penalty(scored)
        apply_source_diversity_bonus(scored)
        scored.sort(key=lambda p: p["scores"]["total"], reverse=True)

    output_text = json.dumps(scored, ensure_ascii=False, indent=2)
    try:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output_text)
        else:
            sys.stdout.write(output_text + "\n")
    except Exception:
        logging.exception("Failed to write ranked output")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
