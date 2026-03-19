#!/usr/bin/env python3
"""Export research session data in multiple formats."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
from typing import Any


def load_json(path: str, default: Any = None) -> Any:
    """Load JSON from file or return default."""
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def bibtex_escape(text: str | None) -> str:
    """Escape text for BibTeX output."""
    if not text:
        return ""
    for ch in ("\\", "{", "}", "&", "%", "#", "_", "~", "^", "$"):
        text = text.replace(ch, f"\\{ch}")
    return text


def bibtex_key(paper: dict[str, Any]) -> str:
    """Build BibTeX key from first author + year."""
    authors = paper.get("authors") or []
    first = authors[0] if authors else "Unknown"
    last_name = re.sub(r"[^A-Za-z0-9]", "", (first.split()[-1] if first.split() else "Unknown")) or "Unknown"
    year = str(paper.get("year") or "n.d.")
    return f"{last_name}{year}"


def paper_to_bibtex(paper: dict[str, Any], key: str | None = None) -> str:
    """Convert paper dict to BibTeX article entry."""
    if key is None:
        key = bibtex_key(paper)
    authors = " and ".join(paper.get("authors") or [])
    lines = [
        f"@article{{{key},",
        f"  author = {{{bibtex_escape(authors)}}},",
        f"  title = {{{bibtex_escape(paper.get('title'))}}},",
        f"  year = {{{paper.get('year') or ''}}},",
        f"  journal = {{{bibtex_escape(paper.get('venue'))}}},",
        f"  doi = {{{paper.get('doi') or ''}}},",
        f"  url = {{{paper.get('url') or ''}}},",
        f"  abstract = {{{bibtex_escape(paper.get('abstract'))}}}",
        "}",
    ]
    return "\n".join(lines)


def write_json_export(session_dir: str, papers: list[dict[str, Any]], quotes: Any) -> None:
    """Write export.json with full session payload."""
    payload = {"papers": papers, "quotes": quotes or []}
    with open(os.path.join(session_dir, "export.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def write_bibtex_export(session_dir: str, papers: list[dict[str, Any]]) -> None:
    """Write export.bib with unique keys (append a/b/c on collision)."""
    used_keys: dict[str, int] = {}
    entries: list[str] = []
    for paper in papers:
        base_key = bibtex_key(paper)
        count = used_keys.get(base_key, 0)
        used_keys[base_key] = count + 1
        unique_key = base_key if count == 0 else f"{base_key}{chr(ord('a') + count - 1)}"
        entries.append(paper_to_bibtex(paper, unique_key))
    content = "\n\n".join(entries)
    with open(os.path.join(session_dir, "export.bib"), "w", encoding="utf-8") as fh:
        fh.write(content + ("\n" if content else ""))


def _read_query(session_dir: str) -> str:
    """Read query from session metadata."""
    meta = load_json(os.path.join(session_dir, "metadata.json"), default=None)
    if isinstance(meta, dict) and meta.get("query"):
        return meta["query"]
    query_file = os.path.join(session_dir, "query.txt")
    if os.path.exists(query_file):
        with open(query_file, "r", encoding="utf-8") as fh:
            return fh.read().strip() or "N/A"
    return "N/A"


def write_markdown_export(session_dir: str, papers: list[dict[str, Any]], quotes: Any) -> None:
    """Write export.md summary document."""
    pdf_count = sum(1 for p in papers if p.get("pdf_path"))
    lines = [
        "# Research Session Export",
        "",
        f"- Date: {dt.datetime.now().isoformat()}",
        f"- Query: {_read_query(session_dir)}",
        f"- Total papers: {len(papers)}",
        f"- PDFs downloaded: {pdf_count}",
        "",
    ]
    for paper in papers:
        lines.extend(
            [
                f"## {paper.get('title') or 'Untitled'}",
                f"**Authors:** {', '.join(paper.get('authors') or [])}",
                f"**Year:** {paper.get('year')}",
                f"**DOI:** {paper.get('doi')}",
                f"**Abstract:** {paper.get('abstract')}",
                "",
            ]
        )
    if quotes:
        lines.extend(["# Quotes", ""])
        if isinstance(quotes, list):
            for q in quotes:
                lines.append(f"- {q}")
        elif isinstance(quotes, dict):
            for key, value in quotes.items():
                lines.append(f"- **{key}:** {value}")
        lines.append("")

    with open(os.path.join(session_dir, "export.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_manual_acquisition(session_dir: str, papers: list[dict[str, Any]], pdf_status_path: str) -> int:
    """Write manual_acquisition.md for papers that failed PDF download.

    Returns the number of failed papers written.
    """
    pdf_status: dict[str, Any] = load_json(pdf_status_path, default={})
    if not pdf_status:
        logging.warning("pdf_status.json is empty or missing — skipping manual acquisition export")
        return 0

    failed: list[dict[str, Any]] = []
    for paper in papers:
        key = paper.get("doi") or paper.get("title", "unknown")
        entry = pdf_status.get(key, {})
        if not entry.get("success"):
            failed.append(paper)

    if not failed:
        return 0

    failed.sort(key=lambda p: (p.get("scores") or {}).get("total", 0), reverse=True)

    lines = [
        "# Manuelle Beschaffung — Papers ohne PDF",
        "",
        f"> {len(failed)} von {len(papers)} Papers konnten nicht automatisch heruntergeladen werden.",
        "> Sortiert nach Gesamtscore (höchste Relevanz zuerst).",
        "",
        "| # | Score | Titel | Autoren | Jahr | DOI | Relevanz | Aktualität | Qualität | Autorität |",
        "|---|-------|-------|---------|------|-----|----------|------------|----------|-----------|",
    ]
    for idx, paper in enumerate(failed, 1):
        scores = paper.get("scores") or {}
        authors = ", ".join(paper.get("authors") or [])
        doi = paper.get("doi") or ""
        lines.append(
            f"| {idx} "
            f"| {scores.get('total', 0):.2f} "
            f"| {paper.get('title') or 'Untitled'} "
            f"| {authors} "
            f"| {paper.get('year') or ''} "
            f"| {doi} "
            f"| {scores.get('relevance', 0):.2f} "
            f"| {scores.get('recency', 0):.2f} "
            f"| {scores.get('quality', 0):.2f} "
            f"| {scores.get('authority', 0):.2f} |"
        )

    lines.append("")
    with open(os.path.join(session_dir, "manual_acquisition.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return len(failed)


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Export session outputs")
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--format", required=True, help="Comma-separated: bibtex,markdown,json")
    parser.add_argument("--output", help="Output directory (defaults to session-dir)")
    parser.add_argument("--pdf-status", help="Path to pdf_status.json — generates manual_acquisition.md for failed downloads")
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    papers_path = os.path.join(args.session_dir, "papers.json")
    quotes_path = os.path.join(args.session_dir, "quotes.json")

    try:
        papers = load_json(papers_path, default=[])
        quotes = load_json(quotes_path, default=None)
    except Exception:
        logging.exception("Failed to load session data")
        return 1

    output_dir = args.output or args.session_dir
    os.makedirs(output_dir, exist_ok=True)
    formats = {f.strip().lower() for f in args.format.split(",") if f.strip()}
    try:
        if "json" in formats:
            write_json_export(output_dir, papers, quotes)
        if "bibtex" in formats:
            write_bibtex_export(output_dir, papers)
        if "markdown" in formats:
            write_markdown_export(output_dir, papers, quotes)
        if args.pdf_status:
            count = write_manual_acquisition(output_dir, papers, args.pdf_status)
            if count:
                logging.info("manual_acquisition.md: %d papers without PDF", count)
    except Exception:
        logging.exception("Export failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
