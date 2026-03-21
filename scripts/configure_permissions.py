#!/usr/bin/env python3
"""Configure Claude Code permissions for academic-research v4.

Adds required tool permissions to ~/.claude/settings.local.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.local.json"

REQUIRED_PERMISSIONS = [
    "Bash(~/.academic-research/venv/bin/python *)",
    "Bash(~/.academic-research/venv/bin/pip *)",
    "Bash(python3 *)",
    "Bash(mkdir *)",
    "Bash(ls *)",
    "Bash(cat *)",
    "Bash(npx playwright *)",
    "Bash(npx @playwright/mcp *)",
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_evaluate",
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_press_key",
    "mcp__playwright__browser_wait_for",
    "mcp__playwright__browser_tabs",
    "mcp__playwright__browser_navigate_back",
    "mcp__playwright__browser_hover",
    "mcp__playwright__browser_close",
    "mcp__playwright__browser_fill_form",
    "mcp__playwright__browser_take_screenshot",
]


def main() -> int:
    settings: dict = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    allow_list: list[str] = settings.get("permissions", {}).get("allow", [])
    added = 0
    for perm in REQUIRED_PERMISSIONS:
        if perm not in allow_list:
            allow_list.append(perm)
            added += 1

    settings.setdefault("permissions", {})["allow"] = allow_list
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"✅ Permissions updated ({added} new rules added)")
    print(f"   File: {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
