# Destatis — Browser Navigation Guide

## URL-Schema

- **Startseite:** `https://www.destatis.de/DE/Home/_inhalt.html`
- **Suche:** `https://www.destatis.de/SiteGlobals/Forms/Suche/Servicesuche_Formular.html?nn=206104&input_=&gts=&templateQueryString=QUERY`
- **Themen:** `https://www.destatis.de/DE/Themen/_inhalt.html`
- **GENESIS (Datenbank):** `https://www-genesis.destatis.de/genesis/online`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#searchInput, input[name="templateQueryString"]` | `textbox "Suchbegriff"` |
| Such-Button | `button.btn-search` | `button "Suchen"` |
| Ergebnis-Liste | `.search-result, .result-list li` | — |
| Ergebnis-Titel | `.search-result h3 a, .result-title a` | `link "Titel"` |
| Ergebnis-Beschreibung | `.search-result .description` | — |
| Publikation-Link | `a[href*="/Publikationen/"]` | — |
| Download-Link | `a[href*=".pdf"]` | `link "PDF Download"` |

## Workflow

1. `browser_navigate` → Destatis-Suchseite
2. `browser_snapshot` → Suchfeld identifizieren
3. `browser_type` → Query eingeben
4. `browser_click` → Suche starten
5. `browser_wait_for` → Ergebnisse laden
6. `browser_evaluate` → Ergebnisse extrahieren:
```javascript
Array.from(document.querySelectorAll('.search-result, .result-list li')).map(r => ({
  title: r.querySelector('h3 a, .result-title a')?.textContent?.trim() || '',
  url: r.querySelector('h3 a, .result-title a')?.href || '',
  description: r.querySelector('.description, p')?.textContent?.trim() || '',
  pdf_url: r.querySelector('a[href*=".pdf"]')?.href || ''
}))
```

## Bekannte Probleme

- **Kein akademisches Format:** Ergebnisse sind Statistik-Berichte, keine Papers — Autoren/DOI fehlen oft
- **Deutsch:** Seite ist primär auf Deutsch, englische Queries liefern weniger Treffer
- **PDF-Berichte:** PDFs sind oft große Berichte (>100 Seiten), nicht einzelne Papers
- **GENESIS-Datenbank:** Für Tabellendaten besser GENESIS direkt nutzen (anderes Interface)
