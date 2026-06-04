"""Regressionstest fuer Issue #234.

setup.md (Schritt 7) beschreibt ein SciHub-Opt-in, das setup.sh NICHT
implementiert hat (kein read-Prompt, kein Schreiben von scihub_optin). Diese
Tests pruefen das *reale* Verhalten:

1. scripts/scihub_optin.py existiert und ist importierbar.
2. set_optin() schreibt scihub_optin in active.yaml (true UND false), erhaelt
   andere Keys, legt die Datei aus Default an, wenn sie fehlt — idempotent.
3. _prompt_optin() faellt auf False (Safety-Default) zurueck, wenn stdin
   nicht interaktiv ist.
4. setup.sh ruft den Opt-in-Helper auf (setup.md und setup.sh stimmen ueberein)
   und die Kommentar-Nummerierung springt nicht mehr 5 -> 7 ohne 6.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SETUP_SH = SCRIPTS_DIR / "setup.sh"
OPTIN_SCRIPT = SCRIPTS_DIR / "scihub_optin.py"

sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# 1. Helper existiert und ist importierbar
# ---------------------------------------------------------------------------

def test_scihub_optin_script_exists():
    assert OPTIN_SCRIPT.exists(), (
        f"scripts/scihub_optin.py fehlt — setup.sh kann SciHub-Opt-in nicht "
        f"implementieren ({OPTIN_SCRIPT})"
    )


def test_scihub_optin_importable():
    import scihub_optin  # noqa: F401

    assert hasattr(scihub_optin, "set_optin")
    assert hasattr(scihub_optin, "_prompt_optin")


# ---------------------------------------------------------------------------
# 2. set_optin schreibt das Flag korrekt
# ---------------------------------------------------------------------------

def test_set_optin_creates_file_with_false_default(tmp_path):
    import scihub_optin

    active = tmp_path / "active.yaml"
    scihub_optin.set_optin(active, False)
    assert active.exists()
    data = yaml.safe_load(active.read_text())
    assert data["scihub_optin"] is False


def test_set_optin_writes_true(tmp_path):
    import scihub_optin

    active = tmp_path / "active.yaml"
    scihub_optin.set_optin(active, True)
    data = yaml.safe_load(active.read_text())
    assert data["scihub_optin"] is True


def test_set_optin_preserves_other_keys(tmp_path):
    import scihub_optin

    active = tmp_path / "active.yaml"
    active.write_text("uni: tum\nauth_type: shibboleth\nscihub_optin: false\n")
    scihub_optin.set_optin(active, True)
    data = yaml.safe_load(active.read_text())
    assert data["scihub_optin"] is True
    assert data["uni"] == "tum"
    assert data["auth_type"] == "shibboleth"


def test_set_optin_idempotent(tmp_path):
    import scihub_optin

    active = tmp_path / "active.yaml"
    scihub_optin.set_optin(active, True)
    first = active.read_text()
    scihub_optin.set_optin(active, True)
    second = active.read_text()
    data = yaml.safe_load(second)
    assert data["scihub_optin"] is True
    # Re-run darf keine doppelten Keys o.ae. erzeugen
    assert second.count("scihub_optin") == 1
    assert first == second


def test_set_optin_overwrites_existing_value(tmp_path):
    import scihub_optin

    active = tmp_path / "active.yaml"
    scihub_optin.set_optin(active, True)
    scihub_optin.set_optin(active, False)
    data = yaml.safe_load(active.read_text())
    assert data["scihub_optin"] is False
    assert active.read_text().count("scihub_optin") == 1


# ---------------------------------------------------------------------------
# 3. Prompt-Default ist sicher (False) bei nicht-interaktivem stdin
# ---------------------------------------------------------------------------

def test_prompt_optin_defaults_false_non_interactive(monkeypatch):
    import scihub_optin

    class _FakeStdin:
        @staticmethod
        def isatty():
            return False

    monkeypatch.setattr(sys, "stdin", _FakeStdin())
    assert scihub_optin._prompt_optin() is False


# ---------------------------------------------------------------------------
# 4. setup.sh stimmt mit setup.md ueberein
# ---------------------------------------------------------------------------

def test_setup_sh_invokes_scihub_optin():
    content = SETUP_SH.read_text(encoding="utf-8")
    assert "scihub_optin.py" in content, (
        "setup.sh muss den SciHub-Opt-in-Helper aufrufen — setup.md Schritt 7 "
        "verlangt das, setup.sh implementierte es bisher nicht (Issue #234)"
    )


def test_setup_sh_numbering_has_step_six():
    """Die Nummerierung darf nicht kommentarlos 5 -> 7 springen (Issue #234)."""
    content = SETUP_SH.read_text(encoding="utf-8")
    # Schritt 6 (Projekt-Bootstrap) muss als Kommentar vorhanden sein,
    # bevor Schritt 7 (SciHub) kommt.
    assert "# 6." in content, "setup.sh fehlt Schritt-6-Kommentar (Nummerierung springt 5->7)"
    six = content.index("# 6.")
    seven = content.index("# 7.")
    assert six < seven, "Schritt 6 muss vor Schritt 7 stehen"


def test_setup_sh_prints_scihub_status_markers():
    """setup.sh muss die in setup.md dokumentierten Status-Marker ausgeben."""
    content = SETUP_SH.read_text(encoding="utf-8")
    assert "SciHub Opt-in" in content, (
        "setup.sh muss SciHub-Opt-in-Status melden (setup.md Interpretationstabelle)"
    )
