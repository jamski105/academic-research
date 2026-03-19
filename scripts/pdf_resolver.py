#!/usr/bin/env python3
"""Resolve and download PDFs with multi-tier fallbacks."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

import httpx

TIMEOUT = 30.0


def normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI string for API and file usage."""
    if not doi:
        return None
    value = doi.strip()
    value = re.sub(r"^https?://doi\.org/", "", value, flags=re.IGNORECASE)
    return value or None


def safe_filename(value: str) -> str:
    """Create safe filename segment."""
    return value.replace("/", "_").replace(":", "_")


def download_pdf(client: httpx.Client, pdf_url: str, output_path: str) -> None:
    """Stream-download PDF to output path."""
    with client.stream("GET", pdf_url, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as fh:
            for chunk in resp.iter_bytes():
                if chunk:
                    fh.write(chunk)


def tier_unpaywall(client: httpx.Client, doi: str, email: str) -> str | None:
    """Resolve PDF URL via Unpaywall."""
    resp = client.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email}, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    return ((payload.get("best_oa_location") or {}).get("url_for_pdf"))


def tier_core(client: httpx.Client, doi: str) -> str | None:
    """Resolve PDF URL via CORE."""
    resp = client.get("https://api.core.ac.uk/v3/search/works", params={"q": f"doi:{doi}"}, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    results = payload.get("results", [])
    if not results:
        return None
    return results[0].get("downloadUrl")


def tier_module_urls(paper: dict[str, Any]) -> str | None:
    """Resolve from source-provided OA URL fields."""
    open_access_pdf = paper.get("openAccessPdf")
    if isinstance(open_access_pdf, dict):
        url = open_access_pdf.get("url")
        if url:
            return url
    if isinstance(open_access_pdf, str) and open_access_pdf:
        return open_access_pdf
    oa_url = paper.get("oa_url")
    if isinstance(oa_url, str) and oa_url:
        return oa_url
    return None


def tier_direct_url(paper: dict[str, Any]) -> str | None:
    """Resolve direct PDF URL."""
    url = paper.get("url")
    if isinstance(url, str) and url.lower().endswith(".pdf"):
        return url
    return None


def resolve_pdf_url(client: httpx.Client, paper: dict[str, Any], email: str) -> tuple[str | None, str | None, str | None]:
    """Resolve PDF URL and source tier."""
    doi = normalize_doi(paper.get("doi"))
    try:
        if doi:
            url = tier_unpaywall(client, doi, email)
            if url:
                return url, "unpaywall", None
    except Exception as exc:
        logging.exception("Unpaywall failed for DOI %s", doi)
        last_error = str(exc)
    else:
        last_error = None

    try:
        if doi:
            url = tier_core(client, doi)
            if url:
                return url, "core", last_error
    except Exception as exc:
        logging.exception("CORE failed for DOI %s", doi)
        last_error = str(exc)

    module_url = tier_module_urls(paper)
    if module_url:
        return module_url, "module", last_error

    direct_url = tier_direct_url(paper)
    if direct_url:
        return direct_url, "direct", last_error

    return None, None, last_error


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Resolve PDFs for papers")
    parser.add_argument("--papers", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL", "academic-research@example.com"),
                        help="Email for Unpaywall API (set UNPAYWALL_EMAIL env var or pass --email)")
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

    os.makedirs(args.output_dir, exist_ok=True)
    status: dict[str, dict[str, Any]] = {}

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        for paper in papers:
            doi = normalize_doi(paper.get("doi"))
            key = doi or (paper.get("title") or "unknown")
            url, source, last_error = resolve_pdf_url(client, paper, args.email)
            if not url:
                status[key] = {"success": False, "pdf_path": None, "source": None, "error": last_error or "No PDF URL found"}
                continue

            filename_basis = doi or safe_filename((paper.get("title") or "untitled")[:80])
            output_path = os.path.join(args.output_dir, f"{safe_filename(filename_basis)}.pdf")
            try:
                download_pdf(client, url, output_path)
                status[key] = {"success": True, "pdf_path": output_path, "source": source, "error": None}
            except Exception as exc:
                logging.exception("Failed to download PDF for %s", key)
                status[key] = {"success": False, "pdf_path": None, "source": source, "error": str(exc)}

    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(status, fh, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("Failed to write status output")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
