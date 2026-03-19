#!/usr/bin/env python3
"""Multi-source academic paper search."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import sys
import time
from typing import Any, Callable

import xml.etree.ElementTree as ET

import httpx

TIMEOUT = 30.0
OAI_DC_NS = "http://purl.org/dc/elements/1.1/"
ARXIV_NS = "http://www.w3.org/2005/Atom"


def retry_on_429(fn: Callable, max_retries: int = 3, base_delay: float = 2.0) -> Any:
    """Call fn(), retrying on HTTP 429 with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 429 or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 2s, 4s, 8s
            logging.warning("429 rate limit — retrying in %.0fs (attempt %d/%d)", delay, attempt + 1, max_retries)
            time.sleep(delay)


def normalize_paper(data: dict[str, Any], source_module: str) -> dict[str, Any]:
    """Normalize source-specific paper payload to common schema."""
    return {
        "doi": data.get("doi"),
        "title": data.get("title"),
        "authors": data.get("authors") or [],
        "year": data.get("year"),
        "abstract": data.get("abstract"),
        "venue": data.get("venue"),
        "citations": int(data.get("citations") or 0),
        "url": data.get("url"),
        "source_module": source_module,
    }


def search_crossref(query: str, limit: int) -> list[dict[str, Any]]:
    """Search Crossref works endpoint."""
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
            full_name = (f"{given} {family}").strip()
            if full_name:
                authors.append(full_name)
        year = None
        date_parts = item.get("published-print", {}).get("date-parts") or item.get("published-online", {}).get("date-parts")
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


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Rekonstruiert Abstract-Text aus OpenAlex inverted index."""
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
        authors = [a.get("author", {}).get("display_name") for a in item.get("authorships", []) if a.get("author", {}).get("display_name")]
        location = item.get("primary_location", {}) or {}
        source = location.get("source", {}) or {}
        entry = normalize_paper(
            {
                "doi": (item.get("doi") or "").replace("https://doi.org/", "") or None,
                "title": item.get("title"),
                "authors": authors,
                "year": item.get("publication_year"),
                "abstract": reconstruct_abstract(item.get("abstract_inverted_index")),
                "venue": source.get("display_name"),
                "citations": item.get("cited_by_count", 0),
                "url": item.get("id"),
            },
            "openalex",
        )
        entry["oa_url"] = (item.get("open_access") or {}).get("oa_url")
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
        resp = retry_on_429(_get)
        items = resp.json().get("data", [])
    time.sleep(0.5)
    results: list[dict[str, Any]] = []
    for item in items:
        external_ids = item.get("externalIds") or {}
        open_access_pdf = item.get("openAccessPdf") or {}
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
            },
            "semantic_scholar",
        )
        entry["openAccessPdf"] = open_access_pdf.get("url")
        results.append(entry)
    return results


def search_base(query: str, limit: int) -> list[dict[str, Any]]:
    """Search BASE API (Bielefeld Academic Search Engine)."""
    url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
    params = {
        "func": "PerformSearch",
        "query": query,
        "format": "json",
        "hits": limit,  # FIX: was missing — BASE returns 0 docs without this
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    time.sleep(0.5)
    items = payload.get("response", {}).get("docs", []) or []

    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        # FIX: BASE uses Dublin Core — all fields are arrays, extract first element
        def dc(field: str) -> str | None:
            val = item.get(field)
            if isinstance(val, list):
                return val[0] if val else None
            return val

        # Extract DOI from dcidentifier array (may contain DOI URL or plain DOI)
        doi = None
        for ident in (item.get("dcidentifier") or []):
            ident_str = str(ident)
            if "doi.org/" in ident_str:
                doi = ident_str.split("doi.org/")[-1]
                break
            if ident_str.startswith("10."):
                doi = ident_str
                break

        year_raw = dc("dcyear")
        year = int(year_raw) if year_raw and str(year_raw).isdigit() else None

        results.append(normalize_paper({
            "doi": doi,
            "title": dc("dctitle"),
            "authors": item.get("dccreator") or [],
            "year": year,
            "abstract": dc("dcabstract"),
            "venue": dc("dcpublisher"),
            "citations": 0,
            "url": dc("dcidentifier"),
        }, "base"))
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
    """Search EconStor via OAI-PMH (Dublin Core)."""
    url = "https://www.econstor.eu/oai/request"
    params = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
        "set": f"col_10419_{query.replace(' ', '_')}",
    }
    # OAI-PMH set-based filtering is limited; fall back to keyword search
    # via the simple search endpoint if the set approach fails.
    search_url = "https://www.econstor.eu/oai/request"
    search_params = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        # Use OAI-PMH ListIdentifiers with keyword in set isn't reliable,
        # so we query the HTML search and parse handles, then fetch OAI per item.
        # Simpler approach: use the EconStor REST-like search endpoint.
        search_resp = client.get(
            "https://www.econstor.eu/rest/items/find-by-metadata-field",
            params={"value": query, "key": "dc.title", "limit": limit},
            timeout=TIMEOUT,
        )
        if search_resp.status_code == 200:
            items = search_resp.json() if search_resp.headers.get("content-type", "").startswith("application/json") else []
        else:
            # Fallback: OAI-PMH full harvest with client-side filtering
            items = []
            resp = client.get(url, params=search_params, timeout=TIMEOUT)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            ns = {"oai": "http://www.openarchives.org/OAI/2.0/", "dc": OAI_DC_NS}
            query_lower = query.lower()
            for record in root.findall(".//oai:record", ns):
                metadata = record.find(".//oai:metadata", ns)
                if metadata is None:
                    continue
                dc = metadata.find("{http://www.openarchives.org/OAI/2.0/oai_dc/}dc")
                if dc is None:
                    continue
                title_el = dc.find(f"{{{OAI_DC_NS}}}title")
                title = title_el.text if title_el is not None and title_el.text else ""
                desc_el = dc.find(f"{{{OAI_DC_NS}}}description")
                desc = desc_el.text if desc_el is not None and desc_el.text else ""
                if query_lower not in title.lower() and query_lower not in desc.lower():
                    continue
                creators = [c.text for c in dc.findall(f"{{{OAI_DC_NS}}}creator") if c.text]
                date_el = dc.find(f"{{{OAI_DC_NS}}}date")
                year = None
                if date_el is not None and date_el.text:
                    year_match = date_el.text[:4]
                    if year_match.isdigit():
                        year = int(year_match)
                id_els = dc.findall(f"{{{OAI_DC_NS}}}identifier")
                doi = None
                item_url = None
                for id_el in id_els:
                    if id_el.text and "doi.org" in id_el.text:
                        doi = id_el.text.replace("https://doi.org/", "").replace("http://doi.org/", "")
                    elif id_el.text and id_el.text.startswith("http"):
                        item_url = id_el.text
                items.append({
                    "title": title,
                    "authors": creators,
                    "year": year,
                    "abstract": desc,
                    "doi": doi,
                    "url": item_url,
                })
                if len(items) >= limit:
                    break
    time.sleep(0.5)
    results: list[dict[str, Any]] = []
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
    """Search arXiv via Atom feed API — primary OA source for CS/ML."""
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
    results = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        raw_id = (entry.findtext(f"{{{ARXIV_NS}}}id") or "").strip()
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0]  # "1906.10742"

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

        results.append(normalize_paper({
            "doi": f"10.48550/arxiv.{arxiv_id}" if arxiv_id else None,
            "title": title,
            "authors": [a for a in authors if a],
            "year": year,
            "abstract": abstract,
            "venue": "arXiv",
            "citations": 0,
            "url": pdf_url,
        }, "arxiv"))

    time.sleep(0.5)  # arXiv asks for polite crawling
    return results


MODULES: dict[str, Callable[[str, int], list[dict[str, Any]]]] = {
    "crossref": search_crossref,
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "base": search_base,
    "econbiz": search_econbiz,
    "econstor": search_econstor,
    "arxiv": search_arxiv,
}


def run_module(module_name: str, query: str, limit: int) -> tuple[str, list[dict[str, Any]], bool]:
    """Run one module and return (module, papers, failed)."""
    max_attempts = 3 if module_name == "semantic_scholar" else 1
    for attempt in range(max_attempts):
        try:
            return module_name, MODULES[module_name](query, limit), False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_attempts - 1:
                delay = 2 ** attempt * 2  # 2s, dann 4s
                logging.warning("Module '%s' rate-limited, retry in %ds", module_name, delay)
                time.sleep(delay)
                continue
            logging.exception("Module '%s' failed (HTTP %s)", module_name, e.response.status_code)
            return module_name, [], True
        except Exception:
            logging.exception("Module '%s' failed", module_name)
            return module_name, [], True
    return module_name, [], True


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Search multiple academic APIs")
    parser.add_argument("--query", required=True)
    parser.add_argument("--modules", required=True, help="Comma-separated module names")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    requested_modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    invalid = [m for m in requested_modules if m not in MODULES]
    if invalid:
        logging.error("Unknown modules: %s", ", ".join(invalid))
        return 1

    all_results: list[dict[str, Any]] = []
    failed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(requested_modules))) as executor:
        futures = [executor.submit(run_module, m, args.query, args.limit) for m in requested_modules]
        for future in concurrent.futures.as_completed(futures):
            _, papers, failed = future.result()
            all_results.extend(papers)
            if failed:
                failed_count += 1

    output_text = json.dumps(all_results, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output_text)
    else:
        sys.stdout.write(output_text + "\n")

    return 1 if failed_count == len(requested_modules) else 0


if __name__ == "__main__":
    sys.exit(main())
