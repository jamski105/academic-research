# Chunk D — F2.4: OCR-Detection und Trigger-Workflow für Scan-PDFs

## Ticket

\#74 — v6.1 · F2.4

## Ziel

Scan-PDFs ohne Text-Layer werden erkannt, bevor `quote-extractor` lautlos scheitert.
Der User wird um Erlaubnis gefragt und OCR via `ocrmypdf` wird optional lokal ausgefuehrt.
Nach erfolgreichem OCR-Lauf wird der neue PDF-Pfad und `ocr_done=1` im Vault gespeichert.

## Deliverables

### 1. `scripts/pdf.py` (MODIFY)

Neue Funktion:

```python
def detect_needs_ocr(pdf_path: str, sample_pages: int = 5, threshold: int = 100) -> bool:
    """Prueft ob ein PDF OCR benoetigt.

    Liest bis zu sample_pages zufaellig verteilte Seiten via PyPDF2.
    Gibt True zurueck wenn der Durchschnitt der extrahierten Zeichen
    je Seite < threshold (Standard: 100).
    Bei leeren PDFs (0 Seiten) gibt die Funktion True zurueck.
    """
```

Kein neues CLI-Subkommando noetig — die Funktion ist eine reine Hilfsfunktion
fuer andere Aufrufer (ocr.py, book-handler SKILL, Tests).

### 2. `scripts/ocr.py` (CREATE)

```python
def run_ocrmypdf(input_pdf: str, output_pdf: str) -> None:
    """Fuehrt ocrmypdf auf input_pdf aus und schreibt Ergebnis nach output_pdf.

    Prueft via subprocess.which ob ocrmypdf im PATH vorhanden.
    Raises RuntimeError mit Install-Hinweis wenn nicht vorhanden:
      "ocrmypdf nicht gefunden. Installation: brew install ocrmypdf
       oder pip install ocrmypdf"

    Fuehrt aus: ocrmypdf --skip-text <input_pdf> <output_pdf>
    --skip-text: ueberspringt Seiten die bereits Text haben (sicher fuer gemischte PDFs).
    Raises RuntimeError wenn Prozess mit Exit-Code != 0 endet.
    """
```

### 3. `skills/book-handler/SKILL.md` (MODIFY — minimal)

Neuer Abschnitt **„5. OCR-Pruefung (optional)"** nach dem OA-Check:

```
### 5. OCR-Pruefung (optional)

Falls pdf_path gesetzt:
  python scripts/pdf.py (via detect_needs_ocr) ausfuehren.
  Bei Verdacht auf fehlenden Text-Layer:

  User-Prompt ausgeben:
    "Scan-PDF erkannt: wenig Text auf Stichproben-Seiten.
     OCR ausfuehren? (~30 s/Seite, lokal via ocrmypdf) [j/n]"

  Bei Zustimmung:
    python scripts/ocr.py ausfuehren (run_ocrmypdf).
    vault.set_ocr_done(paper_id)
    vault.update_pdf_path(paper_id, neuer_pfad)
    User bestaetigen: "OCR abgeschlossen. Neuer Pfad: {pfad}"

  Bei Ablehnung:
    Hinweis: "quote-extractor koennte fehlschlagen (kein Text-Layer)"
```

Token-Budget: SKILL.md baseline ist 4220 Zeichen. Der neue Abschnitt darf
maximal +400 Zeichen hinzufuegen (neue Gesamtgroesse <= 4620).
Baseline-Datei `tests/baselines/skill_sizes.json` wird entsprechend angepasst.

### 4. `mcp/academic_vault/server.py` (MODIFY — additiv)

Zwei neue reine Funktionen (kein Schema-Change):

```python
def set_ocr_done(db_path: str, paper_id: str, value: int = 1) -> None:
    """Setzt ocr_done-Flag fuer paper_id (bestehende Spalte nutzen)."""

def update_pdf_path(db_path: str, paper_id: str, new_path: str) -> None:
    """Aktualisiert pdf_path fuer paper_id."""
```

Beide als MCP-Tools exponieren: `vault.set_ocr_done`, `vault.update_pdf_path`.

### 5. `mcp/academic_vault/db.py` (MODIFY — additiv)

Zwei neue Methoden in `VaultDB`:

```python
def set_ocr_done(self, paper_id: str, value: int = 1) -> None:
    """UPDATE papers SET ocr_done = value WHERE paper_id = ?"""

def update_pdf_path(self, paper_id: str, new_path: str) -> None:
    """UPDATE papers SET pdf_path = new_path WHERE paper_id = ?"""
```

### 6. `README.md` (MODIFY)

Optionale Abhaengigkeit `ocrmypdf` in bestehenden Abschnitt „Abhaengigkeiten"
aufnehmen:

```markdown
**Optional:**
- `ocrmypdf` (OCR fuer Scan-PDFs ohne Text-Layer):
  - macOS: `brew install ocrmypdf`
  - Python: `pip install ocrmypdf`
```

### 7. `tests/test_ocr_detection.py` (CREATE)

Tests (alle via Mocks, keine echte OCR):

- `test_detect_needs_ocr_text_pdf` — PDF mit viel Text → `False`
- `test_detect_needs_ocr_scan_pdf` — PDF mit leerem Text-Layer → `True`
- `test_detect_needs_ocr_mixed_pdf` — Mischung aus Text/Scan-Seiten → `True` (Durchschnitt < 100)
- `test_detect_needs_ocr_empty_pdf` — 0 Seiten → `True`
- `test_run_ocrmypdf_not_found` — `subprocess.which` gibt None → `RuntimeError`
- `test_run_ocrmypdf_success` — Prozess laeuft durch → kein Fehler
- `test_run_ocrmypdf_failure` — Prozess Exit-Code != 0 → `RuntimeError`
- `test_set_ocr_done` — Vault-Setter setzt `ocr_done=1`
- `test_update_pdf_path` — Vault-Setter aktualisiert `pdf_path`

### 8. `tests/fixtures/ocr/` (CREATE)

Kleine Fixture-PDFs (< 50 KB jeweils):

- `scan_no_text.pdf` — minimales PDF ohne Text-Layer (nur leere Seiten via PyPDF2)
- `text_document.pdf` — minimales PDF mit Text-Inhalt

Da PyPDF2 keine Bild-Only-PDFs erzeugt, werden Fixtures programmatisch
erstellt: `scan_no_text.pdf` hat Seiten mit `extract_text() == ""`.
Dies wird im Test per Mock simuliert — die Fixtures dienen als valide
PDF-Dateien fuer Datei-Existenz-Pruefungen; die Text-Layer-Simulation
erfolgt via Mock in den Unit-Tests.

## Schnittstellen-Kontrakt

```
detect_needs_ocr(pdf_path: str, sample_pages: int = 5, threshold: int = 100) -> bool
run_ocrmypdf(input_pdf: str, output_pdf: str) -> None  # raises RuntimeError
set_ocr_done(db_path, paper_id, value=1) -> None
update_pdf_path(db_path, paper_id, new_path) -> None
```

## Akzeptanzkriterien

- [ ] `detect_needs_ocr` erkennt Text-PDF korrekt (False) und Scan-PDF (True)
- [ ] `run_ocrmypdf` prueft PATH und gibt RuntimeError mit Hinweis wenn fehlt
- [ ] `set_ocr_done` und `update_pdf_path` persistieren korrekt in Vault-DB
- [ ] SKILL.md erhaelt OCR-Abschnitt, Token-Budget eingehalten (< +400 Zeichen)
- [ ] Alle neuen Tests grueen, bestehende Tests unveraendert grueen

## Abhaengigkeiten

- Chunk A gemergt (schema.sql mit `ocr_done`-Spalte, VaultDB-Muster)
- PyPDF2 bereits in `scripts/requirements.txt` vorhanden
- `ocrmypdf` bleibt optionale Tool-Dep (kein Python-Import, nur subprocess)
