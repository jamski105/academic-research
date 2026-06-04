"""Token-Regression-Test fuer Skills (Issue #200).

Liest tests/baselines/tokens.json mit Schema ``{<skill>: <token_count>}``.

Die Baseline ist nicht mehr leer: sie haelt fuer jeden nicht-vendored Skill
die gemessene Token-Groesse (cl100k-Proxy: 4 Zeichen ~ 1 Token). Der Test
skippt damit NICHT mehr stillschweigend, sondern:

- schlaegt fehl, wenn die Baseline fehlt oder leer ist (gegen stilles Skippen),
- schlaegt fehl, wenn ein Skill +20% gegenueber der Baseline waechst (Drift-Alarm),
- schlaegt fehl, wenn ein Skill in der Baseline fehlt (neue Skills muessen erfasst werden).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

BASELINE_FILE = Path(__file__).parent.parent / "baselines" / "tokens.json"
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
VENDORED_SKILLS = {"xlsx", "_common", "humanizer-de"}
THRESHOLD = 1.20  # 20 % Anstieg gegenueber Baseline ist erlaubt, mehr nicht.
CHARS_PER_TOKEN = 4  # cl100k-Proxy, identisch zum Kommentar in test_skills_manifest.py.


def _all_skill_paths() -> list[Path]:
    return sorted(
        p
        for p in SKILLS_DIR.glob("*/SKILL.md")
        if p.parent.name not in VENDORED_SKILLS
    )


def estimate_tokens(text: str) -> int:
    """Deterministischer cl100k-Proxy: aufgerundete Zeichenzahl / 4.

    Offline-hermetisch, keine externe Tokenizer-Abhaengigkeit.
    """
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def _load_baseline() -> dict:
    assert BASELINE_FILE.exists(), (
        f"Baseline fehlt: {BASELINE_FILE} -- Token-Regression kann nicht pruefen"
    )
    data = json.loads(BASELINE_FILE.read_text())
    assert data, (
        "tokens.json ist leer -- Token-Regression wuerde stillschweigend skippen. "
        "Baseline muss befuellt sein (Issue #200)."
    )
    return data


def _check_regression(skill: str, tokens: int, baseline: dict) -> list[str]:
    """Prueft, ob ``tokens`` innerhalb +20% der Baseline fuer ``skill`` liegt.

    Gibt Liste von Fehlermeldungen zurueck (leer = OK).
    """
    errors: list[str] = []
    baseline_tokens = baseline.get(skill)
    if baseline_tokens is None:
        return [f"{skill}: kein Baseline-Eintrag in tokens.json"]
    if baseline_tokens > 0 and tokens > baseline_tokens * THRESHOLD:
        errors.append(
            f"{skill}: tokens {tokens} > baseline "
            f"{baseline_tokens} * {THRESHOLD} = {baseline_tokens * THRESHOLD:.0f}"
        )
    return errors


def test_baseline_file_exists():
    """tokens.json muss vorhanden sein."""
    assert BASELINE_FILE.exists(), f"Baseline fehlt: {BASELINE_FILE}"


def test_baseline_not_empty():
    """tokens.json darf NICHT leer sein (sonst skippt die Regression stillschweigend)."""
    data = json.loads(BASELINE_FILE.read_text())
    assert data, "tokens.json ist leer -- Baseline muss erfasst sein (Issue #200)"


def test_baseline_schema_valid():
    """Schema ``{<skill>: <int token_count>}``."""
    data = _load_baseline()
    for skill, tokens in data.items():
        assert isinstance(skill, str), f"Skill-Key {skill!r} muss str sein"
        assert isinstance(tokens, int), (
            f"{skill}: token_count muss int sein, ist {type(tokens).__name__}"
        )
        assert tokens > 0, f"{skill}: token_count muss > 0 sein"


def test_baseline_covers_all_skills():
    """Jeder nicht-vendored Skill muss in der Baseline stehen."""
    baseline = _load_baseline()
    skill_names = {p.parent.name for p in _all_skill_paths()}
    missing = sorted(skill_names - set(baseline))
    assert not missing, f"Skills ohne Baseline-Eintrag: {missing}"


def test_estimate_tokens_proxy():
    """Token-Proxy: aufgerundete Zeichenzahl / 4."""
    assert estimate_tokens("") == 0
    assert estimate_tokens("a") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2
    assert estimate_tokens("x" * 1400) == 350


def test_stable_values_pass():
    """Werte identisch zur Baseline duerfen nicht fehlschlagen."""
    errors = _check_regression("skill-x", 1000, {"skill-x": 1000})
    assert errors == [], f"Stabile Werte schlagen fehl: {errors}"


def test_small_increase_passes():
    """Anstieg unter 20% darf nicht fehlschlagen."""
    # +19%
    errors = _check_regression("skill-x", 1190, {"skill-x": 1000})
    assert errors == [], f"Kleiner Anstieg schlaegt fehl: {errors}"


def test_large_increase_fails():
    """Anstieg ueber 20% muss als Drift erkannt werden."""
    # +21%
    errors = _check_regression("skill-x", 1210, {"skill-x": 1000})
    assert len(errors) == 1, f"Drift nicht erkannt: {errors}"
    assert "tokens" in errors[0]


def test_missing_skill_in_baseline_fails():
    """Ein Skill ohne Baseline-Eintrag muss als Fehler gemeldet werden."""
    errors = _check_regression("neuer-skill", 500, {"alter-skill": 1000})
    assert len(errors) == 1
    assert "kein Baseline-Eintrag" in errors[0]


def test_real_baseline_no_drift():
    """Echte Baseline: kein Skill darf +20% Token-Drift aufweisen.

    Dies ist der eigentliche Regressions-Waechter (Issue #200): nicht mehr
    stilles Skippen, sondern harter Vergleich aller realen Skills.
    """
    baseline = _load_baseline()
    all_errors: list[str] = []
    for skill_path in _all_skill_paths():
        skill = skill_path.parent.name
        tokens = estimate_tokens(skill_path.read_text())
        all_errors.extend(_check_regression(skill, tokens, baseline))
    assert not all_errors, "Token-Regression erkannt:\n" + "\n".join(all_errors)
