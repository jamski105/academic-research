"""Regressionstest fuer Issue #207 — README dokumentiert alle MCP-Tools.

Befund (Doku-Drift): Die README-MCP-Sektion listete nur eine "Auswahl" der
Tools, obwohl `academic_vault/server.py` 28 Tools via `@mcp.tool(name=...)`
registriert. Dieser Test koppelt README und Code: jeder registrierte
Tool-Name muss in der README dokumentiert sein, und die README muss auf die
Code-Referenz `academic_vault/server.py` verlinken.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SERVER_PY = REPO_ROOT / "academic_vault" / "server.py"
README = REPO_ROOT / "README.md"

# Vom Code registrierte Tools sind die autoritative Quelle.
TOOL_NAME_RE = re.compile(r'@mcp\.tool\(name="(vault\.[a-z_]+)"\)')


def _registered_tools() -> list[str]:
    return TOOL_NAME_RE.findall(SERVER_PY.read_text())


def _readme_text() -> str:
    return README.read_text()


def test_registered_tool_count_is_stable() -> None:
    """Sanity-Check: server.py registriert genau 33 MCP-Tools (Drift-Anker).

    Erhoeht sich, wenn neue @mcp.tool dazukommen (zuletzt +5 via #204/#226/#195).
    Bei Aenderung: README-Tabellen UND diese Zahl gemeinsam aktualisieren.
    """
    tools = _registered_tools()
    assert len(tools) == 33, (
        f"Erwartet 33 registrierte @mcp.tool, gefunden {len(tools)}: {tools}"
    )


def test_every_registered_tool_documented_in_readme() -> None:
    """Jeder in server.py registrierte vault.*-Tool steht in der README."""
    readme = _readme_text()
    tools = _registered_tools()
    missing = [t for t in tools if t not in readme]
    assert not missing, (
        f"{len(missing)} registrierte MCP-Tools fehlen in der README: {missing}"
    )


def test_readme_links_to_server_code_reference() -> None:
    """README MCP-Sektion verlinkt auf den Code (academic_vault/server.py)."""
    readme = _readme_text()
    assert "academic_vault/server.py" in readme, (
        "README verlinkt nicht auf die Code-Referenz academic_vault/server.py"
    )


def test_readme_does_not_advertise_unregistered_snapshot_tools() -> None:
    """export_snapshot/restore_snapshot sind KEINE @mcp.tool — duerfen nicht
    als MCP-Tool-Signatur (vault.export_snapshot(...)) ausgegeben werden."""
    readme = _readme_text()
    tools = _registered_tools()
    for ghost in ("vault.export_snapshot", "vault.restore_snapshot"):
        if ghost not in tools:
            assert ghost not in readme, (
                f"README bewirbt nicht-registriertes Tool {ghost} "
                f"(kein @mcp.tool in server.py)"
            )
