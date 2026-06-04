#!/usr/bin/env python3
"""Eval-Runner fuer verbatim-guard.

Laedt cases.json, befuellt eine temporaere SQLite-Datenbank mit den
"real"-Quotes, und prueft ob vault.search_quote_text() die echten Quotes
findet (pass) und die erfundenen nicht findet (block).

Aufruf: python3 evals/verbatim-guard/runner.py

Erwartet: 5/5 real → pass, 5/5 invented → block. FPR = 0 % < 5 % AC.
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

# Repo-Root aus diesem Datei-Pfad ableiten
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CASES_PATH = Path(__file__).parent / "cases.json"

VAULT_SRC = REPO_ROOT
sys.path.insert(0, str(VAULT_SRC))

# Importiert vault-Funktionen — schlaegt fehl wenn search_quote_text fehlt
from academic_vault.db import VaultDB  # noqa: E402
from academic_vault.server import search_quote_text  # noqa: E402


def _build_test_db(cases: list[dict]) -> str:
    """Erstellt eine temporaere SQLite-DB und befuellt sie mit 'real'-Quotes."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp.name
    tmp.close()

    # Schema initialisieren
    db = VaultDB(db_path)
    db.init_schema()

    # Dummy-Paper einfuegen (FK-Constraint)
    conn = VaultDB._open(db_path)
    now = int(time.time())
    conn.execute(
        """INSERT OR IGNORE INTO papers
           (paper_id, type, csl_json, added_at, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("eval-paper-1", "article-journal", '{"title":"Eval Paper"}', now, now),
    )
    conn.commit()

    # Echte Quotes einfuegen
    for case in cases:
        if case["in_vault"]:
            conn.execute(
                """INSERT INTO quotes
                   (quote_id, paper_id, verbatim, extraction_method, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid4()), "eval-paper-1", case["quote_text"], "manual", now),
            )
    conn.commit()
    conn.close()
    return db_path


def run_eval_cases() -> dict:
    """Fuehrt alle Eval-Cases aus und gibt strukturierte Ergebnisse zurueck.

    Importierbar (z. B. aus pytest), ohne zu printen oder ``sys.exit`` zu rufen.

    Rueckgabe:
        dict mit Schluesseln:
          - ``passed``  (int): Anzahl korrekt klassifizierter Cases
          - ``failed``  (int): Anzahl fehlklassifizierter Cases
          - ``total``   (int): Gesamtzahl der Cases
          - ``fpr``     (float): False-Positive-Rate in Prozent
                        (echter Quote faelschlich geblockt)
          - ``real_pass`` (bool): alle echten Quotes bestanden
          - ``invented_block`` (bool): alle erfundenen Quotes geblockt
          - ``details`` (list[dict]): pro Case id/type/status/expected/actual/hits
    """
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    db_path = _build_test_db(cases)

    results: dict = {"pass": 0, "fail": 0, "details": []}

    try:
        for case in cases:
            quote = case["quote_text"]
            expected = case["expected"]

            # Vault-Lookup
            hits = search_quote_text(db_path, quote)
            found = len(hits) > 0
            actual = "pass" if found else "block"

            ok = actual == expected
            status = "OK" if ok else "FAIL"
            results["pass" if ok else "fail"] += 1

            results["details"].append(
                {
                    "id": case["id"],
                    "type": case["type"],
                    "status": status,
                    "expected": expected,
                    "actual": actual,
                    "hits": len(hits),
                }
            )
    finally:
        os.unlink(db_path)

    # FPR berechnen: echter Quote, der geblockt wird = False Positive
    fp = sum(
        1 for d in results["details"] if d["type"] == "real" and d["actual"] == "block"
    )
    real_total = sum(1 for c in cases if c["type"] == "real")
    fpr = (fp / real_total * 100) if real_total > 0 else 0.0

    real_pass = all(
        d["status"] == "OK" for d in results["details"] if d["type"] == "real"
    )
    invented_block = all(
        d["status"] == "OK" for d in results["details"] if d["type"] == "invented"
    )

    return {
        "passed": results["pass"],
        "failed": results["fail"],
        "total": len(cases),
        "fpr": fpr,
        "real_pass": real_pass,
        "invented_block": invented_block,
        "details": results["details"],
    }


def run_eval() -> None:
    """CLI-Einstiegspunkt: fuehrt die Cases aus, printet Report, exit 1 bei Fehler."""
    summary = run_eval_cases()

    for d in summary["details"]:
        print(
            f"  [{d['status']}] Case {d['id']} ({d['type']}): "
            f"expected={d['expected']}, actual={d['actual']}, hits={d['hits']}"
        )

    total = summary["total"]
    passed = summary["passed"]
    failed = summary["failed"]

    print(f"\n{'='*50}")
    print(f"Ergebnis: {passed}/{total} korrekt ({failed} Fehler)")

    fpr = summary["fpr"]
    fp = sum(
        1 for d in summary["details"] if d["type"] == "real" and d["actual"] == "block"
    )
    real_total = sum(1 for d in summary["details"] if d["type"] == "real")
    print(f"False-Positive-Rate: {fp}/{real_total} = {fpr:.1f}% (AC: < 5 %)")

    # Acceptance Criteria pruefen
    real_pass = summary["real_pass"]
    invented_block = summary["invented_block"]

    print(f"\nAC-Check:")
    print(f"  Echte Quotes 100 % pass:      {'✅' if real_pass else '❌'}")
    print(f"  Erfundene Quotes 100 % block: {'✅' if invented_block else '❌'}")
    print(f"  FPR < 5 %:                    {'✅' if fpr < 5 else '❌'}")

    if failed > 0:
        sys.exit(1)
    print("\n✅ Alle Eval-Cases bestanden.")


if __name__ == "__main__":
    run_eval()
