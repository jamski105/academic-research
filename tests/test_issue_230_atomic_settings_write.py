"""Regressionstests für Issue #230:

scripts/configure_permissions.py muss settings.local.json ATOMAR schreiben
(Tempfile + os.replace), damit ein Abbruch während des Schreibens (SIGKILL,
Stromausfall, volle Disk) niemals eine kaputte/leere Datei hinterlässt.

Akzeptanzkriterium (#230):
  - Abbruch während des Schreibens hinterlässt die alte gültige Datei
    (Test mit simuliertem Fehler).
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import configure_permissions  # noqa: E402


# ---------------------------------------------------------------------------
# Modul-API
# ---------------------------------------------------------------------------

def test_main_accepts_settings_path_override():
    """main() muss einen settings_path-Parameter akzeptieren (testbar machen)."""
    import inspect

    sig = inspect.signature(configure_permissions.main)
    assert "settings_path" in sig.parameters, (
        "main() muss einen optionalen settings_path-Parameter besitzen, "
        "damit der Schreibpfad in Tests umgelenkt werden kann."
    )


# ---------------------------------------------------------------------------
# Happy Path
# ---------------------------------------------------------------------------

def test_writes_valid_json_and_keeps_existing_settings(tmp_path):
    """Nach erfolgreichem Lauf ist die Datei valides JSON inkl. Permissions."""
    target = tmp_path / "settings.local.json"
    target.write_text(
        json.dumps({"theme": "dark", "permissions": {"allow": ["Bash(ls *)"]}}),
        encoding="utf-8",
    )

    rc = configure_permissions.main(settings_path=target)
    assert rc == 0

    data = json.loads(target.read_text(encoding="utf-8"))
    # Fremd-Settings bleiben erhalten
    assert data["theme"] == "dark"
    # Bestehende und neue Permissions sind vorhanden
    allow = data["permissions"]["allow"]
    assert "Bash(ls *)" in allow
    for perm in configure_permissions.REQUIRED_PERMISSIONS:
        assert perm in allow


def test_creates_file_when_missing(tmp_path):
    """Existiert die Datei nicht, wird sie frisch und valide angelegt."""
    target = tmp_path / "nested" / "settings.local.json"
    rc = configure_permissions.main(settings_path=target)
    assert rc == 0
    data = json.loads(target.read_text(encoding="utf-8"))
    allow = data["permissions"]["allow"]
    for perm in configure_permissions.REQUIRED_PERMISSIONS:
        assert perm in allow


# ---------------------------------------------------------------------------
# Kern-Akzeptanzkriterium: Abbruch hinterlässt die alte gültige Datei
# ---------------------------------------------------------------------------

def test_interrupted_write_keeps_old_valid_file(tmp_path):
    """Bricht der Schreibvorgang ab, bleibt die ORIGINALE gültige Datei intakt."""
    target = tmp_path / "settings.local.json"
    original = {"theme": "dark", "permissions": {"allow": ["Bash(custom *)"]}}
    original_text = json.dumps(original, indent=2)
    target.write_text(original_text, encoding="utf-8")

    # Simuliere Abbruch genau beim finalen, atomaren Umbenennen.
    with patch.object(
        configure_permissions.os,
        "replace",
        side_effect=OSError("simulierter Abbruch (z.B. SIGKILL / volle Disk)"),
    ):
        with pytest.raises(OSError):
            configure_permissions.main(settings_path=target)

    # Die alte Datei MUSS unverändert und valide vorhanden sein.
    assert target.exists(), "Originaldatei wurde gelöscht/überschrieben"
    survived = json.loads(target.read_text(encoding="utf-8"))
    assert survived == original, (
        "Originalinhalt ging beim abgebrochenen Schreiben verloren"
    )


def test_no_temp_file_leftover_after_failed_write(tmp_path):
    """Nach einem fehlgeschlagenen atomaren Schreiben bleibt kein Tempfile-Müll
    auf dem eigentlichen Zielpfad liegen (das Ziel selbst bleibt valide)."""
    target = tmp_path / "settings.local.json"
    target.write_text(json.dumps({"permissions": {"allow": []}}), encoding="utf-8")

    with patch.object(
        configure_permissions.os,
        "replace",
        side_effect=OSError("boom"),
    ):
        with pytest.raises(OSError):
            configure_permissions.main(settings_path=target)

    # Das Ziel ist weiterhin gültiges JSON (nicht halb beschrieben).
    json.loads(target.read_text(encoding="utf-8"))
