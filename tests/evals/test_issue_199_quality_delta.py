"""Regressionstest fuer Issue #199.

README verspricht: Quality-Evals enforced eine Schwelle von Delta >= 20 pp
PASS-Rate zwischen with_skill und without_skill. Der Code in
tests/evals/eval_runner.py muss diese Schwelle tatsaechlich durchsetzen.

Akzeptanzkriterien:
- check_quality_delta() faellt bei Quality-Drop > 20 pp mit AssertionError.
- Schwelle konfigurierbar via EVAL_DELTA_THRESHOLD (Default 0.20).
- Kuenstlicher Quality-Drop laesst den Check fehlschlagen.
"""
from __future__ import annotations

import pytest

from tests.evals import eval_runner


def test_check_quality_delta_exists():
    """eval_runner exportiert eine Delta-Schwellen-Pruefung."""
    assert hasattr(eval_runner, "check_quality_delta"), (
        "eval_runner.check_quality_delta fehlt - Delta-Schwelle nicht enforced"
    )


def test_quality_delta_pass_when_better():
    """Verbesserung gegenueber Baseline besteht die Pruefung."""
    # with_skill 0.9, baseline 0.5 -> Delta +0.4, klar PASS
    eval_runner.check_quality_delta(current_score=0.9, baseline_score=0.5)


def test_quality_delta_pass_within_threshold():
    """Kleiner Drop innerhalb der 20-pp-Schwelle besteht."""
    # Drop von genau 20 pp ist noch erlaubt (>= -0.20)
    eval_runner.check_quality_delta(current_score=0.6, baseline_score=0.8)


def test_quality_delta_fails_on_large_drop():
    """Kuenstlicher Quality-Drop > 20 pp laesst den Check fehlschlagen (rot)."""
    # 30-pp-Drop: baseline 0.9 -> current 0.6
    with pytest.raises(AssertionError):
        eval_runner.check_quality_delta(current_score=0.6, baseline_score=0.9)


def test_quality_delta_threshold_env_override(monkeypatch):
    """EVAL_DELTA_THRESHOLD ueberschreibt die Default-Schwelle (0.20)."""
    # Strengere Schwelle 0.05: ein 10-pp-Drop muss jetzt fehlschlagen
    monkeypatch.setenv("EVAL_DELTA_THRESHOLD", "0.05")
    with pytest.raises(AssertionError):
        eval_runner.check_quality_delta(current_score=0.7, baseline_score=0.8)


def test_quality_delta_default_threshold_is_0_20(monkeypatch):
    """Ohne ENV gilt Default-Schwelle 0.20."""
    monkeypatch.delenv("EVAL_DELTA_THRESHOLD", raising=False)
    # 20-pp-Drop genau an der Default-Grenze besteht noch
    eval_runner.check_quality_delta(current_score=0.6, baseline_score=0.8)
    # 21-pp-Drop ueberschreitet Default-Grenze
    with pytest.raises(AssertionError):
        eval_runner.check_quality_delta(current_score=0.59, baseline_score=0.80)
