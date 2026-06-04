"""Regressionstest fuer Issue #215 — Dev-UX-Buendel (M1+L1+L2+M4).

Prueft die vier Akzeptanzkriterien aus dem Issue konkret als Datei-Existenz,
Datei-Inhalt und valides YAML:

- M1: docs/SKIP_REASONS.md mit Reason-Tabelle (Test -> Reason -> permanent/todo).
- L1: pytest-cov in requirements-dev.txt; CI emittet coverage.xml; Codecov-Badge in README.
- L2: .github/dependabot.yml fuer pip + npm/github-actions, valides YAML.
- M4: .github/workflows/release.yml prueft plugin.json==Tag UND
      marketplace.json.plugins[0].version == plugin.json.version, valides YAML.
"""

import json
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).parent.parent


# --------------------------------------------------------------------------- #
# M1 — Skip-Reasons dokumentiert
# --------------------------------------------------------------------------- #
def test_m1_skip_reasons_doc_exists():
    doc = ROOT / "docs" / "SKIP_REASONS.md"
    assert doc.is_file(), "docs/SKIP_REASONS.md fehlt (M1)"


def test_m1_skip_reasons_has_reason_table():
    doc = ROOT / "docs" / "SKIP_REASONS.md"
    text = doc.read_text(encoding="utf-8")
    # Markdown-Tabelle vorhanden
    assert "|" in text and "---" in text, "Keine Markdown-Tabelle in SKIP_REASONS.md"
    low = text.lower()
    assert "reason" in low or "grund" in low, "Spalte Reason/Grund fehlt"
    # Klassifizierung permanent vs. todo
    assert "permanent" in low, "Klassifizierung 'permanent' fehlt"
    assert "todo" in low, "Klassifizierung 'todo' fehlt"


# --------------------------------------------------------------------------- #
# L1 — Coverage / Codecov
# --------------------------------------------------------------------------- #
def test_l1_requirements_dev_has_pytest_cov():
    req = ROOT / "requirements-dev.txt"
    assert req.is_file(), "requirements-dev.txt fehlt (L1)"
    text = req.read_text(encoding="utf-8")
    assert "pytest-cov" in text, "pytest-cov nicht in requirements-dev.txt"


def test_l1_ci_emits_coverage_xml():
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    text = ci.read_text(encoding="utf-8")
    assert "coverage.xml" in text, "CI emittet keinen coverage.xml-Report (L1)"


def test_l1_readme_has_codecov_badge():
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "codecov.io" in text, "Codecov-Badge fehlt im README (L1)"


# --------------------------------------------------------------------------- #
# L2 — Dependabot
# --------------------------------------------------------------------------- #
def test_l2_dependabot_exists_and_valid_yaml():
    dep = ROOT / ".github" / "dependabot.yml"
    assert dep.is_file(), ".github/dependabot.yml fehlt (L2)"
    data = yaml.safe_load(dep.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "dependabot.yml ist kein YAML-Mapping"
    assert data.get("version") == 2, "dependabot version muss 2 sein"
    ecosystems = {
        u.get("package-ecosystem") for u in data.get("updates", [])
    }
    assert "pip" in ecosystems, "dependabot deckt kein pip-Oekosystem ab"
    # npm fuer Node-/hooks-Deps ODER github-actions (Workflows) muss abgedeckt sein
    assert ecosystems & {"npm", "github-actions"}, (
        "dependabot deckt weder npm noch github-actions ab"
    )


# --------------------------------------------------------------------------- #
# M4 — Release-Workflow mit Marketplace-Version-Check
# --------------------------------------------------------------------------- #
def test_m4_release_workflow_exists_and_valid_yaml():
    rel = ROOT / ".github" / "workflows" / "release.yml"
    assert rel.is_file(), ".github/workflows/release.yml fehlt (M4)"
    data = yaml.safe_load(rel.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "release.yml ist kein YAML-Mapping"
    # 'on'-Trigger fuer Tag-Push (PyYAML parst bare 'on' als True)
    trigger = data.get("on", data.get(True))
    assert trigger and "push" in trigger, "release.yml hat keinen push-Trigger"
    assert "tags" in trigger["push"], "release.yml triggert nicht auf Tags"


def test_m4_release_checks_marketplace_version_match():
    rel = ROOT / ".github" / "workflows" / "release.yml"
    text = rel.read_text(encoding="utf-8")
    assert "marketplace.json" in text, (
        "release.yml prueft marketplace.json-Version nicht (M4)"
    )
    # plugin.json-Tag-Check muss weiterhin existieren
    assert "plugin.json" in text, "release.yml prueft plugin.json-Version nicht mehr"


def test_m4_manifest_versions_currently_match():
    """Sanity: marketplace.plugins[0].version == plugin.json.version."""
    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    market = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    assert plugin["version"] == market["plugins"][0]["version"], (
        "plugin.json und marketplace.json Versionen weichen ab"
    )


# --------------------------------------------------------------------------- #
# Globale YAML-Validitaet aller Config-Dateien (Issue: 'YAML valide')
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "relpath",
    [
        ".github/dependabot.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
    ],
)
def test_config_yaml_is_valid(relpath):
    path = ROOT / relpath
    assert path.is_file(), f"{relpath} fehlt"
    # Wirft yaml.YAMLError bei invalidem YAML
    yaml.safe_load(path.read_text(encoding="utf-8"))
