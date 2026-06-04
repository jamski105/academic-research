"""pytest-Integration fuer den verbatim-guard-Eval-Runner (Issue #241).

Der Runner unter ``evals/verbatim-guard/runner.py`` enthaelt 10 Vault-Lookup-
Cases (``cases.json``), die ``academic_vault.server.search_quote_text()`` gegen
echte vs. erfundene Zitate pruefen. Bis Issue #241 war der Runner ein reines
CLI-Skript (``if __name__ == '__main__'``) und wurde von keiner pytest-Datei
aufgerufen → er lief in CI nie automatisch.

Diese Datei bindet den Runner als echten pytest-Test ein:
  * importiert eine wiederverwendbare Funktion aus ``runner.py``,
  * parametrisiert ueber alle 10 Cases (FAIL statt still-skip),
  * verifiziert die Akzeptanzkriterien (100 % pass/block, FPR < 5 %).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Runner-Modul dynamisch laden (Verzeichnis enthaelt Bindestrich → kein Paket)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNNER_PATH = REPO_ROOT / "evals" / "verbatim-guard" / "runner.py"
CASES_PATH = REPO_ROOT / "evals" / "verbatim-guard" / "cases.json"


def _load_runner():
    """Laedt evals/verbatim-guard/runner.py als Modul (Pfad mit Bindestrich)."""
    assert RUNNER_PATH.exists(), f"Runner fehlt: {RUNNER_PATH}"
    spec = importlib.util.spec_from_file_location("verbatim_guard_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


@pytest.fixture(scope="module")
def eval_results(runner):
    """Fuehrt den verbatim-guard-Eval-Lauf genau einmal pro Modul aus.

    Erwartet eine importierbare Funktion ``run_eval_cases()``, die strukturierte
    Ergebnisse zurueckgibt (statt nur zu printen und ``sys.exit`` zu rufen).
    """
    assert hasattr(runner, "run_eval_cases"), (
        "runner.py muss eine importierbare run_eval_cases()-Funktion exportieren, "
        "damit der verbatim-guard ueber pytest erreichbar ist (Issue #241)."
    )
    return runner.run_eval_cases()


def _load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC: Die 10 Vault-Lookup-Cases laufen bei jedem pytest-Lauf.
# ---------------------------------------------------------------------------

def test_runner_is_importable_via_pytest(runner):
    """runner.py wird ueber pytest erreicht und exportiert run_eval_cases()."""
    assert hasattr(runner, "run_eval_cases"), (
        "verbatim-guard-Runner ist nicht ueber pytest erreichbar (Issue #241)."
    )


def test_all_ten_cases_execute(eval_results):
    """Alle 10 Cases werden tatsaechlich ausgefuehrt (kein still-skip)."""
    details = eval_results["details"]
    assert len(details) == 10, f"Erwartet 10 ausgefuehrte Cases, erhalten: {len(details)}"
    assert len(_load_cases()) == 10, "cases.json muss 10 Cases enthalten."


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: f"case{c['id']}-{c['type']}")
def test_each_case_matches_expected(case, eval_results):
    """Jeder einzelne Case erfuellt sein expected (pass/block) — FAIL statt skip."""
    detail = next(d for d in eval_results["details"] if d["id"] == case["id"])
    assert detail["actual"] == case["expected"], (
        f"Case {case['id']} ({case['type']}): "
        f"expected={case['expected']} actual={detail['actual']} hits={detail['hits']}"
    )


def test_real_quotes_all_pass(eval_results):
    """AC: Echte Quotes werden zu 100 % gefunden (pass)."""
    real = [d for d in eval_results["details"] if d["type"] == "real"]
    assert real, "Es muss mindestens einen real-Case geben."
    assert all(d["actual"] == "pass" for d in real), (
        f"Nicht alle echten Quotes bestehen: {real}"
    )


def test_invented_quotes_all_blocked(eval_results):
    """AC: Erfundene Quotes werden zu 100 % geblockt (block)."""
    invented = [d for d in eval_results["details"] if d["type"] == "invented"]
    assert invented, "Es muss mindestens einen invented-Case geben."
    assert all(d["actual"] == "block" for d in invented), (
        f"Nicht alle erfundenen Quotes werden geblockt: {invented}"
    )


def test_false_positive_rate_below_threshold(eval_results):
    """AC: False-Positive-Rate (echter Quote faelschlich geblockt) < 5 %."""
    assert eval_results["fpr"] < 5.0, (
        f"FPR {eval_results['fpr']:.1f}% verletzt AC (< 5 %)."
    )


def test_overall_pass(eval_results):
    """Gesamtergebnis: kein einziger Case schlaegt fehl."""
    assert eval_results["failed"] == 0, (
        f"{eval_results['failed']} Eval-Case(s) fehlgeschlagen: {eval_results['details']}"
    )
