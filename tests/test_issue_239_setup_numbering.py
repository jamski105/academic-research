"""Regressionstest fuer #239: Abschnitt-Nummerierung in ``scripts/setup.sh``.

Der Header-Kommentar listet 5 Schritte (``:5-9``), der letzte
Abschnittskommentar lautete aber ``# 7. Projekt-Bootstrap`` — Schritt 6
fehlte komplett, die Nummerierung sprang von 5 auf 7.

Akzeptanzkriterium (#239): Schritt-Nummerierung in ``setup.sh`` ist
lueckenlos/konsistent (kein 5->7-Sprung).

Die Tests pruefen das ueber den reinen Datei-Inhalt — ohne ``setup.sh``
auszufuehren —, damit sie in CI ohne Netzwerk/venv-Seiteneffekte laufen.
"""
import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SETUP_SH = _REPO_ROOT / "scripts" / "setup.sh"

_DIVIDER = re.compile(r"^#\s*-{3,}\s*$")
_SECTION = re.compile(r"^#\s*(\d+)\.\s+\S")


def _divider_section_numbers() -> list[int]:
    """Nummern der Abschnitts-Header, die zwischen ``# ----``-Trennlinien stehen.

    Genau diese Bloecke leiten in ``setup.sh`` die durchnummerierten
    Installationsschritte ein. Der Header-Kommentar oben im Skript (eine
    eingerueckte Aufzaehlung) zaehlt hier bewusst nicht mit.
    """
    lines = _SETUP_SH.read_text(encoding="utf-8").splitlines()
    numbers: list[int] = []
    for i, line in enumerate(lines):
        m = _SECTION.match(line)
        if not m:
            continue
        prev_is_divider = i > 0 and _DIVIDER.match(lines[i - 1])
        if prev_is_divider:
            numbers.append(int(m.group(1)))
    return numbers


def test_setup_sh_exists():
    assert _SETUP_SH.is_file(), f"{_SETUP_SH} fehlt"


def test_section_numbering_has_no_gap():
    """Die Abschnittsnummern sind lueckenlos aufsteigend (kein 5->7-Sprung)."""
    numbers = _divider_section_numbers()
    assert numbers, "keine nummerierten Abschnitts-Header gefunden"

    expected = list(range(numbers[0], numbers[0] + len(numbers)))
    assert numbers == expected, (
        f"Abschnitts-Nummerierung ist nicht lueckenlos: {numbers} "
        f"(erwartet {expected})"
    )


def test_no_section_number_seven_without_six():
    """Konkret: kein ``# 7.``-Abschnitt, solange ``# 6.`` fehlt."""
    numbers = set(_divider_section_numbers())
    if 7 in numbers:
        assert 6 in numbers, "Abschnitt '# 7.' existiert, aber '# 6.' fehlt"


def test_bash_syntax_valid():
    """``bash -n setup.sh`` bleibt syntaktisch valide."""
    result = subprocess.run(
        ["bash", "-n", str(_SETUP_SH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"bash -n schlug fehl: {result.stderr}"
