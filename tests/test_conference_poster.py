"""Tests fuer Conference-Poster Skill (Ticket #108 — F28).

TDD-First: Tests schreiben BEVOR die Implementierung existiert.

Abdeckung:
- SKILL.md existiert mit gueltigem Frontmatter
- Preamble-Reference vorhanden
- tikzposter-Template-Referenz existiert und enthaelt 4 \block{}-Sektionen
- opt-in via output_targets guard beschrieben
- A0-Format und 4-Sektionen-Struktur beschrieben
- vault.list_figures fuer Top-Figures Workflow beschrieben
- Skill-Eintrag in skill_sizes.json vorhanden
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_SKILL_DIR = _ROOT / "skills" / "conference-poster"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_TIKZ_REF = _SKILL_DIR / "references" / "tikzposter-template.md"
_BASELINES = _ROOT / "tests" / "baselines" / "skill_sizes.json"
_PREAMBLE_PATTERN = "> **Gemeinsames Preamble laden:**"


# ---------------------------------------------------------------------------
# SKILL.md Struktur
# ---------------------------------------------------------------------------

class TestConferencePosterSkillMd:
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

    def test_a0_format_described(self):
        text = _SKILL_MD.read_text().upper()
        assert "A0" in text, "SKILL.md beschreibt A0-Format nicht"

    def test_four_sections_described(self):
        """SKILL.md beschreibt 4-Sektionen-Struktur: Intro/Methode/Ergebnis/Diskussion."""
        text = _SKILL_MD.read_text().lower()
        required = ["intro", "methode", "ergebni", "diskuss"]
        for kw in required:
            assert kw in text, f"SKILL.md: Sektion '{kw}' nicht erwaehnt"

    def test_vault_list_figures_workflow_described(self):
        assert "vault.list_figures" in _SKILL_MD.read_text(), (
            "SKILL.md erwaehnt vault.list_figures fuer Top-Figures nicht"
        )

    def test_tikzposter_and_powerpoint_mentioned(self):
        text = _SKILL_MD.read_text().lower()
        assert "tikzposter" in text, "SKILL.md erwaehnt tikzposter nicht"
        assert "powerpoint" in text or "pptx" in text, (
            "SKILL.md erwaehnt PowerPoint-Export nicht"
        )


# ---------------------------------------------------------------------------
# tikzposter-Template Referenz
# ---------------------------------------------------------------------------

class TestTikzposterTemplate:
    def test_template_file_exists(self):
        assert _TIKZ_REF.exists(), f"{_TIKZ_REF} fehlt"

    def test_template_has_four_block_sections(self):
        """tikzposter-template.md enthaelt 4 \\block{}-Abschnitte."""
        text = _TIKZ_REF.read_text()
        blocks = re.findall(r"\\block\{", text)
        assert len(blocks) >= 4, (
            f"tikzposter-template.md enthaelt nur {len(blocks)} \\block{{}} — erwartet >= 4"
        )

    def test_template_has_includegraphics(self):
        """tikzposter-template.md enthaelt \\includegraphics fuer Figure-Einbindung."""
        assert "\\includegraphics" in _TIKZ_REF.read_text(), (
            "tikzposter-template.md enthaelt kein \\includegraphics"
        )

    def test_template_has_a0paper_setting(self):
        """tikzposter-template.md setzt A0-Papierformat."""
        text = _TIKZ_REF.read_text()
        assert "a0paper" in text.lower() or "a0" in text.lower(), (
            "tikzposter-template.md setzt kein A0-Papierformat"
        )

    def test_template_has_documentclass(self):
        assert "\\documentclass" in _TIKZ_REF.read_text(), (
            "tikzposter-template.md enthaelt kein \\documentclass"
        )


# ---------------------------------------------------------------------------
# skill_sizes.json Eintrag
# ---------------------------------------------------------------------------

class TestConferencePosterBaseline:
    def test_skill_sizes_contains_conference_poster(self):
        sizes = json.loads(_BASELINES.read_text())
        assert "conference-poster" in sizes, (
            "skill_sizes.json enthaelt keinen 'conference-poster'-Eintrag"
        )
        assert sizes["conference-poster"] > 0
