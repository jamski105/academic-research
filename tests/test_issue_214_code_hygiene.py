"""Regressionstest fuer Issue #214 (Code-Hygiene-Buendel, verbleibender Scope).

Deckt die beiden offenen Sub-Items ab:

* L3 — SQL ``LIKE``-Suchen in ``academic_vault/db.py`` muessen ``%`` und ``_``
  im User-Input literal behandeln (``ESCAPE``-Klausel + ``escape_like``-Helper),
  damit Sonderzeichen das Suchverhalten nicht still veraendern.
* Doc LOW — README-Pfade: Test-Pfade mit ``tests/``-Prefix und Output-Pfade als
  User-Projekt-Output (``<projekt>/...``) markiert.

L1 (Hook execFileSync) und L2 (tar-Portabilitaet) wurden laut Scope-Update
2026-06-03 bereits behoben und sind hier nicht erneut Gegenstand.
"""
import re
import sys
import uuid
from pathlib import Path

import pytest

_WORKTREE_ROOT = Path(__file__).parent.parent
if str(_WORKTREE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_ROOT))

_DB_SRC_PATH = _WORKTREE_ROOT / "academic_vault" / "db.py"
_README_PATH = _WORKTREE_ROOT / "README.md"

try:
    from academic_vault.db import VaultDB

    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _seed_quote(db: VaultDB, verbatim: str) -> tuple[str, str]:
    """Legt ein Paper + Quote mit gegebenem verbatim an. Gibt (paper_id, quote_id)."""
    paper_id = "p_" + uuid.uuid4().hex[:8]
    quote_id = "q_" + uuid.uuid4().hex[:8]
    db.add_paper(paper_id=paper_id, csl_json='{"type": "article-journal"}')
    db.add_quote(
        quote_id=quote_id,
        paper_id=paper_id,
        verbatim=verbatim,
        extraction_method="manual",
    )
    return paper_id, quote_id


# ---------------------------------------------------------------------------
# L3 — escape_like-Helper + ESCAPE-Klausel
# ---------------------------------------------------------------------------

def test_escape_like_helper_exists_and_escapes_wildcards():
    """Es gibt einen importierbaren escape_like-Helper, der %, _ und \\ escaped."""
    from academic_vault import db as db_mod

    assert hasattr(db_mod, "escape_like"), (
        "academic_vault.db braucht einen escape_like-Helper fuer LIKE-Patterns"
    )
    esc = db_mod.escape_like
    # Backslash zuerst, dann Wildcards -> jeweils mit Backslash escaped.
    assert esc("a%b") == r"a\%b"
    assert esc("a_b") == r"a\_b"
    assert esc(r"a\b") == r"a\\b"
    # Reihenfolge: erst Backslash, sonst doppeltes Escaping von schon-Escaptem.
    assert esc(r"50\_%") == r"50\\\_\%"


def test_like_queries_use_escape_clause():
    """Alle LIKE-Suchen in db.py tragen eine ESCAPE-Klausel im SQL."""
    src = _DB_SRC_PATH.read_text(encoding="utf-8")
    # Jede LIKE ?-Stelle muss von einer ESCAPE-Klausel begleitet sein.
    like_count = len(re.findall(r"LIKE\s+\?", src))
    escape_count = len(re.findall(r"LIKE\s+\?\s+ESCAPE\s+", src))
    assert like_count > 0, "Erwartete mindestens eine LIKE ?-Suche in db.py"
    assert escape_count == like_count, (
        f"{like_count} LIKE ?-Stellen, aber nur {escape_count} mit ESCAPE-Klausel"
    )


def _open_db(tmp_path) -> VaultDB:
    """Oeffnet eine frische VaultDB mit initialisiertem Schema (Context-Manager)."""
    db = VaultDB(str(tmp_path / "vault.db"))
    db.__enter__()
    db.init_schema()
    return db


@pytest.mark.skipif(not _DB_AVAILABLE, reason="academic_vault.db nicht importierbar")
def test_search_quote_text_treats_percent_literally(tmp_path):
    """'%' im Such-Input matcht nur literale '%', nicht beliebige Zeichen."""
    db = _open_db(tmp_path)
    try:
        _seed_quote(db, "Ergebnis 50% signifikant")
        _seed_quote(db, "Ergebnis 50A signifikant")

        # Literale Prozent-Suche darf NUR die echte 50%-Zeile finden.
        hits = db.search_quote_text("50%")
        verbatims = {h["verbatim"] for h in hits}
        assert "Ergebnis 50% signifikant" in verbatims
        assert "Ergebnis 50A signifikant" not in verbatims
    finally:
        db.__exit__(None, None, None)


@pytest.mark.skipif(not _DB_AVAILABLE, reason="academic_vault.db nicht importierbar")
def test_search_quote_text_treats_underscore_literally(tmp_path):
    """'_' im Such-Input matcht nur literalen Unterstrich, nicht ein Wildcard-Zeichen."""
    db = _open_db(tmp_path)
    try:
        _seed_quote(db, "var_name = 1")
        _seed_quote(db, "varXname = 1")

        hits = db.search_quote_text("var_name")
        verbatims = {h["verbatim"] for h in hits}
        assert "var_name = 1" in verbatims
        assert "varXname = 1" not in verbatims
    finally:
        db.__exit__(None, None, None)


@pytest.mark.skipif(not _DB_AVAILABLE, reason="academic_vault.db nicht importierbar")
def test_find_figures_by_caption_treats_wildcards_literally(tmp_path):
    """find_figures_by_caption behandelt % literal (kein Silent-Wildcard)."""
    db = _open_db(tmp_path)
    try:
        paper_id = "p_" + uuid.uuid4().hex[:8]
        db.add_paper(paper_id=paper_id, csl_json='{"type": "article-journal"}')
        db.add_figure(paper_id, 1, "Abbildung 100% Auslastung", None, None)
        db.add_figure(paper_id, 2, "Abbildung 100x Auslastung", None, None)

        hits = db.find_figures_by_caption("100%")
        captions = {h["caption"] for h in hits}
        assert "Abbildung 100% Auslastung" in captions
        assert "Abbildung 100x Auslastung" not in captions
    finally:
        db.__exit__(None, None, None)


# ---------------------------------------------------------------------------
# Doc LOW — README-Pfade
# ---------------------------------------------------------------------------

def test_readme_test_paths_have_tests_prefix():
    """README erwaehnt Test-Dateien mit tests/-Prefix (nicht nackt)."""
    text = _README_PATH.read_text(encoding="utf-8")
    assert "tests/test_skill_naming.py" in text
    assert "tests/test_cross_references.py" in text
    # Nackte Erwaehnung ohne Prefix darf nicht mehr vorkommen.
    assert not re.search(r"(?<!/)\btest_skill_naming\.py", text), (
        "test_skill_naming.py wird noch ohne tests/-Prefix erwaehnt"
    )
    assert not re.search(r"(?<!/)\btest_cross_references\.py", text), (
        "test_cross_references.py wird noch ohne tests/-Prefix erwaehnt"
    )


def test_readme_output_paths_marked_as_project_output():
    """README markiert User-Output-Pfade als <projekt>/... (nicht als Repo-Files)."""
    text = _README_PATH.read_text(encoding="utf-8")
    assert "<projekt>/" in text, (
        "README sollte User-Output-Pfade klar als <projekt>/... markieren"
    )
