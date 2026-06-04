#!/usr/bin/env python3
"""Configure Claude Code permissions for academic-research v4.

Adds required tool permissions to ~/.claude/settings.local.json.
"""

from __future__ import annotations

import json
import os
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
    "Bash(browser-use:*)",
    "Bash(browser-use *)",
]


def atomic_write_text(path: Path, text: str) -> None:
    """Schreibe ``text`` atomar nach ``path``.

    Es wird zunächst in eine temporäre Datei im selben Verzeichnis geschrieben,
    auf die Platte geflusht und anschließend per ``os.replace`` an die Zielposition
    umbenannt. ``os.replace`` ist auf POSIX und Windows atomar. Bricht der Prozess
    vor dem ``os.replace`` ab (SIGKILL, Stromausfall, volle Disk), bleibt die alte
    Zieldatei unverändert erhalten; ein eventuell übrig gebliebenes Tempfile wird
    weggeräumt.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        # Bei jedem Fehler keine halbfertige Tempdatei zurücklassen.
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def main(settings_path: Path | None = None) -> int:
    settings_path = Path(settings_path) if settings_path is not None else SETTINGS_PATH

    settings: dict = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    allow_list: list[str] = settings.get("permissions", {}).get("allow", [])
    added = 0
    for perm in REQUIRED_PERMISSIONS:
        if perm not in allow_list:
            allow_list.append(perm)
            added += 1

    settings.setdefault("permissions", {})["allow"] = allow_list
    atomic_write_text(
        settings_path,
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
    )

    print(f"✅ Permissions updated ({added} new rules added)")
    print(f"   File: {settings_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
