"""Regressionstest fuer Issue #203 — PyPDF2 -> pypdf-Migration.

Akzeptanzkriterien (aus dem Issue):
  - requirements.txt: `PyPDF2>=3.0.0` -> `pypdf>=4.0.0` (kein PyPDF2 mehr gelistet).
  - Keine `import PyPDF2` / `from PyPDF2`-Statements mehr im Repo-Code.
  - `_get_pdf_reader()`-Compat-Pattern (try PyPDF2 / fallback pypdf) entfernt.
  - pypdf wird produktiv genutzt (import pypdf / from pypdf ...).

Der Test scannt den realen Quellcode (scripts/, skills/, academic_vault/,
tests/) und die requirements-Dateien. Er ist bewusst inhaltsbasiert, damit er
auf dem aktuellen (noch nicht migrierten) Stand ROT ist und nach der Migration
GRUEN wird.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Verzeichnisse mit produktivem bzw. test-relevantem Python-Code.
SCAN_DIRS = ["scripts", "skills", "academic_vault", "tests"]

# Diese Testdatei selbst enthaelt das Wort "PyPDF2" als String — ausschliessen.
SELF = Path(__file__).resolve()

# Importe, die nicht mehr vorkommen duerfen.
_IMPORT_PYPDF2 = re.compile(r"^\s*(import\s+PyPDF2|from\s+PyPDF2)\b", re.MULTILINE)


def _python_files() -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if p.resolve() == SELF:
                continue
            # Verschachtelte Worktrees ausschliessen (relativ zum Repo-Root,
            # da der Repo-Root selbst in einem Worktree-Pfad liegen kann).
            rel = p.resolve().relative_to(REPO_ROOT)
            if str(rel).startswith(".claude/worktrees"):
                continue
            files.append(p)
    return files


def test_requirements_uses_pypdf_not_pypdf2():
    req = REPO_ROOT / "scripts" / "requirements.txt"
    text = req.read_text(encoding="utf-8")
    assert not re.search(r"(?im)^\s*PyPDF2\b", text), (
        "scripts/requirements.txt listet noch PyPDF2 — auf pypdf umstellen."
    )
    assert re.search(r"(?im)^\s*pypdf\b", text), (
        "scripts/requirements.txt muss pypdf listen."
    )


def test_no_pypdf2_imports_remain():
    offenders = []
    for p in _python_files():
        text = p.read_text(encoding="utf-8")
        if _IMPORT_PYPDF2.search(text):
            offenders.append(str(p.relative_to(REPO_ROOT)))
    assert not offenders, (
        "Noch PyPDF2-Importe vorhanden in:\n  " + "\n  ".join(offenders)
    )


def test_no_pypdf2_compat_helper_remains():
    """_get_pdf_reader() durfte PyPDF2 als bevorzugte Quelle nutzen — weg damit."""
    po = REPO_ROOT / "scripts" / "page_offset.py"
    text = po.read_text(encoding="utf-8")
    assert "PyPDF2" not in text, (
        "scripts/page_offset.py darf PyPDF2 nicht mehr referenzieren "
        "(Compat-Pattern entfernen)."
    )


def test_pypdf_is_used_in_scripts():
    """Mindestens ein produktives scripts/-Modul nutzt pypdf direkt."""
    pat = re.compile(r"^\s*(import\s+pypdf|from\s+pypdf)\b", re.MULTILINE)
    scripts_dir = REPO_ROOT / "scripts"
    found = any(
        pat.search(p.read_text(encoding="utf-8"))
        for p in scripts_dir.rglob("*.py")
    )
    assert found, "Kein scripts/-Modul importiert pypdf."


def test_chunk_pdf_imports_pypdf():
    text = (REPO_ROOT / "scripts" / "chunk_pdf.py").read_text(encoding="utf-8")
    assert "from pypdf import PdfReader, PdfWriter" in text
    assert "from pypdf.generic import" in text
    assert "PyPDF2" not in text
