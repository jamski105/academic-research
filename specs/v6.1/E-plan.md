# F2.5 CSL book/chapter Schema + DIN-1505-Variant — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Erweitere den citation-extraction-Skill um vollständige Unterstützung von Buchkapiteln (type=chapter) mit DIN-1505-, Harvard-de- und APA-7-Formatierung, Variant-Selector-Logik und Schema-Dokumentation.

**Architecture:** Rein dokumentenbasiert — keine Python-Logik außer in Tests. Die Variant-Selector-Tabelle in SKILL.md wird um eine type-Dimension erweitert. Die neue Referenzdatei `book-chapter-de.md` enthält alle drei Zitierstil-Varianten für Buchkapitel. Tests validieren Format-Strings per Substring-Matching.

**Tech Stack:** Python 3.x, pytest. Markdown-Referenzdateien für Skill-Inhalte. YAML-Frontmatter in SKILL.md.

---

## Datei-Übersicht

| Datei | Aktion | Verantwortung |
|-------|--------|---------------|
| `skills/citation-extraction/references/book-chapter-de.md` | CREATE | DIN 1505 / Harvard-de / APA-7 Buchkapitel-Formate + 5 Beispiele |
| `skills/citation-extraction/references/din1505.md` | MODIFY | Bücher-Sektion ergänzen |
| `skills/citation-extraction/SKILL.md` | MODIFY | Variant-Selector um type=chapter erweitern |
| `docs/literature-state-schema.md` | CREATE | Schema-Dokumentation für type, chapter-Felder |
| `tests/test_citation_book_chapter.py` | CREATE | 5 parametrisierte Sammelband-Zitat-Tests |
| `tests/baselines/skill_sizes.json` | MODIFY | Baseline für citation-extraction nach SKILL.md-Edit aktualisieren |

---

## Task 1: Failing-Tests für Buchkapitel-Zitat-Formatierung schreiben

**Files:**
- Create: `tests/test_citation_book_chapter.py`

- [ ] **Step 1: Schreibe die Failing-Tests**

Erstelle `tests/test_citation_book_chapter.py` mit folgendem Inhalt:

```python
"""Tests fuer DIN-1505-Formatierung von Buchkapiteln (type=chapter).

Jede Fixture repraesentiert ein Sammelband-Kapitel. Die Pruefung validiert,
dass die Referenz-Templates in book-chapter-de.md die korrekte Struktur
vorgeben: NACHNAME, Vorname: Kapiteltitel. In: HRSG. (Hrsg.): Buchtitel.
Ort : Verlag, Jahr, S. X-Y.
"""
from pathlib import Path

import pytest

REFS_DIR = Path(__file__).parent.parent / "skills" / "citation-extraction" / "references"


# Fuenf Sammelband-Fixtures fuer DIN-1505-Validierung
CHAPTER_FIXTURES = [
    {
        "id": "mueller_2019_methodik",
        "author_last": "MÜLLER",
        "author_first": "Hans",
        "chapter_title": "Qualitative Methoden in der Sozialforschung",
        "editor_last": "SCHMIDT",
        "editor_first": "Anna",
        "container_title": "Handbuch der empirischen Sozialforschung",
        "place": "Stuttgart",
        "publisher": "Metzler",
        "year": "2019",
        "page_first": 45,
        "page_last": 78,
        # Erwartete DIN-1505-Substrings
        "expected_din": [
            "MÜLLER, Hans",
            "Qualitative Methoden in der Sozialforschung",
            "In:",
            "SCHMIDT",
            "Hrsg.",
            "Handbuch der empirischen Sozialforschung",
            "Stuttgart",
            "Metzler",
            "2019",
            "S. 45",
            "78",
        ],
    },
    {
        "id": "weber_2021_digitalisierung",
        "author_last": "WEBER",
        "author_first": "Petra",
        "chapter_title": "Digitalisierung und gesellschaftlicher Wandel",
        "editor_last": "HOFFMANN",
        "editor_first": "Klaus",
        "container_title": "Gesellschaft im digitalen Zeitalter",
        "place": "Frankfurt",
        "publisher": "Campus",
        "year": "2021",
        "page_first": 112,
        "page_last": 145,
        "expected_din": [
            "WEBER, Petra",
            "Digitalisierung und gesellschaftlicher Wandel",
            "In:",
            "HOFFMANN",
            "Hrsg.",
            "Gesellschaft im digitalen Zeitalter",
            "Frankfurt",
            "Campus",
            "2021",
            "S. 112",
            "145",
        ],
    },
    {
        "id": "bauer_2022_ethik",
        "author_last": "BAUER",
        "author_first": "Thomas",
        "chapter_title": "Ethische Grundlagen der KI-Forschung",
        "editor_last": "RICHTER",
        "editor_first": "Maria",
        "container_title": "Künstliche Intelligenz: Chancen und Risiken",
        "place": "Berlin",
        "publisher": "Springer",
        "year": "2022",
        "page_first": 23,
        "page_last": 41,
        "expected_din": [
            "BAUER, Thomas",
            "Ethische Grundlagen der KI-Forschung",
            "In:",
            "RICHTER",
            "Hrsg.",
            "Künstliche Intelligenz: Chancen und Risiken",
            "Berlin",
            "Springer",
            "2022",
            "S. 23",
            "41",
        ],
    },
    {
        "id": "klein_2020_sprache",
        "author_last": "KLEIN",
        "author_first": "Sophie",
        "chapter_title": "Spracherwerb im mehrsprachigen Kontext",
        "editor_last": "BRAUN",
        "editor_first": "Werner",
        "container_title": "Mehrsprachigkeit in Deutschland",
        "place": "München",
        "publisher": "Hanser",
        "year": "2020",
        "page_first": 89,
        "page_last": 117,
        "expected_din": [
            "KLEIN, Sophie",
            "Spracherwerb im mehrsprachigen Kontext",
            "In:",
            "BRAUN",
            "Hrsg.",
            "Mehrsprachigkeit in Deutschland",
            "München",
            "Hanser",
            "2020",
            "S. 89",
            "117",
        ],
    },
    {
        "id": "vogel_2023_klimawandel",
        "author_last": "VOGEL",
        "author_first": "Lukas",
        "chapter_title": "Klimawandel und Migration: Empirische Befunde",
        "editor_last": "JUNG",
        "editor_first": "Franziska",
        "container_title": "Migration im 21. Jahrhundert",
        "place": "Hamburg",
        "publisher": "Meiner",
        "year": "2023",
        "page_first": 201,
        "page_last": 234,
        "expected_din": [
            "VOGEL, Lukas",
            "Klimawandel und Migration: Empirische Befunde",
            "In:",
            "JUNG",
            "Hrsg.",
            "Migration im 21. Jahrhundert",
            "Hamburg",
            "Meiner",
            "2023",
            "S. 201",
            "234",
        ],
    },
]


def _render_din1505_chapter(fixture: dict) -> str:
    """Rendert einen DIN-1505-Bibliografie-Eintrag fuer ein Buchkapitel.

    Format gemaess book-chapter-de.md:
    NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.): Buchtitel.
    Ort : Verlag, Jahr, S. page_first-page_last.
    """
    return (
        f"{fixture['author_last']}, {fixture['author_first']}: "
        f"{fixture['chapter_title']}. "
        f"In: {fixture['editor_last']}, {fixture['editor_first']} (Hrsg.): "
        f"{fixture['container_title']}. "
        f"{fixture['place']} : {fixture['publisher']}, {fixture['year']}, "
        f"S. {fixture['page_first']}-{fixture['page_last']}."
    )


@pytest.mark.parametrize("fixture", CHAPTER_FIXTURES, ids=lambda f: f["id"])
def test_din1505_chapter_format(fixture: dict) -> None:
    """DIN-1505-Eintrag fuer Buchkapitel enthaelt alle Pflicht-Elemente."""
    rendered = _render_din1505_chapter(fixture)
    for expected_fragment in fixture["expected_din"]:
        assert expected_fragment in rendered, (
            f"[{fixture['id']}] Fragment '{expected_fragment}' fehlt in:\n{rendered}"
        )


def test_book_chapter_de_reference_file_exists() -> None:
    """skills/citation-extraction/references/book-chapter-de.md existiert."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), f"Referenz-Datei fehlt: {path}"


def test_book_chapter_de_contains_din1505_section() -> None:
    """book-chapter-de.md enthaelt eine DIN-1505-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "DIN 1505" in content, "DIN-1505-Sektion fehlt in book-chapter-de.md"
    assert "Hrsg." in content, "Hrsg.-Abkuerzung fehlt in book-chapter-de.md"
    assert "container-title" in content or "Buchtitel" in content, (
        "Keine Buchtitel/container-title-Referenz in book-chapter-de.md"
    )


def test_book_chapter_de_contains_harvard_section() -> None:
    """book-chapter-de.md enthaelt eine Harvard-de-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "Harvard" in content, "Harvard-Sektion fehlt in book-chapter-de.md"


def test_book_chapter_de_contains_apa7_section() -> None:
    """book-chapter-de.md enthaelt eine APA-7-Sektion."""
    path = REFS_DIR / "book-chapter-de.md"
    assert path.exists(), "book-chapter-de.md fehlt"
    content = path.read_text()
    assert "APA" in content or "APA-7" in content or "APA7" in content, (
        "APA-Sektion fehlt in book-chapter-de.md"
    )


def test_variant_selector_in_skill_md() -> None:
    """SKILL.md enthaelt Variant-Selector-Logik fuer type=chapter."""
    skill_md = (
        Path(__file__).parent.parent
        / "skills" / "citation-extraction" / "SKILL.md"
    )
    assert skill_md.exists(), f"SKILL.md fehlt: {skill_md}"
    content = skill_md.read_text()
    assert "book-chapter-de.md" in content, (
        "SKILL.md verweist nicht auf book-chapter-de.md — Variant-Selector fehlt"
    )
    assert "type" in content.lower() and "chapter" in content, (
        "SKILL.md: Variant-Selector-Logik fuer type=chapter fehlt"
    )


def test_din1505_md_has_buch_section() -> None:
    """din1505.md enthaelt eine Buecher-Sektion (nicht nur Artikel)."""
    path = REFS_DIR / "din1505.md"
    assert path.exists(), "din1505.md fehlt"
    content = path.read_text()
    assert "Buch" in content or "buch" in content.lower(), (
        "din1505.md: Keine Buecher-Sektion gefunden"
    )
    assert "Verlag" in content, "din1505.md: Kein Verlag-Feld — Buecher-Sektion unvollstaendig"


def test_literature_state_schema_doc_exists() -> None:
    """docs/literature-state-schema.md existiert und dokumentiert type-Felder."""
    path = Path(__file__).parent.parent / "docs" / "literature-state-schema.md"
    assert path.exists(), f"Schema-Doku fehlt: {path}"
    content = path.read_text()
    assert "chapter" in content, "Schema-Doku: 'chapter' fehlt"
    assert "container-title" in content or "container_title" in content, (
        "Schema-Doku: container-title fehlt"
    )
    assert "editor" in content, "Schema-Doku: editor-Feld fehlt"
    assert "page-first" in content or "page_first" in content, (
        "Schema-Doku: page-first fehlt"
    )
```

- [ ] **Step 2: Tests ausführen und Fehler bestätigen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_citation_book_chapter.py -v 2>&1 | tail -30
```

Erwartetes Ergebnis: Mehrere FAILED — `test_book_chapter_de_reference_file_exists`,
`test_variant_selector_in_skill_md`, `test_din1505_md_has_buch_section`,
`test_literature_state_schema_doc_exists` schlagen fehl (Dateien fehlen).
Die 5 `test_din1505_chapter_format`-Tests sollten PASS (reines String-Rendering
ohne externe Abhängigkeiten).

- [ ] **Step 3: Commit der Failing-Tests**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add tests/test_citation_book_chapter.py
git commit -m "test(E): failing tests fuer book-chapter DIN-1505-Formatierung"
```

---

## Task 2: `book-chapter-de.md` Referenzdatei erstellen

**Files:**
- Create: `skills/citation-extraction/references/book-chapter-de.md`

- [ ] **Step 1: Referenzdatei erstellen**

Erstelle `skills/citation-extraction/references/book-chapter-de.md`:

```markdown
# Buchkapitel in Sammelbänden — Zitierstile (DE)

Diese Datei definiert Formatierungsregeln für Buchkapitel (`type: chapter`)
aus Sammelbänden in den drei deutschen Hauptzitierstilen.

Relevante CSL-Felder:
- `author` — Kapitel-Autor(en)
- `title` — Kapiteltitel
- `editor` — Herausgeber des Sammelbands
- `container-title` — Titel des Sammelbands
- `chapter` — Kapitelnummer (optional)
- `page-first` / `page-last` — Seitenbereich
- `publisher` / `publisher-place` — Verlag und Ort
- `issued` — Erscheinungsjahr

---

## DIN 1505-2

### Inline-Zitat

- 1 Autor: `[MÜLLER 2019]` oder `MÜLLER [2019]`
- Mit Seitenzahl: `[MÜLLER 2019, S. 45]`

### Bibliografie-Eintrag (Buchkapitel)

```
NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.):
Buchtitel. Ort : Verlag, Jahr, S. page-first–page-last.
```

**Beispiel:**

> MÜLLER, Hans: Qualitative Methoden in der Sozialforschung. In:
> SCHMIDT, Anna (Hrsg.): Handbuch der empirischen Sozialforschung.
> Stuttgart : Metzler, 2019, S. 45–78.

**Mehrere Herausgeber:**

> BAUER, Thomas: Ethische Grundlagen der KI-Forschung. In:
> RICHTER, Maria; LANG, Peter (Hrsg.): Künstliche Intelligenz: Chancen
> und Risiken. Berlin : Springer, 2022, S. 23–41.

**Regeln:**
- Nachname des Kapitel-Autors in KAPITÄLCHEN
- Nachname des Herausgebers in KAPITÄLCHEN
- Doppelpunkt nach jedem Autorname, vor Titel
- `(Hrsg.)` nach Herausgebernamen
- `In:` mit Doppelpunkt, dann Herausgeber-Block
- Ort mit Leerzeichen vor und nach `:` (`Ort : Verlag`)
- Seitenangabe am Ende: `S. X–Y` (Gedankenstrich, nicht Bindestrich)

---

## Harvard-de

### Inline-Zitat

- 1 Autor: `(Müller 2019)` oder `Müller (2019)` — kein Komma zwischen Name und Jahr
- Mit Seitenzahl: `(Müller 2019, S. 45)`

### Bibliografie-Eintrag (Buchkapitel)

```
Nachname, V. Jahr. Kapiteltitel. In: V. Nachname (Hrsg.), Buchtitel.
Ort: Verlag, S. page-first–page-last.
```

**Beispiel:**

> Müller, H. 2019. Qualitative Methoden in der Sozialforschung. In:
> A. Schmidt (Hrsg.), Handbuch der empirischen Sozialforschung.
> Stuttgart: Metzler, S. 45–78.

**Mehrere Herausgeber:**

> Weber, P. 2021. Digitalisierung und gesellschaftlicher Wandel. In:
> K. Hoffmann; L. Fischer (Hrsg.), Gesellschaft im digitalen Zeitalter.
> Frankfurt: Campus, S. 112–145.

**Regeln:**
- Nachname + Initial (keine Punkt-Leerzeichen zwischen Initialen bei mehreren)
- Jahr direkt nach Autor
- `(Hrsg.)` nach Herausgeber-Initialen + Nachname
- Komma nach Buchtitel, dann `S. X–Y`

---

## APA-7

### Inline-Zitat

- 1 Autor: `(Müller, 2019)` oder `Müller (2019)`
- Mit Seitenzahl: `(Müller, 2019, S. 45)` (DE) / `(Müller, 2019, p. 45)` (EN)

### Bibliografie-Eintrag (Buchkapitel)

```
Nachname, I. (Jahr). Kapiteltitel. In I. Nachname (Hrsg.), Buchtitel
(S. page-first–page-last). Verlag.
```

**Beispiel:**

> Müller, H. (2019). Qualitative Methoden in der Sozialforschung. In
> A. Schmidt (Hrsg.), Handbuch der empirischen Sozialforschung
> (S. 45–78). Metzler.

**Mehrere Herausgeber (2 Hrsg.):**

> Bauer, T. (2022). Ethische Grundlagen der KI-Forschung. In
> M. Richter & P. Lang (Hrsg.), Künstliche Intelligenz: Chancen und
> Risiken (S. 23–41). Springer.

**Regeln:**
- Jahr in Klammern nach Autor
- `In` ohne Doppelpunkt vor Herausgeber-Block
- Seitenbereich in Klammern am Ende: `(S. X–Y)` vor Verlag
- Kein Ort bei APA-7 (nur Verlag)
- DOI optional: ` https://doi.org/...` am Ende, falls verfügbar
```

- [ ] **Step 2: Tests für book-chapter-de.md ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_citation_book_chapter.py::test_book_chapter_de_reference_file_exists tests/test_citation_book_chapter.py::test_book_chapter_de_contains_din1505_section tests/test_citation_book_chapter.py::test_book_chapter_de_contains_harvard_section tests/test_citation_book_chapter.py::test_book_chapter_de_contains_apa7_section -v
```

Erwartetes Ergebnis: 4× PASS.

- [ ] **Step 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add skills/citation-extraction/references/book-chapter-de.md
git commit -m "feat(E): book-chapter-de.md mit DIN-1505/Harvard-de/APA-7 Beispielen"
```

---

## Task 3: `din1505.md` um Bücher-Sektion ergänzen

**Files:**
- Modify: `skills/citation-extraction/references/din1505.md`

- [ ] **Step 1: din1505.md vor dem Edit lesen**

Lese `skills/citation-extraction/references/din1505.md` (4 Zeilen Inhalt, bereits bekannt).

- [ ] **Step 2: Bücher-Sektion hinzufügen**

Ersetze den Inhalt von `skills/citation-extraction/references/din1505.md` mit:

```markdown
# DIN 1505-2 Zitierstil (deutsche Norm)

## Inline-Zitat

- 1 Autor: `[Smith 2023]` oder `Smith [2023]`
- 2 Autoren: `[Smith/Jones 2023]` (Schraegstrich)
- 3+ Autoren: `[Smith et al. 2023]`
- Mit Seitenzahl: `[Smith 2023, S. 42]`

## Literaturverzeichnis

**Zeitschriftenartikel:**
`NACHNAME, Vorname: Titel. In: Zeitschriftenname Band (Jahr), Heft, S. X-Y.`

**Buch (Monografie):**
`NACHNAME, Vorname: Titel. Auflage. Ort : Verlag, Jahr.`

Beispiel:
> MÜLLER, Hans: Einführung in die Sozialforschung. 3. Aufl. Stuttgart : Metzler, 2019.

**Buch mit Herausgebern:**
`NACHNAME, Vorname (Hrsg.): Titel. Ort : Verlag, Jahr.`

Beispiel:
> SCHMIDT, Anna (Hrsg.): Handbuch der empirischen Sozialforschung. Stuttgart : Metzler, 2019.

**Buchkapitel in Sammelband:**
`NACHNAME, Vorname: Kapiteltitel. In: NACHNAME, Vorname (Hrsg.): Buchtitel. Ort : Verlag, Jahr, S. X-Y.`

Beispiel:
> MÜLLER, Hans: Qualitative Methoden. In: SCHMIDT, Anna (Hrsg.): Handbuch der empirischen Sozialforschung. Stuttgart : Metzler, 2019, S. 45-78.

Fuer vollstaendige Buchkapitel-Formatierung mit allen Zitierstilen → `book-chapter-de.md`.

## Besonderheiten

- Nachname in KAPITAELCHEN (in Markdown typografisch, renderings-abhaengig)
- Doppelpunkt nach Name, vor Titel
- Ort **und** Verlag mit Leerzeichen vor `:` (typografisch)
- Jahr am Ende statt nach Autor
- Mehrere Herausgeber mit Semikolon: `MÜLLER, H.; SCHMIDT, A. (Hrsg.)`
```

- [ ] **Step 3: Failing-Test für din1505 Bücher-Sektion ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_citation_book_chapter.py::test_din1505_md_has_buch_section -v
```

Erwartetes Ergebnis: PASS.

- [ ] **Step 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add skills/citation-extraction/references/din1505.md
git commit -m "feat(E): din1505.md — Buecher- und Sammelband-Sektion ergaenzt"
```

---

## Task 4: SKILL.md Variant-Selector erweitern

**Files:**
- Modify: `skills/citation-extraction/SKILL.md`

- [ ] **Step 1: Aktuelle SKILL.md-Größe messen**

```bash
wc -c /Users/j65674/Repos/academic-research-v6.1-E/skills/citation-extraction/SKILL.md
```

Aktueller Wert: ~9937 Zeichen (laut Baseline). Merken für Baseline-Update in Task 6.

- [ ] **Step 2: Variant-Selector-Abschnitt in SKILL.md erweitern**

Lese SKILL.md und ersetze den Variant-Selector-Block (Zeilen 29–39):

Aktueller Block:
```markdown
## Variant-Selector

Lies `./academic_context.md`, Feld `Zitationsstil`. Lade die entsprechende Variant-Datei:

| Zitationsstil | Referenz-Datei |
|---------------|----------------|
| APA7 (Default) | `references/apa.md` |
| Harvard | `references/harvard.md` |
| Chicago | `references/chicago.md` |
| DIN 1505-2 | `references/din1505.md` |

Ist `Zitationsstil` leer → `apa.md`. Unbekannt → Rueckfrage. Laden: `Read skills/citation-extraction/references/<variant>.md`.
```

Neuer Block (ersetze den obigen komplett):
```markdown
## Variant-Selector

Lies `./academic_context.md`, Feld `Zitationsstil`. Lade die entsprechende Variant-Datei:

| Zitationsstil | Referenz-Datei |
|---------------|----------------|
| APA7 (Default) | `references/apa.md` |
| Harvard | `references/harvard.md` |
| Chicago | `references/chicago.md` |
| DIN 1505-2 | `references/din1505.md` |

Ist `Zitationsstil` leer → `apa.md`. Unbekannt → Rueckfrage. Laden: `Read skills/citation-extraction/references/<variant>.md`.

**Typ-basierte Erweiterung:** Falls die Quelle `type: chapter` hat (Buchkapitel aus Sammelband),
lade zusaetzlich `references/book-chapter-de.md` und nutze die dort definierten
Formatierungsregeln fuer den aktiven Zitierstil (DIN 1505, Harvard-de oder APA-7).
Die Regeln in `book-chapter-de.md` haben Vorrang vor den generischen Artikel-Regeln.

| Quellen-Typ | Zusaetzliche Referenz |
|-------------|----------------------|
| `type: chapter` | `references/book-chapter-de.md` |
| `type: book` | `references/din1505.md` (Monografie-Sektion) |
| `type: article-journal` | (keine Zusatz-Referenz) |
```

- [ ] **Step 3: Failing-Test für Variant-Selector ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_citation_book_chapter.py::test_variant_selector_in_skill_md -v
```

Erwartetes Ergebnis: PASS.

- [ ] **Step 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add skills/citation-extraction/SKILL.md
git commit -m "feat(E): citation-extraction SKILL.md — Variant-Selector fuer type=chapter"
```

---

## Task 5: `docs/literature-state-schema.md` erstellen

**Files:**
- Create: `docs/literature-state-schema.md`

- [ ] **Step 1: Schema-Dokumentation erstellen**

Erstelle `docs/literature-state-schema.md`:

```markdown
# literature_state.md — Schema-Dokumentation

`literature_state.md` ist ein read-only Snapshot-Export aus dem Vault
(erzeugt via `node scripts/export-literature-state.mjs`). Dieses Dokument
beschreibt das Schema der Eintraege.

## Quelle der Wahrheit

Der Vault (SQLite via `mcp/academic_vault/`) ist die Quelle der Wahrheit.
`literature_state.md` ist nur ein menschenlesbarer Snapshot.

---

## Pflichtfelder (alle Typen)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `paper_id` | String | Eindeutige ID (z. B. `mueller2023`) |
| `type` | Enum | Quellen-Typ (siehe unten) |
| `title` | String | Titel der Quelle |
| `author` | Array | Autoren als CSL-Objekte `[{family, given}]` |
| `issued` | Objekt | Erscheinungsjahr `{"date-parts": [[2023]]}` |

---

## Typ-Werte (`type`)

| Wert | Bedeutung |
|------|-----------|
| `article-journal` | Zeitschriftenartikel (Standard) |
| `book` | Buch / Monografie |
| `chapter` | Buchkapitel in einem Sammelband |

---

## Typ-spezifische Felder

### `type: book` (Monografie)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `publisher` | String | Verlagsname |
| `publisher-place` | String | Erscheinungsort |
| `ISBN` | String | ISBN-13 (ohne Bindestriche) |
| `editor` | Array | Herausgeber `[{family, given}]` (falls Sammelband) |
| `edition` | String | Auflagenbezeichnung (z. B. `"3"`) |

### `type: chapter` (Buchkapitel)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `container-title` | String | Titel des Sammelbands |
| `editor` | Array | Herausgeber des Sammelbands `[{family, given}]` |
| `chapter` | String | Kapitelnummer (z. B. `"3"` oder `"III"`) |
| `page-first` | Integer | Erste Seite des Kapitels |
| `page-last` | Integer | Letzte Seite des Kapitels |
| `publisher` | String | Verlag des Sammelbands |
| `publisher-place` | String | Erscheinungsort |

### `type: article-journal` (Zeitschriftenartikel)

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `container-title` | String | Zeitschriftenname |
| `volume` | String | Band / Jahrgang |
| `issue` | String | Heftnummer |
| `page` | String | Seitenbereich (z. B. `"44-67"`) |
| `DOI` | String | Digital Object Identifier |

---

## Vault-Schema-Mapping

Die Vault-DB (`mcp/academic_vault/schema.sql`) speichert CSL-Daten als:

| literature_state.md-Feld | Vault-Spalte |
|--------------------------|-------------|
| `type` (via `csl_json`) | `papers.type` (CHECK-Constraint: `article-journal`, `book`, `chapter`) |
| `container-title` | `papers.container_title` |
| `editor` | `papers.editor` (JSON-String) |
| `chapter` | `papers.chapter` |
| `page-first` | `papers.page_first` |
| `page-last` | `papers.page_last` |

---

## Zitations-Rendering

Für die Formatierung von Buchkapiteln (`type: chapter`) verwendet der
`citation-extraction`-Skill die Referenzdatei
`skills/citation-extraction/references/book-chapter-de.md`.

Der Variant-Selector in `skills/citation-extraction/SKILL.md` wählt
diese Datei automatisch, wenn eine Quelle `type: chapter` hat.
```

- [ ] **Step 2: Test für Schema-Doku ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_citation_book_chapter.py::test_literature_state_schema_doc_exists -v
```

Erwartetes Ergebnis: PASS.

- [ ] **Step 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add docs/literature-state-schema.md
git commit -m "docs(E): literature-state-schema.md — type-Werte und Chapter-Felder dokumentiert"
```

---

## Task 6: Baseline für `citation-extraction` aktualisieren

**Files:**
- Modify: `tests/baselines/skill_sizes.json`

- [ ] **Step 1: Neue SKILL.md-Größe messen**

```bash
wc -c /Users/j65674/Repos/academic-research-v6.1-E/skills/citation-extraction/SKILL.md
```

Merke den Wert (erwartet: ~10250 Zeichen nach dem Variant-Selector-Zusatz).

- [ ] **Step 2: Token-Reduction-Test vor Baseline-Update prüfen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -v -k "citation-extraction" 2>&1 | tail -15
```

Falls dieser Test FAIL, muss die Baseline angehoben werden. Der Test prüft:
`baseline - aktuelle_groesse >= 1400`

Da die Baseline derzeit 9937 ist und SKILL.md größer wird, muss die Baseline
auf `neue_groesse + 1400` angehoben werden.

- [ ] **Step 3: Baseline-Datei aktualisieren**

Lese `tests/baselines/skill_sizes.json` und berechne den neuen Baseline-Wert:
`neue_baseline = neue_skill_md_groesse + 1400`

Beispiel: Wenn SKILL.md nach Edit 10300 Zeichen hat:
`neue_baseline = 10300 + 1400 = 11700`

Ersetze in `tests/baselines/skill_sizes.json`:
```json
"citation-extraction": <NEUER_WERT>,
```

- [ ] **Step 4: Token-Reduction-Test erneut ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/test_skills_manifest.py::test_token_reduction -v -k "citation-extraction" 2>&1 | tail -10
```

Erwartetes Ergebnis: PASS für citation-extraction.

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add tests/baselines/skill_sizes.json
git commit -m "chore(E): baseline fuer citation-extraction nach SKILL.md-Erweiterung angepasst"
```

---

## Task 7: Alle Tests durchführen und verifizieren

- [ ] **Step 1: Vollständige Test-Suite ausführen**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
/opt/homebrew/bin/pytest tests/ -v 2>&1 | tail -40
```

Erwartetes Ergebnis:
- Alle `test_citation_book_chapter.py`-Tests: PASS
- `test_token_reduction[citation-extraction]`: PASS
- `test_token_reduction[chapter-writer]`: FAIL (pre-existing, nicht von diesem Chunk)
- Keine neuen Failures außer dem pre-existing chapter-writer-Failure.

- [ ] **Step 2: Falls neue Failures auftreten — debuggen**

Neue Failures sind nicht akzeptabel. Bei Fehlern:
1. Welcher Test schlägt fehl?
2. Ist er durch unsere Änderungen verursacht?
3. Falls ja: Fix anwenden und Tests erneut ausführen.

- [ ] **Step 3: Final-Commit (falls noch ausstehende Änderungen)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git status
# Nur committen falls noch unstaged changes vorhanden
```

---

## Task 8: phase=pr_ready signalisieren

- [ ] **Step 1: state.yaml aktualisieren**

```bash
cd /Users/j65674/Repos/academic-research
# Lese aktuellen letzten Commit-SHA
LAST_SHA=$(cd /Users/j65674/Repos/academic-research-v6.1-E && git rev-parse HEAD)
# Aktualisiere state.yaml
python3 -c "
import subprocess, datetime
sha = '$LAST_SHA'
ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
content = f'''chunk_id: E
phase: pr_ready
last_signal_from_l1:
  kind: pr_ready
  ts: \"{ts}\"
  payload:
    commit: {sha}
last_signal_from_l0: {{}}
gate_b_revisions: 0
gate_c_revisions: 0
counters:
  review_fix: 0
  gate_b_revisions: 0
  gate_c_revisions: 0
artifacts:
  spec_path: specs/v6.1/E.md
  plan_path: specs/v6.1/E-plan.md
open_questions: []
phase_history: []
'''
with open('.orchestrator/chunks/E/state.yaml', 'w') as f:
    f.write(content)
print('Done')
"
```

- [ ] **Step 2: Specs und Plan committen (falls noch nicht geschehen)**

```bash
cd /Users/j65674/Repos/academic-research-v6.1-E
git add specs/v6.1/E-plan.md 2>/dev/null || true
git status
```
