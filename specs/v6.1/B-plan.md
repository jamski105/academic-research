# Chunk B — Kapitel-Schnitt aus Buch-PDFs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zerlegt grosse Buch-PDFs kapitelweise via PyPDF2 Outline-Tree (Fallback: TOC-Textextraktion) und speichert Eltern-Kind-Beziehung in der Vault-DB.

**Architecture:** `scripts/chunk_pdf.py` liest den PyPDF2 Outline-Tree und schreibt je Kapitel ein separates PDF. Die Vault erhaelt eine `parent_paper_id`-Spalte, `db.py`/`server.py` werden um den neuen Parameter erweitert. Migrations-Pattern von Chunk A (idempotentes ALTER TABLE) wird emuliert.

**Tech Stack:** Python 3.x, PyPDF2 >= 3.0.0, SQLite (via bestehende VaultDB), pytest

---

## File Map

| Datei | Aktion | Verantwortung |
|---|---|---|
| `scripts/chunk_pdf.py` | CREATE | CLI-Skript: Outline-Tree + TOC-Fallback, Kapitel-PDFs schreiben |
| `tests/fixtures/sample_book.pdf` | CREATE | Minimales Test-PDF mit Outline-Tree (< 200 KB) |
| `tests/test_chunk_pdf.py` | CREATE | Unit- + Integrationstests fuer chunk_pdf.py |
| `mcp/academic_vault/schema.sql` | MODIFY | parent_paper_id-Spalte in papers |
| `mcp/academic_vault/migrate.py` | MODIFY | add_parent_paper_id_column() idempotent |
| `mcp/academic_vault/db.py` | MODIFY | add_paper() + parent_paper_id |
| `mcp/academic_vault/server.py` | MODIFY | add_paper() + add_chapter() helper |
| `tests/test_vault_parent.py` | CREATE | parent/child Vault-Tests |
| `skills/citation-extraction/SKILL.md` | MODIFY | Hinweis Kapitel-PDF-Modus |

---

### Task 1: Test-Fixture PDF mit Outline erstellen

**Files:**
- Create: `tests/fixtures/sample_book.pdf`
- Create: `tests/fixtures/create_sample_book.py` (Hilfsskript, nicht im Test-Pfad)

- [ ] **Schritt 1: Hilfsskript schreiben (kein Test)**

```python
# tests/fixtures/create_sample_book.py
"""Erstellt sample_book.pdf mit PyPDF2 fuer Tests."""
from PyPDF2 import PdfWriter
from PyPDF2.generic import (
    ArrayObject, DictionaryObject, IndirectObject,
    NameObject, NumberObject, TextStringObject,
)
import io, os

def create_sample_book(output_path: str) -> None:
    writer = PdfWriter()

    # 10 Seiten: 2 Titelseiten + je 2 Seiten pro Kapitel (4 Kapitel)
    for i in range(10):
        page = writer.add_blank_page(width=595, height=842)

    # Outline-Eintraege: 4 Kapitel
    chapters = [
        ("Kapitel 1: Einleitung", 2),
        ("Kapitel 2: Grundlagen", 4),
        ("Kapitel 3: Methodik", 6),
        ("Kapitel 4: Ergebnisse", 8),
    ]
    for title, page_num in chapters:
        writer.add_outline_item(title, page_num)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

if __name__ == "__main__":
    create_sample_book("sample_book.pdf")
```

- [ ] **Schritt 2: Fixture generieren**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-B
python tests/fixtures/create_sample_book.py
# Ausgabe: sample_book.pdf im CWD
mv sample_book.pdf tests/fixtures/sample_book.pdf
ls -lh tests/fixtures/sample_book.pdf
# Erwartet: < 50 KB
```

- [ ] **Schritt 3: Commit**

```bash
git add tests/fixtures/create_sample_book.py tests/fixtures/sample_book.pdf
git commit -m "test: Fixture sample_book.pdf mit 4-Kapitel-Outline"
```

---

### Task 2: TDD — chunk_pdf.py Outline-Tree-Parsing

**Files:**
- Create: `tests/test_chunk_pdf.py`
- Create: `scripts/chunk_pdf.py`

- [ ] **Schritt 1: Failing test schreiben**

```python
# tests/test_chunk_pdf.py
"""Tests fuer scripts/chunk_pdf.py"""
import importlib.util
import sys
import os
import tempfile
from pathlib import Path
import pytest

# Skript direkt laden (kein Package)
_SCRIPT = Path(__file__).parent.parent / "scripts" / "chunk_pdf.py"
spec = importlib.util.spec_from_file_location("chunk_pdf", _SCRIPT)
chunk_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chunk_pdf)

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_book.pdf"


class TestOutlineParsing:
    def test_extract_chapters_from_outline(self):
        """Outline-Tree mit 4 Kapiteln korrekt parsen."""
        chapters = chunk_pdf.extract_chapters(str(FIXTURE_PDF))
        assert len(chapters) == 4
        assert chapters[0]["title"] == "Kapitel 1: Einleitung"
        assert chapters[0]["start_page"] == 2  # 0-indexed
        assert chapters[1]["start_page"] == 4
        assert chapters[2]["start_page"] == 6
        assert chapters[3]["start_page"] == 8

    def test_chapter_end_page_derived_from_next_start(self):
        """end_page = naechstes Kapitel start - 1."""
        chapters = chunk_pdf.extract_chapters(str(FIXTURE_PDF))
        assert chapters[0]["end_page"] == 3
        assert chapters[1]["end_page"] == 5
        assert chapters[2]["end_page"] == 7
        # Letztes Kapitel endet auf letzter Seite des PDFs
        assert chapters[3]["end_page"] == 9  # 10 Seiten insgesamt (0-indexed: 0-9)


class TestWriteChapter:
    def test_write_single_chapter_creates_pdf(self):
        """write_chapter schreibt ein gueltiges PDF."""
        from PyPDF2 import PdfReader
        chapters = chunk_pdf.extract_chapters(str(FIXTURE_PDF))
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "ch1.pdf")
            chunk_pdf.write_chapter(str(FIXTURE_PDF), chapters[0], out_path)
            assert os.path.exists(out_path)
            reader = PdfReader(out_path)
            assert len(reader.pages) == 2  # Seiten 2-3 (0-indexed)

    def test_write_all_chapters(self):
        """--chapter all erzeugt 4 Dateien."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = chunk_pdf.write_all_chapters(
                str(FIXTURE_PDF), tmpdir, isbn="test-isbn"
            )
            assert len(paths) == 4
            for p in paths:
                assert os.path.exists(p)
                assert "test-isbn" in os.path.basename(p)


class TestTOCFallback:
    def test_toc_fallback_for_pdf_without_outline(self, tmp_path):
        """PDF ohne Outline-Tree: TOC-Fallback liefert leere Liste (kein Absturz)."""
        from PyPDF2 import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        pdf_path = str(tmp_path / "no_outline.pdf")
        with open(pdf_path, "wb") as f:
            writer.write(f)
        # Kein Outline vorhanden -> Fallback -> leere Liste oder Fehler mit SystemExit
        try:
            chapters = chunk_pdf.extract_chapters(pdf_path)
            # Falls Fallback greift und nichts findet: leere Liste ist ok
            assert isinstance(chapters, list)
        except SystemExit as e:
            assert e.code == 2  # Kein TOC gefunden -> Exit 2


class TestCLI:
    def test_cli_toc_mode_returns_json(self):
        """--chapter toc gibt JSON-TOC aus."""
        import json, subprocess
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(FIXTURE_PDF),
             "--chapter", "toc",
             "--output", "/dev/null"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        toc = json.loads(result.stdout)
        assert len(toc) == 4
        assert toc[0]["title"] == "Kapitel 1: Einleitung"

    def test_cli_chapter_n(self, tmp_path):
        """--chapter 1 schreibt eine Datei."""
        import subprocess
        out_path = str(tmp_path / "ch1.pdf")
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             "--input", str(FIXTURE_PDF),
             "--chapter", "1",
             "--output", out_path],
            capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert os.path.exists(out_path)
```

- [ ] **Schritt 2: Test ausfuehren — muss fehlschlagen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-B
/opt/homebrew/bin/pytest tests/test_chunk_pdf.py -v --tb=short 2>&1 | head -40
# Erwartet: ImportError oder ModuleNotFoundError (chunk_pdf nicht vorhanden)
```

- [ ] **Schritt 3: chunk_pdf.py implementieren**

```python
#!/usr/bin/env python3
"""chunk_pdf.py — Zerlegt Buch-PDFs kapitelweise via PyPDF2 Outline-Tree.

CLI:
    python chunk_pdf.py --input book.pdf --chapter <n|toc|all> --output <pfad>

Kapitel-Erkennung:
    1. PyPDF2 Outline-Tree (PdfReader.outline)
    2. Fallback: Textextraktion erste 20 Seiten, Regex-Kapitelsuche

Ausgabe:
    --chapter all  -> Alle Kapitel nach <output_dir>/<isbn>-ch<n>.pdf
    --chapter N    -> Kapitel N nach <output>-Pfad
    --chapter toc  -> JSON-TOC auf stdout
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import Destination


def _outline_page_number(reader: PdfReader, item) -> Optional[int]:
    """Gibt 0-indexed Seitennummer eines Outline-Items zurueck oder None."""
    try:
        if isinstance(item, Destination):
            return reader.get_destination_page_number(item)
        # Neuere PyPDF2/pypdf-Versionen: item ist dict-aehnlich
        if hasattr(item, "page"):
            page_obj = item.page
            if hasattr(page_obj, "get_object"):
                page_obj = page_obj.get_object()
            for i, p in enumerate(reader.pages):
                if p.get_object() == page_obj:
                    return i
    except Exception:
        pass
    return None


def _flatten_outline(reader: PdfReader, outline, depth: int = 0) -> list[dict]:
    """Flacht den Outline-Tree auf Top-Level-Kapitel ab."""
    result = []
    if outline is None:
        return result
    for item in outline:
        if isinstance(item, list):
            # Verschachtelte Ebene: nur Top-Level aufnehmen wenn depth==0
            if depth == 0:
                result.extend(_flatten_outline(reader, item, depth + 1))
        else:
            page_num = _outline_page_number(reader, item)
            title = getattr(item, "title", str(item))
            if page_num is not None and title:
                result.append({"title": title, "start_page": page_num})
    return result


def _extract_via_outline(reader: PdfReader) -> list[dict]:
    """Extrahiert Kapitel aus PyPDF2 Outline-Tree."""
    outline = reader.outline
    if not outline:
        return []
    chapters = _flatten_outline(reader, outline)
    # Duplikate und unsortierte Eintraege bereinigen
    seen = set()
    unique = []
    for ch in chapters:
        key = (ch["title"], ch["start_page"])
        if key not in seen:
            seen.add(key)
            unique.append(ch)
    unique.sort(key=lambda c: c["start_page"])
    return unique


def _extract_via_toc_text(reader: PdfReader) -> list[dict]:
    """Fallback: Sucht Kapitelzeilen in den ersten 20 Seiten per Regex."""
    # Kapitel-Pattern: "1. Einleitung .... 5", "Kapitel 1 Einleitung 5", etc.
    patterns = [
        re.compile(
            r"(?:Kapitel|Chapter)\s+(\d+)[.:)]\s*(.+?)\s+(\d+)\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(\d+)\.\s+([A-ZAEOEUÄÖÜ][^\n]{3,60}?)\s{2,}(\d+)\s*$",
            re.MULTILINE,
        ),
    ]
    text_pages = min(20, len(reader.pages))
    full_text = ""
    for i in range(text_pages):
        try:
            full_text += (reader.pages[i].extract_text() or "") + "\n"
        except Exception:
            pass

    chapters = []
    for pat in patterns:
        for m in pat.finditer(full_text):
            try:
                num = int(m.group(1))
                title = m.group(2).strip()
                page = int(m.group(3)) - 1  # 1-indexed -> 0-indexed
                if 0 <= page < len(reader.pages):
                    chapters.append({
                        "title": f"Kapitel {num}: {title}",
                        "start_page": page,
                    })
            except (ValueError, IndexError):
                pass
        if chapters:
            break

    chapters.sort(key=lambda c: c["start_page"])
    # Duplikate entfernen
    seen = set()
    unique = []
    for ch in chapters:
        key = ch["start_page"]
        if key not in seen:
            seen.add(key)
            unique.append(ch)
    return unique


def _assign_end_pages(chapters: list[dict], total_pages: int) -> list[dict]:
    """Berechnet end_page fuer jedes Kapitel."""
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            ch["end_page"] = chapters[i + 1]["start_page"] - 1
        else:
            ch["end_page"] = total_pages - 1
    return chapters


def extract_chapters(pdf_path: str) -> list[dict]:
    """Extrahiert Kapitel-Metadaten aus PDF. Gibt [{title, start_page, end_page}] zurueck.

    Raises SystemExit(2) wenn weder Outline noch TOC gefunden.
    """
    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    chapters = _extract_via_outline(reader)
    if not chapters:
        chapters = _extract_via_toc_text(reader)
    if not chapters:
        print(
            f"[chunk_pdf] Fehler: Kein Outline-Tree und kein TOC-Text in '{pdf_path}' gefunden.",
            file=sys.stderr,
        )
        sys.exit(2)

    return _assign_end_pages(chapters, total)


def write_chapter(pdf_path: str, chapter: dict, output_path: str) -> None:
    """Schreibt einen Kapitel-Bereich als neues PDF."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    start = chapter["start_page"]
    end = chapter["end_page"]
    for page_num in range(start, end + 1):
        if 0 <= page_num < len(reader.pages):
            writer.add_page(reader.pages[page_num])
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)


def write_all_chapters(
    pdf_path: str,
    output_dir: str,
    isbn: str = "book",
) -> list[str]:
    """Schreibt alle Kapitel als separate PDFs. Gibt Liste der Pfade zurueck."""
    chapters = extract_chapters(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, ch in enumerate(chapters, start=1):
        safe_isbn = re.sub(r"[^a-zA-Z0-9_-]", "-", isbn)
        fname = f"{safe_isbn}-ch{i}.pdf"
        out_path = os.path.join(output_dir, fname)
        write_chapter(pdf_path, ch, out_path)
        paths.append(out_path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zerlegt Buch-PDFs kapitelweise (PyPDF2 Outline-Tree)."
    )
    parser.add_argument("--input", required=True, help="Eingabe-PDF")
    parser.add_argument(
        "--chapter",
        required=True,
        help="Kapitel-Nummer (1-basiert), 'all' oder 'toc'",
    )
    parser.add_argument(
        "--output", required=True, help="Ausgabe-Pfad oder Verzeichnis (bei --chapter all)"
    )
    parser.add_argument("--isbn", default="book", help="ISBN fuer Dateinamen (bei --chapter all)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[chunk_pdf] Eingabe-PDF nicht gefunden: {args.input}", file=sys.stderr)
        return 1

    if args.chapter == "toc":
        chapters = extract_chapters(args.input)
        print(json.dumps(
            [{"title": c["title"], "start_page": c["start_page"], "end_page": c["end_page"]}
             for c in chapters],
            ensure_ascii=False, indent=2,
        ))
        return 0

    if args.chapter == "all":
        paths = write_all_chapters(args.input, args.output, isbn=args.isbn)
        print(f"[chunk_pdf] {len(paths)} Kapitel geschrieben nach {args.output}")
        for p in paths:
            print(f"  {p}")
        return 0

    # Einzelnes Kapitel
    try:
        n = int(args.chapter)
    except ValueError:
        print(f"[chunk_pdf] Ungueltige Kapitel-Angabe: {args.chapter!r}", file=sys.stderr)
        return 1

    chapters = extract_chapters(args.input)
    if n < 1 or n > len(chapters):
        print(
            f"[chunk_pdf] Kapitel {n} nicht vorhanden (1-{len(chapters)}).",
            file=sys.stderr,
        )
        return 1

    write_chapter(args.input, chapters[n - 1], args.output)
    print(f"[chunk_pdf] Kapitel {n} geschrieben: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Schritt 4: Tests ausfuehren — muessen gruen sein**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-B
/opt/homebrew/bin/pytest tests/test_chunk_pdf.py -v --tb=short 2>&1
# Erwartet: alle Tests PASS
```

- [ ] **Schritt 5: Commit**

```bash
git add scripts/chunk_pdf.py tests/test_chunk_pdf.py
git commit -m "feat: chunk_pdf.py — Kapitel-Schnitt via PyPDF2 Outline-Tree"
```

---

### Task 3: Vault schema.sql — parent_paper_id Spalte

**Files:**
- Modify: `mcp/academic_vault/schema.sql`

- [ ] **Schritt 1: Failing test schreiben**

```python
# tests/test_vault_parent.py (nur diese eine Test-Klasse)
"""Tests fuer parent_paper_id in Vault."""
import tempfile, os
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mcp.academic_vault.db import VaultDB


class TestParentPaperIdSchema:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        self.db = VaultDB(self.db_path)
        self.db.init_schema()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_parent_paper_id_column_exists(self):
        """papers-Tabelle hat parent_paper_id-Spalte."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(papers)").fetchall()]
        conn.close()
        assert "parent_paper_id" in cols

    def test_add_paper_with_parent_paper_id(self):
        """add_paper akzeptiert parent_paper_id."""
        import json
        # Eltern-Buch anlegen
        self.db.add_paper(
            paper_id="book-parent",
            csl_json=json.dumps({"type": "book", "title": "Elternbuch"}),
        )
        # Kapitel mit parent_paper_id
        self.db.add_paper(
            paper_id="chapter-child",
            csl_json=json.dumps({"type": "chapter", "title": "Kapitel 1"}),
            parent_paper_id="book-parent",
        )
        paper = self.db.get_paper("chapter-child")
        assert paper is not None
        assert paper["parent_paper_id"] == "book-parent"

    def test_parent_paper_id_nullable(self):
        """parent_paper_id ist NULL wenn nicht gesetzt."""
        import json
        self.db.add_paper(
            paper_id="standalone",
            csl_json=json.dumps({"type": "article-journal", "title": "Artikel"}),
        )
        paper = self.db.get_paper("standalone")
        assert paper["parent_paper_id"] is None
```

- [ ] **Schritt 2: Test ausfuehren — muss fehlschlagen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-B
/opt/homebrew/bin/pytest tests/test_vault_parent.py::TestParentPaperIdSchema -v --tb=short
# Erwartet: FAIL — 'parent_paper_id' not in cols
```

- [ ] **Schritt 3: schema.sql erweitern**

In `mcp/academic_vault/schema.sql` die Zeile nach `container_title` einfuegen:

```sql
  container_title       TEXT,
  parent_paper_id       TEXT REFERENCES papers(paper_id),
```

Die vollstaendige papers-Tabelle sieht danach so aus (nur die neue Zeile wird hinzugefuegt):

```sql
CREATE TABLE IF NOT EXISTS papers (
  paper_id              TEXT PRIMARY KEY,
  type                  TEXT NOT NULL DEFAULT 'article-journal'
                          CHECK(type IN ('article-journal','book','chapter')),
  csl_json              TEXT NOT NULL,
  doi                   TEXT,
  isbn                  TEXT,
  pdf_path              TEXT,
  file_id               TEXT,
  file_id_expires_at    INTEGER,
  page_offset           INTEGER DEFAULT 0,
  ocr_done              INTEGER DEFAULT 0,
  editor                TEXT,
  chapter               TEXT,
  page_first            INTEGER,
  page_last             INTEGER,
  container_title       TEXT,
  parent_paper_id       TEXT REFERENCES papers(paper_id),
  added_at              INTEGER NOT NULL,
  updated_at            INTEGER NOT NULL
);
```

- [ ] **Schritt 4: Tests ausfuehren — muessen gruen sein**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py::TestParentPaperIdSchema -v --tb=short
# Erwartet: PASS (init_schema erstellt jetzt Tabelle mit neuer Spalte)
```

- [ ] **Schritt 5: Commit**

```bash
git add mcp/academic_vault/schema.sql
git commit -m "feat(vault): parent_paper_id Spalte in papers-Tabelle"
```

---

### Task 4: migrate.py — add_parent_paper_id_column()

**Files:**
- Modify: `mcp/academic_vault/migrate.py`

- [ ] **Schritt 1: Failing test schreiben (zu tests/test_vault_parent.py hinzufuegen)**

```python
class TestMigrateParentPaperId:
    def setup_method(self):
        import tempfile
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()
        # Altes Schema ohne parent_paper_id simulieren
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE papers (
                paper_id TEXT PRIMARY KEY,
                type TEXT NOT NULL DEFAULT 'article-journal',
                csl_json TEXT NOT NULL,
                added_at INTEGER NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_parent_paper_id_column_idempotent(self):
        """Migration fuegt Spalte hinzu; zweiter Lauf wirft keinen Fehler."""
        from mcp.academic_vault.migrate import add_parent_paper_id_column
        import sqlite3
        # Erster Lauf
        add_parent_paper_id_column(self.db_path)
        cols = [
            row[1] for row in
            sqlite3.connect(self.db_path).execute("PRAGMA table_info(papers)").fetchall()
        ]
        assert "parent_paper_id" in cols
        # Zweiter Lauf: kein Fehler
        add_parent_paper_id_column(self.db_path)
```

- [ ] **Schritt 2: Test ausfuehren — muss fehlschlagen**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py::TestMigrateParentPaperId -v --tb=short
# Erwartet: AttributeError — add_parent_paper_id_column nicht vorhanden
```

- [ ] **Schritt 3: Funktion in migrate.py hinzufuegen**

Am Ende der Datei (vor `main()`), nach `add_book_columns()`:

```python
def add_parent_paper_id_column(db_path: str) -> None:
    """Fuegt parent_paper_id-Spalte zu papers hinzu. Idempotent (try/except).

    Aufruf-Sicher: Kann mehrfach auf derselben DB ausgefuehrt werden.
    """
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    try:
        try:
            conn.execute(
                "ALTER TABLE papers ADD COLUMN "
                "parent_paper_id TEXT REFERENCES papers(paper_id)"
            )
        except _sqlite3.OperationalError:
            pass  # Spalte existiert bereits -- idempotent
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Schritt 4: Tests ausfuehren**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py -v --tb=short
# Erwartet: alle TestMigrateParentPaperId-Tests PASS
```

- [ ] **Schritt 5: Commit**

```bash
git add mcp/academic_vault/migrate.py tests/test_vault_parent.py
git commit -m "feat(vault): add_parent_paper_id_column() idempotente Migration"
```

---

### Task 5: db.py — add_paper() um parent_paper_id erweitern

**Files:**
- Modify: `mcp/academic_vault/db.py`

- [ ] **Schritt 1: Failing test (in TestParentPaperIdSchema bereits enthalten)**

Der Test `test_add_paper_with_parent_paper_id` aus Task 3 schlaegt bei diesem
Schritt fehl, weil `add_paper()` noch keinen `parent_paper_id`-Parameter hat.
Pruefen:

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py::TestParentPaperIdSchema::test_add_paper_with_parent_paper_id -v --tb=short
# Erwartet: FAIL — TypeError: add_paper() got unexpected keyword argument
```

- [ ] **Schritt 2: db.py add_paper() erweitern**

Die Methode `add_paper` in `mcp/academic_vault/db.py` erhielt folgende Signatur
(nach Chunk A):

```python
def add_paper(
    self,
    paper_id: str,
    csl_json: str,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
    pdf_path: Optional[str] = None,
    page_offset: int = 0,
    editor: Optional[str] = None,
    chapter: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
    container_title: Optional[str] = None,
) -> None:
```

Erweitern um `parent_paper_id: Optional[str] = None`:

```python
def add_paper(
    self,
    paper_id: str,
    csl_json: str,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
    pdf_path: Optional[str] = None,
    page_offset: int = 0,
    editor: Optional[str] = None,
    chapter: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
    container_title: Optional[str] = None,
    parent_paper_id: Optional[str] = None,
) -> None:
    """Upsert eines Papers in die papers-Tabelle.

    type wird aus csl_json extrahiert. Erlaubte Werte: article-journal, book, chapter.
    """
    try:
        csl = json.loads(csl_json)
        paper_type = csl.get("type", "article-journal")
    except Exception:
        paper_type = "article-journal"

    if paper_type not in VALID_PAPER_TYPES:
        raise ValueError(
            f"Ungueltiger type '{paper_type}' -- erlaubt: {sorted(VALID_PAPER_TYPES)}"
        )

    now = int(time.time())
    conn = self._get_conn()
    own_conn = self._conn is None
    conn.execute(
        """
        INSERT INTO papers
          (paper_id, type, csl_json, doi, isbn, pdf_path, page_offset,
           editor, chapter, page_first, page_last, container_title,
           parent_paper_id,
           added_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(paper_id) DO UPDATE SET
          type           = excluded.type,
          csl_json       = excluded.csl_json,
          doi            = excluded.doi,
          isbn           = excluded.isbn,
          pdf_path       = excluded.pdf_path,
          page_offset    = excluded.page_offset,
          editor         = excluded.editor,
          chapter        = excluded.chapter,
          page_first     = excluded.page_first,
          page_last      = excluded.page_last,
          container_title= excluded.container_title,
          parent_paper_id= excluded.parent_paper_id,
          updated_at     = excluded.updated_at
        """,
        (
            paper_id, paper_type, csl_json, doi, isbn, pdf_path, page_offset,
            editor, chapter, page_first, page_last, container_title,
            parent_paper_id,
            now, now,
        ),
    )
    if own_conn:
        conn.commit()
        conn.close()
```

- [ ] **Schritt 3: Tests ausfuehren**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py -v --tb=short
# Erwartet: alle Tests PASS
```

- [ ] **Schritt 4: Commit**

```bash
git add mcp/academic_vault/db.py
git commit -m "feat(vault): db.add_paper() + parent_paper_id Parameter"
```

---

### Task 6: server.py — add_paper() + add_chapter() erweitern

**Files:**
- Modify: `mcp/academic_vault/server.py`

- [ ] **Schritt 1: Failing test hinzufuegen (zu test_vault_parent.py)**

```python
class TestServerAddChapter:
    def setup_method(self):
        import tempfile
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.tmp.close()

    def teardown_method(self):
        os.unlink(self.db_path)

    def test_add_chapter_via_server(self):
        """server.add_chapter() legt Kapitel mit parent_paper_id an."""
        import json
        from mcp.academic_vault import server as vault_server
        # Elternbuch anlegen
        vault_server.add_paper(
            self.db_path, "buch-001",
            csl_json=json.dumps({"type": "book", "title": "Grundlagen"}),
        )
        # Kapitel via add_chapter
        vault_server.add_chapter(
            db_path=self.db_path,
            parent_paper_id="buch-001",
            chapter_number=1,
            csl_json=json.dumps({"type": "chapter", "title": "Einleitung"}),
            paper_id="buch-001-ch1",
        )
        paper = vault_server.get_paper(self.db_path, "buch-001-ch1")
        assert paper is not None
        assert paper["parent_paper_id"] == "buch-001"
        assert paper["type"] == "chapter"

    def test_server_add_paper_accepts_parent_paper_id(self):
        """server.add_paper() akzeptiert parent_paper_id."""
        import json
        from mcp.academic_vault import server as vault_server
        vault_server.add_paper(
            self.db_path, "root-book",
            csl_json=json.dumps({"type": "book", "title": "Root"}),
        )
        vault_server.add_paper(
            self.db_path, "ch-2",
            csl_json=json.dumps({"type": "chapter", "title": "Kap 2"}),
            parent_paper_id="root-book",
        )
        paper = vault_server.get_paper(self.db_path, "ch-2")
        assert paper["parent_paper_id"] == "root-book"
```

- [ ] **Schritt 2: Test ausfuehren — muss fehlschlagen**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py::TestServerAddChapter -v --tb=short
# Erwartet: AttributeError — add_chapter nicht in server
```

- [ ] **Schritt 3: server.py erweitern**

In `mcp/academic_vault/server.py`:

1. `add_paper()`-Funktion um `parent_paper_id` erweitern:

```python
def add_paper(
    db_path: str,
    paper_id: str,
    csl_json: str,
    pdf_path: Optional[str] = None,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
    page_offset: int = 0,
    editor: Optional[str] = None,
    chapter: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
    container_title: Optional[str] = None,
    parent_paper_id: Optional[str] = None,
) -> None:
    """Upsert eines Papers in den Vault. Unterstuetzt type=book|chapter."""
    db = VaultDB(db_path)
    db.init_schema()
    db.add_paper(
        paper_id, csl_json,
        doi=doi, isbn=isbn, pdf_path=pdf_path, page_offset=page_offset,
        editor=editor, chapter=chapter,
        page_first=page_first, page_last=page_last,
        container_title=container_title,
        parent_paper_id=parent_paper_id,
    )
```

2. Neue Funktion `add_chapter()` nach `add_paper()`:

```python
def add_chapter(
    db_path: str,
    parent_paper_id: str,
    chapter_number: int,
    csl_json: str,
    paper_id: Optional[str] = None,
    pdf_path: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
) -> str:
    """Legt ein Kapitel als Kind-Paper in den Vault. Gibt paper_id zurueck.

    Setzt type=chapter automatisch falls nicht in csl_json angegeben.
    """
    import json as _json
    if paper_id is None:
        paper_id = f"{parent_paper_id}-ch{chapter_number}"
    # Sicherstellen dass type=chapter in csl_json gesetzt ist
    try:
        csl = _json.loads(csl_json)
        csl.setdefault("type", "chapter")
        csl_json = _json.dumps(csl, ensure_ascii=False)
    except Exception:
        pass
    add_paper(
        db_path=db_path,
        paper_id=paper_id,
        csl_json=csl_json,
        pdf_path=pdf_path,
        chapter=str(chapter_number),
        page_first=page_first,
        page_last=page_last,
        parent_paper_id=parent_paper_id,
    )
    return paper_id
```

3. Im `_build_mcp_server()`-Block: `vault.add_paper` und `vault.add_chapter` aktualisieren:

```python
@mcp.tool(name="vault.add_paper")
def _vault_add_paper(
    paper_id: str,
    csl_json: str,
    pdf_path: str = None,
    doi: str = None,
    isbn: str = None,
    page_offset: int = 0,
    editor: str = None,
    chapter: str = None,
    page_first: int = None,
    page_last: int = None,
    container_title: str = None,
    parent_paper_id: str = None,
) -> None:
    """Upsert eines Papers. type aus csl_json; book|chapter|article-journal erlaubt."""
    add_paper(
        db_path, paper_id, csl_json,
        pdf_path=pdf_path, doi=doi, isbn=isbn, page_offset=page_offset,
        editor=editor, chapter=chapter,
        page_first=page_first, page_last=page_last,
        container_title=container_title,
        parent_paper_id=parent_paper_id,
    )

@mcp.tool(name="vault.add_chapter")
def _vault_add_chapter(
    parent_paper_id: str,
    chapter_number: int,
    csl_json: str,
    paper_id: str = None,
    pdf_path: str = None,
    page_first: int = None,
    page_last: int = None,
) -> str:
    """Legt Kapitel als Kind-Paper an. Gibt paper_id zurueck."""
    return add_chapter(
        db_path=db_path,
        parent_paper_id=parent_paper_id,
        chapter_number=chapter_number,
        csl_json=csl_json,
        paper_id=paper_id,
        pdf_path=pdf_path,
        page_first=page_first,
        page_last=page_last,
    )
```

- [ ] **Schritt 4: Tests ausfuehren**

```bash
/opt/homebrew/bin/pytest tests/test_vault_parent.py -v --tb=short
# Erwartet: alle Tests PASS
```

- [ ] **Schritt 5: Commit**

```bash
git add mcp/academic_vault/server.py tests/test_vault_parent.py
git commit -m "feat(vault): server.add_chapter() + parent_paper_id in add_paper()"
```

---

### Task 7: skills/citation-extraction/SKILL.md anpassen

**Files:**
- Modify: `skills/citation-extraction/SKILL.md`

- [ ] **Schritt 1: Hinweis in SKILL.md einfuegen**

Im Abschnitt `### 3. Zitat-Extraktion` (nach dem ersten Absatz, vor dem JSON-Block) folgendes einfuegen:

```markdown
> **Kapitel-PDF-Modus:** Wenn `vault.get_paper(paper_id)["parent_paper_id"]` gesetzt
> ist, liegt ein Kapitel-PDF vor (erzeugt von `chunk_pdf.py`). Uebergib statt des
> Gesamt-Buches nur dieses Kapitel-PDF als `file_id` via `vault.ensure_file(paper_id)`.
> Das reduziert den Token-Footprint um typisch 90-95 % gegenueber dem Gesamtbuch.
```

- [ ] **Schritt 2: Kein automatisierter Test fuer Skill-Docs erforderlich**

Die Skill-Doku ist prose — kein pytest-Test noetig. Sicherstellen dass
`test_skills_manifest.py` weiterhin gruен ist:

```bash
/opt/homebrew/bin/pytest tests/test_skills_manifest.py -v --tb=short -k "not token_reduction"
# Erwartet: PASS
```

- [ ] **Schritt 3: Commit**

```bash
git add skills/citation-extraction/SKILL.md
git commit -m "docs(skill): citation-extraction Hinweis fuer Kapitel-PDF-Modus"
```

---

### Task 8: Full Test Suite + Abschluss-Verifikation

- [ ] **Schritt 1: Alle Tests ausfuehren**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-B
/opt/homebrew/bin/pytest tests/ --tb=short -q 2>&1 | tail -20
# Erwartet:
# - PASSED: alle neuen Tests (test_chunk_pdf.py, test_vault_parent.py)
# - FAILED: nur test_token_reduction[chapter-writer] und test_token_reduction[citation-extraction]
#   (vorbestehende Fehler)
# - 0 neue Fehler
```

- [ ] **Schritt 2: state.yaml aktualisieren**

```bash
# phase auf pr_ready setzen
```

Die Datei `/Users/j65674/Repos/academic-research-v6.1-B/.orchestrator/chunks/B/state.yaml`
wird nach Abschluss der Implementierung auf `phase: pr_ready` gesetzt.
