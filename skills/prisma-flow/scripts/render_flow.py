#!/usr/bin/env python3
"""Render a PRISMA 2020 flow diagram as a Mermaid code block.

Usage (CLI):
  python render_flow.py \\
    --n-identified 100 \\
    --n-after-dedup 60 \\
    --n-excluded-screening 30 \\
    --n-excluded-eligibility 12 \\
    --n-included 8 \\
    [--output kapitel/methodik.md]

API:
  from render_flow import render_prisma_flow
  mermaid = render_prisma_flow(counters, output_path="kapitel/methodik.md")
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def render_prisma_flow(
    counters: dict[str, Any],
    output_path: str | None = None,
) -> str:
    """Generate a PRISMA 2020 Mermaid flowchart from counter dict.

    Args:
        counters: dict with keys n_identified, n_after_dedup,
                  n_excluded_screening, n_excluded_eligibility, n_included.
        output_path: if given, write the Mermaid block to that file (append).

    Returns:
        Rendered Mermaid block as string.
    """
    n_id = counters.get("n_identified", 0)
    n_dedup = counters.get("n_after_dedup", 0)
    n_ex_screen = counters.get("n_excluded_screening", 0)
    n_ex_elig = counters.get("n_excluded_eligibility", 0)
    n_inc = counters.get("n_included", 0)

    # Derived: how many records went to full-text eligibility
    n_eligible = n_dedup - n_ex_screen

    mermaid = f"""\
```mermaid
flowchart TD
    A["Identifiziert\\nn = {n_id}"]
    B["Nach Deduplikation\\nn = {n_dedup}"]
    C["Screening ausgeschlossen\\nn = {n_ex_screen}"]
    D["Volltextprüfung\\nn = {n_eligible}"]
    E["Eligibility ausgeschlossen\\nn = {n_ex_elig}"]
    F["Eingeschlossen\\nn = {n_inc}"]

    A --> B
    B -->|"ausgeschlossen"| C
    B --> D
    D -->|"ausgeschlossen"| E
    D --> F
```"""

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n\n## PRISMA Flow\n\n")
            fh.write(mermaid)
            fh.write("\n")

    return mermaid


def main() -> int:
    parser = argparse.ArgumentParser(description="Render PRISMA 2020 flow as Mermaid")
    parser.add_argument("--n-identified", type=int, required=True)
    parser.add_argument("--n-after-dedup", type=int, required=True)
    parser.add_argument("--n-excluded-screening", type=int, required=True)
    parser.add_argument("--n-excluded-eligibility", type=int, required=True)
    parser.add_argument("--n-included", type=int, required=True)
    parser.add_argument("--output", help="Append Mermaid block to this file")
    args = parser.parse_args()

    counters = {
        "n_identified": args.n_identified,
        "n_after_dedup": args.n_after_dedup,
        "n_excluded_screening": args.n_excluded_screening,
        "n_excluded_eligibility": args.n_excluded_eligibility,
        "n_included": args.n_included,
    }
    result = render_prisma_flow(counters, output_path=args.output)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
