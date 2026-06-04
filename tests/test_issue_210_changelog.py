"""Regressionstest fuer Issue #210 — CHANGELOG-Konsistenz.

Akzeptanzkriterien aus dem Issue:
- v6.5.0 und v6.4.0 duerfen NICHT dasselbe Datum tragen (Copy-Paste-Fehler).
- Jede Release-Ueberschrift hat ein eindeutiges Datum.
- Release-Daten stehen in chronologisch absteigender Reihenfolge (neueste zuerst).
- Der Hooks-Stack (#91, #103) listet jeden der vier Hooks mit eigenem Bullet
  inkl. PR-Referenz.
"""

import re
from datetime import date
from pathlib import Path

import pytest

CHANGELOG = Path(__file__).parent.parent / "CHANGELOG.md"

# Ueberschriften der Form: "## [6.4.0] — 2026-05-17"
RELEASE_RE = re.compile(
    r"^##\s+\[(?P<version>\d+\.\d+\.\d+)\]\s+[—-]\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$",
    re.MULTILINE,
)


def _releases() -> list[tuple[str, date]]:
    text = CHANGELOG.read_text(encoding="utf-8")
    out: list[tuple[str, date]] = []
    for m in RELEASE_RE.finditer(text):
        y, mo, d = (int(x) for x in m.group("date").split("-"))
        out.append((m.group("version"), date(y, mo, d)))
    return out


def _v6_releases() -> list[tuple[str, date]]:
    """Nur die v6.x-Releases — Scope von Issue #210 (v5.x-Launch-Burst bleibt unberuehrt)."""
    return [(v, d) for v, d in _releases() if v.startswith("6.")]


def test_changelog_exists():
    assert CHANGELOG.is_file(), f"CHANGELOG fehlt: {CHANGELOG}"


def test_at_least_one_release_parsed():
    assert _releases(), "Keine Release-Ueberschrift mit Datum geparst"


def test_v6_release_dates_are_unique():
    """Kernforderung: keine zwei v6.x-Releases teilen sich ein Datum."""
    by_date: dict[date, list[str]] = {}
    for version, dt in _v6_releases():
        by_date.setdefault(dt, []).append(version)
    duplicates = {str(d): v for d, v in by_date.items() if len(v) > 1}
    assert not duplicates, f"Mehrere v6.x-Releases mit identischem Datum: {duplicates}"


def test_v640_and_v650_have_distinct_dates():
    """Explizit aus dem Issue: v6.4.0 != v6.5.0 Datum."""
    dates = {v: dt for v, dt in _releases()}
    assert "6.4.0" in dates, "v6.4.0-Eintrag fehlt im CHANGELOG"
    assert "6.5.0" in dates, "v6.5.0-Eintrag fehlt im CHANGELOG"
    assert dates["6.4.0"] != dates["6.5.0"], (
        f"v6.4.0 und v6.5.0 tragen dasselbe Datum: {dates['6.4.0']}"
    )


def test_v6_release_dates_descending():
    """Neueste v6.x-Releases stehen oben — Daten duerfen nicht aelter-zu-neuer laufen."""
    releases = _v6_releases()
    dates = [dt for _, dt in releases]
    assert dates == sorted(dates, reverse=True), (
        f"v6.x-Release-Daten nicht absteigend sortiert: {[(v, str(d)) for v, d in releases]}"
    )


HOOKS = [
    "pre-compact.mjs",
    "post-tool-use-decisions.mjs",
    "mid-session-reinforcement.mjs",
    "verbatim-guard.mjs",
]


def test_hooks_stack_lists_each_hook():
    text = CHANGELOG.read_text(encoding="utf-8")
    missing = [h for h in HOOKS if h not in text]
    assert not missing, f"Hooks fehlen im CHANGELOG: {missing}"


def test_hooks_stack_has_pr_reference():
    """Der Hooks-Stack-Block referenziert die PRs (#91, #103)."""
    text = CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r"\*\*Hooks-Stack[^\n]*", text)
    assert m, "Kein 'Hooks-Stack'-Eintrag im CHANGELOG gefunden"
    assert re.search(r"#\d+", m.group(0)), (
        f"Hooks-Stack-Eintrag ohne PR-Referenz: {m.group(0)}"
    )
