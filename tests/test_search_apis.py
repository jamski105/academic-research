import pytest
from unittest.mock import patch, MagicMock
import httpx
from scripts.search_apis import search_semantic_scholar, search_arxiv, search_base


def test_semantic_scholar_retries_on_429():
    """Should retry up to 3 times with backoff, then succeed."""
    call_count = 0

    def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            resp = MagicMock()
            resp.status_code = 429
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=resp
            )
            return resp
        # Third call succeeds
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "data": [{"paperId": "abc", "title": "Test Paper", "authors": [],
                      "year": 2023, "abstract": None, "venue": None,
                      "citationCount": 0, "openAccessPdf": None, "externalIds": {}}]
        }
        return resp

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: s
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = mock_get
        mock_client_cls.return_value = mock_client

        with patch("time.sleep"):
            results = search_semantic_scholar("machine learning testing", 10)

    assert call_count == 3
    assert len(results) == 1
    assert results[0]["title"] == "Test Paper"


def test_semantic_scholar_raises_after_max_retries():
    """Should raise after 3 failed attempts."""
    def always_429(*args, **kwargs):
        resp = MagicMock()
        resp.status_code = 429
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429", request=MagicMock(), response=resp
        )
        return resp

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: s
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = always_429
        mock_client_cls.return_value = mock_client

        with patch("time.sleep"):
            with pytest.raises(httpx.HTTPStatusError):
                search_semantic_scholar("machine learning testing", 10)


def test_arxiv_returns_normalized_papers():
    """search_arxiv should return papers with the standard schema."""
    mock_xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/1906.10742v2</id>
        <title>Machine learning testing: Survey, landscapes and horizons</title>
        <author><name>Jie M. Zhang</name></author>
        <author><name>Mark Harman</name></author>
        <summary>Abstract here.</summary>
        <published>2020-01-15T00:00:00Z</published>
        <link href="http://arxiv.org/pdf/1906.10742v2" title="pdf" type="application/pdf"/>
      </entry>
    </feed>"""

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: s
        mock_client.__exit__ = MagicMock(return_value=False)
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.text = mock_xml
        mock_client.get.return_value = resp
        mock_client_cls.return_value = mock_client

        results = search_arxiv("machine learning testing", 10)

    assert len(results) == 1
    p = results[0]
    assert p["source_module"] == "arxiv"
    assert "Zhang" in p["authors"][0] or "Zhang" in str(p["authors"])
    assert p["year"] == 2020
    assert p["url"] is not None


def test_base_parses_response_and_sends_hits_param():
    """BASE must send 'hits' param and handle array-valued DC fields."""
    mock_payload = {
        "response": {
            "numFound": 1,
            "docs": [{
                "dctitle": ["Machine Learning Testing: Survey and Horizons"],
                "dccreator": ["Zhang, Jie M.", "Harman, Mark"],
                "dcyear": "2020",
                "dcidentifier": ["https://doi.org/10.1016/j.infsof.2022.107007", "other-id"],
                "dcabstract": ["A survey of machine learning testing methods."],
                "dcpublisher": ["Information and Software Technology"],
            }]
        }
    }

    captured_params = {}

    def mock_get(url, params=None, **kwargs):
        captured_params.update(params or {})
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = mock_payload
        return resp

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: s
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = mock_get
        mock_client_cls.return_value = mock_client

        with patch("time.sleep"):
            results = search_base("machine learning testing", 10)

    assert "hits" in captured_params, "BASE search must include 'hits' param or returns 0 results"
    assert captured_params["hits"] == 10
    assert len(results) == 1
    p = results[0]
    assert p["title"] == "Machine Learning Testing: Survey and Horizons"
    assert "Zhang" in p["authors"][0]
    assert p["year"] == 2020
    assert p["source_module"] == "base"
    assert p["doi"] is not None
