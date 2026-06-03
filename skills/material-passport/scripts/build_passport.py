"""build_passport.py — Material-Passport Wrapper-Script (v6.4, Ticket #104).

Ruft vault.export_material_passport auf, ergaenzt kapitel/methodik.md um einen
"## Reproduzierbarkeit"-Block und sperrt optional den Vault via vault.lock_passport.

Aufruf:
    python skills/material-passport/scripts/build_passport.py \\
        --db vault.db \\
        --slug mein-projekt \\
        --output-dir . \\
        --methodik kapitel/methodik.md \\
        [--lock]

Flags:
    --db         Pfad zur Vault-SQLite-Datenbank (Pflicht)
    --slug       Projekt-Slug (Pflicht)
    --output-dir Verzeichnis fuer material-passport.json (Standard: .)
    --methodik   Pfad zu kapitel/methodik.md (Standard: kapitel/methodik.md)
    --lock       Sperrt den Vault nach Export (Repro-Lock)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from academic_vault import server as vault_server

# Reproduzierbarkeits-Block-Marker — verhindert Doppel-Eintraege
_REPRO_MARKER = "## Reproduzierbarkeit"

_REPRO_BLOCK_TEMPLATE = """

## Reproduzierbarkeit

Dieser Abschnitt wurde automatisch durch den Material-Passport Skill generiert.

Ein vollstaendiges Reproduzierbarkeits-Manifest (paper_ids, DOIs, Score-Versionen,
Modellversionen, PDF-Hashes und Decision-Snapshots) wurde exportiert:

- **Datei:** `material-passport.json` (im Projektverzeichnis)
- **Passport-Hash:** wird bei jeder Generierung neu berechnet

Zum Verifizieren der Reproduzierbarkeit:
1. `material-passport.json` oeffnen und `passport_hash` notieren
2. `build_passport.py` erneut ausfuehren (gleiches Datum, gleiche Paper) →
   Hash muss identisch sein, wenn kein neues Material hinzugefuegt wurde

> Der Vault wurde gesperrt (Repro-Lock): keine weiteren Aenderungen nach Abgabe.
"""

_REPRO_BLOCK_TEMPLATE_UNLOCKED = """

## Reproduzierbarkeit

Dieser Abschnitt wurde automatisch durch den Material-Passport Skill generiert.

Ein vollstaendiges Reproduzierbarkeits-Manifest (paper_ids, DOIs, Score-Versionen,
Modellversionen, PDF-Hashes und Decision-Snapshots) wurde exportiert:

- **Datei:** `material-passport.json` (im Projektverzeichnis)
- **Passport-Hash:** wird bei jeder Generierung neu berechnet

Zum Verifizieren der Reproduzierbarkeit:
1. `material-passport.json` oeffnen und `passport_hash` notieren
2. `build_passport.py` erneut ausfuehren (gleiches Datum, gleiche Paper) →
   Hash muss identisch sein, wenn kein neues Material hinzugefuegt wurde
"""


def _update_methodik(methodik_path: Path, passport_path: str, locked: bool) -> None:
    """Ergaenzt methodik.md um den Reproduzierbarkeits-Block (idempotent)."""
    if methodik_path.exists():
        content = methodik_path.read_text(encoding="utf-8")
    else:
        content = "# Methodik\n"

    # Idempotenz: Block nur einmal einfuegen
    if _REPRO_MARKER in content:
        return

    block = _REPRO_BLOCK_TEMPLATE if locked else _REPRO_BLOCK_TEMPLATE_UNLOCKED
    content = content.rstrip() + block
    methodik_path.parent.mkdir(parents=True, exist_ok=True)
    methodik_path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Material-Passport exportieren und methodik.md aktualisieren."
    )
    parser.add_argument("--db", required=True, help="Pfad zur Vault-DB")
    parser.add_argument("--slug", required=True, help="Projekt-Slug")
    parser.add_argument("--output-dir", default=".", help="Ausgabeverzeichnis fuer JSON")
    parser.add_argument(
        "--methodik",
        default="kapitel/methodik.md",
        help="Pfad zu kapitel/methodik.md",
    )
    parser.add_argument(
        "--lock",
        action="store_true",
        help="Vault nach Export sperren (Repro-Lock, irreversibel)",
    )
    args = parser.parse_args(argv)

    db_path = args.db
    slug = args.slug
    output_dir = args.output_dir
    methodik_path = Path(args.methodik)
    do_lock = args.lock

    # Lock-Check: Vault bereits gesperrt?
    try:
        locked = vault_server.is_locked(db_path=db_path, slug=slug)
    except Exception as exc:
        print(f"FEHLER: Vault-Lock-Status konnte nicht gelesen werden: {exc}", file=sys.stderr)
        return 1

    if locked:
        print(
            f"FEHLER: Vault fuer Slug '{slug}' ist gesperrt (Repro-Lock).\n"
            "Der Passport wurde bereits finalisiert und der Vault ist read-only.\n"
            "Kein erneuter Export moeglich.",
            file=sys.stderr,
        )
        return 2

    # Material-Passport exportieren
    try:
        out_path = vault_server.export_material_passport(
            db_path=db_path,
            slug=slug,
            output_dir=output_dir,
        )
    except Exception as exc:
        print(f"FEHLER beim Exportieren des Material-Passports: {exc}", file=sys.stderr)
        return 1

    # methodik.md aktualisieren
    try:
        _update_methodik(methodik_path, out_path, locked=do_lock)
    except Exception as exc:
        print(f"WARNUNG: methodik.md konnte nicht aktualisiert werden: {exc}", file=sys.stderr)
        # Kein harter Fehler — Passport wurde schon geschrieben

    # Optional: Vault sperren
    if do_lock:
        try:
            vault_server.lock_passport(db_path=db_path, slug=slug)
            print(f"Vault fuer '{slug}' gesperrt (Repro-Lock aktiv).")
        except Exception as exc:
            print(f"WARNUNG: Vault konnte nicht gesperrt werden: {exc}", file=sys.stderr)

    print(f"Material-Passport exportiert: {out_path}")
    print(f"methodik.md aktualisiert: {methodik_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
