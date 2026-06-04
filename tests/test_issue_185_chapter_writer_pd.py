"""Regression-Test fuer Issue #185.

skills/chapter-writer/SKILL.md ueberschritt den 8-KB-Progressive-Disclosure-
Soll-Wert (~13 KB). Detailinhalt (Few-Shot-Beispiele, spezielle Kapiteltypen,
Quality-Review-JSON) wird nach references/ ausgelagert und aus SKILL.md
verlinkt.

Akzeptanzkriterien (aus dem Issue):
- Few-Shot-Beispiele     -> references/chapter-examples.md
- Spezielle Kapiteltypen -> references/chapter-types.md
- Quality-Review-JSON    -> references/quality-review-config.md
- SKILL.md < 8 KB
- Frontmatter (name/description) + Trigger intakt
"""
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).parent.parent / "skills" / "chapter-writer"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"

EXPECTED_REFERENCES = [
    "chapter-examples.md",
    "chapter-types.md",
    "quality-review-config.md",
]

MAX_BYTES = 8 * 1024  # 8 KB Progressive-Disclosure-Soll-Wert


def _frontmatter() -> dict:
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "SKILL.md ohne Frontmatter"
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end])


def test_references_dir_exists() -> None:
    assert REFERENCES_DIR.is_dir(), (
        f"references/-Verzeichnis fehlt: {REFERENCES_DIR}"
    )


def test_expected_reference_files_exist_and_nonempty() -> None:
    for name in EXPECTED_REFERENCES:
        ref = REFERENCES_DIR / name
        assert ref.exists(), f"Ausgelagerte Referenz fehlt: {ref}"
        assert len(ref.read_text(encoding="utf-8").strip()) > 0, (
            f"Ausgelagerte Referenz ist leer: {ref}"
        )


def test_skill_md_links_to_references() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    for name in EXPECTED_REFERENCES:
        assert f"references/{name}" in text, (
            f"SKILL.md verlinkt nicht auf references/{name}"
        )


def test_skill_md_under_8kb() -> None:
    size = SKILL_MD.stat().st_size
    assert size < MAX_BYTES, (
        f"SKILL.md ist {size} Bytes (>= {MAX_BYTES} = 8 KB); "
        "Detailinhalt muss nach references/ ausgelagert werden"
    )


def test_frontmatter_intact() -> None:
    fm = _frontmatter()
    assert fm.get("name") == "chapter-writer", "name-Frontmatter beschaedigt"
    desc = fm.get("description", "")
    assert desc, "description-Frontmatter fehlt"
    # Trigger muessen erhalten bleiben.
    for trigger in ["Einleitung schreiben", "Diskussion schreiben"]:
        assert trigger in desc, f"Trigger '{trigger}' aus description verloren"


def test_detail_content_moved_out_of_skill_md() -> None:
    """Der ausgelagerte Detailinhalt darf nicht mehr inline in SKILL.md stehen."""
    text = SKILL_MD.read_text(encoding="utf-8")
    # Few-Shot-Beispiel-Prosa darf nicht mehr inline sein.
    assert "transaktionalen Anreize hinaus motivieren" not in text, (
        "Few-Shot-Beispiel noch inline in SKILL.md"
    )
    # Quality-Review-Kriterien-JSON darf nicht mehr inline sein.
    assert "count_per_1000" not in text, (
        "Quality-Review-JSON noch inline in SKILL.md"
    )
