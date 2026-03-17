# ProQuest — Browser Navigation Guide

## URL-Schema

- **HAN-Zugang:** `https://han.leibniz-fh.de/han/proquest`
- **Nach Login:** `https://www.proquest.com/`
- **Suche:** `https://www.proquest.com/results/...`
- **Dissertationen:** `https://www.proquest.com/dissertations-theses/...`
- **Detail:** `https://www.proquest.com/docview/DOC_ID`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#queryTermField, input[name="queryTerm"]` | `textbox "Search"` |
| Such-Button | `button#searchToResultPage` | `button "Search"` |
| Datenbank-Filter | `.database-filter` | — |
| Ergebnis-Titel | `.resultTitle a, h3.result-title a` | `link "Paper Title"` |
| Autoren | `.author, .authorInfo` | — |
| Quelle/Jahr | `.source, .pubInfo` | — |
| Abstract | `.abstract` | — |
| PDF-Link | `a[title*="Full text - PDF"], .pdf-link` | `link "Full text - PDF"` |
| Nächste Seite | `.pagination .nextPage a` | `link "Next"` |

## Workflow

### Suche (immer via HAN)

1. HAN-Login durchführen (siehe `han_login.md`)
2. `browser_wait_for` → ProQuest-Suchmaske geladen
3. `browser_snapshot` → Suchfeld identifizieren
4. `browser_type` → Query eingeben
5. `browser_click` → Such-Button
6. `browser_wait_for` → Ergebnisliste
7. **Optional:** Filter auf "Dissertations & Theses" setzen
8. `browser_evaluate` → Ergebnisse extrahieren:
```javascript
Array.from(document.querySelectorAll('.resultItem, .result-item')).map(r => ({
  title: r.querySelector('.resultTitle a, h3 a')?.textContent?.trim() || '',
  url: r.querySelector('.resultTitle a, h3 a')?.href || '',
  authors: r.querySelector('.author, .authorInfo')?.textContent?.trim() || '',
  source: r.querySelector('.source, .pubInfo')?.textContent?.trim() || '',
  abstract: r.querySelector('.abstract')?.textContent?.trim() || '',
  pdf_available: !!r.querySelector('a[title*="PDF"], .pdf-link')
}))
```

### PDF-Download

1. Ergebnis-Detail öffnen → `browser_click` auf Titel
2. `browser_snapshot` → "Full text - PDF" Link suchen
3. `browser_click` → PDF öffnen
4. `browser_wait_for` → PDF-Viewer laden
5. `browser_evaluate` → Tatsächliche PDF-URL aus Viewer extrahieren:
```javascript
document.querySelector('iframe[src*=".pdf"], embed[src*=".pdf"]')?.src || ''
```

## Bekannte Probleme

- **Nur via HAN:** ProQuest erfordert immer institutionellen Zugang
- **Dissertationen-Fokus:** Hauptnutzen ist Zugriff auf Dissertationen/Thesen die sonst nirgends verfügbar sind
- **PDF-Viewer:** PDFs werden in eingebettetem Viewer angezeigt, Download-URL muss aus iframe extrahiert werden
- **Session-Timeout:** Sessions laufen nach ~20 Minuten ab
- **Langsam:** ProQuest-Seiten laden oft langsam, großzügige Timeouts setzen (5-10s)
