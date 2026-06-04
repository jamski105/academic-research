"""Regressionstest fuer Issue #173.

`agents/` darf ausschliesslich Sub-Agent-`.md`-Dateien enthalten, damit die
Claude-Code-Auto-Discovery fuer `agents/` nicht mit Python-Files vermischt wird.
Die Auth-Logik-Bibliothek gehoert nach `scripts/`.

Akzeptanzkriterien:
- `find agents -name '*.py'` ist leer (kein Python in `agents/`).
- `agents/__init__.py` existiert nicht mehr.
- `scripts/auth_helper_lib.py` existiert und ist als `scripts.auth_helper_lib`
  importierbar (inkl. der oeffentlichen Auth-Funktionen).
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def test_agents_dir_contains_no_python_files():
    """`agents/` enthaelt keine `.py`-Dateien mehr (Smoke-Test aus dem Issue)."""
    py_files = sorted(p.name for p in AGENTS_DIR.rglob("*.py"))
    assert py_files == [], f"agents/ enthaelt noch Python-Files: {py_files}"


def test_agents_init_py_removed():
    """`agents/__init__.py` wurde geloescht."""
    assert not (AGENTS_DIR / "__init__.py").exists()


def test_auth_helper_lib_moved_to_scripts():
    """Die Auth-Logik-Bibliothek liegt jetzt unter `scripts/`."""
    assert (SCRIPTS_DIR / "auth_helper_lib.py").exists()
    assert not (AGENTS_DIR / "auth_helper_lib.py").exists()


def test_auth_helper_lib_importable_from_scripts():
    """Die oeffentlichen Auth-Funktionen sind unter `scripts.auth_helper_lib` importierbar."""
    from scripts.auth_helper_lib import (  # noqa: F401
        InsecureProfilePermissionsError,
        ProfileSchemaError,
        build_auth_flow_result,
        check_profile_permissions,
        detect_auth_type,
        load_credentials,
        validate_profile_schema,
    )
