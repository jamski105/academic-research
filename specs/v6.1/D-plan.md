# F2.4 OCR-Detection + ocrmypdf-Workflow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scan-PDFs ohne Text-Layer erkennen, User-Prompt ausgeben, OCR via ocrmypdf ausfuehren und Ergebnis im Vault persistieren.

**Architecture:** `detect_needs_ocr()` in `scripts/pdf.py` sampelt zufaellige Seiten via PyPDF2. `scripts/ocr.py` wrappt `ocrmypdf` als optionale CLI-Dep. Vault bekommt zwei additive Setter (`set_ocr_done`, `update_pdf_path`). `skills/book-handler/SKILL.md` erhaelt einen neuen OCR-Abschnitt (minimal, Token-Budget beachten). Tests mocken PyPDF2 und subprocess vollstaendig — keine echte OCR noetig.

**Tech Stack:** Python 3.x, PyPDF2, subprocess.which, pytest, SQLite via VaultDB

---

### Task 1: Fixture-PDFs erstellen

**Files:**
- Create: `tests/fixtures/ocr/scan_no_text.pdf`
- Create: `tests/fixtures/ocr/text_document.pdf`
- Create: `tests/fixtures/ocr/create_fixtures.py` (Hilfsskript, nicht getestet)

- [ ] **Step 1: Hilfsskript schreiben**

Erstelle `tests/fixtures/ocr/create_fixtures.py`:

```python
#!/usr/bin/env python3
"""Erzeugt minimale Test-Fixture-PDFs fuer OCR-Tests."""
import sys
import os

# Minimales PDF ohne Text (nur Seiten-Struktur) via PyPDF2
from PyPDF2 import PdfWriter


def create_empty_pdf(path: str, pages: int = 3) -> None:
    """PDF mit leeren Seiten (kein Text-Layer)."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def create_text_pdf(path: str) -> None:
    """PDF mit Text-Inhalt via reportlab (Fallback: leere Seiten mit Dummy-Text via PyPDF2)."""
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(path)
        c.drawString(100, 750, "Dies ist ein Test-Dokument mit ausreichend Text-Inhalt.")
        c.drawString(100, 700, "Zweite Zeile mit weiterem Text fuer die OCR-Erkennung.")
        c.drawString(100, 650, "Dritte Zeile mit noch mehr Text damit die Erkennung klappt.")
        c.save()
    except ImportError:
        # Fallback: leeres PDF (wird in Tests ohnehin gemockt)
        create_empty_pdf(path, pages=2)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    base = os.path.dirname(os.path.abspath(__file__))
    create_empty_pdf(os.path.join(base, "scan_no_text.pdf"), pages=5)
    create_text_pdf(os.path.join(base, "text_document.pdf"))
    print("Fixtures erstellt.")
```

- [ ] **Step 2: Fixture-PDFs erzeugen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
mkdir -p tests/fixtures/ocr
python tests/fixtures/ocr/create_fixtures.py
ls -la tests/fixtures/ocr/
```

Erwartet: `scan_no_text.pdf` und `text_document.pdf` vorhanden, je < 50 KB.

---

### Task 2: `detect_needs_ocr` — RED-Phase (failing test)

**Files:**
- Create: `tests/test_ocr_detection.py` (Teilmenge — nur detect_needs_ocr Tests)

- [ ] **Step 1: Failing tests schreiben**

Erstelle `tests/test_ocr_detection.py`:

```python
"""Tests fuer OCR-Detection und ocrmypdf-Workflow."""
import os
import sys
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock, call

import pytest

# scripts/ im Suchpfad
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "ocr")


# ---------------------------------------------------------------------------
# detect_needs_ocr
# ---------------------------------------------------------------------------

class TestDetectNeedsOcr:
    """Tests fuer scripts.pdf.detect_needs_ocr."""

    def test_text_pdf_returns_false(self):
        """PDF mit viel Text → False (kein OCR noetig)."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 200  # 200 Zeichen pro Seite

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 10

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is False

    def test_scan_pdf_returns_true(self):
        """PDF ohne Text-Layer → True (OCR benoetigt)."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # kein Text

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 10

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is True

    def test_mixed_pdf_returns_true(self):
        """Mischung: wenige Seiten mit Text, viele leer → True (Durchschnitt < 100)."""
        from pdf import detect_needs_ocr

        pages = []
        # 2 Seiten mit etwas Text, 8 Seiten leer → avg < 100
        for _ in range(2):
            p = MagicMock()
            p.extract_text.return_value = "A" * 50  # 50 Zeichen
            pages.append(p)
        for _ in range(8):
            p = MagicMock()
            p.extract_text.return_value = ""
            pages.append(p)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf", sample_pages=5, threshold=100)

        assert result is True

    def test_empty_pdf_returns_true(self):
        """PDF ohne Seiten → True."""
        from pdf import detect_needs_ocr

        mock_reader = MagicMock()
        mock_reader.pages = []

        with patch("pdf.PdfReader", return_value=mock_reader):
            result = detect_needs_ocr("dummy.pdf")

        assert result is True

    def test_sample_pages_capped_at_total(self):
        """Wenn sample_pages > Gesamtseiten, werden alle Seiten benutzt."""
        from pdf import detect_needs_ocr

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 50  # unter threshold

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page] * 3  # nur 3 Seiten

        with patch("pdf.PdfReader", return_value=mock_reader):
            # sample_pages=10 > 3 Seiten — soll nicht crashen
            result = detect_needs_ocr("dummy.pdf", sample_pages=10, threshold=100)

        assert result is True  # 50 < 100


class TestRunOcrmypdf:
    """Tests fuer scripts.ocr.run_ocrmypdf."""

    def test_ocrmypdf_not_found_raises_runtime_error(self):
        """subprocess.which gibt None → RuntimeError mit Install-Hinweis."""
        import importlib
        # ocr-Modul koennte noch nicht existieren → ImportError ist OK
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        with patch("subprocess.which", return_value=None):
            with pytest.raises(RuntimeError, match="ocrmypdf nicht gefunden"):
                run_ocrmypdf("input.pdf", "output.pdf")

    def test_ocrmypdf_success(self):
        """Erfolgreicher Aufruf — kein Fehler."""
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.which", return_value="/usr/local/bin/ocrmypdf"):
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                run_ocrmypdf("input.pdf", "output.pdf")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "ocrmypdf" in call_args[0]
        assert "input.pdf" in call_args
        assert "output.pdf" in call_args

    def test_ocrmypdf_failure_raises_runtime_error(self):
        """Prozess endet mit Exit-Code != 0 → RuntimeError."""
        try:
            from ocr import run_ocrmypdf
        except ImportError:
            pytest.skip("ocr.py noch nicht implementiert")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = b"OCR failed"

        with patch("subprocess.which", return_value="/usr/local/bin/ocrmypdf"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(RuntimeError, match="ocrmypdf"):
                    run_ocrmypdf("input.pdf", "output.pdf")


class TestVaultOcrSetters:
    """Tests fuer set_ocr_done und update_pdf_path in Vault."""

    @pytest.fixture
    def tmp_db(self, tmp_path):
        db_file = str(tmp_path / "vault.db")
        # Schema initialisieren
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp", "academic_vault"))
        from db import VaultDB
        db = VaultDB(db_file)
        db.init_schema()
        # Test-Paper anlegen
        db.add_paper(
            paper_id="test-paper-ocr",
            csl_json='{"type":"book","title":"Scan Test"}',
            pdf_path="/tmp/scan.pdf",
        )
        return db_file

    def test_set_ocr_done(self, tmp_db):
        """set_ocr_done setzt ocr_done=1 im Vault."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp", "academic_vault"))
        from server import set_ocr_done, get_paper

        set_ocr_done(tmp_db, "test-paper-ocr")
        paper = get_paper(tmp_db, "test-paper-ocr")

        assert paper is not None
        assert paper["ocr_done"] == 1

    def test_update_pdf_path(self, tmp_db):
        """update_pdf_path aktualisiert pdf_path im Vault."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp", "academic_vault"))
        from server import update_pdf_path, get_paper

        update_pdf_path(tmp_db, "test-paper-ocr", "/tmp/scan_ocr.pdf")
        paper = get_paper(tmp_db, "test-paper-ocr")

        assert paper is not None
        assert paper["pdf_path"] == "/tmp/scan_ocr.pdf"
```

- [ ] **Step 2: Tests ausfuehren — muessen scheitern**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_ocr_detection.py -v 2>&1 | head -50
```

Erwartet: Tests in `TestDetectNeedsOcr` schlagen fehl mit `ImportError` oder `AttributeError` (Funktion fehlt in pdf.py). Tests in `TestRunOcrmypdf` und `TestVaultOcrSetters` werden via `pytest.skip` oder ImportError uebersprungen.

---

### Task 3: `detect_needs_ocr` implementieren — GREEN-Phase

**Files:**
- Modify: `scripts/pdf.py` (neue Funktion am Ende des Moduls, vor CLI-Abschnitt)

- [ ] **Step 1: Funktion zu `scripts/pdf.py` hinzufuegen**

In `scripts/pdf.py` vor dem Kommentar `# ---------------------------------------------------------------------------\n# CLI` einfuegen:

```python
# ---------------------------------------------------------------------------
# OCR-Detection
# ---------------------------------------------------------------------------

def detect_needs_ocr(
    pdf_path: str,
    sample_pages: int = 5,
    threshold: int = 100,
) -> bool:
    """Prueft ob ein PDF OCR benoetigt.

    Liest bis zu sample_pages zufaellig verteilte Seiten via PyPDF2.
    Gibt True zurueck wenn der Durchschnitt der extrahierten Zeichen
    je Seite < threshold (Standard: 100 Zeichen).
    Bei leerem PDF (0 Seiten) gibt die Funktion True zurueck.
    """
    import random

    try:
        reader = PdfReader(pdf_path)
    except Exception:
        log.exception("detect_needs_ocr: konnte %s nicht oeffnen", pdf_path)
        return True  # Im Fehlerfall: OCR vorschlagen

    total_pages = len(reader.pages)
    if total_pages == 0:
        return True

    # Seiten-Indizes samplen
    n = min(sample_pages, total_pages)
    indices = random.sample(range(total_pages), n)

    total_chars = 0
    for i in indices:
        text = reader.pages[i].extract_text() or ""
        total_chars += len(text)

    avg_chars = total_chars / n
    return avg_chars < threshold
```

- [ ] **Step 2: Import sicherstellen**

`PdfReader` wird bereits in `extract_text_from_pdf` importiert (lokaler Import). Fuer `detect_needs_ocr` denselben Stil verwenden. Der Import von `random` erfolgt innerhalb der Funktion.

Pruefe, dass `from PyPDF2 import PdfReader` bereits in `extract_text_from_pdf` als lokaler Import vorhanden ist — falls ja, denselben Pattern in `detect_needs_ocr` verwenden. Alternativ: gemeinsamen Top-Level-Import.

Schaue auf Zeile 230 in `pdf.py`:
```python
from PyPDF2 import PdfReader
reader = PdfReader(pdf_path)
```
Der Import ist lokal in `extract_text_from_pdf`. Gleichen Stil in `detect_needs_ocr` beibehalten (lokaler Import mit `from PyPDF2 import PdfReader` direkt in der Funktion nach dem `import random`).

- [ ] **Step 3: Tests ausfuehren — muessen gruenwerden**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_ocr_detection.py::TestDetectNeedsOcr -v
```

Erwartet: Alle 5 Tests in `TestDetectNeedsOcr` PASS.

- [ ] **Step 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
git add scripts/pdf.py tests/test_ocr_detection.py tests/fixtures/ocr/
git commit -m "feat(F2.4): detect_needs_ocr in pdf.py + failing tests fuer ocr.py + vault-setter"
```

---

### Task 4: `scripts/ocr.py` erstellen — GREEN-Phase

**Files:**
- Create: `scripts/ocr.py`

- [ ] **Step 1: `scripts/ocr.py` erstellen**

```python
#!/usr/bin/env python3
"""OCR-Wrapper fuer ocrmypdf.

Optionale Abhaengigkeit: ocrmypdf muss im PATH vorhanden sein.
Installation: brew install ocrmypdf  ODER  pip install ocrmypdf
"""
from __future__ import annotations

import subprocess


def run_ocrmypdf(input_pdf: str, output_pdf: str) -> None:
    """Fuehrt ocrmypdf auf input_pdf aus und schreibt Ergebnis nach output_pdf.

    Prueft via subprocess.which ob ocrmypdf im PATH vorhanden.

    Args:
        input_pdf: Pfad zum Eingangs-PDF (Scan ohne Text-Layer).
        output_pdf: Pfad fuer das OCR-behandelte Ausgabe-PDF.

    Raises:
        RuntimeError: Wenn ocrmypdf nicht im PATH oder Prozess fehlschlaegt.
    """
    if subprocess.which("ocrmypdf") is None:
        raise RuntimeError(
            "ocrmypdf nicht gefunden. "
            "Installation: brew install ocrmypdf  ODER  pip install ocrmypdf"
        )

    result = subprocess.run(
        ["ocrmypdf", "--skip-text", input_pdf, output_pdf],
        capture_output=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(
            f"ocrmypdf fehlgeschlagen (Exit {result.returncode}): {stderr}"
        )
```

- [ ] **Step 2: Tests ausfuehren**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_ocr_detection.py::TestRunOcrmypdf -v
```

Erwartet: Alle 3 Tests in `TestRunOcrmypdf` PASS (kein `pytest.skip` mehr).

---

### Task 5: Vault-Setter in `db.py` und `server.py` — GREEN-Phase

**Files:**
- Modify: `mcp/academic_vault/db.py`
- Modify: `mcp/academic_vault/server.py`

- [ ] **Step 1: `db.py` — zwei neue Methoden in VaultDB**

In `mcp/academic_vault/db.py` am Ende der Klasse `VaultDB` (nach `find_quotes`) hinzufuegen:

```python
    def set_ocr_done(self, paper_id: str, value: int = 1) -> None:
        """Setzt ocr_done-Flag fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET ocr_done = ?, updated_at = ? WHERE paper_id = ?",
            (value, int(__import__("time").time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()

    def update_pdf_path(self, paper_id: str, new_path: str) -> None:
        """Aktualisiert pdf_path fuer ein Paper."""
        conn = self._get_conn()
        own_conn = self._conn is None
        conn.execute(
            "UPDATE papers SET pdf_path = ?, updated_at = ? WHERE paper_id = ?",
            (new_path, int(__import__("time").time()), paper_id),
        )
        if own_conn:
            conn.commit()
            conn.close()
```

- [ ] **Step 2: `server.py` — zwei neue Funktionen + MCP-Tools**

In `mcp/academic_vault/server.py` nach der Funktion `get_stats` (vor `_build_mcp_server`) hinzufuegen:

```python
def set_ocr_done(db_path: str, paper_id: str, value: int = 1) -> None:
    """Setzt ocr_done-Flag fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.set_ocr_done(paper_id, value)


def update_pdf_path(db_path: str, paper_id: str, new_path: str) -> None:
    """Aktualisiert pdf_path fuer ein Paper im Vault."""
    db = VaultDB(db_path)
    db.update_pdf_path(paper_id, new_path)
```

In `_build_mcp_server()`, nach dem `vault.stats`-Tool, zwei neue Tools registrieren:

```python
    @mcp.tool(name="vault.set_ocr_done")
    def _vault_set_ocr_done(paper_id: str, value: int = 1) -> None:
        """Setzt ocr_done-Flag (1=OCR durchgefuehrt) fuer ein Paper."""
        set_ocr_done(db_path, paper_id, value)

    @mcp.tool(name="vault.update_pdf_path")
    def _vault_update_pdf_path(paper_id: str, new_path: str) -> None:
        """Aktualisiert den PDF-Pfad nach OCR."""
        update_pdf_path(db_path, paper_id, new_path)
```

- [ ] **Step 3: Tests ausfuehren**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_ocr_detection.py -v
```

Erwartet: Alle Tests PASS (inkl. `TestVaultOcrSetters`).

- [ ] **Step 4: Alle bestehenden Tests noch gruen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/ --ignore=tests/test_skills_manifest.py -q
```

Erwartet: Alle bisherigen Tests PASS + neue Tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
git add scripts/ocr.py mcp/academic_vault/db.py mcp/academic_vault/server.py
git commit -m "feat(F2.4): ocr.py Wrapper + Vault set_ocr_done/update_pdf_path"
```

---

### Task 6: `skills/book-handler/SKILL.md` — OCR-Abschnitt

**Files:**
- Modify: `skills/book-handler/SKILL.md`
- Modify: `tests/baselines/skill_sizes.json`

- [ ] **Step 1: Aktuelle Groesse pruefen**

```bash
wc -c /Users/j65674/Repos/academic-research-v6.1-D/skills/book-handler/SKILL.md
```

Erwartet: ~4220 Zeichen (Baseline in `skill_sizes.json`). Neuer Abschnitt darf <= 400 Zeichen hinzufuegen.

- [ ] **Step 2: OCR-Abschnitt in SKILL.md einfuegen**

In `skills/book-handler/SKILL.md` den Abschnitt `### 4. Nachfolge-Hinweise` ersetzen:

Aktueller Text (Zeilen 68-71):
```markdown
### 4. Nachfolge-Hinweise

Nach erfolgreichem Vault-Eintrag dem User anbieten:
- Kapitel extrahieren? -> F2.2: `chunk_pdf.py`
- Scan-PDF (kein Text)? -> F2.4: OCR-Detection
```

Ersetzen durch:
```markdown
### 4. Nachfolge-Hinweise

Nach erfolgreichem Vault-Eintrag dem User anbieten:
- Kapitel extrahieren? -> F2.2: `chunk_pdf.py`
- Scan-PDF (kein Text)? -> Schritt 5 ausfuehren

### 5. OCR-Pruefung (bei pdf_path vorhanden)

```python
from pdf import detect_needs_ocr
if detect_needs_ocr(pdf_path):
    # User fragen:
    # "Scan-PDF erkannt: wenig Text auf Stichproben-Seiten.
    #  OCR ausfuehren? (~30 s/Seite, lokal via ocrmypdf) [j/n]"
    # Bei Zustimmung:
    from ocr import run_ocrmypdf
    run_ocrmypdf(pdf_path, pdf_path_ocr)
    vault.set_ocr_done(paper_id)
    vault.update_pdf_path(paper_id, pdf_path_ocr)
```
```

**WICHTIG:** Den eingebetteten Backtick-Block korrekt escapen — triple backticks werden innerhalb von SKILL.md-Markdown als Code-Block verwendet; sicherstellen dass der Block korrekt geschlossen ist.

- [ ] **Step 3: Neue Groesse messen und Baseline aktualisieren**

```bash
NEW_SIZE=$(wc -c < /Users/j65674/Repos/academic-research-v6.1-D/skills/book-handler/SKILL.md)
echo "Neue Groesse: $NEW_SIZE"
```

Wenn `NEW_SIZE > 4620` (d.h. > 4220 + 400): SKILL.md kuerzeln bis Budget eingehalten.

Dann `tests/baselines/skill_sizes.json` aktualisieren:
```json
{
  "book-handler": <NEW_SIZE>,
  ...
}
```
(Nur den `book-handler`-Eintrag aendern, alle anderen unveraendert lassen.)

- [ ] **Step 4: Token-Reduction-Test pruefen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -k "book-handler" -v
```

Erwartet: PASS (book-handler ueberschreitet Budget nicht).

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
git add skills/book-handler/SKILL.md tests/baselines/skill_sizes.json
git commit -m "feat(F2.4): OCR-Hinweis-Abschnitt in book-handler SKILL.md"
```

---

### Task 7: README.md aktualisieren

**Files:**
- Modify: `README.md`

- [ ] **Step 1: README.md lesen um bestehende Abhaengigkeits-Sektion zu finden**

```bash
grep -n "Abhaengigkeit\|Abhängigkeit\|requirements\|Requirements\|Install\|brew\|pip" \
  /Users/j65674/Repos/academic-research-v6.1-D/README.md | head -20
```

- [ ] **Step 2: ocrmypdf-Hinweis einfuegen**

Den gefundenen Abhaengigkeits-Abschnitt um folgendes erweitern (nach vorhandenen optionalen Deps oder am Ende des Abschnitts):

```markdown
**Optional:**
- `ocrmypdf` (OCR fuer Scan-PDFs ohne Text-Layer):
  - macOS: `brew install ocrmypdf`
  - Python-basiert: `pip install ocrmypdf`
```

Falls kein dedizierter Abschnitt existiert, neuen Abschnitt `## Optionale Abhaengigkeiten` vor `## Nutzung` oder am Ende einfuegen.

- [ ] **Step 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
git add README.md
git commit -m "docs(F2.4): ocrmypdf optionale Dep in README"
```

---

### Task 8: Vollstaendiger Test-Lauf + Code-Review

- [ ] **Step 1: Vollstaendige Test-Suite**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/ --ignore=tests/test_skills_manifest.py -v 2>&1 | tail -20
```

Erwartet: Alle Tests PASS. Keine Regressionen.

- [ ] **Step 2: test_skills_manifest.py fuer book-handler**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
/opt/homebrew/bin/pytest tests/test_skills_manifest.py -k "book-handler" -v
```

Erwartet: PASS.

- [ ] **Step 3: Code-Review via Skill**

`superpowers:requesting-code-review` ausfuehren auf dem Diff vs. main.

- [ ] **Step 4: Finaler Commit falls noetig**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-D
git diff --stat HEAD
```

---

## Selbst-Review der Plan-Vollstaendigkeit

Spec-Anforderungen vs. Plan-Abdeckung:

| Spec-Requirement | Task |
|---|---|
| `detect_needs_ocr` in `scripts/pdf.py` | Task 3 |
| `scripts/ocr.py` mit `run_ocrmypdf` | Task 4 |
| `set_ocr_done` + `update_pdf_path` in `db.py` | Task 5 |
| `set_ocr_done` + `update_pdf_path` in `server.py` | Task 5 |
| MCP-Tools `vault.set_ocr_done` + `vault.update_pdf_path` | Task 5 |
| `skills/book-handler/SKILL.md` OCR-Abschnitt | Task 6 |
| `README.md` ocrmypdf Hinweis | Task 7 |
| `tests/test_ocr_detection.py` | Task 2 (Struktur) + Tasks 3–5 (Impl) |
| `tests/fixtures/ocr/` Fixture-PDFs | Task 1 |
| Token-Budget SKILL.md eingehalten | Task 6 Step 3–4 |
| Baseline `skill_sizes.json` aktualisiert | Task 6 Step 3 |

Alle Spec-Anforderungen sind abgedeckt.
