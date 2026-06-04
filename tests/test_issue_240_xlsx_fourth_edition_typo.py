"""Regressionstest fuer Issue #240.

skills/xlsx enthielt den Pfad-Tippfehler 'fouth-edition' statt 'fourth-edition':
- Das ECMA-Schema-Verzeichnis hiess 'fouth-edition'.
- skills/xlsx/scripts/office/validators/base.py referenzierte den Tippfehler dreimal
  (SCHEMA_MAPPINGS fuer '[Content_Types].xml', 'core.xml', '.rels').

Akzeptanzkriterium: Pfad korrekt geschrieben ('fourth-edition'), Schema-Mappings
loesen weiterhin auf existierende XSD-Dateien auf.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OFFICE_DIR = REPO_ROOT / "skills" / "xlsx" / "scripts" / "office"
ECMA_DIR = OFFICE_DIR / "schemas" / "ecma"
BASE_PY = OFFICE_DIR / "validators" / "base.py"


def test_fourth_edition_directory_exists_and_typo_dir_gone():
    """Das Verzeichnis ist korrekt als 'fourth-edition' benannt, der Tippfehler fehlt."""
    assert (ECMA_DIR / "fourth-edition").is_dir(), (
        "Verzeichnis 'fourth-edition' fehlt unter " + str(ECMA_DIR)
    )
    assert not (ECMA_DIR / "fouth-edition").exists(), (
        "Tippfehler-Verzeichnis 'fouth-edition' existiert noch"
    )


def test_base_py_has_no_typo():
    """base.py darf den Tippfehler 'fouth-edition' nicht mehr enthalten."""
    text = BASE_PY.read_text(encoding="utf-8")
    assert "fouth-edition" not in text, (
        "Tippfehler 'fouth-edition' steht noch in base.py"
    )
    assert "ecma/fourth-edition/" in text, (
        "Korrigierter Pfad 'ecma/fourth-edition/' fehlt in base.py"
    )


def _ecma_schema_paths():
    """ecma/-Schema-Pfade aus den SCHEMA_MAPPINGS-Stringliteralen von base.py lesen.

    Dependency-frei (kein Import von base.py, das optionale Module wie defusedxml
    laedt), damit der Test in jeder Test-Umgebung laeuft statt zu skippen.
    """
    text = BASE_PY.read_text(encoding="utf-8")
    return re.findall(r'"(ecma/[^"]+\.xsd)"', text)


def test_ecma_schema_mappings_resolve_to_existing_files():
    """Alle ecma/-Schema-Mappings zeigen auf real existierende XSD-Dateien."""
    schemas_dir = OFFICE_DIR / "schemas"
    ecma_paths = _ecma_schema_paths()
    assert ecma_paths, "Keine ecma/-Schema-Pfade in base.py gefunden"
    for rel in ecma_paths:
        assert "fouth-edition" not in rel, (
            "Schema-Pfad enthaelt noch den Tippfehler: %s" % rel
        )
        target = schemas_dir / rel
        assert target.is_file(), "Schema-Datei fehlt: %s" % target
