"""Regressionstest fuer Issue #181.

Vereinheitlicht ${CLAUDE_PLUGIN_ROOT}-Pfade in allen Skills.

Akzeptanzkriterien (aus dem Issue):
- Alle Skript-Aufrufe in SKILL.md auf
  ``${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/<file>`` umstellen.
- Alle References-Verweise auf
  ``${CLAUDE_PLUGIN_ROOT}/skills/<name>/references/<file>``.
- Gold-Standard: ``skills/prisma-flow/SKILL.md``.

Der Test prueft, dass in keiner ``skills/*/SKILL.md`` mehr ein
hardcodierter, relativer Plugin-Pfad der Form
``skills/<name>/(scripts|references)/...`` vorkommt, der NICHT direkt
hinter ``${CLAUDE_PLUGIN_ROOT}/`` steht. Das einheitliche Pattern ist
``${CLAUDE_PLUGIN_ROOT}/skills/<name>/(scripts|references)/<file>``.
"""

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
ALL_SKILL_MD = sorted(SKILLS_DIR.glob("*/SKILL.md"))

# Matcht einen relativen Plugin-Pfad ``skills/<name>/(scripts|references)/``.
HARDCODED_PATH = re.compile(r"skills/[a-z0-9][a-z0-9-]*/(?:scripts|references)/")

# Erlaubtes, einheitliches Pattern: ``${CLAUDE_PLUGIN_ROOT}/skills/...``.
ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"


def _hardcoded_hits(text: str) -> list[tuple[int, str]]:
    """Liefert (Zeilennummer, Zeile) fuer jede hardcodierte Plugin-Pfad-Stelle.

    Eine Stelle gilt als hardcodiert, wenn das Match NICHT direkt hinter
    ``${CLAUDE_PLUGIN_ROOT}/`` steht.
    """
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in HARDCODED_PATH.finditer(line):
            start = m.start()
            prefix = line[:start]
            if prefix.endswith(ROOT_PREFIX):
                continue
            hits.append((lineno, line.strip()))
            break
    return hits


def test_skill_md_files_exist():
    assert ALL_SKILL_MD, "Keine SKILL.md gefunden – Pfad-Setup pruefen."


@pytest.mark.parametrize("skill_md", ALL_SKILL_MD, ids=lambda p: p.parent.name)
def test_no_hardcoded_plugin_paths(skill_md: Path):
    text = skill_md.read_text(encoding="utf-8")
    hits = _hardcoded_hits(text)
    assert not hits, (
        f"{skill_md.relative_to(SKILLS_DIR.parent)} enthaelt hardcodierte "
        f"Plugin-Pfade ohne ${{CLAUDE_PLUGIN_ROOT}}-Prefix:\n"
        + "\n".join(f"  L{ln}: {body}" for ln, body in hits)
    )


def test_gold_standard_prisma_flow_uses_root():
    """Gold-Standard muss das einheitliche Pattern weiterhin nutzen."""
    text = (SKILLS_DIR / "prisma-flow" / "SKILL.md").read_text(encoding="utf-8")
    assert ROOT_PREFIX + "skills/prisma-flow/scripts/" in text
    assert ROOT_PREFIX + "skills/prisma-flow/references/" in text
    assert not _hardcoded_hits(text)
