"""
Tests fuer Issue #201 — Python-Version-Konsistenz.

Befund: README sagte "Python 3.10+", real wird 3.12/3.14 genutzt (CI nutzt 3.12).
Die Versionsangaben muessen konsistent sein zwischen README, pyproject.toml,
CI-Matrix und setup.sh.

5 Test-Cases (kein LLM-Call, keine Netzwerk-/Browser-Automation):
1. README nennt NICHT mehr "3.10+" und nennt die korrekte Mindestversion 3.11.
2. pyproject.toml existiert mit requires-python = ">=3.11".
3. CI-Matrix enthaelt mindestens 3.11, 3.12, 3.13.
4. setup.sh prueft die Python-Version vor der venv-Erstellung.
5. Konsistenz: die in README/pyproject genannte Mindestversion stimmt mit der
   kleinsten in der CI getesteten Version ueberein.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
SETUP_SH = REPO_ROOT / "scripts" / "setup.sh"

MIN_VERSION = (3, 11)


def _ver_tuple(s: str) -> tuple[int, int]:
    parts = s.strip().strip('"').strip("'").split(".")
    return (int(parts[0]), int(parts[1]))


# ---------------------------------------------------------------------------
# 1. README
# ---------------------------------------------------------------------------

def test_readme_no_stale_310():
    text = README.read_text(encoding="utf-8")
    assert "3.10+" not in text, "README nennt weiterhin das veraltete 'Python 3.10+'."


def test_readme_states_min_311():
    text = README.read_text(encoding="utf-8")
    # Es muss eine Angabe geben, die 3.11 als Mindestversion ausweist.
    assert re.search(r"Python\s*3\.11\+", text), (
        "README muss 'Python 3.11+' als Mindestversion ausweisen."
    )


# ---------------------------------------------------------------------------
# 2. pyproject.toml mit requires-python
# ---------------------------------------------------------------------------

def test_pyproject_exists():
    assert PYPROJECT.exists(), "pyproject.toml fehlt im Repo-Root."


def test_pyproject_requires_python_311():
    assert PYPROJECT.exists(), "pyproject.toml fehlt im Repo-Root."
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'requires-python\s*=\s*"(>=)?\s*([0-9.]+)"', text)
    assert m, "pyproject.toml hat kein requires-python-Feld."
    assert _ver_tuple(m.group(2)) == MIN_VERSION, (
        f"requires-python muss >=3.11 sein, gefunden: {m.group(0)}"
    )


# ---------------------------------------------------------------------------
# 3. CI-Matrix
# ---------------------------------------------------------------------------

def test_ci_matrix_covers_311_312_313():
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    for v in ("3.11", "3.12", "3.13"):
        assert v in text, f"CI-Workflow testet Version {v} nicht."


# ---------------------------------------------------------------------------
# 4. setup.sh prueft Python-Version
# ---------------------------------------------------------------------------

def test_setup_sh_checks_python_version():
    text = SETUP_SH.read_text(encoding="utf-8")
    # Vor der venv-Erstellung (python3 -m venv) muss eine Versionspruefung stehen.
    venv_idx = text.find("python3 -m venv")
    assert venv_idx != -1, "setup.sh erstellt keine venv mehr?"
    head = text[:venv_idx]
    assert "sys.version_info" in head or "version_info" in head, (
        "setup.sh prueft die Python-Version nicht vor der venv-Erstellung."
    )
    assert "3.11" in head or "(3, 11)" in head, (
        "setup.sh referenziert die Mindestversion 3.11 nicht in der Versionspruefung."
    )


# ---------------------------------------------------------------------------
# 5. Konsistenz README/pyproject <-> CI-Mindestversion
# ---------------------------------------------------------------------------

def test_min_version_consistent_across_readme_pyproject_ci():
    readme = README.read_text(encoding="utf-8")
    m_readme = re.search(r"Python\s*3\.(\d+)\+", readme)
    assert m_readme, "README nennt keine 'Python 3.x+'-Mindestversion."
    readme_min = (3, int(m_readme.group(1)))

    pyproject = PYPROJECT.read_text(encoding="utf-8")
    m_py = re.search(r'requires-python\s*=\s*">=\s*([0-9.]+)"', pyproject)
    assert m_py, "pyproject.toml hat kein '>='-requires-python."
    py_min = _ver_tuple(m_py.group(1))

    ci = CI_WORKFLOW.read_text(encoding="utf-8")
    ci_versions = sorted(
        {_ver_tuple(v) for v in re.findall(r'python-version:\s*"?(3\.\d+)"?', ci)}
    )
    assert ci_versions, "CI-Workflow nennt keine python-version-Eintraege."
    ci_min = ci_versions[0]

    assert readme_min == py_min == ci_min == MIN_VERSION, (
        f"Mindestversionen inkonsistent: README={readme_min}, "
        f"pyproject={py_min}, CI-min={ci_min}, erwartet={MIN_VERSION}"
    )
