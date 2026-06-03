"""Server-Start-Regressionstests fuer den academic_vault MCP-Server.

Deckt die drei Start-Blocker aus #217 ab:
  - Das Paket muss als Top-Level ``academic_vault`` importierbar sein, ohne
    Namespace-Kollision mit dem installierten ``mcp``-SDK (#217 Ursache 3).
  - ``python -m academic_vault.server`` baut den FastMCP-Server, sobald das
    ``mcp``-SDK installiert ist — ohne RuntimeError "mcp SDK nicht installiert"
    (#217 Ursache 2).
  - Eine ``tools/list``-Anfrage liefert die registrierten ``vault.*``-Tools.
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


def test_package_importable_as_top_level_academic_vault():
    """Paket ist als ``academic_vault.server`` importierbar (kein ``mcp.``-Prefix).

    Schuetzt gegen die Namespace-Kollision mit dem ``mcp``-SDK: solange das
    lokale Paket ``mcp`` hiess, verdeckte das installierte SDK es und
    ``python -m academic_vault.server`` brach mit ModuleNotFoundError ab.
    """
    server = importlib.import_module("academic_vault.server")
    assert hasattr(server, "_build_mcp_server")


def test_server_builds_and_answers_tools_list():
    """Frischer Server-Build beantwortet ``tools/list`` mit den ``vault.*``-Tools.

    Erfordert das ``mcp``-SDK (FastMCP). Ohne SDK liefert ``_build_mcp_server()``
    None und ``python -m academic_vault.server`` bricht mit RuntimeError ab —
    genau der Zustand, den #217 Ursache 2 beschreibt.
    """
    pytest.importorskip("mcp.server.fastmcp")
    server = importlib.import_module("academic_vault.server")

    mcp_server = server._build_mcp_server()
    assert mcp_server is not None, (
        "mcp SDK nicht installiert — setup.sh muss mcp>=1.0 ins venv installieren"
    )

    tools = asyncio.run(mcp_server.list_tools())
    names = {t.name for t in tools}
    assert "vault.search" in names, f"vault.search fehlt in tools/list: {sorted(names)}"
    assert "vault.get_paper" in names
    assert "vault.add_paper" in names
    assert len(names) >= 28, f"Erwartet >=28 Tools, erhielt {len(names)}: {sorted(names)}"
