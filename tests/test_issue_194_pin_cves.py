"""
Regressionstest fuer Issue #194 — CVE-Pinning in scripts/requirements.txt.

Scope (NUR Pinning/CVE-Aspekt, siehe Issue #194):
- requests muss eine Untergrenze >= 2.32.4 erzwingen (CVE-2024-35195).
- lxml muss eine Untergrenze >= 5.2.0 erzwingen (CVE-2022-2309).

PyPDF2->pypdf (#203) und pandas/openpyxl-Entfernung (#235) sind explizit NICHT
Teil dieses Tests.

Die Tests parsen die requirements.txt mit packaging und pruefen die effektive
untere Versionsgrenze der relevanten Spezifizierer. Damit greifen sie unabhaengig
von der genauen Schreibweise (`>=`, `==`, `~=`, kombinierte Specifier).
"""

from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).parent.parent
REQUIREMENTS = REPO_ROOT / "scripts" / "requirements.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_requirements() -> dict[str, Requirement]:
    """Liefert {normalisierter Paketname: Requirement} aus scripts/requirements.txt."""
    parsed: dict[str, Requirement] = {}
    for raw in REQUIREMENTS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        req = Requirement(line)
        parsed[req.name.lower()] = req
    return parsed


def _min_allowed_version(spec: SpecifierSet, ceiling: str = "1000.0.0") -> Version:
    """
    Ermittelt die kleinste Version, die der SpecifierSet erlaubt, indem
    Kandidaten aus den Grenzen der Spezifizierer gegen den Set geprueft werden.
    """
    candidates: set[Version] = set()
    for s in spec:
        if s.version:
            base = Version(s.version)
            candidates.add(base)
            # knapp oberhalb einer exklusiven Untergrenze (>) mitberuecksichtigen
            candidates.add(Version(f"{base}.post1"))
    candidates.add(Version("0"))
    allowed = sorted(v for v in candidates if v in spec)
    if not allowed:
        pytest.fail(f"SpecifierSet {spec!r} erlaubt keine der Grenz-Kandidaten")
    return allowed[0]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_requirements_file_exists():
    assert REQUIREMENTS.is_file(), f"{REQUIREMENTS} fehlt"


def test_requests_pinned_to_cve_fixed_floor():
    """requests muss mindestens 2.32.4 verlangen (CVE-2024-35195)."""
    reqs = _parse_requirements()
    assert "requests" in reqs, "requests fehlt in scripts/requirements.txt"
    floor = _min_allowed_version(reqs["requests"].specifier)
    assert floor >= Version("2.32.4"), (
        f"requests-Untergrenze {floor} ist anfaellig "
        f"(CVE-2024-35195); erwartet >= 2.32.4. "
        f"Specifier: {reqs['requests'].specifier}"
    )


def test_lxml_pinned_to_cve_fixed_floor():
    """lxml muss mindestens 5.2.0 verlangen (CVE-2022-2309)."""
    reqs = _parse_requirements()
    assert "lxml" in reqs, "lxml fehlt in scripts/requirements.txt"
    floor = _min_allowed_version(reqs["lxml"].specifier)
    assert floor >= Version("5.2.0"), (
        f"lxml-Untergrenze {floor} ist anfaellig "
        f"(CVE-2022-2309); erwartet >= 5.2.0. "
        f"Specifier: {reqs['lxml'].specifier}"
    )


def test_requirements_still_parseable():
    """Alle Zeilen muessen valide PEP-508-Requirements bleiben (kein Bruch)."""
    reqs = _parse_requirements()
    # Sanity: Kernpakete bleiben vorhanden, nichts versehentlich entfernt.
    for pkg in ("anthropic", "httpx", "requests", "lxml"):
        assert pkg in reqs, f"{pkg} unerwartet aus requirements.txt entfernt"
