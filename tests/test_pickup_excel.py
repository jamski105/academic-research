"""Tests fuer /academic-research:pickup Excel-Generierung.

Abdeckung:
  - scripts.barcode_utils.generate_isbn_barcode: Code128-PNG-Erzeugung
  - scripts.barcode_utils.assign_sheet: availability_status -> Sheet-Mapping
  - scripts.barcode_utils.build_pickup_sheets: Gruppierung aller Eintraege
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "pickup"


# ---------------------------------------------------------------------------
# Barcode-Generierung
# ---------------------------------------------------------------------------

def test_barcode_generates_png():
    """generate_isbn_barcode() erzeugt eine lesbare PNG-Datei."""
    from scripts.barcode_utils import generate_isbn_barcode

    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "barcode.png")
        result = generate_isbn_barcode("9783161484100", output_path=out)

        assert result is not None, "Erwarte Pfad, nicht None"
        assert os.path.exists(result), f"PNG-Datei fehlt: {result}"
        assert result.endswith(".png"), f"Erwartete .png-Endung: {result}"
        assert os.path.getsize(result) > 0, "PNG-Datei ist leer"


def test_barcode_invalid_isbn():
    """generate_isbn_barcode() gibt None zurueck bei leerer ISBN."""
    from scripts.barcode_utils import generate_isbn_barcode

    result = generate_isbn_barcode("")
    assert result is None, f"Erwarte None fuer leere ISBN, bekam: {result}"


def test_barcode_none_isbn():
    """generate_isbn_barcode() gibt None zurueck bei None-Input."""
    from scripts.barcode_utils import generate_isbn_barcode

    result = generate_isbn_barcode(None)
    assert result is None, f"Erwarte None fuer None-Input, bekam: {result}"


# ---------------------------------------------------------------------------
# Sheet-Zuordnung
# ---------------------------------------------------------------------------

def test_sheet_assignment_vor_ort():
    """availability_status=vor_ort_verfuegbar -> Sheet 'Vor Ort verfuegbar'."""
    from scripts.barcode_utils import assign_sheet

    entry = json.loads((FIXTURES / "book_vor_ort.json").read_text())
    assert assign_sheet(entry) == "Vor Ort verfügbar"


def test_sheet_assignment_fernleihe():
    """availability_status=fernleihe -> Sheet 'Fernleihe'."""
    from scripts.barcode_utils import assign_sheet

    entry = json.loads((FIXTURES / "book_fernleihe.json").read_text())
    assert assign_sheet(entry) == "Fernleihe"


def test_sheet_assignment_online_oa():
    """availability_status=online_oa -> Sheet 'Online OA'."""
    from scripts.barcode_utils import assign_sheet

    entry = json.loads((FIXTURES / "paper_online_oa.json").read_text())
    assert assign_sheet(entry) == "Online OA"


def test_sheet_assignment_lizenz():
    """availability_status=lizenz_noetig -> Sheet 'Lizenz noetig'."""
    from scripts.barcode_utils import assign_sheet

    entry = json.loads((FIXTURES / "paper_lizenz.json").read_text())
    assert assign_sheet(entry) == "Lizenz nötig"


def test_no_status_defaults_to_lizenz():
    """Kein availability_status -> Default Sheet 'Lizenz noetig'."""
    from scripts.barcode_utils import assign_sheet

    entry = json.loads((FIXTURES / "thesis_no_status.json").read_text())
    assert "availability_status" not in entry, "Fixture soll keinen Status haben"
    assert assign_sheet(entry) == "Lizenz nötig"


# ---------------------------------------------------------------------------
# Integration: build_pickup_sheets()
# ---------------------------------------------------------------------------

def _load_all_fixtures():
    """Laedt alle 5 Fixture-Dateien."""
    entries = []
    for fname in [
        "book_vor_ort.json",
        "book_fernleihe.json",
        "paper_online_oa.json",
        "paper_lizenz.json",
        "thesis_no_status.json",
    ]:
        entries.append(json.loads((FIXTURES / fname).read_text()))
    return entries


def test_pickup_command_integration():
    """build_pickup_sheets() liefert Dict mit allen 4 Sheet-Namen."""
    from scripts.barcode_utils import build_pickup_sheets

    entries = _load_all_fixtures()
    sheets = build_pickup_sheets(entries)

    expected_sheets = {"Vor Ort verfügbar", "Fernleihe", "Online OA", "Lizenz nötig"}
    assert set(sheets.keys()) == expected_sheets, (
        f"Sheet-Keys passen nicht: {set(sheets.keys())} != {expected_sheets}"
    )


def test_pickup_sheets_correct_assignment():
    """Jeder Eintrag landet im korrekten Sheet."""
    from scripts.barcode_utils import build_pickup_sheets

    entries = _load_all_fixtures()
    sheets = build_pickup_sheets(entries)

    assert len(sheets["Vor Ort verfügbar"]) == 1
    assert len(sheets["Fernleihe"]) == 1
    assert len(sheets["Online OA"]) == 1
    # paper_lizenz + thesis_no_status -> beide landen in "Lizenz nötig"
    assert len(sheets["Lizenz nötig"]) == 2


def test_pickup_sheets_all_entries_covered():
    """Alle 5 Eintraege erscheinen in einem Sheet (keine verloren)."""
    from scripts.barcode_utils import build_pickup_sheets

    entries = _load_all_fixtures()
    sheets = build_pickup_sheets(entries)

    total = sum(len(v) for v in sheets.values())
    assert total == 5, f"Erwartet 5 Eintraege gesamt, bekam {total}"
