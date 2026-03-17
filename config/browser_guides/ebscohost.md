# EBSCOhost — Browser Navigation Guide

## URL-Schema

- **HAN-Zugang:** `https://han.leibniz-fh.de/han/ebscohost`
- **Suche:** Nach Login wird zu `search.ebscohost.com` weitergeleitet
- **Erweiterte Suche:** URL enthält `/eds/search/advanced`
- **Ergebnisse:** `/eds/results?...`
- **Detail/PDF:** `/eds/detail?...`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#SearchTerm, textarea[name="SearchTerm"]` | `textbox "Search"` |
| Such-Button | `button.search-submit, input[value="Search"]` | `button "Search"` |
| Datenbank-Auswahl | `select#limiters_databases` | `combobox "Databases"` |
| Ergebnis-Titel | `.result-list-record .record-title a` | `link "Paper Title"` |
| Autoren | `.result-list-record .authors` | — |
| Quelle/Jahr | `.result-list-record .source` | — |
| PDF-Link | `a[title*="PDF"], .pdf-link` | `link "PDF Full Text"` |
| HTML-Volltext | `a[title*="HTML"]` | `link "HTML Full Text"` |
| Nächste Seite | `.pagination .next a` | `link "Next"` |
| Ergebnis-Anzahl | `.result-count` | — |

## Workflow

### Suche

1. HAN-Login durchführen (siehe `han_login.md`)
2. `browser_wait_for` → Warte auf EBSCOhost-Suchmaske
3. `browser_snapshot` → Suchfeld identifizieren
4. `browser_type` → Query eingeben
5. `browser_click` → Such-Button klicken
6. `browser_wait_for` → Ergebnisliste laden
7. `browser_evaluate` → Ergebnisse extrahieren:
```javascript
Array.from(document.querySelectorAll('.result-list-record')).map(r => ({
  title: r.querySelector('.record-title a')?.textContent?.trim() || '',
  url: r.querySelector('.record-title a')?.href || '',
  authors: r.querySelector('.authors')?.textContent?.trim() || '',
  source: r.querySelector('.source')?.textContent?.trim() || '',
  pdf_url: r.querySelector('a[title*="PDF"]')?.href || ''
}))
```

### PDF-Download

1. Ergebnis-Detail öffnen → `browser_click` auf Titel
2. `browser_snapshot` → PDF-Link suchen
3. `browser_click` → "PDF Full Text" oder "HTML Full Text"
4. `browser_wait_for` → PDF-Viewer / Download
5. Falls eingebetteter Viewer: `browser_evaluate` → PDF-URL aus iframe extrahieren

## Bekannte Probleme

- **Session-Abhängig:** Nur über HAN-Proxy erreichbar, Sessions laufen ab
- **JavaScript-Heavy:** Seite lädt asynchron, `browser_wait_for` wichtig
- **PDF-Viewer:** PDFs werden oft in eingebettetem Viewer gezeigt, nicht als direkter Download
- **Datenbank-Auswahl:** Standard ist "All Databases" — für spezifischere Suche einzelne DB wählen
- **Limit:** EBSCO zeigt max 250 Ergebnisse pro Suche
