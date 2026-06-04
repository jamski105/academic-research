"""Regression guard: chapter-writer/SKILL.md ### N. Überschriften sind eindeutig und fortlaufend."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_MD = REPO_ROOT / "skills" / "chapter-writer" / "SKILL.md"

# Findet alle ### N. Überschriften (z.B. ### 4. Draften)
NUMBERED_HEADING_RE = re.compile(r"^### (\d+)\.", re.MULTILINE)


def _extract_numbers(text: str) -> list[int]:
    return [int(m.group(1)) for m in NUMBERED_HEADING_RE.finditer(text)]


def test_chapter_writer_headings_unique():
    """Keine ### N.-Nummer darf doppelt vorkommen."""
    text = SKILL_MD.read_text(encoding="utf-8")
    numbers = _extract_numbers(text)
    assert len(numbers) == len(set(numbers)), (
        f"Doppelte ### N.-Nummern in {SKILL_MD}: {numbers}"
    )


def test_chapter_writer_headings_sequential():
    """### N.-Nummern müssen bei 1 starten und lückenlos aufsteigen."""
    text = SKILL_MD.read_text(encoding="utf-8")
    numbers = _extract_numbers(text)
    assert numbers, f"Keine nummerierten ### N.-Überschriften in {SKILL_MD} gefunden"
    expected = list(range(1, len(numbers) + 1))
    assert numbers == expected, (
        f"Nummern in {SKILL_MD} sind nicht fortlaufend: {numbers} (erwartet: {expected})"
    )
