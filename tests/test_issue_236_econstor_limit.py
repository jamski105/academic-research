"""Regression tests for issue #236.

EconStor OAI-PMH-Fallback in scripts/search.py darf nicht unbegrenzt
paginieren bzw. nicht den gesamten Repo-Dump in den Speicher laden.

Akzeptanzkriterium (#236):
- EconStor-Fallback laedt nicht den gesamten Repo-Dump in Memory.

Konkret abgesichert:
1. Es existieren explizite Mengenlimits (max. Records bzw. max.
   resumptionToken-Runden) als Modul-Konstanten.
2. Liefert das OAI-Endpoint endlos resumptionTokens, terminiert die
   Schleife dennoch nach <= OAI_MAX_PAGES Requests (kein Endlos-Paginieren).
3. Pro Seite werden hoechstens OAI_MAX_RECORDS Records geparst (kein
   vollstaendiger Repo-Dump im Speicher).
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import search


OAI_NS = "http://www.openarchives.org/OAI/2.0/"
DC_NS = "http://purl.org/dc/elements/1.1/"


def _record_xml(idx: int) -> str:
    """Ein OAI-record, dessen Titel die Query 'limittest' enthaelt."""
    return (
        "<record><metadata>"
        f'<oai_dc:dc xmlns:oai_dc="{OAI_NS}oai_dc/" xmlns:dc="{DC_NS}">'
        f"<dc:title>limittest paper {idx}</dc:title>"
        f"<dc:description>limittest abstract {idx}</dc:description>"
        f"<dc:creator>Author {idx}</dc:creator>"
        "<dc:date>2020-01-01</dc:date>"
        "</oai_dc:dc>"
        "</metadata></record>"
    )


def _list_records_response(n_records: int, with_token: bool) -> str:
    records = "".join(_record_xml(i) for i in range(n_records))
    token = (
        "<resumptionToken>tok-next</resumptionToken>" if with_token else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<OAI-PMH xmlns="{OAI_NS}">'
        f"<ListRecords>{records}{token}</ListRecords>"
        "</OAI-PMH>"
    )


def test_oai_limit_constants_exist():
    """Mengenlimit-Konstanten muessen existieren und endlich/positiv sein."""
    assert hasattr(search, "OAI_MAX_PAGES"), "OAI_MAX_PAGES fehlt"
    assert hasattr(search, "OAI_MAX_RECORDS"), "OAI_MAX_RECORDS fehlt"
    assert isinstance(search.OAI_MAX_PAGES, int) and search.OAI_MAX_PAGES > 0
    assert isinstance(search.OAI_MAX_RECORDS, int) and search.OAI_MAX_RECORDS > 0


def test_oai_fallback_terminates_on_endless_resumption_tokens(monkeypatch):
    """Endlos-resumptionToken darf nicht zu unbegrenztem Paginieren fuehren."""
    request_count = {"rest": 0, "oai": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "find-by-metadata-field" in url:
            request_count["rest"] += 1
            # Kein JSON -> erzwingt OAI-Fallback.
            return httpx.Response(503, text="upstream down")
        if "oai/request" in url:
            request_count["oai"] += 1
            # Liefert IMMER einen resumptionToken -> ohne Limit Endlosschleife.
            body = _list_records_response(n_records=2, with_token=True)
            return httpx.Response(200, text=body)
        return httpx.Response(404, text="")

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(search.httpx, "Client", patched_client)
    monkeypatch.setattr(search.time, "sleep", lambda *a, **k: None)

    results = search.search_econstor("limittest", limit=5)

    # Schleife terminiert ueberhaupt (kein Hang) und respektiert das Runden-Limit.
    assert request_count["oai"] <= search.OAI_MAX_PAGES, (
        f"OAI wurde {request_count['oai']}x abgefragt, "
        f"Limit ist {search.OAI_MAX_PAGES}"
    )
    assert isinstance(results, list)
    assert len(results) <= 5


def test_oai_fallback_caps_records_per_giant_page(monkeypatch):
    """Eine riesige Seite darf nicht komplett in Memory geparst werden."""
    huge = search.OAI_MAX_RECORDS + 5000
    parsed = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "find-by-metadata-field" in url:
            return httpx.Response(503, text="upstream down")
        if "oai/request" in url:
            body = _list_records_response(n_records=huge, with_token=False)
            return httpx.Response(200, text=body)
        return httpx.Response(404, text="")

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(search.httpx, "Client", patched_client)
    monkeypatch.setattr(search.time, "sleep", lambda *a, **k: None)

    # normalize_paper zaehlen, um die Anzahl tatsaechlich verarbeiteter
    # Records zu messen (Proxy fuer "nicht der ganze Dump").
    real_normalize = search.normalize_paper

    def counting_normalize(*args, **kwargs):
        parsed["count"] += 1
        return real_normalize(*args, **kwargs)

    monkeypatch.setattr(search, "normalize_paper", counting_normalize)

    results = search.search_econstor("limittest", limit=3)

    assert len(results) <= 3
    # Es duerfen nicht zehntausende Records verarbeitet werden.
    assert parsed["count"] <= search.OAI_MAX_RECORDS
