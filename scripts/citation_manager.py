#!/usr/bin/env python3
"""Manage citations and annotations."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

import httpx

BASE_DIR = os.path.expanduser("~/.academic-research")
CITATIONS_BIB = os.path.join(BASE_DIR, "citations.bib")
ANNOTATIONS_JSON = os.path.join(BASE_DIR, "annotations.json")
TIMEOUT = 30.0


def ensure_storage() -> None:
    """Ensure storage files exist."""
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(CITATIONS_BIB):
        open(CITATIONS_BIB, "a", encoding="utf-8").close()
    if not os.path.exists(ANNOTATIONS_JSON):
        with open(ANNOTATIONS_JSON, "w", encoding="utf-8") as fh:
            json.dump({}, fh)


def normalize_doi(doi: str) -> str:
    """Normalize DOI to local paper id."""
    return doi.strip().lower().replace("/", "_")


def load_annotations() -> dict[str, Any]:
    """Load annotations JSON."""
    with open(ANNOTATIONS_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_annotations(data: dict[str, Any]) -> None:
    """Save annotations JSON."""
    with open(ANNOTATIONS_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def parse_bibtex_entries(content: str) -> list[dict[str, str]]:
    """Parse BibTeX entries of any type (@article, @inproceedings, @book, etc.)."""
    entries: list[dict[str, str]] = []
    for match in re.finditer(r"@(\w+)\s*\{", content):
        entry_type = match.group(1).lower()
        start = match.end()
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            if content[pos] == "{":
                depth += 1
            elif content[pos] == "}":
                depth -= 1
            pos += 1
        block = content[start:pos - 1]
        entry: dict[str, str] = {"type": entry_type}
        key_match = re.search(r"\s*([^,]+),", block)
        if key_match:
            entry["id"] = key_match.group(1).strip()
        for field in ["author", "title", "year", "journal", "booktitle", "doi", "url", "abstract", "publisher"]:
            field_match = re.search(rf"{field}\s*=\s*\{{(.*?)\}}", block, flags=re.IGNORECASE | re.DOTALL)
            if field_match:
                entry[field] = field_match.group(1).strip()
        if "journal" not in entry and "booktitle" in entry:
            entry["journal"] = entry["booktitle"]
        entries.append(entry)
    return entries


def read_bib_entries() -> list[dict[str, str]]:
    """Read all citation entries from BibTeX file."""
    with open(CITATIONS_BIB, "r", encoding="utf-8") as fh:
        return parse_bibtex_entries(fh.read())


def append_bib_entry(entry: str) -> None:
    """Append BibTeX entry to storage."""
    with open(CITATIONS_BIB, "a", encoding="utf-8") as fh:
        if os.path.getsize(CITATIONS_BIB) > 0:
            fh.write("\n")
        fh.write(entry + "\n")


def fetch_crossref(doi: str) -> dict[str, Any]:
    """Fetch citation metadata from CrossRef."""
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(f"https://api.crossref.org/works/{doi}")
        resp.raise_for_status()
        message = resp.json().get("message", {})
    authors = []
    for a in message.get("author", []):
        full = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if full:
            authors.append(full)
    year = None
    date_parts = message.get("published-print", {}).get("date-parts") or message.get("published-online", {}).get("date-parts")
    if date_parts and date_parts[0]:
        year = date_parts[0][0]
    return {
        "doi": message.get("DOI") or doi,
        "title": (message.get("title") or ["Untitled"])[0],
        "authors": authors,
        "year": year,
        "venue": (message.get("container-title") or [""])[0],
        "url": message.get("URL") or f"https://doi.org/{doi}",
        "abstract": message.get("abstract") or "",
    }


def to_bibtex(metadata: dict[str, Any]) -> str:
    """Convert fetched metadata into BibTeX article format."""
    paper_id = normalize_doi(metadata["doi"])
    authors = " and ".join(metadata.get("authors") or [])
    return "\n".join(
        [
            f"@article{{{paper_id},",
            f"  author = {{{authors}}},",
            f"  title = {{{metadata.get('title', '')}}},",
            f"  year = {{{metadata.get('year') or ''}}},",
            f"  journal = {{{metadata.get('venue') or ''}}},",
            f"  doi = {{{metadata.get('doi') or ''}}},",
            f"  url = {{{metadata.get('url') or ''}}},",
            f"  abstract = {{{metadata.get('abstract') or ''}}}",
            "}",
        ]
    )


def action_list(tag: str | None, status: str | None) -> int:
    """List papers filtered by tag and/or status."""
    entries = read_bib_entries()
    annotations = load_annotations()
    for entry in entries:
        doi = entry.get("doi", "")
        paper_id = normalize_doi(doi) if doi else entry.get("id", "")
        ann = annotations.get(paper_id, {"tags": [], "status": "unread"})
        if tag and tag not in ann.get("tags", []):
            continue
        if status and ann.get("status") != status:
            continue
        print(f"{entry.get('title', 'Untitled')} [{paper_id}] status={ann.get('status', 'unread')} tags={ann.get('tags', [])}")
    return 0


def action_add(doi: str) -> int:
    """Add a citation by DOI."""
    try:
        metadata = fetch_crossref(doi)
        append_bib_entry(to_bibtex(metadata))
        annotations = load_annotations()
        paper_id = normalize_doi(metadata["doi"])
        annotations.setdefault(paper_id, {"tags": [], "notes": [], "status": "unread"})
        save_annotations(annotations)
    except Exception:
        logging.exception("Failed to add citation")
        return 1
    return 0


def action_tag(paper_id: str, tag: str) -> int:
    """Attach tag to a paper."""
    try:
        annotations = load_annotations()
        entry = annotations.setdefault(paper_id, {"tags": [], "notes": [], "status": "unread"})
        if tag not in entry["tags"]:
            entry["tags"].append(tag)
        save_annotations(annotations)
    except Exception:
        logging.exception("Failed to tag paper")
        return 1
    return 0


def action_note(paper_id: str, note: str) -> int:
    """Append note to a paper."""
    try:
        annotations = load_annotations()
        entry = annotations.setdefault(paper_id, {"tags": [], "notes": [], "status": "unread"})
        entry["notes"].append(note)
        save_annotations(annotations)
    except Exception:
        logging.exception("Failed to add note")
        return 1
    return 0


def action_export(output: str) -> int:
    """Export BibTeX entries to output file."""
    try:
        with open(CITATIONS_BIB, "r", encoding="utf-8") as src, open(output, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    except Exception:
        logging.exception("Failed to export BibTeX")
        return 1
    return 0


def action_merge(session_dir: str) -> int:
    """Merge session papers into global citations.bib."""
    papers_path = os.path.join(session_dir, "papers.json")
    if not os.path.exists(papers_path):
        logging.warning("No papers.json in session dir: %s", session_dir)
        return 0
    try:
        with open(papers_path, "r", encoding="utf-8") as fh:
            papers = json.load(fh)
    except Exception:
        logging.exception("Failed to load session papers")
        return 1

    existing = read_bib_entries()
    existing_dois = {e.get("doi", "").lower() for e in existing if e.get("doi")}
    added = 0
    annotations = load_annotations()
    for paper in papers:
        doi = paper.get("doi")
        if doi and doi.lower() in existing_dois:
            continue
        entry_bib = to_bibtex(paper)
        append_bib_entry(entry_bib)
        paper_id = normalize_doi(doi) if doi else ""
        if paper_id and paper_id not in annotations:
            annotations[paper_id] = {"tags": [], "notes": [], "status": "unread"}
        added += 1
    save_annotations(annotations)
    logging.info("Merged %d new papers into global citations", added)
    return 0


def action_search(query: str) -> int:
    """Search entries by keyword over title/abstract/authors."""
    q = query.lower()
    entries = read_bib_entries()
    for entry in entries:
        text = " ".join([entry.get("title", ""), entry.get("abstract", ""), entry.get("author", "")]).lower()
        if q in text:
            print(f"{entry.get('title', 'Untitled')} ({entry.get('doi', '')})")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Citation manager")
    parser.add_argument("--action", required=True, choices=["list", "add", "tag", "note", "export", "search", "merge"])
    parser.add_argument("--tag")
    parser.add_argument("--status")
    parser.add_argument("--doi")
    parser.add_argument("--paper-id")
    parser.add_argument("--note")
    parser.add_argument("--format")
    parser.add_argument("--output")
    parser.add_argument("--query")
    parser.add_argument("--session-dir")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    ensure_storage()
    args = parse_args()

    if args.action == "list":
        return action_list(args.tag, args.status)
    if args.action == "add":
        if not args.doi:
            logging.error("--doi is required for add")
            return 1
        return action_add(args.doi)
    if args.action == "tag":
        if not args.paper_id or not args.tag:
            logging.error("--paper-id and --tag are required for tag")
            return 1
        return action_tag(args.paper_id, args.tag)
    if args.action == "note":
        if not args.paper_id or args.note is None:
            logging.error("--paper-id and --note are required for note")
            return 1
        return action_note(args.paper_id, args.note)
    if args.action == "export":
        if (args.format or "").lower() != "bibtex" or not args.output:
            logging.error("export requires --format bibtex --output file")
            return 1
        return action_export(args.output)
    if args.action == "search":
        if not args.query:
            logging.error("--query is required for search")
            return 1
        return action_search(args.query)
    if args.action == "merge":
        if not args.session_dir:
            logging.error("--session-dir is required for merge")
            return 1
        return action_merge(args.session_dir)

    logging.error("Unsupported action")
    return 1


if __name__ == "__main__":
    sys.exit(main())
