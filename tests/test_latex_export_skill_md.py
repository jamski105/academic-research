"""Regressions-Tests fuer skills/latex-export/SKILL.md (#170).

Prueft:
- Skript-Pfade enthalten ${CLAUDE_PLUGIN_ROOT} (nicht relativ)
- Abgrenzungsabschnitt zu citation-extraction vorhanden
- Fehlerpfad-/Troubleshooting-Sektion vorhanden
  (Pandoc-not-found, Vault-leer, Template-not-found)
"""

from pathlib import Path

import pytest

SKILL_MD = Path(__file__).parent.parent / "skills" / "latex-export" / "SKILL.md"


@pytest.fixture(scope="module")
def skill_text():
    return SKILL_MD.read_text(encoding="utf-8")


class TestSkriptPfade:
    """Skript-Pfade muessen absolut via ${CLAUDE_PLUGIN_ROOT} sein."""

    def test_render_tex_uses_plugin_root(self, skill_text):
        """render_tex.py-Pfad muss ${CLAUDE_PLUGIN_ROOT} enthalten."""
        assert "${CLAUDE_PLUGIN_ROOT}" in skill_text, (
            "SKILL.md: Skript-Pfade sollen ${CLAUDE_PLUGIN_ROOT}/... verwenden, "
            "nicht relative Pfade wie 'skills/latex-export/scripts/render_tex.py'."
        )

    def test_no_bare_relative_scripts_path(self, skill_text):
        """Kein bare 'skills/latex-export/scripts/' ohne ${CLAUDE_PLUGIN_ROOT}."""
        # Wenn 'skills/latex-export/scripts/' vorkommt ohne vorangehendes ${CLAUDE_PLUGIN_ROOT}
        import re
        bare_relative = re.search(
            r"(?<!\$\{CLAUDE_PLUGIN_ROOT\}/)skills/latex-export/scripts/",
            skill_text,
        )
        assert bare_relative is None, (
            "SKILL.md: relativer Pfad 'skills/latex-export/scripts/' gefunden "
            "ohne '${CLAUDE_PLUGIN_ROOT}/' Praefix."
        )


class TestAbgrenzungCitationExtraction:
    """citation-extraction-Abgrenzung muss explizit dokumentiert sein."""

    def test_citation_extraction_mentioned(self, skill_text):
        """SKILL.md muss 'citation-extraction' erwaehnen."""
        assert "citation-extraction" in skill_text, (
            "SKILL.md: Abgrenzung zu citation-extraction fehlt. "
            "Wann latex-export vs. citation-extraction verwenden? Undokumentiert."
        )

    def test_abgrenzung_section_or_hint_present(self, skill_text):
        """SKILL.md muss einen Abgrenzungshinweis zu citation-extraction enthalten."""
        lower = skill_text.lower()
        has_abgrenzung = (
            "abgrenzung" in lower
            or "nicht triggern" in lower
            or "vs." in lower
            or "statt" in lower
        ) and "citation-extraction" in skill_text
        assert has_abgrenzung, (
            "SKILL.md: Kein Abgrenzungshinweis zu citation-extraction gefunden. "
            "Ergaenze z.B. einen 'Nicht triggern fuer' oder 'Abgrenzung'-Abschnitt."
        )


class TestFehlerpfade:
    """Fehlerpfade / Troubleshooting-Sektion muss vorhanden sein."""

    def test_pandoc_not_found_documented(self, skill_text):
        """Pandoc-not-found-Fallback muss erwaehnt sein."""
        lower = skill_text.lower()
        has_pandoc_error = (
            "pandoc not found" in lower
            or "pandoc fehlt" in lower
            or "pandoc nicht" in lower
            or "pandoc-not-found" in lower
            or ("pandoc" in lower and ("fallback" in lower or "fehler" in lower or "error" in lower))
        )
        assert has_pandoc_error, (
            "SKILL.md: Kein Pandoc-not-found-Fehlerpfad dokumentiert. "
            "Ergaenze Fehlerpfad-Sektion mit Pandoc-Detection und Custom-Renderer-Fallback."
        )

    def test_vault_empty_documented(self, skill_text):
        """Vault-leer-Fall muss erwaehnt sein."""
        lower = skill_text.lower()
        has_vault_empty = (
            "vault leer" in lower
            or "vault ist leer" in lower
            or "vault-leer" in lower
            or "leerer vault" in lower
            or "keine papers" in lower
            or "no papers" in lower
            or ("vault" in lower and ("leer" in lower or "empty" in lower))
        )
        assert has_vault_empty, (
            "SKILL.md: Kein Vault-leer-Fehlerpfad dokumentiert. "
            "Ergaenze Fallback wenn Vault keine Papers enthaelt."
        )

    def test_template_not_found_documented(self, skill_text):
        """Template-not-found-Fall muss erwaehnt sein."""
        lower = skill_text.lower()
        has_template_error = (
            "template not found" in lower
            or "template fehlt" in lower
            or "template nicht" in lower
            or "vorlage nicht" in lower
            or ("template" in lower and ("fehlt" in lower or "nicht" in lower or "missing" in lower or "error" in lower))
        )
        assert has_template_error, (
            "SKILL.md: Kein Template-not-found-Fehlerpfad dokumentiert. "
            "Ergaenze Fallback wenn uni-Template nicht gefunden wird."
        )

    def test_error_section_exists(self, skill_text):
        """Eine Fehlerpfad- oder Troubleshooting-Sektion muss vorhanden sein."""
        lower = skill_text.lower()
        has_section = (
            "## fehlerpfade" in lower
            or "## fehlerbehandlung" in lower
            or "## troubleshooting" in lower
            or "## error" in lower
            or "## fallbacks" in lower
        )
        assert has_section, (
            "SKILL.md: Keine Fehlerpfad-/Troubleshooting-Sektion (## Fehlerpfade o.ae.) gefunden."
        )
