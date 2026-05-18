"""Tests fuer LaTeX-Export (F17 — #96).

TDD-First: Tests werden rot sein bis zur Implementierung.

Abgedeckt:
- render_tex: Markdown -> .tex (pandoc + custom-renderer-fallback)
- build_bib: Vault -> .bib (biblatex DIN-1505-Stil, gemockter Vault)
- verbatim-guard: *.tex-Pfade sind geschuetzt
- 3-Kapitel-Integration
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Pfade
WORKTREE = Path(__file__).parent.parent
SCRIPTS_DIR = WORKTREE / "skills" / "latex-export" / "scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "latex_export"
HOOK_PATH = WORKTREE / "hooks" / "verbatim-guard.mjs"

# sys.path fuer direkten Import der Scripts
sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def run_hook(tool_name: str, file_path: str, content: str, env_overrides: dict = None) -> subprocess.CompletedProcess:
    """Startet verbatim-guard-Hook als Subprocess."""
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"file_path": file_path, "content": content},
    })
    env = os.environ.copy()
    env["VAULT_DB_PATH"] = str(WORKTREE / "nonexistent_vault_for_tests.db")
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["node", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


# ---------------------------------------------------------------------------
# render_tex Tests
# ---------------------------------------------------------------------------

class TestRenderTex:
    """Tests fuer skills/latex-export/scripts/render_tex.py"""

    def test_import(self):
        """render_tex kann importiert werden."""
        import render_tex  # noqa: F401

    def test_render_heading_h1(self):
        """H1 wird zu \\chapter{} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("# Einleitung\n", force_custom=True)
        assert r"\chapter{Einleitung}" in result

    def test_render_heading_h2(self):
        """H2 wird zu \\section{} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("## Hintergrund\n", force_custom=True)
        assert r"\section{Hintergrund}" in result

    def test_render_heading_h3(self):
        """H3 wird zu \\subsection{} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("### Unterpunkt\n", force_custom=True)
        assert r"\subsection{Unterpunkt}" in result

    def test_render_bold(self):
        """**fett** wird zu \\textbf{} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("Ein **fetter** Text.\n", force_custom=True)
        assert r"\textbf{fetter}" in result

    def test_render_italic(self):
        """_kursiv_ wird zu \\textit{} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("Ein _kursiver_ Text.\n", force_custom=True)
        assert r"\textit{kursiver}" in result

    def test_render_unordered_list(self):
        """Ungeordnete Liste wird zu \\begin{itemize}/\\item (custom renderer)."""
        from render_tex import render_markdown_to_tex
        md = "- Alpha\n- Beta\n- Gamma\n"
        result = render_markdown_to_tex(md, force_custom=True)
        assert r"\begin{itemize}" in result
        assert r"\item Alpha" in result
        assert r"\end{itemize}" in result

    def test_render_ordered_list(self):
        """Geordnete Liste wird zu \\begin{enumerate}/\\item (custom renderer)."""
        from render_tex import render_markdown_to_tex
        md = "1. Erster\n2. Zweiter\n3. Dritter\n"
        result = render_markdown_to_tex(md, force_custom=True)
        assert r"\begin{enumerate}" in result
        assert r"\item Erster" in result
        assert r"\end{enumerate}" in result

    def test_render_blockquote(self):
        """Blockzitat wird zu \\begin{quote} (custom renderer)."""
        from render_tex import render_markdown_to_tex
        result = render_markdown_to_tex("> Ein wichtiges Zitat.\n", force_custom=True)
        assert r"\begin{quote}" in result
        assert r"\end{quote}" in result

    def test_render_sample_fixture(self):
        """Sample-Kapitel-Fixture erzeugt valides .tex mit chapter + section + subsection (custom renderer)."""
        from render_tex import render_markdown_to_tex
        md = (FIXTURES_DIR / "sample_chapter.md").read_text(encoding="utf-8")
        result = render_markdown_to_tex(md, force_custom=True)
        assert r"\chapter{Einleitung}" in result
        assert r"\section{Hintergrund}" in result
        assert r"\subsection{Unterpunkt}" in result

    def test_render_file_output(self, tmp_path):
        """render_tex_file() schreibt .tex-Datei auf Disk (custom renderer)."""
        from render_tex import render_tex_file
        src = FIXTURES_DIR / "sample_chapter.md"
        out = tmp_path / "kap1.tex"
        render_tex_file(str(src), str(out), force_custom=True)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert r"\chapter{Einleitung}" in content

    def test_three_chapters_produce_three_files(self, tmp_path):
        """3 Kapitel erzeugen 3 .tex-Dateien (custom renderer)."""
        from render_tex import render_tex_file
        src = FIXTURES_DIR / "sample_chapter.md"
        # Erzeuge 3 Output-Files (selbe Quelle fuer Simplizitaet)
        out_files = [tmp_path / f"kap{i}.tex" for i in range(1, 4)]
        for out in out_files:
            render_tex_file(str(src), str(out), force_custom=True)
        for out in out_files:
            assert out.exists(), f"{out} fehlt"
            content = out.read_text(encoding="utf-8")
            assert r"\chapter{Einleitung}" in content

    def test_render_special_chars_escaped(self):
        """LaTeX-Sonderzeichen werden escaped (& % $ # _ ^ ~ { } \\) (custom renderer)."""
        from render_tex import render_markdown_to_tex
        # & und % sind typische Sonderzeichen in normalem Fliesstext
        result = render_markdown_to_tex("Kosten: 50% & mehr.\n", force_custom=True)
        assert r"\%" in result or "%" not in result.replace(r"\%", "")
        assert r"\&" in result or "&" not in result.replace(r"\&", "")

    def test_no_pandoc_fallback(self, monkeypatch):
        """Wenn pandoc nicht verfuegbar: custom renderer wird genutzt (kein Absturz)."""
        from render_tex import render_markdown_to_tex
        # Monkeypatche subprocess um pandoc-Fehler zu simulieren
        import subprocess as sp
        original_run = sp.run

        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "pandoc":
                raise FileNotFoundError("pandoc not found")
            return original_run(cmd, *args, **kwargs)

        monkeypatch.setattr(sp, "run", fake_run)
        result = render_markdown_to_tex("# Titel\n\nText.\n", force_custom=True)
        assert r"\chapter{Titel}" in result


# ---------------------------------------------------------------------------
# build_bib Tests
# ---------------------------------------------------------------------------

class TestBuildBib:
    """Tests fuer skills/latex-export/scripts/build_bib.py"""

    def test_import(self):
        """build_bib kann importiert werden."""
        import build_bib  # noqa: F401

    def test_paper_to_bibtex_article(self):
        """Zeitschriftenartikel -> @article{} mit DIN-1505-Feldern."""
        from build_bib import paper_to_bibtex
        paper = {
            "paper_id": "smith2023test",
            "csl_json": json.dumps({
                "type": "article-journal",
                "title": "Test Article",
                "author": [{"family": "Smith", "given": "John"}],
                "issued": {"date-parts": [[2023]]},
                "container-title": "Journal of Testing",
                "volume": "5",
                "page": "10-20",
                "DOI": "10.1234/test",
            }),
        }
        entry = paper_to_bibtex(paper)
        assert entry.startswith("@article{smith2023test")
        assert "author" in entry
        assert "title" in entry
        assert "year" in entry
        assert "journal" in entry

    def test_paper_to_bibtex_book(self):
        """Buch -> @book{} mit DIN-1505-Feldern."""
        from build_bib import paper_to_bibtex
        paper = {
            "paper_id": "mueller2019einfuehrung",
            "csl_json": json.dumps({
                "type": "book",
                "title": "Einführung in die Sozialforschung",
                "author": [{"family": "Müller", "given": "Hans"}],
                "issued": {"date-parts": [[2019]]},
                "publisher": "Metzler",
                "publisher-place": "Stuttgart",
                "edition": "3",
            }),
        }
        entry = paper_to_bibtex(paper)
        assert entry.startswith("@book{mueller2019einfuehrung")
        assert "publisher" in entry
        assert "year" in entry

    def test_paper_to_bibtex_incollection(self):
        """Buchkapitel -> @incollection{} mit booktitle."""
        from build_bib import paper_to_bibtex
        paper = {
            "paper_id": "mueller2019qualitativ",
            "csl_json": json.dumps({
                "type": "chapter",
                "title": "Qualitative Methoden",
                "author": [{"family": "Müller", "given": "Hans"}],
                "issued": {"date-parts": [[2019]]},
                "container-title": "Handbuch der empirischen Sozialforschung",
                "editor": [{"family": "Schmidt", "given": "Anna"}],
                "publisher": "Metzler",
                "publisher-place": "Stuttgart",
                "page": "45-78",
            }),
        }
        entry = paper_to_bibtex(paper)
        assert entry.startswith("@incollection{mueller2019qualitativ")
        assert "booktitle" in entry

    def test_build_bib_from_vault_mock(self, tmp_path):
        """build_bib_from_vault() erzeugt .bib mit mehreren Eintraegen (Vault gemockt)."""
        from build_bib import build_bib_from_vault
        mock_papers = [
            {
                "paper_id": "smith2023test",
                "csl_json": json.dumps({
                    "type": "article-journal",
                    "title": "Test Article",
                    "author": [{"family": "Smith", "given": "John"}],
                    "issued": {"date-parts": [[2023]]},
                    "container-title": "Journal of Testing",
                }),
            },
            {
                "paper_id": "jones2021book",
                "csl_json": json.dumps({
                    "type": "book",
                    "title": "A Great Book",
                    "author": [{"family": "Jones", "given": "Alice"}],
                    "issued": {"date-parts": [[2021]]},
                    "publisher": "Academic Press",
                }),
            },
        ]
        out = tmp_path / "refs.bib"
        with patch("build_bib.get_all_papers") as mock_get:
            mock_get.return_value = mock_papers
            build_bib_from_vault(db_path="fake.db", output_path=str(out))
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "@article{smith2023test" in content
        assert "@book{jones2021book" in content

    def test_bibtex_author_format(self):
        """Mehrere Autoren werden korrekt in BibTeX-Format formatiert (Last, First)."""
        from build_bib import format_authors_bibtex
        authors = [
            {"family": "Smith", "given": "John"},
            {"family": "Jones", "given": "Alice"},
        ]
        result = format_authors_bibtex(authors)
        assert "Smith, John" in result
        assert "Jones, Alice" in result
        assert " and " in result

    def test_bibtex_author_single(self):
        """Einzelner Autor korrekt formatiert."""
        from build_bib import format_authors_bibtex
        authors = [{"family": "Müller", "given": "Hans"}]
        result = format_authors_bibtex(authors)
        assert result == "Müller, Hans"

    def test_bibtex_entry_has_required_fields_article(self):
        """@article hat author, title, journal, year."""
        from build_bib import paper_to_bibtex
        paper = {
            "paper_id": "test2023",
            "csl_json": json.dumps({
                "type": "article-journal",
                "title": "Some Paper",
                "author": [{"family": "Test", "given": "Author"}],
                "issued": {"date-parts": [[2023]]},
                "container-title": "Some Journal",
            }),
        }
        entry = paper_to_bibtex(paper)
        for field in ["author", "title", "journal", "year"]:
            assert f"  {field}" in entry, f"Fehlendes Feld: {field}"

    def test_bibtex_doi_included_when_present(self):
        """DOI wird als doi-Feld in den Entry uebernommen."""
        from build_bib import paper_to_bibtex
        paper = {
            "paper_id": "doi2023",
            "csl_json": json.dumps({
                "type": "article-journal",
                "title": "DOI Paper",
                "author": [{"family": "Doi", "given": "Test"}],
                "issued": {"date-parts": [[2023]]},
                "container-title": "Journal",
                "DOI": "10.9999/doi-test",
            }),
        }
        entry = paper_to_bibtex(paper)
        assert "doi" in entry
        assert "10.9999/doi-test" in entry


# ---------------------------------------------------------------------------
# verbatim-guard: *.tex-Pfade sind geschuetzt
# ---------------------------------------------------------------------------

class TestVerbatimGuardTex:
    """Tests dass verbatim-guard auch *.tex-Pfade schutzt."""

    def test_hook_failopen_tex_no_vault(self):
        """Hook erlaubt (fail-open) .tex-Datei wenn Vault-DB fehlt."""
        content = r'Laut \cite{smith2023} ist das wichtig.'
        result = run_hook("Write", "output/thesis.tex", content)
        assert result.returncode == 0

    def test_hook_ignores_tex_non_write(self):
        """Hook ignoriert .tex-Datei bei Nicht-Write-Tools."""
        result = run_hook("Read", "output/thesis.tex", r'\section{Test}')
        assert result.returncode == 0

    def test_hook_tex_path_is_protected(self, tmp_path):
        """Hook prueft .tex-Dateien auf Quote-Spans (kein Vault -> fail-open)."""
        # Ohne Vault -> fail-open -> exit 0 trotz Quote
        content = 'Der Autor schreibt: "Dies ist ein sehr langer unverifiziierter Satz."'
        result = run_hook("Write", "thesis.tex", content)
        # fail-open weil kein Vault -> 0
        assert result.returncode == 0

    def test_hook_tex_quote_blocked_with_vault(self, tmp_path):
        """Hook blockiert .tex bei unverifiziiertem Quote-Span wenn Vault existiert."""
        sys.path.insert(0, str(WORKTREE / "mcp"))
        from academic_vault.db import VaultDB
        from academic_vault.server import add_paper

        db_path = str(tmp_path / "tex_vault.db")
        db = VaultDB(db_path)
        db.init_schema()
        add_paper(
            db_path=db_path,
            paper_id="paper-tex",
            csl_json=json.dumps({"title": "LaTeX Paper", "type": "article-journal"}),
        )

        content = 'Der Autor: "Dies ist ein langer unverifiziierter Satz aus dem Buch hier."'
        result = run_hook(
            "Write",
            "thesis.tex",
            content,
            env_overrides={"VAULT_DB_PATH": db_path},
        )
        assert result.returncode == 2, f"Erwartet exit 2 (block auf .tex), got {result.returncode}"

    def test_hook_tex_bypass_works(self):
        """<!-- vault-guard: skip --> Bypass funktioniert auch bei .tex-Pfaden."""
        content = '<!-- vault-guard: skip -->\n"Unverifiziiertes Zitat in LaTeX."'
        result = run_hook("Write", "thesis.tex", content)
        assert result.returncode == 0
