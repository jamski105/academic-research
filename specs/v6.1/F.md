# Spec: F — VLM Figure/Table Verification (Chunk F, v6.1)

**Ticket:** #99  
**Branch:** feat/v6.1-F-vlm-figure-verifier  
**Status:** draft

---

## Überblick

Bücher und Papers enthalten Diagramme und Tabellen, die im Text referenziert werden
("siehe Abb. 3.4", "Tab. 5.1"). Aktuell werden diese ignoriert oder halluziniert.
Dieser Chunk implementiert:

1. Vault-Schicht für Figures (SQLite `figures`-Tabelle + DB-API + MCP-Tools)
2. `figure-verifier`-Agent (Sonnet, Vision, Citations-API)
3. Additiven Figure-Check im `verbatim-guard`-Hook
4. Tests (Vault-Roundtrip + Hook-Verhalten) + Eval-Skeleton

---

## Dateigrenze

| Datei | Aktion |
|---|---|
| `agents/figure-verifier.md` | CREATE |
| `mcp/academic_vault/schema.sql` | MODIFY — neue `figures`-Tabelle |
| `mcp/academic_vault/migrate.py` | MODIFY — `add_figures_table()` |
| `mcp/academic_vault/db.py` | MODIFY — `add_figure`, `get_figure`, `list_figures` |
| `mcp/academic_vault/server.py` | MODIFY — MCP-Tools `vault.add_figure`, `vault.get_figure`, `vault.list_figures` |
| `hooks/verbatim-guard.mjs` | MODIFY — Figure-Referenz-Check additiv |
| `tests/test_figure_verifier.py` | CREATE |
| `tests/test_verbatim_figure_guard.py` | CREATE |
| `evals/figure-verifier/evals.json` | CREATE |

---

## 1. Datenbankschema

### 1.1 `figures`-Tabelle (schema.sql)

```sql
CREATE TABLE IF NOT EXISTS figures (
  figure_id         TEXT PRIMARY KEY,
  paper_id          TEXT NOT NULL REFERENCES papers(paper_id),
  page              INTEGER,
  caption           TEXT,
  vlm_description   TEXT,
  data_extracted_json TEXT,
  created_at        INTEGER NOT NULL
);
```

Kein FTS5, keine Embeddings — YAGNI.

### 1.2 migrate.py — `add_figures_table(db_path)`

Idempotente Migration analog zu `add_book_columns()` / `add_parent_paper_id_column()`:

```python
def add_figures_table(db_path: str) -> None:
    """Erstellt figures-Tabelle falls nicht vorhanden. Idempotent."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS figures (
              figure_id         TEXT PRIMARY KEY,
              paper_id          TEXT NOT NULL REFERENCES papers(paper_id),
              page              INTEGER,
              caption           TEXT,
              vlm_description   TEXT,
              data_extracted_json TEXT,
              created_at        INTEGER NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
```

---

## 2. DB-Schicht (db.py)

Drei neue Methoden auf `VaultDB`, analog zu Quotes-Methoden:

### `add_figure(paper_id, page, caption, vlm_description, data_extracted) -> str`

- Generiert UUID als `figure_id`
- INSERT (kein UPSERT nötig — jeder Figure-Eintrag ist eindeutig)
- Gibt `figure_id` zurück

### `get_figure(figure_id) -> Optional[dict]`

- SELECT * WHERE figure_id = ?

### `list_figures(paper_id) -> list[dict]`

- SELECT * WHERE paper_id = ? ORDER BY page

---

## 3. Server-Schicht (server.py)

Drei pure Funktionen + drei MCP-Tool-Dekoratoren:

### Pure Funktionen

```python
def add_figure(db_path, paper_id, page, caption, vlm_description, data_extracted) -> str
def get_figure(db_path, figure_id) -> Optional[dict]
def list_figures(db_path, paper_id) -> list[dict]
```

### MCP-Tools

- `vault.add_figure(paper_id, page, caption, vlm_description, data_extracted_json) -> str`
- `vault.get_figure(figure_id) -> Optional[dict]`
- `vault.list_figures(paper_id) -> list[dict]`

---

## 4. Agent: `figure-verifier.md`

**Frontmatter:**
- `name: figure-verifier`
- `model: sonnet` (Vision-fähig)
- `color: purple`
- `tools: [Read, mcp__academic_vault__vault_ensure_file, mcp__academic_vault__vault_add_figure, mcp__academic_vault__vault_list_figures]`
- `maxTurns: 8`

**Body-Aufbau** (analog quote-extractor.md):

1. Rolle: VLM-Analyst für Figures/Tabellen in akademischen PDFs
2. Auftrag: Pro Figure/Tabelle → Caption extrahieren, VLM-Beschreibung erstellen (≥ 50 Zeichen), Datenpunkte bei Tabellen als JSON
3. API-Call-Schema: Citations-API mit `document`-Parameter (Files-API file_id via `vault.ensure_file`)
4. Output-Format: Strukturiertes JSON `{figure_id, caption, vlm_description, data_extracted_json}`
5. Qualitätskriterien: Beschreibung ≥ 50 Zeichen, Tabellen als JSON-Array

---

## 5. verbatim-guard.mjs — Figure-Check (additiv)

**Neues Pattern** (ergänzt bestehende Quote-Prüfung):

```
(Abb|Abbildung|Tab|Tabelle|Fig|Figure)\s*\d+(\.\d+)?
```

**Strategie:**
- Wenn ein Figure-Referenz-Pattern gefunden wird, extrahiere die Caption aus dem direkten Textkontext (nachfolgendes Anführungszeichen-Span ≤ 200 Zeichen)
- Suche via `find_figure_by_caption(db_path, caption_fragment, paper_id=None)` im Vault
- Wenn kein Vault-Eintrag mit passendem Caption-Fragment: BLOCK mit Hint
- Fail-open: Wenn Vault-DB fehlt oder Python-Fehler → Warnung + allow

**Wichtig:** Bestehende Quote-Prüfung (`extractQuoteSpans` → `lookupInVault`) bleibt unverändert. Figure-Check ist ein zusätzlicher Schritt NACH dem Quote-Check.

**Scope:** Figure-Check gilt nur für `isProtectedPath(filePath) === true`-Paths (gleicher Scope wie bestehender Quote-Check). Performance: ein Vault-Lookup pro Figure-Verweis pro Write.

**Neue Python-Hilfsfunktion in server.py:**
```python
def find_figure_by_caption(db_path, caption_fragment, paper_id=None) -> list[dict]
```

`find_figure_by_caption` ist keine MCP-Tool-Funktion und erhält keinen Tool-Dekorator — sie wird ausschließlich aus dem Hook via Python-Subprocess aufgerufen (analog zu `search_quote_text` in der bestehenden Hook-Logik).

**Hook-Ablauf:**
1. Bestehender Quote-Check (unverändert)
2. Figure-Referenz-Pattern suchen
3. Bei Treffer: Caption-Fragment extrahieren + Vault-Lookup
4. Bei Mismatch: BLOCK

---

## 6. Tests

### tests/test_figure_verifier.py

- Vault-Roundtrip: `add_figure` → `get_figure` → Felder prüfen
- `list_figures` gibt leere Liste bei unbekanntem paper_id
- JSON-Schema-Validierung: `data_extracted_json` muss valides JSON sein
- MCP-Tool-Smoke: `server.add_figure(...)` gibt `figure_id` zurück

### tests/test_verbatim_figure_guard.py

- Hook erkennt "Abb. 3.4" → blockiert wenn kein Vault-Eintrag
- Hook erlaubt wenn Caption im Vault gefunden
- Hook blockiert NICHT bei fehlendem Vault-DB (fail-open)
- Bestehende Quote-Prüfung bleibt funktional (Regression)

---

## 7. Evals

`evals/figure-verifier/evals.json` — 5 Cases (trigger-only Skeleton):

**Abweichung von chunks.md (L0-genehmigt):** chunks.md spezifiziert 15 Cases (5 Bücher × 3 Figures). Spec reduziert auf 5-Case-Skeleton mit Trigger-Evals, weil (a) Quality-Cases reproduzierbare Buch-PDF-Fixtures verlangen die in Chunk G konsolidiert werden, (b) Wave 1 Fokus ist Vertical Slice + Foundation, nicht vollständige Eval-Suite. Chunk G erweitert dies auf vollwertige Quality-Evals als Teil der F15-Token-Regression-Initiative.

- fv-01: Agent mit valider paper_id + Seite → `figure_id` non-empty
- fv-02: Caption ≥ 50 Zeichen in vlm_description
- fv-03: Tabelle → `data_extracted_json` ist valides JSON-Array
- fv-04: Unbekannte Paper-ID → graceful error
- fv-05: Mehrere Figures auf einer Seite → alle mit figure_id

---

## Akzeptanzkriterien

- [ ] Tabellen werden zu strukturiertem JSON extrahiert (Agent-Output)
- [ ] Bilder bekommen LLM-Beschreibung ≥ 50 Zeichen
- [ ] Verbatim-Hook erkennt erfundene Figure-Verweise (Block bei Mismatch)
- [ ] Existing Quote-Checks funktionieren weiterhin (keine Regression)
- [ ] `pytest tests/test_figure_verifier.py tests/test_verbatim_figure_guard.py` grün

---

## Offene Fragen

Keine — Ticket ist selbstständig, kein Blockierer durch F2.x.

VLM-Aufrufe in Tests: Kein echter API-Call nötig. Tests prüfen Vault-Roundtrip
und Hook-Logik. Der Agent selbst ist eine Markdown-Definitionsdatei (nicht
ausführbarer Code), daher Agent-Smoke = Syntaxprüfung + Frontmatter-Validierung.
