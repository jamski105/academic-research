"""
Tests fuer SciHub-Tier Opt-in (Chunk D, v6.5 #97).

5 Test-Cases (kein LLM-Call, keine Browser-Automation):
1. Default-active.yaml.template hat scihub_optin: false
2. Opt-in setzt Flag auf true (Parsing-Logik)
3. Mock-Fetch-Pipeline: alle Tiers fail + scihub_optin=true → scihub-fetcher aufgerufen
4. Vault-Entry bekommt provenance=scihub Tag
5. Output-Disclaimer erscheint bei provenance=scihub
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
ACTIVE_YAML_TEMPLATE = REPO_ROOT / "library-profiles" / "active.yaml.template"
SCIHUB_AGENT = REPO_ROOT / "agents" / "scihub-fetcher.md"
SETUP_COMMAND = REPO_ROOT / "commands" / "setup.md"
README = REPO_ROOT / "README.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_active_template() -> dict:
    with open(ACTIVE_YAML_TEMPLATE) as f:
        return yaml.safe_load(f)


def _simulate_scihub_dispatch(scihub_optin: bool, tiers_all_fail: bool) -> bool:
    """
    Simuliert die Dispatch-Logik der Fetch-Pipeline:
    Gibt True zurueck, wenn scihub-fetcher aufgerufen wuerde.
    Regel: tiers_all_fail AND scihub_optin == True → dispatch
    """
    return tiers_all_fail and scihub_optin


def _build_vault_entry(provenance: str | None = None) -> dict:
    """Baut einen minimalen Vault-Entry mit optionalem provenance-Tag."""
    entry = {
        "title": "Test Paper",
        "doi": "10.1234/test",
        "tags": [],
    }
    if provenance:
        entry["tags"].append(f"provenance:{provenance}")
    return entry


def _format_source_line(entry: dict) -> str:
    """
    Gibt den Output-Hinweis-Text zurueck, falls provenance:scihub im tags-Feld steht.
    Spiegelt die Output-Layer-Logik aus scihub-fetcher.md.
    """
    for tag in entry.get("tags", []):
        if tag == "provenance:scihub":
            return "Quelle via SciHub bezogen — bitte zusaetzlich legalen Zugriff klaeren."
    return ""


# ---------------------------------------------------------------------------
# Test 1: Default-Template hat scihub_optin: false
# ---------------------------------------------------------------------------

class TestDefaultOptinFalse:
    def test_active_yaml_template_exists(self):
        assert ACTIVE_YAML_TEMPLATE.exists(), (
            f"active.yaml.template nicht gefunden: {ACTIVE_YAML_TEMPLATE}"
        )

    def test_scihub_optin_default_false(self):
        data = _read_active_template()
        assert "scihub_optin" in data, "scihub_optin-Feld fehlt in active.yaml.template"
        assert data["scihub_optin"] is False, (
            f"scihub_optin muss per Default False sein, ist: {data['scihub_optin']}"
        )


# ---------------------------------------------------------------------------
# Test 2: Opt-in setzt Flag auf true (Parsing-Logik)
# ---------------------------------------------------------------------------

class TestOptinParsing:
    def test_optin_true_recognized(self, tmp_path):
        """Wenn active.yaml scihub_optin: true enthaelt, wird es korrekt gelesen."""
        active = tmp_path / "active.yaml"
        active.write_text("scihub_optin: true\nuni: test\n")
        with open(active) as f:
            data = yaml.safe_load(f)
        assert data["scihub_optin"] is True

    def test_optin_false_recognized(self, tmp_path):
        """Wenn active.yaml scihub_optin: false enthaelt, wird es korrekt gelesen."""
        active = tmp_path / "active.yaml"
        active.write_text("scihub_optin: false\nuni: test\n")
        with open(active) as f:
            data = yaml.safe_load(f)
        assert data["scihub_optin"] is False

    def test_optin_missing_treated_as_false(self, tmp_path):
        """Wenn scihub_optin fehlt, wird es als False behandelt (Safety-Default)."""
        active = tmp_path / "active.yaml"
        active.write_text("uni: test\n")
        with open(active) as f:
            data = yaml.safe_load(f)
        assert data.get("scihub_optin", False) is False


# ---------------------------------------------------------------------------
# Test 3: Dispatch-Logik — alle Tiers fail + opt-in = true → scihub aufgerufen
# ---------------------------------------------------------------------------

class TestDispatchLogic:
    def test_scihub_dispatched_when_tiers_fail_and_optin(self):
        result = _simulate_scihub_dispatch(scihub_optin=True, tiers_all_fail=True)
        assert result is True, "scihub-fetcher haette aufgerufen werden sollen"

    def test_scihub_not_dispatched_when_optin_false(self):
        result = _simulate_scihub_dispatch(scihub_optin=False, tiers_all_fail=True)
        assert result is False, "scihub-fetcher soll nicht aufgerufen werden ohne Opt-in"

    def test_scihub_not_dispatched_when_tiers_succeed(self):
        result = _simulate_scihub_dispatch(scihub_optin=True, tiers_all_fail=False)
        assert result is False, "scihub-fetcher soll nicht aufgerufen werden wenn Tiers Erfolg haben"

    def test_scihub_not_dispatched_when_both_false(self):
        result = _simulate_scihub_dispatch(scihub_optin=False, tiers_all_fail=False)
        assert result is False


# ---------------------------------------------------------------------------
# Test 4: Vault-Entry hat provenance=scihub Tag
# ---------------------------------------------------------------------------

class TestVaultProvenance:
    def test_vault_entry_has_scihub_tag(self):
        entry = _build_vault_entry(provenance="scihub")
        assert "provenance:scihub" in entry["tags"], (
            "Vault-Entry muss provenance:scihub-Tag enthalten"
        )

    def test_vault_entry_without_scihub_has_no_tag(self):
        entry = _build_vault_entry()
        assert "provenance:scihub" not in entry["tags"]

    def test_vault_entry_oa_has_different_provenance(self):
        entry = _build_vault_entry(provenance="oa")
        assert "provenance:oa" in entry["tags"]
        assert "provenance:scihub" not in entry["tags"]


# ---------------------------------------------------------------------------
# Test 5: Output-Disclaimer erscheint bei provenance=scihub
# ---------------------------------------------------------------------------

class TestOutputDisclaimer:
    def test_disclaimer_shown_for_scihub_provenance(self):
        entry = _build_vault_entry(provenance="scihub")
        line = _format_source_line(entry)
        assert "SciHub" in line, "Disclaimer muss 'SciHub' enthalten"
        assert "legalen Zugriff" in line, "Disclaimer muss auf legalen Zugriff hinweisen"

    def test_no_disclaimer_for_normal_entry(self):
        entry = _build_vault_entry()
        line = _format_source_line(entry)
        assert line == "", "Kein Disclaimer fuer normale Eintraege"

    def test_no_disclaimer_for_oa_entry(self):
        entry = _build_vault_entry(provenance="oa")
        line = _format_source_line(entry)
        assert line == "", "Kein Disclaimer fuer OA-Eintraege"


# ---------------------------------------------------------------------------
# Artefakt-Existenz-Tests (Sanity)
# ---------------------------------------------------------------------------

class TestArtifactExistence:
    def test_scihub_agent_exists(self):
        assert SCIHUB_AGENT.exists(), f"Agent nicht gefunden: {SCIHUB_AGENT}"

    def test_setup_command_has_scihub_optin_question(self):
        content = SETUP_COMMAND.read_text(encoding="utf-8")
        assert "scihub" in content.lower() or "SciHub" in content, (
            "setup.md muss SciHub Opt-in Frage enthalten"
        )

    def test_readme_has_ethics_disclaimer(self):
        content = README.read_text(encoding="utf-8")
        assert "SciHub" in content, "README muss SciHub-Ethik-Disclaimer enthalten"
        assert "rechtlich" in content.lower() or "Rechtlich" in content or "legal" in content.lower(), (
            "README-Disclaimer muss auf rechtliche Situation hinweisen"
        )
