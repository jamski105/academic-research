"""Regression-Guard für Issue #174: README-Badges dürfen nicht veralten.

Akzeptanzkriterien:
- Skills-Badge zeigt die tatsächliche Anzahl der SKILL.md (Claude-Code-Discovery-Count).
- Tests-Badge zeigt die tatsächliche Collect-Zahl statt "~60".
- Inhaltsverzeichnis nennt dieselbe Skill-Zahl.
- Sektion "Entwicklung und Evals" nennt nicht mehr "~60 Tests" und weist auf
  Network/External-abhängige Tests hin.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"


def _skill_count() -> int:
    """Zahl der SKILL.md unter skills/ — entspricht dem Claude-Code-Discovery-Count."""
    return len(list((REPO_ROOT / "skills").rglob("SKILL.md")))


def test_skills_badge_matches_actual_skill_count():
    text = README.read_text(encoding="utf-8")
    count = _skill_count()
    assert count == 28, f"Erwartet 28 SKILL.md, gefunden {count} (Test ggf. anpassen)."
    # Veraltetes "skills-23+"-Badge darf nicht mehr vorkommen.
    assert "skills-23+" not in text, "Veraltetes skills-23+-Badge noch vorhanden."
    badge = re.search(r"!\[Skills\]\(https://img\.shields\.io/badge/skills-(\d+)", text)
    assert badge is not None, "Skills-Badge nicht gefunden."
    assert int(badge.group(1)) == count, (
        f"Skills-Badge zeigt {badge.group(1)}, tatsächlich {count} SKILL.md."
    )


def test_toc_entry_matches_skill_count():
    text = README.read_text(encoding="utf-8")
    count = _skill_count()
    assert "Skills (23+ selbstaktivierend)" not in text, "Veralteter TOC-Eintrag 23+."
    assert f"Skills ({count} selbstaktivierend)" in text, (
        f"TOC-Eintrag nennt nicht 'Skills ({count} selbstaktivierend)'."
    )


def test_tests_badge_not_stale():
    text = README.read_text(encoding="utf-8")
    assert "tests-~60" not in text, "Veraltetes tests-~60-Badge noch vorhanden."
    badge = re.search(r"!\[Tests\]\(https://img\.shields\.io/badge/tests-([^)]+)\)", text)
    assert badge is not None, "Tests-Badge nicht gefunden."
    value = badge.group(1)
    # Stale-Form "963 passing" OHNE Collect-Angabe ist verboten.
    assert "collected" in value.lower(), (
        f"Tests-Badge nennt keine Collect-Zahl (veraltete Form): {value}"
    )
    # Badge muss die reale Collect-Zahl (vierstellig, >= 1000) enthalten.
    assert re.search(r"1\d{3}", value), (
        f"Tests-Badge enthält keine realistische Collect-Zahl: {value}"
    )


def test_dev_section_no_stale_sixty_and_mentions_external():
    text = README.read_text(encoding="utf-8")
    # Sektion isolieren.
    start = text.index("## Entwicklung und Evals")
    section = text[start:]
    assert "~60 Tests" not in section, "Sektion nennt noch '~60 Tests'."
    # Hinweis auf Network/External-abhängige Tests muss vorhanden sein.
    lowered = section.lower()
    assert any(token in lowered for token in ("network", "netzwerk", "external", "extern", "api-key", "api_key")), (
        "Kein Hinweis auf Network/External-abhängige Tests in 'Entwicklung und Evals'."
    )
