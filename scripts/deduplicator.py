#!/usr/bin/env python3
"""Two-level paper deduplication."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from difflib import SequenceMatcher
from typing import Any


def normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI string."""
    if not doi:
        return None
    value = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if value.startswith(prefix):
            value = value[len(prefix) :]
    return value or None


def non_none_field_count(paper: dict[str, Any]) -> int:
    """Count non-empty fields for merge selection."""
    count = 0
    for _, value in paper.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, list) and not value:
            continue
        count += 1
    return count


def similarity(a: str, b: str) -> float:
    """Compute title similarity ratio."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def merge_group(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge duplicate papers by best representative and field strategy."""
    best = sorted(
        group,
        key=lambda p: (non_none_field_count(p), int(p.get("citations") or 0)),
        reverse=True,
    )[0]
    merged = dict(best)
    merged_authors: list[str] = []
    for paper in group:
        for author in paper.get("authors") or []:
            if author not in merged_authors:
                merged_authors.append(author)
    merged["authors"] = merged_authors
    merged["citations"] = max(int(p.get("citations") or 0) for p in group)
    return merged


def group_by_title_similarity(papers: list[dict[str, Any]], threshold: float = 0.85) -> list[list[dict[str, Any]]]:
    """Greedy grouping by fuzzy title similarity."""
    groups: list[list[dict[str, Any]]] = []
    for paper in papers:
        title = (paper.get("title") or "").strip()
        if not title:
            groups.append([paper])
            continue
        placed = False
        for group in groups:
            representative_title = (group[0].get("title") or "").strip()
            if representative_title and similarity(title, representative_title) >= threshold:
                group.append(paper)
                placed = True
                break
        if not placed:
            groups.append([paper])
    return groups


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Deduplicate paper list")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        with open(args.papers, "r", encoding="utf-8") as fh:
            papers = json.load(fh)
    except Exception:
        logging.exception("Failed to load papers")
        return 1

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

    deduped: list[dict[str, Any]] = [merge_group(group) for group in doi_groups.values()]
    for group in group_by_title_similarity(no_doi, threshold=0.85):
        deduped.append(merge_group(group))

    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(deduped, fh, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("Failed to write deduplicated output")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
