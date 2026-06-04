"""Registrierungstests fuer die Snapshot-MCP-Tools des academic_vault-Servers.

Deckt #204 ab: ``README.md`` dokumentiert ``vault.export_snapshot`` und
``vault.restore_snapshot`` als MCP-Tools, aber die vorhandenen Funktionen
``export_snapshot`` (server.py) und ``restore_snapshot`` waren nicht mit
``@mcp.tool(...)`` registriert. Der Backup-/Restore-Workflow war damit ueber
MCP nicht aufrufbar.

Zwei Test-Ebenen:

* AST-basiert (``test_*_decorated_in_build_block``): introspiziert den
  ``_build_mcp_server``-Registrierungsblock der ``server.py``-Quelle und
  prueft, dass beide Tools mit ``@mcp.tool(name="vault.export_snapshot")``
  bzw. ``...restore_snapshot`` dekoriert sind. Funktioniert ohne installiertes
  ``mcp``-SDK und schlaegt gegen die ungefixte ``server.py`` fehl.
* Laufzeit-basiert (``test_*_in_tools_list``): introspiziert die
  ``tools/list``-Antwort des frisch gebauten FastMCP-Servers, sofern das
  ``mcp``-SDK installiert ist (sonst ``skip``).
"""
import asyncio
import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest

# Repo-Root auf den Pfad, damit `academic_vault` (Top-Level) importierbar ist.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _registered_tool_names_from_source():
    """Liest die ``@mcp.tool(name=...)``-Namen aus dem ``_build_mcp_server``-Block.

    SDK-unabhaengig: parst die Quelle der ``server.py`` per AST und sammelt alle
    String-Literale aus ``name=``-Keywords von ``@mcp.tool(...)``-Dekoratoren
    innerhalb der ``_build_mcp_server``-Funktion.
    """
    server = importlib.import_module("academic_vault.server")
    source = inspect.getsource(server._build_mcp_server)
    tree = ast.parse(source)

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            # Form: @mcp.tool(name="...")
            if not isinstance(deco, ast.Call):
                continue
            func = deco.func
            if not (isinstance(func, ast.Attribute) and func.attr == "tool"):
                continue
            for kw in deco.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    names.add(kw.value.value)
    return names


def _registered_tool_names_from_runtime():
    pytest.importorskip("mcp.server.fastmcp")
    server = importlib.import_module("academic_vault.server")
    mcp_server = server._build_mcp_server()
    assert mcp_server is not None, (
        "mcp SDK nicht installiert — setup.sh muss mcp>=1.0 ins venv installieren"
    )
    tools = asyncio.run(mcp_server.list_tools())
    return {t.name for t in tools}


def test_export_snapshot_decorated_in_build_block():
    """``vault.export_snapshot`` ist im Registrierungsblock dekoriert (#204)."""
    names = _registered_tool_names_from_source()
    assert "vault.export_snapshot" in names, (
        f"vault.export_snapshot nicht als @mcp.tool registriert: {sorted(names)}"
    )


def test_restore_snapshot_decorated_in_build_block():
    """``vault.restore_snapshot`` ist im Registrierungsblock dekoriert (#204)."""
    names = _registered_tool_names_from_source()
    assert "vault.restore_snapshot" in names, (
        f"vault.restore_snapshot nicht als @mcp.tool registriert: {sorted(names)}"
    )


def test_snapshot_tools_in_tools_list():
    """Frisch gebauter Server listet beide Snapshot-Tools (#204).

    Erfordert das ``mcp``-SDK; ohne SDK ``skip``.
    """
    names = _registered_tool_names_from_runtime()
    assert "vault.export_snapshot" in names, (
        f"vault.export_snapshot fehlt in tools/list: {sorted(names)}"
    )
    assert "vault.restore_snapshot" in names, (
        f"vault.restore_snapshot fehlt in tools/list: {sorted(names)}"
    )
