"""
Tests fuer den CSL-Import-Skill (F13).

TDD: Diese Tests wurden VOR der Implementierung geschrieben.
Alle Tests sind initial rot (ImportError).
"""
import sys
import pathlib
import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "csl_import"
APA_CSL = FIXTURES / "apa-7th-edition.csl"
SPRINGER_CSL = FIXTURES / "springer-basic-author-date.csl"

# Pfad zum Scripts-Verzeichnis hinzufuegen (analog zotero-import-Tests)
_SCRIPTS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "skills" / "citation-style-import" / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# Import will fail until implementation exists (RED)
from csl_import import CSLParser, csl_to_markdown


class TestCSLParserMetadata:
    """Parser liest Metadaten aus dem CSL-File."""

    def test_loads_style_title_apa(self):
        parser = CSLParser(APA_CSL)
        assert "American Psychological Association" in parser.style_title

    def test_loads_style_title_springer(self):
        parser = CSLParser(SPRINGER_CSL)
        assert "Springer" in parser.style_title

    def test_citation_format_author_date(self):
        parser = CSLParser(SPRINGER_CSL)
        assert parser.citation_format == "author-date"

    def test_citation_format_apa_author_date(self):
        parser = CSLParser(APA_CSL)
        assert parser.citation_format == "author-date"


class TestCSLParserMacros:
    """Parser extrahiert relevante Macros."""

    def test_author_macro_extracted(self):
        parser = CSLParser(APA_CSL)
        macros = parser.macros
        assert "author" in macros

    def test_issued_macro_extracted(self):
        parser = CSLParser(APA_CSL)
        macros = parser.macros
        assert "issued" in macros


class TestCSLParserSourceTypes:
    """Parser erkennt alle 5 Quelltypen."""

    def test_detects_article_journal(self):
        parser = CSLParser(APA_CSL)
        types = parser.source_types
        assert "article-journal" in types

    def test_detects_book(self):
        parser = CSLParser(APA_CSL)
        types = parser.source_types
        assert "book" in types

    def test_detects_chapter(self):
        parser = CSLParser(APA_CSL)
        types = parser.source_types
        assert "chapter" in types

    def test_detects_paper_conference(self):
        parser = CSLParser(APA_CSL)
        types = parser.source_types
        assert "paper-conference" in types

    def test_detects_fallback_type(self):
        """Der 'else'-Zweig zaehlt als Webseite/Sonstige."""
        parser = CSLParser(APA_CSL)
        types = parser.source_types
        assert "other" in types

    def test_springer_detects_book(self):
        parser = CSLParser(SPRINGER_CSL)
        types = parser.source_types
        assert "book" in types


class TestCSLParserVariables:
    """Parser erkennt verwendete CSL-Variablen."""

    def test_doi_variable_detected(self):
        parser = CSLParser(APA_CSL)
        assert "DOI" in parser.variables

    def test_title_variable_detected(self):
        parser = CSLParser(APA_CSL)
        assert "title" in parser.variables

    def test_author_variable_detected(self):
        parser = CSLParser(APA_CSL)
        assert "author" in parser.variables

    def test_container_title_variable_detected(self):
        parser = CSLParser(APA_CSL)
        assert "container-title" in parser.variables

    def test_issued_variable_detected(self):
        parser = CSLParser(APA_CSL)
        assert "issued" in parser.variables


class TestCSLToMarkdown:
    """csl_to_markdown generiert valides Prompt-Regel-Markdown."""

    def test_returns_string(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert isinstance(md, str)
        assert len(md) > 100

    def test_contains_style_title(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "American Psychological Association" in md

    def test_contains_inline_citation_section(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "Inline" in md or "inline" in md or "Zitat" in md

    def test_contains_bibliography_section(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "Literaturverzeichnis" in md or "bibliography" in md.lower()

    def test_contains_article_journal_rule(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "article-journal" in md or "Zeitschriftenartikel" in md

    def test_contains_book_rule(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "book" in md or "Buch" in md

    def test_contains_chapter_rule(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "chapter" in md or "Buchkapitel" in md

    def test_contains_conference_rule(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "paper-conference" in md or "Konferenz" in md

    def test_contains_doi_hint(self):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        assert "DOI" in md

    def test_springer_variant_title(self):
        parser = CSLParser(SPRINGER_CSL)
        md = csl_to_markdown(parser)
        assert "Springer" in md


class TestCSLToMarkdownSpringer:
    """csl_to_markdown fuer Springer Author-Date korrekt."""

    def test_springer_returns_string(self):
        parser = CSLParser(SPRINGER_CSL)
        md = csl_to_markdown(parser)
        assert isinstance(md, str) and len(md) > 100

    def test_springer_has_all_5_source_types(self):
        """Eval: 5 Quellentypen abgedeckt."""
        parser = CSLParser(SPRINGER_CSL)
        md = csl_to_markdown(parser)
        covered = sum(1 for t in ["article-journal", "book", "chapter", "paper-conference", "other"]
                      if t in md or any(k in md for k in {
                          "article-journal": ["Zeitschriftenartikel"],
                          "book": ["Buch"],
                          "chapter": ["Buchkapitel"],
                          "paper-conference": ["Konferenz"],
                          "other": ["Webseite", "Sonstige"],
                      }[t]))
        assert covered == 5, f"Nur {covered}/5 Quellentypen im Markdown gefunden"


class TestSkillSizes:
    """citation-style-import muss in skill_sizes.json eingetragen sein."""

    def test_citation_style_import_in_skill_sizes(self):
        import json
        baseline = pathlib.Path(__file__).parent / "baselines" / "skill_sizes.json"
        data = json.loads(baseline.read_text())
        assert "citation-style-import" in data, \
            "citation-style-import fehlt in tests/baselines/skill_sizes.json"

    def test_citation_style_import_size_positive(self):
        import json
        baseline = pathlib.Path(__file__).parent / "baselines" / "skill_sizes.json"
        data = json.loads(baseline.read_text())
        assert data.get("citation-style-import", 0) > 0


class TestOutputFileGeneration:
    """csl_to_markdown kann in eine Datei geschrieben werden."""

    def test_output_file_written(self, tmp_path):
        parser = CSLParser(APA_CSL)
        md = csl_to_markdown(parser)
        out = tmp_path / "custom-apa.md"
        out.write_text(md, encoding="utf-8")
        assert out.exists()
        assert out.stat().st_size > 100

    def test_springer_output_file_written(self, tmp_path):
        """Acceptance: User waehlt 'Springer Basic - Author Date' → custom-Variant generiert."""
        parser = CSLParser(SPRINGER_CSL)
        md = csl_to_markdown(parser)
        out = tmp_path / "custom-springer-basic-author-date.md"
        out.write_text(md, encoding="utf-8")
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "Springer" in content
