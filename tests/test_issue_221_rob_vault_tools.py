"""Regressionstest fuer Issue #221.

agents/risk-of-bias.md ruft im Workflow vier Vault-MCP-Tools auf
(vault.get_paper, vault.search_quote_text, vault.add_quote,
vault.add_risk_of_bias), deklarierte aber nur `tools: [Read]`. Ohne
Registrierung der MCP-Tools kann der Agent sie nicht aufrufen und die
RoB-Persistenz in den Vault ist blockiert.

Dieser Test kodiert das Akzeptanzkriterium ("risk-of-bias-Agent kann
RoB-Bewertungen in den Vault schreiben"): Jedes im Body genutzte
vault.<tool> muss als `mcp__academic_vault__vault_<tool>` im
tools-Frontmatter deklariert sein. Stil-Vorlage: tests/test_publisher_fetchers.py.
"""
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
AGENT_NAME = "risk-of-bias"

# Vault-Tools, die der Agent im Workflow aktiv aufruft (Schritte 1, 2, 4, 5).
# Mapping vault.<tool>  ->  mcp__academic_vault__vault_<tool>
# (Server-Name 'academic-vault' aus .mcp.json, Tool-Namen via @mcp.tool in
#  academic_vault/server.py).
REQUIRED_VAULT_TOOLS = [
    "mcp__academic_vault__vault_get_paper",
    "mcp__academic_vault__vault_search_quote_text",
    "mcp__academic_vault__vault_add_quote",
    "mcp__academic_vault__vault_add_risk_of_bias",
]


def _parse_agent_frontmatter(agent_name: str) -> tuple[dict, str]:
    """Parst YAML-Frontmatter und Body eines Agent-Files."""
    agent_path = REPO_ROOT / "agents" / f"{agent_name}.md"
    assert agent_path.exists(), f"Agent-Datei fehlt: {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    assert match, f"Kein gueltiges Frontmatter in {agent_path}"
    fm = yaml.safe_load(match.group(1))
    body = match.group(2)
    return fm, body


def test_frontmatter_includes_required_vault_tools():
    """tools-Frontmatter muss alle vom Workflow genutzten Vault-MCP-Tools deklarieren."""
    fm, _ = _parse_agent_frontmatter(AGENT_NAME)
    tools = fm.get("tools", [])
    assert isinstance(tools, list), f"tools muss eine Liste sein, ist: {type(tools)}"
    missing = [t for t in REQUIRED_VAULT_TOOLS if t not in tools]
    assert not missing, (
        f"{AGENT_NAME}: tools-Frontmatter fehlen Vault-MCP-Tools: {missing}. "
        f"Aktuell deklariert: {tools}"
    )


def test_frontmatter_retains_read_tool():
    """Read-Tool muss erhalten bleiben (Agent liest PDFs via Read)."""
    fm, _ = _parse_agent_frontmatter(AGENT_NAME)
    tools = fm.get("tools", [])
    assert "Read" in tools, f"{AGENT_NAME}: 'Read' fehlt in tools: {tools}"


def test_every_body_vault_call_is_declared():
    """Jeder vault.<tool>-Aufruf im Body (ausser PRISMA-Hinweis) ist deklariert.

    Schuetzt davor, dass kuenftige Workflow-Aenderungen erneut undeklarierte
    Vault-Tools einfuehren. vault.list_risk_of_bias wird ausgenommen, da es im
    PRISMA-Kopplungs-Abschnitt nur beschreibt, was ein *anderer* Skill liest.
    """
    fm, body = _parse_agent_frontmatter(AGENT_NAME)
    tools_str = str(fm.get("tools", []))

    called = set(re.findall(r"vault\.([a-z_]+)", body))
    # Nur Tools, die der Agent selbst aufruft — list_risk_of_bias gehoert zum PRISMA-Reader.
    called.discard("list_risk_of_bias")

    undeclared = sorted(
        t for t in called if f"mcp__academic_vault__vault_{t}" not in tools_str
    )
    assert not undeclared, (
        f"{AGENT_NAME}: im Body genutzte, aber nicht deklarierte Vault-Tools: "
        f"{undeclared}"
    )
