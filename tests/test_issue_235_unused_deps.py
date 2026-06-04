"""Regressionstest fuer Issue #235: pandas + openpyxl ungenutzt.

`pandas` und `openpyxl` standen in `scripts/requirements.txt`, werden aber
von keinem `scripts/*.py` importiert (`openpyxl` nur im separaten Skill
`skills/xlsx`). Dieser Test sichert ab, dass

1. `scripts/requirements.txt` weder `pandas` noch `openpyxl` listet, und
2. kein `scripts/`-Code `pandas` oder `openpyxl` importiert,

sodass nur tatsaechlich genutzte Pakete im Top-Level-Requirements stehen.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
REQUIREMENTS = REPO_ROOT / "scripts" / "requirements.txt"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Pakete, die laut Akzeptanzkriterien NICHT mehr im Top-Level-Requirements
# stehen duerfen, weil sie von scripts/ nicht importiert werden.
UNUSED_PACKAGES = ("pandas", "openpyxl")


def _listed_packages() -> set[str]:
    """Liefert die in requirements.txt gelisteten Paketnamen (lowercase)."""
    packages: set[str] = set()
    for raw in REQUIREMENTS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Paketname = alles vor Version-Specifier / Extras / Whitespace.
        name = re.split(r"[<>=!~\[ ;]", line, maxsplit=1)[0].strip().lower()
        if name:
            packages.add(name)
    return packages


@pytest.mark.parametrize("package", UNUSED_PACKAGES)
def test_unused_package_not_in_requirements(package: str) -> None:
    """`pandas`/`openpyxl` duerfen nicht in scripts/requirements.txt stehen."""
    assert package not in _listed_packages(), (
        f"{package!r} steht in scripts/requirements.txt, wird aber von "
        f"scripts/ nicht importiert (siehe Issue #235)."
    )


@pytest.mark.parametrize("package", UNUSED_PACKAGES)
def test_unused_package_not_imported_in_scripts(package: str) -> None:
    """Kein scripts/*.py darf pandas/openpyxl importieren (Regression-Guard)."""
    import_pattern = re.compile(
        rf"^\s*(?:import\s+{re.escape(package)}\b|from\s+{re.escape(package)}\b)",
        re.MULTILINE,
    )
    offenders = []
    for py_file in SCRIPTS_DIR.rglob("*.py"):
        if import_pattern.search(py_file.read_text()):
            offenders.append(str(py_file.relative_to(REPO_ROOT)))
    assert not offenders, (
        f"{package!r} wird in scripts/ importiert ({offenders}); Entfernen aus "
        f"requirements.txt waere falsch."
    )
