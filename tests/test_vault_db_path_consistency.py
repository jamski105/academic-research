"""Tests fuer Issue #190 — vault.db-Pfad-Konsistenz.

Stellt sicher:
  (a) .gitignore (Repo-Wurzel) UND das Bootstrap-Fragment ignorieren *.db / vault.db,
      damit keine Forschungs-PII versehentlich committet wird (CWE-538).
  (b) Es gibt genau EINE kanonische Quelle der Wahrheit fuer den DB-Default:
      academic_vault.db.default_db_path(). Der MCP-Server (server.py) leitet
      seinen Default davon ab, und der Default zeigt NICHT mehr ins CWD oder
      ins Plugin-Verzeichnis, sondern nach ~/.academic-research/projects/<slug>/vault.db.

TDD: Diese Tests schlagen gegen den Zustand auf origin/main fehl, weil dort
weder .gitignore noch das Fragment *.db ignorieren und es keine zentrale
default_db_path()-Funktion gibt (server.py:19 nutzt hart "vault.db" im CWD).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# (a) .gitignore — vault.db / *.db duerfen nicht ins Repo gelangen
# ---------------------------------------------------------------------------

def _matches_db_pattern(lines: list[str]) -> bool:
    """True, wenn irgendeine .gitignore-Zeile vault.db bzw. *.db erfasst."""
    db_patterns = {"*.db", "vault.db", "**/*.db", "*.db*"}
    return any(ln.strip() in db_patterns for ln in lines)


def test_repo_gitignore_ignores_db_files():
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore fehlt in der Repo-Wurzel"
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert _matches_db_pattern(lines), (
        ".gitignore muss ein Pattern enthalten, das vault.db/*.db ignoriert "
        "(Forschungs-PII darf nicht committet werden — CWE-538)."
    )


def test_bootstrap_gitignore_fragment_ignores_db_files():
    fragment = REPO_ROOT / "scripts" / "bootstrap" / "gitignore.fragment"
    assert fragment.exists(), "bootstrap/gitignore.fragment fehlt"
    lines = fragment.read_text(encoding="utf-8").splitlines()
    assert _matches_db_pattern(lines), (
        "Das Bootstrap-Fragment muss vault.db/*.db ignorieren, damit "
        "bootstrappte Projekte ihre DB nicht versehentlich committen."
    )


# ---------------------------------------------------------------------------
# (b) Single Source of Truth fuer den DB-Default
# ---------------------------------------------------------------------------

def test_canonical_resolver_exists():
    from academic_vault import db

    assert hasattr(db, "default_db_path"), (
        "academic_vault.db muss eine kanonische Resolver-Funktion "
        "default_db_path() exportieren (Single Source of Truth)."
    )


def test_canonical_resolver_respects_env(monkeypatch):
    from academic_vault import db

    monkeypatch.setenv("VAULT_DB_PATH", "/tmp/explicit/vault.db")
    assert db.default_db_path() == "/tmp/explicit/vault.db"


def test_canonical_resolver_default_is_under_home_projects(monkeypatch, tmp_path):
    """Ohne VAULT_DB_PATH liegt der Default unter ~/.academic-research/projects/<slug>/vault.db
    und NICHT im CWD oder im Plugin-Verzeichnis."""
    from academic_vault import db

    monkeypatch.delenv("VAULT_DB_PATH", raising=False)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    workdir = tmp_path / "meine-facharbeit"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    resolved = Path(db.default_db_path())
    expected = fake_home / ".academic-research" / "projects" / "meine-facharbeit" / "vault.db"
    assert resolved == expected, f"erwartet {expected}, war {resolved}"
    # Darf nicht im CWD und nicht im Plugin-Repo liegen
    assert Path(resolved).parent != workdir
    assert REPO_ROOT not in Path(resolved).parents


def test_server_default_derives_from_canonical_resolver(monkeypatch):
    """server.py darf den Default nicht mehr hart als 'vault.db' (CWD) setzen,
    sondern muss ihn aus dem kanonischen Resolver ableiten."""
    src = (REPO_ROOT / "academic_vault" / "server.py").read_text(encoding="utf-8")
    # Kein hart kodierter CWD-Fallback "vault.db" mehr als Default-Quelle.
    assert 'os.environ.get("VAULT_DB_PATH", "vault.db")' not in src, (
        "server.py darf den CWD-Fallback 'vault.db' nicht mehr verwenden; "
        "muss default_db_path() referenzieren."
    )
    assert "default_db_path" in src, (
        "server.py muss die kanonische default_db_path()-Funktion verwenden."
    )
