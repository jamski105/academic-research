"""Regressionstest fuer Issue #182.

`.claude-plugin/marketplace.json` muss die Marketplace-Metadaten-Felder
fuehren, die der offizielle Anthropic-Marketplace durchgaengig nutzt:

- Top-Level `$schema`
- Top-Level `description` (nicht-leer)
- pro Plugin `category` = "research"
- pro Plugin `tags` (nicht-leere Liste mit den geforderten Eintraegen)

Zusaetzlich muss die JSON jq-valide / per json.load parsebar bleiben.
"""

import json
from pathlib import Path

import pytest

MARKETPLACE_PATH = (
    Path(__file__).parent.parent / ".claude-plugin" / "marketplace.json"
)

EXPECTED_SCHEMA = "https://anthropic.com/claude-code/marketplace.schema.json"
EXPECTED_CATEGORY = "research"
EXPECTED_TAGS = [
    "academic",
    "vault",
    "literature-review",
    "latex",
    "humanizer",
    "open-access",
]


@pytest.fixture(scope="module")
def manifest() -> dict:
    # Muss valides JSON sein (jq-Aequivalent).
    return json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))


def test_marketplace_is_valid_json(manifest: dict) -> None:
    assert isinstance(manifest, dict)


def test_top_level_schema_present(manifest: dict) -> None:
    assert manifest.get("$schema") == EXPECTED_SCHEMA


def test_top_level_description_present_and_nonempty(manifest: dict) -> None:
    desc = manifest.get("description")
    assert isinstance(desc, str) and desc.strip(), (
        "Top-Level 'description' fehlt oder ist leer"
    )


def test_first_plugin_category_is_research(manifest: dict) -> None:
    plugins = manifest.get("plugins")
    assert isinstance(plugins, list) and plugins, "plugins-Liste fehlt/leer"
    assert plugins[0].get("category") == EXPECTED_CATEGORY


def test_first_plugin_tags_match_acceptance(manifest: dict) -> None:
    plugins = manifest.get("plugins")
    assert isinstance(plugins, list) and plugins, "plugins-Liste fehlt/leer"
    tags = plugins[0].get("tags")
    assert isinstance(tags, list) and tags, "plugins[0].tags fehlt oder ist leer"
    assert tags == EXPECTED_TAGS, f"tags weichen ab: {tags!r}"
