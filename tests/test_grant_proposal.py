"""Tests fuer Grant-Proposal Skill (Ticket #108 — F28).

TDD-First: Tests schreiben BEVOR die Implementierung existiert.

Abdeckung:
- SKILL.md existiert mit gueltigem Frontmatter
- Preamble-Reference vorhanden
- DFG/BMBF/EU-Horizon-Referenz-Dateien existieren und enthalten Pflichtfelder
- opt-in via output_targets guard beschrieben
- 10-Seiten-DFG-Skelett mit Bibliographie-Block in Referenz definiert
- Skill-Eintrag in skill_sizes.json vorhanden
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_SKILL_DIR = _ROOT / "skills" / "grant-proposal"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_DFG_REF = _SKILL_DIR / "references" / "dfg.md"
_BMBF_REF = _SKILL_DIR / "references" / "bmbf.md"
_EU_REF = _SKILL_DIR / "references" / "eu-horizon.md"
_BASELINES = _ROOT / "tests" / "baselines" / "skill_sizes.json"
_PREAMBLE_PATTERN = "> **Gemeinsames Preamble laden:**"


# ---------------------------------------------------------------------------
# SKILL.md Struktur
# ---------------------------------------------------------------------------

class TestGrantProposalSkillMd:
    def test_skill_md_exists(self):
        assert _SKILL_MD.exists(), f"{_SKILL_MD} fehlt"

    def test_frontmatter_has_name(self):
        text = _SKILL_MD.read_text()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m, "Kein YAML-Frontmatter gefunden"
        assert re.search(r"^name:\s*\S+", m.group(1), re.M), "name fehlt im Frontmatter"

    def test_frontmatter_has_description(self):
        text = _SKILL_MD.read_text()
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        assert m
        assert re.search(r"^description:\s*\S+", m.group(1), re.M), "description fehlt"

    def test_description_has_umlaut_pair(self):
        """description enthaelt mindestens ein Umlaut-Paar (X... / X... Muster)."""
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
        assert _PREAMBLE_PATTERN in _SKILL_MD.read_text(), (
            f"Preamble-Ladereferenz fehlt in {_SKILL_MD}"
        )

    def test_no_inline_vorbedingungen(self):
        assert "\n## Vorbedingungen\n" not in _SKILL_MD.read_text()

    def test_no_inline_fabrikation(self):
        assert "\n## Keine Fabrikation\n" not in _SKILL_MD.read_text()

    def test_opt_in_guard_mentioned(self):
        """SKILL.md beschreibt den output_targets opt-in Guard."""
        text = _SKILL_MD.read_text()
        assert "output_targets" in text, (
            "SKILL.md erwaehnt 'output_targets' opt-in Guard nicht"
        )

    def test_foerderlinien_choice_described(self):
        """SKILL.md beschreibt DFG/BMBF/EU Foerderlinien-Auswahl."""
        text = _SKILL_MD.read_text().lower()
        assert "dfg" in text and "bmbf" in text and "horizon" in text, (
            "SKILL.md erwaehnt nicht alle drei Foerderlinien (DFG, BMBF, EU-Horizon)"
        )

    def test_vault_search_workflow_described(self):
        """SKILL.md beschreibt vault.search fuer Quellen-Retrieval."""
        assert "vault.search" in _SKILL_MD.read_text(), (
            "SKILL.md erwaehnt vault.search nicht"
        )

    def test_bibliographie_mentioned(self):
        """SKILL.md erwaehnt Bibliographie als Pflichtbestandteil."""
        text = _SKILL_MD.read_text().lower()
        assert "bibliographie" in text or "bibliography" in text, (
            "SKILL.md erwaehnt keine Bibliographie"
        )


# ---------------------------------------------------------------------------
# Referenz-Dateien
# ---------------------------------------------------------------------------

class TestDfgReference:
    def test_dfg_ref_exists(self):
        assert _DFG_REF.exists(), f"{_DFG_REF} fehlt"

    def test_dfg_ref_has_10_seiten_limit(self):
        text = _DFG_REF.read_text().lower()
        assert "10 seiten" in text or "10-seiten" in text or "zehn seiten" in text, (
            "dfg.md erwaehnt das 10-Seiten-Limit nicht"
        )

    def test_dfg_ref_has_bibliographie_section(self):
        text = _DFG_REF.read_text()
        assert "Bibliographie" in text or "Literatur" in text, (
            "dfg.md enthaelt keine Bibliographie-Section"
        )

    def test_dfg_ref_has_skeleton_sections(self):
        """dfg.md beschreibt die Antragsstruktur mit mind. 4 Pflicht-Sektionen."""
        text = _DFG_REF.read_text()
        required = ["Zusammenfassung", "Ziele", "Methoden", "Bibliographie"]
        for section in required:
            assert section in text, f"dfg.md: Pflicht-Sektion '{section}' fehlt"


class TestBmbfReference:
    def test_bmbf_ref_exists(self):
        assert _BMBF_REF.exists(), f"{_BMBF_REF} fehlt"

    def test_bmbf_ref_has_foerderlinien(self):
        text = _BMBF_REF.read_text()
        assert "Foerderlinie" in text or "Förderlinien" in text or "Förderlinie" in text, (
            "bmbf.md erwaehnt keine Foerderlinien"
        )

    def test_bmbf_ref_has_structure(self):
        text = _BMBF_REF.read_text()
        assert "#" in text, "bmbf.md hat keine Markdown-Struktur"


class TestEuHorizonReference:
    def test_eu_ref_exists(self):
        assert _EU_REF.exists(), f"{_EU_REF} fehlt"

    def test_eu_ref_mentions_horizon_europe(self):
        text = _EU_REF.read_text().lower()
        assert "horizon" in text, "eu-horizon.md erwaehnt Horizon Europe nicht"

    def test_eu_ref_has_structure(self):
        text = _EU_REF.read_text()
        assert "#" in text, "eu-horizon.md hat keine Markdown-Struktur"


# ---------------------------------------------------------------------------
# skill_sizes.json Eintrag
# ---------------------------------------------------------------------------

class TestGrantProposalBaseline:
    def test_skill_sizes_contains_grant_proposal(self):
        sizes = json.loads(_BASELINES.read_text())
        assert "grant-proposal" in sizes, (
            "skill_sizes.json enthaelt keinen 'grant-proposal'-Eintrag"
        )
        assert sizes["grant-proposal"] > 0
