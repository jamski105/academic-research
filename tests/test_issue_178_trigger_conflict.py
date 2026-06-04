"""Regression-Guard fuer Issue #178 — Trigger-Konflikt chapter-writer vs advisor.

User-Phrase "Mein Diskussionskapitel braucht Feedback" durfte frueher BEIDE
Skills triggern. Dieser Test kodiert die Akzeptanzkriterien aus #178 offline
(kein Netzwerk noetig): er asserted die geforderten Trigger-Abgrenzungen und
die wechselseitige Abgrenzungs-Section direkt im SKILL.md-Text.

Akzeptanzkriterien (#178):
- advisor: Trigger auf strukturelle Feedback-Phrasen beschraenken
  ("Gliederung pruefen", "Argumentations-Outline review", "Expose feedback");
  die mehrdeutige Phrase "Kapitel-Feedback" entfaellt.
- chapter-writer: Trigger auf Schreib-Aktion fokussieren
  ("Kapitel SCHREIBEN", "Diskussionsteil drafted", "Theorieteil ausformulieren").
- Beide SKILL.md: Abgrenzungs-Section, die chapter-writer = Text-Output und
  advisor = Review/Feedback ohne Neuschrieb klar trennt.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"
ADVISOR_MD = SKILLS_DIR / "advisor" / "SKILL.md"
CHAPTER_WRITER_MD = SKILLS_DIR / "chapter-writer" / "SKILL.md"


def _frontmatter_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, f"{path}: kein Frontmatter gefunden"
    fm = m.group(1)
    desc_m = re.search(r"^description:\s*\|?\s*(.+?)(?=^[a-zA-Z_-]+:|\Z)", fm, re.M | re.S)
    assert desc_m, f"{path}: keine description im Frontmatter"
    return " ".join(desc_m.group(1).split())


def _abgrenzung_section(path: Path) -> str:
    """Extrahiert den Text der '## Abgrenzung'-Section (bis zur naechsten H2)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Abgrenzung\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"{path}: keine '## Abgrenzung'-Section gefunden"
    return m.group(1)


# --- advisor: Trigger auf strukturelles Feedback beschraenken --------------


def test_advisor_no_kapitel_feedback_trigger() -> None:
    """Die mehrdeutige Phrase 'Kapitel-Feedback' darf advisor NICHT mehr triggern."""
    desc = _frontmatter_description(ADVISOR_MD)
    assert "Kapitel-Feedback" not in desc, (
        "advisor description enthaelt noch die mehrdeutige Phrase 'Kapitel-Feedback' "
        "— sie kollidiert mit chapter-writer (#178)."
    )


def test_advisor_has_structural_feedback_triggers() -> None:
    """advisor muss strukturelle Feedback-Phrasen als Trigger fuehren."""
    desc = _frontmatter_description(ADVISOR_MD)
    assert "Gliederung prüfen" in desc or "Gliederung pruefen" in desc, (
        "advisor description fehlt der strukturelle Trigger 'Gliederung pruefen'."
    )
    assert "Argumentations-Outline review" in desc, (
        "advisor description fehlt der strukturelle Trigger 'Argumentations-Outline review'."
    )
    assert "Exposé feedback" in desc or "Expose feedback" in desc, (
        "advisor description fehlt der strukturelle Trigger 'Expose feedback'."
    )


# --- chapter-writer: Trigger auf Schreib-Aktion fokussieren -----------------


def test_chapter_writer_has_write_action_triggers() -> None:
    """chapter-writer muss explizite Schreib-Aktions-Phrasen als Trigger fuehren."""
    desc = _frontmatter_description(CHAPTER_WRITER_MD)
    assert "Kapitel SCHREIBEN" in desc, (
        "chapter-writer description fehlt der Schreib-Trigger 'Kapitel SCHREIBEN'."
    )
    assert "Diskussionsteil drafted" in desc, (
        "chapter-writer description fehlt der Schreib-Trigger 'Diskussionsteil drafted'."
    )
    assert "Theorieteil ausformulieren" in desc, (
        "chapter-writer description fehlt der Schreib-Trigger 'Theorieteil ausformulieren'."
    )


def test_chapter_writer_no_bare_feedback_trigger() -> None:
    """chapter-writer darf keine reinen Feedback-Phrasen als Trigger fuehren."""
    desc = _frontmatter_description(CHAPTER_WRITER_MD)
    assert "Kapitel-Feedback" not in desc, (
        "chapter-writer description enthaelt 'Kapitel-Feedback' — gehoert zu advisor (#178)."
    )


# --- Wechselseitige Abgrenzungs-Section -------------------------------------


def test_chapter_writer_abgrenzung_marks_text_output() -> None:
    """chapter-writer Abgrenzung muss sich als Text-Output gegen advisor abgrenzen."""
    section = _abgrenzung_section(CHAPTER_WRITER_MD)
    assert "advisor" in section, (
        "chapter-writer Abgrenzung verweist nicht auf 'advisor' (#178)."
    )
    assert "Text" in section or "Output" in section, (
        "chapter-writer Abgrenzung beschreibt nicht den Text-Output-Charakter (#178)."
    )


def test_advisor_abgrenzung_marks_review_no_rewrite() -> None:
    """advisor Abgrenzung muss Review/Feedback ohne Neuschrieb betonen."""
    section = _abgrenzung_section(ADVISOR_MD)
    assert "chapter-writer" in section, (
        "advisor Abgrenzung verweist nicht auf 'chapter-writer' (#178)."
    )
    assert "Neuschrieb" in section or "Neuschrieb" in section.replace("ß", "ss"), (
        "advisor Abgrenzung erwaehnt nicht den fehlenden Neuschrieb (#178)."
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
