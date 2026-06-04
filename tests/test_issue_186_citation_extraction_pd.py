"""Regressionstest fuer Issue #186 — Progressive-Disclosure citation-extraction.

Akzeptanzkriterien (siehe Issue #186):
- Few-Shot-Beispiele → references/citation-examples.md (ausgelagert).
- Export-Formate-Beschreibung → references/output-formats.md (ausgelagert).
- SKILL.md nach Fix < 8 KB.
- node scripts/export-literature-state.mjs (Zeile ~174) existiert tatsaechlich.
- Frontmatter (name + description + Trigger) bleibt intakt.
- SKILL.md verlinkt die ausgelagerten Referenz-Dateien.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "citation-extraction"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFS_DIR = SKILL_DIR / "references"

SKILL_MD_MAX_BYTES = 8 * 1024  # < 8 KB Soll


def test_skill_md_under_8kb() -> None:
    """SKILL.md ist nach Auslagerung < 8 KB."""
    size = SKILL_MD.stat().st_size
    assert size < SKILL_MD_MAX_BYTES, (
        f"SKILL.md ist {size} Bytes — Soll < {SKILL_MD_MAX_BYTES} Bytes (8 KB)"
    )


def test_citation_examples_reference_exists() -> None:
    """Few-Shot-Beispiele sind nach references/citation-examples.md ausgelagert."""
    path = REFS_DIR / "citation-examples.md"
    assert path.exists(), f"Ausgelagerte Referenz fehlt: {path}"
    content = path.read_text()
    # Die Few-Shot-Beispiele muessen tatsaechlich umgezogen sein, nicht nur eine
    # leere Stub-Datei.
    assert "Few-Shot" in content or "APA7" in content, (
        "citation-examples.md enthaelt die Few-Shot-Beispiele nicht"
    )
    assert "Müller" in content, (
        "citation-examples.md enthaelt das APA7-Beispiel (Müller) nicht"
    )


def test_output_formats_reference_exists() -> None:
    """Export-Formate-Beschreibung ist nach references/output-formats.md ausgelagert."""
    path = REFS_DIR / "output-formats.md"
    assert path.exists(), f"Ausgelagerte Referenz fehlt: {path}"
    content = path.read_text()
    for fmt in ("BibTeX", "Markdown", "JSON"):
        assert fmt in content, f"output-formats.md nennt das Format '{fmt}' nicht"


def test_skill_md_links_to_extracted_references() -> None:
    """SKILL.md verlinkt die ausgelagerten Referenz-Dateien (Progressive Disclosure)."""
    content = SKILL_MD.read_text()
    assert "references/citation-examples.md" in content, (
        "SKILL.md verlinkt references/citation-examples.md nicht"
    )
    assert "references/output-formats.md" in content, (
        "SKILL.md verlinkt references/output-formats.md nicht"
    )


def test_skill_md_few_shot_block_removed() -> None:
    """Der vollstaendige Few-Shot-Beispielblock ist aus SKILL.md ausgelagert."""
    content = SKILL_MD.read_text()
    # Das konkrete APA7-Beispiel darf nicht mehr inline im SKILL.md stehen.
    assert "Cloud-Migration in deutschen" not in content, (
        "SKILL.md enthaelt das ausgelagerte APA7-Few-Shot-Beispiel noch inline"
    )


def test_frontmatter_and_triggers_intact() -> None:
    """Frontmatter (name, description, Trigger) bleibt unveraendert intakt."""
    content = SKILL_MD.read_text()
    assert content.startswith("---\n"), "SKILL.md beginnt nicht mit Frontmatter"
    assert "name: citation-extraction" in content, "name-Feld fehlt im Frontmatter"
    assert "description:" in content, "description-Feld fehlt im Frontmatter"
    # Kern-Trigger muessen erhalten bleiben.
    for trigger in ("Literaturverzeichnis", "citation extraction", "Bibliographie"):
        assert trigger in content, f"Trigger '{trigger}' fehlt im Frontmatter"


def test_export_literature_state_script_exists() -> None:
    """node scripts/export-literature-state.mjs existiert tatsaechlich."""
    script = REPO_ROOT / "scripts" / "export-literature-state.mjs"
    assert script.exists(), f"Referenziertes Skript fehlt: {script}"
    # SKILL.md verweist weiterhin korrekt auf das Skript.
    assert "scripts/export-literature-state.mjs" in SKILL_MD.read_text(), (
        "SKILL.md verweist nicht mehr auf scripts/export-literature-state.mjs"
    )
