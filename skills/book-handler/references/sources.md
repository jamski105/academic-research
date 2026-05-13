# book-handler -- API-Quellen und Endpunkte

## ISBN-Regex

```
\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d
```

Beispiel: `978-3-446-46103-1`

## DNB SRU (Deutsche Nationalbibliothek)

- **Basis-URL:** `https://services.dnb.de/sru/dnb`
- **Protokoll:** SRU 1.1 (Search/Retrieve via URL)
- **Format:** `recordSchema=MARC21-xml`
- **ISBN-Abfrage:** `?version=1.1&operation=searchRetrieve&query=isbn+%3D+{isbn}&recordSchema=MARC21-xml&maximumRecords=1`
- **Titel-Abfrage:** `?version=1.1&operation=searchRetrieve&query=title+%3D+{title}&recordSchema=MARC21-xml&maximumRecords=5`
- **Freies Kontingent:** Ja (oeffentliche DNB-API, keine Registrierung noetig)

## OpenLibrary (Internet Archive)

- **Basis-URL:** `https://openlibrary.org/api/books`
- **Protokoll:** JSON REST
- **ISBN-Abfrage:** `?bibkeys=ISBN:{isbn}&jscmd=data&format=json`
- **Freies Kontingent:** Ja (oeffentliche API)

## GoogleBooks

- **Basis-URL:** `https://www.googleapis.com/books/v1/volumes`
- **Protokoll:** JSON REST
- **ISBN-Abfrage:** `?q=isbn:{isbn}&maxResults=1`
- **Freies Kontingent:** 1000 Requests/Tag ohne API-Key

## DOAB (Directory of Open Access Books)

- **Basis-URL:** `https://directory.doabooks.org/rest/search`
- **Protokoll:** REST (DSpace-API)
- **ISBN-Abfrage:** `?query=isbn:{isbn}&expand=metadata,bitstreams`
- **DOI-Abfrage:** `?query=doi:{doi}&expand=metadata,bitstreams`
- **Gibt zurueck:** OA-Flag, PDF-Download-Link (falls OA)

## Fallback-Strategie

```
ISBN/Titel/DOI
  -> 1. DNB SRU (primaer, beste DE-Abdeckung)
  -> 2. OpenLibrary (falls DNB leer/Fehler)
  -> 3. GoogleBooks (falls OL leer/Fehler)
  -> DOAB immer als ergaenzender OA-Check
```
