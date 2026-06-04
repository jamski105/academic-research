"""
Tests für Issue #166: Manifest-Version 5.4.0 -> 6.5.0 + Description-Sync (28 Skills, v6-Features)

Regressions-Tests, die sicherstellen, dass:
- plugin.json und marketplace.json beide Version 6.5.0 deklarieren
- plugin.json description "28" enthält
- Beide JSON-Dateien valide sind
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def test_plugin_json_version():
    """plugin.json muss Version 6.5.0 deklarieren."""
    data = json.loads(PLUGIN_JSON.read_text())
    version = data["version"]
    assert re.match(r"^6\.5\.", version), (
        f"plugin.json version erwartet ^6.5.x, got '{version}' — "
        "vermutlich noch auf altem Stand (5.4.0)"
    )


def test_marketplace_json_version():
    """marketplace.json plugins[0].version muss 6.5.0 deklarieren."""
    data = json.loads(MARKETPLACE_JSON.read_text())
    version = data["plugins"][0]["version"]
    assert re.match(r"^6\.5\.", version), (
        f"marketplace.json plugins[0].version erwartet ^6.5.x, got '{version}' — "
        "vermutlich noch auf altem Stand (5.4.0)"
    )


def test_plugin_json_description_mentions_28_skills():
    """plugin.json description soll '28' Skills nennen, nicht '13'."""
    data = json.loads(PLUGIN_JSON.read_text())
    description = data["description"]
    assert "28" in description, (
        f"plugin.json description enthält nicht '28': '{description}'"
    )


def test_plugin_json_version_matches_marketplace():
    """Beide Manifeste müssen exakt dieselbe version tragen."""
    plugin_data = json.loads(PLUGIN_JSON.read_text())
    marketplace_data = json.loads(MARKETPLACE_JSON.read_text())
    plugin_version = plugin_data["version"]
    marketplace_version = marketplace_data["plugins"][0]["version"]
    assert plugin_version == marketplace_version, (
        f"Versions-Diskrepanz: plugin.json='{plugin_version}', "
        f"marketplace.json='{marketplace_version}'"
    )


def test_plugin_json_keywords_contain_vault():
    """plugin.json keywords sollen 'vault' enthalten (Issue #166 AC)."""
    data = json.loads(PLUGIN_JSON.read_text())
    keywords = data.get("keywords", [])
    assert "vault" in keywords, (
        f"'vault' fehlt in plugin.json keywords: {keywords}"
    )


def test_plugin_json_keywords_contain_latex():
    """plugin.json keywords sollen 'latex' enthalten (Issue #166 AC)."""
    data = json.loads(PLUGIN_JSON.read_text())
    keywords = data.get("keywords", [])
    assert "latex" in keywords, (
        f"'latex' fehlt in plugin.json keywords: {keywords}"
    )


def test_plugin_json_valid_json():
    """plugin.json muss valides JSON sein."""
    try:
        json.loads(PLUGIN_JSON.read_text())
    except json.JSONDecodeError as e:
        raise AssertionError(f"plugin.json ist kein valides JSON: {e}")


def test_marketplace_json_valid_json():
    """marketplace.json muss valides JSON sein."""
    try:
        json.loads(MARKETPLACE_JSON.read_text())
    except json.JSONDecodeError as e:
        raise AssertionError(f"marketplace.json ist kein valides JSON: {e}")
