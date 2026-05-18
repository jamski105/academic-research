#!/usr/bin/env python3
"""DerSimonian-Laird Random-Effects Meta-Analysis + Mermaid Forest-Plot.

Usage (CLI):
  python meta_analysis.py --input studies.json --output kapitel/meta-analyse.md

Input JSON format:
  [{"name": "Smith 2020", "yi": 0.50, "vi": 0.0625}, ...]

Output: Markdown with statistical summary + Mermaid Forest-Plot.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class Study:
    """A single study with effect size and variance."""
    name: str
    yi: float   # Effect size estimate
    vi: float   # Within-study variance


@dataclass
class MetaAnalysisResult:
    """Result of a DerSimonian-Laird random-effects meta-analysis."""
    k: int                  # Number of studies
    Q: float                # Cochran's Q statistic
    tau2: float             # Between-study variance (τ²)
    i2: float               # Heterogeneity index I² (%)
    pooled_es: float        # Pooled effect size (random-effects)
    se_pool: float          # Standard error of pooled ES
    ci_lo: float            # 95% CI lower bound
    ci_hi: float            # 95% CI upper bound


def dersimonianlaird(studies: list[Study]) -> MetaAnalysisResult:
    """Compute DerSimonian-Laird random-effects meta-analysis.

    Algorithm (Borenstein et al., 2009):
      1. Fixed-effect weights:  wi  = 1 / vi
      2. Q = Σ wi·(yi − ȳ_FE)²
      3. C = Σwi − Σwi²/Σwi
      4. τ² = max(0, (Q − df) / C)
      5. Random-effects weights: wi* = 1 / (vi + τ²)
      6. Pooled ES = Σ(wi*·yi) / Σwi*
      7. SE = √(1/Σwi*);  95% CI = ES ± 1.96·SE
      8. I² = max(0, (Q − df) / Q) · 100%

    Args:
        studies: List of Study objects (≥3 required).

    Returns:
        MetaAnalysisResult with all computed statistics.

    Raises:
        ValueError: If fewer than 3 studies are provided.
    """
    if len(studies) < 3:
        raise ValueError("Meta-analysis requires at least 3 studies.")

    k = len(studies)
    yi = [s.yi for s in studies]
    vi = [s.vi for s in studies]

    # --- Step 1: Fixed-effect weights ---
    wi = [1.0 / v for v in vi]
    sum_wi = sum(wi)
    sum_wi2 = sum(w * w for w in wi)
    sum_wiyi = sum(w * y for w, y in zip(wi, yi))

    # Fixed-effect pooled estimate (for Q calculation)
    fe_pool = sum_wiyi / sum_wi

    # --- Step 2: Q statistic ---
    Q = sum(w * (y - fe_pool) ** 2 for w, y in zip(wi, yi))
    df = k - 1

    # --- Step 3: C ---
    C = sum_wi - sum_wi2 / sum_wi

    # --- Step 4: τ² (clamped at 0) ---
    tau2 = max(0.0, (Q - df) / C)

    # --- Step 5: Random-effects weights ---
    wi_star = [1.0 / (v + tau2) for v in vi]
    sum_wi_star = sum(wi_star)
    sum_wi_star_yi = sum(ws * y for ws, y in zip(wi_star, yi))

    # --- Step 6: Pooled ES ---
    pooled_es = sum_wi_star_yi / sum_wi_star

    # --- Step 7: SE and 95% CI ---
    se_pool = math.sqrt(1.0 / sum_wi_star)
    ci_lo = pooled_es - 1.96 * se_pool
    ci_hi = pooled_es + 1.96 * se_pool

    # --- Step 8: I² ---
    if Q > 0:
        i2 = max(0.0, (Q - df) / Q * 100.0)
    else:
        i2 = 0.0

    return MetaAnalysisResult(
        k=k,
        Q=Q,
        tau2=tau2,
        i2=i2,
        pooled_es=pooled_es,
        se_pool=se_pool,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
    )


def build_forest_plot_mermaid(studies: list[Study], result: MetaAnalysisResult) -> str:
    """Build a Mermaid graph LR Forest-Plot from meta-analysis results.

    Each study is shown with its point estimate and 95% CI.
    All study nodes point to a Pool node.

    Args:
        studies: Original study list.
        result:  MetaAnalysisResult from dersimonianlaird().

    Returns:
        Mermaid diagram string.
    """
    lines = ["graph LR"]

    for i, study in enumerate(studies):
        # Individual study 95% CI
        se_i = math.sqrt(study.vi)
        lo_i = study.yi - 1.96 * se_i
        hi_i = study.yi + 1.96 * se_i
        node_id = f"S{i}"
        label = f"{study.name}<br/>{study.yi:.2f} ({lo_i:.2f}–{hi_i:.2f})"
        lines.append(f"  {node_id}[\"{label}\"] --> Pool")

    # Pool node
    pool_label = (
        f"Pooled<br/>"
        f"{result.pooled_es:.2f} ({result.ci_lo:.2f}–{result.ci_hi:.2f})<br/>"
        f"I²={result.i2:.1f}%"
    )
    lines.append(f'  Pool["{pool_label}"]')

    return "\n".join(lines)


def _load_studies(path: str) -> list[Study]:
    """Load studies from a JSON file."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    studies = []
    for item in raw:
        studies.append(Study(
            name=item["name"],
            yi=float(item["yi"]),
            vi=float(item["vi"]),
        ))
    return studies


def _render_markdown(studies: list[Study], result: MetaAnalysisResult) -> str:
    """Render a full Markdown report including stats + Forest-Plot."""
    mermaid = build_forest_plot_mermaid(studies, result)
    lines = [
        "# Meta-Analyse",
        "",
        "## Statistische Zusammenfassung",
        "",
        f"- **Anzahl Studien (k):** {result.k}",
        f"- **Gepoolter Effekt (RE-Modell):** {result.pooled_es:.4f}",
        f"- **95%-Konfidenzintervall:** [{result.ci_lo:.4f}, {result.ci_hi:.4f}]",
        f"- **Standardfehler:** {result.se_pool:.4f}",
        f"- **Cochran's Q:** {result.Q:.4f} (df={result.k - 1})",
        f"- **τ² (Between-Study-Varianz):** {result.tau2:.4f}",
        f"- **I² (Heterogenität):** {result.i2:.1f}%",
        "",
        "> Modell: Random-Effects (DerSimonian & Laird, 1986)",
        "",
        "## Forest-Plot",
        "",
        "```mermaid",
        mermaid,
        "```",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DerSimonian-Laird Meta-Analysis + Mermaid Forest-Plot"
    )
    parser.add_argument("--input", required=True, help="JSON file with studies (name/yi/vi)")
    parser.add_argument("--output", required=True, help="Output Markdown file path")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    args = _parse_args()

    try:
        studies = _load_studies(args.input)
    except Exception:
        log.exception("Failed to load studies from %s", args.input)
        return 1

    try:
        result = dersimonianlaird(studies)
    except ValueError as exc:
        log.error("Meta-analysis failed: %s", exc)
        return 1

    md = _render_markdown(studies, result)

    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(md)
        log.info("Wrote meta-analysis to %s", args.output)
    except Exception:
        log.exception("Failed to write output to %s", args.output)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
