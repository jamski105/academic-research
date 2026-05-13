"""TDD-Tests fuer scripts/page_offset.py.

5 Testfaelle mit synthetischen PDFs (tests/fixtures/page_offset/).
Konvention: Seitenzahl steht als isolierte Zahl als erste Zeile des
extrahierten Textes (reportlab: y=40 = unten, aber pypdf liest
aufsteigend nach y, also erscheint y=40 zuerst).
"""
import sys
from pathlib import Path

import pytest

# scripts/ zum Python-Pfad hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures" / "page_offset"


def _require_fixture(name: str) -> Path:
    p = FIXTURES / name
    if not p.exists():
        pytest.skip(
            f"Fixture fehlt: {p}. "
            "Aufruf: python tests/fixtures/page_offset/create_fixtures.py"
        )
    return p


# ---------------------------------------------------------------------------
# detect_page_offset Tests
# ---------------------------------------------------------------------------

def test_no_preface_offset_zero():
    """Buch ohne Vorwort: offset soll 0 sein (erste PDF-Seite traegt '1')."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("no_preface.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 0, f"Erwartet offset=0, erhalten {offset}"


def test_ten_prefaces_offset_ten():
    """10 Vorseiten: erste arabische '1' auf PDF-Seite 11 (1-basiert) -> offset=10."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 10, f"Erwartet offset=10, erhalten {offset}"


def test_roman_numerals_offset_six():
    """6 roemische Seiten, dann arabisch ab 1 auf PDF-Seite 7 -> offset=6."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("roman_numerals.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 6, f"Erwartet offset=6, erhalten {offset}"


def test_double_pagination_offset_five():
    """5 unnummerierte Seiten, arabisch ab 1 auf PDF-Seite 6 -> offset=5."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("double_pagination.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 5, f"Erwartet offset=5, erhalten {offset}"


def test_large_offset_twenty_five():
    """25 Vorseiten, arabisch ab 1 auf PDF-Seite 26 -> offset=25."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("large_offset.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 25, f"Erwartet offset=25, erhalten {offset}"


# ---------------------------------------------------------------------------
# validate_offset Tests
# ---------------------------------------------------------------------------

def test_validate_offset_stable():
    """validate_offset gibt True zurueck wenn Stichproben konsistent sind."""
    from page_offset import validate_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    # offset=10: PDF-Seite 11 (0-basiert: 10) soll '1' zeigen
    # Stichproben bei PDF-Seiten 11 und 12 (0-basiert: gedruckt 2 und 3)
    result = validate_offset(str(pdf), offset=10, check_pages=[11, 12])
    assert result is True, "validate_offset soll True fuer stabilen Offset zurueckgeben"


def test_validate_offset_wrong_rejects():
    """validate_offset gibt False zurueck wenn Offset falsch ist."""
    from page_offset import validate_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    result = validate_offset(str(pdf), offset=0, check_pages=[11, 12])
    assert result is False, "validate_offset soll False fuer falschen Offset zurueckgeben"


# ---------------------------------------------------------------------------
# Vault-DB Tests
# ---------------------------------------------------------------------------

def test_vault_db_set_get_page_offset():
    """set_page_offset und get_page_offset runden-trip im Vault."""
    import tempfile
    import json

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.db import VaultDB

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    db = VaultDB(db_path)
    db.init_schema()
    csl = json.dumps({"type": "book", "title": "Test"})
    db.add_paper("buch_test_2024", csl)

    db.set_page_offset("buch_test_2024", 12)
    result = db.get_page_offset("buch_test_2024")
    assert result == 12, f"Erwartet 12, erhalten {result}"


def test_vault_db_get_page_offset_missing_returns_zero():
    """get_page_offset gibt 0 zurueck fuer unbekanntes paper_id."""
    import tempfile

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.db import VaultDB

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    db = VaultDB(db_path)
    db.init_schema()
    result = db.get_page_offset("nonexistent_paper")
    assert result == 0, f"Erwartet 0, erhalten {result}"


# ---------------------------------------------------------------------------
# Server-Funktionen Tests
# ---------------------------------------------------------------------------

def test_server_set_and_get_printed_page():
    """set_page_offset + get_printed_page runden-trip via server.py."""
    import tempfile
    import json

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.server import (
        set_page_offset as srv_set_offset,
        get_printed_page,
        add_paper,
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    csl = json.dumps({"type": "book", "title": "Server Test"})
    add_paper(db_path, "server_test_2024", csl)
    srv_set_offset(db_path, "server_test_2024", 10)

    # pdf_page=15 (1-basiert) -> printed_page = 15 - 10 = 5
    result = get_printed_page(db_path, "server_test_2024", pdf_page=15)
    assert result == 5, f"Erwartet 5, erhalten {result}"


def test_server_get_printed_page_zero_offset():
    """get_printed_page mit offset=0 gibt pdf_page unveraendert zurueck."""
    import tempfile
    import json

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.server import get_printed_page, add_paper

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    csl = json.dumps({"type": "book", "title": "Zero Offset Test"})
    add_paper(db_path, "zero_offset_2024", csl)
    # Kein set_page_offset -> offset=0

    result = get_printed_page(db_path, "zero_offset_2024", pdf_page=42)
    assert result == 42, f"Erwartet 42 (kein Offset), erhalten {result}"
