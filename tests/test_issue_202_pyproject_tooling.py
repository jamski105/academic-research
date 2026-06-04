"""Regressionstest fuer Issue #202 — pyproject.toml + ruff/mypy + pre-commit.

Prueft die Akzeptanzkriterien aus dem Issue konkret gegen den Dateiinhalt:

- ``pyproject.toml`` existiert und enthaelt ``[project]``,
  ``[tool.pytest.ini_options]``, ``[tool.ruff]`` und ``[tool.mypy]``.
- ``[tool.pytest.ini_options]`` bricht die Discovery NICHT (testpaths == tests).
- ``.pre-commit-config.yaml`` enthaelt ruff, mypy, end-of-file-fixer,
  check-yaml und check-json.
- ``requirements.lock`` existiert (verwandt #194).
- CI (``.github/workflows/ci.yml``) fuehrt ruff + mypy aus (verwandt #184).
- README enthaelt eine CONTRIBUTING-Sektion mit pre-commit-Setup.
"""

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
REQ_LOCK = ROOT / "requirements.lock"
CI = ROOT / ".github" / "workflows" / "ci.yml"
README = ROOT / "README.md"


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pyproject_existiert():
    assert PYPROJECT.is_file(), "pyproject.toml fehlt im Repo-Root"


def test_pyproject_valides_toml():
    # darf nicht mit tomllib.TOMLDecodeError scheitern
    data = _pyproject()
    assert isinstance(data, dict)


def test_pyproject_hat_project_sektion():
    data = _pyproject()
    assert "project" in data, "[project] fehlt"
    assert data["project"].get("name"), "[project].name fehlt/leer"


def test_pyproject_hat_pytest_ini_options():
    data = _pyproject()
    pytest_cfg = data.get("tool", {}).get("pytest", {}).get("ini_options")
    assert pytest_cfg is not None, "[tool.pytest.ini_options] fehlt"


def test_pytest_discovery_nicht_gebrochen():
    """testpaths muss auf tests/ zeigen, sonst bricht die Suite-Discovery."""
    data = _pyproject()
    ini = data["tool"]["pytest"]["ini_options"]
    testpaths = ini.get("testpaths")
    assert testpaths is not None, "testpaths nicht gesetzt"
    # toml liefert entweder string oder list — beides normalisieren
    if isinstance(testpaths, str):
        testpaths = testpaths.split()
    assert "tests" in testpaths, f"testpaths zeigt nicht auf tests/: {testpaths}"


def test_pyproject_hat_ruff_sektion():
    data = _pyproject()
    assert "ruff" in data.get("tool", {}), "[tool.ruff] fehlt"


def test_pyproject_hat_mypy_sektion():
    data = _pyproject()
    assert "mypy" in data.get("tool", {}), "[tool.mypy] fehlt"


def test_precommit_existiert():
    assert PRECOMMIT.is_file(), ".pre-commit-config.yaml fehlt"


@pytest.mark.parametrize(
    "hook_id",
    ["ruff", "mypy", "end-of-file-fixer", "check-yaml", "check-json"],
)
def test_precommit_enthaelt_hook(hook_id):
    text = PRECOMMIT.read_text(encoding="utf-8")
    assert f"id: {hook_id}" in text, f"pre-commit-Hook '{hook_id}' fehlt"


def test_requirements_lock_existiert():
    assert REQ_LOCK.is_file(), "requirements.lock fehlt (verwandt #194)"


def test_ci_fuehrt_ruff_und_mypy():
    text = CI.read_text(encoding="utf-8")
    assert "ruff" in text, "CI fuehrt ruff nicht aus (verwandt #184)"
    assert "mypy" in text, "CI fuehrt mypy nicht aus (verwandt #184)"


def test_readme_contributing_mit_precommit():
    text = README.read_text(encoding="utf-8").lower()
    assert "pre-commit" in text, "README erklaert pre-commit-Setup nicht"
