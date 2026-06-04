"""Regression-Test fuer Issue #176.

Trigger-Konflikt latex-export vs citation-extraction beim BibTeX-Output:
Die User-Phrase "Erstelle mir eine BibTeX-Datei" triggerte beide Skills.
Beide SKILL.md muessen einen Abgrenzungs-Block enthalten, der den
BibTeX-Scope klar zuordnet:

- citation-extraction = Einzelzitat-Extraktion aus PDF (one-shot)
- latex-export        = vollstaendiger Vault-Bibliography-Dump

Offline-hermetisch: prueft ausschliesslich Datei-Inhalte, kein Netzwerk.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
CITATION_SKILL = SKILLS_DIR / "citation-extraction" / "SKILL.md"
LATEX_SKILL = SKILLS_DIR / "latex-export" / "SKILL.md"


def _read(path: Path) -> str:
    assert path.exists(), f"SKILL.md fehlt: {path}"
    return path.read_text(encoding="utf-8")


def test_citation_extraction_grenzt_vault_bibtex_ab() -> None:
    """citation-extraction muss Vault-weiten .bib-Export an latex-export delegieren."""
    text = _read(CITATION_SKILL)
    assert "latex-export" in text, (
        "citation-extraction/SKILL.md verweist nicht auf latex-export fuer "
        "den vollstaendigen Vault->.bib-Export (Issue #176)"
    )
    # Der Verweis muss im BibTeX-/Export-Kontext stehen, nicht irgendwo.
    bibtex_section = re.search(
        r"BibTeX[^\n]*\n(?:.*\n){0,12}", text, re.IGNORECASE
    )
    assert bibtex_section is not None, "Kein BibTeX-Abschnitt in citation-extraction"
    assert "latex-export" in bibtex_section.group(0), (
        "Der Verweis auf latex-export steht nicht im BibTeX-Kontext "
        "(Issue #176: Abgrenzung des one-shot-Einzelzitats vom Vault-Dump)"
    )


def test_latex_export_grenzt_einzelzitat_ab() -> None:
    """latex-export muss Einzelzitat-Extraktion an citation-extraction delegieren."""
    text = _read(LATEX_SKILL)
    assert "citation-extraction" in text, (
        "latex-export/SKILL.md verweist nicht auf citation-extraction fuer "
        "die Einzelzitat-Extraktion aus PDFs (Issue #176)"
    )


def test_latex_export_behaelt_vault_bibtex_trigger() -> None:
    """Routing-Signal: 'BibTeX aus Vault' bleibt latex-export zugeordnet.

    Akzeptanzkriterium #3: User-Phrase 'BibTeX aus Vault' trifft latex-export.
    """
    text = _read(LATEX_SKILL)
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m is not None, "Kein Frontmatter in latex-export/SKILL.md"
    frontmatter = m.group(1)
    assert "BibTeX aus Vault" in frontmatter, (
        "latex-export-Description nennt 'BibTeX aus Vault' nicht mehr als Trigger "
        "(Issue #176, Akzeptanzkriterium #3)"
    )
    # citation-extraction darf diesen Vault-weiten Trigger gerade NICHT fuer sich
    # beanspruchen.
    cite = _read(CITATION_SKILL)
    cite_fm = re.match(r"^---\n(.*?)\n---", cite, re.DOTALL)
    assert cite_fm is not None
    assert "BibTeX aus Vault" not in cite_fm.group(1), (
        "citation-extraction-Description beansprucht den Vault-weiten "
        "'BibTeX aus Vault'-Trigger (Overtriggering, Issue #176)"
    )
