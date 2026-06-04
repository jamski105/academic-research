"""Regressionstest fuer Shell-Injection in scripts/export-literature-state.mjs (#218).

Das Skript ruft Python via Node-Subprocess auf. Frueher wurde der Python-Code
als String per ``python3 -c "<interpolierter Code>"`` an die Shell uebergeben,
wobei ``VAULT_DB`` (aus ``VAULT_DB_PATH``) in den Code-String interpoliert und nur
``\\``, ``"`` und ``\\n`` escaped wurden. Backtick und ``$()`` ueberstanden das
Escaping und wurden von der Shell als Command Substitution ausgefuehrt.

Dieser Test setzt ``VAULT_DB_PATH`` auf einen Payload mit ``$()``- und Backtick-
Command-Substitution, die eine Sentinel-Datei anlegen wuerde, und verifiziert,
dass diese Datei NICHT entsteht (kein injizierter Befehl wird ausgefuehrt).

Gegen die verwundbare Version schlaegt der Test fehl (Sentinel wird angelegt),
nach dem Fix ist er gruen.
"""
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "export-literature-state.mjs"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node nicht verfuegbar"
)


def _run_export(vault_db_path: str, cwd: Path) -> subprocess.CompletedProcess:
    """Startet das Export-Skript als Node-Subprocess mit gesetztem VAULT_DB_PATH."""
    env = os.environ.copy()
    env["VAULT_DB_PATH"] = vault_db_path
    return subprocess.run(
        ["node", str(SCRIPT_PATH), "--output", str(cwd / "literature_state.md")],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_vault_db_path_command_substitution_does_not_execute():
    """Backtick/``$()``-Payload in VAULT_DB_PATH darf keinen Befehl ausfuehren."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        sentinel = tmpdir / f"PWNED_{uuid.uuid4().hex}"
        assert not sentinel.exists()
        # Sentinel-Pfad enthaelt keine Sonderzeichen (mktemp/TemporaryDirectory),
        # damit der Payload nicht durch das (verwundbare) Escaping zerstoert wird.
        assert "'" not in str(sentinel) and " " not in str(sentinel)

        # Payload nutzt sowohl $() als auch Backtick-Command-Substitution.
        payload = f"vault.db$(touch {sentinel})`touch {sentinel}`"

        result = _run_export(payload, tmpdir)

        assert not sentinel.exists(), (
            "Shell-Injection: VAULT_DB_PATH-Payload hat einen Befehl ausgefuehrt "
            f"(Sentinel {sentinel} wurde angelegt).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def test_vault_db_path_semicolon_payload_does_not_execute():
    """Auch ein ``;``-getrennter Payload darf keinen Befehl ausfuehren."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        sentinel = tmpdir / f"PWNED_{uuid.uuid4().hex}"
        assert not sentinel.exists()
        assert "'" not in str(sentinel) and " " not in str(sentinel)

        payload = f"/tmp/x; touch {sentinel}"

        _run_export(payload, tmpdir)

        assert not sentinel.exists(), (
            "Shell-Injection: ;-getrennter VAULT_DB_PATH-Payload wurde ausgefuehrt "
            f"(Sentinel {sentinel} wurde angelegt)."
        )


def test_node_syntax_check_passes():
    """``node --check`` muss fuer das Skript gruen bleiben (CI-Spiegelung)."""
    result = subprocess.run(
        ["node", "--check", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"node --check fehlgeschlagen: {result.stderr}"
    )
