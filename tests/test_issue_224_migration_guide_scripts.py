"""Regression guard fuer Issue #224.

Der Migration-Guide (docs/MIGRATION-v5-to-v6.md) darf nur auf Skripte
verweisen, die tatsaechlich im Repo existieren. Ein frueherer Stand
verwies auf das nicht existente ``scripts/migrate_v5.py``.

Akzeptanzkriterium: Migration-Guide referenziert nur Befehle/Skripte,
die existieren.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MIGRATION_GUIDE = REPO_ROOT / "docs" / "MIGRATION-v5-to-v6.md"

# Erkennt Verweise wie ``scripts/migrate_v5.py`` oder ``scripts/foo/bar.py``
# innerhalb des Doku-Texts (auch in Code-Bloecken).
SCRIPT_REF_PATTERN = re.compile(r"scripts/[\w./-]+\.py")


def test_migration_guide_exists():
    assert MIGRATION_GUIDE.exists(), f"{MIGRATION_GUIDE} fehlt"


def test_migration_guide_references_only_existing_scripts():
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    referenced = set(SCRIPT_REF_PATTERN.findall(text))
    missing = sorted(ref for ref in referenced if not (REPO_ROOT / ref).exists())
    assert not missing, (
        "Migration-Guide referenziert nicht existente Skripte:\n"
        + "\n".join(missing)
    )


def test_migration_guide_does_not_mention_migrate_v5_script():
    """``migrate_v5.py`` wurde nie ausgeliefert und darf nicht referenziert werden."""
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    assert "migrate_v5.py" not in text, (
        "Migration-Guide verweist auf das nicht existente Skript migrate_v5.py. "
        "Stattdessen die automatische Migration "
        "(/academic-research:setup --migrate-v5) dokumentieren."
    )
