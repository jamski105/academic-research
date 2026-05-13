"""book_resolve.py — ISBN/Titel/DOI -> CSL-JSON via DNB SRU, OpenLibrary,
GoogleBooks, DOAB.

CLI:
    python scripts/book_resolve.py --isbn 9783446461031
    python scripts/book_resolve.py --title "Werkzeugmaschinen Grundlagen"
    python scripts/book_resolve.py --doi 10.1007/978-3-658-12345-6

Output: CSL-JSON auf stdout. Fehler auf stderr. Exit-Code 0/1.
"""
import argparse
import json
import sys
from typing import Optional

try:
    import requests
    from lxml import etree
except ImportError as _e:
    print(
        f"[ERROR] Fehlende Abhaengigkeit: {_e}. Bitte 'pip install requests lxml' ausfuehren.",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# DNB SRU Client
# ---------------------------------------------------------------------------

DNB_SRU_URL = "https://services.dnb.de/sru/dnb"
_MARC_NS = "http://www.loc.gov/MARC21/slim"
_SRW_NS = "http://www.loc.gov/zing/srw/"


def _marc_field(record_el, tag: str, subfield_code: str, ns: str) -> Optional[str]:
    """Extrahiert Inhalt eines MARC-Subfelds aus einem lxml-Element."""
    for df in record_el.findall(f".//{{{ns}}}datafield[@tag='{tag}']"):
        for sf in df.findall(f"{{{ns}}}subfield[@code='{subfield_code}']"):
            if sf.text:
                return sf.text.strip()
    return None


def _marc_all_fields(record_el, tag: str, subfield_code: str, ns: str) -> list:
    """Gibt alle Werte eines MARC-Subfelds zurueck (fuer mehrfache Autoren/Editoren)."""
    results = []
    for df in record_el.findall(f".//{{{ns}}}datafield[@tag='{tag}']"):
        for sf in df.findall(f"{{{ns}}}subfield[@code='{subfield_code}']"):
            if sf.text:
                results.append(sf.text.strip())
    return results


def _parse_name(raw: str) -> dict:
    """Wandelt 'Nachname, Vorname' in CSL-Name-Dict um."""
    parts = raw.split(",", 1)
    if len(parts) == 2:
        return {"family": parts[0].strip(), "given": parts[1].strip()}
    return {"literal": raw.strip()}


def _dnb_record_to_csl(record_el) -> dict:
    """Wandelt ein MARC21-Record-Element in CSL-JSON-Dict um."""
    ns = _MARC_NS
    csl: dict = {"type": "book"}

    title_a = _marc_field(record_el, "245", "a", ns) or ""
    title_b = _marc_field(record_el, "245", "b", ns) or ""
    csl["title"] = (title_a + (" " + title_b if title_b else "")).rstrip(": /,").strip()

    authors = []
    for tag in ("100", "700"):
        for n in _marc_all_fields(record_el, tag, "a", ns):
            authors.append(_parse_name(n))
    if authors:
        csl["author"] = authors

    editors = []
    for df in record_el.findall(f".//{{{ns}}}datafield[@tag='700']"):
        role_sf = df.find(f"{{{ns}}}subfield[@code='e']")
        name_sf = df.find(f"{{{ns}}}subfield[@code='a']")
        if role_sf is not None and name_sf is not None:
            role = (role_sf.text or "").lower()
            if any(r in role for r in ("hrsg", "editor", "hg")):
                editors.append(_parse_name(name_sf.text))
    if editors:
        csl["editor"] = editors

    publisher = _marc_field(record_el, "264", "b", ns)
    if publisher:
        csl["publisher"] = publisher.rstrip(",").strip()
    year_str = _marc_field(record_el, "264", "c", ns)
    if year_str:
        year_digits = "".join(c for c in year_str if c.isdigit())[:4]
        if year_digits:
            csl["issued"] = {"date-parts": [[int(year_digits)]]}

    isbn = _marc_field(record_el, "020", "a", ns)
    if isbn:
        csl["ISBN"] = isbn.replace("-", "").strip()

    for df in record_el.findall(f".//{{{ns}}}datafield[@tag='024']"):
        type_sf = df.find(f"{{{ns}}}subfield[@code='2']")
        id_sf = df.find(f"{{{ns}}}subfield[@code='a']")
        if type_sf is not None and id_sf is not None:
            if (type_sf.text or "").lower() == "doi":
                csl["DOI"] = id_sf.text.strip()

    return csl


def resolve_dnb(isbn: Optional[str] = None, title: Optional[str] = None) -> Optional[dict]:
    """Loest ISBN oder Titel via DNB SRU auf. Gibt CSL-Dict oder None zurueck."""
    if isbn:
        query = f"isbn+%3D+{isbn.replace('-', '')}"
    elif title:
        safe_title = requests.utils.quote(title)
        query = f"title+%3D+{safe_title}"
    else:
        return None

    params = {
        "version": "1.1",
        "operation": "searchRetrieve",
        "query": query,
        "recordSchema": "MARC21-xml",
        "maximumRecords": "1",
    }
    try:
        resp = requests.get(DNB_SRU_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[WARN] DNB SRU Fehler: {exc}", file=sys.stderr)
        return None

    try:
        root = etree.fromstring(resp.content)
        records = root.findall(f".//{{{_SRW_NS}}}numberOfRecords")
        if not records or records[0].text == "0":
            return None
        record_els = root.findall(f".//{{{_MARC_NS}}}record")
        if not record_els:
            return None
        return _dnb_record_to_csl(record_els[0])
    except Exception as exc:
        print(f"[WARN] DNB XML-Parse-Fehler: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# OpenLibrary Client
# ---------------------------------------------------------------------------

OL_API_URL = "https://openlibrary.org/api/books"


def resolve_openlibrary(isbn: Optional[str] = None) -> Optional[dict]:
    """ISBN -> CSL-Dict via OpenLibrary JSON-API. Gibt None bei Fehler/leer."""
    if not isbn:
        return None
    key = f"ISBN:{isbn.replace('-', '')}"
    try:
        resp = requests.get(
            OL_API_URL,
            params={"bibkeys": key, "jscmd": "data", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[WARN] OpenLibrary Fehler: {exc}", file=sys.stderr)
        return None

    if not data or key not in data:
        return None

    item = data[key]
    csl: dict = {"type": "book"}
    csl["title"] = item.get("title", "")

    authors = [{"literal": a["name"]} for a in item.get("authors", [])]
    if authors:
        csl["author"] = authors

    publishers = item.get("publishers", [])
    if publishers:
        csl["publisher"] = publishers[0].get("name", "")

    pub_date = item.get("publish_date", "")
    year_digits = "".join(c for c in pub_date if c.isdigit())[:4]
    if year_digits:
        csl["issued"] = {"date-parts": [[int(year_digits)]]}

    isbn13 = item.get("isbn_13", [])
    if isbn13:
        csl["ISBN"] = isbn13[0]

    return csl if csl.get("title") else None


# ---------------------------------------------------------------------------
# GoogleBooks Client
# ---------------------------------------------------------------------------

GB_API_URL = "https://www.googleapis.com/books/v1/volumes"


def resolve_googlebooks(isbn: Optional[str] = None, title: Optional[str] = None) -> Optional[dict]:
    """ISBN oder Titel -> CSL-Dict via GoogleBooks JSON-API."""
    if isbn:
        query = f"isbn:{isbn.replace('-', '')}"
    elif title:
        query = title
    else:
        return None

    try:
        resp = requests.get(GB_API_URL, params={"q": query, "maxResults": 1}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[WARN] GoogleBooks Fehler: {exc}", file=sys.stderr)
        return None

    items = data.get("items", [])
    if not items:
        return None

    vi = items[0].get("volumeInfo", {})
    csl: dict = {"type": "book"}
    csl["title"] = vi.get("title", "")

    raw_authors = vi.get("authors", [])
    if raw_authors:
        csl["author"] = [_parse_name(a) for a in raw_authors]

    publisher = vi.get("publisher")
    if publisher:
        csl["publisher"] = publisher

    pub_date = vi.get("publishedDate", "")
    year_digits = "".join(c for c in pub_date if c.isdigit())[:4]
    if year_digits:
        csl["issued"] = {"date-parts": [[int(year_digits)]]}

    for id_entry in vi.get("industryIdentifiers", []):
        if id_entry.get("type") == "ISBN_13":
            csl["ISBN"] = id_entry["identifier"]
        elif id_entry.get("type") == "ISBN_10" and "ISBN" not in csl:
            csl["ISBN"] = id_entry["identifier"]

    return csl if csl.get("title") else None


# ---------------------------------------------------------------------------
# DOAB Client
# ---------------------------------------------------------------------------

DOAB_API_URL = "https://directory.doabooks.org/rest/search"


def check_doab(isbn: Optional[str] = None, doi: Optional[str] = None) -> Optional[dict]:
    """Prueft DOAB auf OA-Verfuegbarkeit. Gibt {open_access: True, download_url: ...} oder None."""
    if isbn:
        query = f"isbn:{isbn.replace('-', '')}"
    elif doi:
        query = f"doi:{doi}"
    else:
        return None

    try:
        resp = requests.get(
            DOAB_API_URL,
            params={"query": query, "expand": "metadata,bitstreams"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[WARN] DOAB Fehler: {exc}", file=sys.stderr)
        return None

    if not data:
        return None

    result: dict = {"open_access": True}
    # Download-URL aus Bitstreams extrahieren
    for item in data:
        for bs in item.get("bitstreams", []):
            if bs.get("mimeType") == "application/pdf":
                link = bs.get("retrieveLink", "")
                if link:
                    result["download_url"] = (
                        f"https://directory.doabooks.org{link}"
                        if link.startswith("/")
                        else link
                    )
                    break
        if "download_url" in result:
            break

    # OAPEN-URL als Fallback
    if "download_url" not in result:
        for item in data:
            for meta in item.get("metadata", []):
                if meta.get("key") == "dc.identifier.uri":
                    result["download_url"] = meta.get("value", "")
                    break
            if "download_url" in result:
                break

    return result


# ---------------------------------------------------------------------------
# Hauptfunktion: resolve() — Fallback-Kette
# ---------------------------------------------------------------------------

def resolve(
    isbn: Optional[str] = None,
    title: Optional[str] = None,
    doi: Optional[str] = None,
) -> dict:
    """Loest Buch-Metadaten auf: DNB -> OL -> GoogleBooks. DOAB als OA-Ergaenzung.

    Gibt CSL-JSON-Dict zurueck (evtl. leer bei totalem Fehlschlag).
    """
    # ISBN einmalig normalisieren (Bindestriche entfernen)
    norm_isbn = isbn.replace("-", "") if isbn else None

    csl: Optional[dict] = None

    # 1. DNB SRU
    csl = resolve_dnb(isbn=norm_isbn, title=title)

    # 2. OpenLibrary (Fallback)
    if not csl and norm_isbn:
        csl = resolve_openlibrary(isbn=norm_isbn)

    # 3. GoogleBooks (Fallback)
    if not csl:
        csl = resolve_googlebooks(isbn=norm_isbn, title=title)

    if csl is None:
        csl = {}

    if doi and "DOI" not in csl:
        csl["DOI"] = doi

    # DOAB OA-Check (ergaenzend)
    oa_info = check_doab(isbn=norm_isbn, doi=doi or csl.get("DOI"))
    if oa_info:
        csl["open_access"] = oa_info.get("open_access", False)
        if oa_info.get("download_url"):
            csl["URL"] = oa_info["download_url"]

    return csl


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli_main() -> None:
    parser = argparse.ArgumentParser(
        description="ISBN/Titel/DOI -> CSL-JSON via DNB, OpenLibrary, GoogleBooks, DOAB"
    )
    parser.add_argument("--isbn", help="ISBN-13 (mit oder ohne Bindestriche)")
    parser.add_argument("--title", help="Buchtitel (Freitext)")
    parser.add_argument("--doi", help="DOI (z.B. 10.1007/978-...)")
    args = parser.parse_args()

    if not any([args.isbn, args.title, args.doi]):
        parser.print_help()
        sys.exit(1)

    result = resolve(isbn=args.isbn, title=args.title, doi=args.doi)
    if not result:
        print("{}", file=sys.stdout)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli_main()
