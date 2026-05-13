"""Schema-Validation fuer evals/book-handler/evals.json -- kein API-Call."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

EVALS_FILE = Path(__file__).parent.parent.parent / "evals" / "book-handler" / "evals.json"

REQUIRED_CASE_FIELDS = {"id", "description", "type", "input", "expected"}
EXPECTED_IDS = {"bh-01", "bh-02", "bh-03", "bh-04", "bh-05"}


def _load() -> dict:
    if not EVALS_FILE.exists():
        pytest.skip(f"evals.json fehlt: {EVALS_FILE}")
    return json.loads(EVALS_FILE.read_text())


def test_evals_file_exists():
    assert EVALS_FILE.exists(), f"Datei fehlt: {EVALS_FILE}"


def test_exactly_five_cases():
    data = _load()
    cases = data.get("cases", [])
    assert len(cases) == 5, f"Erwartet 5 Cases, gefunden: {len(cases)}"


def test_case_ids_correct():
    data = _load()
    ids = {c["id"] for c in data.get("cases", [])}
    assert ids == EXPECTED_IDS, f"IDs falsch: {ids}"


def test_required_fields_present():
    data = _load()
    for case in data.get("cases", []):
        missing = REQUIRED_CASE_FIELDS - set(case.keys())
        assert not missing, f"Case {case.get('id')} fehlt Felder: {missing}"


def test_component_metadata():
    data = _load()
    assert data.get("component") == "book-handler"
    assert data.get("component_type") in ("skill", "agent")


def test_bh01_has_url_input():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-01")
    assert "url" in case["input"], "bh-01 muss url im input haben"


def test_bh04_has_pdf_fixture():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-04")
    fixture_path = case.get("fixture")
    assert fixture_path is not None, "bh-04 muss fixture-Pfad haben"
    full = Path(__file__).parent.parent.parent / "evals" / "book-handler" / fixture_path
    assert full.exists(), f"bh-04 fixture fehlt: {full}"


def test_bh05_has_editors():
    data = _load()
    case = next(c for c in data["cases"] if c["id"] == "bh-05")
    assert case["input"].get("editors", []) or case.get("fixture"), (
        "bh-05 muss editors oder fixture haben"
    )
