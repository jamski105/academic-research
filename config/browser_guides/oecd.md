# OECD — Browser Navigation Guide

## URL-Schema

- **Suche (alle Inhalte):** `https://www.oecd.org/en/search.html?orderBy=mostRelevant&q=QUERY`
- **Suche (nur Publikationen):** `https://www.oecd.org/en/search/publications.html?orderBy=mostRelevant&q=QUERY`
- **Paper-Detail:** `https://www.oecd.org/en/publications/TITLE_DOISUFFIX-en.html`

**WICHTIG:** Die alte Domain `oecd-ilibrary.org` leitet auf `oecd.org` um. Immer `oecd.org` verwenden.

## Selektoren

### Suchseite

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | — | `searchbox "Search field allowing to enter a search term"` |
| Such-Button | — | `button "Search button"` |
| Ergebnis-Container | `article.search-result-list-item` | `article` in `listitem` |
| Titel + Link | `.search-result-list-item__title a` | `link "Paper Title"` |
| Metadaten | `.search-result-list-item__meta` | Text: "Type•Date•Pages" |
| Snippet | `.search-result-list-item__snippet` | `paragraph` (Keywords via `mark` hervorgehoben) |
| Ergebnis-Anzahl | — | `heading "N results"` |
| Sortierung | — | `combobox "Order by"` (Most relevant, Most recent, Oldest, A-Z, Z-A) |
| Pagination | `navigation "Pagination"` | `button "Page N"`, `button "Next page"` |

### Filter (linke Sidebar)

| Filter | Accessibility | Relevante Optionen |
|--------|--------------|-------------------|
| Sprache | `checkbox "English(N)"` | English, French |
| Content-Typ | `checkbox "Working paper(N)"`, `checkbox "Report(N)"` | Working paper, Report, Policy paper, Policy brief |
| Topics | `checkbox "Governance(N)"`, `checkbox "Digital(N)"` | Governance, Digital, Economy, etc. |

## Workflow

### Suche

1. `browser_navigate` → `https://www.oecd.org/en/search/publications.html?orderBy=mostRelevant&q=QUERY`
   - Bevorzugt `/search/publications.html` um nur Publikationen zu suchen
2. `browser_snapshot` → Ergebnisse pruefen
3. **Optional:** Filter setzen (z.B. "Working paper" checkbox klicken)
4. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('article.search-result-list-item')).map(article => {
  const titleEl = article.querySelector('.search-result-list-item__title a');
  const meta = article.querySelector('.search-result-list-item__meta')?.textContent?.trim() || '';
  const snippet = article.querySelector('.search-result-list-item__snippet')?.textContent?.trim() || '';
  // Metadata-Format: "Report6 August 202590 Pages" — Typ, Datum, Seiten
  const typeMatch = meta.match(/^([\w\s]+?)(\d)/);
  const dateMatch = meta.match(/(\d{1,2}\s\w+\s\d{4})/);
  const yearMatch = meta.match(/(\d{4})/);
  return {
    title: titleEl?.textContent?.trim() || '',
    url: titleEl?.href || '',
    type: typeMatch?.[1]?.trim() || '',
    date: dateMatch?.[1] || '',
    year: yearMatch?.[1] || '',
    snippet: snippet,
    source_module: 'oecd'
  };
})
```
5. Bei Bedarf: Pagination via `browser_click` auf `button "Next page"`

### PDF-Download

1. Paper-Detail oeffnen (`browser_navigate` → Paper-URL)
2. `browser_snapshot` → Download-Optionen suchen
3. OECD Working Papers und Policy Briefs sind oft frei verfuegbar
4. DOI aus URL extrahieren (Suffix `_DOIHASH-en` am Ende der URL)
5. Bei Paywall: DOI → `pdf_resolver.py` (Unpaywall/CORE)

## Bekannte Probleme

- **Domain-Migration:** `oecd-ilibrary.org` → `oecd.org` — alte URLs leiten um aber verlieren ggf. Query-Parameter
- **Kein REST API:** OECD hat kein oeffentliches Such-API
- **Mischung OA/Paywall:** OECD Working Papers meist frei, Reports oft hinter Paywall
- **Langsame Seite:** SPA-basiert (React/Next.js), 3-5 Sekunden Ladezeit
- **Metadata-Parsing:** Typ/Datum/Seiten sind in einem String ohne klare Trenner zusammengefasst
- **DOIs:** OECD-Publikationen haben DOIs im URL-Suffix — nuetzlich fuer Crossref-Lookup
- **Viele Content-Typen:** Nicht alles sind Papers — Blog, News, Events etc. filtern
