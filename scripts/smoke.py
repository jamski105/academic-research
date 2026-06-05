#!/usr/bin/env python3
"""scripts/smoke.py — eigenständiger End-to-End-Smoke-Reporter.

Führt dieselben Checks wie ``tests/test_smoke_e2e.py`` aus (geteilte Logik in
``tests/helpers/smoke_core.py``), druckt aber einen kategorisierten,
menschenlesbaren PASS/FAIL-Report mit Gesamtergebnis.

  Exit 0  → alle Checks grün.
  Exit 1  → mindestens ein Check rot (oder Voraussetzung fehlt).

Aufruf:
    python scripts/smoke.py
    ~/.academic-research/venv/bin/python scripts/smoke.py
"""

from __future__ import annotations

import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any

# Repo-Root importierbar machen (Skript läuft eigenständig).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.helpers import smoke_core  # noqa: E402

# ANSI-Farben (nur wenn TTY).
_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
DIM = "\033[2m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"


def _check_prerequisites() -> list[str]:
    """Gibt eine Liste von Voraussetzungs-Problemen zurück (leer = ok)."""
    problems: list[str] = []
    try:
        import mcp.client.stdio  # noqa: F401
    except Exception:
        problems.append("mcp-SDK nicht importierbar (mcp.client.stdio)")
    if not smoke_core.VENV_PYTHON.exists():
        problems.append(f"venv-Python fehlt: {smoke_core.VENV_PYTHON}")
    if shutil.which("node") is None:
        problems.append("node nicht im PATH (Hooks nicht ausführbar)")
    return problems


def _run_one(label: str, fn) -> tuple[bool, str, float]:
    """Führt einen Check aus. Gibt (ok, detail, dauer_s) zurück."""
    start = time.perf_counter()
    try:
        fn()
        return True, "", time.perf_counter() - start
    except AssertionError as exc:
        return False, str(exc).strip() or "AssertionError", time.perf_counter() - start
    except Exception as exc:  # noqa: BLE001
        detail = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}"
        return False, detail, time.perf_counter() - start


def main() -> int:
    print(f"{BOLD}academic-research — Ultimate Smoke E2E{RESET}")
    print(f"{DIM}Repo: {smoke_core.REPO_ROOT}{RESET}\n")

    problems = _check_prerequisites()
    if problems:
        print(f"{RED}{BOLD}VORAUSSETZUNGEN FEHLEN:{RESET}")
        for p in problems:
            print(f"  {RED}✗{RESET} {p}")
        print(f"\n{RED}{BOLD}GESAMT: FAIL{RESET} (Smoke nicht ausführbar)")
        return 1

    # Reihenfolge: erst State-unabhängige Checks (billig, fail-fast bei Struktur),
    # dann der teure MCP-Round-Trip (ein Server-Start) + State-abhängige Checks.
    results: list[tuple[str, str, bool, str, float]] = []  # (cat, name, ok, detail, dur)

    for category, name, plain_fn in smoke_core.plain_checks():
        ok, detail, dur = _run_one(name, plain_fn)
        results.append((category, name, ok, detail, dur))

    # MCP-Round-Trip: ein einziger Server-Start liefert das State-dict.
    state: dict[str, Any] | None = None
    mcp_setup_error = None
    t0 = time.perf_counter()
    try:
        state = smoke_core.run_mcp_roundtrip()
    except Exception as exc:  # noqa: BLE001
        mcp_setup_error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=4)}"
    mcp_dur = time.perf_counter() - t0

    captured_state = state  # stabil ausserhalb der Schleife (vermeidet B023)
    for category, name, state_fn in smoke_core.stateful_checks():
        if captured_state is None:
            results.append(
                (category, name, False, f"MCP-Round-Trip fehlgeschlagen: {mcp_setup_error}", 0.0)
            )
        else:
            ok, detail, dur = _run_one(name, lambda f=state_fn: f(captured_state))
            results.append((category, name, ok, detail, dur))

    # --- Report nach Kategorie gruppiert -----------------------------------
    categories: dict[str, list[tuple[str, bool, str, float]]] = {}
    for cat, name, ok, detail, dur in results:
        categories.setdefault(cat, []).append((name, ok, detail, dur))

    total = len(results)
    passed = sum(1 for _, _, ok, _, _ in results if ok)
    failed = total - passed

    print(f"{BOLD}Ergebnisse nach Kategorie:{RESET}\n")
    for cat in sorted(categories):
        rows = categories[cat]
        cat_pass = sum(1 for _, ok, _, _ in rows if ok)
        head_col = GREEN if cat_pass == len(rows) else RED
        print(f"{head_col}{BOLD}{cat}{RESET} {DIM}({cat_pass}/{len(rows)}){RESET}")
        for name, ok, detail, dur in rows:
            status = PASS if ok else FAIL
            print(f"  [{status}] {name} {DIM}({dur*1000:.0f} ms){RESET}")
            if not ok and detail:
                indented = "\n        ".join(detail.splitlines())
                print(f"        {YELLOW}{indented}{RESET}")
        print()

    print(f"{DIM}MCP-Round-Trip (1 Server-Start): {mcp_dur*1000:.0f} ms{RESET}")
    print(f"{BOLD}{'─' * 48}{RESET}")
    overall_color = GREEN if failed == 0 else RED
    verdict = "PASS" if failed == 0 else "FAIL"
    print(
        f"{overall_color}{BOLD}GESAMT: {verdict}{RESET}  "
        f"({passed}/{total} Checks grün, {failed} rot)"
    )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
