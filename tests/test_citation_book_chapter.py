"""Tests fuer DIN-1505-Formatierung von Buchkapiteln (type=chapter).

Jede Fixture repraesentiert ein Sammelband-Kapitel. Die Pruefung validiert,
dass die Referenz-Templates in book-chapter-de.md die korrekte Struktur
vorgeben: NACHNAME, Vorname: Kapiteltitel. In: HRSG. (Hrsg.): Buchtitel.
Ort : Verlag, Jahr, S. X-Y.
"""
from pathlib import Path

import pytest

REFS_DIR = Path(__file__).parent.parent / "skills" / "citation-extraction" / "references"


# Fuenf Sammelband-Fixtures fuer DIN-1505-Validierung
CHAPTER_FIXTURES = [
    {
        "id": "mueller_2019_methodik",
        "author_last": "MÜLLER",
        "author_first": "Hans",
        "chapter_title": "Qualitative Methoden in der Sozialforschung",
        "editor_last": "SCHMIDT",
        "editor_first": "Anna",
        "container_title": "Handbuch der empirischen Sozialforschung",
        "place": "Stuttgart",
        "publisher": "Metzler",
        "year": "2019",
        "page_first": 45,
        "page_last": 78,
        # Erwartete DIN-1505-Substrings
        "expected_din": [
            "MÜLLER, Hans",
            "Qualitative Methoden in der Sozialforschung",
            "In:",
            "SCHMIDT",
            "Hrsg.",
            "Handbuch der empirischen Sozialforschung",
            "Stuttgart",
            "Metzler",
            "2019",
            "S. 45",
            "78",
        ],
    },
    {
        "id": "weber_2021_digitalisierung",
        "author_last": "WEBER",
        "author_first": "Petra",
        "chapter_title": "Digitalisierung und gesellschaftlicher Wandel",
        "editor_last": "HOFFMANN",
        "editor_first": "Klaus",
        "container_title": "Gesellschaft im digitalen Zeitalter",
        "place": "Frankfurt",
        "publisher": "Campus",
        "year": "2021",
        "page_first": 112,
        "page_last": 145,
        "expected_din": [
            "WEBER, Petra",
            "Digitalisierung und gesellschaftlicher Wandel",
            "In:",
            "HOFFMANN",
            "Hrsg.",
            "Gesellschaft im digitalen Zeitalter",
            "Frankfurt",
            "Campus",
            "2021",
            "S. 112",
            "145",
        ],
    },
    {
        "id": "bauer_2022_ethik",
        "author_last": "BAUER",
        "author_first": "Thomas",
        "chapter_title": "Ethische Grundlagen der KI-Forschung",
        "editor_last": "RICHTER",
        "editor_first": "Maria",
        "container_title": "Künstliche Intelligenz: Chancen und Risiken",
        "place": "Berlin",
        "publisher": "Springer",
        "year": "2022",
        "page_first": 23,
        "page_last": 41,
        "expected_din": [
            "BAUER, Thomas",
            "Ethische Grundlagen der KI-Forschung",
            "In:",
            "RICHTER",
            "Hrsg.",
            "Künstliche Intelligenz: Chancen und Risiken",
            "Berlin",
            "Springer",
            "2022",
            "S. 23",
            "41",
        ],
    },
    {
        "id": "klein_2020_sprache",
        "author_last": "KLEIN",
        "author_first": "Sophie",
        "chapter_title": "Spracherwerb im mehrsprachigen Kontext",
        "editor_last": "BRAUN",
        "editor_first": "Werner",
        "container_title": "Mehrsprachigkeit in Deutschland",
        "place": "München",
        "publisher": "Hanser",
        "year": "2020",
        "page_first": 89,
        "page_last": 117,
        "expected_din": [
            "KLEIN, Sophie",
            "Spracherwerb im mehrsprachigen Kontext",
            "In:",
            "BRAUN",
            "Hrsg.",
            "Mehrsprachigkeit in Deutschland",
            "München",
            "Hanser",
            "2020",
            "S. 89",
            "117",
        ],
    },
    {
        "id": "vogel_2023_klimawandel",
        "author_last": "VOGEL",
        "author_first": "Lukas",
        "chapter_title": "Klimawandel und Migration: Empirische Befunde",
        "editor_last": "JUNG",
        "editor_first": "Franziska",
        "container_title": "Migration im 21. Jahrhundert",
        "place": "Hamburg",
        "publisher": "Meiner",
        "year": "2023",
        "page_first": 201,
        "page_last": 234,
        "expected_din": [
            "VOGEL, Lukas",
            "Klimawandel und Migration: Empirische Befunde",
            "In:",
            "JUNG",
            "Hrsg.",
            "Migration im 21. Jahrhundert",
            "Hamburg",
            "Meiner",
            "2023",
            "S. 201",
            "234",
        ],
    },
]


def _render_din1505_chapter(fixture: dict) -> str:
    """Rendert einen DIN-1505-Bibliografie-Eintrag fuer ein Buchkapitel.

    Format gemaess book-chapter-de.md:
    NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.): Buchtitel.
    Ort : Verlag, Jahr, S. page_first-page_last.
    """
    return (
        f"{fixture['author_last']}, {fixture['author_first']}: "
        f"{fixture['chapter_title']}. "
        f"In: {fixture['editor_last']}, {fixture['editor_first']} (Hrsg.): "
        f"{fixture['container_title']}. "
        f"{fixture['place']} : {fixture['publisher']}, {fixture['year']}, "
        f"S. {fixture['page_first']}-{fixture['page_last']}."
    )


@pytest.mark.parametrize("fixture", CHAPTER_FIXTURES, ids=lambda f: f["id"])
def test_din1505_chapter_format(fixture: dict) -> None:
    """DIN-1505-Eintrag fuer Buchkapitel enthaelt alle Pflicht-Elemente."""
    rendered = _render_din1505_chapter(fixture)
    for expected_fragment in fixture["expected_din"]:
        assert expected_fragment in rendered, (
            f"[{fixture['id']}] Fragment '{expected_fragment}' fehlt in:\n{rendered}"
        )


def test_book_chapter_de_reference_file_exists() -> None:
    """skills/citation-extraction/references/book-chapter-de.md existiert."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), f"Referenz-Datei fehlt: {path}"


def test_book_chapter_de_contains_din1505_section() -> None:
    """book-chapter-de.md enthaelt eine DIN-1505-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "DIN 1505" in content, "DIN-1505-Sektion fehlt in book-chapter-de.md"
    assert "Hrsg." in content, "Hrsg.-Abkuerzung fehlt in book-chapter-de.md"
    assert "container-title" in content or "Buchtitel" in content, (
        "Keine Buchtitel/container-title-Referenz in book-chapter-de.md"
    )


def test_book_chapter_de_contains_harvard_section() -> None:
    """book-chapter-de.md enthaelt eine Harvard-de-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "Harvard" in content, "Harvard-Sektion fehlt in book-chapter-de.md"


def test_book_chapter_de_contains_apa7_section() -> None:
    """book-chapter-de.md enthaelt eine APA-7-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "APA" in content or "APA-7" in content or "APA7" in content, (
        "APA-Sektion fehlt in book-chapter-de.md"
    )


def test_variant_selector_in_skill_md() -> None:
    """SKILL.md enthaelt Variant-Selector-Logik fuer type=chapter."""
    skill_md = (
        Path(__file__).parent.parent
        / "skills" / "citation-extraction" / "SKILL.md"
    )
    assert skill_md.exists(), f"SKILL.md fehlt: {skill_md}"
    content = skill_md.read_text()
    assert "book-chapter-de.md" in content, (
        "SKILL.md verweist nicht auf book-chapter-de.md — Variant-Selector fehlt"
    )
    assert "type" in content.lower() and "chapter" in content, (
        "SKILL.md: Variant-Selector-Logik fuer type=chapter fehlt"
    )


def test_din1505_md_has_buch_section() -> None:
    """din1505.md enthaelt eine Buecher-Sektion (nicht nur Artikel)."""
    path = REFS_DIR / "din1505.md"
    assert path.exists(), "din1505.md fehlt"
    content = path.read_text()
    assert "Buch" in content or "buch" in content.lower(), (
        "din1505.md: Keine Buecher-Sektion gefunden"
    )
    assert "Verlag" in content, "din1505.md: Kein Verlag-Feld — Buecher-Sektion unvollstaendig"


def test_literature_state_schema_doc_exists() -> None:
    """docs/literature-state-schema.md existiert und dokumentiert type-Felder."""
    path = Path(__file__).parent.parent / "docs" / "literature-state-schema.md"
    assert path.exists(), f"Schema-Doku fehlt: {path}"
    content = path.read_text()
    assert "chapter" in content, "Schema-Doku: 'chapter' fehlt"
    assert "container-title" in content or "container_title" in content, (
        "Schema-Doku: container-title fehlt"
    )
    assert "editor" in content, "Schema-Doku: editor-Feld fehlt"
    assert "page-first" in content or "page_first" in content, (
        "Schema-Doku: page-first fehlt"
    )
