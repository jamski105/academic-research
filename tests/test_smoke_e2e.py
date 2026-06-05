"""Ultimativer End-to-End-Smoke-Test für das academic-research-Plugin.

Beweist in EINEM Lauf, dass das Plugin als Ganzes funktioniert — mit Fokus auf
das, was die ~1600 bestehenden Unit-Tests NICHT abdecken: den echten
MCP-Server-PROZESS, echte node-Hook-Subprozesse, Struktur-Integrität und
Script-Importierbarkeit.

Die eigentliche Logik lebt in ``tests/helpers/smoke_core.py`` und wird vom
eigenständigen Reporter ``scripts/smoke.py`` 1:1 wiederverwendet (Single Source
of Truth). Dieser Wrapper exponiert sie als parametrisierte pytest-Cases.

Voraussetzungen (in CI gegeben):
  * ``~/.academic-research/venv/bin/python`` mit installiertem ``mcp``-SDK.
  * ``node`` im PATH (für die Hook-Subprozesse).
"""

import shutil
import sys
from pathlib import Path

import pytest

# Repo-Root + helpers importierbar machen.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.helpers import smoke_core  # noqa: E402

# Harte Voraussetzungen: ohne mcp-SDK / venv-Python / node ist kein E2E möglich.
pytest.importorskip("mcp.client.stdio", reason="mcp-SDK nicht installiert")

if not smoke_core.VENV_PYTHON.exists():
    pytest.skip(
        f"venv-Python fehlt ({smoke_core.VENV_PYTHON}) — /academic-research:setup ausführen",
        allow_module_level=True,
    )

if shutil.which("node") is None:
    pytest.skip("node nicht im PATH — Hooks nicht ausführbar", allow_module_level=True)


# ---------------------------------------------------------------------------
# Geteilter MCP-Round-Trip (genau EIN Server-Start für alle State-Checks).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mcp_state() -> dict:
    """Startet den MCP-Server einmal als Subprozess und führt den vollen
    Daten-Round-Trip aus. Liefert das Ergebnis-State-dict."""
    return smoke_core.run_mcp_roundtrip()


# ---------------------------------------------------------------------------
# A) + C-3) State-abhängige Checks (MCP-Lifecycle + Tool-3-Wege-Konsistenz).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "category,name,check",
    smoke_core.stateful_checks(),
    ids=[f"{c}::{n}" for c, n, _ in smoke_core.stateful_checks()],
)
def test_stateful(category, name, check, mcp_state):
    check(mcp_state)


# ---------------------------------------------------------------------------
# B) + C) + D) State-unabhängige Checks (Hooks, Struktur, Scripts).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "category,name,check",
    smoke_core.plain_checks(),
    ids=[f"{c}::{n}" for c, n, _ in smoke_core.plain_checks()],
)
def test_plain(category, name, check):
    check()
