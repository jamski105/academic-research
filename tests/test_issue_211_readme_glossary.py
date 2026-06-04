"""Regressionstest für Issue #211: README-Glossar muss v6-Begriffe erklären.

Das README-Glossar (Sektion 15) muss zentrale v6-Begriffe definieren:
Decision-Log, Vault-Lock, OCR-Detection, page_offset, output_targets,
Repro-Lock, Contextual Retrieval, RRF. Jeder Begriff braucht eine eigene
Glossar-Zeile mit Definition.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
README = REPO_ROOT / "README.md"

# v6-Begriffe, die im Glossar definiert sein müssen (Issue #211).
REQUIRED_TERMS = [
    "Decision-Log",
    "Vault-Lock",
    "OCR-Detection",
    "page_offset",
    "output_targets",
    "Repro-Lock",
    "Contextual Retrieval",
    "RRF",
]


def _glossary_section() -> str:
    """Extrahiert den Glossar-Abschnitt aus dem README."""
    text = README.read_text(encoding="utf-8")
    m = re.search(r"^## Glossar\s*$", text, flags=re.MULTILINE)
    assert m, "README enthält keine '## Glossar'-Sektion"
    start = m.end()
    nxt = re.search(r"^## ", text[start:], flags=re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    return text[start:end]


def _glossary_entries(section: str) -> dict[str, str]:
    """Mappt Glossar-Begriff (bold in Spalte 1) auf seine Bedeutung."""
    entries: dict[str, str] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        term = cells[0]
        meaning = cells[1]
        # Header- und Trennzeilen überspringen.
        if term.lower() in {"begriff", ""} or set(term) <= set("-: "):
            continue
        # Bold-Markup entfernen für den Schlüsselvergleich.
        key = term.replace("**", "").strip()
        entries[key] = meaning
    return entries


@pytest.mark.parametrize("term", REQUIRED_TERMS)
def test_glossary_defines_v6_term(term):
    section = _glossary_section()
    entries = _glossary_entries(section)
    assert term in entries, (
        f"Glossar-Begriff '{term}' fehlt im README-Glossar (Issue #211). "
        f"Vorhandene Begriffe: {sorted(entries)}"
    )
    meaning = entries[term]
    assert len(meaning) >= 20, (
        f"Glossar-Eintrag für '{term}' hat keine substanzielle Definition: {meaning!r}"
    )


def test_glossary_entries_are_bold():
    """Jeder geforderte Begriff steht als **fetter** Glossar-Eintrag."""
    section = _glossary_section()
    for term in REQUIRED_TERMS:
        assert f"**{term}**" in section, (
            f"Glossar-Begriff '{term}' ist nicht als **{term}** ausgezeichnet."
        )
