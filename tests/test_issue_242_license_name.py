"""Regressionstest fuer Issue #242.

Die LICENSE-Datei nannte im Copyright nur den Vornamen 'Jonas' statt des
vollstaendigen Namens 'Jonas Ahler'. Der Copyright-Inhaber im LICENSE muss
dem author.name aus plugin.json entsprechen (Akzeptanzkriterium).
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LICENSE_PATH = REPO_ROOT / "LICENSE"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


def _license_copyright_holder() -> str:
    """Extrahiert den Copyright-Inhaber aus der LICENSE-Zeile."""
    text = LICENSE_PATH.read_text(encoding="utf-8")
    match = re.search(r"Copyright \(c\) \d{4}\s+(.+)", text)
    assert match, "LICENSE enthaelt keine Copyright-Zeile im erwarteten Format"
    return match.group(1).strip()


def test_license_nennt_vollen_namen():
    """Copyright-Zeile muss den vollen Namen 'Jonas Ahler' nennen."""
    assert _license_copyright_holder() == "Jonas Ahler"


def test_license_copyright_entspricht_manifest():
    """Copyright-Inhaber im LICENSE entspricht author.name in plugin.json."""
    manifest_author = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["author"]["name"]
    assert _license_copyright_holder() == manifest_author
