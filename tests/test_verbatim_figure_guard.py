"""Tests fuer den additiven Figure-Check im verbatim-guard-Hook.

Der Hook wird als Node.js-Subprocess gestartet. JSON auf stdin, Ausgabe auf stdout/stderr.
Exit-Code 0 = allow, Exit-Code 2 = block.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "verbatim-guard.mjs"
WORKTREE_ROOT = Path(__file__).parent.parent


def run_hook(tool_name: str, file_path: str, content: str, env_overrides: dict = None) -> subprocess.CompletedProcess:
    """Startet den Hook als Subprocess mit JSON-Eingabe auf stdin."""
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {
            "file_path": file_path,
            "content": content,
        }
    })
    env = os.environ.copy()
    # Vault-DB-Pfad auf nicht-existierende DB setzen (fail-open Tests)
    env["VAULT_DB_PATH"] = str(WORKTREE_ROOT / "nonexistent_vault_for_tests.db")
    if env_overrides:
        env.update(env_overrides)

    return subprocess.run(
        ["node", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


@pytest.fixture
def vault_with_figure(tmp_path):
    """Erstellt temporaere Vault-DB mit einem Figure-Eintrag."""
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper, add_figure

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="test-paper",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )
    add_figure(
        db_path=db_path,
        paper_id="test-paper",
        page=3,
        caption="Abb. 3.4: Ergebnisse der Messung",
        vlm_description="Balkendiagramm mit fuenf Experimenten.",
        data_extracted=None,
    )
    return db_path


def test_hook_failopen_when_vault_missing():
    """Hook erlaubt (fail-open) wenn Vault-DB nicht existiert."""
    content = 'In Abb. 3.4 sieht man deutlich, dass der Wert steigt.'
    result = run_hook("Write", "kapitel/kap1.md", content)
    # fail-open → exit 0
    assert result.returncode == 0, f"Erwartet 0 (fail-open), got {result.returncode}. stderr: {result.stderr}"


def test_hook_ignores_non_protected_path():
    """Hook ignoriert Pfade die nicht geschuetzt sind."""
    content = 'In Abb. 3.4 ist ein Diagramm dargestellt.'
    result = run_hook("Write", "README.md", content)
    assert result.returncode == 0


def test_hook_non_write_tool_ignored():
    """Hook reagiert nicht auf Nicht-Write-Tools."""
    result = run_hook("Read", "kapitel/kap1.md", "Abb. 3.4 zeigt etwas.")
    assert result.returncode == 0


def test_hook_blocks_unknown_figure_reference(tmp_path):
    """Hook blockiert bei Abb.-Referenz die nicht im Vault ist (Vault existiert, kein Eintrag)."""
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper

    db_path = str(tmp_path / "empty_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="test-paper",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )

    content = 'Wie in Abb. 3.4 gezeigt, ist der Effekt signifikant.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": db_path},
    )
    assert result.returncode == 2, f"Erwartet exit 2 (block), got {result.returncode}. stderr: {result.stderr}"


def test_hook_allows_when_figure_in_vault(vault_with_figure):
    """Hook erlaubt wenn Figure-Caption im Vault gefunden wird (kein Quote-Span, nur Figure-Ref)."""
    # Inhalt ohne Quote-Span, nur Figure-Referenz mit passendem Caption-Fragment
    content = 'Wie in Abb. 3.4 sichtbar, ist der Wert hoch.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": vault_with_figure},
    )
    # Figure ist im Vault -> kein Figure-Block
    assert "[Figure-Guard] BLOCKIERT" not in result.stderr
    assert result.returncode == 0


def test_existing_quote_check_still_works(tmp_path):
    """Regression: bestehende Quote-Pruefung blockiert weiterhin bei unverifizierten Zitaten."""
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper

    db_path = str(tmp_path / "quote_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="paper-001",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )

    # Langer Quote-Span (>10 Zeichen) ohne Vault-Eintrag -> Block
    content = 'Laut dem Autor "Dies ist ein sehr wichtiger Satz aus dem Buch" stimmt das.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": db_path},
    )
    assert result.returncode == 2, f"Erwartet exit 2 (Quote-Block), got {result.returncode}"
