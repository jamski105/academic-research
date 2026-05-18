# Spec: Chunk I — `/academic-research:pickup` Slash-Command

**Ticket:** #77  
**Branch:** `feat/v6.2-I-pickup-cmd`  
**Stand:** 2026-05-18

---

## 1. Overview

`/academic-research:pickup` erzeugt eine Bibliotheks-Pickup-Liste als `.xlsx`-Datei
mit 4 Sheets, aufgeteilt nach Verfügbarkeitsstatus. Code128-Barcodes werden für ISBNs
als Zellbild (Image-Embed) in Excel eingebettet. Excel-Generierung erfolgt
ausschließlich via `document-skills:xlsx`-Skill.

**Input:** Vault-Einträge mit `availability_status` (oder ohne → Default-Sheet
`Lizenz nötig`). In Tests: fixturierte JSON-Dateien.

**Output:** `pickup-list.xlsx` mit 4 Sheets.

---

## 2. AC-Mapping

| AC | Umsetzung |
|----|-----------|
| `/academic-research:pickup` aufrufbar | `commands/pickup.md` mit Slash-Command-Definition |
| 4 Sheets nach Verfügbarkeitsstatus | `Vor Ort verfügbar`, `Fernleihe`, `Online OA`, `Lizenz nötig` |
| Code128-Barcodes als Zellbild im Books-Sheet | `scripts/barcode.py` → PNG → `insert_image` via xlsx-Skill |
| Excel via `document-skills:xlsx` only | Skill-Aufruf in `commands/pickup.md`; barcode.py nur für PNG-Erzeugung |
| Test mit 5 Quellen, valide .xlsx | `tests/test_pickup_excel.py` + `tests/fixtures/pickup/` |
| Alle Vault-Einträge aufnehmen | Sheet-Zuordnung via `availability_status`, kein OA-Filter |

---

## 3. Architektur

### 3.1 Slash-Command (`commands/pickup.md`)

```
/academic-research:pickup [--vault-selection <path|glob>]
```

1. Liest Vault-Einträge (JSON-Frontmatter oder YAML) aus der Auswahl.
2. Ruft `scripts/barcode.py generate_isbn_barcode(isbn)` für alle Bücher auf
   → gibt temporäre PNG-Pfade zurück.
3. Baut die 4-Sheet-Struktur auf.
4. Ruft `document-skills:xlsx`-Skill auf:
   - `create_workbook` mit 4 Sheets
   - `write_rows` pro Sheet
   - `insert_image` für Barcode-PNGs im Books-Sheet
   - `save_workbook` → `pickup-list.xlsx`

### 3.2 Barcode-Generator (`scripts/barcode.py`)

- Nutzt `python-barcode`-Lib (Code128-Format).
- `generate_isbn_barcode(isbn: str, output_path: str) -> str`
  — schreibt PNG in temporäres Verzeichnis, gibt Pfad zurück.
- Fallback: wenn `python-barcode` nicht installiert, gibt `None` zurück
  (Command dokumentiert Dependency-Fehler im Output).

### 3.3 Fixture-Daten (`tests/fixtures/pickup/`)

5 JSON-Dateien mit `availability_status`-Variation:

| Datei | Typ | `availability_status` |
|-------|-----|----------------------|
| `book_vor_ort.json` | book | `vor_ort_verfuegbar` |
| `book_fernleihe.json` | book | `fernleihe` |
| `paper_online_oa.json` | article | `online_oa` |
| `paper_lizenz.json` | article | `lizenz_noetig` |
| `thesis_no_status.json` | thesis | _(keins)_ → Default `lizenz_noetig` |

### 3.4 Sheet-Zuordnung

```
availability_status         → Sheet
vor_ort_verfuegbar          → "Vor Ort verfügbar"
fernleihe                   → "Fernleihe"
online_oa                   → "Online OA"
lizenz_noetig / (kein Wert) → "Lizenz nötig"
```

### 3.5 Spalten pro Sheet

**Vor Ort verfügbar / Fernleihe** (Bücher + Artikel):
- Titel, Autor(en), ISBN/DOI, Barcode (Bild-Spalte, nur wenn book+ISBN), Signatur, Standort

**Online OA:**
- Titel, Autor(en), URL, Zugriffsdatum

**Lizenz nötig:**
- Titel, Autor(en), ISBN/DOI, Verlag, Preis-Schätzung (optional)

---

## 4. Test-Plan

### `tests/test_pickup_excel.py`

| Test | RED-Beschreibung |
|------|-----------------|
| `test_barcode_generates_png` | `generate_isbn_barcode("9783161484100", ...)` → Datei existiert, `.png`-Endung |
| `test_barcode_invalid_isbn` | leere/ungültige ISBN → `None` oder Exception, kein Crash |
| `test_sheet_assignment` | je 1 Fixture pro Status → korrekte Sheet-Zuordnung |
| `test_no_status_defaults_to_lizenz` | Fixture ohne `availability_status` → Sheet `Lizenz nötig` |
| `test_pickup_command_integration` | 5 Fixtures → Pickup-Output enthält alle 4 Sheet-Namen |

---

## 5. Out-of-Scope

- Echter Vault-Lookup (MCP-Server) — Tests nutzen Fixtures.
- `/fetch`-Integration (Chunk H) — pickup liest nur vorhandene `availability_status`-Felder.
- openpyxl / pandas — explizit verboten (User-Memory).
- Spalten-Autofit, Conditional Formatting — kein AC.

---

## 6. Risiken

| Risiko | Mitigation |
|--------|-----------|
| `document-skills:xlsx`-Skill nicht verfügbar | Graceful error in Command; tests mocken den Skill-Aufruf |
| `python-barcode` nicht installiert | Fallback in `barcode.py`; Test prüft Fallback-Verhalten |
| `insert_image`-API des xlsx-Skills unbekannt | Test überspringt Bild-Embed wenn Skill-API nicht verfügbar; pure-font als Fallback |
| ISBN-Format-Varianten (ISBN-10 vs ISBN-13) | `barcode.py` normalisiert via Standard-Konvention |
