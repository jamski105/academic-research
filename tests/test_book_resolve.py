"""Tests fuer book_resolve.py — DNB/OL/GoogleBooks/DOAB Clients."""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Sicherstellen dass scripts/ im Pfad ist
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Hilfs-Fixtures
# ---------------------------------------------------------------------------

DNB_SRU_RESPONSE_ISBN = """<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
  <numberOfRecords>1</numberOfRecords>
  <records>
    <record>
      <recordData>
        <record xmlns="http://www.loc.gov/MARC21/slim">
          <datafield tag="245" ind1=" " ind2=" ">
            <subfield code="a">Werkzeugmaschinen</subfield>
            <subfield code="b">Grundlagen</subfield>
          </datafield>
          <datafield tag="100" ind1=" " ind2=" ">
            <subfield code="a">Tschaetsch, Heinz</subfield>
          </datafield>
          <datafield tag="264" ind1=" " ind2="1">
            <subfield code="b">Hanser</subfield>
            <subfield code="c">2014</subfield>
          </datafield>
          <datafield tag="020" ind1=" " ind2=" ">
            <subfield code="a">9783446461031</subfield>
          </datafield>
        </record>
      </recordData>
    </record>
  </records>
</searchRetrieveResponse>""".encode("utf-8")

DNB_SRU_EMPTY = """<?xml version="1.0"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
  <numberOfRecords>0</numberOfRecords>
  <records/>
</searchRetrieveResponse>""".encode("utf-8")

OL_RESPONSE = {
    "ISBN:9783446461031": {
        "title": "Werkzeugmaschinen Grundlagen",
        "authors": [{"name": "Tschätsch, Heinz"}],
        "publishers": [{"name": "Hanser"}],
        "publish_date": "2014",
        "isbn_13": ["9783446461031"],
    }
}

GB_RESPONSE = {
    "kind": "books#volumes",
    "totalItems": 1,
    "items": [
        {
            "volumeInfo": {
                "title": "Werkzeugmaschinen Grundlagen",
                "authors": ["Tschätsch, Heinz"],
                "publisher": "Hanser",
                "publishedDate": "2014",
                "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9783446461031"}],
            }
        }
    ],
}

DOAB_RESPONSE = [
    {
        "uuid": "abc123",
        "metadata": [
            {"key": "dc.title", "value": "Open Access Buch"},
            {"key": "dc.identifier.uri", "value": "https://oapen.org/record/12345"},
        ],
        "bitstreams": [
            {"bundleName": "ORIGINAL", "mimeType": "application/pdf",
             "retrieveLink": "/bitstream/handle/123/book.pdf"}
        ],
    }
]


def _make_mock_response(content: bytes, status: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.content = content
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# DNB SRU Tests
# ---------------------------------------------------------------------------

def test_dnb_isbn_hit():
    """ISBN 9783446461031 liefert DNB-Treffer mit type=book und title."""
    import book_resolve

    with patch("book_resolve.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(DNB_SRU_RESPONSE_ISBN)
        result = book_resolve.resolve_dnb(isbn="9783446461031")

    assert result is not None
    assert result.get("type") == "book"
    assert "Werkzeugmaschinen" in result.get("title", "")
    assert result.get("ISBN") == "9783446461031"


# ---------------------------------------------------------------------------
# OpenLibrary Fallback Tests
# ---------------------------------------------------------------------------

def test_openlibrary_fallback():
    """DNB leer -> OpenLibrary liefert Daten."""
    import book_resolve

    def _make_json_response(data):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = data
        resp.raise_for_status = MagicMock()
        return resp

    with patch("book_resolve.requests.get") as mock_get:
        def side_effect(url, **kwargs):
            if "dnb.de" in url:
                return _make_mock_response(DNB_SRU_EMPTY)
            elif "openlibrary.org" in url:
                return _make_json_response(OL_RESPONSE)
            else:
                # DOAB und andere: leer zurueckgeben
                return _make_json_response([])

        mock_get.side_effect = side_effect
        result = book_resolve.resolve(isbn="9783446461031")

    assert result is not None
    assert result.get("type") == "book"
    assert "Werkzeugmaschinen" in result.get("title", "")


# ---------------------------------------------------------------------------
# GoogleBooks Fallback Tests
# ---------------------------------------------------------------------------

def test_googlebooks_fallback():
    """DNB + OL leer -> GoogleBooks liefert Daten."""
    import book_resolve

    def _make_json_response(data):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = data
        resp.raise_for_status = MagicMock()
        return resp

    with patch("book_resolve.requests.get") as mock_get:
        def side_effect(url, **kwargs):
            if "dnb.de" in url:
                return _make_mock_response(DNB_SRU_EMPTY)
            elif "openlibrary.org" in url:
                return _make_json_response({})
            elif "googleapis.com" in url:
                return _make_json_response(GB_RESPONSE)
            else:
                # DOAB: leer
                return _make_json_response([])

        mock_get.side_effect = side_effect
        result = book_resolve.resolve(isbn="9783446461031")

    assert result is not None
    assert result.get("type") == "book"
    assert result.get("ISBN") == "9783446461031"


# ---------------------------------------------------------------------------
# DOAB OA-Check Tests
# ---------------------------------------------------------------------------

def test_doab_oa_check():
    """DOAB-Check liefert OA-Flag und download_url."""
    import book_resolve

    with patch("book_resolve.requests.get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = DOAB_RESPONSE
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        result = book_resolve.check_doab(isbn="9783446461031")

    assert result is not None
    assert result.get("open_access") is True
    assert "download_url" in result


def test_no_source_returns_empty():
    """Alle Quellen schlagen fehl → leeres dict, kein crash."""
    import book_resolve

    with patch("book_resolve.requests.get") as mock_get:
        mock_get.side_effect = Exception("Netzwerkfehler")
        result = book_resolve.resolve(isbn="0000000000000")

    assert result == {} or result is None  # Kein crash


def test_isbn_csl_has_required_fields():
    """CSL-JSON enthält immer type, title."""
    import book_resolve

    with patch("book_resolve.requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(DNB_SRU_RESPONSE_ISBN)
        result = book_resolve.resolve(isbn="9783446461031")

    assert result.get("type") in ("book", "chapter")
    assert result.get("title"), "title darf nicht leer sein"
