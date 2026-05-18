"""
CSL-Import: Parst eine .csl-Datei (XML) und generiert Prompt-Regel-Markdown.

Unterstuetzte Quellentypen: article-journal, book, chapter, paper-conference, other.
Ausgabe: Markdown analog skills/citation-extraction/references/apa.md.

Verwendung:
    python csl_import.py springer-basic-author-date.csl -o custom-springer-ad.md
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Optional
from xml.etree import ElementTree as ET

# CSL XML-Namespace
CSL_NS = "http://purl.org/net/xbiblio/csl"
NS = {"csl": CSL_NS}

# Quellentyp-Mapping: CSL-Typ → Lesbare Bezeichnung (DE)
SOURCE_TYPE_LABELS: dict[str, str] = {
    "article-journal": "Zeitschriftenartikel",
    "book": "Buch",
    "chapter": "Buchkapitel",
    "paper-conference": "Konferenzbeitrag",
    "other": "Webseite / Sonstige",
}

# Relevante CSL-Variablen fuer den Parser
RELEVANT_VARIABLES = {
    "author", "editor", "title", "container-title", "issued",
    "volume", "issue", "page", "page-first", "publisher",
    "publisher-place", "DOI", "ISBN", "URL", "edition",
}


class CSLParser:
    """Parst eine .csl-Datei und stellt relevante Metadaten bereit."""

    def __init__(self, source: pathlib.Path | str) -> None:
        self._path = pathlib.Path(source)
        if not self._path.exists():
            raise FileNotFoundError(f"CSL-Datei nicht gefunden: {self._path}")
        self._tree = ET.parse(self._path)
        self._root = self._tree.getroot()
        self._info = self._root.find("csl:info", NS)

    # ------------------------------------------------------------------ #
    # Metadaten
    # ------------------------------------------------------------------ #

    @property
    def style_title(self) -> str:
        """Titel des Stils aus <info><title>."""
        if self._info is None:
            return ""
        title_el = self._info.find("csl:title", NS)
        return title_el.text.strip() if title_el is not None and title_el.text else ""

    @property
    def citation_format(self) -> str:
        """Zitierformat: 'author-date', 'numeric' oder 'note'."""
        if self._info is None:
            return ""
        for cat in self._info.findall("csl:category", NS):
            fmt = cat.get("citation-format", "")
            if fmt:
                return fmt
        return ""

    # ------------------------------------------------------------------ #
    # Macros
    # ------------------------------------------------------------------ #

    @property
    def macros(self) -> dict[str, ET.Element]:
        """Alle <macro name="..."> als Dict name → Element."""
        return {
            m.get("name", ""): m
            for m in self._root.findall("csl:macro", NS)
            if m.get("name")
        }

    # ------------------------------------------------------------------ #
    # Quellentypen
    # ------------------------------------------------------------------ #

    @property
    def source_types(self) -> list[str]:
        """Alle im <bibliography> vorkommenden CSL-Typen + 'other' fuer else-Zweig."""
        bib = self._root.find("csl:bibliography", NS)
        if bib is None:
            return []
        types: list[str] = []
        has_else = False
        for choose in bib.iter(f"{{{CSL_NS}}}choose"):
            for child in choose:
                local = child.tag.split("}")[-1]  # strip namespace
                if local == "if" or local == "else-if":
                    typ = child.get("type", "")
                    if typ:
                        types.extend(t.strip() for t in typ.split() if t.strip())
                elif local == "else":
                    has_else = True
        if has_else:
            types.append("other")
        return list(dict.fromkeys(types))  # deduplicate, preserve order

    # ------------------------------------------------------------------ #
    # Variablen
    # ------------------------------------------------------------------ #

    @property
    def variables(self) -> set[str]:
        """Alle CSL-Variablen, die irgendwo im Dokument referenziert werden."""
        found: set[str] = set()
        for el in self._root.iter():
            for attr in ("variable", "match"):
                val = el.get(attr, "")
                if val:
                    for v in val.split():
                        if v in RELEVANT_VARIABLES:
                            found.add(v)
        return found


# ------------------------------------------------------------------ #
# Markdown-Generierung
# ------------------------------------------------------------------ #

def csl_to_markdown(parser: CSLParser) -> str:
    """
    Wandelt einen CSLParser in Prompt-Regel-Markdown um.

    Format analog skills/citation-extraction/references/apa.md.
    """
    lines: list[str] = []

    # Header
    title = parser.style_title or "Unbekannter Stil"
    lines += [
        f"# {title}",
        "",
        f"**Zitierformat:** {parser.citation_format or 'unbekannt'}",
        "",
    ]

    # Inline-Zitat-Abschnitt
    lines += [
        "## Inline-Zitat",
        "",
    ]
    if parser.citation_format == "author-date":
        lines += [
            "- 1 Autor: `(Smith 2023)` oder `Smith (2023)`",
            "- 2 Autoren: `(Smith, Jones 2023)`",
            "- 3+ Autoren: `(Smith et al. 2023)`",
            "- Mit Seitenzahl: `(Smith 2023, S. 42)`",
            "",
        ]
    elif parser.citation_format == "numeric":
        lines += [
            "- Numerisch: `[1]`, `[1, 2]` oder `[1–3]`",
            "",
        ]
    else:
        lines += [
            "- Stilspezifisches Format — Details aus der CSL-Definition entnehmen.",
            "",
        ]

    # Literaturverzeichnis-Abschnitt
    lines += [
        "## Literaturverzeichnis",
        "",
    ]

    source_types = parser.source_types
    if not source_types:
        source_types = list(SOURCE_TYPE_LABELS.keys())

    for typ in source_types:
        label = SOURCE_TYPE_LABELS.get(typ, typ)
        rule = _rule_for_type(typ, parser.citation_format)
        lines += [
            f"**{label} (`{typ}`):**",
            f"`{rule}`",
            "",
        ]

    # Besonderheiten
    variables = parser.variables
    lines += ["## Besonderheiten", ""]
    hints: list[str] = []
    if "DOI" in variables:
        hints.append("- DOI als `https://doi.org/...` URL angeben")
    if "issued" in variables:
        hints.append("- Erscheinungsjahr ist Pflichtfeld")
    if "author" in variables:
        hints.append("- Nachname vor Initiale(n) in Literaturverzeichnis-Eintraegen")
    if "container-title" in variables:
        hints.append("- Zeitschriften-/Buchtitel kursiv setzen")
    if not hints:
        hints.append("- Keine besonderen Hinweise")
    lines.extend(hints)
    lines.append("")

    return "\n".join(lines)


def _rule_for_type(typ: str, citation_format: str) -> str:
    """Gibt eine Beispiel-Formatregel fuer den Quellentyp zurueck."""
    if typ == "article-journal":
        if citation_format == "author-date":
            return "Nachname V (Jahr) Titel. Zeitschrift Band:Seiten. https://doi.org/DOI"
        return "Nachname, Initiale. (Jahr). Titel. Zeitschrift, Band(Heft), Seiten. https://doi.org/DOI"
    elif typ == "book":
        if citation_format == "author-date":
            return "Nachname V (Jahr) Titel, Aufl. Verlag, Ort"
        return "Nachname, Initiale. (Jahr). Titel (Auflage). Verlag."
    elif typ == "chapter":
        if citation_format == "author-date":
            return "Nachname V (Jahr) Kapiteltitel. In: Buchtitel, Hrsg V Nachname. Verlag, Ort, pp Seiten"
        return "Nachname, Initiale. (Jahr). Kapiteltitel. In Hrsg. (Hrsg.), Buchtitel (S. XX–YY). Verlag."
    elif typ == "paper-conference":
        if citation_format == "author-date":
            return "Nachname V (Jahr) Titel. In: Konferenz-Proceedings, Ort, pp Seiten"
        return "Nachname, Initiale. (Jahr). Titel. Konferenz-Proceedings, Seiten."
    elif typ == "other":
        return "Nachname, Initiale. (Jahr). Titel. URL"
    return f"Nachname (Jahr) Titel [{typ}]"


# ------------------------------------------------------------------ #
# CLI-Einstiegspunkt
# ------------------------------------------------------------------ #

def main() -> None:
    parser_args = argparse.ArgumentParser(
        description="CSL-Datei in Prompt-Regel-Markdown umwandeln"
    )
    parser_args.add_argument(
        "csl_file",
        type=pathlib.Path,
        help="Pfad zur .csl-Datei oder URL (lokal: Pfad; remote: URL)",
    )
    parser_args.add_argument(
        "-o", "--output",
        type=pathlib.Path,
        default=None,
        help="Ausgabedatei (Standard: stdout)",
    )
    args = parser_args.parse_args()

    csl_parser = CSLParser(args.csl_file)
    md = csl_to_markdown(csl_parser)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"Geschrieben: {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
