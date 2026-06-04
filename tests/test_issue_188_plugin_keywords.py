"""Regressionstest fuer Issue #188: plugin.json keywords v5-veraltet.

Die `keywords` in `.claude-plugin/plugin.json` waren v5-zentriert und
enthielten keine v6-Hauptfeatures. Dieser Test stellt sicher, dass die
laut Akzeptanzkriterien geforderten v6-Begriffe vorhanden sind und das
Manifest weiterhin valides JSON bleibt.
"""

import json
from pathlib import Path

import pytest

PLUGIN_JSON = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"

# Laut Akzeptanzkriterien geforderte neue v6-Keywords.
REQUIRED_V6_KEYWORDS = [
    "vault",
    "latex",
    "bibtex",
    "humanizer",
    "book-fetcher",
    "open-access",
    "prisma",
    "meta-analysis",
    "risk-of-bias",
]


def _keywords() -> list[str]:
    data = json.loads(PLUGIN_JSON.read_text())
    return data["keywords"]


def test_plugin_json_is_valid_json() -> None:
    """Das Manifest muss jq-valides JSON bleiben."""
    data = json.loads(PLUGIN_JSON.read_text())
    assert isinstance(data.get("keywords"), list)


@pytest.mark.parametrize("keyword", REQUIRED_V6_KEYWORDS)
def test_v6_keyword_present(keyword: str) -> None:
    """Jedes geforderte v6-Keyword muss in keywords vorhanden sein."""
    keywords = _keywords()
    assert keyword in keywords, (
        f"v6-Keyword '{keyword}' fehlt in plugin.json keywords: {keywords}"
    )


def test_legacy_core_keywords_preserved() -> None:
    """Bestehende Kern-Keywords duerfen nicht verloren gehen."""
    keywords = _keywords()
    for kw in ("academic", "research", "papers", "citations"):
        assert kw in keywords, f"Bestehendes Keyword '{kw}' wurde entfernt"


def test_keywords_unique() -> None:
    """Keine Duplikate in keywords."""
    keywords = _keywords()
    assert len(keywords) == len(set(keywords)), (
        f"Duplikate in keywords: {keywords}"
    )
