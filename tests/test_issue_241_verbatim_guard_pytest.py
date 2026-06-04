"""Regressionstest fuer Issue #241 (verbatim-guard nicht in pytest integriert).

Sicherstellt, dass der verbatim-guard-Eval-Runner ueber pytest erreichbar ist:
  * die pytest-Integrationsdatei ``tests/evals/test_verbatim_guard_evals.py``
    existiert,
  * ``evals/verbatim-guard/runner.py`` exportiert eine importierbare
    ``run_eval_cases()``-Funktion (statt nur CLI/``sys.exit``),
  * ein realer pytest-Lauf fuehrt alle 10 Vault-Lookup-Cases aus und sie
    bestehen die Akzeptanzkriterien.

Die fachlichen Per-Case-Asserts liegen in der Integrationsdatei; dieser Test
verriegelt die strukturelle AC (verbatim-guard wird ueber pytest erreicht).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = REPO_ROOT / "evals" / "verbatim-guard" / "runner.py"
INTEGRATION_TEST = REPO_ROOT / "tests" / "evals" / "test_verbatim_guard_evals.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("verbatim_guard_runner_241", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pytest_integration_file_exists():
    """Die pytest-Integration fuer den verbatim-guard muss existieren (Issue #241)."""
    assert INTEGRATION_TEST.exists(), (
        f"verbatim-guard ist nicht in pytest integriert — fehlt: {INTEGRATION_TEST}"
    )


def test_runner_exposes_importable_entrypoint():
    """runner.py muss eine importierbare run_eval_cases()-Funktion bereitstellen."""
    runner = _load_runner()
    assert hasattr(runner, "run_eval_cases"), (
        "runner.py exportiert keine run_eval_cases() — verbatim-guard nicht ueber "
        "pytest erreichbar (Issue #241)."
    )
    assert callable(runner.run_eval_cases)


def test_runner_executes_ten_cases_and_passes():
    """Ein realer Lauf fuehrt alle 10 Cases aus und erfuellt die AC (kein still-skip)."""
    runner = _load_runner()
    results = runner.run_eval_cases()
    assert len(results["details"]) == 10, (
        f"Erwartet 10 Cases, ausgefuehrt: {len(results['details'])}"
    )
    assert results["failed"] == 0, (
        f"verbatim-guard-Eval fehlgeschlagen: {results['details']}"
    )
    assert results["fpr"] < 5.0, f"FPR {results['fpr']:.1f}% verletzt AC (< 5 %)."
