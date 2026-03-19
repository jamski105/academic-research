#!/usr/bin/env python3
"""Multi-source academic paper search."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import sys
import time
from typing import Any, Callable

import xml.etree.ElementTree as ET

import httpx

TIMEOUT = 30.0
OAI_DC_NS = "http://purl.org/dc/elements/1.1/"


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
                "abstract": None,
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
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
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
    """Search BASE API."""
    url = "https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi"
    params = {"func": "PerformSearch", "query": query, "format": "json"}
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    time.sleep(0.5)
    items = payload.get("response", {}).get("docs", []) or payload.get("records", []) or []
    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        results.append(
            normalize_paper(
                {
                    "doi": item.get("doi"),
                    "title": item.get("title") or item.get("dctitle"),
                    "authors": item.get("authors") or item.get("creator") or [],
                    "year": int(item["year"]) if item.get("year") and str(item.get("year")).isdigit() else None,
                    "abstract": item.get("abstract"),
                    "venue": item.get("publisher"),
                    "citations": 0,
                    "url": item.get("url") or item.get("id"),
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


MODULES: dict[str, Callable[[str, int], list[dict[str, Any]]]] = {
    "crossref": search_crossref,
    "openalex": search_openalex,
    "semantic_scholar": search_semantic_scholar,
    "base": search_base,
    "econbiz": search_econbiz,
    "econstor": search_econstor,
}


def run_module(module_name: str, query: str, limit: int) -> tuple[str, list[dict[str, Any]], bool]:
    """Run one module and return (module, papers, failed)."""
    try:
        return module_name, MODULES[module_name](query, limit), False
    except Exception:
        logging.exception("Module '%s' failed", module_name)
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
