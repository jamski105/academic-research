"""Regressionstest fuer Issue #212: ASCII-Doppelung der Trigger-Phrasen.

Befund (Doku-Drift Round-2 LOW): Die ASCII-Doppelung von Trigger-Phrasen in
``skills/*/SKILL.md`` war inkonsistent. Manche Skills doppeln einen deutschen
Trigger mit Umlauten als exakte ASCII-Transliteration (z.B. ``"Foerderantrag"``
neben ``"Förderantrag"``), andere fehlen ganz, und einige mischten eine
englische Uebersetzung statt einer Transliteration ein (z.B.
``"... schreiben / ... write"``). Nutzer mit reiner ASCII-Eingabe (SSH-Terminal
ohne UTF-8) verpassen so Skills, deren Trigger nur in Umlaut-Form vorliegen.

Policy (Mehrheitskonvention, 14 von 26 Skills hatten sie bereits): JEDE
nicht-vendored ``description`` enthaelt MINDESTENS eine echte ASCII-Doppelung:
eine in Anfuehrungszeichen stehende Trigger-Phrase mit Umlaut, unmittelbar
gefolgt von `` / `` und der exakten ASCII-Transliteration (ae/oe/ue/ss).

Dieser Test prueft die Konsistenz ueber alle SKILL.md.
"""

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
# Vendored / fremde Skills folgen nicht der deutschen Trigger-Konvention.
VENDORED_SKILLS = {"xlsx", "_common", "humanizer-de"}
ALL_SKILLS = sorted(
    p for p in SKILLS_DIR.glob("*/SKILL.md") if p.parent.name not in VENDORED_SKILLS
)

_UMLAUTS = "äöüÄÖÜß"
_TRANSLIT = [
    ("ä", "ae"), ("ö", "oe"), ("ü", "ue"),
    ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"),
    ("ß", "ss"),
]


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    current_key: str | None = None
    for line in m.group(1).splitlines():
        if re.match(r"^[a-zA-Z_-]+:\s*", line):
            key, _, val = line.partition(":")
            current_key = key.strip()
            fm[current_key] = val.strip()
        elif current_key and line.startswith("  "):
            fm[current_key] += " " + line.strip()
    return fm


def _asciify(s: str) -> str:
    for src, dst in _TRANSLIT:
        s = s.replace(src, dst)
    return s


def _ascii_doublings(desc: str) -> list[tuple[str, str]]:
    """Echte ASCII-Doppelungen innerhalb der zitierten Trigger-Phrasen.

    Erkennt sowohl Phrasen-Doppelung (``"Phrase / Asciified-Phrase"``) als auch
    Wort-Doppelung (``"Wort / Asciified-Wort Rest"``). Eine englische
    Uebersetzung statt einer Transliteration zaehlt NICHT.
    """
    found: list[tuple[str, str]] = []
    for quoted in re.findall(r'"([^"]*)"', desc):
        if " / " not in quoted:
            continue
        segs = quoted.split(" / ")
        for i in range(len(segs) - 1):
            left, right = segs[i].strip(), segs[i + 1].strip()
            if not left or not right:
                continue
            # 1) ganze Segment-Doppelung
            if any(c in left for c in _UMLAUTS) and (
                _asciify(left).lower() == right.lower()
                and left.lower() != right.lower()
            ):
                found.append((left, right))
                continue
            # 2) Wort-Doppelung: letztes Wort links vs. erstes Wort rechts
            lw = left.split()[-1]
            rw = right.split()[0]
            if any(c in lw for c in _UMLAUTS) and (
                _asciify(lw).lower() == rw.lower() and lw.lower() != rw.lower()
            ):
                found.append((lw, rw))
    return found


@pytest.mark.parametrize("skill_path", ALL_SKILLS, ids=lambda p: p.parent.name)
def test_trigger_phrases_have_utf8_and_ascii_variant(skill_path: Path) -> None:
    """Jede description enthaelt >= 1 echte ASCII-Doppelung einer Trigger-Phrase."""
    fm = _frontmatter(skill_path)
    desc = fm.get("description", "")
    assert desc, f"{skill_path}: description fehlt"
    doublings = _ascii_doublings(desc)
    assert len(doublings) >= 1, (
        f"{skill_path.parent.name}: keine echte ASCII-Doppelung (UTF-8 + ASCII) "
        f"in einer Trigger-Phrase gefunden. Erwartet z.B. "
        f'"Förderantrag / Foerderantrag". description={desc[:200]!r}'
    )


def test_ascii_doubling_policy_consistent_across_all_skills() -> None:
    """Konsistenz-Gesamtcheck: KEIN nicht-vendored Skill ohne ASCII-Doppelung."""
    missing = []
    for skill_path in ALL_SKILLS:
        desc = _frontmatter(skill_path).get("description", "")
        if not _ascii_doublings(desc):
            missing.append(skill_path.parent.name)
    assert not missing, (
        "Skills ohne echte ASCII-Doppelung der Trigger-Phrasen "
        f"(inkonsistent gegen Mehrheitskonvention): {sorted(missing)}"
    )
