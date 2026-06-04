"""Regressionstest fuer #226.

``supersede_decision`` und ``list_excluded_sources`` sind als Python-Funktionen
implementiert (``server.py`` :369 / :387), waren aber nicht mit
``@mcp.tool(name=...)`` registriert. Damit waren sie ueber MCP nicht via
``tools/list`` sichtbar oder aufrufbar — anders als ihr registriertes
Gegenpaar ``vault.add_excluded_source`` / ``vault.is_excluded``.

Dieser Test kodiert das Akzeptanzkriterium: beide Operationen muessen via
MCP ``tools/list`` sichtbar (und damit aufrufbar) sein.
"""
import asyncio
import importlib
import sys
from pathlib import Path

import pytest

# Repo-Root auf den Pfad, damit `academic_vault` (Top-Level) importierbar ist.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _list_tool_names():
    """Baut den Server und gibt die Menge der registrierten Tool-Namen zurueck."""
    pytest.importorskip("mcp.server.fastmcp")
    server = importlib.import_module("academic_vault.server")
    mcp_server = server._build_mcp_server()
    assert mcp_server is not None, (
        "mcp SDK nicht installiert — setup.sh muss mcp>=1.0 ins venv installieren"
    )
    tools = asyncio.run(mcp_server.list_tools())
    return {t.name for t in tools}


def test_supersede_decision_registered_as_mcp_tool():
    """``vault.supersede_decision`` ist via ``tools/list`` sichtbar (#226)."""
    names = _list_tool_names()
    assert "vault.supersede_decision" in names, (
        f"vault.supersede_decision fehlt in tools/list: {sorted(names)}"
    )


def test_list_excluded_sources_registered_as_mcp_tool():
    """``vault.list_excluded_sources`` ist via ``tools/list`` sichtbar (#226)."""
    names = _list_tool_names()
    assert "vault.list_excluded_sources" in names, (
        f"vault.list_excluded_sources fehlt in tools/list: {sorted(names)}"
    )
