# Chunk B — F2.2: Kapitel-Schnitt aus Buch-PDFs (PyPDF2 Outline-Tree)

## Ticket

\#72 — v6.1 · F2.2

## Ziel

Grosse Buch-PDFs (600+ Seiten) so zerlegen, dass pro Kapitel ein separates PDF
entsteht. Damit sinkt der Token-Footprint je API-Call von bis zu 600 Seiten auf
typisch < 30 Seiten pro Kapitel.

## Deliverables

### 1. `scripts/chunk_pdf.py`

CLI-Skript mit Subkommando-Stil:

```
python scripts/chunk_pdf.py \
  --input book.pdf \
  --chapter <n|toc|all> \
  --output <pfad-oder-verzeichnis>
```

**Kapitel-Erkennung (Prioritaet):**

1. **PyPDF2 Outline-Tree** (`PdfReader.outline`) — iteriert die Struktur,
   mappt Kapitel auf Seitenbereiche, schreibt PDFs via `PdfWriter`.
2. **Fallback: TOC-Textextraktion** — liest die ersten 20 Seiten, sucht per
   Regex nach Kapitelzeilen (`Kapitel N`, `Chapter N`, `\d+\.\s+\w+`) inkl.
   Seitenzahlen. Wird aktiviert wenn Outline-Tree leer ist.

**Ausgabe-Konvention:**

- `--chapter all` → alle Kapitel nach `<session>/pdfs/<isbn>-ch<n>.pdf`
  (oder `<output_dir>/<isbn>-ch<n>.pdf`)
- `--chapter N` → einzelnes Kapitel nach `--output`-Pfad
- `--chapter toc` → Gibt nur JSON-TOC aus (Kapitel-Nummern + Seiten)

**Fehlerverhalten:**
- Kein Outline UND kein TOC-Text gefunden → `SystemExit(2)` mit klarer
  Meldung, keine leeren PDFs.

### 2. `mcp/academic_vault/schema.sql`

Neue Spalte in `papers`:

```sql
parent_paper_id TEXT REFERENCES papers(paper_id)
```

Idempotent in `CREATE TABLE IF NOT EXISTS`-Block aufgenommen.

### 3. `mcp/academic_vault/migrate.py`

Neue Funktion `add_parent_paper_id_column(db_path)`:

- Pattern identisch zu `add_book_columns()` — `ALTER TABLE papers ADD COLUMN`
  in try/except auf `OperationalError`.
- Wird von `main()` bei Bedarf aufgerufen (opt-in Flag `--add-parent`).

### 4. `mcp/academic_vault/db.py`

`add_paper()` um Parameter `parent_paper_id: Optional[str] = None`
erweitern — sowohl in INSERT als auch in ON CONFLICT DO UPDATE.

### 5. `mcp/academic_vault/server.py`

- `add_paper()` um `parent_paper_id` erweitern.
- Neue Hilfsfunktion `add_chapter(parent_paper_id, chapter_number, ...)` als
  convenience-Wrapper (ruft `add_paper` mit `type=chapter` auf).
- MCP-Tool `vault.add_paper` + `vault.add_chapter` exponieren.

### 6. `skills/citation-extraction/SKILL.md`

Hinweis-Block in Schritt 3 (Zitat-Extraktion):

> Wenn `parent_paper_id` gesetzt ist, liegt ein Kapitel-PDF vor. Statt des
> Gesamt-Buches nur dieses Kapitel als `file_id` uebergeben — reduziert
> Token-Footprint um ~95 %.

### 7. Tests

- `tests/test_chunk_pdf.py` — unit + integration (Fixture-PDF)
- `tests/test_vault_parent.py` — parent/child-Beziehung in Vault
- `tests/fixtures/sample_book.pdf` — minimales PDF mit Outline (< 200 KB)

## Akzeptanzkriterien

- [ ] 1 OA-Buch (>= 400 Seiten) -> 8+ Kapitel-PDFs in `<session>/pdfs/<isbn>-ch<n>.pdf`
- [ ] Kapitel-Token-Footprint < 30k pro API-Call
- [ ] Migration idempotent (kann mehrfach laufen)
- [ ] Tests: alle bestehenden pass + neue tests grueen

## Abhaengigkeiten

- Chunk A muss gemergt sein (schema.sql mit book-columns, db.py-Signatur)
- PyPDF2 >= 3.0.0 bereits in `scripts/requirements.txt`
