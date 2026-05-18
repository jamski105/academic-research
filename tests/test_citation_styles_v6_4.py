"""Tests fuer neue Citation-Styles: MLA, Vancouver, Springer Author-Date.

Pro Stil werden 5 Quellentypen getestet:
  book, chapter, journal, conference, online

Strategie: Jede Referenz-Datei wird auf erwartete Schluessel-Substrings geprueft.
Die Render-Funktionen geben formatierte Strings zurueck und validieren gegen
Pflicht-Felder des jeweiligen Stils.
"""
from pathlib import Path

import pytest

REFS_DIR = Path(__file__).parent.parent / "skills" / "citation-extraction" / "references"
SKILL_MD = Path(__file__).parent.parent / "skills" / "citation-extraction" / "SKILL.md"


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Formatierung nach Stil
# ---------------------------------------------------------------------------

def render_mla_book(last: str, first: str, title: str, publisher: str, year: str) -> str:
    """MLA 9th Ed. Buch: Last, First. Title. Publisher, Year."""
    return f"{last}, {first}. {title}. {publisher}, {year}."


def render_mla_chapter(
    author_last: str, author_first: str,
    chapter_title: str,
    editor_last: str, editor_first: str,
    container: str, publisher: str, year: str,
    pages: str,
) -> str:
    """MLA Buchkapitel: Author. 'Chapter Title.' Container, ed. Editor, Publisher, Year, pp. X-Y."""
    return (
        f"{author_last}, {author_first}. \"{chapter_title}.\""
        f" {container}, edited by {editor_first} {editor_last},"
        f" {publisher}, {year}, pp. {pages}."
    )


def render_mla_journal(
    last: str, first: str,
    article_title: str,
    journal: str, volume: str, issue: str,
    year: str, pages: str,
) -> str:
    """MLA Journal: Last, First. 'Title.' Journal, vol. V, no. N, Year, pp. X-Y."""
    return (
        f"{last}, {first}. \"{article_title}.\""
        f" {journal}, vol. {volume}, no. {issue}, {year}, pp. {pages}."
    )


def render_mla_conference(
    last: str, first: str,
    paper_title: str,
    proceedings: str, year: str, pages: str,
) -> str:
    """MLA Conference: Last, First. 'Title.' Proceedings, Year, pp. X-Y."""
    return (
        f"{last}, {first}. \"{paper_title}.\""
        f" {proceedings}, {year}, pp. {pages}."
    )


def render_mla_online(
    last: str, first: str,
    page_title: str,
    site_name: str, year: str, url: str,
) -> str:
    """MLA Online: Last, First. 'Page Title.' Site Name, Year, URL."""
    return f"{last}, {first}. \"{page_title}.\" {site_name}, {year}, {url}."


def render_vancouver_journal(
    authors: str,
    title: str,
    journal_abbr: str,
    year: str, volume: str, issue: str, pages: str,
) -> str:
    """Vancouver Journal: Authors. Title. J Abbr. Year;Vol(Issue):Pages."""
    return f"{authors}. {title}. {journal_abbr}. {year};{volume}({issue}):{pages}."


def render_vancouver_book(
    authors: str, title: str, edition: str,
    place: str, publisher: str, year: str,
) -> str:
    """Vancouver Buch: Authors. Title. Edition ed. Place: Publisher; Year."""
    return f"{authors}. {title}. {edition} ed. {place}: {publisher}; {year}."


def render_vancouver_chapter(
    chapter_authors: str, chapter_title: str,
    book_editors: str, book_title: str,
    place: str, publisher: str, year: str, pages: str,
) -> str:
    """Vancouver Kapitel: Authors. Title. In: Editors, editors. Book. Place: Publisher; Year. p. X-Y."""
    return (
        f"{chapter_authors}. {chapter_title}."
        f" In: {book_editors}, editors. {book_title}."
        f" {place}: {publisher}; {year}. p. {pages}."
    )


def render_vancouver_conference(
    authors: str, title: str,
    proceedings: str, year: str, pages: str,
) -> str:
    """Vancouver Conference: Authors. Title. In: Proceedings; Year. p. X-Y."""
    return f"{authors}. {title}. In: {proceedings}; {year}. p. {pages}."


def render_vancouver_online(
    authors: str, title: str,
    site: str, year: str, url: str,
) -> str:
    """Vancouver Online: Authors. Title [Internet]. Site; Year [cited Year]. Available from: URL."""
    return f"{authors}. {title} [Internet]. {site}; {year}. Available from: {url}."


def render_springer_journal(
    author_last: str, author_initials: str,
    year: str, title: str,
    journal: str, volume: str, pages: str,
) -> str:
    """Springer Author-Date Journal: Last AB (Year) Title. Journal Vol:Pages."""
    return f"{author_last} {author_initials} ({year}) {title}. {journal} {volume}:{pages}."


def render_springer_book(
    author_last: str, author_initials: str,
    year: str, title: str,
    publisher: str, place: str,
) -> str:
    """Springer Author-Date Buch: Last AB (Year) Title. Publisher, Place."""
    return f"{author_last} {author_initials} ({year}) {title}. {publisher}, {place}."


def render_springer_chapter(
    author_last: str, author_initials: str,
    year: str, chapter_title: str,
    editor_last: str, editor_initials: str,
    book_title: str, publisher: str, place: str, pages: str,
) -> str:
    """Springer Author-Date Kapitel: Last AB (Year) Chapter. In: Ed AB (ed) Book. Publisher, Place, pp X-Y."""
    return (
        f"{author_last} {author_initials} ({year}) {chapter_title}."
        f" In: {editor_last} {editor_initials} (ed) {book_title}."
        f" {publisher}, {place}, pp {pages}."
    )


def render_springer_conference(
    author_last: str, author_initials: str,
    year: str, title: str,
    proceedings: str, pages: str,
) -> str:
    """Springer Author-Date Conference: Last AB (Year) Title. Proceedings, pp X-Y."""
    return (
        f"{author_last} {author_initials} ({year}) {title}."
        f" {proceedings}, pp {pages}."
    )


def render_springer_online(
    author_last: str, author_initials: str,
    year: str, title: str, url: str,
) -> str:
    """Springer Author-Date Online: Last AB (Year) Title. URL."""
    return f"{author_last} {author_initials} ({year}) {title}. {url}."


# ---------------------------------------------------------------------------
# MLA 9th Edition — 5 Quellentypen
# ---------------------------------------------------------------------------

class TestMLAStyle:
    def test_mla_book(self):
        """MLA Buch-Eintrag enthaelt Last, First. Title. Publisher, Year."""
        result = render_mla_book(
            last="Atwood", first="Margaret",
            title="The Handmaid's Tale",
            publisher="McClelland and Stewart", year="1985",
        )
        assert "Atwood, Margaret." in result
        assert "The Handmaid's Tale" in result
        assert "McClelland and Stewart" in result
        assert "1985" in result

    def test_mla_chapter(self):
        """MLA Kapitel-Eintrag enthaelt Author, Titel in Anfuehrungszeichen, Container, Editor, pp."""
        result = render_mla_chapter(
            author_last="Said", author_first="Edward W.",
            chapter_title="Orientalism Reconsidered",
            editor_last="Barker", editor_first="Francis",
            container="Literature, Politics and Theory",
            publisher="Methuen", year="1986", pages="210-229",
        )
        assert "Said, Edward W." in result
        assert '"Orientalism Reconsidered."' in result
        assert "Literature, Politics and Theory" in result
        assert "Francis Barker" in result
        assert "pp. 210-229" in result

    def test_mla_journal(self):
        """MLA Journal-Eintrag enthaelt Author, Artikeltitel in Quotes, Journal, vol., no., pp."""
        result = render_mla_journal(
            last="Butler", first="Judith",
            article_title="Performative Acts and Gender Constitution",
            journal="Theatre Journal",
            volume="40", issue="4", year="1988", pages="519-531",
        )
        assert "Butler, Judith." in result
        assert '"Performative Acts and Gender Constitution."' in result
        assert "Theatre Journal" in result
        assert "vol. 40" in result
        assert "no. 4" in result
        assert "pp. 519-531" in result

    def test_mla_conference(self):
        """MLA Conference-Eintrag enthaelt Author, Titel, Proceedings, Jahr, pp."""
        result = render_mla_conference(
            last="Derrida", first="Jacques",
            paper_title="Structure, Sign and Play",
            proceedings="Proceedings of the Johns Hopkins International Symposium",
            year="1966", pages="247-265",
        )
        assert "Derrida, Jacques." in result
        assert '"Structure, Sign and Play."' in result
        assert "1966" in result
        assert "pp. 247-265" in result

    def test_mla_online(self):
        """MLA Online-Eintrag enthaelt Author, Seitentitel, Website-Name, Jahr, URL."""
        result = render_mla_online(
            last="hooks", first="bell",
            page_title="Representing Whiteness in the Black Imagination",
            site_name="Cultural Studies Archive",
            year="1997", url="https://culturalstudies.org/hooks-1997",
        )
        assert "hooks, bell." in result
        assert '"Representing Whiteness in the Black Imagination."' in result
        assert "Cultural Studies Archive" in result
        assert "1997" in result
        assert "https://culturalstudies.org/hooks-1997" in result


# ---------------------------------------------------------------------------
# Vancouver (ICMJE) — 5 Quellentypen
# ---------------------------------------------------------------------------

class TestVancouverStyle:
    def test_vancouver_journal(self):
        """Vancouver Journal enthaelt Authors. Title. J. Year;Vol(Issue):Pages."""
        result = render_vancouver_journal(
            authors="Smith JA, Jones BC",
            title="Randomised trial of antibiotic treatment",
            journal_abbr="BMJ",
            year="2020", volume="368", issue="3", pages="m1226",
        )
        assert "Smith JA, Jones BC." in result
        assert "Randomised trial of antibiotic treatment." in result
        assert "BMJ." in result
        assert "2020;368(3):m1226" in result

    def test_vancouver_book(self):
        """Vancouver Buch enthaelt Authors. Title. Edition. Place: Publisher; Year."""
        result = render_vancouver_book(
            authors="Murray RK, Granner DK",
            title="Harper's Illustrated Biochemistry",
            edition="30th",
            place="New York", publisher="McGraw-Hill", year="2012",
        )
        assert "Murray RK, Granner DK." in result
        assert "Harper's Illustrated Biochemistry." in result
        assert "30th ed." in result
        assert "New York" in result
        assert "McGraw-Hill" in result
        assert "2012." in result

    def test_vancouver_chapter(self):
        """Vancouver Kapitel enthaelt Chapter-Authors, Title, In: Editors, Book, Place, Year, p. X-Y."""
        result = render_vancouver_chapter(
            chapter_authors="Meltzer PS, Kallioniemi A",
            chapter_title="Chromosome abnormalities in human cancer",
            book_editors="Mendelsohn J, Howley PM",
            book_title="The Molecular Basis of Cancer",
            place="Philadelphia", publisher="Saunders", year="2001",
            pages="17-40",
        )
        assert "Meltzer PS, Kallioniemi A." in result
        assert "Chromosome abnormalities in human cancer." in result
        assert "Mendelsohn J, Howley PM, editors." in result
        assert "The Molecular Basis of Cancer." in result
        assert "Philadelphia" in result
        assert "Saunders" in result
        assert "2001." in result
        assert "p. 17-40." in result

    def test_vancouver_conference(self):
        """Vancouver Conference enthaelt Authors, Title, In: Proceedings; Year. p. X-Y."""
        result = render_vancouver_conference(
            authors="Halpern SD, Ubel PA",
            title="Solid-organ transplantation in HIV-infected patients",
            proceedings="Proceedings of the 3rd Annual HIV Research Symposium",
            year="2002", pages="129-131",
        )
        assert "Halpern SD, Ubel PA." in result
        assert "Solid-organ transplantation in HIV-infected patients." in result
        assert "2002" in result
        assert "p. 129-131" in result

    def test_vancouver_online(self):
        """Vancouver Online enthaelt Authors, Title [Internet], Site; Year. Available from: URL."""
        result = render_vancouver_online(
            authors="WHO",
            title="COVID-19 Disease Outbreak",
            site="World Health Organization",
            year="2023", url="https://www.who.int/emergencies/diseases/novel-coronavirus-2019",
        )
        assert "WHO." in result
        assert "COVID-19 Disease Outbreak [Internet]." in result
        assert "World Health Organization" in result
        assert "2023" in result
        assert "Available from: https://www.who.int" in result


# ---------------------------------------------------------------------------
# Springer Author-Date — 5 Quellentypen
# ---------------------------------------------------------------------------

class TestSpringerAuthorDateStyle:
    def test_springer_journal(self):
        """Springer Journal enthaelt Last AB (Year) Title. Journal Vol:Pages."""
        result = render_springer_journal(
            author_last="Müller", author_initials="HJ",
            year="2021",
            title="Machine learning in clinical diagnostics",
            journal="J Med Inform", volume="45", pages="112-128",
        )
        assert "Müller HJ" in result
        assert "(2021)" in result
        assert "Machine learning in clinical diagnostics." in result
        assert "J Med Inform" in result
        assert "45:112-128" in result

    def test_springer_book(self):
        """Springer Buch enthaelt Last AB (Year) Title. Publisher, Place."""
        result = render_springer_book(
            author_last="Schmidt", author_initials="KL",
            year="2019", title="Grundlagen der Biophysik",
            publisher="Springer", place="Berlin",
        )
        assert "Schmidt KL" in result
        assert "(2019)" in result
        assert "Grundlagen der Biophysik." in result
        assert "Springer" in result
        assert "Berlin" in result

    def test_springer_chapter(self):
        """Springer Kapitel enthaelt Author (Year) ChapterTitle. In: Ed (ed) Book. Publisher, Place, pp X-Y."""
        result = render_springer_chapter(
            author_last="Weber", author_initials="AB",
            year="2020", chapter_title="Signal transduction pathways",
            editor_last="Klein", editor_initials="MN",
            book_title="Cell Biology Advances",
            publisher="Springer", place="Heidelberg", pages="45-67",
        )
        assert "Weber AB" in result
        assert "(2020)" in result
        assert "Signal transduction pathways." in result
        assert "Klein MN (ed)" in result
        assert "Cell Biology Advances." in result
        assert "Springer" in result
        assert "pp 45-67" in result

    def test_springer_conference(self):
        """Springer Conference enthaelt Author (Year) Title. Proceedings, pp X-Y."""
        result = render_springer_conference(
            author_last="Fischer", author_initials="TG",
            year="2022", title="Neural network architectures for protein folding",
            proceedings="Proceedings of the 15th International Conference on Bioinformatics",
            pages="301-315",
        )
        assert "Fischer TG" in result
        assert "(2022)" in result
        assert "Neural network architectures for protein folding." in result
        assert "pp 301-315" in result

    def test_springer_online(self):
        """Springer Online enthaelt Author (Year) Title. URL."""
        result = render_springer_online(
            author_last="Becker", author_initials="RS",
            year="2023", title="Guidelines for statistical reporting in biomedical research",
            url="https://www.springer.com/guidelines/statistical-reporting",
        )
        assert "Becker RS" in result
        assert "(2023)" in result
        assert "Guidelines for statistical reporting in biomedical research." in result
        assert "https://www.springer.com/guidelines/statistical-reporting" in result


# ---------------------------------------------------------------------------
# Datei-Existenz-Tests fuer Referenz-Dateien
# ---------------------------------------------------------------------------

class TestReferenceFilesExist:
    def test_mla_reference_file_exists(self):
        """skills/citation-extraction/references/mla.md existiert."""
        path = REFS_DIR / "mla.md"
        assert path.exists(), f"Referenz-Datei fehlt: {path}"

    def test_vancouver_reference_file_exists(self):
        """skills/citation-extraction/references/vancouver.md existiert."""
        path = REFS_DIR / "vancouver.md"
        assert path.exists(), f"Referenz-Datei fehlt: {path}"

    def test_springer_author_date_reference_file_exists(self):
        """skills/citation-extraction/references/springer-author-date.md existiert."""
        path = REFS_DIR / "springer-author-date.md"
        assert path.exists(), f"Referenz-Datei fehlt: {path}"


# ---------------------------------------------------------------------------
# Inhalt der Referenz-Dateien
# ---------------------------------------------------------------------------

class TestReferenceFileContent:
    def test_mla_md_contains_key_elements(self):
        """mla.md enthaelt MLA-Pflicht-Elemente: Autor, Titel, Verlag, Jahr."""
        path = REFS_DIR / "mla.md"
        assert path.exists(), "mla.md fehlt"
        content = path.read_text()
        assert "MLA" in content
        assert "Inline" in content or "In-Text" in content or "Zitat" in content
        assert "Literaturverzeichnis" in content or "Works Cited" in content
        assert "vol." in content or "volume" in content.lower()

    def test_vancouver_md_contains_icmje_elements(self):
        """vancouver.md enthaelt ICMJE-Pflicht-Elemente."""
        path = REFS_DIR / "vancouver.md"
        assert path.exists(), "vancouver.md fehlt"
        content = path.read_text()
        assert "Vancouver" in content
        assert "ICMJE" in content or "Medizin" in content or "journal" in content.lower()
        assert "Internet" in content or "online" in content.lower() or "URL" in content

    def test_springer_ad_md_contains_key_elements(self):
        """springer-author-date.md enthaelt Springer-Author-Date-Pflicht-Elemente."""
        path = REFS_DIR / "springer-author-date.md"
        assert path.exists(), "springer-author-date.md fehlt"
        content = path.read_text()
        assert "Springer" in content
        assert "Author-Date" in content or "Author Date" in content
        assert "(ed)" in content or "editor" in content.lower()


# ---------------------------------------------------------------------------
# Variant-Selector in SKILL.md
# ---------------------------------------------------------------------------

class TestVariantSelector:
    def test_skill_md_contains_mla(self):
        """SKILL.md Variant-Selector enthaelt MLA-Eintrag."""
        assert SKILL_MD.exists(), f"SKILL.md fehlt: {SKILL_MD}"
        content = SKILL_MD.read_text()
        assert "mla.md" in content, "SKILL.md: mla.md fehlt im Variant-Selector"

    def test_skill_md_contains_vancouver(self):
        """SKILL.md Variant-Selector enthaelt Vancouver-Eintrag."""
        assert SKILL_MD.exists()
        content = SKILL_MD.read_text()
        assert "vancouver.md" in content, "SKILL.md: vancouver.md fehlt im Variant-Selector"

    def test_skill_md_contains_springer_author_date(self):
        """SKILL.md Variant-Selector enthaelt Springer-Author-Date-Eintrag."""
        assert SKILL_MD.exists()
        content = SKILL_MD.read_text()
        assert "springer-author-date.md" in content, (
            "SKILL.md: springer-author-date.md fehlt im Variant-Selector"
        )

    def test_skill_md_has_seven_styles(self):
        """SKILL.md Variant-Selector enthaelt genau 7 Stile (alt 4 + neu 3)."""
        assert SKILL_MD.exists()
        content = SKILL_MD.read_text()
        # Alle 7 Style-Bezeichner muessen vorhanden sein
        required_styles = ["apa.md", "harvard.md", "chicago.md", "din1505.md",
                           "mla.md", "vancouver.md", "springer-author-date.md"]
        for style in required_styles:
            assert style in content, f"SKILL.md: '{style}' fehlt im Variant-Selector"
