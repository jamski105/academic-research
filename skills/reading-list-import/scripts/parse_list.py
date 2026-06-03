"""parse_list.py — Reading-List-Import Skill (F14).

Extrahiert strukturierte Bibliographieeintraege aus PDF/Markdown/Plaintext,
resolvet DOI/ISBN via Crossref + book_resolve, und schreibt alles in den Vault.

CLI:
    python skills/reading-list-import/scripts/parse_list.py --file refs.txt --db vault.db

Verwendbar auch als Modul (fuer Tests und den Skill selbst).
"""
from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional-Dependencies (graceful fallback)
# ---------------------------------------------------------------------------

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

try:
    import anthropic as _anthropic_module
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

# book_resolve ist im scripts/-Verzeichnis des Repos
_REPO_SCRIPTS = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
if str(_REPO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_REPO_SCRIPTS))

# server.py-Funktionen fuer Vault-Zugriff (als optionale Laufzeit-Deps)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
    from academic_vault.server import add_paper as _vault_add_paper_native
    _VAULT_NATIVE = True
except ImportError:
    _VAULT_NATIVE = False


# ---------------------------------------------------------------------------
# Oeffentliche Interfaces (werden in Tests gemockt)
# ---------------------------------------------------------------------------

def vault_add_paper(
    db_path: str,
    paper_id: str,
    csl_json: str,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
) -> None:
    """Wrapper um academic_vault.server.add_paper.

    Wird in Tests via patch() ersetzt.
    """
    if _VAULT_NATIVE:
        _vault_add_paper_native(
            db_path=db_path,
            paper_id=paper_id,
            csl_json=csl_json,
            doi=doi,
            isbn=isbn,
        )
    else:
        raise RuntimeError(
            "vault_add_paper: academic_vault.server nicht verfuegbar. "
            "Stelle sicher dass der MCP-Server im PYTHONPATH ist."
        )


def ask_user_question(question: str, options: list[str]) -> int:
    """Fragt den User bei Mehrdeutigkeit.

    Gibt den Index der gewaehlten Option zurueck.
    In echter Nutzung ueber Claude AskUserQuestion-Tool — hier als Stub
    der in Tests gemockt wird.
    """
    print(f"\n[Reading-List-Import] {question}")
    for i, opt in enumerate(options):
        print(f"  [{i}] {opt}")
    raw = input("Auswahl (Nummer): ").strip()
    try:
        return int(raw)
    except ValueError:
        return 0


def book_resolve_isbn(isbn: str) -> Optional[str]:
    """Delegiert ISBN-Aufloesung an scripts/book_resolve.py.

    Wird in Tests via patch() ersetzt.
    """
    try:
        from book_resolve import resolve_isbn as _br_resolve
        return _br_resolve(isbn)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Format-Erkennung
# ---------------------------------------------------------------------------

def detect_format(file_path: str) -> str:
    """Gibt 'pdf', 'md', oder 'txt' zurueck. Wirft ValueError bei Unbekanntem."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in (".md", ".markdown"):
        return "md"
    if suffix in (".txt", ".text", ""):
        return "txt"
    raise ValueError(f"Unbekanntes Dateiformat: {suffix!r}. Erwartet: .pdf, .md, .txt")


# ---------------------------------------------------------------------------
# Text-Extraktion
# ---------------------------------------------------------------------------

def _extract_pdf(file_path: str) -> str:
    """Extrahiert Text aus PDF via PyPDF2 oder pdfminer als Fallback."""
    try:
        import PyPDF2  # type: ignore
        with open(file_path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages)
    except ImportError:
        pass
    try:
        from pdfminer.high_level import extract_text as _pdfminer_extract  # type: ignore
        return _pdfminer_extract(file_path)
    except ImportError:
        raise ImportError(
            "PDF-Extraktion benoetigt PyPDF2 oder pdfminer.six: "
            "pip install PyPDF2  ODER  pip install pdfminer.six"
        )


def extract_text(file_path: str) -> str:
    """Liest Datei ein und gibt Rohtext zurueck."""
    fmt = detect_format(file_path)
    if fmt == "pdf":
        return _extract_pdf(file_path)
    with open(file_path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# LLM-Parser
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Du bist ein Bibliographie-Parser.
Analysiere die gegebene Referenzliste und extrahiere strukturierte Eintraege.
Gib ein JSON-Array zurueck. Jedes Element hat folgende Felder:
- author (string, Autoren getrennt durch '; ')
- title (string)
- year (string, vierstellig)
- doi (string oder null)
- isbn (string, nur Ziffern, oder null)
- _ambiguous (boolean, true wenn mehrere moegliche Quellen in Frage kommen)
- _candidates (array von {title, doi} falls _ambiguous true)

Antworte NUR mit dem JSON-Array. Kein Prosatext davor oder danach."""


def _strip_json_fence(text: str) -> str:
    """Entfernt ```json ... ``` Markdown-Code-Block falls vorhanden."""
    text = text.strip()
    # Markdown-Code-Block
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


def llm_parse(text: str, client=None) -> list[dict]:
    """Ruft Sonnet auf um Referenzliste zu parsen.

    Args:
        text: Rohtext der Referenzliste
        client: anthropic.Anthropic-Instanz (optional; wird fuer Tests gemockt)

    Returns:
        Liste von Eintraegen als Dicts

    Raises:
        ValueError: Falls LLM kein valides JSON zurueckgibt
    """
    if client is None:
        if not _ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic-SDK benoetigt: pip install anthropic")
        import anthropic
        client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )

    raw = response.content[0].text
    cleaned = _strip_json_fence(raw)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM-Parser hat kein valides JSON zurueckgegeben: {exc}\nRohtext: {raw[:200]}"
        ) from exc

    if not isinstance(parsed, list):
        raise ValueError(f"LLM-Parser: Erwartet JSON-Array, erhalten: {type(parsed)}")

    return parsed


# ---------------------------------------------------------------------------
# DOI-Resolution via Crossref
# ---------------------------------------------------------------------------

_CROSSREF_API = "https://api.crossref.org/works/{doi}"
_DOI_URL_RE = re.compile(r"(?:https?://)?(?:dx\.)?doi\.org/(.+)")


def _normalize_doi(doi: str) -> str:
    """Normalisiert DOI: entfernt doi.org-Praefix, lowercase."""
    doi = doi.strip()
    m = _DOI_URL_RE.match(doi)
    if m:
        doi = m.group(1)
    return doi


def _crossref_message_to_csl(msg: dict) -> str:
    """Konvertiert Crossref-API-Response zu CSL-JSON-String."""
    authors = []
    for a in msg.get("author", []):
        entry: dict = {}
        if "family" in a:
            entry["family"] = a["family"]
        if "given" in a:
            entry["given"] = a["given"]
        if not entry:
            entry = {"literal": a.get("name", "")}
        authors.append(entry)

    issued = msg.get("published") or msg.get("issued") or {}
    date_parts = issued.get("date-parts", [[]])
    year = date_parts[0][0] if date_parts and date_parts[0] else None

    titles = msg.get("title", [])
    title = titles[0] if titles else ""

    csl: dict = {
        "type": msg.get("type", "article-journal"),
        "title": title,
        "author": authors,
        "DOI": msg.get("DOI", ""),
    }
    if year:
        csl["issued"] = {"date-parts": [[year]]}

    container = msg.get("container-title", [])
    if container:
        csl["container-title"] = container[0]

    volume = msg.get("volume")
    if volume:
        csl["volume"] = volume

    return json.dumps(csl, ensure_ascii=False)


def resolve_doi(doi: str) -> Optional[str]:
    """Holt CSL-JSON fuer einen DOI via Crossref.

    Gibt None zurueck falls nicht gefunden oder Netz-Fehler.
    """
    if not doi:
        return None
    if not _REQUESTS_AVAILABLE:
        return None

    doi_clean = _normalize_doi(doi)
    url = _CROSSREF_API.format(doi=doi_clean)

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "academic-research/1.0"})
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    try:
        msg = resp.json().get("message", {})
    except Exception:
        return None

    return _crossref_message_to_csl(msg)


# ---------------------------------------------------------------------------
# ISBN-Resolution
# ---------------------------------------------------------------------------

def resolve_isbn(isbn: str) -> Optional[str]:
    """Delegiert an book_resolve_isbn() (mockar in Tests)."""
    if not isbn:
        return None
    return book_resolve_isbn(isbn)


# ---------------------------------------------------------------------------
# Haupt-Import-Pipeline
# ---------------------------------------------------------------------------

def _make_fallback_csl(entry: dict) -> str:
    """Erstellt minimales CSL-JSON aus einem geparsten Eintrag ohne Resolution."""
    year_raw = entry.get("year", "")
    try:
        year = int(year_raw)
    except (ValueError, TypeError):
        year = None

    authors_raw = entry.get("author", "")
    authors = []
    for part in authors_raw.split(";"):
        part = part.strip()
        if "," in part:
            fam, giv = part.split(",", 1)
            authors.append({"family": fam.strip(), "given": giv.strip()})
        elif part:
            authors.append({"literal": part})

    csl: dict = {
        "type": "article-journal",
        "title": entry.get("title", ""),
        "author": authors,
    }
    if year:
        csl["issued"] = {"date-parts": [[year]]}
    doi = entry.get("doi")
    if doi:
        csl["DOI"] = doi
    isbn = entry.get("isbn")
    if isbn:
        csl["ISBN"] = isbn

    return json.dumps(csl, ensure_ascii=False)


def _generate_paper_id(entry: dict) -> str:
    """Generiert eine stabile paper_id aus DOI/ISBN oder UUID."""
    doi = entry.get("doi")
    isbn = entry.get("isbn")
    if doi:
        clean = re.sub(r"[^a-z0-9]", "-", _normalize_doi(doi).lower())
        return f"doi-{clean}"
    if isbn:
        clean = re.sub(r"[^0-9]", "", str(isbn))
        return f"isbn-{clean}"
    return f"rli-{uuid.uuid4().hex[:12]}"


def _handle_ambiguous(entry: dict) -> Optional[dict]:
    """Fragt User bei ambiguem Eintrag. Gibt gewahlten Kandidaten zurueck oder None."""
    candidates = entry.get("_candidates", [])
    if not candidates:
        return None

    options = [
        f"{c.get('title', '?')} (DOI: {c.get('doi', 'kein DOI')})"
        for c in candidates
    ]
    question = (
        f"Mehrdeutiger Eintrag: \"{entry.get('title', '?')}\" von {entry.get('author', '?')}.\n"
        f"Welche Quelle ist gemeint?"
    )

    idx = ask_user_question(question=question, options=options)
    if 0 <= idx < len(candidates):
        chosen = dict(entry)
        chosen.update(candidates[idx])
        chosen["_ambiguous"] = False
        return chosen
    return None


def import_reading_list(
    file_path: str,
    db_path: str = "vault.db",
    llm_client=None,
) -> dict:
    """Hauptfunktion: importiert eine Referenzliste in den Vault.

    Args:
        file_path: Pfad zu .pdf / .md / .txt
        db_path: Pfad zur Vault-SQLite-Datenbank
        llm_client: anthropic.Anthropic-Instanz (optional; fuer Tests mocken)

    Returns:
        {imported: int, skipped: int, errors: list[str], total: int}
    """
    text = extract_text(file_path)
    entries = llm_parse(text, client=llm_client)

    imported = 0
    skipped = 0
    errors: list[str] = []

    for entry in entries:
        try:
            # Mehrdeutigkeit behandeln
            if entry.get("_ambiguous"):
                resolved_entry = _handle_ambiguous(entry)
                if resolved_entry is None:
                    skipped += 1
                    continue
                entry = resolved_entry

            doi = entry.get("doi") or None
            isbn = entry.get("isbn") or None

            # Resolution versuchen
            csl_json: Optional[str] = None
            if doi:
                csl_json = resolve_doi(doi)
            if not csl_json and isbn:
                csl_json = resolve_isbn(isbn)

            # Fallback: eigenes CSL aus geparsten Daten
            if not csl_json:
                csl_json = _make_fallback_csl(entry)

            paper_id = _generate_paper_id(entry)

            vault_add_paper(
                db_path=db_path,
                paper_id=paper_id,
                csl_json=csl_json,
                doi=doi,
                isbn=isbn,
            )
            imported += 1

        except Exception as exc:
            errors.append(f"{entry.get('title', '?')}: {exc}")
            skipped += 1

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "total": len(entries),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Reading-List-Import: Bibliographie → Vault"
    )
    parser.add_argument("--file", required=True, help="Pfad zur Referenzliste (.pdf/.md/.txt)")
    parser.add_argument("--db", default="vault.db", help="Vault-DB-Pfad (default: vault.db)")
    args = parser.parse_args()

    result = import_reading_list(args.file, db_path=args.db)
    print(
        f"Import abgeschlossen: {result['imported']} importiert, "
        f"{result['skipped']} uebersprungen, "
        f"{result['total']} gesamt."
    )
    if result["errors"]:
        print(f"Fehler ({len(result['errors'])}):")
        for e in result["errors"]:
            print(f"  - {e}")


if __name__ == "__main__":
    _cli()
