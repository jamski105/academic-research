"""Tests for meta_analysis.py — DerSimonian-Laird Random-Effects Meta-Analysis.

TDD: Tests written before implementation.
Expected values pre-computed manually for 5-study example.
"""
from __future__ import annotations

import sys
import os
import pytest

# Ensure scripts/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from meta_analysis import (
    dersimonianlaird,
    build_forest_plot_mermaid,
    MetaAnalysisResult,
    Study,
)


# ---------------------------------------------------------------------------
# Fixture: 5 Beispiel-Studien (yi, vi) aus Ticket-Prompt
# ---------------------------------------------------------------------------
STUDIES = [
    Study(name="Smith 2020", yi=0.50, vi=0.0625),
    Study(name="Jones 2021", yi=0.30, vi=0.0900),
    Study(name="Chen 2019",  yi=0.70, vi=0.0400),
    Study(name="Brown 2022", yi=0.20, vi=0.0625),
    Study(name="Liu 2023",   yi=0.55, vi=0.0500),
]


class TestDerSimonianLaird:
    """Numerical correctness of the DL algorithm."""

    def test_returns_meta_analysis_result(self):
        result = dersimonianlaird(STUDIES)
        assert isinstance(result, MetaAnalysisResult)

    def test_pooled_effect_size(self):
        result = dersimonianlaird(STUDIES)
        assert abs(result.pooled_es - 0.4884) < 0.001

    def test_tau_squared_zero_when_q_lt_df(self):
        # Q=2.92 < df=4 → τ²=0 (clamped at 0)
        result = dersimonianlaird(STUDIES)
        assert result.tau2 == pytest.approx(0.0, abs=1e-9)

    def test_i_squared_zero(self):
        result = dersimonianlaird(STUDIES)
        assert result.i2 == pytest.approx(0.0, abs=0.01)

    def test_q_statistic(self):
        result = dersimonianlaird(STUDIES)
        assert abs(result.Q - 2.9226) < 0.001

    def test_se_pooled(self):
        result = dersimonianlaird(STUDIES)
        assert abs(result.se_pool - 0.1065) < 0.001

    def test_ci_lower(self):
        result = dersimonianlaird(STUDIES)
        assert abs(result.ci_lo - 0.2796) < 0.001

    def test_ci_upper(self):
        result = dersimonianlaird(STUDIES)
        assert abs(result.ci_hi - 0.6972) < 0.001

    def test_k_equals_number_of_studies(self):
        result = dersimonianlaird(STUDIES)
        assert result.k == 5

    def test_minimum_three_studies_required(self):
        with pytest.raises(ValueError, match="at least 3"):
            dersimonianlaird(STUDIES[:2])

    def test_nonzero_tau_squared_with_heterogeneous_studies(self):
        """Heterogeneous studies should yield τ²>0."""
        heterogeneous = [
            Study(name="A", yi=0.10, vi=0.01),
            Study(name="B", yi=0.90, vi=0.01),
            Study(name="C", yi=0.50, vi=0.01),
        ]
        result = dersimonianlaird(heterogeneous)
        assert result.tau2 > 0
        assert result.i2 > 0


class TestForestPlotMermaid:
    """Forest-plot Mermaid output."""

    def test_returns_string(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        assert isinstance(mermaid, str)

    def test_starts_with_graph_lr(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        assert mermaid.strip().startswith("graph LR")

    def test_contains_all_study_names(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        for study in STUDIES:
            assert study.name in mermaid, f"Study '{study.name}' missing from Forest-Plot"

    def test_contains_pool_node(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        assert "Pool" in mermaid

    def test_contains_i_squared(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        assert "I²" in mermaid or "I&sup2;" in mermaid or "I2" in mermaid

    def test_all_studies_point_to_pool(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        # Each study should have an arrow to Pool
        assert mermaid.count("-->") >= len(STUDIES)

    def test_pooled_effect_in_plot(self):
        result = dersimonianlaird(STUDIES)
        mermaid = build_forest_plot_mermaid(STUDIES, result)
        # Pooled ES rounded to 2 decimal places should appear
        assert "0.49" in mermaid or "0.488" in mermaid


class TestEdgeCases:
    """Edge-cases and robustness."""

    def test_exactly_three_studies(self):
        three = STUDIES[:3]
        result = dersimonianlaird(three)
        assert result.k == 3
        assert isinstance(result.pooled_es, float)

    def test_studies_with_identical_effect_sizes(self):
        same = [Study(name=f"S{i}", yi=0.5, vi=0.04) for i in range(4)]
        result = dersimonianlaird(same)
        assert abs(result.pooled_es - 0.5) < 0.001
        assert result.tau2 == pytest.approx(0.0, abs=1e-9)
