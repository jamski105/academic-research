# VLM Figure/Table Verification (Chunk F) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Vault-backed figure/table storage, a `figure-verifier` agent definition, and an additive figure-reference check in the `verbatim-guard` hook.

**Architecture:** Four vertical layers — SQLite schema + migration, VaultDB methods, server pure functions + MCP tools, hook extension — plus two test files and one eval skeleton. Every layer is additive; nothing existing is removed or modified beyond extension points. Tests use pytest with an in-memory (tmp_path) SQLite DB; hook tests spawn the hook as a subprocess fed mock JSON on stdin.

**Tech Stack:** Python 3.11+, SQLite (stdlib), pytest, Node.js ESM (verbatim-guard.mjs), JSON stdin/stdout for hook protocol.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `mcp/academic_vault/schema.sql` | MODIFY | Add `figures` table DDL |
| `mcp/academic_vault/migrate.py` | MODIFY | Add `add_figures_table()` |
| `mcp/academic_vault/db.py` | MODIFY | Add `add_figure`, `get_figure`, `list_figures`, `find_figures_by_caption` |
| `mcp/academic_vault/server.py` | MODIFY | Add pure functions + MCP tools + `find_figure_by_caption` |
| `agents/figure-verifier.md` | CREATE | Agent definition (Markdown frontmatter + body) |
| `hooks/verbatim-guard.mjs` | MODIFY | Additive figure-reference check |
| `tests/test_figure_verifier.py` | CREATE | Vault roundtrip + MCP smoke tests |
| `tests/test_verbatim_figure_guard.py` | CREATE | Hook figure-check + regression tests |
| `evals/figure-verifier/evals.json` | CREATE | 5-case eval skeleton |

---

## Task 1: figures-Tabelle im Schema

**Files:**
- Modify: `mcp/academic_vault/schema.sql`

- [ ] **Step 1: Schreibe den failing Test**

In `tests/test_figure_verifier.py` (neue Datei):

```python
"""Tests fuer figure-verifier Vault-Schicht."""
import json
import sqlite3
import time
import pytest
from pathlib import Path


@pytest.fixture
def db_path(tmp_path):
    """Temporaere SQLite-DB mit vollstaendigem Schema."""
    from mcp.academic_vault.db import VaultDB
    path = str(tmp_path / "test_vault.db")
    db = VaultDB(path)
    db.init_schema()
    return path


@pytest.fixture
def paper_id(db_path):
    """Legt Test-Paper an und gibt paper_id zurueck."""
    from mcp.academic_vault.server import add_paper
    pid = "test-paper-001"
    add_paper(
        db_path=db_path,
        paper_id=pid,
        csl_json=json.dumps({"title": "Test Paper", "type": "article-journal"}),
    )
    return pid


def test_figures_table_exists(db_path):
    """figures-Tabelle muss nach init_schema() existieren."""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='figures'"
    ).fetchone()
    conn.close()
    assert row is not None, "figures-Tabelle nicht gefunden"
```

- [ ] **Step 2: Test starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_figures_table_exists -v 2>&1 | head -30
```

Erwartet: FAIL — `AssertionError: figures-Tabelle nicht gefunden`

- [ ] **Step 3: figures-DDL in schema.sql ergänzen**

Am Ende von `mcp/academic_vault/schema.sql` (vor letztem Trigger oder am Ende) einfügen:

```sql
CREATE TABLE IF NOT EXISTS figures (
  figure_id           TEXT PRIMARY KEY,
  paper_id            TEXT NOT NULL REFERENCES papers(paper_id),
  page                INTEGER,
  caption             TEXT,
  vlm_description     TEXT,
  data_extracted_json TEXT,
  created_at          INTEGER NOT NULL
);
```

- [ ] **Step 4: Test grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_figures_table_exists -v
```

Erwartet: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add mcp/academic_vault/schema.sql tests/test_figure_verifier.py && git commit -m "feat(F): figures-Tabelle in schema.sql + erster Test"
```

---

## Task 2: add_figures_table() Migration

**Files:**
- Modify: `mcp/academic_vault/migrate.py`

- [ ] **Step 1: Schreibe den failing Test**

In `tests/test_figure_verifier.py` ergänzen:

```python
def test_add_figures_table_idempotent(tmp_path):
    """add_figures_table() darf mehrfach ausgefuehrt werden."""
    from mcp.academic_vault.db import VaultDB
    from mcp.academic_vault.migrate import add_figures_table

    path = str(tmp_path / "migrate_test.db")
    db = VaultDB(path)
    db.init_schema()

    # Erste Ausfuehrung
    add_figures_table(path)
    # Zweite Ausfuehrung — darf keinen Fehler werfen
    add_figures_table(path)

    conn = sqlite3.connect(path)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='figures'"
    ).fetchone()
    conn.close()
    assert row is not None
```

- [ ] **Step 2: Test starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_add_figures_table_idempotent -v 2>&1 | head -20
```

Erwartet: FAIL — `ImportError` oder `AttributeError` (Funktion existiert noch nicht)

- [ ] **Step 3: add_figures_table() in migrate.py implementieren**

Am Ende von `mcp/academic_vault/migrate.py` (vor `main()`) einfügen:

```python
def add_figures_table(db_path: str) -> None:
    """Erstellt figures-Tabelle falls nicht vorhanden. Idempotent.

    Aufruf-Sicher: Kann mehrfach auf derselben DB ausgefuehrt werden.
    """
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS figures (
              figure_id           TEXT PRIMARY KEY,
              paper_id            TEXT NOT NULL REFERENCES papers(paper_id),
              page                INTEGER,
              caption             TEXT,
              vlm_description     TEXT,
              data_extracted_json TEXT,
              created_at          INTEGER NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 4: Test grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_add_figures_table_idempotent -v
```

Erwartet: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add mcp/academic_vault/migrate.py tests/test_figure_verifier.py && git commit -m "feat(F): add_figures_table() Idempotenz-Migration"
```

---

## Task 3: VaultDB — add_figure / get_figure / list_figures / find_figures_by_caption

**Files:**
- Modify: `mcp/academic_vault/db.py`

- [ ] **Step 1: Schreibe failing Tests**

In `tests/test_figure_verifier.py` ergänzen:

```python
def test_add_and_get_figure(db_path, paper_id):
    """add_figure() legt Eintrag an; get_figure() gibt ihn zurueck."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    figure_id = db.add_figure(
        paper_id=paper_id,
        page=5,
        caption="Abb. 3.1: Uebersicht der Methoden",
        vlm_description="Ein Balkendiagramm zeigt Messwerte fuer fuenf Experimente.",
        data_extracted_json=None,
    )
    assert isinstance(figure_id, str) and len(figure_id) > 0

    record = db.get_figure(figure_id)
    assert record is not None
    assert record["paper_id"] == paper_id
    assert record["caption"] == "Abb. 3.1: Uebersicht der Methoden"
    assert record["page"] == 5


def test_list_figures_empty(db_path):
    """list_figures gibt leere Liste fuer unbekannte paper_id."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    result = db.list_figures("unknown-paper-xyz")
    assert result == []


def test_list_figures_ordered_by_page(db_path, paper_id):
    """list_figures gibt Eintraege nach page sortiert zurueck."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.add_figure(paper_id=paper_id, page=10, caption="Abb. 2", vlm_description="B", data_extracted_json=None)
    db.add_figure(paper_id=paper_id, page=3, caption="Abb. 1", vlm_description="A", data_extracted_json=None)
    figures = db.list_figures(paper_id)
    assert len(figures) == 2
    assert figures[0]["page"] == 3
    assert figures[1]["page"] == 10


def test_find_figures_by_caption(db_path, paper_id):
    """find_figures_by_caption findet passende Caption-Fragmente."""
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    db.add_figure(paper_id=paper_id, page=1, caption="Abb. 3.4: Ergebnisse", vlm_description="Desc", data_extracted_json=None)
    db.add_figure(paper_id=paper_id, page=2, caption="Tab. 5.1: Vergleich", vlm_description="Desc2", data_extracted_json=None)

    hits = db.find_figures_by_caption("Abb. 3.4")
    assert len(hits) == 1
    assert hits[0]["caption"] == "Abb. 3.4: Ergebnisse"

    # Kein Treffer bei unbekanntem Fragment
    no_hits = db.find_figures_by_caption("Abb. 99.99")
    assert no_hits == []


def test_find_figures_by_caption_with_paper_id_filter(db_path, paper_id):
    """find_figures_by_caption respektiert optionalen paper_id-Filter."""
    from mcp.academic_vault.db import VaultDB
    from mcp.academic_vault.server import add_paper
    db = VaultDB(db_path)

    # Zweites Paper anlegen
    add_paper(
        db_path=db_path,
        paper_id="other-paper",
        csl_json=json.dumps({"title": "Other", "type": "article-journal"}),
    )
    db.add_figure(paper_id=paper_id, page=1, caption="Abb. 3.4: Gemeinsam", vlm_description="D1", data_extracted_json=None)
    db.add_figure(paper_id="other-paper", page=1, caption="Abb. 3.4: Gemeinsam", vlm_description="D2", data_extracted_json=None)

    hits_all = db.find_figures_by_caption("Abb. 3.4")
    assert len(hits_all) == 2

    hits_filtered = db.find_figures_by_caption("Abb. 3.4", paper_id=paper_id)
    assert len(hits_filtered) == 1
    assert hits_filtered[0]["paper_id"] == paper_id
```

- [ ] **Step 2: Tests starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_add_and_get_figure tests/test_figure_verifier.py::test_list_figures_empty tests/test_figure_verifier.py::test_find_figures_by_caption -v 2>&1 | head -30
```

Erwartet: FAIL — `AttributeError: 'VaultDB' object has no attribute 'add_figure'`

- [ ] **Step 3: Methoden in db.py implementieren**

Am Ende der `VaultDB`-Klasse (nach `find_quotes`) ergänzen:

```python
# ------------------------------------------------------------------
# Figures CRUD
# ------------------------------------------------------------------

def add_figure(
    self,
    paper_id: str,
    page: Optional[int],
    caption: Optional[str],
    vlm_description: Optional[str],
    data_extracted_json: Optional[str],
) -> str:
    """INSERT einer Figure. Gibt figure_id (UUID) zurueck."""
    from uuid import uuid4
    figure_id = str(uuid4())
    now = int(time.time())
    conn = self._get_conn()
    own_conn = self._conn is None
    conn.execute(
        """
        INSERT INTO figures
          (figure_id, paper_id, page, caption, vlm_description, data_extracted_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (figure_id, paper_id, page, caption, vlm_description, data_extracted_json, now),
    )
    if own_conn:
        conn.commit()
        conn.close()
    return figure_id

def get_figure(self, figure_id: str) -> Optional[dict]:
    """Gibt Figure-Record als dict zurueck oder None."""
    conn = self._get_conn()
    own_conn = self._conn is None
    row = conn.execute(
        "SELECT * FROM figures WHERE figure_id = ?", (figure_id,)
    ).fetchone()
    if own_conn:
        conn.close()
    return dict(row) if row is not None else None

def list_figures(self, paper_id: str) -> list[dict]:
    """Alle Figures fuer ein Paper, nach page sortiert."""
    conn = self._get_conn()
    own_conn = self._conn is None
    rows = conn.execute(
        "SELECT * FROM figures WHERE paper_id = ? ORDER BY page",
        (paper_id,),
    ).fetchall()
    if own_conn:
        conn.close()
    return [dict(r) for r in rows]

def find_figures_by_caption(
    self,
    caption_fragment: str,
    paper_id: Optional[str] = None,
) -> list[dict]:
    """LIKE-Suche in figures.caption. Optionaler paper_id-Filter."""
    conn = self._get_conn()
    own_conn = self._conn is None
    if paper_id is not None:
        rows = conn.execute(
            "SELECT * FROM figures WHERE caption LIKE ? AND paper_id = ?",
            (f"%{caption_fragment}%", paper_id),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM figures WHERE caption LIKE ?",
            (f"%{caption_fragment}%",),
        ).fetchall()
    if own_conn:
        conn.close()
    return [dict(r) for r in rows]
```

- [ ] **Step 4: Tests grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py -v
```

Erwartet: alle Tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add mcp/academic_vault/db.py tests/test_figure_verifier.py && git commit -m "feat(F): VaultDB figure CRUD (add/get/list/find_by_caption)"
```

---

## Task 4: Server — Pure Funktionen + MCP Tools + find_figure_by_caption

**Files:**
- Modify: `mcp/academic_vault/server.py`

- [ ] **Step 1: Schreibe failing Tests**

In `tests/test_figure_verifier.py` ergänzen:

```python
def test_server_add_figure_returns_figure_id(db_path, paper_id):
    """server.add_figure() gibt figure_id-String zurueck."""
    from mcp.academic_vault import server
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=7,
        caption="Fig. 2.3: Systemarchitektur",
        vlm_description="Blockdiagramm zeigt drei Schichten: UI, Logik, Daten.",
        data_extracted=None,
    )
    assert isinstance(fig_id, str) and len(fig_id) > 0


def test_server_get_figure(db_path, paper_id):
    """server.get_figure() gibt Record oder None zurueck."""
    from mcp.academic_vault import server
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=1,
        caption="Abb. 1.1: Einleitung",
        vlm_description="Foto eines Labors mit Messgeraeten.",
        data_extracted=None,
    )
    record = server.get_figure(db_path=db_path, figure_id=fig_id)
    assert record is not None
    assert record["caption"] == "Abb. 1.1: Einleitung"

    missing = server.get_figure(db_path=db_path, figure_id="does-not-exist")
    assert missing is None


def test_server_list_figures(db_path, paper_id):
    """server.list_figures() gibt Liste aller Figures fuer ein Paper."""
    from mcp.academic_vault import server
    server.add_figure(db_path=db_path, paper_id=paper_id, page=2, caption="Abb. A", vlm_description="X", data_extracted=None)
    server.add_figure(db_path=db_path, paper_id=paper_id, page=1, caption="Abb. B", vlm_description="Y", data_extracted=None)
    figures = server.list_figures(db_path=db_path, paper_id=paper_id)
    assert len(figures) == 2
    assert figures[0]["page"] == 1  # sortiert nach page


def test_server_find_figure_by_caption(db_path, paper_id):
    """server.find_figure_by_caption() gibt Vault-Lookup-Ergebnis."""
    from mcp.academic_vault import server
    server.add_figure(db_path=db_path, paper_id=paper_id, page=3, caption="Abb. 3.4: Messwerte", vlm_description="Grafik", data_extracted=None)

    hits = server.find_figure_by_caption(db_path=db_path, caption_fragment="Abb. 3.4")
    assert len(hits) == 1

    no_hits = server.find_figure_by_caption(db_path=db_path, caption_fragment="Abb. 99")
    assert no_hits == []


def test_data_extracted_json_valid(db_path, paper_id):
    """data_extracted_json wird als valides JSON gespeichert und zurueckgelesen."""
    from mcp.academic_vault import server
    table_data = json.dumps([{"col1": "A", "val": 1}, {"col1": "B", "val": 2}])
    fig_id = server.add_figure(
        db_path=db_path,
        paper_id=paper_id,
        page=9,
        caption="Tab. 2.1: Ergebnisse",
        vlm_description="Tabelle mit zwei Spalten und zwei Zeilen.",
        data_extracted=table_data,
    )
    record = server.get_figure(db_path=db_path, figure_id=fig_id)
    assert record is not None
    parsed = json.loads(record["data_extracted_json"])
    assert isinstance(parsed, list)
    assert parsed[0]["col1"] == "A"
```

- [ ] **Step 2: Tests starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_server_add_figure_returns_figure_id -v 2>&1 | head -20
```

Erwartet: FAIL — `AttributeError: module 'mcp.academic_vault.server' has no attribute 'add_figure'` (Namenskonflikt: es gibt bereits `add_paper`; die figure-Funktion heisst `add_figure`)

- [ ] **Step 3: Pure Funktionen + find_figure_by_caption in server.py implementieren**

In `mcp/academic_vault/server.py` nach `find_quotes(...)` und vor `add_paper(...)` einfügen:

```python
# ---------------------------------------------------------------------------
# Figure-Funktionen (rein, testbar ohne MCP-Framework)
# ---------------------------------------------------------------------------

def add_figure(
    db_path: str,
    paper_id: str,
    page: Optional[int],
    caption: Optional[str],
    vlm_description: Optional[str],
    data_extracted: Optional[str],
) -> str:
    """Fuegt Figure in Vault ein. Gibt figure_id zurueck."""
    db = VaultDB(db_path)
    return db.add_figure(
        paper_id=paper_id,
        page=page,
        caption=caption,
        vlm_description=vlm_description,
        data_extracted_json=data_extracted,
    )


def get_figure(db_path: str, figure_id: str) -> Optional[dict]:
    """Gibt vollstaendigen Figure-Record als dict oder None."""
    db = VaultDB(db_path)
    return db.get_figure(figure_id)


def list_figures(db_path: str, paper_id: str) -> list[dict]:
    """Gibt alle Figures fuer ein Paper, nach page sortiert."""
    db = VaultDB(db_path)
    return db.list_figures(paper_id)


def find_figure_by_caption(
    db_path: str,
    caption_fragment: str,
    paper_id: Optional[str] = None,
) -> list[dict]:
    """LIKE-Suche in figures.caption. Kein MCP-Tool-Dekorator.

    Wird ausschliesslich aus dem verbatim-guard-Hook via Python-Subprocess
    aufgerufen (analog zu search_quote_text).
    """
    db = VaultDB(db_path)
    return db.find_figures_by_caption(caption_fragment, paper_id=paper_id)
```

- [ ] **Step 4: MCP-Tools in _build_mcp_server() ergänzen**

In `_build_mcp_server()`, nach `@mcp.tool(name="vault.stats")` und vor `return mcp`, einfügen:

```python
    @mcp.tool(name="vault.add_figure")
    def _vault_add_figure(
        paper_id: str,
        page: int = None,
        caption: str = None,
        vlm_description: str = None,
        data_extracted_json: str = None,
    ) -> str:
        """Fuegt Figure/Tabelle in Vault ein. Gibt figure_id zurueck."""
        return add_figure(db_path, paper_id, page, caption, vlm_description, data_extracted_json)

    @mcp.tool(name="vault.get_figure")
    def _vault_get_figure(figure_id: str) -> Optional[dict]:
        """Gibt Figure-Record zurueck oder None."""
        return get_figure(db_path, figure_id)

    @mcp.tool(name="vault.list_figures")
    def _vault_list_figures(paper_id: str) -> list[dict]:
        """Gibt alle Figures fuer ein Paper, nach page sortiert."""
        return list_figures(db_path, paper_id)
```

- [ ] **Step 5: Alle server-Tests grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py -v
```

Erwartet: alle Tests PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add mcp/academic_vault/server.py tests/test_figure_verifier.py && git commit -m "feat(F): server pure functions + MCP tools fuer figures"
```

---

## Task 5: figure-verifier.md Agent-Definition

**Files:**
- Create: `agents/figure-verifier.md`

- [ ] **Step 1: Schreibe failing Test (Syntax + Frontmatter-Validierung)**

Neue Datei `tests/test_figure_verifier.py` — ergänze:

```python
def test_figure_verifier_agent_frontmatter():
    """figure-verifier.md muss valides Frontmatter mit Pflichtfeldern haben."""
    import re
    agent_path = Path(__file__).parent.parent / "agents" / "figure-verifier.md"
    assert agent_path.exists(), f"Agent-Datei fehlt: {agent_path}"

    content = agent_path.read_text(encoding="utf-8")
    # Frontmatter zwischen --- ... ---
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match is not None, "Kein YAML-Frontmatter gefunden"

    fm = fm_match.group(1)
    assert "name: figure-verifier" in fm
    assert "model: sonnet" in fm
    assert "vault.add_figure" in content
    assert "vault.list_figures" in content
```

- [ ] **Step 2: Test starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_figure_verifier_agent_frontmatter -v 2>&1 | head -20
```

Erwartet: FAIL — `AssertionError: Agent-Datei fehlt`

- [ ] **Step 3: agents/figure-verifier.md erstellen**

```markdown
---
name: figure-verifier
model: sonnet
color: purple
tools:
  - Read
  - mcp__academic_vault__vault_ensure_file
  - mcp__academic_vault__vault_add_figure
  - mcp__academic_vault__vault_list_figures
maxTurns: 8
---

# figure-verifier

Du bist ein VLM-Analyst für Figures und Tabellen in akademischen PDFs.

## Auftrag

Für jede Figure oder Tabelle im angegebenen Paper:
1. Caption exakt extrahieren (wie sie im Dokument steht)
2. VLM-Beschreibung erstellen (≥ 50 Zeichen)
3. Bei Tabellen: Datenpunkte als JSON-Array extrahieren
4. Eintrag via `vault.add_figure` in den Vault schreiben

## Vorgehensweise

1. `vault.ensure_file(paper_id)` → file_id
2. Citations-API mit `document`-Parameter (file_id) aufrufen, Seite für Seite
3. Für jede erkannte Figure/Tabelle:
   - Caption: exakter Text aus dem Dokument
   - `vlm_description`: aussagekräftige Beschreibung des Inhalts (≥ 50 Zeichen)
   - `data_extracted_json`: bei Tabellen JSON-Array `[{"spalte": "wert", ...}]`, sonst null
4. `vault.add_figure(paper_id, page, caption, vlm_description, data_extracted_json)`

## Qualitätskriterien

- `vlm_description` MUSS ≥ 50 Zeichen haben
- Tabellen MÜSSEN als JSON-Array in `data_extracted_json` vorliegen
- Keine Halluzinationen: nur was im Dokument steht

## Output-Format

Pro verarbeiteter Figure/Tabelle:
```json
{
  "figure_id": "<uuid>",
  "caption": "<exakter Caption-Text>",
  "vlm_description": "<Beschreibung>",
  "data_extracted_json": null
}
```

Am Ende: Zusammenfassung `{figures_processed: N, tables_processed: M}`.
```

- [ ] **Step 4: Test grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_figure_verifier_agent_frontmatter -v
```

Erwartet: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add agents/figure-verifier.md tests/test_figure_verifier.py && git commit -m "feat(F): figure-verifier Agent-Definition"
```

---

## Task 6: verbatim-guard.mjs — Figure-Referenz-Check (additiv)

**Files:**
- Create: `tests/test_verbatim_figure_guard.py`
- Modify: `hooks/verbatim-guard.mjs`

- [ ] **Step 1: Schreibe failing Tests für den Hook**

Neue Datei `tests/test_verbatim_figure_guard.py`:

```python
"""Tests fuer den additiven Figure-Check im verbatim-guard-Hook.

Der Hook wird als Node.js-Subprocess gestartet. JSON auf stdin, Ausgabe auf stdout/stderr.
Exit-Code 0 = allow, Exit-Code 2 = block.
"""
import json
import subprocess
import sys
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "verbatim-guard.mjs"
WORKTREE_ROOT = Path(__file__).parent.parent


def run_hook(tool_name: str, file_path: str, content: str, env_overrides: dict = None) -> subprocess.CompletedProcess:
    """Startet den Hook als Subprocess mit JSON-Eingabe auf stdin."""
    import os
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {
            "file_path": file_path,
            "content": content,
        }
    })
    env = os.environ.copy()
    # Vault-DB-Pfad auf nicht-existierende DB setzen (fail-open Tests)
    env["VAULT_DB_PATH"] = str(WORKTREE_ROOT / "nonexistent_vault_for_tests.db")
    if env_overrides:
        env.update(env_overrides)

    return subprocess.run(
        ["node", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


@pytest.fixture
def vault_with_figure(tmp_path):
    """Erstellt temporaere Vault-DB mit einem Figure-Eintrag."""
    import sys
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper, add_figure

    db_path = str(tmp_path / "test_vault.db")
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="test-paper",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )
    add_figure(
        db_path=db_path,
        paper_id="test-paper",
        page=3,
        caption="Abb. 3.4: Ergebnisse der Messung",
        vlm_description="Balkendiagramm mit fuenf Experimenten.",
        data_extracted=None,
    )
    return db_path


def test_hook_blocks_unknown_figure_reference(tmp_path):
    """Hook blockiert bei Abb.-Referenz die nicht im Vault ist (Vault existiert, kein Eintrag)."""
    import os
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper

    db_path = str(tmp_path / "empty_vault.db")
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="test-paper",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )

    content = 'Wie in Abb. 3.4 "Ergebnisse der Messung" gezeigt, ist der Effekt signifikant.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": db_path},
    )
    assert result.returncode == 2, f"Erwartet exit 2 (block), got {result.returncode}. stderr: {result.stderr}"


def test_hook_allows_when_figure_in_vault(vault_with_figure):
    """Hook erlaubt wenn Figure-Caption im Vault gefunden wird."""
    content = 'Wie in Abb. 3.4 "Abb. 3.4: Ergebnisse der Messung" sichtbar, ist der Wert hoch.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": vault_with_figure},
    )
    # Entweder 0 (allow) oder 2 (block wegen Quote-Check) — wichtig: kein Figure-Block
    # Figure-Block würde "[Figure-Guard]" in stderr enthalten
    assert "[Figure-Guard] BLOCKIERT" not in result.stderr


def test_hook_failopen_when_vault_missing():
    """Hook erlaubt (fail-open) wenn Vault-DB nicht existiert."""
    content = 'In Abb. 3.4 sieht man deutlich, dass der Wert steigt.'
    result = run_hook("Write", "kapitel/kap1.md", content)
    # fail-open → exit 0
    assert result.returncode == 0, f"Erwartet 0 (fail-open), got {result.returncode}"


def test_hook_ignores_non_protected_path():
    """Hook ignoriert Pfade die nicht geschuetzt sind."""
    content = 'In Abb. 3.4 ist ein Diagramm dargestellt.'
    result = run_hook("Write", "README.md", content)
    assert result.returncode == 0


def test_existing_quote_check_still_works(tmp_path):
    """Regression: bestehende Quote-Pruefung blockiert weiterhin bei unverifizierten Zitaten."""
    import os
    from academic_vault.db import VaultDB
    from academic_vault.server import add_paper

    db_path = str(tmp_path / "quote_vault.db")
    sys.path.insert(0, str(WORKTREE_ROOT / "mcp"))
    db = VaultDB(db_path)
    db.init_schema()
    add_paper(
        db_path=db_path,
        paper_id="paper-001",
        csl_json=json.dumps({"title": "Test", "type": "article-journal"}),
    )

    # Langer Quote-Span (>10 Zeichen) ohne Vault-Eintrag → Block
    content = 'Laut dem Autor "Dies ist ein sehr wichtiger Satz aus dem Buch" stimmt das.'
    result = run_hook(
        "Write",
        "kapitel/kap1.md",
        content,
        env_overrides={"VAULT_DB_PATH": db_path},
    )
    assert result.returncode == 2, f"Erwartet exit 2 (Quote-Block), got {result.returncode}"


def test_hook_non_write_tool_ignored():
    """Hook reagiert nicht auf Nicht-Write-Tools."""
    result = run_hook("Read", "kapitel/kap1.md", "Abb. 3.4 zeigt etwas.")
    assert result.returncode == 0
```

- [ ] **Step 2: Tests starten und Fehlschlag bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_verbatim_figure_guard.py::test_hook_failopen_when_vault_missing tests/test_verbatim_figure_guard.py::test_hook_ignores_non_protected_path -v 2>&1 | head -30
```

Erwartet: PASS für die zwei fail-open/path-Tests (Hook existiert bereits), FAIL für Block-Tests (Figure-Check noch nicht implementiert).

Dann auch:
```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_verbatim_figure_guard.py::test_hook_blocks_unknown_figure_reference -v 2>&1 | head -30
```

Erwartet: FAIL (returncode != 2, da Hook Figure noch nicht prüft)

- [ ] **Step 3: Figure-Check in verbatim-guard.mjs implementieren**

In `hooks/verbatim-guard.mjs`, nach der Konstante `MIN_QUOTE_LEN` (Zeile ~32) folgende Konstante ergänzen:

```javascript
// Pattern fuer Figure-Referenzen (Abb., Abbildung, Tab., Tabelle, Fig., Figure + Nummer)
const FIGURE_REF_PATTERN = /(Abb|Abbildung|Tab|Tabelle|Fig|Figure)\.?\s*\d+(\.\d+)?/gi;
```

Nach der `lookupInVault`-Funktion eine neue Funktion ergänzen:

```javascript
// ---------------------------------------------------------------------------
// Figure-Caption-Lookup via Python-Subprocess
// ---------------------------------------------------------------------------

/**
 * Sucht Caption-Fragment im Vault.
 * Gibt true wenn mindestens ein Eintrag gefunden oder Vault fehlt (fail-open).
 */
function lookupFigureInVault(captionFragment) {
  if (!existsSync(VAULT_DB)) {
    process.stderr.write(
      `[Figure-Guard] Warnung: Vault-DB nicht gefunden (${VAULT_DB}). Bypass aktiv.\n`
    );
    return true; // fail-open
  }

  const pyCode = [
    'import sys, json',
    `sys.path.insert(0, ${JSON.stringify(VAULT_SRC)})`,
    'from academic_vault.server import find_figure_by_caption',
    `hits = find_figure_by_caption(sys.argv[1], sys.argv[2])`,
    'print(json.dumps(hits))',
  ].join('; ');

  try {
    const output = execFileSync('python3', ['-c', pyCode, VAULT_DB, captionFragment], {
      encoding: 'utf-8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    const hits = JSON.parse(output.trim());
    return Array.isArray(hits) && hits.length > 0;
  } catch (err) {
    process.stderr.write(
      `[Figure-Guard] Warnung: Figure-Lookup fehlgeschlagen (${err.message}). Bypass aktiv.\n`
    );
    return true; // fail-open
  }
}
```

In der `main()`-Funktion, nach dem Block `// Alle Spans verifiziert` (vor `process.exit(0)`), den Figure-Check einfügen:

```javascript
  // ---------------------------------------------------------------------------
  // Figure-Referenz-Check (additiv, nach Quote-Check)
  // ---------------------------------------------------------------------------
  const figureMatches = [...content.matchAll(FIGURE_REF_PATTERN)];
  for (const match of figureMatches) {
    const refText = match[0]; // z.B. "Abb. 3.4"
    const found = lookupFigureInVault(refText);
    if (!found) {
      const msg = [
        `[Figure-Guard] BLOCKIERT: Figure-Referenz nicht im Vault verifiziert.`,
        `Referenz: "${refText}"`,
        `Bitte Figure via figure-verifier oder vault.add_figure einpflegen.`,
        `Bypass: <!-- vault-guard: skip --> im Content ergaenzen (nur fuer Ausnahmefaelle).`,
      ].join('\n');
      process.stderr.write(msg + '\n');
      console.log(JSON.stringify({
        decision: 'block',
        reason: msg,
      }));
      process.exit(2);
    }
  }
```

- [ ] **Step 4: Tests grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_verbatim_figure_guard.py -v
```

Erwartet: alle Tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add hooks/verbatim-guard.mjs tests/test_verbatim_figure_guard.py && git commit -m "feat(F): verbatim-guard additiver Figure-Check + Tests"
```

---

## Task 7: Eval-Skeleton

**Files:**
- Create: `evals/figure-verifier/evals.json`

- [ ] **Step 1: Verzeichnis und Datei erstellen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.1-F/evals/figure-verifier
```

- [ ] **Step 2: evals.json schreiben**

```json
[
  {
    "id": "fv-01",
    "description": "Agent mit valider paper_id und Seite → figure_id non-empty",
    "type": "trigger",
    "input": {
      "paper_id": "test-paper-001",
      "page": 1
    },
    "expected": {
      "figure_id_non_empty": true
    }
  },
  {
    "id": "fv-02",
    "description": "Caption ≥ 50 Zeichen in vlm_description",
    "type": "trigger",
    "input": {
      "paper_id": "test-paper-001",
      "page": 2
    },
    "expected": {
      "vlm_description_min_length": 50
    }
  },
  {
    "id": "fv-03",
    "description": "Tabelle → data_extracted_json ist valides JSON-Array",
    "type": "trigger",
    "input": {
      "paper_id": "test-paper-001",
      "page": 3,
      "is_table": true
    },
    "expected": {
      "data_extracted_json_is_array": true
    }
  },
  {
    "id": "fv-04",
    "description": "Unbekannte Paper-ID → graceful error",
    "type": "trigger",
    "input": {
      "paper_id": "nonexistent-paper-xyz",
      "page": 1
    },
    "expected": {
      "error_graceful": true
    }
  },
  {
    "id": "fv-05",
    "description": "Mehrere Figures auf einer Seite → alle mit figure_id",
    "type": "trigger",
    "input": {
      "paper_id": "test-paper-001",
      "page": 4,
      "multiple_figures": true
    },
    "expected": {
      "all_figures_have_id": true
    }
  }
]
```

- [ ] **Step 3: Validierungstest (JSON-Syntax)**

In `tests/test_figure_verifier.py` ergänzen:

```python
def test_evals_json_valid():
    """evals/figure-verifier/evals.json muss valides JSON mit 5 Cases sein."""
    evals_path = Path(__file__).parent.parent / "evals" / "figure-verifier" / "evals.json"
    assert evals_path.exists(), f"evals.json fehlt: {evals_path}"
    with open(evals_path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "evals.json muss ein JSON-Array sein"
    assert len(data) == 5, f"Erwartet 5 Cases, gefunden: {len(data)}"
    ids = [c["id"] for c in data]
    assert ids == ["fv-01", "fv-02", "fv-03", "fv-04", "fv-05"]
```

- [ ] **Step 4: Tests grün bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/test_figure_verifier.py::test_evals_json_valid -v
```

Erwartet: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add evals/figure-verifier/evals.json tests/test_figure_verifier.py && git commit -m "feat(F): Eval-Skeleton fuer figure-verifier (5 Cases)"
```

---

## Task 8: Full Test Suite + Polish

- [ ] **Step 1: Vollständige Test Suite starten**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/ -v 2>&1 | tail -30
```

Erwartet: max. 1 vorbestehender Fehler (chapter-writer). Alle neuen Tests grün.

- [ ] **Step 2: Code-Simplifier auf Diff anwenden**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git diff main...HEAD -- mcp/academic_vault/db.py mcp/academic_vault/server.py mcp/academic_vault/migrate.py hooks/verbatim-guard.mjs > /tmp/chunk-F-diff.patch
```

Dann Code-Simplifier-Plugin auf geänderte Dateien anwenden (siehe polish-Schritt im mmp-Workflow).

- [ ] **Step 3: Nach Simplifier-Anwendung erneut Tests starten**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && python -m pytest tests/ -v 2>&1 | tail -20
```

Falls Tests scheitern: simplifier-Änderungen file-by-file rückgängig machen.

- [ ] **Step 4: Polish-Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-F && git add -p && git commit -m "chore: code-simplifier polish (Chunk F)"
```

- [ ] **Step 5: Lokales Code-Review**

`/code-review` aufrufen. Alle Findings ≥ 80 beheben. Max. 3 Iterationen.

---

## Self-Review gegen Spec

| AC | Abgedeckt in Task |
|---|---|
| Tabellen → strukturiertes JSON | Task 4 (`data_extracted_json`) + Task 7 (fv-03 Eval) |
| Bilder → LLM-Beschreibung ≥ 50 Zeichen | Task 5 (Agent-Qualitätskriterien) + Task 7 (fv-02) |
| Verbatim-Hook erkennt erfundene Figure-Verweise | Task 6 (`test_hook_blocks_unknown_figure_reference`) |
| Existing Quote-Checks keine Regression | Task 6 (`test_existing_quote_check_still_works`) |
| pytest grün | Task 8 (Full Suite) |
| `add_figures_table()` idempotent | Task 2 |
| `find_figure_by_caption` kein MCP-Tool | Task 4 (kein `@mcp.tool` Dekorator) |
| Hook Scope = isProtectedPath | Task 6 (`test_hook_ignores_non_protected_path`) |
| Fail-open bei fehlendem Vault | Task 6 (`test_hook_failopen_when_vault_missing`) |
| Eval-Skeleton 5 Cases | Task 7 |
