# Spec C — F2.3 Seitenmapping page_offset + printed_page

Ticket: #73
Chunk: C
Datum: 2026-05-13

## Problem

Citations-API liefert `start_page_number` als PDF-Seite (1-basiert ab erster PDF-Seite).
Bei Buechern mit Vorwort/Inhaltsverzeichnis (oft 5–30 Seiten) stimmt diese
Seitenzahl nicht mit der gedruckten Seitenzahl ueberein. Halluzinierte Seitenangaben
sind Top-3-Fehler.

## Loesung (gewaehlter Ansatz)

PyPDF2/pypdf-Text-Extraktion + Regex auf Seiten 1–30 des PDFs. Kein LLM-Aufruf noetig:

- Einfacher, deterministisch testbar, billig.
- Regex sucht nach dem Muster "erste gedruckte Seite 1" (arabisch).
- Roemische Ziffern und Doppelpaginierung: gesondert behandelt.

## Komponenten

### 1. `scripts/page_offset.py` (CREATE)

Funktionen:
- `detect_page_offset(pdf_path: str, sample_pages: int = 30) -> int`
  - Oeffnet PDF, iteriert ueber die ersten `sample_pages` Seiten
  - Extrahiert Text jeder Seite (pypdf `extract_text()`)
  - Sucht via Regex nach isolierter Ziffer "1" als Seitennummer (unten/oben auf Seite)
  - Regex-Pattern: `r'\b1\b'` auf der letzten/ersten Zeile des extrahierten Textes
  - Gibt `pdf_page_index - 1` zurueck (pdf_page_index = 0-basiert, +1 fuer 1-basiert)
  - Fallback: 0 (kein Offset erkannt)
- `validate_offset(pdf_path: str, offset: int, check_pages: list[int] = None) -> bool`
  - Prueft 2 weitere Stichproben (z.B. pdf-Seiten offset+5, offset+10)
  - Gibt True wenn Stichproben konsistent mit offset

Kein LLM-Aufruf. Nur pypdf + re.

### 2. `mcp/academic_vault/db.py` (MODIFY — additiv)

Neue Methoden:
- `set_page_offset(paper_id: str, offset: int) -> None`
  - UPDATE papers SET page_offset = ?, updated_at = ? WHERE paper_id = ?
- `get_page_offset(paper_id: str) -> int`
  - SELECT page_offset FROM papers WHERE paper_id = ?
  - Gibt 0 zurueck wenn paper nicht gefunden

### 3. `mcp/academic_vault/server.py` (MODIFY — additiv)

Neue reine Funktionen + MCP-Tools:
- `set_page_offset(db_path, paper_id, offset) -> None`
- `get_printed_page(db_path, paper_id, pdf_page) -> int`
  - `printed_page = pdf_page - offset`
  - Nutzt `db.get_page_offset(paper_id)`
- MCP-Tools: `vault.set_page_offset`, `vault.get_printed_page`

### 4. `skills/book-handler/SKILL.md` (MODIFY)

Schritt 2.5 nach Vault-Eintrag einfuegen:
- Wenn PDF vorhanden: `python scripts/page_offset.py {pdf_path}` aufrufen
- Offset via `vault.set_page_offset(paper_id, offset)` speichern
- Baseline-Bump: book-handler baseline 4220 -> 4320 (+100 fuer neuen Schritt)

### 5. `skills/citation-extraction/SKILL.md` (MODIFY)

Im Abschnitt "Citations-API / Output-Integration":
- Erwaehnen: bei Buechern `printed_page = api.start_page_number - page_offset`
- `vault.get_printed_page(paper_id, pdf_page)` aufrufen
- Dateigroesse MUSS <= 9896 bleiben (baseline 11296, delta >= 1400)
- Minimal: 1 Satz (~80 Zeichen) einfuegen an stelle kuerzen wo moeglich

### 6. `tests/test_page_offset.py` (CREATE)

5 Testfaelle (synthetische PDFs via reportlab):
1. Buch ohne Vorwort: erste PDF-Seite = gedruckte Seite 1 → offset=0
2. Buch mit 10 Vorseiten: PDF-Seite 11 = gedruckte Seite 1 → offset=10
3. Buch mit roemischen Ziffern: erste arabische "1" auf PDF-Seite 7 → offset=6
4. Buch mit Doppelpaginierung: nur arabische Seiten zaehlen → offset=5
5. Validierungs-Test: validate_offset prueft 2 Stichproben

### 7. `tests/fixtures/page_offset/` (CREATE)

5 kleine PDF-Dateien (erzeugt von einem Generator-Skript via reportlab):
- `no_preface.pdf` — Seite 1 auf PDF-Seite 1
- `ten_prefaces.pdf` — Seite 1 auf PDF-Seite 11
- `roman_numerals.pdf` — i, ii, iii auf PDF-Seiten 1-3, dann "1" auf PDF-Seite 4
- `double_pagination.pdf` — Seite 1 auf PDF-Seite 6
- `create_fixtures.py` — Generator-Skript (wird im Fixture-Setup oder manuell aufgerufen)

## Constraints

- `page_offset` Spalte in DB existiert seit v5.x → keine Schema-Migration noetig
- book-handler baseline anpassen: von 4220 auf 4320 (neuer Schritt +100 chars)
- citation-extraction MUSS <= 9896 chars bleiben
- pypdf (nicht PyPDF2) verwenden — nur pypdf ist installiert
- Tests via `/opt/homebrew/bin/pytest`
- Keine LLM-Aufrufe in page_offset.py — deterministisch

## Acceptance Criteria

- [ ] 5 synthetische PDFs mit verschiedenen Paginierungs-Mustern; printed_page korrekt in 5/5
- [ ] `vault.set_page_offset` / `vault.get_printed_page` als MCP-Tools verfuegbar
- [ ] `test_token_reduction[book-handler]` und `test_token_reduction[citation-extraction]` gruen
- [ ] Alle bestehenden Tests weiterhin gruen
