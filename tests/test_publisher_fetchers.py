"""
Frontmatter-Validierung und Output-Schema-Check fuer Publisher-Fetcher-Agents.
Keine Live-Browser-Calls. Prueft nur Struktur der Agent-Dateien.
"""
import re
from pathlib import Path

import pytest
import yaml

# Absoluter Pfad zum Repo-Root (relativ zu dieser Test-Datei)
REPO_ROOT = Path(__file__).parent.parent

AGENTS = [
    "springer-book",
    "degruyter",
    "nationallizenzen",
    "ebook-central",
]

REQUIRED_FRONTMATTER_KEYS = {"name", "model", "tools", "maxTurns", "browser-guide"}

VALID_STATUSES = {
    "success",
    "pickup_required",
    "captcha",
    "no_match",
    "metadata_only",
}

REQUIRED_TOOL_PATTERNS = [
    r"browser-use",
]

PAYWALL_KEYWORDS = [
    "paywall",
    "login-wall",
    "auth-trigger",
    "auth_required",
    "auth-helper",
]


def _parse_agent_frontmatter(agent_name: str) -> tuple[dict, str]:
    """Parst YAML-Frontmatter und Body eines Agent-Files."""
    agent_path = REPO_ROOT / "agents" / f"{agent_name}.md"
    assert agent_path.exists(), f"Agent-Datei fehlt: {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    # Frontmatter zwischen erstem und zweitem ---
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    assert match, f"Kein gueltiges Frontmatter in {agent_path}"
    fm = yaml.safe_load(match.group(1))
    body = match.group(2)
    return fm, body


@pytest.mark.parametrize("agent_name", AGENTS)
def test_agent_file_exists(agent_name):
    """Jede Agent-Datei muss existieren."""
    agent_path = REPO_ROOT / "agents" / f"{agent_name}.md"
    assert agent_path.exists(), f"Fehlende Agent-Datei: {agent_path}"


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_required_keys(agent_name):
    """Frontmatter muss alle Pflichtfelder enthalten."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    missing = REQUIRED_FRONTMATTER_KEYS - set(fm.keys())
    assert not missing, f"{agent_name}: fehlende Frontmatter-Felder: {missing}"


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_model_is_sonnet(agent_name):
    """Alle Publisher-Fetcher muessen model: sonnet verwenden."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    assert fm.get("model") == "sonnet", (
        f"{agent_name}: model muss 'sonnet' sein, ist '{fm.get('model')}'"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_tools_include_browser_use(agent_name):
    """Tools-Liste muss browser-use enthalten."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    tools = fm.get("tools", [])
    # tools kann Liste von Strings oder String sein
    tools_str = str(tools)
    assert "browser-use" in tools_str, (
        f"{agent_name}: tools muss 'browser-use' enthalten, ist: {tools}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_browser_guide_referenced(agent_name):
    """browser-guide Frontmatter-Feld muss gesetzt sein."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    guide = fm.get("browser-guide", "")
    assert guide, f"{agent_name}: browser-guide Feld fehlt oder leer"
    assert guide.startswith("config/browser_guides/"), (
        f"{agent_name}: browser-guide muss mit 'config/browser_guides/' beginnen, ist: {guide}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_auth_trigger(agent_name):
    """Agent-Body muss Auth-Trigger-Bedingung dokumentieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    body_lower = body.lower()
    found = any(kw in body_lower for kw in PAYWALL_KEYWORDS)
    assert found, (
        f"{agent_name}: Body dokumentiert keinen Auth-Trigger. "
        f"Erwartete eines von: {PAYWALL_KEYWORDS}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_auth_method(agent_name):
    """Agent-Body muss Auth-Methode (HAN/Shibboleth/EZproxy/DFN-AAI) nennen."""
    _, body = _parse_agent_frontmatter(agent_name)
    auth_methods = ["HAN", "Shibboleth", "EZproxy", "DFN-AAI", "oa-only"]
    found = any(method in body for method in auth_methods)
    assert found, (
        f"{agent_name}: Body nennt keine Auth-Methode. Erwartet eines von: {auth_methods}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_references_auth_helper(agent_name):
    """Agent-Body muss auth-helper als Delegations-Ziel referenzieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    assert "auth-helper" in body, (
        f"{agent_name}: Body muss 'auth-helper' als Delegations-Ziel referenzieren"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_contains_valid_status_values(agent_name):
    """Agent-Body muss alle Output-Status-Werte (success/pickup_required/etc.) erwaehnen."""
    _, body = _parse_agent_frontmatter(agent_name)
    # Mindestens 3 der 5 Status-Werte muessen im Body erwaehnt sein
    found = [s for s in VALID_STATUSES if s in body]
    assert len(found) >= 3, (
        f"{agent_name}: Body nennt zu wenige Status-Werte ({found}). "
        f"Erwartet min. 3 aus: {VALID_STATUSES}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_metadata_only_for_missing_license(agent_name):
    """Agent-Body muss metadata_only fuer fehlende Lizenz dokumentieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    assert "metadata_only" in body, (
        f"{agent_name}: Body muss 'metadata_only' als Fallback fuer fehlende Lizenz dokumentieren"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_references_browser_guide(agent_name):
    """Agent-Body muss den config/browser_guides/-Pfad referenzieren."""
    fm, body = _parse_agent_frontmatter(agent_name)
    # Body muss den Pfad 'config/browser_guides/' referenzieren
    assert "browser_guides" in body, (
        f"{agent_name}: Body muss 'browser_guides' (config/browser_guides/-Pfad) referenzieren"
    )


def test_eval_cases_file_exists():
    """evals/publisher-fetchers/evals.json muss existieren."""
    evals_path = REPO_ROOT / "evals" / "publisher-fetchers" / "evals.json"
    assert evals_path.exists(), f"Eval-Datei fehlt: {evals_path}"


def test_eval_cases_structure():
    """evals.json muss valide Struktur haben."""
    import json
    evals_path = REPO_ROOT / "evals" / "publisher-fetchers" / "evals.json"
    if not evals_path.exists():
        pytest.skip("evals.json noch nicht vorhanden")
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    assert "component" in data
    assert "cases" in data
    assert len(data["cases"]) >= 4, "Mindestens 4 Eval-Cases erwartet"
    for case in data["cases"]:
        assert "id" in case
        assert "description" in case
        assert "agent" in case
