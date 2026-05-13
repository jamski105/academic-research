#!/usr/bin/env python3
"""PDF resolution, download, text extraction and fulltext indexing — v4 rewrite.

Merges v3 pdf_resolver.py + fulltext_index.py into a single module.

Actions:
  resolve  — Download PDFs via 5-tier fallback strategy
  extract  — Extract text from downloaded PDFs (PyPDF2)
  index    — Build TF-IDF fulltext index
  search   — Search fulltext index

Usage:
  python pdf.py --action resolve --papers papers.json --output-dir pdfs/ --output pdf_status.json
  python pdf.py --action extract --pdf-dir pdfs/ --output pdf_texts.json
  python pdf.py --action search --query "governance" --index-path fulltext_index.json
"""

from __future__ import annotations

import argparse
import collections
import json
import logging
import math
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from text_utils import normalize_doi, safe_filename, load_json, save_json

try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore[assignment,misc]

TIMEOUT = 30.0
PDF_MAGIC = b"%PDF"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PDF validation
# ---------------------------------------------------------------------------

def is_valid_pdf(content: bytes) -> bool:
    """Return True if content starts with PDF magic bytes."""
    return len(content) >= 4 and content[:4] == PDF_MAGIC


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_pdf(client: httpx.Client, pdf_url: str, output_path: str) -> None:
    """Stream-download PDF. Raises ValueError if not valid PDF."""
    try:
        with client.stream("GET", pdf_url, timeout=TIMEOUT) as resp:
            resp.raise_for_status()
            chunks: list[bytes] = []
            for chunk in resp.iter_bytes():
                if not chunk:
                    continue
                if not chunks and not is_valid_pdf(chunk):
                    raise ValueError(f"Not a valid PDF: {pdf_url!r}")
                chunks.append(chunk)
        with open(output_path, "wb") as fh:
            for chunk in chunks:
                fh.write(chunk)
    except Exception:
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise


# ---------------------------------------------------------------------------
# Tier-based PDF resolution
# ---------------------------------------------------------------------------

def tier_unpaywall(client: httpx.Client, doi: str, email: str) -> str | None:
    """Tier 1: Resolve via Unpaywall."""
    resp = client.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email}, timeout=TIMEOUT)
    resp.raise_for_status()
    return (resp.json().get("best_oa_location") or {}).get("url_for_pdf")


def tier_core(client: httpx.Client, doi: str) -> str | None:
    """Tier 2: Resolve via CORE."""
    import time
    for attempt in range(3):
        try:
            resp = client.get("https://api.core.ac.uk/v3/search/works", params={"q": f"doi:{doi}"}, timeout=TIMEOUT)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return results[0].get("downloadUrl") if results else None
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt == 2:
                raise
            time.sleep(2.0 * (2 ** attempt))
    return None


def tier_module_urls(paper: dict[str, Any]) -> str | None:
    """Tier 3: OA URLs from search metadata."""
    for field in ("open_access_pdf", "openAccessPdf"):
        val = paper.get(field)
        if isinstance(val, dict) and val.get("url"):
            return val["url"]
        if isinstance(val, str) and val:
            return val
    oa_url = paper.get("oa_url")
    if isinstance(oa_url, str) and oa_url:
        return oa_url
    return None


def tier_direct_url(paper: dict[str, Any]) -> str | None:
    """Tier 4: Direct PDF URL."""
    url = paper.get("url")
    if isinstance(url, str) and url.lower().endswith(".pdf"):
        return url
    return None


def tier_arxiv_title(client: httpx.Client, title: str) -> str | None:
    """Tier 5: arXiv title search fallback."""
    safe_title = title[:80].replace('"', " ")
    try:
        resp = client.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f"ti:{safe_title}", "max_results": "1"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    return link.get("href")
    except Exception:
        log.exception("arXiv title search failed: %s", title[:40])
    return None


def resolve_pdf_url(
    client: httpx.Client, paper: dict[str, Any], email: str
) -> tuple[str | None, str | None, str | None]:
    """Try all tiers to find a PDF URL. Returns (url, source_tier, error)."""
    doi = normalize_doi(paper.get("doi"))
    last_error = None

    # Tier 1: Unpaywall
    if doi:
        try:
            url = tier_unpaywall(client, doi, email)
            if url:
                return url, "unpaywall", None
        except Exception as exc:
            last_error = str(exc)

    # Tier 2: CORE
    if doi:
        try:
            url = tier_core(client, doi)
            if url:
                return url, "core", last_error
        except Exception as exc:
            last_error = str(exc)

    # Tier 3: Module OA URLs
    url = tier_module_urls(paper)
    if url:
        return url, "module_oa", last_error

    # Tier 4: Direct URL
    url = tier_direct_url(paper)
    if url:
        return url, "direct", last_error

    # Tier 5: arXiv title search
    if title := paper.get("title"):
        try:
            url = tier_arxiv_title(client, title)
            if url:
                return url, "arxiv", last_error
        except Exception as exc:
            last_error = str(exc)

    return None, None, last_error or "No PDF URL found"


def action_resolve(papers_path: str, output_dir: str, output_path: str, email: str) -> int:
    """Resolve and download PDFs for all papers."""
    papers = load_json(papers_path)
    os.makedirs(output_dir, exist_ok=True)
    status: dict[str, dict[str, Any]] = {}

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        for paper in papers:
            doi = normalize_doi(paper.get("doi"))
            key = doi or (paper.get("title") or "unknown")
            url, source, error = resolve_pdf_url(client, paper, email)

            if not url:
                status[key] = {"success": False, "pdf_path": None, "source": None, "error": error}
                continue

            fname = safe_filename(doi or (paper.get("title") or "untitled")[:80])
            pdf_path = os.path.join(output_dir, f"{fname}.pdf")
            try:
                download_pdf(client, url, pdf_path)
                status[key] = {"success": True, "pdf_path": pdf_path, "source": source, "error": None}
            except Exception as exc:
                log.exception("PDF download failed: %s", key)
                status[key] = {"success": False, "pdf_path": None, "source": source, "error": str(exc)}

    save_json(status, output_path)
    success = sum(1 for s in status.values() if s["success"])
    log.info("PDFs resolved: %d/%d successful", success, len(status))
    return 0


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyPDF2."""
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception:
        log.exception("Failed to extract text from %s", pdf_path)
        return ""


def action_extract(pdf_dir: str, output_path: str) -> int:
    """Extract text from all PDFs in directory."""
    texts: dict[str, str] = {}
    if not os.path.isdir(pdf_dir):
        log.error("PDF directory not found: %s", pdf_dir)
        return 1

    for fname in sorted(os.listdir(pdf_dir)):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(pdf_dir, fname)
        text = extract_text_from_pdf(path)
        texts[fname] = text

    save_json(texts, output_path)
    log.info("Extracted text from %d PDFs", len(texts))
    return 0


# ---------------------------------------------------------------------------
# TF-IDF fulltext index
# ---------------------------------------------------------------------------

def _tokenize_for_index(text: str) -> list[str]:
    """Tokenize text for indexing."""
    return [t for t in re.split(r"[^a-z0-9äöüß]+", text.lower()) if len(t) > 2]


def action_index(pdf_texts_path: str, output_path: str) -> int:
    """Build TF-IDF index from extracted texts."""
    texts = load_json(pdf_texts_path)
    doc_count = len(texts)
    if doc_count == 0:
        save_json({"index": {}, "doc_count": 0, "doc_lengths": {}}, output_path)
        return 0

    # Term frequency per document
    tf: dict[str, dict[str, int]] = {}
    doc_lengths: dict[str, int] = {}
    df: dict[str, int] = collections.defaultdict(int)

    for doc_id, text in texts.items():
        tokens = _tokenize_for_index(text)
        doc_lengths[doc_id] = len(tokens)
        term_counts: dict[str, int] = collections.defaultdict(int)
        for token in tokens:
            term_counts[token] += 1
        tf[doc_id] = dict(term_counts)
        for term in term_counts:
            df[term] += 1

    # Build inverted index with TF-IDF scores
    index: dict[str, list[tuple[str, float]]] = {}
    for doc_id, term_counts in tf.items():
        length = max(1, doc_lengths[doc_id])
        for term, count in term_counts.items():
            tf_score = count / length
            idf_score = math.log(doc_count / max(1, df[term]))
            tfidf = tf_score * idf_score
            if tfidf > 0.001:
                index.setdefault(term, []).append((doc_id, round(tfidf, 6)))

    # Sort by score
    for term in index:
        index[term].sort(key=lambda x: x[1], reverse=True)

    save_json({"index": index, "doc_count": doc_count, "doc_lengths": doc_lengths}, output_path)
    log.info("Indexed %d documents, %d terms", doc_count, len(index))
    return 0


def action_search(query: str, index_path: str, limit: int = 10) -> int:
    """Search fulltext index."""
    data = load_json(index_path)
    index = data.get("index", {})
    tokens = _tokenize_for_index(query)

    doc_scores: dict[str, float] = collections.defaultdict(float)
    for token in tokens:
        for doc_id, score in index.get(token, []):
            doc_scores[doc_id] += score

    ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    for doc_id, score in ranked:
        print(f"{score:.4f}  {doc_id}")
    return 0


# ---------------------------------------------------------------------------
# OCR-Detection
# ---------------------------------------------------------------------------

def detect_needs_ocr(
    pdf_path: str,
    sample_pages: int = 5,
    threshold: int = 100,
) -> bool:
    """Prueft ob ein PDF OCR benoetigt.

    Liest bis zu sample_pages zufaellig verteilte Seiten via PyPDF2.
    Gibt True zurueck wenn der Durchschnitt der extrahierten Zeichen
    je Seite < threshold (Standard: 100 Zeichen).
    Bei leerem PDF (0 Seiten) gibt die Funktion True zurueck.
    """
    try:
        reader = PdfReader(pdf_path)
    except Exception:
        log.exception("detect_needs_ocr: konnte %s nicht oeffnen", pdf_path)
        return True  # Im Fehlerfall: OCR vorschlagen

    total_pages = len(reader.pages)
    if total_pages == 0:
        return True

    n = min(sample_pages, total_pages)
    indices = random.sample(range(total_pages), n)

    total_chars = 0
    for i in indices:
        text = reader.pages[i].extract_text() or ""
        total_chars += len(text)

    avg_chars = total_chars / n
    return avg_chars < threshold


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PDF resolution, extraction, and indexing")
    parser.add_argument("--action", required=True, choices=["resolve", "extract", "index", "search"])
    parser.add_argument("--papers", help="Papers JSON (for resolve)")
    parser.add_argument("--output-dir", help="PDF output directory (for resolve)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--pdf-dir", help="PDF directory (for extract)")
    parser.add_argument("--pdf-texts", help="PDF texts JSON (for index)")
    parser.add_argument("--index-path", help="Index file path (for search)")
    parser.add_argument("--query", help="Search query (for search)")
    parser.add_argument("--limit", type=int, default=10, help="Search result limit")
    parser.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL", "academic-research@example.com"))
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    if args.action == "resolve":
        if not args.papers or not args.output_dir or not args.output:
            log.error("resolve requires --papers, --output-dir, --output")
            return 1
        return action_resolve(args.papers, args.output_dir, args.output, args.email)

    if args.action == "extract":
        if not args.pdf_dir or not args.output:
            log.error("extract requires --pdf-dir, --output")
            return 1
        return action_extract(args.pdf_dir, args.output)

    if args.action == "index":
        if not args.pdf_texts or not args.output:
            log.error("index requires --pdf-texts, --output")
            return 1
        return action_index(args.pdf_texts, args.output)

    if args.action == "search":
        if not args.query or not args.index_path:
            log.error("search requires --query, --index-path")
            return 1
        return action_search(args.query, args.index_path, args.limit)

    return 1


if __name__ == "__main__":
    sys.exit(main())
