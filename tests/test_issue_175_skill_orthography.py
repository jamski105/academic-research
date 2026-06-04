"""Regression-Guard fuer Issue #175 — ASCII-Substitution in SKILL.md restaurieren.

Die globale CLAUDE.md verlangt volle Orthografie (ue->ü, ae->ä, oe->ö, ss->ß).
Mehrere v6.5-Skills enthielten ASCII-Ersatz statt korrekter Umlaute. Dieser Test
kodiert die Akzeptanzkriterien:

1. Keine der bekannten ASCII-substituierten deutschen Woerter darf in den
   betroffenen SKILL.md-Dateien (Body + Frontmatter) mehr auftauchen.
   Kein blindes sed — eine explizite Wortliste, damit legitime Sequenzen wie
   "Quelle", "neue", "bauen", "manuell", "issued", "true" erhalten bleiben.
2. Trigger-Phrasen in der description bieten weiterhin beide Schreibweisen an
   (vorhandenes "X / Y"-Umlaut-Paar-Muster bleibt erhalten).
"""
import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).parent.parent / "skills"

AFFECTED_SKILLS = [
    "reading-list-import",
    "material-passport",
    "book-handler",
    "cluster-visualizer",
    "citation-style-import",
    "zotero-import",
    "notebook-bundle",
]

# Exakte ASCII-substituierte Woerter, die NICHT mehr vorkommen duerfen.
# Bewusst keine Regex-Heuristik: nur diese konkreten Tokens werden verboten,
# damit legitime ue/oe/ae-Sequenzen (Quelle, neue, bauen, manuell, ...) bleiben.
FORBIDDEN_ASCII_WORDS = {
    # ue -> ü
    "Abhaengigkeiten", "Ausfaelle", "Einschraenkungen", "Eintraege",
    "fortfaehrst", "fuehren", "fuehrt", "Fuer", "fuer", "koennen",
    "moechte", "moegliche", "moeglich", "Pruefe", "prueft", "Pruefung",
    "Prueft", "ueber", "ueberprueft", "uebersprungen", "uebersprungener",
    "uebertragen", "uebrigen", "Unterstuetzt", "Unterstuetzte",
    "unterstuetzt", "verfuegbar", "Verfuegbarkeit", "vervollstaendigt",
    "Buecher", "ausfuehren", "ausgefuehrt", "duerfen", "gewuenschte",
    "Groesse", "Abkuerzungsregeln", "zurueck", "zurueckgegeben",
    "ausgewaehlten", "Quelltext",  # Quelltext -> Quelltext bleibt, s. unten
    # ae -> ä
    "Fehlerfaelle", "ergaenzt", "enthaelt", "erhaelt", "Klaere",
    "bestaetigen", "Bestaetigung", "bestaetigt", "repraesentieren",
    "Vollstaendige", "vollstaendige", "vollstaendigen", "persoenliches",
    # oe -> ö
    "Bloecke", "ermoeglicht", "Loeschen", "Loest", "aufloesen",
    "zusaetzlich", "Aufloesung",
    "Uebersicht", "Ueberblick",
    "Laedt",
}
# "Quelltext" enthaelt KEIN Substitut (Quell+text). Wieder entfernen:
FORBIDDEN_ASCII_WORDS.discard("Quelltext")

# Token-weise pruefen: Worttrenner = alles ausser Buchstaben.
WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+")

# Umlaut-Paar in description: "...ä.../..." analog test_skills_manifest.
DESC_PAIR_RE = re.compile(r'"[^"]*[äöüß][^"]*\s*/\s*[a-zA-Z][^"]*"')


def _read(skill: str) -> str:
    return (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")


def _description(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return ""
    fm = m.group(1)
    # description kann mehrzeilig sein (>- Block oder gequotet)
    dm = re.search(r"^description:\s*(.*(?:\n[ \t]+.*)*)", fm, re.MULTILINE)
    return dm.group(1) if dm else ""


@pytest.mark.parametrize("skill", AFFECTED_SKILLS)
def test_no_ascii_substituted_words(skill: str) -> None:
    text = _read(skill)
    found = sorted({w for w in WORD_RE.findall(text) if w in FORBIDDEN_ASCII_WORDS})
    assert not found, (
        f"skills/{skill}/SKILL.md enthaelt ASCII-substituierte Woerter "
        f"(Umlaute restaurieren): {found}"
    )


@pytest.mark.parametrize("skill", AFFECTED_SKILLS)
def test_description_offers_umlaut_variant(skill: str) -> None:
    """Trigger-Phrasen mit Umlaut bieten weiterhin beide Schreibweisen an."""
    desc = _description(_read(skill))
    pairs = DESC_PAIR_RE.findall(desc)
    assert pairs, (
        f"skills/{skill}/SKILL.md: description bietet kein 'mit/ohne Umlaut'-Paar "
        f'("X / Y") mehr an'
    )
