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
