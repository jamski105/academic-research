"""Regressionstest fuer Issue #229.

arXiv-API muss ueber https:// statt http:// angesprochen werden.
Akzeptanzkriterium: Kein http://-Netzwerk-Endpoint mehr in scripts/.

XML-Namespace-URIs (z.B. http://www.w3.org/2005/Atom) und das
DOI-Prefix-Stripping (http://doi.org/) sind keine Netzwerk-Endpoints
und bleiben unveraendert.
"""

import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

# Bekannte, harmlose http://-Vorkommen: XML-Namespace-Identifier und
# DOI-Prefix-Strings. Das sind keine Netzwerk-Endpoints.
_ALLOWED_HTTP = (
    "http://www.w3.org/2005/Atom",
    "http://www.openarchives.org/OAI/2.0/",
    "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "http://purl.org/dc/elements/1.1/",
    "http://www.loc.gov/MARC21/slim",
    "http://www.loc.gov/zing/srw/",
    "http://doi.org/",
)

# Finde http://-URLs, die einen .../api/query- oder export.arxiv.org-Pfad
# enthalten (echte Endpoints).
_ARXIV_HTTP = re.compile(r"http://(?:export\.)?arxiv\.org")


def _iter_http_urls(text: str):
    for match in re.finditer(r"http://[^\s\"'<>)]+", text):
        yield match.group(0)


def test_search_arxiv_uses_https():
    src = (SCRIPTS_DIR / "search.py").read_text(encoding="utf-8")
    assert "https://export.arxiv.org/api/query" in src
    assert "http://export.arxiv.org/api/query" not in src


def test_no_http_arxiv_endpoint_in_scripts():
    for py in SCRIPTS_DIR.rglob("*.py"):
        src = py.read_text(encoding="utf-8")
        assert not _ARXIV_HTTP.search(src), (
            f"{py} enthaelt einen unverschluesselten arXiv-Endpoint (http://)"
        )


def test_no_unexpected_http_endpoint_in_scripts():
    """Kein http://-Netzwerk-Endpoint (ausser bekannten Namespace-/DOI-Strings)."""
    for py in SCRIPTS_DIR.rglob("*.py"):
        src = py.read_text(encoding="utf-8")
        for url in _iter_http_urls(src):
            assert any(url.startswith(allowed) for allowed in _ALLOWED_HTTP), (
                f"{py}: unerwarteter http://-Endpoint {url!r}"
            )
