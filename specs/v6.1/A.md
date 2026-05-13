# Spec: chunk-A — F2.1 book-handler Skill + ISBN-Resolution + Vault book/chapter

## Ziel

First-class Buch-Support im academic-research-Plugin: Bücher und Kapitel werden
wie Artikel indexiert, aufgelöst und zitiert. Fundament für alle F2.x-Chunks.

## Scope (file boundary)

| Datei | Aktion |
|---|---|
| `skills/book-handler/SKILL.md` | CREATE |
| `skills/book-handler/references/sources.md` | CREATE |
| `scripts/book_resolve.py` | CREATE |
| `scripts/requirements.txt` | MODIFY — `requests`, `lxml` |
| `mcp/academic_vault/schema.sql` | MODIFY — neue Spalten |
| `mcp/academic_vault/migrate.py` | MODIFY — idempotente Migration |
| `mcp/academic_vault/server.py` | MODIFY — `add_paper` erweitert |
| `tests/test_book_resolve.py` | CREATE |
| `tests/test_skills_manifest.py` | MODIFY — `book-handler` registrieren |
| `tests/test_vault_book_chapter.py` | CREATE |

---

## 1. Skill `book-handler`

### Trigger-Phrasen (Frontmatter `description`)

- „Buch", „Monografie", „Sammelband", „Kapitel von …"
- ISBN-Pattern `\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d`
- DOI-Muster für Springer-Bücher: `10.1007/978-`

### Skill-Workflow (SKILL.md body)

```
1. Trigger erkennen (ISBN / Titel / DOI / Freitext-Anfrage)
2. book_resolve.py (via Bash-Call oder API-Tool) aufrufen
   → liefert CSL-JSON mit type: book | chapter
3. Vault-Eintrag anlegen: vault.add_paper(type=book|chapter, …)
4. Optional: OPAC-Hinweis (Standort/Signatur, via browser-use oder manuell)
5. DOAB/OAPEN-Check: Falls OA-PDF vorhanden → pdf_path setzen
6. Hinweis an User: Kapitel-Schnitt via F2.2, OCR-Check via F2.4
```

### Abgrenzung

Dieser Skill löst Metadaten auf und legt Vault-Einträge an.
Er schneidet keine Kapitel (→ F2.2), berechnet kein Seitenmapping (→ F2.3)
und führt keine OCR durch (→ F2.4). Zitationsformatierung → `citation-extraction`.

---

## 2. `scripts/book_resolve.py`

### API-Clients (in Prioritätsreihenfolge)

#### 2a. DNB SRU (Deutsche Nationalbibliothek)

- Endpoint: `https://services.dnb.de/sru/dnb`
- Query: `queryParameter=isbn+%3D+{isbn}` oder `queryParameter=title+%3D+{title}`
- Format: `recordSchema=MARC21-xml` → XPath-Parsing mit `lxml`
- Felder: Titel, Autor, Herausgeber, Verlag, Jahr, ISBN, Sprache

#### 2b. OpenLibrary

- Endpoint: `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json`
- Fallback für DNB-Fehlschlag; JSON-API
- Felder: title, authors, publishers, publish_date, isbn_13, subjects

#### 2c. GoogleBooks

- Endpoint: `https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}`
- Tertiär-Fallback; kein API-Key für Basis-Abfragen nötig
- Felder: volumeInfo.title, authors, publisher, publishedDate, industryIdentifiers

#### 2d. DOAB (Directory of Open Access Books)

- Endpoint: `https://directory.doabooks.org/rest/search?query=isbn:{isbn}&expand=metadata`
- Prüft: Ist das Buch Open Access? Gibt `download_url` zurück falls ja
- JSON-API

### CSL-JSON-Output-Schema

```json
{
  "type": "book",            // oder "chapter"
  "title": "...",
  "author": [{"family": "...", "given": "..."}],
  "editor": [{"family": "...", "given": "..."}],   // bei Sammelbänden
  "container-title": "...",  // bei chapter: Titel des Sammelbands
  "chapter-number": "...",   // bei chapter: Kapitelnummer
  "page-first": 1,
  "page-last": 42,
  "publisher": "...",
  "publisher-place": "...",
  "issued": {"date-parts": [[2023]]},
  "ISBN": "978-3-...",
  "DOI": "10.1007/...",
  "URL": "https://..."       // falls OA
}
```

### CLI-Schnittstelle

```
python scripts/book_resolve.py --isbn 9783446461031
python scripts/book_resolve.py --title "Grundlagen der Informatik"
python scripts/book_resolve.py --doi 10.1007/978-3-658-12345-6
```

Output: CSL-JSON auf stdout, Fehler auf stderr, Exit-Code 0/1.

### Fallback-Strategie

1. DNB SRU → bei Fehler/leer: 2.
2. OpenLibrary → bei Fehler/leer: 3.
3. GoogleBooks → bei Fehler/leer: leeres dict + stderr-Warning
4. DOAB immer als ergänzender OA-Check (parallel oder nach Schritt 1–3)

---

## 3. Vault-Schema-Erweiterung

### Neue Spalten in `papers`

```sql
editor          TEXT,          -- JSON-Array: [{"family": "…", "given": "…"}]
chapter         TEXT,          -- Kapitel-Bezeichnung oder -Nummer (string)
page_first      INTEGER,       -- erste Seite im Sammelband / Buch
page_last       INTEGER,       -- letzte Seite im Sammelband / Buch
container_title TEXT           -- Titel des übergeordneten Werks (bei chapter)
```

### CHECK-Constraint erweitern

Bestehend: `type TEXT NOT NULL DEFAULT 'article-journal'`  
Neu: `type TEXT NOT NULL DEFAULT 'article-journal' CHECK(type IN ('article-journal','book','chapter'))`

**Wichtig:** ALTER TABLE in SQLite kann keine CHECK-Constraints nachträglich hinzufügen.
Vorgehen:
- `schema.sql` erhält den vollständigen CREATE TABLE inkl. CHECK (für Neuinstallationen)
- `migrate.py` fügt die neuen Spalten via `ALTER TABLE … ADD COLUMN` hinzu (idempotent)
- Der CHECK-Constraint auf `type` kann in bestehenden DBs nicht erzwungen werden
  → Die Anwendungslogik (server.py) validiert den type-Wert

### Migration (idempotent)

```python
def add_book_columns(db_path: str) -> None:
    """Fuegt book/chapter-Spalten hinzu. Idempotent via try/except."""
    new_cols = [
        ("editor", "TEXT"),
        ("chapter", "TEXT"),
        ("page_first", "INTEGER"),
        ("page_last", "INTEGER"),
        ("container_title", "TEXT"),
    ]
    conn = sqlite3.connect(db_path)
    for col, coltype in new_cols:
        try:
            conn.execute(f"ALTER TABLE papers ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass  # Spalte existiert bereits
    conn.commit()
    conn.close()
```

---

## 4. `server.py` — `add_paper` Erweiterung

### Neue Signatur

```python
def add_paper(
    db_path: str,
    paper_id: str,
    csl_json: str,
    pdf_path: Optional[str] = None,
    doi: Optional[str] = None,
    isbn: Optional[str] = None,
    page_offset: int = 0,
    # Neu:
    editor: Optional[str] = None,         # JSON-String
    chapter: Optional[str] = None,
    page_first: Optional[int] = None,
    page_last: Optional[int] = None,
    container_title: Optional[str] = None,
) -> None:
```

Validierung: `type`-Wert wird aus `csl_json` extrahiert; erlaubt: `article-journal`, `book`, `chapter`.
Bei unbekanntem type → `ValueError`.

### `db.py` — `add_paper` Erweiterung

Entsprechende Anpassung des INSERT-Statements um die 5 neuen Felder.

---

## 5. Tests

### `tests/test_book_resolve.py`

- `test_dnb_isbn_hit` — Mock-Response für ISBN 9783446461031 → CSL-JSON mit type=book
- `test_openlibrary_fallback` — DNB gibt leere Liste → OpenLibrary-Mock liefert Daten
- `test_googlebooks_fallback` — DNB + OL leer → GoogleBooks-Mock
- `test_doab_oa_check` — Springer-DOI → DOAB-Mock liefert download_url
- `test_no_source_returns_empty` — alle Quellen schlagen fehl → leeres dict, kein crash
- `test_isbn_csl_has_required_fields` — CSL-JSON enthält type, title, author/editor

### `tests/test_skills_manifest.py`

- `book-handler` in `baselines/skill_sizes.json` eintragen (Größe ~4000 Zeichen)
- Kein `VENDORED_SKILLS`-Eintrag nötig (normaler Skill)

### `tests/test_vault_book_chapter.py`

- `test_add_paper_type_book` — add_paper mit type=book, editor, → get_paper prüft Felder
- `test_add_paper_type_chapter` — add_paper mit type=chapter, container_title, page_first/last
- `test_add_paper_invalid_type` — type=unknown → ValueError
- `test_migration_idempotent` — add_book_columns zweimal ausführen → kein Fehler
- `test_old_paper_still_readable` — type=article-journal (Default) funktioniert weiter

---

## 6. Acceptance-Proben (aus Ticket #71)

1. `book_resolve.py --isbn 9783446461031` → DNB-Treffer + valides CSL-JSON
   (type=book, title nicht leer, issued.date-parts vorhanden)
2. Springer-DOI `10.1007/978-3-658-*` → OAPEN/DOAB-Lookup liefert OA-Flag;
   falls tatsächlich OA: `pdf_url` im CSL-Output

---

## 7. Nicht in Scope

- Kapitel-Schnitt (→ chunk-B / F2.2)
- Seitenmapping-Logik (→ chunk-C / F2.3)
- OCR-Detection (→ chunk-D / F2.4)
- DIN-1505-Zitationsformat für Bücher (→ chunk-E / F2.5)
- parent_paper_id-Feld in DB (→ chunk-B)
- Evaluation-Suite (→ chunk-G / F15)

---

## 8. Abhängigkeiten

- `requests` (HTTP-Clients) — bereits in Python-Stdlib: nein → zu `scripts/requirements.txt`
- `lxml` (XML-Parsing für DNB SRU MARC21) → zu `scripts/requirements.txt`
- Keine neuen MCP-SDK-Abhängigkeiten
