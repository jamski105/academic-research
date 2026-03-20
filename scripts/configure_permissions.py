#!/usr/bin/env python3
"""
Adds academic-research plugin permissions to ~/.claude/settings.local.json
and removes stale session-specific entries accumulated during research sessions.
"""
import json
import os
import re

SETTINGS_PATH = os.path.expanduser("~/.claude/settings.local.json")

REQUIRED_PERMISSIONS = [
    "mcp__plugin_academic-research_playwright__browser_navigate",
    "mcp__plugin_academic-research_playwright__browser_snapshot",
    "mcp__plugin_academic-research_playwright__browser_click",
    "mcp__plugin_academic-research_playwright__browser_fill_form",
    "mcp__plugin_academic-research_playwright__browser_type",
    "mcp__plugin_academic-research_playwright__browser_press_key",
    "mcp__plugin_academic-research_playwright__browser_wait_for",
    "mcp__plugin_academic-research_playwright__browser_evaluate",
    "mcp__plugin_academic-research_playwright__browser_take_screenshot",
    "mcp__plugin_academic-research_playwright__browser_close",
    "mcp__plugin_academic-research_playwright__browser_tabs",
    "mcp__plugin_academic-research_playwright__browser_navigate_back",
    "mcp__plugin_academic-research_playwright__browser_hover",
    "mcp__plugin_academic-research_playwright__browser_select_option",
    "mcp__plugin_academic-research_playwright__browser_handle_dialog",
    "mcp__plugin_academic-research_playwright__browser_network_requests",
    "mcp__plugin_academic-research_playwright__browser_resize",
    "mcp__plugin_academic-research_playwright__browser_run_code",
    "mcp__plugin_academic-research_playwright__browser_console_messages",
    "mcp__plugin_academic-research_playwright__browser_install",
    "mcp__plugin_academic-research_playwright__browser_file_upload",
    "mcp__plugin_academic-research_playwright__browser_drag",
    "Bash(~/.academic-research/venv/bin/python*)",
    "Bash(python3*)",
]

STALE_PATTERNS = [
    re.compile(r"SESSION_DIR="),
    re.compile(r"PLUGIN_ROOT="),
    re.compile(r"__NEW_LINE_[0-9a-f]+__"),
    re.compile(r"sessions/\d{4}-\d{2}-\d{2}"),
    re.compile(r"PYTHON=\"\$HOME/\.academic-research"),
    re.compile(r"SCRIPTS=\"/Users/"),
]


def is_stale(entry: str) -> bool:
    return any(p.search(entry) for p in STALE_PATTERNS)


def main():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH) as f:
            settings = json.load(f)
    else:
        settings = {}

    settings.setdefault("permissions", {}).setdefault("allow", [])
    allow: list = settings["permissions"]["allow"]

    # Remove stale session-specific entries
    stale = [e for e in allow if is_stale(e)]
    if stale:
        allow[:] = [e for e in allow if not is_stale(e)]
        print(f"  Removed {len(stale)} stale session entries")

    # Add missing permissions
    added = 0
    for perm in REQUIRED_PERMISSIONS:
        if perm not in allow:
            allow.append(perm)
            added += 1

    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")

    print(f"  Added {added} new permissions")
    print(f"✅ Permissions configured: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
