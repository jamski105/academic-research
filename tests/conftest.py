"""Zentrale pytest-Fixtures fuer die academic-research-Testsuite (Issue #183).

Bisher hatte tests/ kein conftest.py; haeufig genutzte Bausteine (Repo-Root auf
sys.path, temporaere Vault-DB, browser-use-Mock, Beispiel-PDF, TUM-Bibliotheks-
profil) waren in einzelnen test_*.py dupliziert. Diese Datei zentralisiert sie,
ohne bestehende Tests zu veraendern -- die Fixtures sind rein additiv.

Bereitgestellte Fixtures:
  - temp_vault_db        Pfad auf eine frisch initialisierte SQLite-Vault-DB
  - mock_browser_use     MagicMock als Ersatz fuer browser-use-Aufrufe
  - sample_pdf           Pfad auf tests/fixtures/sample_book.pdf
  - library_profile_tum  geparstes config/library-profiles/tum.yaml als dict
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Pfade: Repo-Root auf sys.path, damit `academic_vault`/`scripts` importierbar
# sind. Dieser Block war zuvor in ~30 test_*.py dupliziert.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LIBRARY_PROFILES_DIR = REPO_ROOT / "config" / "library-profiles"


# ---------------------------------------------------------------------------
# Vault-DB
# ---------------------------------------------------------------------------
@pytest.fixture
def temp_vault_db(tmp_path):
    """Frisch initialisierte SQLite-Vault-DB in einem Tempdir.

    Liefert den Pfad (str) auf die DB-Datei mit bereits ausgefuehrtem
    `init_schema()`. Faellt auf ein nacktes sqlite-Setup zurueck, falls
    `academic_vault.db` (noch) nicht importierbar ist, damit Tests, die nur
    eine leere DB-Datei brauchen, die Fixture trotzdem nutzen koennen.
    """
    db_path = tmp_path / "vault.db"
    try:
        from academic_vault.db import VaultDB
    except Exception:
        # Fallback: leere DB-Datei ohne Schema (z.B. wenn sqlite-Extensions fehlen)
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.close()
        return str(db_path)

    db = VaultDB(str(db_path))
    db.init_schema()
    return str(db_path)


# ---------------------------------------------------------------------------
# browser-use-Mock
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_browser_use():
    """MagicMock als Ersatz fuer browser-use-Interaktionen.

    Verhindert echte Browser-Automation in Unit-Tests. `.run(...)` liefert
    standardmaessig einen leeren Erfolgs-String; einzelne Tests koennen
    Rueckgabewerte/Seiteneffekte ueber den Mock konfigurieren.
    """
    mock = MagicMock(name="browser_use")
    mock.run.return_value = ""
    mock.navigate.return_value = ""
    mock.extract.return_value = {}
    return mock


# ---------------------------------------------------------------------------
# Beispiel-PDF
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_pdf():
    """Pfad auf eine kleine, echte Beispiel-PDF (tests/fixtures/sample_book.pdf)."""
    pdf_path = FIXTURES_DIR / "sample_book.pdf"
    if not pdf_path.is_file():
        pytest.skip(f"Beispiel-PDF fehlt: {pdf_path}")
    return pdf_path


# ---------------------------------------------------------------------------
# Bibliotheksprofil TUM
# ---------------------------------------------------------------------------
@pytest.fixture
def library_profile_tum():
    """Geparstes TUM-Bibliotheksprofil (config/library-profiles/tum.yaml) als dict."""
    import yaml

    profile_path = LIBRARY_PROFILES_DIR / "tum.yaml"
    if not profile_path.is_file():
        pytest.skip(f"TUM-Profil fehlt: {profile_path}")
    with open(profile_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
