# OECD iLibrary — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://www.oecd-ilibrary.org/search?q=QUERY`
- **Erweiterte Suche:** `https://www.oecd-ilibrary.org/search?q=QUERY&content%5B%5D=book&content%5B%5D=workingpaper&content%5B%5D=paper`
- **Paper-Detail:** `https://www.oecd-ilibrary.org/.../{DOI_SUFFIX}`
- **PDF:** Detail-Seite → Download-Link

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#searchField, input[name="q"]` | `textbox "Search"` |
| Such-Button | `button[type="submit"], .search-btn` | `button "Search"` |
| Ergebnis-Liste | `.result-item, .search-result` | — |
| Ergebnis-Titel | `.result-item h3 a, .title a` | `link "Paper Title"` |
| Autoren | `.result-item .authors, .meta-authors` | — |
| Jahr | `.result-item .date, .pub-date` | — |
| Typ-Badge | `.result-item .content-type` | — |
| PDF-Download | `a.pdf-link, a[href*=".pdf"]` | `link "PDF"` |
| Nächste Seite | `.pagination .next a` | `link "Next"` |
| Filter: Working Papers | `input[value="workingpaper"]` | `checkbox "Working Papers"` |

## Workflow

### Suche (Open Access Inhalte)

1. `browser_navigate` → `https://www.oecd-ilibrary.org/search?q=QUERY`
2. `browser_wait_for` → Ergebnisliste laden
3. `browser_snapshot` → Ergebnisse prüfen
4. **Optional:** Filter auf "Working Papers" oder "Papers" setzen
5. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('.result-item, .search-result')).map(r => ({
  title: r.querySelector('h3 a, .title a')?.textContent?.trim() || '',
  url: r.querySelector('h3 a, .title a')?.href || '',
  authors: r.querySelector('.authors, .meta-authors')?.textContent?.trim() || '',
  year: r.querySelector('.date, .pub-date')?.textContent?.trim() || '',
  type: r.querySelector('.content-type')?.textContent?.trim() || '',
  pdf_url: r.querySelector('a[href*=".pdf"]')?.href || ''
}))
```

### PDF-Download

1. Paper-Detail öffnen
2. `browser_snapshot` → Download-Optionen prüfen
3. Viele OECD Working Papers sind frei verfügbar
4. `browser_click` → "Read" oder "PDF" Link
5. Bei Paywall: DOI extrahieren → über pdf_resolver.py (Unpaywall) versuchen

## Bekannte Probleme

- **Kein REST API:** OECD iLibrary hat kein öffentliches Suchapi
- **Mischung OA/Paywall:** Manche Inhalte sind frei, andere erfordern Lizenz
- **OECD Working Papers:** Meistens frei verfügbar und besonders wertvoll für Policy-Forschung
- **Langsame Seite:** Große Ladezeiten, 3-5 Sekunden Timeout empfohlen
- **DOIs:** OECD-Publikationen haben fast immer DOIs → gut für Crossref-Lookup
