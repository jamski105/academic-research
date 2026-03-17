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
    return text.replace("{", "\\{").replace("}", "\\}")


def bibtex_key(paper: dict[str, Any]) -> str:
    """Build BibTeX key from first author + year."""
    authors = paper.get("authors") or []
    first = authors[0] if authors else "Unknown"
    last_name = re.sub(r"[^A-Za-z0-9]", "", (first.split()[-1] if first.split() else "Unknown")) or "Unknown"
    year = str(paper.get("year") or "n.d.")
    return f"{last_name}{year}"


def paper_to_bibtex(paper: dict[str, Any]) -> str:
    """Convert paper dict to BibTeX article entry."""
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
    """Write export.bib."""
    content = "\n\n".join(paper_to_bibtex(p) for p in papers)
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


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Export session outputs")
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--format", required=True, help="Comma-separated: bibtex,markdown,json")
    parser.add_argument("--output", help="Output directory (defaults to session-dir)")
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
    except Exception:
        logging.exception("Export failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
