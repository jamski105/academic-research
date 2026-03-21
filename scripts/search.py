#!/usr/bin/env python3
"""Multi-source academic paper search — v4 rewrite.

Searches across 7 API sources in parallel:
  CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv

Usage:
  python search.py --query "DevOps Governance" --modules crossref,openalex --limit 50
  python search.py --queries-file queries.json --modules crossref,semantic_scholar
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Callable

import httpx

from text_utils import normalize_paper, save_json

TIMEOUT = 30.0
OAI_DC_NS = "http://purl.org/dc/elements/1.1/"
ARXIV_NS = "http://www.w3.org/2005/Atom"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

def _retry_on_429(fn: Callable, max_retries: int = 3, base_delay: float = 2.0) -> Any:
    """Call fn(), retrying on HTTP 429 with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            log.warning("429 rate limit — retrying in %.0fs (%d/%d)", delay, attempt + 1, max_retries)
            time.sleep(delay)


# ---------------------------------------------------------------------------
# Search modules
# ---------------------------------------------------------------------------

def search_crossref(query: str, limit: int) -> list[dict[str, Any]]:
    """Search CrossRef works endpoint."""
    url = "https://api.crossref.org/works"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params={"query": query, "rows": limit})
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
    time.sleep(0.5)
    results: list[dict[str, Any]] = []
    for item in items:
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            full_name = f"{given} {family}".strip()
            if full_name:
                authors.append(full_name)
        year = None
        date_parts = (
            item.get("published-print", {}).get("date-parts")
            or item.get("published-online", {}).get("date-parts")
        )
        if date_parts and date_parts[0]:
            year = int(date_parts[0][0])
        results.append(
            normalize_paper(
                {
                    "doi": item.get("DOI"),
                    "title": (item.get("title") or [None])[0],
                    "authors": authors,
                    "year": year,
                    "abstract": item.get("abstract"),
                    "venue": (item.get("container-title") or [None])[0],
                    "citations": item.get("is-referenced-by-count", 0),
                    "url": item.get("URL"),
                },
                "crossref",
            )
        )
    return results


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Reconstruct abstract from OpenAlex inverted index."""
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions))


def search_openalex(query: str, limit: int) -> list[dict[str, Any]]:
    """Search OpenAlex works endpoint."""
    url = "https://api.openalex.org/works"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params={"search": query, "per-page": limit})
        resp.raise_for_status()
        items = resp.json().get("results", [])
    time.sleep(0.5)
    results: list[dict[str, Any]] = []
    for item in items:
        authors = [
            a.get("author", {}).get("display_name")
            for a in item.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]
        location = item.get("primary_location", {}) or {}
        source = location.get("source", {}) or {}
        oa_info = item.get("open_access") or {}
        entry = normalize_paper(
            {
                "doi": (item.get("doi") or "").replace("https://doi.org/", "") or None,
                "title": item.get("title"),
                "authors": authors,
                "year": item.get("publication_year"),
                "abstract": _reconstruct_abstract(item.get("abstract_inverted_index")),
                "venue": source.get("display_name"),
                "citations": item.get("cited_by_count", 0),
                "url": item.get("id"),
                "oa_url": oa_info.get("oa_url"),
            },
            "openalex",
        )
        results.append(entry)
    return results


def search_semantic_scholar(query: str, limit: int) -> list[dict[str, Any]]:
    """Search Semantic Scholar paper endpoint."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,authors,year,abstract,venue,citationCount,openAccessPdf,externalIds",
    }
    headers: dict[str, str] = {}
    if api_key := os.environ.get("SS_API_KEY"):
        headers["x-api-key"] = api_key
    with httpx.Client(timeout=TIMEOUT) as client:
        def _get() -> httpx.Response:
            r = client.get(url, params=params, headers=headers)
            r.raise_for_status()
            return r
        resp = _retry_on_429(_get)
        items = resp.json().get("data", [])
    time.sleep(0.5)
    results: list[dict[str, Any]] = []
    for item in items:
        external_ids = item.get("externalIds") or {}
        oa_pdf = item.get("openAccessPdf") or {}
        entry = normalize_paper(
            {
                "doi": external_ids.get("DOI"),
                "title": item.get("title"),
                "authors": [a.get("name") for a in item.get("authors", []) if a.get("name")],
                "year": item.get("year"),
                "abstract": item.get("abstract"),
                "venue": item.get("venue"),
                "citations": item.get("citationCount", 0),
                "url": f"https://www.semanticscholar.org/paper/{item.get('paperId')}" if item.get("paperId") else None,
                "open_access_pdf": oa_pdf.get("url"),
            },
            "semantic_scholar",
        )
        results.append(entry)
    return results


def search_base(query: str, limit: int) -> list[dict[str, Any]]:
    """Search BASE API (Bielefeld Academic Search Engine)."""
    url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
    params = {"func": "PerformSearch", "query": query, "format": "json", "hits": limit}
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    time.sleep(0.5)
    items = payload.get("response", {}).get("docs", []) or []
    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        def dc(fld: str) -> str | None:
            val = item.get(fld)
            return val[0] if isinstance(val, list) and val else val

        doi = None
        for ident in item.get("dcidentifier") or []:
            ident_str = str(ident)
            if "doi.org/" in ident_str:
                doi = ident_str.split("doi.org/")[-1]
                break
            if ident_str.startswith("10."):
                doi = ident_str
                break
        year_raw = dc("dcyear")
        year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
        results.append(
            normalize_paper(
                {
                    "doi": doi,
                    "title": dc("dctitle"),
                    "authors": item.get("dccreator") or [],
                    "year": year,
                    "abstract": dc("dcabstract"),
                    "venue": dc("dcpublisher"),
                    "citations": 0,
                    "url": dc("dcidentifier"),
                },
                "base",
            )
        )
    return results


def search_econbiz(query: str, limit: int) -> list[dict[str, Any]]:
    """Search EconBiz API."""
    url = "https://api.econbiz.de/v1/search"
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params={"q": query, "size": limit})
        resp.raise_for_status()
        payload = resp.json()
    time.sleep(0.5)
    items = payload.get("results", []) or payload.get("items", []) or []
    results: list[dict[str, Any]] = []
    for item in items:
        results.append(
            normalize_paper(
                {
                    "doi": item.get("doi"),
                    "title": item.get("title"),
                    "authors": item.get("authors") or [],
                    "year": int(item["year"]) if item.get("year") and str(item.get("year")).isdigit() else None,
                    "abstract": item.get("abstract"),
                    "venue": item.get("source") or item.get("venue"),
                    "citations": item.get("citationCount", 0),
                    "url": item.get("url"),
                },
                "econbiz",
            )
        )
    return results


def search_econstor(query: str, limit: int) -> list[dict[str, Any]]:
    """Search EconStor via REST API with OAI-PMH fallback."""
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=TIMEOUT) as client:
        rest_resp = client.get(
            "https://www.econstor.eu/rest/items/find-by-metadata-field",
            params={"value": query, "key": "dc.title", "limit": limit},
        )
        if rest_resp.status_code == 200 and rest_resp.headers.get("content-type", "").startswith("application/json"):
            items = rest_resp.json()
        else:
            # Fallback: OAI-PMH harvest with client-side keyword filtering
            items = []
            oai_resp = client.get(
                "https://www.econstor.eu/oai/request",
                params={"verb": "ListRecords", "metadataPrefix": "oai_dc"},
            )
            oai_resp.raise_for_status()
            root = ET.fromstring(oai_resp.text)
            ns = {"oai": "http://www.openarchives.org/OAI/2.0/", "dc": OAI_DC_NS}
            query_lower = query.lower()
            for record in root.findall(".//oai:record", ns):
                metadata = record.find(".//oai:metadata", ns)
                if metadata is None:
                    continue
                dc_el = metadata.find("{http://www.openarchives.org/OAI/2.0/oai_dc/}dc")
                if dc_el is None:
                    continue
                title_el = dc_el.find(f"{{{OAI_DC_NS}}}title")
                title = title_el.text if title_el is not None and title_el.text else ""
                desc_el = dc_el.find(f"{{{OAI_DC_NS}}}description")
                desc = desc_el.text if desc_el is not None and desc_el.text else ""
                if query_lower not in title.lower() and query_lower not in desc.lower():
                    continue
                creators = [c.text for c in dc_el.findall(f"{{{OAI_DC_NS}}}creator") if c.text]
                date_el = dc_el.find(f"{{{OAI_DC_NS}}}date")
                year = None
                if date_el is not None and date_el.text:
                    year_str = date_el.text[:4]
                    if year_str.isdigit():
                        year = int(year_str)
                doi = None
                item_url = None
                for id_el in dc_el.findall(f"{{{OAI_DC_NS}}}identifier"):
                    if id_el.text and "doi.org" in id_el.text:
                        doi = id_el.text.replace("https://doi.org/", "").replace("http://doi.org/", "")
                    elif id_el.text and id_el.text.startswith("http"):
                        item_url = id_el.text
                items.append({"title": title, "authors": creators, "year": year, "abstract": desc, "doi": doi, "url": item_url})
                if len(items) >= limit:
                    break
    time.sleep(0.5)
    for item in items[:limit]:
        if isinstance(item, dict):
            results.append(
                normalize_paper(
                    {
                        "doi": item.get("doi"),
                        "title": item.get("title"),
                        "authors": item.get("authors") or [],
                        "year": item.get("year"),
                        "abstract": item.get("abstract"),
                        "venue": "EconStor",
                        "citations": 0,
                        "url": item.get("url"),
                    },
                    "econstor",
                )
            )
    return results


def search_arxiv(query: str, limit: int) -> list[dict[str, Any]]:
    """Search arXiv via Atom feed API."""
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results: list[dict[str, Any]] = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        raw_id = (entry.findtext(f"{{{ARXIV_NS}}}id") or "").strip()
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0]
        title = (entry.findtext(f"{{{ARXIV_NS}}}title") or "").strip().replace("\n", " ")
        abstract = (entry.findtext(f"{{{ARXIV_NS}}}summary") or "").strip()
        authors = [
            a.findtext(f"{{{ARXIV_NS}}}name") or ""
            for a in entry.findall(f"{{{ARXIV_NS}}}author")
        ]
        published = entry.findtext(f"{{{ARXIV_NS}}}published") or ""
        year = int(published[:4]) if len(published) >= 4 else None
        pdf_url = None
        for link in entry.findall(f"{{{ARXIV_NS}}}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        results.append(
            normalize_paper(
                {
                    "doi": f"10.48550/arxiv.{arxiv_id}" if arxiv_id else None,
                    "title": title,
                    "authors": [a for a in authors if a],
                    "year": year,
                    "abstract": abstract,
                    "venue": "arXiv",
                    "citations": 0,
                    "url": pdf_url,
                    "open_access_pdf": pdf_url,
                },
                "arxiv",
            )
        )
    time.sleep(0.5)
    return results


# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

MODULES: dict[str, Callable[[str, int], list[dict[str, Any]]]] = {
    "crossref": search_crossref,
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "base": search_base,
    "econbiz": search_econbiz,
    "econstor": search_econstor,
    "arxiv": search_arxiv,
}


# ---------------------------------------------------------------------------
# Parallel execution
# ---------------------------------------------------------------------------

def _run_module(module_name: str, query: str, limit: int) -> tuple[str, list[dict[str, Any]], bool]:
    """Run one search module, return (name, papers, failed)."""
    max_attempts = 3 if module_name == "semantic_scholar" else 1
    for attempt in range(max_attempts):
        try:
            return module_name, MODULES[module_name](query, limit), False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_attempts - 1:
                delay = 2 ** attempt * 2
                log.warning("Module '%s' rate-limited, retry in %ds", module_name, delay)
                time.sleep(delay)
                continue
            log.exception("Module '%s' failed (HTTP %s)", module_name, e.response.status_code)
            return module_name, [], True
        except Exception:
            log.exception("Module '%s' failed", module_name)
            return module_name, [], True
    return module_name, [], True


def run_search(
    query: str,
    modules: list[str],
    limit: int = 50,
    queries_map: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Run search across multiple modules in parallel.

    Args:
        query: Default search query.
        modules: List of module names to search.
        limit: Max results per module.
        queries_map: Optional module-specific queries (from query-generator).

    Returns:
        Tuple of (all_papers, failed_modules).
    """
    all_results: list[dict[str, Any]] = []
    failed: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(modules))) as executor:
        futures = []
        for m in modules:
            q = (queries_map or {}).get(m, query)
            futures.append(executor.submit(_run_module, m, q, limit))
        for future in concurrent.futures.as_completed(futures):
            name, papers, did_fail = future.result()
            all_results.extend(papers)
            if did_fail:
                failed.append(name)
    return all_results, failed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search multiple academic APIs")
    parser.add_argument("--query", required=True)
    parser.add_argument("--modules", required=True, help="Comma-separated module names")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--queries-file", help="JSON file with module-specific queries")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    requested = [m.strip() for m in args.modules.split(",") if m.strip()]
    invalid = [m for m in requested if m not in MODULES]
    if invalid:
        log.error("Unknown modules: %s", ", ".join(invalid))
        return 1

    queries_map = None
    if args.queries_file:
        try:
            with open(args.queries_file, "r", encoding="utf-8") as fh:
                queries_map = json.load(fh)
        except Exception:
            log.exception("Failed to load queries file")
            return 1

    papers, failed = run_search(args.query, requested, args.limit, queries_map)
    log.info("Found %d papers (%d modules failed)", len(papers), len(failed))

    output_text = json.dumps(papers, ensure_ascii=False, indent=2)
    if args.output:
        save_json(papers, args.output)
    else:
        sys.stdout.write(output_text + "\n")

    return 1 if len(failed) == len(requested) else 0


if __name__ == "__main__":
    sys.exit(main())
