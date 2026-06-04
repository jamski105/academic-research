"""Regressions-Tests fuer README/Doku-Konsistenz des Hook-Stacks (#205).

Testet:
  (a) README enthaelt NICHT den erfundenen "SessionMid"-Event.
  (b) Die im README genannten Hook-Events stimmen mit den real in hooks/hooks.json
      konfigurierten Events ueberein.
  (c) MIGRATION-v5-to-v6.md enthaelt ebenfalls kein "SessionMid".
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
HOOKS_JSON = REPO_ROOT / "hooks" / "hooks.json"
MIGRATION_GUIDE = REPO_ROOT / "docs" / "MIGRATION-v5-to-v6.md"


def _readme_hooks_section() -> str:
    """Gibt den Inhalt der Hooks-Stack-Sektion aus dem README zurueck."""
    text = README.read_text(encoding="utf-8")
    match = re.search(r"## Hooks-Stack.*?(?=\n## |\Z)", text, re.DOTALL)
    assert match, "README enthaelt keine '## Hooks-Stack'-Sektion"
    return match.group(0)


def test_readme_does_not_contain_session_mid():
    """README darf 'SessionMid' nicht erwaehnen — dieser Event existiert nicht in Claude Code."""
    readme_text = README.read_text(encoding="utf-8")
    assert "SessionMid" not in readme_text, (
        "README enthaelt den nicht-existierenden Claude-Code-Event 'SessionMid'. "
        "Der echte Event-Name ist 'Notification' (und 'PostCompact')."
    )


def test_migration_guide_does_not_contain_session_mid():
    """MIGRATION-v5-to-v6.md darf 'SessionMid' nicht erwaehnen."""
    if not MIGRATION_GUIDE.exists():
        import pytest
        pytest.skip("MIGRATION-v5-to-v6.md nicht vorhanden")
    migration_text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    assert "SessionMid" not in migration_text, (
        "MIGRATION-v5-to-v6.md enthaelt den nicht-existierenden Event 'SessionMid'."
    )


def test_readme_hook_events_match_hooks_json():
    """Die Hook-Events in der README-Tabelle muessen mit hooks/hooks.json uebereinstimmen."""
    hooks_data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    real_events = set(hooks_data["hooks"].keys())

    hooks_section = _readme_hooks_section()

    # Alle bekannten echten Events muessen in der Hooks-Sektion erwaehnt sein
    for event in real_events:
        assert event in hooks_section, (
            f"Event '{event}' ist in hooks/hooks.json konfiguriert, "
            f"wird aber in der README-Hooks-Stack-Sektion nicht erwaehnt."
        )


def test_readme_hook_count_not_four():
    """README soll nicht mehr behaupten, es gaebe 'vier Hooks' (tatsaechlich 7 Events)."""
    hooks_section = _readme_hooks_section()
    assert "vier Hooks" not in hooks_section, (
        "README behauptet noch 'vier Hooks', aber hooks/hooks.json konfiguriert 7 Events."
    )


def test_hooks_json_has_expected_events():
    """hooks/hooks.json muss alle sieben erwarteten Events enthalten."""
    hooks_data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    real_events = set(hooks_data["hooks"].keys())

    expected_events = {
        "PreToolUse",
        "PostToolUse",
        "PreCompact",
        "Notification",
        "PostCompact",
        "SessionStart",
        "Stop",
    }
    assert expected_events == real_events, (
        f"hooks.json enthaelt andere Events als erwartet.\n"
        f"Erwartet: {sorted(expected_events)}\n"
        f"Gefunden: {sorted(real_events)}"
    )
