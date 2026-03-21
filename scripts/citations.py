#!/usr/bin/env python3
"""Citation management, formatting, and export — v4 rewrite.

Merges v3 citation_manager.py + export.py into a unified module.

Supports: APA7, IEEE, Harvard, Chicago, MLA citation formatting.
Actions: format, export, merge, list, add, tag, note, search

Usage:
  python citations.py --action export --session-dir SESSION --format bibtex,markdown,json
  python citations.py --action merge --session-dir SESSION
  python citations.py --action format --papers papers.json --style apa7
  python citations.py --action list [--tag important] [--status unread]
  python citations.py --action add --doi 10.1109/TEST
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
from typing import Any

import httpx

from text_utils import normalize_doi, load_json, save_json

BASE_DIR = os.path.expanduser("~/.academic-research")
CITATIONS_BIB = os.path.join(BASE_DIR, "citations.bib")
ANNOTATIONS_JSON = os.path.join(BASE_DIR, "annotations.json")
TIMEOUT = 30.0

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def ensure_storage() -> None:
    """Ensure citation storage files exist."""
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(CITATIONS_BIB):
        open(CITATIONS_BIB, "a", encoding="utf-8").close()
    if not os.path.exists(ANNOTATIONS_JSON):
        save_json({}, ANNOTATIONS_JSON)


def load_annotations() -> dict[str, Any]:
    return load_json(ANNOTATIONS_JSON)


def save_annotations(data: dict[str, Any]) -> None:
    save_json(data, ANNOTATIONS_JSON)


# ---------------------------------------------------------------------------
# BibTeX parsing
# ---------------------------------------------------------------------------

def parse_bibtex_entries(content: str) -> list[dict[str, str]]:
    """Parse BibTeX entries of any type."""
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
        block = content[start : pos - 1]
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
    with open(CITATIONS_BIB, "r", encoding="utf-8") as fh:
        return parse_bibtex_entries(fh.read())


def append_bib_entry(entry_text: str) -> None:
    with open(CITATIONS_BIB, "a", encoding="utf-8") as fh:
        if os.path.getsize(CITATIONS_BIB) > 0:
            fh.write("\n")
        fh.write(entry_text + "\n")


# ---------------------------------------------------------------------------
# Citation formatting (multi-style)
# ---------------------------------------------------------------------------

def _bibtex_escape(text: str | None) -> str:
    if not text:
        return ""
    for ch in ("\\", "{", "}", "&", "%", "#", "_", "~", "^", "$"):
        text = text.replace(ch, f"\\{ch}")
    return text


def _bibtex_key(paper: dict[str, Any]) -> str:
    authors = paper.get("authors") or []
    first = authors[0] if authors else "Unknown"
    last_name = re.sub(r"[^A-Za-z0-9]", "", (first.split()[-1] if first.split() else "Unknown"))
    year = str(paper.get("year") or "n.d.")
    return f"{last_name}{year}"


def format_bibtex(paper: dict[str, Any], key: str | None = None) -> str:
    """Format paper as BibTeX entry."""
    if key is None:
        key = _bibtex_key(paper)
    authors = " and ".join(paper.get("authors") or [])
    return "\n".join([
        f"@article{{{key},",
        f"  author = {{{_bibtex_escape(authors)}}},",
        f"  title = {{{_bibtex_escape(paper.get('title'))}}},",
        f"  year = {{{paper.get('year') or ''}}},",
        f"  journal = {{{_bibtex_escape(paper.get('venue'))}}},",
        f"  doi = {{{paper.get('doi') or ''}}},",
        f"  url = {{{paper.get('url') or ''}}},",
        f"  abstract = {{{_bibtex_escape(paper.get('abstract'))}}}",
        "}",
    ])


def format_apa7(paper: dict[str, Any]) -> str:
    """Format citation in APA 7th edition style."""
    authors = paper.get("authors") or []
    if len(authors) == 0:
        author_str = "Unknown"
    elif len(authors) == 1:
        parts = authors[0].split()
        author_str = f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}." if len(parts) > 1 else authors[0]
    elif len(authors) <= 20:
        formatted = []
        for i, a in enumerate(authors):
            parts = a.split()
            if len(parts) > 1:
                formatted.append(f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}.")
            else:
                formatted.append(a)
        if len(formatted) > 1:
            author_str = ", ".join(formatted[:-1]) + ", & " + formatted[-1]
        else:
            author_str = formatted[0]
    else:
        formatted = []
        for a in authors[:19]:
            parts = a.split()
            formatted.append(f"{parts[-1]}, {parts[0][0]}." if len(parts) > 1 else a)
        author_str = ", ".join(formatted) + f", ... {authors[-1].split()[-1]}"

    year = paper.get("year") or "n.d."
    title = paper.get("title") or "Untitled"
    venue = paper.get("venue") or ""
    doi = paper.get("doi") or ""

    citation = f"{author_str} ({year}). {title}."
    if venue:
        citation += f" *{venue}*."
    if doi:
        citation += f" https://doi.org/{doi}"
    return citation


def format_ieee(paper: dict[str, Any]) -> str:
    """Format citation in IEEE style."""
    authors = paper.get("authors") or ["Unknown"]
    if len(authors) <= 3:
        author_str = ", ".join(authors)
    else:
        author_str = f"{authors[0]} et al."
    title = paper.get("title") or "Untitled"
    venue = paper.get("venue") or ""
    year = paper.get("year") or "n.d."
    citation = f'{author_str}, "{title},"'
    if venue:
        citation += f" *{venue}*,"
    citation += f" {year}."
    if doi := paper.get("doi"):
        citation += f" doi: {doi}"
    return citation


def format_harvard(paper: dict[str, Any]) -> str:
    """Format citation in Harvard style."""
    authors = paper.get("authors") or ["Unknown"]
    if len(authors) <= 3:
        author_parts = []
        for a in authors:
            parts = a.split()
            author_parts.append(f"{parts[-1]}, {parts[0][0]}." if len(parts) > 1 else a)
        author_str = ", ".join(author_parts[:-1]) + " and " + author_parts[-1] if len(author_parts) > 1 else author_parts[0]
    else:
        parts = authors[0].split()
        author_str = f"{parts[-1]}, {parts[0][0]}. et al." if len(parts) > 1 else f"{authors[0]} et al."

    year = paper.get("year") or "n.d."
    title = paper.get("title") or "Untitled"
    venue = paper.get("venue") or ""
    citation = f"{author_str} ({year}) '{title}'"
    if venue:
        citation += f", *{venue}*"
    citation += "."
    return citation


def format_chicago(paper: dict[str, Any]) -> str:
    """Format citation in Chicago style."""
    authors = paper.get("authors") or ["Unknown"]
    if len(authors) == 1:
        parts = authors[0].split()
        author_str = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else authors[0]
    elif len(authors) <= 3:
        formatted = []
        for i, a in enumerate(authors):
            parts = a.split()
            if i == 0:
                formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else a)
            else:
                formatted.append(a)
        author_str = ", ".join(formatted[:-1]) + ", and " + formatted[-1]
    else:
        parts = authors[0].split()
        author_str = f"{parts[-1]}, {' '.join(parts[:-1])}, et al." if len(parts) > 1 else f"{authors[0]} et al."

    title = paper.get("title") or "Untitled"
    venue = paper.get("venue") or ""
    year = paper.get("year") or "n.d."
    citation = f'{author_str}. "{title}."'
    if venue:
        citation += f" *{venue}*"
    citation += f" ({year})."
    return citation


def format_citation(paper: dict[str, Any], style: str = "apa7") -> str:
    """Format a single citation in the given style."""
    formatters = {
        "apa7": format_apa7,
        "ieee": format_ieee,
        "harvard": format_harvard,
        "chicago": format_chicago,
        "bibtex": format_bibtex,
    }
    fn = formatters.get(style.lower())
    if fn is None:
        raise ValueError(f"Unknown style: {style}. Supported: {', '.join(formatters)}")
    return fn(paper)


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def export_json(session_dir: str, papers: list, quotes: Any) -> None:
    save_json({"papers": papers, "quotes": quotes or []}, os.path.join(session_dir, "export.json"))


def export_bibtex(session_dir: str, papers: list) -> None:
    used_keys: dict[str, int] = {}
    entries: list[str] = []
    for paper in papers:
        base_key = _bibtex_key(paper)
        count = used_keys.get(base_key, 0)
        used_keys[base_key] = count + 1
        key = base_key if count == 0 else f"{base_key}{chr(ord('a') + count - 1)}"
        entries.append(format_bibtex(paper, key))
    content = "\n\n".join(entries)
    with open(os.path.join(session_dir, "export.bib"), "w", encoding="utf-8") as fh:
        fh.write(content + ("\n" if content else ""))


def export_markdown(session_dir: str, papers: list, quotes: Any) -> None:
    meta = load_json(os.path.join(session_dir, "metadata.json")) if os.path.exists(os.path.join(session_dir, "metadata.json")) else {}
    query = meta.get("query", "N/A") if isinstance(meta, dict) else "N/A"
    lines = [
        "# Research Session Export",
        "",
        f"- Date: {dt.datetime.now().isoformat()}",
        f"- Query: {query}",
        f"- Total papers: {len(papers)}",
        "",
    ]
    for paper in papers:
        lines.extend([
            f"## {paper.get('title') or 'Untitled'}",
            f"**Authors:** {', '.join(paper.get('authors') or [])}",
            f"**Year:** {paper.get('year')}  |  **DOI:** {paper.get('doi')}",
            f"**Score:** {(paper.get('scores') or {}).get('total', 'N/A')}  |  **Cluster:** {paper.get('cluster', 'N/A')}",
            "",
        ])
    with open(os.path.join(session_dir, "export.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def export_manual_acquisition(session_dir: str, papers: list, pdf_status: dict) -> int:
    """Write manual_acquisition.md for failed PDF downloads. Returns count."""
    failed = [p for p in papers if not pdf_status.get(normalize_doi(p.get("doi")) or p.get("title", ""), {}).get("success")]
    if not failed:
        return 0
    failed.sort(key=lambda p: (p.get("scores") or {}).get("total", 0), reverse=True)
    lines = [
        "# Manuelle Beschaffung",
        "",
        f"> {len(failed)} von {len(papers)} Papers ohne PDF.",
        "",
        "| # | Score | Titel | Jahr | DOI |",
        "|---|-------|-------|------|-----|",
    ]
    for i, p in enumerate(failed, 1):
        s = (p.get("scores") or {}).get("total", 0)
        lines.append(f"| {i} | {s:.2f} | {p.get('title', 'Untitled')} | {p.get('year', '')} | {p.get('doi', '')} |")
    with open(os.path.join(session_dir, "manual_acquisition.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(failed)


# ---------------------------------------------------------------------------
# CrossRef fetch (for add action)
# ---------------------------------------------------------------------------

def fetch_crossref(doi: str) -> dict[str, Any]:
    """Fetch metadata from CrossRef."""
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(f"https://api.crossref.org/works/{doi}")
        resp.raise_for_status()
        msg = resp.json().get("message", {})
    authors = []
    for a in msg.get("author", []):
        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if name:
            authors.append(name)
    year = None
    dp = msg.get("published-print", {}).get("date-parts") or msg.get("published-online", {}).get("date-parts")
    if dp and dp[0]:
        year = dp[0][0]
    return {
        "doi": msg.get("DOI") or doi,
        "title": (msg.get("title") or ["Untitled"])[0],
        "authors": authors,
        "year": year,
        "venue": (msg.get("container-title") or [""])[0],
        "url": msg.get("URL") or f"https://doi.org/{doi}",
    }


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_list(tag: str | None, status: str | None) -> int:
    entries = read_bib_entries()
    annotations = load_annotations()
    for entry in entries:
        doi = entry.get("doi", "")
        pid = normalize_doi(doi) if doi else entry.get("id", "")
        ann = annotations.get(pid or "", {"tags": [], "status": "unread"})
        if tag and tag not in ann.get("tags", []):
            continue
        if status and ann.get("status") != status:
            continue
        print(f"{entry.get('title', 'Untitled')} [{pid}] status={ann.get('status', 'unread')} tags={ann.get('tags', [])}")
    return 0


def action_add(doi: str) -> int:
    try:
        metadata = fetch_crossref(doi)
        append_bib_entry(format_bibtex(metadata))
        annotations = load_annotations()
        pid = normalize_doi(metadata["doi"]) or ""
        annotations.setdefault(pid, {"tags": [], "notes": [], "status": "unread"})
        save_annotations(annotations)
    except Exception:
        log.exception("Failed to add citation")
        return 1
    return 0


def action_tag(paper_id: str, tag: str) -> int:
    annotations = load_annotations()
    entry = annotations.setdefault(paper_id, {"tags": [], "notes": [], "status": "unread"})
    if tag not in entry["tags"]:
        entry["tags"].append(tag)
    save_annotations(annotations)
    return 0


def action_note(paper_id: str, note: str) -> int:
    annotations = load_annotations()
    entry = annotations.setdefault(paper_id, {"tags": [], "notes": [], "status": "unread"})
    entry["notes"].append(note)
    save_annotations(annotations)
    return 0


def action_search(query: str) -> int:
    q = query.lower()
    for entry in read_bib_entries():
        text = " ".join([entry.get("title", ""), entry.get("abstract", ""), entry.get("author", "")]).lower()
        if q in text:
            print(f"{entry.get('title', 'Untitled')} ({entry.get('doi', '')})")
    return 0


def action_export(session_dir: str, formats: set[str], pdf_status_path: str | None) -> int:
    papers = load_json(os.path.join(session_dir, "papers.json"))
    quotes = load_json(os.path.join(session_dir, "quotes.json")) if os.path.exists(os.path.join(session_dir, "quotes.json")) else None
    if "json" in formats:
        export_json(session_dir, papers, quotes)
    if "bibtex" in formats:
        export_bibtex(session_dir, papers)
    if "markdown" in formats:
        export_markdown(session_dir, papers, quotes)
    if pdf_status_path and os.path.exists(pdf_status_path):
        pdf_status = load_json(pdf_status_path)
        export_manual_acquisition(session_dir, papers, pdf_status)
    return 0


def action_merge(session_dir: str) -> int:
    papers_path = os.path.join(session_dir, "papers.json")
    if not os.path.exists(papers_path):
        log.warning("No papers.json in: %s", session_dir)
        return 0
    papers = load_json(papers_path)
    existing = read_bib_entries()
    existing_dois = {e.get("doi", "").lower() for e in existing if e.get("doi")}
    existing_titles = {e.get("title", "").strip().lower() for e in existing if e.get("title")}
    added = 0
    annotations = load_annotations()
    for paper in papers:
        doi = paper.get("doi")
        title = (paper.get("title") or "").strip()
        if doi and doi.lower() in existing_dois:
            continue
        if not doi and title and title.lower() in existing_titles:
            continue
        append_bib_entry(format_bibtex(paper))
        if doi:
            existing_dois.add(doi.lower())
        if title:
            existing_titles.add(title.lower())
        pid = normalize_doi(doi) if doi else ""
        if pid and pid not in annotations:
            annotations[pid] = {"tags": [], "notes": [], "status": "unread"}
        added += 1
    save_annotations(annotations)
    log.info("Merged %d new papers", added)
    return 0


def action_format(papers_path: str, style: str) -> int:
    papers = load_json(papers_path)
    for paper in papers:
        print(format_citation(paper, style))
        print()
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Citation management and export")
    parser.add_argument("--action", required=True, choices=["format", "export", "merge", "list", "add", "tag", "note", "search"])
    parser.add_argument("--style", default="apa7")
    parser.add_argument("--papers")
    parser.add_argument("--session-dir")
    parser.add_argument("--format")
    parser.add_argument("--pdf-status")
    parser.add_argument("--doi")
    parser.add_argument("--paper-id")
    parser.add_argument("--tag")
    parser.add_argument("--note")
    parser.add_argument("--status")
    parser.add_argument("--query")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    ensure_storage()
    args = parse_args()

    if args.action == "format":
        if not args.papers:
            log.error("--papers required for format")
            return 1
        return action_format(args.papers, args.style)
    if args.action == "export":
        if not args.session_dir or not args.format:
            log.error("--session-dir and --format required for export")
            return 1
        formats = {f.strip().lower() for f in args.format.split(",") if f.strip()}
        return action_export(args.session_dir, formats, args.pdf_status)
    if args.action == "merge":
        if not args.session_dir:
            log.error("--session-dir required for merge")
            return 1
        return action_merge(args.session_dir)
    if args.action == "list":
        return action_list(args.tag, args.status)
    if args.action == "add":
        if not args.doi:
            log.error("--doi required for add")
            return 1
        return action_add(args.doi)
    if args.action == "tag":
        if not args.paper_id or not args.tag:
            log.error("--paper-id and --tag required")
            return 1
        return action_tag(args.paper_id, args.tag)
    if args.action == "note":
        if not args.paper_id or args.note is None:
            log.error("--paper-id and --note required")
            return 1
        return action_note(args.paper_id, args.note)
    if args.action == "search":
        if not args.query:
            log.error("--query required")
            return 1
        return action_search(args.query)
    return 1


if __name__ == "__main__":
    sys.exit(main())
