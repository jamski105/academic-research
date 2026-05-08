-- academic_vault SQLite Schema
-- Tabellen: papers, papers_fts, quotes, quote_embeddings, decisions, notes
-- FTS5-Content-Table-Trigger: papers_ai, papers_ad, papers_au

CREATE TABLE IF NOT EXISTS papers (
  paper_id              TEXT PRIMARY KEY,
  type                  TEXT NOT NULL DEFAULT 'article-journal',
  csl_json              TEXT NOT NULL,
  doi                   TEXT,
  isbn                  TEXT,
  pdf_path              TEXT,
  file_id               TEXT,
  file_id_expires_at    INTEGER,
  page_offset           INTEGER DEFAULT 0,
  ocr_done              INTEGER DEFAULT 0,
  added_at              INTEGER NOT NULL,
  updated_at            INTEGER NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
  paper_id UNINDEXED,
  title,
  abstract,
  fulltext,
  content='papers',
  content_rowid='rowid'
);

CREATE TABLE IF NOT EXISTS quotes (
  quote_id          TEXT PRIMARY KEY,
  paper_id          TEXT NOT NULL REFERENCES papers(paper_id),
  verbatim          TEXT NOT NULL,
  pdf_page          INTEGER,
  printed_page      INTEGER,
  section           TEXT,
  context_before    TEXT,
  context_after     TEXT,
  extraction_method TEXT NOT NULL CHECK(extraction_method IN ('citations-api','manual')),
  api_response_id   TEXT,
  created_at        INTEGER NOT NULL
);

-- vec0 Virtual Table: optional, nur wenn sqlite-vec Extension geladen ist.
-- Wird in db.py per try/except erstellt; Fehler wird ignoriert.
-- CREATE VIRTUAL TABLE IF NOT EXISTS quote_embeddings USING vec0(
--   quote_id TEXT PRIMARY KEY,
--   embedding FLOAT[384]
-- );

CREATE TABLE IF NOT EXISTS decisions (
  decision_id   TEXT PRIMARY KEY,
  category      TEXT,
  text          TEXT NOT NULL,
  rationale     TEXT,
  created_at    INTEGER NOT NULL,
  superseded_by TEXT REFERENCES decisions(decision_id)
);

CREATE TABLE IF NOT EXISTS notes (
  note_id    TEXT PRIMARY KEY,
  paper_id   TEXT REFERENCES papers(paper_id),
  text       TEXT NOT NULL,
  tags       TEXT,
  created_at INTEGER NOT NULL
);

-- FTS5-Content-Table-Trigger: halten papers_fts synchron mit papers
CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
  INSERT INTO papers_fts(rowid, paper_id, title, abstract, fulltext)
  VALUES (
    new.rowid,
    new.paper_id,
    json_extract(new.csl_json, '$.title'),
    json_extract(new.csl_json, '$.abstract'),
    NULL
  );
END;

CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
  INSERT INTO papers_fts(papers_fts, rowid, paper_id, title, abstract, fulltext)
  VALUES (
    'delete',
    old.rowid,
    old.paper_id,
    json_extract(old.csl_json, '$.title'),
    json_extract(old.csl_json, '$.abstract'),
    NULL
  );
END;

CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
  INSERT INTO papers_fts(papers_fts, rowid, paper_id, title, abstract, fulltext)
  VALUES (
    'delete',
    old.rowid,
    old.paper_id,
    json_extract(old.csl_json, '$.title'),
    json_extract(old.csl_json, '$.abstract'),
    NULL
  );
  INSERT INTO papers_fts(rowid, paper_id, title, abstract, fulltext)
  VALUES (
    new.rowid,
    new.paper_id,
    json_extract(new.csl_json, '$.title'),
    json_extract(new.csl_json, '$.abstract'),
    NULL
  );
END;
