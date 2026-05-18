"""Tests fuer Reviewer-Response Skill (Ticket #108 — F28).

TDD-First: Tests schreiben BEVOR die Implementierung existiert.

Abdeckung:
- SKILL.md existiert mit gueltigem Frontmatter
- Preamble-Reference vorhanden
- response-letter-structure.md existiert mit point-by-point Format
- opt-in via output_targets guard beschrieben
- vault.add_quote fuer Vault-Anchored-Beweise beschrieben
- 5-Kommentar-Beispiel-Struktur in Referenz beschrieben
- Skill-Eintrag in skill_sizes.json vorhanden
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_SKILL_DIR = _ROOT / "skills" / "reviewer-response"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_STRUCTURE_REF = _SKILL_DIR / "references" / "response-letter-structure.md"
_BASELINES = _ROOT / "tests" / "baselines" / "skill_sizes.json"
_PREAMBLE_PATTERN = "> **Gemeinsames Preamble laden:**"


# ---------------------------------------------------------------------------
# SKILL.md Struktur
# ---------------------------------------------------------------------------

class TestReviewerResponseSkillMd:
    def test_skill_md_exists(self):
        assert _SKILL_MD.exists(), f"{_SKILL_MD} fehlt"

    def test_frontmatter_has_name(self):
        text = _SKILL_MD.read_text()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m, "Kein YAML-Frontmatter"
        assert re.search(r"^name:\s*\S+", m.group(1), re.M)

    def test_frontmatter_has_description(self):
        text = _SKILL_MD.read_text()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m
        assert re.search(r"^description:\s*\S+", m.group(1), re.M)

    def test_description_has_umlaut_pair(self):
        text = _SKILL_MD.read_text()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m
        desc = ""
        current_key = None
        for line in m.group(1).splitlines():
            if re.match(r"^[a-zA-Z_-]+:\s*", line):
                key, _, val = line.partition(":")
                current_key = key.strip()
                if current_key == "description":
                    desc = val.strip()
            elif current_key == "description" and line.startswith("  "):
                desc += " " + line.strip()
        pairs = re.findall(r'"[^"]*[äöüß][^"]*\s*/\s*[a-zA-Z][^"]*"', desc)
        assert len(pairs) >= 1, f"0 Umlaut-Paare in description: {desc[:200]}"

    def test_preamble_load_instruction_present(self):
        assert _PREAMBLE_PATTERN in _SKILL_MD.read_text()

    def test_no_inline_vorbedingungen(self):
        assert "\n## Vorbedingungen\n" not in _SKILL_MD.read_text()

    def test_no_inline_fabrikation(self):
        assert "\n## Keine Fabrikation\n" not in _SKILL_MD.read_text()

    def test_opt_in_guard_mentioned(self):
        assert "output_targets" in _SKILL_MD.read_text(), (
            "SKILL.md erwaehnt 'output_targets' opt-in Guard nicht"
        )

    def test_point_by_point_described(self):
        text = _SKILL_MD.read_text().lower()
        assert "point-by-point" in text or "punkt für punkt" in text or "punkt-fuer-punkt" in text, (
            "SKILL.md beschreibt point-by-point Format nicht"
        )

    def test_vault_add_quote_workflow_described(self):
        assert "vault.add_quote" in _SKILL_MD.read_text(), (
            "SKILL.md erwaehnt vault.add_quote fuer Vault-Anchored-Beweise nicht"
        )

    def test_reviewer_comments_input_described(self):
        text = _SKILL_MD.read_text().lower()
        assert "reviewer" in text and "kommentar" in text or "comment" in text, (
            "SKILL.md beschreibt Reviewer-Kommentar-Input nicht"
        )


# ---------------------------------------------------------------------------
# Response-Letter-Structure Referenz
# ---------------------------------------------------------------------------

class TestResponseLetterStructure:
    def test_structure_file_exists(self):
        assert _STRUCTURE_REF.exists(), f"{_STRUCTURE_REF} fehlt"

    def test_structure_has_point_by_point_format(self):
        text = _STRUCTURE_REF.read_text().lower()
        assert "point-by-point" in text or "punkt" in text, (
            "response-letter-structure.md beschreibt point-by-point Format nicht"
        )

    def test_structure_has_example_with_comments(self):
        """Referenz enthaelt ein Beispiel mit numerierten Reviewer-Kommentaren."""
        text = _STRUCTURE_REF.read_text()
        # Mindestens 5 Nummern/Ziffern fuer 5-Kommentar-Beispiel
        numbered = re.findall(r"\b[1-5]\b", text)
        assert len(numbered) >= 5, (
            "response-letter-structure.md enthaelt keine nummerierten Kommentar-Beispiele (1-5)"
        )

    def test_structure_has_vault_quote_reference(self):
        """Referenz erwaehnt Vault-Quote-Verweis als Beweis-Mechanismus."""
        text = _STRUCTURE_REF.read_text().lower()
        assert "vault" in text or "quote" in text or "zitat" in text, (
            "response-letter-structure.md erwaehnt keinen Vault-Quote-Verweis"
        )

    def test_structure_has_sections(self):
        """Referenz hat mindestens 3 Markdown-Sektionen."""
        text = _STRUCTURE_REF.read_text()
        sections = re.findall(r"^#{1,3}\s+\S+", text, re.M)
        assert len(sections) >= 3, (
            f"response-letter-structure.md hat nur {len(sections)} Sektionen — erwartet >= 3"
        )


# ---------------------------------------------------------------------------
# skill_sizes.json Eintrag
# ---------------------------------------------------------------------------

class TestReviewerResponseBaseline:
    def test_skill_sizes_contains_reviewer_response(self):
        sizes = json.loads(_BASELINES.read_text())
        assert "reviewer-response" in sizes, (
            "skill_sizes.json enthaelt keinen 'reviewer-response'-Eintrag"
        )
        assert sizes["reviewer-response"] > 0
