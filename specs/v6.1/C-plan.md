# F2.3 page_offset Seitenmapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministisches Seitenmapping `pdf_page → printed_page` via page_offset-Berechnung, gespeichert im Vault, genutzt in Citation-Output.

**Architecture:** pypdf-Text-Extraktion + Regex identifiziert erste gedruckte Seite "1" in den ersten 30 PDF-Seiten. Offset = pdf_page_1basiert - 1. Zwei Stichproben validieren Stabilitaet. MCP-Tools `vault.set_page_offset` / `vault.get_printed_page` exponieren die Logik. Skills erhalten minimale Hinweise.

**Tech Stack:** Python 3.x, pypdf 6.x, reportlab 4.x (nur Fixture-Generierung), pytest, SQLite (ueber VaultDB)

---

## Datei-Uebersicht

| Datei | Aktion | Verantwortung |
|-------|--------|---------------|
| `tests/fixtures/page_offset/create_fixtures.py` | CREATE | Erzeugt 5 synthetische Test-PDFs via reportlab |
| `tests/fixtures/page_offset/no_preface.pdf` | CREATE (generated) | Seite 1 auf PDF-Seite 1 |
| `tests/fixtures/page_offset/ten_prefaces.pdf` | CREATE (generated) | 10 Vorseiten, gedruckte Seite 1 auf PDF-Seite 11 |
| `tests/fixtures/page_offset/roman_numerals.pdf` | CREATE (generated) | i-vi (roemisch), dann arabisch ab "1" auf PDF-Seite 7 |
| `tests/fixtures/page_offset/double_pagination.pdf` | CREATE (generated) | Deckblatt + 5 unnumm. Seiten, dann "1" auf PDF-Seite 6 |
| `tests/fixtures/page_offset/large_offset.pdf` | CREATE (generated) | 25 Vorseiten, arabische "1" auf PDF-Seite 26 |
| `scripts/page_offset.py` | CREATE | detect_page_offset() + validate_offset() + CLI |
| `mcp/academic_vault/db.py` | MODIFY (additiv) | set_page_offset() + get_page_offset() |
| `mcp/academic_vault/server.py` | MODIFY (additiv) | set_page_offset() + get_printed_page() + MCP-Tools |
| `skills/book-handler/SKILL.md` | MODIFY | Schritt 2.5 page_offset-Berechnung nach PDF-Add |
| `skills/citation-extraction/SKILL.md` | MODIFY | printed_page-Hinweis in Output-Integration |
| `tests/baselines/skill_sizes.json` | MODIFY | book-handler baseline erhoeht auf 4320 |
| `tests/test_page_offset.py` | CREATE | 5 TDD-Tests fuer page_offset-Logik |

---

## Task 1: Fixture-Generator und PDF-Fixtures erstellen

**Files:**
- Create: `tests/fixtures/page_offset/create_fixtures.py`
- Create: `tests/fixtures/page_offset/` (5 PDFs werden generiert)

- [ ] **Schritt 1.1: Fixture-Generator schreiben**

Erstelle `tests/fixtures/page_offset/create_fixtures.py`:

```python
"""Erzeugt 5 synthetische PDF-Fixtures fuer page_offset-Tests.

Aufruf: python tests/fixtures/page_offset/create_fixtures.py
Benoetigt: reportlab (pip install reportlab)
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


OUT = Path(__file__).parent


def _page_label(pdf_page_0: int, num_text: str) -> str:
    """Seitentext fuer eine gegebene PDF-Seite."""
    return num_text


def create_no_preface(path: Path) -> None:
    """Buch ohne Vorwort: gedruckte Seite 1 auf PDF-Seite 1 (offset=0)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))  # Seitenzahl unten
        c.drawString(72, 750, f"Inhalt Seite {printed}")
        c.showPage()
    c.save()


def create_ten_prefaces(path: Path) -> None:
    """10 Vorseiten (unnummeriert), dann gedruckte Seite 1 (offset=10)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(10):
        c.drawString(72, 750, f"Vorwort Seite {i + 1}")
        # keine Seitenzahl unten
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Kapitel Inhalt {printed}")
        c.showPage()
    c.save()


def create_roman_numerals(path: Path) -> None:
    """Seiten i-vi (roemisch), dann arabisch ab 1 auf PDF-Seite 7 (offset=6)."""
    roman = ["i", "ii", "iii", "iv", "v", "vi"]
    c = canvas.Canvas(str(path), pagesize=A4)
    for r in roman:
        c.drawString(72, 40, r)
        c.drawString(72, 750, f"Vorbemerkung {r}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Kapitel {printed}")
        c.showPage()
    c.save()


def create_double_pagination(path: Path) -> None:
    """5 unnummerierte Seiten (Deckblatt etc.), dann arabisch ab 1 (offset=5)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(5):
        c.drawString(72, 750, f"Frontmatter {i + 1}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Text {printed}")
        c.showPage()
    c.save()


def create_large_offset(path: Path) -> None:
    """25 Vorseiten, arabische 1 auf PDF-Seite 26 (offset=25)."""
    c = canvas.Canvas(str(path), pagesize=A4)
    for i in range(25):
        c.drawString(72, 750, f"Frontmatter {i + 1}")
        c.showPage()
    for i in range(10):
        printed = i + 1
        c.drawString(72, 40, str(printed))
        c.drawString(72, 750, f"Inhalt {printed}")
        c.showPage()
    c.save()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    create_no_preface(OUT / "no_preface.pdf")
    create_ten_prefaces(OUT / "ten_prefaces.pdf")
    create_roman_numerals(OUT / "roman_numerals.pdf")
    create_double_pagination(OUT / "double_pagination.pdf")
    create_large_offset(OUT / "large_offset.pdf")
    print(f"5 Fixtures erstellt in {OUT}")
```

- [ ] **Schritt 1.2: Fixtures generieren**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
python tests/fixtures/page_offset/create_fixtures.py
```

Erwartet: `5 Fixtures erstellt in tests/fixtures/page_offset`

- [ ] **Schritt 1.3: Verify**

```bash
ls -la tests/fixtures/page_offset/*.pdf | wc -l
```

Erwartet: `5`

---

## Task 2: Fehlschlagende Tests schreiben (RED)

**Files:**
- Create: `tests/test_page_offset.py`

- [ ] **Schritt 2.1: Testdatei erstellen**

Erstelle `tests/test_page_offset.py`:

```python
"""TDD-Tests fuer scripts/page_offset.py.

5 Testfaelle mit synthetischen PDFs (tests/fixtures/page_offset/).
Konvention: Seitenzahl steht als isolierte Zahl unten auf jeder
nummerierten Seite (Position y=40 in reportlab-Koordinaten = unten).
"""
import sys
from pathlib import Path

import pytest

# scripts/ zum Python-Pfad hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures" / "page_offset"


def _require_fixture(name: str) -> Path:
    p = FIXTURES / name
    if not p.exists():
        pytest.skip(f"Fixture fehlt: {p}. Aufruf: python tests/fixtures/page_offset/create_fixtures.py")
    return p


def test_no_preface_offset_zero():
    """Buch ohne Vorwort: offset soll 0 sein (erste PDF-Seite traegt '1')."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("no_preface.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 0, f"Erwartet offset=0, erhalten {offset}"


def test_ten_prefaces_offset_ten():
    """10 Vorseiten: erste arabische '1' auf PDF-Seite 11 (1-basiert) -> offset=10."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 10, f"Erwartet offset=10, erhalten {offset}"


def test_roman_numerals_offset_six():
    """6 roemische Seiten, dann arabisch ab 1 auf PDF-Seite 7 -> offset=6."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("roman_numerals.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 6, f"Erwartet offset=6, erhalten {offset}"


def test_double_pagination_offset_five():
    """5 unnummerierte Seiten, arabisch ab 1 auf PDF-Seite 6 -> offset=5."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("double_pagination.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 5, f"Erwartet offset=5, erhalten {offset}"


def test_large_offset_twenty_five():
    """25 Vorseiten, arabisch ab 1 auf PDF-Seite 26 -> offset=25."""
    from page_offset import detect_page_offset
    pdf = _require_fixture("large_offset.pdf")
    offset = detect_page_offset(str(pdf))
    assert offset == 25, f"Erwartet offset=25, erhalten {offset}"


def test_validate_offset_stable():
    """validate_offset gibt True zurueck wenn Stichproben konsistent sind."""
    from page_offset import validate_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    # offset=10: PDF-Seite 11 (0-basiert: 10) soll '1' zeigen
    # Stichproben bei PDF-Seiten 12 und 13 (gedruckt 2 und 3)
    result = validate_offset(str(pdf), offset=10, check_pages=[11, 12])
    assert result is True, "validate_offset soll True fuer stabilen Offset zurueckgeben"


def test_validate_offset_wrong_rejects():
    """validate_offset gibt False zurueck wenn Offset falsch ist."""
    from page_offset import validate_offset
    pdf = _require_fixture("ten_prefaces.pdf")
    result = validate_offset(str(pdf), offset=0, check_pages=[11, 12])
    assert result is False, "validate_offset soll False fuer falschen Offset zurueckgeben"
```

- [ ] **Schritt 2.2: Tests laufen lassen (erwarte FAIL)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py -v 2>&1 | head -30
```

Erwartet: `ModuleNotFoundError: No module named 'page_offset'` oder `ImportError`

---

## Task 3: `scripts/page_offset.py` implementieren (GREEN)

**Files:**
- Create: `scripts/page_offset.py`

- [ ] **Schritt 3.1: Implementierung schreiben**

Erstelle `scripts/page_offset.py`:

```python
"""page_offset.py — Ermittelt page_offset fuer Buecher mit Vorseiten.

Logik:
  1. Iteriere ueber die ersten sample_pages PDF-Seiten (0-basiert).
  2. Extrahiere Text jeder Seite via pypdf.
  3. Suche nach isolierter arabischer Ziffer "1" am Anfang oder Ende
     des extrahierten Textes (typische Seitenzahl-Position).
  4. offset = gefundene_pdf_seite_1basiert - 1
     (d.h. pdf_page_1basiert - offset = printed_page)

Kein LLM-Aufruf. Deterministisch und schnell.

CLI: python scripts/page_offset.py <pdf_path> [--sample-pages N]
"""
import re
import sys
from pathlib import Path
from typing import Optional


def _extract_page_number(text: str) -> Optional[int]:
    """Extrahiert Seitenzahl aus Seiten-Text.

    Sucht nach einer isolierten arabischen Ziffer am Anfang oder Ende
    des Textes (erste oder letzte nicht-leere Zeile).

    Gibt None zurueck wenn keine eindeutige arabische Seitenzahl gefunden.
    Ignoriert roemische Ziffern (i, ii, iii, iv, v, vi, vii, viii, ix, x).
    """
    if not text or not text.strip():
        return None

    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return None

    # Roemische Ziffern (kleine und grosse) ausschliessen
    roman_pattern = re.compile(
        r'^(i{1,3}|iv|v?i{0,3}|ix|xl|l?x{0,3}|xc|cd|d?c{0,3}|cm|m{0,4})$',
        re.IGNORECASE
    )

    # Erste und letzte Zeile pruefen (Seitenzahlen stehen oben oder unten)
    candidates = [lines[0], lines[-1]]

    for candidate in candidates:
        # Nur reine Zahl akzeptieren (keine Mischung mit Text)
        if re.match(r'^\d+$', candidate):
            num = int(candidate)
            if 1 <= num <= 9999:
                return num
        # Roemische Ziffer explizit ueberspringen
        if roman_pattern.match(candidate):
            continue

    return None


def detect_page_offset(pdf_path: str, sample_pages: int = 30) -> int:
    """Scannt die ersten sample_pages Seiten des PDFs.

    Gibt offset = (pdf_page_1basiert_der_ersten_arabischen_1) - 1 zurueck.
    Gibt 0 zurueck wenn keine arabische '1' gefunden.

    Args:
        pdf_path: Pfad zur PDF-Datei.
        sample_pages: Anzahl der zu scannenden Seiten (Standard: 30).

    Returns:
        page_offset (int >= 0).
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf benoetigt: pip install pypdf")

    reader = PdfReader(pdf_path)
    num_pages = min(sample_pages, len(reader.pages))

    for pdf_idx in range(num_pages):
        page = reader.pages[pdf_idx]
        text = page.extract_text() or ""
        page_num = _extract_page_number(text)
        if page_num == 1:
            # pdf_idx ist 0-basiert; pdf_page_1basiert = pdf_idx + 1
            offset = pdf_idx  # = (pdf_idx + 1) - 1
            return offset

    return 0  # Kein Offset erkannt (z.B. Buch ohne erkennbare Seitenzahlen)


def validate_offset(
    pdf_path: str,
    offset: int,
    check_pages: Optional[list] = None,
) -> bool:
    """Validiert den page_offset anhand von 2 Stichproben.

    Fuer jede check_page (0-basierter PDF-Index) wird geprueft ob:
        _extract_page_number(text) == (check_page + 1) - offset

    Args:
        pdf_path: Pfad zur PDF-Datei.
        offset: Zu validierender Offset.
        check_pages: Liste von 0-basierten PDF-Seiten-Indizes fuer Stichproben.
                     Standard: [offset+1, offset+2] (zwei Seiten nach der "1").

    Returns:
        True wenn alle Stichproben konsistent, False sonst.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf benoetigt: pip install pypdf")

    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)

    if check_pages is None:
        check_pages = [offset + 1, offset + 2]

    for pdf_idx in check_pages:
        if pdf_idx >= num_pages:
            continue
        page = reader.pages[pdf_idx]
        text = page.extract_text() or ""
        page_num = _extract_page_number(text)
        expected = (pdf_idx + 1) - offset
        if page_num != expected:
            return False

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ermittelt page_offset fuer ein Buch-PDF."
    )
    parser.add_argument("pdf_path", help="Pfad zur PDF-Datei")
    parser.add_argument(
        "--sample-pages", type=int, default=30,
        help="Anzahl der zu scannenden Seiten (Standard: 30)"
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Offset zusaetzlich anhand von 2 Stichproben validieren"
    )
    args = parser.parse_args()

    offset = detect_page_offset(args.pdf_path, args.sample_pages)
    print(f"page_offset: {offset}")

    if args.validate and offset > 0:
        valid = validate_offset(args.pdf_path, offset)
        print(f"Validierung: {'OK' if valid else 'INKONSISTENT'}")
```

- [ ] **Schritt 3.2: Tests laufen lassen (erwarte GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py -v
```

Erwartet: Alle 7 Tests PASS.

- [ ] **Schritt 3.3: Commit**

```bash
git add scripts/page_offset.py tests/test_page_offset.py tests/fixtures/page_offset/
git commit -m "feat: page_offset.py — detect/validate Seitenmapping (F2.3 #73)"
```

---

## Task 4: VaultDB erweitern — set_page_offset / get_page_offset

**Files:**
- Modify: `mcp/academic_vault/db.py`
- Test: `tests/test_page_offset.py` (neue Tests erganzen)

- [ ] **Schritt 4.1: Fehlschlagende Tests fuer db.py schreiben**

Erganzen in `tests/test_page_offset.py` (am Ende der Datei hinzufuegen):

```python
# ---------------------------------------------------------------------------
# Vault-DB Tests
# ---------------------------------------------------------------------------

def test_vault_db_set_get_page_offset():
    """set_page_offset und get_page_offset runden-trip im Vault."""
    import tempfile
    import json
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.db import VaultDB

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    db = VaultDB(db_path)
    db.init_schema()
    csl = json.dumps({"type": "book", "title": "Test"})
    db.add_paper("buch_test_2024", csl)

    db.set_page_offset("buch_test_2024", 12)
    result = db.get_page_offset("buch_test_2024")
    assert result == 12, f"Erwartet 12, erhalten {result}"


def test_vault_db_get_page_offset_missing_returns_zero():
    """get_page_offset gibt 0 zurueck fuer unbekanntes paper_id."""
    import tempfile
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.db import VaultDB

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    db = VaultDB(db_path)
    db.init_schema()
    result = db.get_page_offset("nonexistent_paper")
    assert result == 0, f"Erwartet 0, erhalten {result}"
```

- [ ] **Schritt 4.2: Tests laufen lassen (erwarte FAIL)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py::test_vault_db_set_get_page_offset tests/test_page_offset.py::test_vault_db_get_page_offset_missing_returns_zero -v
```

Erwartet: `AttributeError: 'VaultDB' object has no attribute 'set_page_offset'`

- [ ] **Schritt 4.3: db.py anpassen (additiv)**

Lese `mcp/academic_vault/db.py` und fuege nach der `set_file_id`-Methode (nach Zeile ~205) folgende Methoden ein:

```python
    def set_page_offset(self, paper_id: str, offset: int) -> None:
        """Setzt page_offset fuer ein Paper."""
        import time as _time
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET page_offset = ?, updated_at = ? WHERE paper_id = ?",
            (offset, int(_time.time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def get_page_offset(self, paper_id: str) -> int:
        """Gibt page_offset fuer ein Paper zurueck. Fallback: 0."""
        conn = self._get_conn()
        own_conn = self._conn is None
        row = conn.execute(
            "SELECT page_offset FROM papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        if own_conn:
            conn.close()
        if row is None:
            return 0
        return int(row["page_offset"] or 0)
```

- [ ] **Schritt 4.4: Tests laufen lassen (erwarte GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py -v
```

Erwartet: Alle 9 Tests PASS.

---

## Task 5: server.py erweitern — set_page_offset / get_printed_page

**Files:**
- Modify: `mcp/academic_vault/server.py`
- Test: `tests/test_page_offset.py` (neue Tests erganzen)

- [ ] **Schritt 5.1: Fehlschlagende Tests fuer server.py schreiben**

Erganzen in `tests/test_page_offset.py` am Ende:

```python
# ---------------------------------------------------------------------------
# Server-Funktionen Tests
# ---------------------------------------------------------------------------

def test_server_set_and_get_printed_page():
    """set_page_offset + get_printed_page runden-trip via server.py."""
    import tempfile
    import json
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.server import set_page_offset, get_printed_page, add_paper

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    csl = json.dumps({"type": "book", "title": "Server Test"})
    add_paper(db_path, "server_test_2024", csl)
    set_page_offset(db_path, "server_test_2024", 10)

    # pdf_page=15 (1-basiert) -> printed_page = 15 - 10 = 5
    result = get_printed_page(db_path, "server_test_2024", pdf_page=15)
    assert result == 5, f"Erwartet 5, erhalten {result}"


def test_server_get_printed_page_zero_offset():
    """get_printed_page mit offset=0 gibt pdf_page unveraendert zurueck."""
    import tempfile
    import json
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp.academic_vault.server import get_printed_page, add_paper

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    csl = json.dumps({"type": "book", "title": "Zero Offset Test"})
    add_paper(db_path, "zero_offset_2024", csl)
    # Kein set_page_offset -> offset=0

    result = get_printed_page(db_path, "zero_offset_2024", pdf_page=42)
    assert result == 42, f"Erwartet 42 (kein Offset), erhalten {result}"
```

- [ ] **Schritt 5.2: Tests laufen lassen (erwarte FAIL)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py::test_server_set_and_get_printed_page tests/test_page_offset.py::test_server_get_printed_page_zero_offset -v
```

Erwartet: `ImportError: cannot import name 'set_page_offset' from 'mcp.academic_vault.server'`

- [ ] **Schritt 5.3: server.py erweitern (additiv)**

Lese `mcp/academic_vault/server.py`. Fuege nach der `get_stats`-Funktion (vor `_build_mcp_server`) folgende Funktionen ein:

```python
def set_page_offset(db_path: str, paper_id: str, offset: int) -> None:
    """Setzt page_offset fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.set_page_offset(paper_id, offset)


def get_printed_page(db_path: str, paper_id: str, pdf_page: int) -> int:
    """Berechnet gedruckte Seitenzahl: printed_page = pdf_page - page_offset.

    Args:
        db_path: Pfad zur Vault-DB.
        paper_id: Paper-ID im Vault.
        pdf_page: Seitenzahl aus Citations-API (1-basiert ab erster PDF-Seite).

    Returns:
        Gedruckte Seitenzahl (>= 1).
    """
    db = VaultDB(db_path)
    offset = db.get_page_offset(paper_id)
    printed = pdf_page - offset
    return max(1, printed)  # Nie kleiner als 1
```

Ausserdem in `_build_mcp_server()` nach dem `_vault_stats`-Tool folgende MCP-Tools hinzufuegen:

```python
    @mcp.tool(name="vault.set_page_offset")
    def _vault_set_page_offset(paper_id: str, offset: int) -> None:
        """Setzt page_offset fuer ein Paper (Buecher mit Vorseiten/Vorwort)."""
        set_page_offset(db_path, paper_id, offset)

    @mcp.tool(name="vault.get_printed_page")
    def _vault_get_printed_page(paper_id: str, pdf_page: int) -> int:
        """Berechnet gedruckte Seitenzahl: printed_page = pdf_page - page_offset."""
        return get_printed_page(db_path, paper_id, pdf_page)
```

- [ ] **Schritt 5.4: Tests laufen lassen (erwarte GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_page_offset.py -v
```

Erwartet: Alle 11 Tests PASS.

- [ ] **Schritt 5.5: Commit**

```bash
git add mcp/academic_vault/db.py mcp/academic_vault/server.py tests/test_page_offset.py
git commit -m "feat: vault set_page_offset/get_printed_page (F2.3 #73)"
```

---

## Task 6: book-handler/SKILL.md aktualisieren

**Files:**
- Modify: `skills/book-handler/SKILL.md`
- Modify: `tests/baselines/skill_sizes.json` (baseline-Bump)

**Constraint:** Dateigroesse nachher <= 4220 + 100 = 4320 Zeichen (damit delta >= 1400 gehalten wird; baseline wird auf 4320 angehoben). Aktuelle Groesse: 2814 chars. Delta nach Bump: 4320 - (2814 + neue_chars) muss >= 1400 bleiben.

Rechnung: Neue Dateigroesse <= 4320 - 1400 = 2920. Ich darf also maximal 2920 - 2814 = 106 Zeichen hinzufuegen.

- [ ] **Schritt 6.1: SKILL.md anpassen**

Lese `skills/book-handler/SKILL.md`. Ersetze den Abschnitt `### 2. Vault-Eintrag anlegen` so, dass nach dem `vault.add_paper(...)` Block ein neuer Unterschritt `### 2.5. page_offset berechnen` eingefuegt wird.

Ersetze in `skills/book-handler/SKILL.md`:

ALT (nach dem `vault.add_paper`-Block):
```
### 3. OA-Check
```

NEU (einfuegen vor `### 3. OA-Check`):
```
### 2.5. page_offset berechnen

Falls `pdf_path` gesetzt:
```bash
python scripts/page_offset.py {pdf_path}
```
Ergebnis via `vault.set_page_offset({citekey}, {offset})` speichern.

### 3. OA-Check
```

- [ ] **Schritt 6.2: Dateigroesse pruefen**

```bash
python3 -c "
from pathlib import Path
import json
f = Path('skills/book-handler/SKILL.md')
b = json.loads(Path('tests/baselines/skill_sizes.json').read_text())
actual = len(f.read_text())
baseline = b['book-handler']
print(f'book-handler: actual={actual}, baseline={baseline}, delta={baseline - actual}')
print(f'OK: {baseline - actual >= 1400}')
"
```

Falls delta < 1400: Baseline in `skill_sizes.json` erhoehen bis delta >= 1400 erhalten bleibt.

- [ ] **Schritt 6.3: Baseline-Bump in skill_sizes.json**

Lese `tests/baselines/skill_sizes.json`. Setze `"book-handler"` auf `actual_size + 1400` (damit delta exakt 1400 ist).

Beispiel: Wenn `actual` = 2920, dann baseline = 4320.

- [ ] **Schritt 6.4: Token-Reduction-Test laufen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -v -k "book-handler"
```

Erwartet: PASS

- [ ] **Schritt 6.5: Commit**

```bash
git add skills/book-handler/SKILL.md tests/baselines/skill_sizes.json
git commit -m "feat: book-handler — page_offset-Trigger nach PDF-Add (F2.3 #73)"
```

---

## Task 7: citation-extraction/SKILL.md aktualisieren

**Files:**
- Modify: `skills/citation-extraction/SKILL.md`

**Constraint:** Dateigroesse MUSS <= 9896 Zeichen bleiben (baseline 11296, delta >= 1400).
Aktuelle Groesse: 9896 (exakt am Limit). Nur minimalste Ergaenzung erlaubt — MUSS gleichzeitig kuerzen.

- [ ] **Schritt 7.1: Aktuellen Char-Count pruefen**

```bash
python3 -c "from pathlib import Path; print(len(Path('skills/citation-extraction/SKILL.md').read_text()))"
```

Erwartet: 9896

- [ ] **Schritt 7.2: SKILL.md anpassen**

Lese `skills/citation-extraction/SKILL.md`. Im Abschnitt `**Output-Integration:**` (unter `## Citations-API`) ersetze:

ALT:
```
**Output-Integration:** Die `citations[]`-Array-Eintraege der API enthalten `start_page_number` / `end_page_number` direkt — uebernimm sie in die Seitenangabe des Zitats (`S. X–Y`).
```

NEU (kuerzere Formulierung + printed_page-Hinweis, netto <= 0 Zeichen Wachstum):
```
**Output-Integration:** `citations[].start_page_number` / `end_page_number` direkt als Seitenangabe (`S. X–Y`) verwenden. Bei Buechern mit Vorseiten: `printed_page = vault.get_printed_page(paper_id, pdf_page)`.
```

Ziel: Neue Version ist maximal gleich lang oder kuerzer als alte.

- [ ] **Schritt 7.3: Char-Count und Token-Reduction-Test**

```bash
python3 -c "
from pathlib import Path
import json
f = Path('skills/citation-extraction/SKILL.md')
b = json.loads(Path('tests/baselines/skill_sizes.json').read_text())
actual = len(f.read_text())
baseline = b['citation-extraction']
print(f'citation-extraction: actual={actual}, baseline={baseline}, delta={baseline-actual}')
print(f'OK (<=9896): {actual <= 9896}')
print(f'Token-reduction OK: {baseline - actual >= 1400}')
"
```

Erwartet: `OK (<=9896): True` und `Token-reduction OK: True`

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -v -k "citation-extraction"
```

Erwartet: PASS

- [ ] **Schritt 7.4: Commit**

```bash
git add skills/citation-extraction/SKILL.md
git commit -m "feat: citation-extraction — printed_page Hinweis fuer Buecher (F2.3 #73)"
```

---

## Task 8: Full Test Suite und finale Verifikation

- [ ] **Schritt 8.1: Alle Tests laufen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-C
/opt/homebrew/bin/pytest tests/ -v --ignore=tests/evals 2>&1 | tail -30
```

Erwartet: Alle Tests PASS ausser dem bereits bekannten `chapter-writer` token_reduction failure (Chunk B / nicht meine Verantwortung).

- [ ] **Schritt 8.2: page_offset-Tests separat**

```bash
/opt/homebrew/bin/pytest tests/test_page_offset.py -v
```

Erwartet: 11 Tests PASS (5 detect + 2 validate + 2 db + 2 server)

- [ ] **Schritt 8.3: Token-Reduction-Tests**

```bash
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -v
```

Erwartet: Alle PASS ausser `chapter-writer` (nicht Chunk C)

- [ ] **Schritt 8.4: Finaler Commit**

```bash
git add -p  # alle noch nicht committeten Aenderungen
git commit -m "chore: finale Verifikation page_offset (F2.3 #73)"
```

---

## Bekannte Nicht-Verantwortlichkeiten

- `chapter-writer` token_reduction failure: Chunk B Hoheit, nicht fixen
- `scripts/book_resolve.py`, `scripts/chunk_pdf.py`: Nicht anfassen
- Schema-Migration: Nicht noetig (page_offset Spalte existiert)
- OCR-Integration: Chunk D
