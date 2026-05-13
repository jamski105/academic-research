"""Shared helpers fuer Evals-Suites.

Laedt Eval-JSON-Dateien, ruft die Claude-API auf und prueft Expectations.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

EVALS_ROOT = Path(__file__).parent.parent.parent / "evals"
SKILLS_ROOT = Path(__file__).parent.parent.parent / "skills"
AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"
BASELINES_ROOT = Path(__file__).parent.parent / "baselines"


def load_eval_file(component: str, filename: str) -> dict[str, Any]:
    path = EVALS_ROOT / component / filename
    if not path.exists():
        pytest.skip(f"Eval-Datei fehlt: {path}")
    return json.loads(path.read_text())


def load_skill_content(skill: str) -> str:
    return (SKILLS_ROOT / skill / "SKILL.md").read_text()


def load_agent_content(agent: str) -> str:
    return (AGENTS_ROOT / f"{agent}.md").read_text()


def require_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        pytest.skip("ANTHROPIC_API_KEY nicht gesetzt - Eval uebersprungen")
    return key


def call_claude(system: str, user: str, model: str = "claude-sonnet-4-6") -> str:
    if anthropic is None:
        pytest.skip("anthropic-Package nicht installiert")
    assert anthropic is not None  # narrow fuer Type-Checker nach pytest.skip
    key = require_api_key()
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        getattr(block, "text", "") for block in resp.content
    )


def check_expected(output: str, expected: dict[str, Any]) -> bool:
    t = expected.get("type")
    if t == "substring":
        return expected["value"] in output
    if t == "regex":
        return bool(re.search(expected["value"], output))
    if t == "json_field":
        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            return False
        return _jsonpath_check(parsed, expected)
    raise ValueError(f"Unbekannter expected.type: {t}")


def read_token_baseline(baseline_file: Path | None = None) -> dict[str, Any]:
    """Liest tests/baselines/tokens.json (oder angegebene Datei).

    Gibt {} zurueck wenn Datei fehlt oder leer.
    """
    path = baseline_file or (BASELINES_ROOT / "tokens.json")
    if not path.exists():
        return {}
    text = path.read_text().strip()
    if not text:
        return {}
    return json.loads(text)


def write_token_baseline(
    suite: str,
    case_id: str,
    tokens_in: int,
    tokens_out: int,
    baseline_file: Path | None = None,
) -> None:
    """Schreibt tokens_in/tokens_out fuer eine Suite+Case in tokens.json.

    Mergt mit vorhandenen Daten (ueberschreibt nur den eigenen Eintrag).
    """
    path = baseline_file or (BASELINES_ROOT / "tokens.json")
    data = read_token_baseline(baseline_file=path)
    if suite not in data:
        data[suite] = {}
    data[suite][case_id] = {"tokens_in": tokens_in, "tokens_out": tokens_out}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def call_claude_with_tokens(
    system: str,
    user: str,
    model: str = "claude-sonnet-4-6",
) -> tuple[str, int, int]:
    """Ruft Claude auf und gibt (text, tokens_in, tokens_out) zurueck.

    Benoetigt ANTHROPIC_API_KEY. Ohne Key: pytest.skip().
    """
    if anthropic is None:
        pytest.skip("anthropic-Package nicht installiert")
    assert anthropic is not None
    key = require_api_key()
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(getattr(block, "text", "") for block in resp.content)
    tokens_in = resp.usage.input_tokens if resp.usage else 0
    tokens_out = resp.usage.output_tokens if resp.usage else 0
    return text, tokens_in, tokens_out


def _jsonpath_check(obj: Any, expected: dict[str, Any]) -> bool:
    path = expected.get("path", "$")
    check = expected.get("check", "exists")
    # Minimaler JSONPath: $.a.b[0].c - kein Full-Feature JSONPath noetig.
    # Akzeptiert optionales $-Prefix (wie im Schema dokumentiert).
    normalized = path.lstrip("$") if path != "$" else ""
    current: Any = obj
    if normalized:
        segments = re.findall(r"\.(\w+)|\[(\d+)\]", normalized)
        # Ohne Segmente, aber nicht-leerer Path = Syntaxfehler (z.B. "a.b" ohne fuehrendes .)
        if not segments:
            raise ValueError(
                f"Ungueltiger JSONPath: {path!r} - erwartet '$', '$.key' oder '.key'"
            )
        for key, idx in segments:
            if key:
                if not isinstance(current, dict) or key not in current:
                    return False
                current = current[key]
            elif idx:
                if not isinstance(current, list) or int(idx) >= len(current):
                    return False
                current = current[int(idx)]
    if check == "exists":
        return current is not None
    if check == "non_empty":
        return bool(current)
    if check.startswith("equals:"):
        return str(current) == check.split(":", 1)[1]
    raise ValueError(f"Unbekannter check: {check}")
