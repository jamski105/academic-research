# Vault-Architektur — Anhang zum v6-Audit

**Erstellt:** 2026-05-07 · **Bezug:** `docs/AUDIT-v6-roadmap.md` §F7–F9
**Frage:** Wie bekommen wir einen externen Speicher, in dem Claude PDFs,
Metadaten und Zitate so ablegt, dass er token-sparend zugreifen kann und
**garantiert nicht halluziniert**? Reicht Zotero, oder gibt es Besseres?

**Kurzantwort:** Zotero allein reicht nicht. Optimal ist ein eigener
**MCP-Server `academic-vault`** mit Zotero als optionalem Frontend-Layer.
Begründung & Architektur unten.

---

## 1 · Warum Zotero allein nicht ausreicht

| Anforderung | Zotero pur | Bemerkung |
|---|---|---|
| PDF-Storage | ✅ | hash-basierte Ordner, schwer für Tools |
| Metadaten (BibTeX/CSL) | ✅ | sehr gut, Better-BibTeX als Plugin |
| Volltext-Index | ⚠️ | Zotero hat eigenen FTS, aber kein API-Zugriff |
| Semantische Suche | ❌ | nicht eingebaut |
| Zitat-Cache mit Seitenangabe | ❌ | nichts — würde aus PDF jedesmal neu extrahiert |
| Halluzinationsschutz | ❌ | Zotero validiert Output-Texte nicht |
| Token-effiziente Tool-Calls | ❌ | Web-API gibt komplette Items, kein Snippet-Retrieval |
| Cross-Session Memory | ⚠️ | nur Items, keine Decisions/Notes |
| Decision-Log | ❌ | gibt es nicht |

**Ergebnis:** Zotero ist eine sehr gute **User-UI** (PDF-Annotation,
manuelles Tagging, Bibliographien-Export), aber kein Anti-Halluzinations-
Backend. Der Vault muss zusätzlich existieren.

---

## 2 · Inventar: Was es bereits gibt

### 2.1 Zotero-MCP-Server

| Repo | Typ | Stärken | Schwächen |
|---|---|---|---|
| **`54yyyu/zotero-mcp`** (Python, pip) | Standalone-MCP | pyzotero-basiert, semantic search, PyPI-Install | externer Prozess, nicht plugin-internal |
| **`cookjohn/zotero-mcp`** (Zotero-Plugin) | Zotero-Plugin mit MCP via Streamable HTTP | keine separate Installation, läuft im Zotero | nur solange Zotero offen |
| **`ZotPilot`** | MCP-Server | semantic search auf `zotero.sqlite`, draft-LR | reines Read-Tool |

### 2.2 Komplett-Lösungen

| Repo | Was es macht | Eignung |
|---|---|---|
| **`Psypeal/claude-knowledge-vault`** | Claude-Code-Plugin, ingest Zotero/PubMed/arXiv → Wiki + Obsidian | gut als Inspiration, eigene Pfade |
| **`WenyuChiou/research-hub`** | MCP für Zotero+Obsidian+NotebookLM | sehr nah dran, aber nicht plugin-internal |
| **`Galaxy-Dawn/claude-scholar`** | ideation→writing assistant | Workflow, kein Vault |
| **PaperQA2 (Future-House)** | RAG-Agent für Paper-QA mit Citations | Inspirations-Quelle, eigenes CLI |
| **Letta (MemGPT)** | Memory-OS, 83.2 % LongMemEval | Memory-Layer, kein Citation-Backend |
| **Mem0** | Bolt-on Memory | zu generisch für unsere Use-Cases |

### 2.3 Tech-Bausteine

- **`sqlite-vec`** (Alex Garcia) — embedded vector search, KNN, SIMD, dependency-free
- **SQLite-FTS5** — bereits Built-in, BM25 ranking
- **pyzotero** — Zotero-Web-API-Client (OAuth1 read+write)
- **Anthropic Files API** — `file_id` für PDFs, kein Re-Upload
- **Anthropic Citations API** — `page_location` / `char_location`
- **Anthropic Memory-Tool** — File-basiertes Cross-Session-Memory
- **Model2Vec** / **Voyage-3** / **Granite-Embedding** — lokale Embeddings

---

## 3 · Drei Architektur-Optionen

### Option A — "Build the Vault" (eigener MCP-Server)

```
┌─────────────────────────────────────────────────────────┐
│            academic-vault (eigener MCP)                 │
├─────────────────────────────────────────────────────────┤
│  SQLite           : papers, quotes, decisions, files    │
│  FTS5             : Volltext-Suche über pdf_text        │
│  sqlite-vec       : semantic search über chunk_embed    │
│  Files-API-Cache  : pdf_path → file_id (TTL)            │
│  Citation-Cache   : (paper_id, page) → verbatim         │
└─────────────────────────────────────────────────────────┘
                ▲
                │ MCP tools
                │
   ┌────────────┴────────────┐
   │  academic-research      │
   │  Skills/Agents/Commands │
   └─────────────────────────┘
```

**MCP-Tools (Auswahl):**

```
vault.search(query, type?, top_k?)        → [paper_id, snippet, score]
vault.get_paper(paper_id)                  → metadata + pdf_status
vault.get_quote(quote_id)                  → verbatim + page + paper_id
vault.find_quotes(paper_id, query, k?)     → [quote_id, ...]
vault.add_quote(paper_id, quote)           → quote_id (mit Provenance)
vault.add_note(paper_id, note)             → note_id
vault.add_decision(text, category)         → decision_id
vault.list_decisions(category?)            → [decision, ...]
vault.import_zotero(library_id, key)       → import_log
vault.ensure_file(pdf_path)                → file_id (cached)
vault.stats()                              → counts + token-savings
```

**Datenmodell (SQLite-Schema, gekürzt):**

```sql
CREATE TABLE papers (
  paper_id TEXT PRIMARY KEY,            -- citekey oder uuid
  type TEXT NOT NULL,                   -- article-journal | book | chapter
  csl_json TEXT NOT NULL,               -- volle CSL-JSON-Daten
  doi TEXT, isbn TEXT,
  pdf_path TEXT,                        -- lokaler Pfad
  file_id TEXT,                         -- Anthropic Files-API
  file_id_expires_at INTEGER,
  page_offset INTEGER DEFAULT 0,        -- pdf_page → printed_page
  ocr_done BOOLEAN DEFAULT 0,
  added_at INTEGER, updated_at INTEGER
);

CREATE VIRTUAL TABLE papers_fts USING fts5(
  title, abstract, fulltext, content='papers'
);

CREATE TABLE quotes (
  quote_id TEXT PRIMARY KEY,
  paper_id TEXT REFERENCES papers,
  verbatim TEXT NOT NULL,
  pdf_page INTEGER,
  printed_page INTEGER,                 -- mit page_offset korrigiert
  section TEXT,
  context_before TEXT, context_after TEXT,
  extraction_method TEXT NOT NULL,      -- 'citations-api' | 'manual'
  api_response_id TEXT,                 -- Anthropic-Request-ID für Audit
  created_at INTEGER
);

CREATE VIRTUAL TABLE quote_embeddings USING vec0(
  quote_id TEXT PRIMARY KEY,
  embedding FLOAT[384]                  -- Model2Vec dims
);

CREATE TABLE decisions (
  decision_id TEXT PRIMARY KEY,
  category TEXT,                        -- citation_style | methodology | ...
  text TEXT NOT NULL,
  rationale TEXT,
  created_at INTEGER,
  superseded_by TEXT REFERENCES decisions
);

CREATE TABLE notes (
  note_id TEXT PRIMARY KEY,
  paper_id TEXT REFERENCES papers,
  text TEXT NOT NULL,
  tags TEXT,                            -- JSON-Array
  created_at INTEGER
);
```

**Halluzinationsschutz, hart verdrahtet:**

- `vault.add_quote(...)` akzeptiert nur Quotes mit `extraction_method: 'citations-api'` und füllten `api_response_id` — Manuelle Quotes brauchen explizites `--manual`-Flag
- Hook `PreToolUse` für `Write` mit Pfad-Match auf `kapitel/*.md`: parst zitierte Strings (Anführungszeichen-Spans), greppt im Vault → unbekannte Strings führen zu Block + Hinweis „Zitat nicht im Vault, bitte über `quote-extractor` ziehen"
- Skills lesen Zitate **nur** über `vault.get_quote(id)` — Direkter PDF-Lese-Pfad ist deprecated

**Pro/Contra:**

- ✅ Volle Kontrolle, perfekt auf Plugin-Use-Cases getunt
- ✅ Halluzinationsschutz hart verdrahtbar
- ✅ Token-effizient (gezielte Tool-Calls statt PDF in Context)
- ✅ Cross-Session-Persistenz garantiert
- ✅ Lock-in vermeidbar (SQLite portabel, JSON-Export trivial)
- ❌ ~600–900 LOC Python (MCP-Server in `mcp` Python-SDK)
- ❌ 1 Sprint Aufwand (geschätzt 1 Woche)

**Aufwand:** ~1 Woche (1 Sprint)

---

### Option B — "Ride zotero-mcp" (bestehenden MCP nutzen)

```
┌─────────────────────────┐         ┌──────────────────────┐
│  zotero-mcp (54yyyu)    │◄────────│ academic-research    │
│  pyzotero + semantic    │  MCP    │ Skills/Commands      │
│  Zotero Web API v3      │         └──────────────────────┘
└─────────────────────────┘
```

**Pro/Contra:**

- ✅ Kein eigener Code, sofort einsetzbar (`pip install zotero-mcp`)
- ✅ Community-maintained
- ✅ Nutzt vorhandene Zotero-Library als Backend
- ❌ Lock-in auf Zotero-Schema (User muss Zotero-Account haben)
- ❌ Kein Citation-Cache mit Provenance — Zitate werden bei jedem Bedarf neu extrahiert
- ❌ Halluzinationsschutz nur soft (kein Hook-basierter Block)
- ❌ Files-API-Cache nicht trivial integrierbar
- ❌ Decisions/Notes brauchen Zotero-Notes-Hack
- ❌ Bei großen Libraries (>5000 Items) Performance-Themen

**Aufwand:** 1 Tag (Integration + Doku)

---

### Option C — "Vault + Zotero-Bridge" (**empfohlen**)

```
                  ┌─────────────────────────────┐
                  │   academic-vault (eigener)  │  ← Halluzinations-
                  │                             │     kritisch
                  │   - papers, quotes,         │
                  │     decisions, notes        │
                  │   - SQLite + FTS5 +         │
                  │     sqlite-vec              │
                  │   - Files-API-Cache         │
                  └────────┬─────────┬──────────┘
                           ▲         │
                  pull-only│         │PDF-Bundle-Export
                           │         │
              ┌────────────┴┐       ┌▼────────────────┐
              │   Zotero    │       │  NotebookLM     │  ← optionale
              │  (Frontend) │       │  (Triage, opt.) │     Bridges
              │  pyzotero   │       │  Bücher >600 S. │
              └─────────────┘       └─────────────────┘
```

**Komponenten:**

1. **`academic-vault` MCP-Server** (eigener) — Single Source of Truth für
   alles Zitat-/Halluzinations-Kritische
2. **`zotero-import` Skill** — pyzotero-Pull, dedupliziert via DOI/ISBN
3. **`notebook-bundle` Skill (optional)** — packt PDF-Bundle für
   manuellen Upload in NotebookLM (für Bücher >600 Seiten)

**Pro/Contra:**

- ✅ Halluzinationsschutz hart (eigener Vault)
- ✅ User-Frontend frei wählbar (Zotero oder keins)
- ✅ Kein Lock-in auf einzelnes Tool
- ✅ Token-effizient
- ✅ Inkrementell ausrollbar (zuerst Vault, dann Bridges)
- ❌ Eigener MCP-Server zu maintainen
- ❌ ~1.5 Sprints Aufwand

**Aufwand:** ~1.5 Wochen (1 Sprint Vault + 0.5 Sprint Zotero-Bridge)

---

## 4 · Token-Spar-Mechanik im Detail

**Heute (v5.4):** Skill `chapter-writer` lädt
`literature_state.md` (alle Quellen-Stubs) + relevante PDF-Auszüge
manuell pro Aufruf. ≈ 8–15 k Token Boilerplate.

**Mit Vault:**

```
1. chapter-writer ruft: vault.search("DevOps Governance Compliance", k=5)
   → 5 paper_ids + 1-Satz-Snippets  (≈ 200 Token)

2. Pro Paper-ID: vault.find_quotes(paper_id, query, k=3)
   → 15 quote_ids + verbatim + page  (≈ 1500 Token total)

3. chapter-writer schreibt; Hook validiert Verbatim-Strings gegen Vault.

Total: ~1700 Token statt 10000+ → ~83 % Ersparnis pro Kapitel-Iteration.
```

**Anti-Halluzinations-Garantie:**

- Zitate im Output, die nicht in `quotes`-Tabelle existieren → Hook blockt Write
- Seitenangaben werden nicht vom Modell „erinnert", sondern aus
  `quotes.printed_page` materialisiert → keine `(Müller 2023, S. 47)`-
  Halluzination möglich
- Decisions („Wir nutzen IEEE statt APA") sind Tool-Antworten, nicht
  Modell-Erinnerungen

---

## 5 · Migration aus heutigem Stand

**Phase 1 — Vault-Foundation (Sprint v6.0)**
- MCP-Server-Skeleton mit SQLite-Schema
- Tools: `vault.search`, `vault.get_paper`, `vault.add_quote`,
  `vault.ensure_file`
- Migration-Skript: `literature_state.md` + PDFs → SQLite-Initial-Seed

**Phase 2 — Skill-Anpassung (Sprint v6.0)**
- `quote-extractor` schreibt in `vault.add_quote()` statt JSON-File
- `chapter-writer` liest via `vault.find_quotes()`
- Hook für Verbatim-Validation

**Phase 3 — Bridges (Sprint v6.3)**
- `zotero-import` (pyzotero pull-only)
- `notebook-bundle` (PDF-Pack für NotebookLM)

**Phase 4 — Memory & Decisions (Sprint v6.4)**
- `vault.add_decision` integriert in alle Skills
- `decisions.log` exportierbar als PRISMA-Audit-Trail

**Backwards-Compat:** `literature_state.md` bleibt als
**read-only Snapshot-Export** aus dem Vault — Nutzer:innen, die nur
Markdown wollen, sehen kein Regression.

---

## 6 · Empfehlung

**Option C** ("Vault + Zotero-Bridge"). Begründung:

1. **Halluzinationsschutz** ist das Killer-Feature — nur mit eigenem Vault
   hart verdrahtbar (Hook-basierte Verbatim-Validation)
2. **Token-Ersparnis** ~80 % messbar — Tool-Calls statt Context-Stuffing
3. **Lock-in vermeiden** — User können Zotero-Frontend nutzen oder ohne
4. **Inkrementell** — Phase 1+2 liefern schon 80 % des Wertes,
   Zotero-Bridge (Phase 3) ist nice-to-have
5. **Plugin-intern** — kein zweites Repo zu maintainen,
   `mcp/academic-vault/` als Sub-Tree

**Risiko-Mitigation:**

- Vendor-Drift Anthropic Files-API (Beta) → Fallback auf `pdf_path`
- sqlite-vec Build-Abhängigkeit → Fallback auf reine FTS5
- Memory-Tool noch nicht Cross-Session ohne Managed-Agents → Vault
  übernimmt diese Rolle eigenständig

---

## 7 · Quellen (neu hinzugekommen)

- `Psypeal/claude-knowledge-vault` — `github.com/Psypeal/claude-knowledge-vault`
- `54yyyu/zotero-mcp` — `github.com/54yyyu/zotero-mcp`
- `cookjohn/zotero-mcp` — `github.com/cookjohn/zotero-mcp`
- `WenyuChiou/research-hub` — `github.com/WenyuChiou/research-hub`
- `Future-House/paper-qa` (PaperQA2) — `github.com/future-house/paper-qa`
- `letta-ai/letta` (MemGPT) — `letta.com`
- `mem0ai/mem0` — `mem0.ai`
- `asg017/sqlite-vec` — `github.com/asg017/sqlite-vec`
- `Galaxy-Dawn/claude-scholar` — `github.com/Galaxy-Dawn/claude-scholar`
- ZotPilot Forum-Post — `forums.zotero.org/discussion/130483`
