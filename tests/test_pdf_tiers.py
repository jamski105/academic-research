"""Unit-Tests fuer neue PDF-Tier-Funktionen (Tiers 6-8) — Chunk J v6.2."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_httpx_response(json_data: dict | list, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _mock_httpx_client(response: MagicMock) -> MagicMock:
    client = MagicMock()
    client.get.return_value = response
    return client


# ---------------------------------------------------------------------------
# Tier 6: OpenAccessButton
# ---------------------------------------------------------------------------

class TestTierOpenAccessButton:
    def test_success_returns_pdf_url(self):
        """Erfolgsfall: API gibt Treffer zurueck, URL wird extrahiert."""
        from pdf import tier_openaccessbutton

        resp = _mock_httpx_response({
            "data": {
                "url": "https://example.org/paper.pdf",
                "type": "article"
            }
        })
        client = _mock_httpx_client(resp)

        result = tier_openaccessbutton(client, "10.1371/journal.pbio.1002055")
        assert result == "https://example.org/paper.pdf"
        client.get.assert_called_once()
        call_url = client.get.call_args[0][0]
        assert "openaccessbutton.org" in call_url

    def test_empty_data_returns_none(self):
        """Leerfall: API gibt kein 'data.url' zurueck -> None."""
        from pdf import tier_openaccessbutton

        resp = _mock_httpx_response({"data": {}})
        client = _mock_httpx_client(resp)

        result = tier_openaccessbutton(client, "10.9999/nothing")
        assert result is None

    def test_missing_data_key_returns_none(self):
        """Leerfall: Response ohne 'data'-Key -> None."""
        from pdf import tier_openaccessbutton

        resp = _mock_httpx_response({})
        client = _mock_httpx_client(resp)

        result = tier_openaccessbutton(client, "10.9999/nothing")
        assert result is None


# ---------------------------------------------------------------------------
# Tier 7: DOAB
# ---------------------------------------------------------------------------

DOAB_HIT_RESPONSE = [
    {
        "uuid": "abc-123",
        "metadata": [
            {"key": "dc.title", "value": "Open Access Buch"},
        ],
        "bitstreams": [
            {
                "bundleName": "ORIGINAL",
                "mimeType": "application/pdf",
                "retrieveLink": "/bitstream/handle/20.500.12854/123/book.pdf",
            }
        ],
    }
]

DOAB_HIT_ABSOLUTE_URL = [
    {
        "uuid": "def-456",
        "bitstreams": [
            {
                "bundleName": "ORIGINAL",
                "mimeType": "application/pdf",
                "retrieveLink": "https://downloads.doabooks.org/book.pdf",
            }
        ],
    }
]

DOAB_NO_PDF_RESPONSE = [
    {
        "uuid": "ghi-789",
        "bitstreams": [
            {
                "bundleName": "ORIGINAL",
                "mimeType": "text/html",
                "retrieveLink": "/bitstream/handle/123/page.html",
            }
        ],
    }
]


class TestTierDoab:
    def test_success_relative_url_prepends_base(self):
        """Erfolgsfall: relative retrieveLink bekommt DOAB-Basis-URL vorangestellt."""
        from pdf import tier_doab

        resp = _mock_httpx_response(DOAB_HIT_RESPONSE)
        client = _mock_httpx_client(resp)

        result = tier_doab(client, "9783446461031")
        assert result is not None
        assert result.startswith("https://directory.doabooks.org")
        assert "book.pdf" in result
        client.get.assert_called_once()
        call_url = client.get.call_args[0][0]
        assert "doabooks.org" in call_url

    def test_success_absolute_url_returned_as_is(self):
        """Erfolgsfall: absolute URL wird unveraendert zurueckgegeben."""
        from pdf import tier_doab

        resp = _mock_httpx_response(DOAB_HIT_ABSOLUTE_URL)
        client = _mock_httpx_client(resp)

        result = tier_doab(client, "Open Access Buch")
        assert result == "https://downloads.doabooks.org/book.pdf"

    def test_empty_response_returns_none(self):
        """Leerfall: leere Trefferliste -> None."""
        from pdf import tier_doab

        resp = _mock_httpx_response([])
        client = _mock_httpx_client(resp)

        result = tier_doab(client, "9783000000000")
        assert result is None

    def test_no_pdf_bitstream_returns_none(self):
        """Leerfall: Treffer vorhanden aber kein PDF-Bitstream -> None."""
        from pdf import tier_doab

        resp = _mock_httpx_response(DOAB_NO_PDF_RESPONSE)
        client = _mock_httpx_client(resp)

        result = tier_doab(client, "some title")
        assert result is None


# ---------------------------------------------------------------------------
# Tier 8: EuropePMC
# ---------------------------------------------------------------------------

EUROPEPMC_HIT_RESPONSE = {
    "resultList": {
        "result": [
            {
                "pmid": "12345678",
                "title": "A biomedical study",
                "fullTextUrlList": {
                    "fullTextUrl": [
                        {
                            "availability": "Open access",
                            "availabilityCode": "OA",
                            "documentStyle": "html",
                            "site": "Europe_PMC",
                            "url": "https://europepmc.org/articles/PMC12345",
                        },
                        {
                            "availability": "Open access",
                            "availabilityCode": "OA",
                            "documentStyle": "pdf",
                            "site": "Europe_PMC",
                            "url": "https://europepmc.org/articles/PMC12345?pdf=render",
                        },
                    ]
                },
            }
        ]
    }
}

EUROPEPMC_EMPTY_RESPONSE = {
    "resultList": {
        "result": []
    }
}

EUROPEPMC_NO_OA_PDF = {
    "resultList": {
        "result": [
            {
                "fullTextUrlList": {
                    "fullTextUrl": [
                        {
                            "availability": "Subscription",
                            "documentStyle": "pdf",
                            "url": "https://example.com/restricted.pdf",
                        }
                    ]
                }
            }
        ]
    }
}


class TestTierEuropePMC:
    def test_success_returns_oa_pdf_url(self):
        """Erfolgsfall: OA-PDF-URL aus fullTextUrlList extrahiert."""
        from pdf import tier_europepmc

        resp = _mock_httpx_response(EUROPEPMC_HIT_RESPONSE)
        client = _mock_httpx_client(resp)

        result = tier_europepmc(client, "10.1186/s12864-021-07421-4")
        assert result == "https://europepmc.org/articles/PMC12345?pdf=render"
        client.get.assert_called_once()
        call_url = client.get.call_args[0][0]
        assert "europepmc.org" in call_url

    def test_empty_result_list_returns_none(self):
        """Leerfall: keine Treffer -> None."""
        from pdf import tier_europepmc

        resp = _mock_httpx_response(EUROPEPMC_EMPTY_RESPONSE)
        client = _mock_httpx_client(resp)

        result = tier_europepmc(client, "10.9999/nothing")
        assert result is None

    def test_no_oa_pdf_returns_none(self):
        """Leerfall: nur kostenpflichtiger PDF-Link -> None."""
        from pdf import tier_europepmc

        resp = _mock_httpx_response(EUROPEPMC_NO_OA_PDF)
        client = _mock_httpx_client(resp)

        result = tier_europepmc(client, "10.9999/subscription")
        assert result is None
