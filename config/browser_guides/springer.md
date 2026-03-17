# Springer Nature — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://link.springer.com/search?query=QUERY`
- **Erweiterte Suche:** `https://link.springer.com/search?query=QUERY&search-within=Journal&facet-content-type=Article`
- **Paper-Detail:** `https://link.springer.com/article/10.1007/ARTICLE_ID`
- **PDF (Open Access):** `https://link.springer.com/content/pdf/10.1007/ARTICLE_ID.pdf`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#query, input[name="query"]` | `textbox "Search"` |
| Such-Button | `button[type="submit"]` | `button "Search"` |
| Ergebnis-Liste | `#results-list li, .search-result` | — |
| Titel + Link | `.search-result h2 a, .result-title a` | `link "Paper Title"` |
| Autoren | `.authors, .meta-authors` | — |
| Jahr | `.meta-year, time` | — |
| Open Access Badge | `.open-access` | — |
| PDF-Download | `a[data-track-action="download pdf"]` | `link "Download PDF"` |
| Nächste Seite | `a[rel="next"], .next a` | `link "Next"` |
| Ergebnis-Anzahl | `.number-of-search-results` | — |

## Workflow

### Suche (kein HAN nötig für OA)

1. `browser_navigate` → `https://link.springer.com/search?query=QUERY`
2. `browser_wait_for` → Ergebnisliste laden
3. `browser_snapshot` → Ergebnisse prüfen
4. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('#results-list li')).map(r => ({
  title: r.querySelector('h2 a, .result-title a')?.textContent?.trim() || '',
  url: r.querySelector('h2 a, .result-title a')?.href || '',
  authors: r.querySelector('.authors, .meta-authors')?.textContent?.trim() || '',
  year: r.querySelector('time, .meta-year')?.textContent?.trim() || '',
  is_open_access: !!r.querySelector('.open-access'),
  doi: (r.querySelector('h2 a')?.href || '').match(/article\/(10\..+)/)?.[1] || ''
}))
```

### PDF-Download (Open Access)

1. Paper-Detail öffnen
2. `browser_snapshot` → "Download PDF" Button suchen
3. `browser_click` → PDF-Download starten
4. Alternativ: DOI bekannt → direkt `https://link.springer.com/content/pdf/{DOI}.pdf`

### PDF-Download (via HAN für lizenzierte Inhalte)

1. HAN-Login (siehe `han_login.md`)
2. Navigation via `https://han.leibniz-fh.de/han/springer/link.springer.com/article/{DOI}`
3. `browser_snapshot` → Download-Button sollte verfügbar sein

## Bekannte Probleme

- **Paywall:** Nicht-OA Papers zeigen nur Abstract ohne HAN
- **Rate Limiting:** Moderate Limits, 1-2 Sekunden Pause empfohlen
- **JavaScript SPA:** Seite nutzt React, Elemente laden asynchron
- **Captcha:** Selten, aber möglich bei vielen Requests
