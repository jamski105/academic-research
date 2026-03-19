#!/usr/bin/env python3
"""Index and search full text from local PDFs."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader

BASE_DIR = os.path.expanduser("~/.academic-research")
INDEX_PATH = os.path.join(BASE_DIR, "fulltext_index.json")
STOPWORDS = {"a", "an", "the", "and", "or", "in", "of", "to", "is", "are", "was", "were", "for", "with", "that", "this"}


def ensure_index_file() -> None:
    """Ensure index storage exists."""
    base = os.path.dirname(INDEX_PATH)
    os.makedirs(base, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w", encoding="utf-8") as fh:
            json.dump({"index": {}, "docs": {}}, fh)


def load_index() -> dict[str, Any]:
    """Load existing index."""
    with open(INDEX_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_index(data: dict[str, Any]) -> None:
    """Save index to disk."""
    with open(INDEX_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def tokenize(text: str) -> list[str]:
    """Tokenize and remove stopwords."""
    tokens = [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]
    return [t for t in tokens if t not in STOPWORDS]


def extract_pdf_text(pdf_path: Path) -> str | None:
    """Extract text from PDF; return None on read issues."""
    try:
        reader = PdfReader(str(pdf_path))
        if reader.is_encrypted:
            logging.warning("Skipping encrypted PDF: %s", pdf_path)
            return None
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception:
        logging.exception("Skipping unreadable PDF: %s", pdf_path)
        return None


def remove_doc_from_index(index_data: dict[str, Any], doc_id: str) -> None:
    """Remove existing doc postings from inverted index."""
    for term in list(index_data["index"].keys()):
        postings = index_data["index"][term]
        if doc_id in postings:
            del postings[doc_id]
        if not postings:
            del index_data["index"][term]


def index_pdfs(pdf_dir: str) -> int:
    """Index PDFs incrementally by mtime."""
    ensure_index_file()
    data = load_index()
    data.setdefault("index", {})
    data.setdefault("docs", {})

    for pdf_path in Path(pdf_dir).rglob("*.pdf"):
        doc_id = os.path.relpath(str(pdf_path), BASE_DIR)
        mtime = pdf_path.stat().st_mtime
        existing = data["docs"].get(doc_id)
        if existing and float(existing.get("mtime", 0.0)) == mtime:
            continue

        text = extract_pdf_text(pdf_path)
        if text is None:
            continue

        remove_doc_from_index(data, doc_id)
        tokens = tokenize(text)
        total_tokens = len(tokens)
        if total_tokens == 0:
            logging.warning("No tokens extracted from PDF: %s", pdf_path)
            continue

        freqs: dict[str, int] = {}
        for tok in tokens:
            freqs[tok] = freqs.get(tok, 0) + 1
        for term, count in freqs.items():
            tf = count / total_tokens
            data["index"].setdefault(term, {})[doc_id] = tf

        data["docs"][doc_id] = {
            "path": str(pdf_path),
            "title": pdf_path.stem,
            "token_count": total_tokens,
            "mtime": mtime,
        }

    save_index(data)
    return 0


def search_index(query: str, limit: int) -> int:
    """Search index using TF-IDF scoring and print ranked docs."""
    ensure_index_file()
    data = load_index()
    terms = tokenize(query)
    total_docs = max(len(data.get("docs", {})), 1)
    scores: dict[str, float] = {}
    for term in terms:
        postings = data.get("index", {}).get(term, {})
        if not postings:
            continue
        idf = math.log(total_docs / len(postings))
        for doc_id, tf in postings.items():
            scores[doc_id] = scores.get(doc_id, 0.0) + float(tf) * idf

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    for idx, (doc_id, score) in enumerate(ranked, start=1):
        doc = data.get("docs", {}).get(doc_id, {"title": Path(doc_id).stem, "path": doc_id})
        display_path = doc.get("path") or os.path.join(BASE_DIR, doc_id)
        print(f"{idx}. {doc.get('title')} ({display_path}) — score: {score:.4f}")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Index and search PDF full text")
    parser.add_argument("--action", required=True, choices=["index", "search"])
    parser.add_argument("--pdf-dir")
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    try:
        if args.action == "index":
            if not args.pdf_dir:
                logging.error("--pdf-dir is required for index action")
                return 1
            return index_pdfs(args.pdf_dir)
        if not args.query:
            logging.error("--query is required for search action")
            return 1
        return search_index(args.query, args.limit)
    except Exception:
        logging.exception("fulltext_index failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
