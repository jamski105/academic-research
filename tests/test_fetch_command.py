"""
Tests fuer /academic-research:fetch Slash-Command.

Kein LLM-Call. Alle Tests sind reine Unit-Tests:
- Frontmatter-Validierung
- Input-Parser (ISBN-13, ISBN-10, DOI, URL, Titel, isbn:-Prefix)
- Pfad-Sanitizer
- Pickup-Queue-Entry-Generierung
- literature_state-Block-Generierung
- Eval-Datei-Existenz + Schema
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
COMMAND_FILE = REPO_ROOT / "commands/fetch.md"
EVALS_FILE = REPO_ROOT / "evals/fetch/evals.json"


# ---------------------------------------------------------------------------
# Pure-logic helpers (kopiert/spiegelt fetch.md-Workflow fuer testbare Isolation)
# ---------------------------------------------------------------------------

def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter delimited by '---' lines."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    return yaml.safe_load("\n".join(lines[1:end])) or {}


def parse_identifier(raw: str) -> tuple[str, str]:
    """
    Normalisiert einen rohen Input-String in (identifier_type, identifier_value).

    Reihenfolge:
      1. isbn:-Prefix
      2. http(s)://-URL
      3. DOI: ^10.\\d{4,}/
      4. ISBN-13: bereinigt = 97[89]\\d{10}
      5. ISBN-10: bereinigt = \\d{9}[\\dX]
      6. Freitext/Titel (Fallback)
    """
    text = raw.strip()

    # 1. Explizites isbn:-Prefix
    if text.lower().startswith("isbn:"):
        return ("isbn", text[5:].strip())

    # 2. URL
    if text.startswith("http://") or text.startswith("https://"):
        return ("url", text)

    # 3. DOI
    if re.match(r"10\.\d{4,}/", text):
        return ("doi", text)

    # 4+5. ISBN (Bindestriche/Leerzeichen entfernen)
    digits_only = re.sub(r"[- ]", "", text)
    if re.match(r"^97[89]\d{10}$", digits_only):
        return ("isbn", text)
    if re.match(r"^\d{9}[\dX]$", digits_only):
        return ("isbn", text)

    # 6. Freitext
    return ("title", text)


def sanitize_output_path(identifier_value: str) -> Path:
    """
    Gibt den absoluten Ziel-PDF-Pfad fuer einen Identifier zurueck.

    ~/.academic-research/books/<sanitized>.pdf
    Sanitize: Nicht-Alphanumerische Zeichen (ausser ._-) -> '_', max 80 Zeichen.
    """
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", identifier_value)[:80]
    return Path.home() / ".academic-research" / "books" / f"{sanitized}.pdf"


def build_pickup_entry(
    identifier_value: str,
    identifier_type: str,
    bib_pickup_url: str = "",
    reason: str = "Kein Download moeglich",
    source: str = "",
) -> dict:
    """
    Erzeugt einen pickup_queue.json-Eintrag.

    Pflichtfelder: identifier, identifier_type, bib_pickup_url, reason, ts, source.
    """
    return {
        "identifier": identifier_value,
        "identifier_type": identifier_type,
        "bib_pickup_url": bib_pickup_url,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }


def build_literature_state_block(
    title: str,
    year: str,
    identifier_value: str,
    file_path: str,
    source: str,
) -> str:
    """
    Erzeugt den Markdown-Append-Block fuer literature_state.md.
    """
    today = datetime.now(timezone.utc).date().isoformat()
    lines = [
        f"## {title} ({year})",
        "",
        "- **Typ:** book",
        f"- **ISBN/DOI:** {identifier_value}",
        f"- **PDF:** {file_path}",
        f"- **Quelle:** {source}",
        f"- **Hinzugefuegt:** {today}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Test 1 — command file exists
# ---------------------------------------------------------------------------

def test_command_file_exists():
    assert COMMAND_FILE.exists(), f"Missing: {COMMAND_FILE}"


# ---------------------------------------------------------------------------
# Test 2 — frontmatter: Agent(book-fetcher) in allowed-tools
# ---------------------------------------------------------------------------

def test_frontmatter_agent_book_fetcher():
    fm = _parse_frontmatter(COMMAND_FILE)
    allowed = str(fm.get("allowed-tools", ""))
    assert "Agent(book-fetcher)" in allowed, (
        f"'Agent(book-fetcher)' nicht in allowed-tools: {allowed!r}"
    )


# ---------------------------------------------------------------------------
# Test 3 — frontmatter: argument-hint vorhanden
# ---------------------------------------------------------------------------

def test_frontmatter_argument_hint():
    fm = _parse_frontmatter(COMMAND_FILE)
    hint = fm.get("argument-hint", "")
    assert hint, "argument-hint fehlt oder leer"
    # Muss ISBN/DOI/URL/Titel-Formate andeuten
    hint_lower = str(hint).lower()
    assert any(kw in hint_lower for kw in ("isbn", "doi", "url", "titel", "title")), (
        f"argument-hint erwaehnt kein erkennbares Format: {hint!r}"
    )


# ---------------------------------------------------------------------------
# Test 4 — frontmatter: description vorhanden und nicht leer
# ---------------------------------------------------------------------------

def test_frontmatter_description_nonempty():
    fm = _parse_frontmatter(COMMAND_FILE)
    desc = fm.get("description", "")
    assert desc and len(str(desc).strip()) > 10, (
        f"description fehlt oder zu kurz: {desc!r}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Parser: ISBN-13
# ---------------------------------------------------------------------------

def test_parser_isbn13():
    typ, val = parse_identifier("978-3-16-148410-0")
    assert typ == "isbn"
    assert val == "978-3-16-148410-0"


# ---------------------------------------------------------------------------
# Test 6 — Parser: ISBN-10
# ---------------------------------------------------------------------------

def test_parser_isbn10():
    typ, val = parse_identifier("0306406152")
    assert typ == "isbn"
    assert val == "0306406152"


# ---------------------------------------------------------------------------
# Test 7 — Parser: DOI
# ---------------------------------------------------------------------------

def test_parser_doi():
    typ, val = parse_identifier("10.1007/978-3-662-54347-6")
    assert typ == "doi"
    assert val == "10.1007/978-3-662-54347-6"


# ---------------------------------------------------------------------------
# Test 8 — Parser: URL
# ---------------------------------------------------------------------------

def test_parser_url():
    typ, val = parse_identifier("https://link.springer.com/book/10.1007/foo")
    assert typ == "url"
    assert "springer" in val


# ---------------------------------------------------------------------------
# Test 9 — Parser: Freitext/Titel
# ---------------------------------------------------------------------------

def test_parser_title():
    typ, val = parse_identifier("Advanced Machine Learning")
    assert typ == "title"
    assert val == "Advanced Machine Learning"


# ---------------------------------------------------------------------------
# Test 10 — Parser: isbn:-Prefix
# ---------------------------------------------------------------------------

def test_parser_isbn_prefix():
    typ, val = parse_identifier("isbn: 0-306-40615-2")
    assert typ == "isbn"
    assert val == "0-306-40615-2"


# ---------------------------------------------------------------------------
# Test 11 — Pfad-Sanitizer
# ---------------------------------------------------------------------------

def test_sanitize_output_path_isbn():
    result = sanitize_output_path("978-3-16-148410-0")
    assert result.name == "978-3-16-148410-0.pdf"
    assert ".academic-research/books" in str(result)


# ---------------------------------------------------------------------------
# Test 12 — Pickup-Queue-Entry hat Pflichtfelder
# ---------------------------------------------------------------------------

def test_pickup_entry_required_fields():
    entry = build_pickup_entry(
        identifier_value="978-3-16-148410-0",
        identifier_type="isbn",
        bib_pickup_url="https://opac.tum.de",
        reason="Kein OA-PDF",
        source="generic-fetcher",
    )
    for field in ("identifier", "identifier_type", "bib_pickup_url", "reason", "ts", "source"):
        assert field in entry, f"Pflichtfeld '{field}' fehlt im pickup-Eintrag"
    assert entry["identifier"] == "978-3-16-148410-0"
    assert entry["identifier_type"] == "isbn"


# ---------------------------------------------------------------------------
# Test 13 — literature_state-Block hat Pflichtfelder
# ---------------------------------------------------------------------------

def test_literature_state_block_structure():
    block = build_literature_state_block(
        title="Kritik der reinen Vernunft",
        year="1781",
        identifier_value="978-3-16-148410-0",
        file_path="/home/user/.academic-research/books/978-3-16-148410-0.pdf",
        source="oapen-fetcher",
    )
    assert "## Kritik der reinen Vernunft (1781)" in block
    assert "**Typ:** book" in block
    assert "978-3-16-148410-0" in block
    assert "**PDF:**" in block
    assert "**Quelle:** oapen-fetcher" in block
    assert "**Hinzugefuegt:**" in block


# ---------------------------------------------------------------------------
# Test 14 — Eval-Datei existiert
# ---------------------------------------------------------------------------

def test_evals_file_exists():
    assert EVALS_FILE.exists(), f"Missing: {EVALS_FILE}"


# ---------------------------------------------------------------------------
# Test 15 — Eval-Schema: 3 Cases mit id/input/expected
# ---------------------------------------------------------------------------

def test_evals_schema():
    data = json.loads(EVALS_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    assert len(cases) >= 3, f"Erwartet mind. 3 Eval-Cases, gefunden: {len(cases)}"
    for case in cases:
        for field in ("id", "input", "expected"):
            assert field in case, f"Eval-Case fehlt Feld '{field}': {case}"
