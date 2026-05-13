---
name: book-handler
description: 'Verwende diesen Skill wenn der User ein Buch / eine Monografie / einen Sammelband verarbeiten möchte. Trigger: "Buch", "Monografie", "Sammelband", "Kapitel von ...", ISBN-Pattern (\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d), Springer-DOI (10.1007/978-). Löst ISBN/Titel/DOI via DNB + OpenLibrary + DOAB auf und legt CSL-JSON im Vault an. Unterstützt "Monografie / Sammelband" als gleichwertige Buchtypen.'
compatibility: Claude Code mit MCP vault-Tool
license: MIT
---

# Buch-Handler

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Bloecke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfaehrst.

## Uebersicht

Indexiert Buecher und Kapitel erstklassig -- analog zu Artikeln. Liefert
CSL-JSON mit `type: book | chapter`, Herausgeber-Array und Seitenangaben.
Prueft DOAB/OAPEN auf Open-Access-Verfuegbarkeit.

## Abgrenzung

Loest Metadaten auf und legt Vault-Eintraege an. Schneidet keine Kapitel aus
PDFs (F2.2), berechnet kein Seitenmapping (F2.3), fuehrt keine OCR durch (F2.4).
Zitationsformatierung: `citation-extraction`.

## Trigger-Erkennung

Aktiviert sich bei:
- Direkten Begriffen: "Buch", "Monografie", "Sammelband", "Kapitel von ..."
- ISBN-Pattern: `\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d`
- Springer-Buch-DOI: `10.1007/978-`

## Workflow

### 1. Metadaten aufloesen

```bash
python scripts/book_resolve.py --isbn {isbn}
python scripts/book_resolve.py --title "{titel}"
python scripts/book_resolve.py --doi {doi}
```

Output: CSL-JSON (type=book|chapter). API-Quellen: `skills/book-handler/references/sources.md`.

### 2. Vault-Eintrag anlegen

```
vault.add_paper(
  paper_id        = "{citekey}",
  csl_json        = "{csl_json_string}",
  isbn            = "{isbn}",
  editor          = "{editor_json}",
  chapter         = "{kapitel_nr}",
  page_first      = {seite_von},
  page_last       = {seite_bis},
  container_title = "{sammelband_titel}"
)
```

### 2.5. page_offset berechnen

Falls `pdf_path` gesetzt:

```bash
python scripts/page_offset.py {pdf_path}
```

Ergebnis via `vault.set_page_offset({citekey}, {offset})` speichern.

### 3. OA-Check

Falls `book_resolve.py` ein `URL`-Feld liefert (DOAB/OAPEN):
- Setze `pdf_path` im Vault-Eintrag
- Informiere User: "OA-PDF verfuegbar unter {url}"

### 4. Nachfolge-Hinweise

Nach erfolgreichem Vault-Eintrag dem User anbieten:
- Kapitel extrahieren? -> F2.2: `chunk_pdf.py`
- Scan-PDF (kein Text)? -> Schritt 5 ausfuehren

### 5. OCR-Pruefung (bei pdf_path vorhanden)

```python
from pdf import detect_needs_ocr
if detect_needs_ocr(pdf_path):
    # User fragen:
    # "Scan-PDF erkannt: wenig Text auf Stichproben-Seiten.
    #  OCR ausfuehren? (~30 s/Seite, lokal via ocrmypdf) [j/n]"
    # Bei Zustimmung:
    from ocr import run_ocrmypdf
    run_ocrmypdf(pdf_path, pdf_path_ocr)
    vault.set_ocr_done(paper_id)
    vault.update_pdf_path(paper_id, pdf_path_ocr)
```

## Ausgabe

```
Buch indexiert: {titel} ({year})
- paper_id: {citekey}
- type: {type}
- ISBN: {isbn}
- Vault: vault.get_paper("{citekey}")
[- OA-PDF: {url}]
```

## Beispiel

**Gut:** User gibt ISBN 978-3-446-46103-1 an.
book-handler fuehrt `book_resolve.py --isbn 9783446461031` aus,
erhaelt CSL-JSON (type=book, title, author, publisher, year),
legt Vault-Eintrag an, bestaetigt dem User.

**Schlecht:** Metadaten ohne API-Aufruf erfinden -- VERBOTEN.
