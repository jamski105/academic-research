"""Token-Regression-Test.

Liest tests/baselines/tokens.json.
- Wenn leer oder fehlend: pytest.skip (noch keine Baseline).
- Wenn vorhanden: simuliert stabile und gestiegene Werte, prueft +20%-Schwelle.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

BASELINE_FILE = Path(__file__).parent.parent / "baselines" / "tokens.json"
THRESHOLD = 1.20  # 20 % Anstieg


def _load_baseline() -> dict:
    if not BASELINE_FILE.exists():
        pytest.skip("tokens.json fehlt -- noch keine Baseline")
    data = json.loads(BASELINE_FILE.read_text())
    if not data:
        pytest.skip("tokens.json ist leer -- noch keine Baseline erfasst")
    return data


def _check_regression(
    suite: str,
    case_id: str,
    tokens_in: int,
    tokens_out: int,
    baseline: dict,
) -> list[str]:
    """Prueft ob tokens_in/tokens_out innerhalb +20% der Baseline liegen.

    Gibt Liste von Fehlermeldungen zurueck (leer = OK).
    """
    errors: list[str] = []
    suite_data = baseline.get(suite, {})
    case_data = suite_data.get(case_id)
    if case_data is None:
        return []  # Kein Eintrag = kein Vergleich
    baseline_in = case_data.get("tokens_in", 0)
    baseline_out = case_data.get("tokens_out", 0)
    if baseline_in > 0 and tokens_in > baseline_in * THRESHOLD:
        errors.append(
            f"{suite}/{case_id}: tokens_in {tokens_in} > baseline "
            f"{baseline_in} * {THRESHOLD} = {baseline_in * THRESHOLD:.0f}"
        )
    if baseline_out > 0 and tokens_out > baseline_out * THRESHOLD:
        errors.append(
            f"{suite}/{case_id}: tokens_out {tokens_out} > baseline "
            f"{baseline_out} * {THRESHOLD} = {baseline_out * THRESHOLD:.0f}"
        )
    return errors


def test_baseline_file_exists():
    """tokens.json muss vorhanden sein (darf leer sein)."""
    assert BASELINE_FILE.exists(), f"Baseline fehlt: {BASELINE_FILE}"


def test_baseline_schema_valid():
    """Wenn tokens.json Eintraege hat, muss Schema stimmen."""
    if not BASELINE_FILE.exists():
        pytest.skip("Datei fehlt")
    data = json.loads(BASELINE_FILE.read_text())
    for suite, cases in data.items():
        assert isinstance(cases, dict), f"Suite {suite!r} muss dict sein"
        for case_id, vals in cases.items():
            assert "tokens_in" in vals, f"{suite}/{case_id} fehlt tokens_in"
            assert "tokens_out" in vals, f"{suite}/{case_id} fehlt tokens_out"
            assert isinstance(vals["tokens_in"], int), (
                f"{suite}/{case_id} tokens_in muss int sein"
            )
            assert isinstance(vals["tokens_out"], int), (
                f"{suite}/{case_id} tokens_out muss int sein"
            )


def test_stable_values_pass():
    """Stabile Werte (identisch zur Baseline) duerfen nicht fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    errors = _check_regression("test-suite", "case-01", 1000, 200, baseline)
    assert errors == [], f"Stabile Werte schlagen fehl: {errors}"


def test_small_increase_passes():
    """Anstieg unter 20% darf nicht fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # +19% auf tokens_in, +10% auf tokens_out
    errors = _check_regression("test-suite", "case-01", 1190, 220, baseline)
    assert errors == [], f"Kleiner Anstieg schlaegt fehl: {errors}"


def test_large_increase_fails():
    """Anstieg ueber 20% muss fehlschlagen."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # +21% auf tokens_in
    errors = _check_regression("test-suite", "case-01", 1210, 200, baseline)
    assert len(errors) == 1, f"Grosser Anstieg wurde nicht erkannt: {errors}"
    assert "tokens_in" in errors[0]


def test_tokens_out_regression_detected():
    """Anstieg von tokens_out ueber 20% wird separat erkannt."""
    baseline = {
        "test-suite": {
            "case-01": {"tokens_in": 1000, "tokens_out": 200}
        }
    }
    # tokens_out +21%
    errors = _check_regression("test-suite", "case-01", 1000, 243, baseline)
    assert len(errors) == 1, f"tokens_out Regression nicht erkannt: {errors}"
    assert "tokens_out" in errors[0]


def test_real_baseline_regression():
    """Wenn echte Baseline vorhanden: keine Regression ueber 20% erlaubt."""
    baseline = _load_baseline()
    all_errors: list[str] = []
    for suite, cases in baseline.items():
        for case_id, vals in cases.items():
            errs = _check_regression(
                suite,
                case_id,
                vals["tokens_in"],
                vals["tokens_out"],
                baseline,
            )
            all_errors.extend(errs)
    assert not all_errors, "Token-Regression erkannt:\n" + "\n".join(all_errors)
