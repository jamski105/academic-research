"""Regressionstest fuer Issue #228:

commands/search.md weist Nutzer an, Batch-Jobs via `/history --batch <id>`
abzuholen (search.md:151,156). commands/history.md kannte dieses Flag aber
weder im `argument-hint` (Frontmatter :4) noch im Workflow-Body. Wer `--batch`
gemaess Anweisung aufrief, erhielt kein definiertes Verhalten.

Dieser Test kodiert das Akzeptanzkriterium:
  - `/academic-research:history --batch <id>` ist dokumentiert.

Reiner Markdown-Assert-Test (kein LLM-Call), analog zu test_fetch_command.py.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HISTORY_MD = REPO_ROOT / "commands" / "history.md"
SEARCH_MD = REPO_ROOT / "commands" / "search.md"


def _parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter delimited by '---' lines (ohne yaml-Dep)."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


# ---------------------------------------------------------------------------
# Voraussetzung: search.md verweist tatsaechlich auf /history --batch
# ---------------------------------------------------------------------------

def test_search_md_references_history_batch():
    """search.md verweist Nutzer auf /history --batch <id> (Quelle des Issues)."""
    content = SEARCH_MD.read_text(encoding="utf-8")
    assert "/history --batch" in content, (
        "search.md sollte weiterhin auf /history --batch verweisen "
        "(Grundlage von Issue #228)"
    )


# ---------------------------------------------------------------------------
# Akzeptanzkriterium: --batch in history.md dokumentiert
# ---------------------------------------------------------------------------

def test_history_md_argument_hint_documents_batch():
    """`--batch <id>` muss im argument-hint-Frontmatter von history.md stehen."""
    fm = _parse_frontmatter(HISTORY_MD)
    hint = fm.get("argument-hint", "")
    assert "--batch" in hint, (
        f"argument-hint von history.md dokumentiert --batch nicht: {hint!r}"
    )


def test_history_md_body_documents_batch_workflow():
    """history.md muss einen Workflow-Abschnitt fuer --batch-Abholung enthalten."""
    content = HISTORY_MD.read_text(encoding="utf-8")
    assert "--batch" in content, "history.md erwaehnt --batch ueberhaupt nicht"
    # Workflow muss den Batch-Status pruefen und Ergebnisse einlesen.
    assert "batch_id" in content or "Batch-Job" in content, (
        "history.md --batch-Workflow referenziert keine batch_id/Batch-Job"
    )
    assert "ended" in content, (
        "history.md --batch-Workflow prueft den Batch-Status 'ended' nicht"
    )


def test_history_md_batch_uses_batch_api_module():
    """Der --batch-Workflow muss das batch_api-Modul nutzen (load_batch_job)."""
    content = HISTORY_MD.read_text(encoding="utf-8")
    assert "batch_api" in content, (
        "history.md --batch-Workflow importiert das batch_api-Modul nicht"
    )
    assert "load_batch_job" in content, (
        "history.md --batch-Workflow nutzt load_batch_job nicht"
    )
