#!/usr/bin/env python3
"""Two-level paper deduplication — v4 rewrite.

Level 1: Exact DOI match (after normalization).
Level 2: Fuzzy title similarity (SequenceMatcher, threshold 0.85).

Usage:
  python dedup.py --papers api_results.json --output deduped.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from difflib import SequenceMatcher
from typing import Any

from text_utils import normalize_doi, load_json, save_json

log = logging.getLogger(__name__)


def _non_none_count(paper: dict[str, Any]) -> int:
    """Count non-empty fields for merge selection."""
    count = 0
    for value in paper.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and not value:
            continue
        count += 1
    return count


def _title_similarity(a: str, b: str) -> float:
    """Compute title similarity ratio."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def merge_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge duplicate papers: pick best representative, consolidate fields."""
    best = sorted(
        group,
        key=lambda p: (_non_none_count(p), int(p.get("citations") or 0)),
        reverse=True,
    )[0]
    merged = dict(best)

    # Consolidate authors from all duplicates
    all_authors: list[str] = []
    for paper in group:
        for author in paper.get("authors") or []:
            if author not in all_authors:
                all_authors.append(author)
    merged["authors"] = all_authors

    # Take max citations
    merged["citations"] = max(int(p.get("citations") or 0) for p in group)

    # Consolidate OA URLs
    for paper in group:
        if not merged.get("oa_url") and paper.get("oa_url"):
            merged["oa_url"] = paper["oa_url"]
        if not merged.get("open_access_pdf") and paper.get("open_access_pdf"):
            merged["open_access_pdf"] = paper["open_access_pdf"]

    # Track all source modules
    sources = list({p.get("source_module", "") for p in group if p.get("source_module")})
    if len(sources) > 1:
        merged["source_modules"] = sources

    return merged


def _group_by_title(papers: list[dict[str, Any]], threshold: float = 0.85) -> list[list[dict[str, Any]]]:
    """Greedy grouping by fuzzy title similarity."""
    groups: list[list[dict[str, Any]]] = []
    for paper in papers:
        title = (paper.get("title") or "").strip()
        if not title:
            groups.append([paper])
            continue
        placed = False
        for group in groups:
            rep_title = (group[0].get("title") or "").strip()
            if rep_title and _title_similarity(title, rep_title) >= threshold:
                group.append(paper)
                placed = True
                break
        if not placed:
            groups.append([paper])
    return groups


def deduplicate(papers: list[dict[str, Any]], threshold: float = 0.85) -> list[dict[str, Any]]:
    """Deduplicate papers: DOI-first, then title similarity.

    Returns deduplicated list.
    """
    doi_groups: dict[str, list[dict[str, Any]]] = {}
    no_doi: list[dict[str, Any]] = []

    for paper in papers:
        doi = normalize_doi(paper.get("doi"))
        if doi:
            paper_copy = dict(paper)
            paper_copy["doi"] = doi
            doi_groups.setdefault(doi, []).append(paper_copy)
        else:
            no_doi.append(paper)

    deduped = [merge_group(group) for group in doi_groups.values()]
    for group in _group_by_title(no_doi, threshold):
        deduped.append(merge_group(group))

    log.info("Dedup: %d → %d papers", len(papers), len(deduped))
    return deduped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deduplicate paper list")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=float, default=0.85, help="Title similarity threshold")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        papers = load_json(args.papers)
    except Exception:
        log.exception("Failed to load papers")
        return 1

    deduped = deduplicate(papers, args.threshold)

    try:
        save_json(deduped, args.output)
    except Exception:
        log.exception("Failed to write output")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
