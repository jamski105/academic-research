"""migrate.py — Seed-Skript: literature_state.md + PDFs -> SQLite-Vault.

CLI:
    python migrate.py --state literature_state.md --pdf-dir ./pdfs --db vault.db

Parst YAML-Frontmatter-aehnliche Bloecke aus Markdown-Listeneintraegen.
Idempotent (INSERT OR REPLACE via add_paper-Upsert).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def _parse_literature_state(state_path: str) -> list[dict]:
    """Parst literature_state.md und gibt Liste von Paper-Dicts zurueck.

    Erwartet Eintraege im Format:
        ### citekey
        - title: ...
        - authors: ...
        - year: ...
        - doi: ...
        - pdf_path: ...

    Alternativ: YAML-Frontmatter-Bloecke zwischen ---
    """
    text = Path(state_path).read_text(encoding="utf-8")
    papers = []

    # Versuch 1: YAML-Frontmatter-Bloecke zwischen ---
    frontmatter_pattern = re.compile(r"---\s*\n(.*?)\n---", re.DOTALL)
    for match in frontmatter_pattern.finditer(text):
        block = match.group(1)
        paper = _parse_yaml_block(block)
        if paper.get("citekey") or paper.get("title"):
            papers.append(paper)

    if papers:
        return papers

    # Versuch 2: Markdown-Sektionen mit ### citekey + Listenwerten
    section_pattern = re.compile(
        r"^#{1,4}\s+(.+?)\s*\n((?:^[ \t]*[-*]\s+\S+.*\n?)*)",
        re.MULTILINE,
    )
    for match in section_pattern.finditer(text):
        citekey = match.group(1).strip()
        body = match.group(2)
        paper = _parse_list_block(body)
        if paper.get("title") or paper.get("doi"):
            paper.setdefault("citekey", citekey)
            papers.append(paper)

    return papers


def _parse_yaml_block(block: str) -> dict:
    """Parst einfaches YAML (kein nested). Gibt dict zurueck."""
    result = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _parse_list_block(block: str) -> dict:
    """Parst Markdown-Listenwerte (- key: value)."""
    result = {}
    for line in block.splitlines():
        line = line.strip().lstrip("-*").strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _build_csl_json(paper: dict) -> str:
    """Baut minimales CSL-JSON aus geparsten Feldern."""
    csl: dict = {}
    if paper.get("title"):
        csl["title"] = paper["title"]
    if paper.get("abstract"):
        csl["abstract"] = paper["abstract"]
    if paper.get("year"):
        try:
            csl["issued"] = {"date-parts": [[int(paper["year"])]]}
        except ValueError:
            pass
    if paper.get("authors"):
        raw = paper["authors"]
        names = [n.strip() for n in raw.split(";") if n.strip()]
        csl["author"] = [{"literal": n} for n in names]
    if paper.get("doi"):
        csl["DOI"] = paper["doi"]
    if paper.get("isbn"):
        csl["ISBN"] = paper["isbn"]
    if paper.get("type"):
        csl["type"] = paper["type"]
    return json.dumps(csl, ensure_ascii=False)


def run_migration(
    state_path: str,
    pdf_dir: str,
    db_path: str,
) -> dict:
    """Fuehrt Migration aus. Gibt {inserted, skipped, errors} zurueck."""
    from mcp.academic_vault.db import VaultDB

    db = VaultDB(db_path)
    db.init_schema()

    papers = _parse_literature_state(state_path)
    inserted = 0
    skipped = 0
    errors = 0

    for paper in papers:
        try:
            citekey = paper.get("citekey") or paper.get("title", "unknown")
            paper_id = re.sub(r"[^a-zA-Z0-9_-]", "_", citekey)

            # PDF-Pfad aufloesen
            pdf_path = paper.get("pdf_path")
            if pdf_path:
                candidate = Path(pdf_dir) / pdf_path
                if candidate.exists():
                    pdf_path = str(candidate)
                elif Path(pdf_path).exists():
                    pdf_path = str(Path(pdf_path))
                else:
                    pdf_path = None

            csl_json = _build_csl_json(paper)

            # Idempotenz: paper_id bereits vorhanden?
            existing = db.get_paper(paper_id)
            if existing is not None:
                skipped += 1
                continue

            db.add_paper(
                paper_id=paper_id,
                csl_json=csl_json,
                doi=paper.get("doi"),
                isbn=paper.get("isbn"),
                pdf_path=pdf_path,
            )
            inserted += 1
        except Exception as exc:
            print(f"[ERROR] Paper '{paper.get('citekey', '?')}': {exc}", file=sys.stderr)
            errors += 1

    return {"inserted": inserted, "skipped": skipped, "errors": errors}


def add_book_columns(db_path: str) -> None:
    """Fuegt book/chapter-Spalten zu papers hinzu. Idempotent (try/except pro Spalte).

    Aufruf-Sicher: Kann mehrfach auf derselben DB ausgefuehrt werden.
    """
    import sqlite3 as _sqlite3
    new_cols = [
        ("editor", "TEXT"),
        ("chapter", "TEXT"),
        ("page_first", "INTEGER"),
        ("page_last", "INTEGER"),
        ("container_title", "TEXT"),
    ]
    conn = _sqlite3.connect(db_path)
    try:
        for col, coltype in new_cols:
            try:
                conn.execute(f"ALTER TABLE papers ADD COLUMN {col} {coltype}")
            except _sqlite3.OperationalError:
                pass  # Spalte existiert bereits -- idempotent
        conn.commit()
    finally:
        conn.close()


def add_parent_paper_id_column(db_path: str) -> None:
    """Fuegt parent_paper_id-Spalte zu papers hinzu. Idempotent (try/except).

    Aufruf-Sicher: Kann mehrfach auf derselben DB ausgefuehrt werden.
    """
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    try:
        try:
            conn.execute(
                "ALTER TABLE papers ADD COLUMN "
                "parent_paper_id TEXT REFERENCES papers(paper_id)"
            )
        except _sqlite3.OperationalError:
            pass  # Spalte existiert bereits -- idempotent
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed-Migration: literature_state.md -> academic_vault SQLite"
    )
    parser.add_argument(
        "--state",
        required=True,
        help="Pfad zur literature_state.md",
    )
    parser.add_argument(
        "--pdf-dir",
        default=".",
        help="Verzeichnis mit PDF-Dateien (default: .)",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Pfad zur SQLite-Vault-Datenbank",
    )
    args = parser.parse_args()

    if not Path(args.state).exists():
        print(f"[ERROR] state-Datei nicht gefunden: {args.state}", file=sys.stderr)
        sys.exit(1)

    result = run_migration(args.state, args.pdf_dir, args.db)
    print(
        f"Migration abgeschlossen: "
        f"inserted={result['inserted']}, "
        f"skipped={result['skipped']}, "
        f"errors={result['errors']}"
    )


if __name__ == "__main__":
    main()
