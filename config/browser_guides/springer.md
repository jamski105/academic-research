# Springer Nature — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://link.springer.com/search?query=QUERY`
- **Artikel-Filter:** `https://link.springer.com/search?query=QUERY&facet-content-type=Article`
- **Paper-Detail:** `https://link.springer.com/article/10.1007/ARTICLE_ID`
- **Chapter-Detail:** `https://link.springer.com/chapter/10.1007/CHAPTER_ID`
- **PDF (Open Access):** `https://link.springer.com/content/pdf/10.1007/ARTICLE_ID.pdf`

## Selektoren

### Suchseite

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input[name="query"]` | `textbox` |
| Ergebnis-Card | `.app-card-open` | — |
| Titel + Link | `.app-card-open__heading a`, `h3 a` | `link "Paper Title"` |
| Abstract/Snippet | `.app-card-open__description` | — |
| Autoren | `.app-card-open__authors` | — |
| Datum/Jahr | `.app-card-open__meta`, `.c-meta__item` | — |
| Content-Typ | `.c-meta__type` | Text: "Article", "Conference paper", "Chapter", "Book" |
| Open Access | `.c-meta__item` mit Text "Open access" | — |
| Ergebnis-Anzahl | `.app-search-filter__result-count` | "Showing 1-20 of N results" |
| Naechste Seite | `a[rel="next"]` | — |

### Filter

| Filter | Selektor |
|--------|---------|
| Content-Typ | `#list-content-type-filter` (Article, Chapter, ConferencePaper, Book, etc.) |
| Open Access | `#list-publishing-model-filter` |
| Sprache | `#list-language-filter` |
| Disziplin | `#list-discipline-filter` |

### Cookie-Consent

**WICHTIG:** Beim ersten Besuch erscheint ein Cookie-Dialog. Diesen per `browser_evaluate` schliessen:
```javascript
const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Reject'));
if (btn) btn.click();
```
Oder via `browser_click` auf den Button mit Text "Reject optional cookies".

## Workflow

### Suche (kein HAN noetig fuer OA)

1. `browser_navigate` → `https://link.springer.com/search?query=QUERY`
2. Cookie-Dialog schliessen (falls vorhanden)
3. `browser_snapshot` → Ergebnisse pruefen
4. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('.app-card-open')).map(card => {
  const titleLink = card.querySelector('h3 a');
  const url = titleLink?.href || '';
  const doiMatch = url.match(/(10\.\d{4,}\/[^\s]+)/);
  const metaItems = Array.from(card.querySelectorAll('.c-meta__item'));
  const isOA = metaItems.some(m => m.textContent?.trim() === 'Open access');
  const dateItem = metaItems.find(m => /\d{4}/.test(m.textContent) && !m.textContent.includes('Open'));
  return {
    title: titleLink?.textContent?.trim() || '',
    url: url,
    doi: doiMatch?.[1] || '',
    authors: card.querySelector('.app-card-open__authors')?.textContent?.trim().replace(/\s+/g, ' ') || '',
    year: dateItem?.textContent?.trim()?.match(/(\d{4})/)?.[1] || '',
    type: card.querySelector('.c-meta__type')?.textContent?.trim() || '',
    abstract: card.querySelector('.app-card-open__description')?.textContent?.trim() || '',
    is_open_access: isOA,
    source_module: 'springer'
  };
})
```
5. Bei Bedarf: `browser_click` auf `a[rel="next"]` fuer naechste Seite

### PDF-Download (Open Access)

1. Paper-Detail oeffnen
2. `browser_snapshot` → "Download PDF" Button suchen
3. `browser_click` → PDF-Download starten
4. Alternativ: DOI bekannt → direkt `https://link.springer.com/content/pdf/{DOI}.pdf`

### PDF-Download (via HAN fuer lizenzierte E-Books)

**Lizenzierte Pakete (Leibniz FH):** Wirtschaftswissenschaften + Technik & Informatik

1. HAN-Login (siehe `han_login.md`)
2. Navigation via `http://lfh.hh-han.com/han/springer-e-books-it/doi.org/{DOI}`
3. `browser_snapshot` → Download-Button sollte verfuegbar sein
4. HAN leitet zu Microsoft OAuth weiter → User loggt manuell ein

**WICHTIG:** HAN-Service heisst `springer-e-books-it`, nicht `springer`. Die URL-Struktur ist:
`http://lfh.hh-han.com/han/springer-e-books-it/doi.org/{DOI}`

## Bekannte Probleme

- **Cookie-Consent:** Muss beim ersten Besuch geschlossen werden, blockiert sonst die Seite
- **Paywall:** Nicht-OA Papers zeigen nur Abstract ohne HAN
- **E-Books vs. Journals:** HAN-Zugang gilt primaer fuer E-Book-Pakete, nicht alle Springer-Journals
- **Rate Limiting:** Moderate Limits, 1-2 Sekunden Pause empfohlen
- **DOI-Extraktion:** DOI ist im URL-Pfad enthalten (`/article/10.1007/...` oder `/chapter/10.1007/...`)
- **Content-Typen:** Ergebnisse mischen Articles, Conference Papers, Chapters und Books
