# NotebookLM-Bundle Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skill und Python-Skripte, die aus einer JSON-Selektion (Top-N Paper) ein konkateniertes Bundle-PDF mit Cover und TOC für manuellen NotebookLM-Upload erzeugen.

**Architecture:** `bundle.py` orchestriert den Prozess: Cover-PDF via `cover_pdf.py` erzeugen (PyPDF2-Stream-Injection, kein reportlab), dann alle PDFs per PyPDF2 konkatenieren, TOC als erste Seite einsetzen. Bei >500MB Split in mehrere Dateien. `SKILL.md` definiert Trigger, Verbatim-Warning und Workflow für Claude.

**Tech Stack:** Python 3.x, PyPDF2>=3.0.0 (bereits in requirements.txt), pytest, keine externen Heavy-Deps.

---

## Dateikarte

| Datei | Aktion | Zweck |
|-------|--------|-------|
| `tests/test_notebook_bundle.py` | Neu | 6 TDD-Tests (red-first) |
| `tests/fixtures/notebook_bundle/selection.json` | Neu | Mock-Selection mit 5 Papieren |
| `tests/fixtures/notebook_bundle/paper_*.pdf` | Neu | 5 Mock-PDFs à 3 Seiten (via conftest) |
| `skills/notebook-bundle/scripts/cover_pdf.py` | Neu | Bibliographie-Cover als PDF-Seite(n) |
| `skills/notebook-bundle/scripts/bundle.py` | Neu | Haupt-Bundle-Orchestrierung + CLI |
| `skills/notebook-bundle/SKILL.md` | Neu | Skill-Frontmatter, Verbatim-Warning, Workflow |
| `docs/skills/notebook-bundle.md` | Neu | User-Doku mit NotebookLM-Upload-Flow |

---

## Task 1: Test-Fixtures anlegen (Mock-PDFs + Selection-JSON)

**Files:**
- Create: `tests/fixtures/notebook_bundle/selection.json`
- Create: `tests/fixtures/notebook_bundle/conftest.py`

- [ ] **Schritt 1: Verzeichnis anlegen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.3-B/tests/fixtures/notebook_bundle
```

- [ ] **Schritt 2: `selection.json` schreiben**

Inhalt: 5 Paper-Einträge. `pdf_path` zeigt auf Fixtures-Verzeichnis (relativ zu CWD beim Test-Run, daher wird in Tests dynamisch gesetzt).

Datei: `tests/fixtures/notebook_bundle/selection.json`
```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Deep Learning for NLP",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2020,
      "pdf_path": "__FIXTURE_DIR__/paper_smith2020.pdf"
    },
    {
      "id": "jones2019",
      "title": "Transformer Architectures",
      "authors": ["Jones, B."],
      "year": 2019,
      "pdf_path": "__FIXTURE_DIR__/paper_jones2019.pdf"
    },
    {
      "id": "brown2021",
      "title": "Few-Shot Learning in LLMs",
      "authors": ["Brown, C.", "White, D."],
      "year": 2021,
      "pdf_path": "__FIXTURE_DIR__/paper_brown2021.pdf"
    },
    {
      "id": "zhang2022",
      "title": "Instruction Tuning Approaches",
      "authors": ["Zhang, L."],
      "year": 2022,
      "pdf_path": "__FIXTURE_DIR__/paper_zhang2022.pdf"
    },
    {
      "id": "lee2023",
      "title": "RLHF and Alignment",
      "authors": ["Lee, K.", "Park, M."],
      "year": 2023,
      "pdf_path": "__FIXTURE_DIR__/paper_lee2023.pdf"
    }
  ]
}
```

- [ ] **Schritt 3: Mock-PDF-Generator als pytest-Fixture schreiben**

Datei: `tests/fixtures/notebook_bundle/conftest.py`
```python
"""Pytest-Fixtures für notebook-bundle Tests."""
import io
import json
import os
import pytest
from PyPDF2 import PdfWriter


def make_mock_pdf(title: str, num_pages: int = 3) -> bytes:
    """Erzeugt ein minimales PDF mit num_pages leeren Seiten."""
    writer = PdfWriter()
    for i in range(num_pages):
        writer.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture(scope="session")
def fixture_dir(tmp_path_factory):
    """Temporäres Verzeichnis mit 5 Mock-PDFs und selection.json."""
    d = tmp_path_factory.mktemp("notebook_bundle")
    paper_ids = ["smith2020", "jones2019", "brown2021", "zhang2022", "lee2023"]
    titles = [
        "Deep Learning for NLP",
        "Transformer Architectures",
        "Few-Shot Learning in LLMs",
        "Instruction Tuning Approaches",
        "RLHF and Alignment",
    ]
    authors_list = [
        ["Smith, J.", "Doe, A."],
        ["Jones, B."],
        ["Brown, C.", "White, D."],
        ["Zhang, L."],
        ["Lee, K.", "Park, M."],
    ]
    years = [2020, 2019, 2021, 2022, 2023]

    papers = []
    for pid, title, authors, year in zip(paper_ids, titles, authors_list, years):
        pdf_path = d / f"paper_{pid}.pdf"
        pdf_path.write_bytes(make_mock_pdf(title, num_pages=3))
        papers.append(
            {
                "id": pid,
                "title": title,
                "authors": authors,
                "year": year,
                "pdf_path": str(pdf_path),
            }
        )

    selection_path = d / "selection.json"
    selection_path.write_text(json.dumps({"papers": papers}, indent=2))
    return d
```

- [ ] **Schritt 4: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add tests/fixtures/notebook_bundle/
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "test(v6.3-B): fixture setup für notebook-bundle (Mock-PDFs + selection.json)"
```

---

## Task 2: Failing Tests schreiben (RED)

**Files:**
- Create: `tests/test_notebook_bundle.py`

- [ ] **Schritt 1: Test-Datei schreiben**

Datei: `tests/test_notebook_bundle.py`
```python
"""Tests für skills/notebook-bundle.

TDD: Alle Tests schreiben BEVOR die Implementierung existiert.
"""
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import pytest
from PyPDF2 import PdfReader, PdfWriter

# Pfad zu scripts hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "notebook-bundle" / "scripts"))


class TestBundleFivePapers:
    """AC: 5 Paper × 30 Seiten (hier Mock: 3 S. je) → Bundle hat ≥ 15 Seiten."""

    def test_bundle_5_papers_page_count(self, fixture_dir, tmp_path):
        """Bundle aus 5 Paper × 3 Seiten hat mindestens 15 Inhaltsseiten."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle.pdf"
        result = build_bundle(str(selection_path), str(output_path))

        assert result["status"] == "ok"
        reader = PdfReader(str(output_path))
        # 15 Inhaltsseiten + Cover + TOC = mindestens 17
        assert len(reader.pages) >= 15


class TestTOC:
    """TOC-Seite ist erste Seite und enthält alle Paper-Titel."""

    def test_toc_is_first_page(self, fixture_dir, tmp_path):
        """Erste Seite des Bundles ist die TOC-Seite."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle_toc.pdf"
        build_bundle(str(selection_path), str(output_path))

        reader = PdfReader(str(output_path))
        first_page_text = reader.pages[0].extract_text() or ""
        assert "Inhaltsverzeichnis" in first_page_text or "Table of Contents" in first_page_text or "TOC" in first_page_text


class TestCoverPage:
    """Cover-PDF enthält alle Paper-Einträge (Titel + Autoren + Jahr)."""

    def test_cover_contains_all_papers(self, fixture_dir, tmp_path):
        """Cover-Seite enthält alle 5 Paper-Titel."""
        from cover_pdf import generate_cover

        selection_path = fixture_dir / "selection.json"
        selection = json.loads(Path(str(selection_path)).read_text())
        cover_path = tmp_path / "cover.pdf"
        generate_cover(selection["papers"], str(cover_path))

        reader = PdfReader(str(cover_path))
        full_text = " ".join(
            reader.pages[i].extract_text() or "" for i in range(len(reader.pages))
        )
        for paper in selection["papers"]:
            assert paper["title"] in full_text, f"Titel '{paper['title']}' nicht im Cover"


class TestSplitOver500MB:
    """Bundle >500MB wird in mehrere Dateien aufgeteilt."""

    def test_split_produces_multiple_files(self, fixture_dir, tmp_path):
        """Wenn size_limit_mb=0.001, werden mehrere Bundle-Dateien erzeugt."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        output_path = tmp_path / "bundle_split.pdf"
        result = build_bundle(
            str(selection_path), str(output_path), size_limit_mb=0.001
        )

        assert result["status"] == "split"
        assert len(result["output_files"]) > 1
        for f in result["output_files"]:
            assert Path(f).exists()


class TestMissingPDFSkipped:
    """Paper mit nicht-existenter PDF wird übersprungen, kein Exception."""

    def test_missing_pdf_skipped(self, tmp_path):
        """Paper mit fehlendem PDF wird übersprungen; restliche Paper im Bundle."""
        from bundle import build_bundle

        # Selection mit 1 existenter + 1 fehlender PDF
        good_pdf = tmp_path / "good.pdf"
        writer = PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=595, height=842)
        buf = io.BytesIO()
        writer.write(buf)
        good_pdf.write_bytes(buf.getvalue())

        selection = {
            "papers": [
                {
                    "id": "good",
                    "title": "Good Paper",
                    "authors": ["A. Good"],
                    "year": 2021,
                    "pdf_path": str(good_pdf),
                },
                {
                    "id": "missing",
                    "title": "Missing Paper",
                    "authors": ["B. Missing"],
                    "year": 2020,
                    "pdf_path": str(tmp_path / "nonexistent.pdf"),
                },
            ]
        }
        sel_path = tmp_path / "selection.json"
        sel_path.write_text(json.dumps(selection))
        output_path = tmp_path / "bundle_missing.pdf"

        result = build_bundle(str(sel_path), str(output_path))

        assert result["status"] in ("ok", "partial")
        assert "missing" in result.get("skipped_ids", []) or result.get("skipped_count", 0) > 0
        assert Path(output_path).exists()


class TestOutputFilenamePattern:
    """Output-Dateiname enthält 'notebook-bundle-' + Timestamp-Pattern."""

    def test_auto_output_filename(self, fixture_dir, tmp_path):
        """Wenn kein output_path angegeben, wird notebook-bundle-<ts>.pdf erzeugt."""
        from bundle import build_bundle

        selection_path = fixture_dir / "selection.json"
        result = build_bundle(str(selection_path), output_dir=str(tmp_path))

        assert result["status"] in ("ok", "split")
        main_file = result["output_files"][0]
        filename = Path(main_file).name
        assert re.match(r"notebook-bundle-\d{8}T\d{6}.*\.pdf", filename), (
            f"Dateiname '{filename}' entspricht nicht dem Pattern notebook-bundle-<ts>.pdf"
        )
```

- [ ] **Schritt 2: Tests ausführen — müssen FEHLSCHLAGEN**

```bash
~/.academic-research/venv/bin/python -m pytest /Users/j65674/Repos/academic-research-v6.3-B/tests/test_notebook_bundle.py -v 2>&1 | head -50
```

Erwartetes Ergebnis: `ModuleNotFoundError: No module named 'bundle'` oder `ImportError` — Tests schlagen fehl, weil Implementierung noch fehlt.

- [ ] **Schritt 3: Commit (nur Tests)**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add tests/test_notebook_bundle.py
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "test(v6.3-B): failing tests für notebook-bundle (TDD RED)"
```

---

## Task 3: `cover_pdf.py` implementieren (GREEN für Cover-Test)

**Files:**
- Create: `skills/notebook-bundle/scripts/__init__.py`
- Create: `skills/notebook-bundle/scripts/cover_pdf.py`

- [ ] **Schritt 1: Verzeichnis anlegen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.3-B/skills/notebook-bundle/scripts
touch /Users/j65674/Repos/academic-research-v6.3-B/skills/notebook-bundle/scripts/__init__.py
```

- [ ] **Schritt 2: `cover_pdf.py` schreiben**

Datei: `skills/notebook-bundle/scripts/cover_pdf.py`
```python
"""Erzeugt Bibliographie-Cover-PDF aus einer Paper-Liste.

Nutzt PyPDF2-Stream-Injection (kein reportlab, kein fpdf).
Jede Zeile wird als PDF-Content-Stream in eine Blank-Page injiziert.
"""
from __future__ import annotations

import io
from typing import List, Dict, Any

from PyPDF2 import PdfWriter
from PyPDF2.generic import NameObject, DecodedStreamObject, ArrayObject


# Seitengröße A4 in Punkten
PAGE_WIDTH = 595
PAGE_HEIGHT = 842

# Standard-Schriftgröße (nur Helvetica — eingebettet in PDF-Spec, kein Font-Embedding nötig)
FONT_TITLE = 14
FONT_BODY = 11
FONT_SMALL = 9


def _make_text_page(lines: List[tuple]) -> bytes:
    """Erzeugt eine PDF-Seite mit Text via Content-Stream.

    Args:
        lines: Liste von (text, x, y, font_size) Tupeln.
               Koordinaten in Punkten (0,0 = unten links).

    Returns:
        Serialisiertes PDF als bytes.
    """
    writer = PdfWriter()
    page = writer.add_blank_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

    # Content-Stream aufbauen
    stream_parts = ["BT"]
    for text, x, y, size in lines:
        # Text bereinigen: Klammern escapen für PDF-Literal-String
        safe_text = (
            text.replace("\\", "\\\\")
                .replace("(", "\\(")
                .replace(")", "\\)")
                .replace("\n", " ")
        )
        stream_parts.append(f"/Helvetica {size} Tf")
        stream_parts.append(f"{x} {y} Td")
        stream_parts.append(f"({safe_text}) Tj")
        stream_parts.append("0 0 Td")  # Reset-Offset (absolut via Td)
    stream_parts.append("ET")
    stream_data = "\n".join(stream_parts).encode("latin-1", errors="replace")

    # Stream-Objekt injizieren
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(stream_data)
    stream_ref = writer._add_object(stream_obj)
    page[NameObject("/Contents")] = stream_ref

    # Font-Resource eintragen
    from PyPDF2.generic import DictionaryObject
    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = writer._add_object(font_dict)

    resources = DictionaryObject()
    font_resources = DictionaryObject()
    font_resources[NameObject("/Helvetica")] = font_ref
    resources[NameObject("/Font")] = font_resources
    page[NameObject("/Resources")] = resources

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def generate_cover(papers: List[Dict[str, Any]], output_path: str) -> None:
    """Erzeugt Bibliographie-Cover-PDF mit allen Paper-Einträgen.

    Args:
        papers: Liste von Paper-Dicts mit keys: title, authors, year, id.
        output_path: Ausgabepfad für die Cover-PDF.
    """
    writer = PdfWriter()

    # Kopfzeile-Seite
    lines = []
    y = PAGE_HEIGHT - 60
    lines.append(("Bibliographie — NotebookLM Bundle", 50, y, FONT_TITLE + 2))
    y -= 30
    lines.append(("Dieser Bundle dient der Orientierung. Kein verbatim-gesicherter Zitat-Pfad.", 50, y, FONT_SMALL))
    y -= 40

    papers_per_page = 20
    current_lines = list(lines)
    page_count = 0

    for i, paper in enumerate(papers):
        if i > 0 and i % papers_per_page == 0:
            # Neue Seite
            page_bytes = _make_text_page(current_lines)
            from PyPDF2 import PdfReader as _PR
            reader = _PR(io.BytesIO(page_bytes))
            writer.add_page(reader.pages[0])
            page_count += 1
            current_lines = []
            y = PAGE_HEIGHT - 60

        authors_str = "; ".join(paper.get("authors", []))
        year = paper.get("year", "")
        title = paper.get("title", "(kein Titel)")
        entry = f"[{i + 1}] {title} — {authors_str} ({year})"

        current_lines.append((entry, 50, y, FONT_BODY))
        y -= 20

    # Letzte / einzige Seite
    if current_lines:
        page_bytes = _make_text_page(current_lines)
        from PyPDF2 import PdfReader as _PR
        reader = _PR(io.BytesIO(page_bytes))
        writer.add_page(reader.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)
```

- [ ] **Schritt 3: Cover-Test ausführen**

```bash
~/.academic-research/venv/bin/python -m pytest /Users/j65674/Repos/academic-research-v6.3-B/tests/test_notebook_bundle.py::TestCoverPage -v 2>&1
```

Erwartetes Ergebnis: `PASSED` für `test_cover_contains_all_papers`. Andere Tests noch `ERROR` (bundle fehlt).

- [ ] **Schritt 4: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add skills/notebook-bundle/scripts/
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "feat(v6.3-B): cover_pdf.py — Bibliographie-Cover via PyPDF2-Stream-Injection"
```

---

## Task 4: `bundle.py` implementieren (GREEN für alle Tests)

**Files:**
- Create: `skills/notebook-bundle/scripts/bundle.py`

- [ ] **Schritt 1: `bundle.py` schreiben**

Datei: `skills/notebook-bundle/scripts/bundle.py`
```python
"""NotebookLM-Bundle — konkateniert PDFs zu einem Bundle für manuellen Upload.

CLI:
    python bundle.py <selection_json> [--output <path>] [--output-dir <dir>]
                     [--size-limit-mb <N>]

Rückgabe von build_bundle():
    {
        "status": "ok" | "split" | "partial",
        "output_files": ["/path/to/bundle.pdf"],
        "skipped_ids": ["paper_id", ...],
        "skipped_count": N,
        "total_pages": N,
    }
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, DecodedStreamObject, DictionaryObject

# Importiere cover_pdf aus demselben Verzeichnis
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))
from cover_pdf import generate_cover  # noqa: E402


# 500 MB Standard-Limit
DEFAULT_SIZE_LIMIT_MB = 500


def _make_toc_page(papers: List[Dict[str, Any]], page_numbers: List[int]) -> bytes:
    """Erzeugt TOC-Seite als PDF.

    Args:
        papers: Paper-Dicts (title, authors, year).
        page_numbers: Seitennummer (1-basiert) jedes Papers im Bundle.

    Returns:
        PDF-Bytes der TOC-Seite.
    """
    from PyPDF2 import PdfWriter as _W

    PAGE_WIDTH = 595
    PAGE_HEIGHT = 842

    writer = _W()
    page = writer.add_blank_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

    lines = ["BT"]
    y = PAGE_HEIGHT - 60

    # Titel
    lines.append(f"/Helvetica 16 Tf")
    lines.append(f"50 {y} Td")
    lines.append("(Inhaltsverzeichnis) Tj")
    lines.append("0 0 Td")
    y -= 40

    for i, (paper, pnum) in enumerate(zip(papers, page_numbers)):
        title = paper.get("title", "(kein Titel)")
        year = paper.get("year", "")
        safe_title = (
            title.replace("\\", "\\\\")
                 .replace("(", "\\(")
                 .replace(")", "\\)")
                 .replace("\n", " ")
        )
        entry = f"{i + 1}. {safe_title} ({year}) ............ S. {pnum}"
        safe_entry = (
            entry.replace("\\", "\\\\")
                 .replace("(", "\\(")
                 .replace(")", "\\)")
        )
        lines.append(f"/Helvetica 11 Tf")
        lines.append(f"50 {y} Td")
        lines.append(f"({safe_entry}) Tj")
        lines.append("0 0 Td")
        y -= 18

        if y < 60:
            break  # TOC zu lang für eine Seite — truncieren (genug für 5 Paper)

    lines.append("ET")
    stream_data = "\n".join(lines).encode("latin-1", errors="replace")

    stream_obj = DecodedStreamObject()
    stream_obj.set_data(stream_data)
    stream_ref = writer._add_object(stream_obj)
    page[NameObject("/Contents")] = stream_ref

    font_dict = DictionaryObject()
    font_dict[NameObject("/Type")] = NameObject("/Font")
    font_dict[NameObject("/Subtype")] = NameObject("/Type1")
    font_dict[NameObject("/BaseFont")] = NameObject("/Helvetica")
    font_ref = writer._add_object(font_dict)

    resources = DictionaryObject()
    font_resources = DictionaryObject()
    font_resources[NameObject("/Helvetica")] = font_ref
    resources[NameObject("/Font")] = font_resources
    page[NameObject("/Resources")] = resources

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def build_bundle(
    selection_json: str,
    output_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    size_limit_mb: float = DEFAULT_SIZE_LIMIT_MB,
) -> Dict[str, Any]:
    """Erzeugt NotebookLM-Bundle-PDF(s) aus einer Selektion.

    Args:
        selection_json: Pfad zur selection.json.
        output_path:    Expliziter Ausgabepfad (optional).
                        Wenn None, wird auto-Name unter output_dir generiert.
        output_dir:     Ausgabeverzeichnis für auto-Name (default: CWD).
        size_limit_mb:  Maximale Dateigröße pro Bundle in MB (default: 500).

    Returns:
        Dict mit status, output_files, skipped_ids, skipped_count, total_pages.
    """
    # 1. Selection laden
    selection_text = Path(selection_json).read_text(encoding="utf-8")
    selection = json.loads(selection_text)
    papers = selection.get("papers", [])

    # 2. PDFs prüfen
    valid_papers = []
    skipped_ids = []
    for paper in papers:
        pdf_path = paper.get("pdf_path", "")
        if pdf_path and Path(pdf_path).exists():
            valid_papers.append(paper)
        else:
            skipped_ids.append(paper.get("id", "unknown"))

    # 3. Cover erzeugen
    cover_buf = io.BytesIO()
    cover_path_tmp = cover_buf  # wir nutzen temp-BytesIO
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_cover_path = tmp.name
    generate_cover(valid_papers, tmp_cover_path)

    # 4. PDFs sammeln + Seitenzahlen tracken
    # Reihenfolge: TOC (Seite 1) + Cover + Paper
    # TOC wird am Ende hinzugefügt (Seiten noch unbekannt)
    cover_reader = PdfReader(tmp_cover_path)
    cover_pages = len(cover_reader.pages)

    paper_readers = []
    for paper in valid_papers:
        try:
            reader = PdfReader(paper["pdf_path"])
            paper_readers.append((paper, reader))
        except Exception:
            skipped_ids.append(paper.get("id", "unknown"))

    # Seitennummern berechnen (1-basiert, nach TOC=Seite 1 und Cover)
    # Seite 1 = TOC, Seiten 2..cover_pages+1 = Cover, dann Paper
    page_numbers = []
    current_page = 1 + cover_pages + 1  # TOC(1) + Cover-Seiten
    for paper, reader in paper_readers:
        page_numbers.append(current_page)
        current_page += len(reader.pages)

    # 5. TOC-Seite erzeugen
    toc_papers = [p for p, _ in paper_readers]
    toc_bytes = _make_toc_page(toc_papers, page_numbers)
    toc_reader = PdfReader(io.BytesIO(toc_bytes))

    # 6. Bundles aufbauen (Split bei >size_limit_mb)
    size_limit_bytes = size_limit_mb * 1024 * 1024
    output_files = []
    ts = _timestamp()

    def _make_output_path(part: Optional[int] = None) -> str:
        if output_path and part is None:
            return output_path
        base = output_dir or os.getcwd()
        if part is None:
            return str(Path(base) / f"notebook-bundle-{ts}.pdf")
        else:
            return str(Path(base) / f"notebook-bundle-{ts}-part{part}.pdf")

    # Wir schreiben Bundle(s)
    # Strategie: Starte mit TOC + Cover in Bundle 1, füge Paper hinzu.
    # Bei Größenüberschreitung neues Bundle beginnen.
    part = 1
    writer = PdfWriter()

    # TOC immer in Bundle 1
    for p in toc_reader.pages:
        writer.add_page(p)
    for p in cover_reader.pages:
        writer.add_page(p)

    def _flush_writer(w: PdfWriter, path: str) -> None:
        with open(path, "wb") as f:
            w.write(f)

    need_split = False
    for paper, reader in paper_readers:
        # Prüfe akkumulierte Größe
        tmp_buf = io.BytesIO()
        writer.write(tmp_buf)
        current_size = tmp_buf.tell()

        if current_size > size_limit_bytes and writer.pages:
            # Aktuellen Writer flushen, neuen starten
            out = _make_output_path(part)
            _flush_writer(writer, out)
            output_files.append(out)
            part += 1
            need_split = True
            writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

    # Letzten Writer flushen
    if writer.pages:
        out = _make_output_path(part if need_split else None)
        _flush_writer(writer, out)
        output_files.append(out)

    # Cleanup
    try:
        os.unlink(tmp_cover_path)
    except OSError:
        pass

    total_pages = sum(
        len(PdfReader(f).pages) for f in output_files
    )

    status = "split" if need_split else ("partial" if skipped_ids else "ok")

    return {
        "status": status,
        "output_files": output_files,
        "skipped_ids": skipped_ids,
        "skipped_count": len(skipped_ids),
        "total_pages": total_pages,
    }


def main() -> None:
    """CLI-Einstiegspunkt."""
    import argparse

    parser = argparse.ArgumentParser(
        description="NotebookLM-Bundle: Konkateniert PDFs für manuellen Upload."
    )
    parser.add_argument("selection_json", help="Pfad zur selection.json")
    parser.add_argument("--output", help="Expliziter Ausgabepfad")
    parser.add_argument("--output-dir", help="Ausgabeverzeichnis (auto-Name)")
    parser.add_argument(
        "--size-limit-mb",
        type=float,
        default=DEFAULT_SIZE_LIMIT_MB,
        help=f"Max. Bundle-Größe in MB (default: {DEFAULT_SIZE_LIMIT_MB})",
    )
    args = parser.parse_args()

    result = build_bundle(
        args.selection_json,
        output_path=args.output,
        output_dir=args.output_dir,
        size_limit_mb=args.size_limit_mb,
    )

    print(f"Status: {result['status']}")
    print(f"Output-Dateien:")
    for f in result["output_files"]:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  {f}  ({size_mb:.2f} MB, {len(PdfReader(f).pages)} Seiten)")
    if result["skipped_ids"]:
        print(f"Übersprungen ({result['skipped_count']}): {', '.join(result['skipped_ids'])}")


if __name__ == "__main__":
    main()
```

- [ ] **Schritt 2: Alle Tests ausführen**

```bash
~/.academic-research/venv/bin/python -m pytest /Users/j65674/Repos/academic-research-v6.3-B/tests/test_notebook_bundle.py -v 2>&1
```

Erwartetes Ergebnis: Alle 6 Tests `PASSED`.

- [ ] **Schritt 3: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add skills/notebook-bundle/scripts/bundle.py
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "feat(v6.3-B): bundle.py — PDF-Konkatenation + TOC + Split >500MB"
```

---

## Task 5: `SKILL.md` schreiben

**Files:**
- Create: `skills/notebook-bundle/SKILL.md`

- [ ] **Schritt 1: SKILL.md schreiben**

Datei: `skills/notebook-bundle/SKILL.md`
```markdown
---
name: notebook-bundle
description: >
  Verwende diesen Skill wenn der User ein NotebookLM-Bundle erstellen möchte.
  Trigger-Phrasen: "NotebookLM Bundle", "PDF-Bundle exportieren", "Bundle für Upload",
  "Bücher zu groß", "Riesen-PDF aufteilen", "NotebookLM vorbereiten".
  Erzeugt ein konkateniertes PDF aller ausgewählten Paper (mit Cover + TOC)
  für manuellen Upload in Google NotebookLM.
compatibility: Claude Code
license: MIT
---

# NotebookLM-Bundle Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke, bevor du fortfährst.

---

## ⚠️ WICHTIGER HINWEIS — KEINE VERBATIM-GARANTIE

**NotebookLM (Gemini) ist ein Triage-Tool, KEIN Zitat-Pfad.**

Antworten aus NotebookLM sind NICHT verbatim aus den Quellen zitiert und dürfen
NICHT als zitierfähige Quellen in wissenschaftlichen Arbeiten verwendet werden.

- Für verbatim-gesicherte Zitate: **Vault-Zitat-Pfad** (`vault.add_quote`) nutzen.
- Dieses Bundle dient der **Orientierung und Übersicht** — nicht als Belegen.
- NotebookLM-Antworten können sinngemäß korrekt, aber verbatim falsch sein.

---

## Übersicht

Erzeugt aus einer Paper-Selektion ein Bundle-PDF:
- Bibliographie-Cover als erste Seite(n)
- Inhaltsverzeichnis (TOC) als allererste Seite
- Alle PDFs konkateniert in TOC-Reihenfolge
- Bei >500MB: automatischer Split in mehrere Bundles

Output: `notebook-bundle-<ts>.pdf` — manuell in NotebookLM hochladen.

## Trigger-Erkennung

Aktiviert bei:
- "NotebookLM Bundle"
- "PDF-Bundle exportieren"
- "Bundle für Upload"
- "Bücher zu groß" / "Riesen-PDF aufteilen"
- "NotebookLM vorbereiten"

## Workflow

### 1. Paper-Selektion bereitstellen

Der User gibt entweder:

a) **Pfad zu `selection.json`:** Datei mit Paper-Liste
b) **Inline-JSON:** Paper-Block direkt in der Nachricht
c) **Cluster-Auswahl:** "Top-5 aus Cluster X" → Skill ruft `search_papers` auf

Erwartetes Schema der `selection.json`:
```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Titel des Papers",
      "authors": ["Smith, J."],
      "year": 2020,
      "pdf_path": "/absoluter/pfad/paper.pdf"
    }
  ]
}
```

### 2. Bundle bauen

```bash
python skills/notebook-bundle/scripts/bundle.py <selection.json> \
  --output-dir <projekt-verzeichnis>
```

Oder mit explizitem Output-Pfad:
```bash
python skills/notebook-bundle/scripts/bundle.py <selection.json> \
  --output <projekt>/notebook-bundle-<ts>.pdf
```

### 3. Ergebnis an User melden

Ausgabe:
- Pfad(e) zur Bundle-PDF
- Anzahl Seiten + Dateigröße
- Liste übersprungener Paper (fehlende PDFs)
- **Wiederholung der Verbatim-Warning**

Beispiel-Output:
```
Bundle erzeugt: /projekt/notebook-bundle-20260518T123456.pdf
Seiten: 152 | Größe: 18.4 MB
Übersprungen (0): —

⚠️  Erinnerung: NotebookLM-Antworten sind NICHT verbatim-garantiert.
Für Zitate: Vault-Zitat-Pfad nutzen.
```

## Abgrenzung

- Kein automatischer Upload nach NotebookLM — manuell durch User.
- Ersetzt nicht den Vault-Zitat-Pfad (verbatim-gesichert).
- Keine Konvertierung von non-PDF-Formaten.
- Keine Vault-DB-Einträge — Bundle ist reine Export-Funktion.
```

- [ ] **Schritt 2: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add skills/notebook-bundle/SKILL.md
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "feat(v6.3-B): SKILL.md — notebook-bundle Trigger + Verbatim-Warning + Workflow"
```

---

## Task 6: User-Doku schreiben

**Files:**
- Create: `docs/skills/notebook-bundle.md`

- [ ] **Schritt 1: `docs/skills/` Verzeichnis sicherstellen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.3-B/docs/skills
```

- [ ] **Schritt 2: Doku schreiben**

Datei: `docs/skills/notebook-bundle.md`
```markdown
# NotebookLM-Bundle — Benutzerhandbuch

## ⚠️ Wichtiger Hinweis: Keine Verbatim-Garantie

**Dieses Bundle ist ein Triage-Tool, kein Zitat-Pfad.**

NotebookLM (Google Gemini) liefert inhaltlich orientierte Antworten auf Basis
der hochgeladenen Quellen. Diese Antworten sind **nicht verbatim** aus den
Dokumenten zitiert und dürfen **nicht als belastbare Quellen** in
wissenschaftlichen Arbeiten verwendet werden.

Für verbatim-gesicherte Zitate nutze den **Vault-Zitat-Pfad** (`vault.add_quote`
über den `citation-extraction`-Skill).

---

## Wozu dient dieses Skill?

Bücher und Paper mit mehr als 600 PDF-Seiten überschreiten die Eingabegrenzen
der Anthropic-API. Google NotebookLM unterstützt bis zu 2 Millionen Token pro
Quelle (Source Grounding) und eignet sich zur Orientierung in großen Dokumenten.

Dieses Skill:
- Konkateniert bis zu N PDFs zu einem Bundle
- Fügt Bibliographie-Cover und Inhaltsverzeichnis ein
- Teilt das Bundle bei >500MB automatisch auf
- Erzeugt eine lokale PDF-Datei für manuellen Upload

---

## Voraussetzungen

- Python 3.x mit PyPDF2>=3.0.0 (in `scripts/requirements.txt` enthalten)
- Lokale PDF-Dateien der gewünschten Paper im Vault oder auf der Festplatte

---

## Schritt-für-Schritt: Bundle erstellen und hochladen

### Schritt 1: Paper-Selektion vorbereiten

Erstelle eine `selection.json` mit den gewünschten Papieren:

```json
{
  "papers": [
    {
      "id": "smith2020",
      "title": "Deep Learning for NLP",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2020,
      "pdf_path": "/pfad/zu/smith2020.pdf"
    },
    {
      "id": "jones2019",
      "title": "Transformer Architectures",
      "authors": ["Jones, B."],
      "year": 2019,
      "pdf_path": "/pfad/zu/jones2019.pdf"
    }
  ]
}
```

Alternativ: Claude Code direkt fragen:
> "Erstelle ein NotebookLM Bundle aus meinen Top-5 Papieren zu Deep Learning"

Claude wählt automatisch relevante Paper aus dem Vault aus.

### Schritt 2: Bundle bauen

```bash
python skills/notebook-bundle/scripts/bundle.py selection.json \
  --output-dir ./mein-projekt/
```

Oder über Claude Code:
> "Baue ein NotebookLM Bundle aus selection.json"

### Schritt 3: Bundle bei NotebookLM hochladen

1. Öffne [notebooklm.google.com](https://notebooklm.google.com)
2. Erstelle ein neues Notebook
3. Klicke auf **"+ Quelle hinzufügen"**
4. Wähle **"PDF"**
5. Lade `notebook-bundle-<timestamp>.pdf` hoch
6. Warte auf Indexierung (kann 1–5 Minuten dauern)

Bei mehreren Bundle-Dateien (Split >500MB): Lade jede Datei als separate Quelle hoch.

### Schritt 4: In NotebookLM arbeiten

NotebookLM erlaubt:
- Fragen zu den hochgeladenen Dokumenten
- Überblick über Themen und Argumente
- Zusammenfassungen von Kapiteln

**Denke daran:** NotebookLM-Antworten sind sinngemäß, nicht verbatim.
Für Zitate ins Vault zurückgehen.

---

## Bundle-Struktur

Das erzeugte Bundle-PDF ist wie folgt aufgebaut:

```
Seite 1:       Inhaltsverzeichnis (TOC) mit Seitennummern
Seiten 2–N:    Bibliographie-Cover (alle Paper mit Autoren + Jahr)
Seiten N+1–:   Paper 1, Paper 2, Paper 3, ... (in TOC-Reihenfolge)
```

---

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| PDF nicht gefunden | `pdf_path` prüfen — absoluter Pfad empfohlen |
| Bundle >500MB | Skill teilt automatisch auf; mehrere Dateien hochladen |
| NotebookLM-Upload schlägt fehl | PDF-Integrität prüfen: `python -c "from PyPDF2 import PdfReader; PdfReader('bundle.pdf')"` |
| Zu viele Paper für ein Bundle | `--size-limit-mb 400` für konservativeres Limit nutzen |

---

## Verwandte Skills

- `citation-extraction` — Verbatim-gesicherte Zitate aus dem Vault
- `cluster-visualizer` — Literatur-Cluster visualisieren (Top-N-Auswahl)
- `book-handler` — Einzelne Bücher als Quelle verarbeiten
```

- [ ] **Schritt 3: Commit**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B add docs/skills/notebook-bundle.md
git -C /Users/j65674/Repos/academic-research-v6.3-B commit -m "docs(v6.3-B): User-Doku notebook-bundle mit NotebookLM-Upload-Flow"
```

---

## Task 7: Vollständige Testsuite ausführen + Polish

- [ ] **Schritt 1: Alle notebook-bundle Tests laufen lassen**

```bash
~/.academic-research/venv/bin/python -m pytest /Users/j65674/Repos/academic-research-v6.3-B/tests/test_notebook_bundle.py -v 2>&1
```

Erwartetes Ergebnis: Alle 6 Tests `PASSED`, 0 Fehler.

- [ ] **Schritt 2: Gesamte Testsuite ausführen (Regressionscheck)**

```bash
~/.academic-research/venv/bin/python -m pytest /Users/j65674/Repos/academic-research-v6.3-B/tests/ -v --ignore=/Users/j65674/Repos/academic-research-v6.3-B/tests/evals/ 2>&1 | tail -30
```

Erwartetes Ergebnis: Keine neuen Failures (known failure `test_token_reduction[chapter-writer]` ist OK).

- [ ] **Schritt 3: Final-Commit falls nötig**

```bash
git -C /Users/j65674/Repos/academic-research-v6.3-B status
```

Falls ungestagete Änderungen: committen. Sonst weiter.

---

## Selbst-Review Checkliste (Spec B.md vs. Plan)

| Anforderung | Task |
|-------------|------|
| 5 Paper × 30 S. → 1 Bundle-PDF | Task 4 (`build_bundle`) |
| Bibliographie-Cover-PDF | Task 3 (`generate_cover`) |
| TOC mit Seitennummern | Task 4 (`_make_toc_page`) |
| Output `notebook-bundle-<ts>.pdf` | Task 4 (`_timestamp`) |
| >500MB Split | Task 4 (size_limit_bytes Loop) |
| Fehlende PDFs überspringen | Task 4 (skipped_ids) |
| SKILL.md mit Verbatim-Warning | Task 5 |
| User-Doku mit Upload-Flow | Task 6 |
| Tests ≥6 | Task 2 (6 Tests) |
| PyPDF2-only, kein reportlab | Task 3+4 (stream-injection) |
