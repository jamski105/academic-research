# ProQuest — Browser Navigation Guide

## URL-Schema

- **HAN-Zugang:** `http://lfh.hh-han.com/han/proquest`
- **Direkt (oeffentlich, limitiert):** `https://www.proquest.com/`
- **Suche (Ergebnis-URL):** `https://www.proquest.com/results/{RESULT_SET_ID}/{PAGE}?accountid={ACCOUNT_ID}`
- **Detail:** `https://www.proquest.com/docview/{DOC_ID}?accountid={ACCOUNT_ID}`
- **PDF:** `https://www.proquest.com/docview/{DOC_ID}/fulltextPDF/{RESULT_SET_ID}/{POS}?accountid={ACCOUNT_ID}`

**WICHTIG:** ProQuest zeigt bei oeffentlichem Zugang nur OA-Inhalte. Fuer lizenzierte Inhalte (Business Source Premier, Dissertations & Theses) ist HAN-Login erforderlich.

## Login

1. HAN-Login durchfuehren (siehe `han_login.md`) via `http://lfh.hh-han.com/han/proquest`
2. Nach erfolgreichem Login wird direkt zu `proquest.com` weitergeleitet
3. Header zeigt "Zugang gewährt durch [Institution]"

## Cookie-Consent

Beim ersten Besuch erscheint ein Cookie-Banner. Schliessen via:
- `browser_click` auf `button "Alle ablehnen"` oder `button "Alle Cookies akzeptieren"`

## Selektoren

### Suchseite

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input#searchTerm[name="searchTerm"]` | `textbox "Suchbegriffe eingeben"` |
| Such-Button | — | `button "Suchen"` |
| Erweiterte Suche | — | `link "Erweiterte Suche"` |
| Quellentyp-Tabs | — | `link "Fachzeitschriften"`, `link "Dissertationen und Abschlussarbeiten"` |
| Volltext-Filter | `checkbox "Volltext"` | Checkbox vor der Suche |
| Peer-Review-Filter | `checkbox "Durch Fachleute geprüft"` | Peer-Reviewed-Filter |

### Suchergebnisse

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Ergebnis-Container | `.resultItem` | Einzelnes Suchergebnis |
| Titel | `.truncatedResultsTitle` | Artikel-Titel (Text) |
| Titel-Link | `a[href*="/docview/"]` | Link zur Detailseite |
| Autoren | `.truncatedAuthor` | Autoren-Zeile |
| Quellentyp | `.source-type-label` | "Wissenschaftliche Zeitschrift", "Arbeitspapier", etc. |
| Abstract-Toggle | `.addFlashPageParameterformat_abstract` | `link "Kurzfassung/Details"` — klicken zum Aufklappen |
| PDF-Link | `a[title*="Volltext - PDF"]` | Direkter PDF-Download |
| Ergebnis-Anzahl | `h3` mit Text "{N} Ergebnisse" | Ergebnis-Counter |
| Naechste Seite | Link mit Text "›" | Pagination: naechste Seite |
| Letzte Seite | Link mit Text "»Ende" | Pagination: letzte Seite |
| Seiten-Eingabe | `input#pageNbrField` | `textbox "Zur Seitennummer springen"` |

### Filter (linke Sidebar auf Ergebnisseite)

| Filter | Accessibility |
|--------|--------------|
| Quellentyp | Heading "Quellentyp" |
| Publikationsdatum | Heading "Publikationsdatum" |
| Thema | Heading "Thema" |
| Sprache | Heading "Sprache" |
| Datenbank | Heading "Datenbank" |

## Workflow

### Suche (via HAN)

1. HAN-Login (siehe `han_login.md`) → `http://lfh.hh-han.com/han/proquest`
2. `browser_wait_for` → ProQuest-Suchmaske geladen
3. Cookie-Banner schliessen falls vorhanden
4. `browser_snapshot` → Suchfeld identifizieren
5. `browser_type` → Query in `textbox "Suchbegriffe eingeben"` eingeben
6. `browser_click` → `button "Suchen"`
7. `browser_wait_for` → Ergebnisliste laden
8. **Optional:** Filter auf "Dissertationen und Abschlussarbeiten" setzen
9. `browser_evaluate` → Ergebnisse extrahieren:
```javascript
Array.from(document.querySelectorAll('.resultItem')).map(item => {
  const titleEl = item.querySelector('.truncatedResultsTitle');
  const docViewLink = Array.from(item.querySelectorAll('a')).find(a => a.href.includes('/docview/'));
  const docId = docViewLink?.href?.match(/\/docview\/(\d+)/)?.[1] || '';
  return {
    title: titleEl?.textContent?.trim() || '',
    url: docViewLink?.href || '',
    doc_id: docId,
    authors: item.querySelector('.truncatedAuthor')?.textContent?.trim() || '',
    source_type: item.querySelector('.source-type-label')?.textContent?.trim() || '',
    pdf_url: item.querySelector('a[title*="Volltext - PDF"]')?.href || '',
    has_fulltext: !!item.querySelector('a[title*="Volltext - PDF"]'),
    source_module: 'proquest'
  };
})
```
10. Bei Bedarf: Pagination via Klick auf Link "›" (naechste Seite)

### PDF-Download

1. Ergebnis-Detail oeffnen → `browser_click` auf Titel-Link (`a[href*="/docview/"]`)
2. `browser_snapshot` → PDF-Link suchen
3. `browser_click` → `a[title*="Volltext - PDF"]`
4. `browser_wait_for` → PDF-Viewer laden
5. Falls eingebetteter Viewer: `browser_evaluate` → PDF-URL aus iframe extrahieren:
```javascript
document.querySelector('iframe[src*=".pdf"], embed[src*=".pdf"]')?.src || ''
```

## Datenbanken

**Via HAN (Leibniz FH):**
- **Publicly Available Content Database** — OA-Inhalte (auch ohne Login)
- **Dissertations & Theses** — Dissertationen und Abschlussarbeiten

**Hinweis:** Ohne HAN-Login zeigt ProQuest nur oeffentlich zugaengliche Inhalte aus der "Publicly Available Content Database".

## Bekannte Probleme

- **Nur via HAN sinnvoll:** Ohne institutionellen Zugang nur OA-Inhalte
- **Abstracts nicht direkt sichtbar:** "Kurzfassung/Details" ist ein Toggle-Link — muss geklickt werden um Abstract anzuzeigen
- **PDF-Viewer:** PDFs werden in eingebettetem Viewer angezeigt, Download-URL muss aus iframe extrahiert werden
- **Session-Timeout:** Sessions laufen nach ~20 Minuten ab
- **Langsam:** ProQuest-Seiten laden oft langsam (3-5 Sekunden), grosszuegige Timeouts setzen
- **Locale:** Seite ist auf Deutsch — Accessibility-Labels verwenden deutsche Begriffe ("Suchen", "Volltext - PDF", "Suchbegriffe eingeben")
- **Ergebnis-Limit:** ProQuest zeigt max. 250 Ergebnisse pro Suche (20 pro Seite)
- **Cookie-Banner:** Muss beim ersten Besuch geschlossen werden
- **Quellentyp-Icons:** SVG-Icons mit CSS-Klasse `.sourceTypeIcon` — nicht als Selektor verwenden
