# Google Scholar — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://scholar.google.com/scholar?q=QUERY`
- **Nächste Seite:** `https://scholar.google.com/scholar?start=10&q=QUERY`
- **Profil:** `https://scholar.google.com/citations?user=USER_ID`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input[name="q"]` | `textbox "Suche"` (DE) / `textbox "Search"` (EN) |
| Ergebnis-Container | `.gs_r.gs_or.gs_scl` | — |
| Titel + Link | `.gs_rt a` | `link "Paper Title"` |
| Autoren/Venue/Jahr | `.gs_a` | — |
| Snippet | `.gs_rs` | — |
| Zitationen-Link | `.gs_fl a` — **filtern nach "Cited by" / "Zitiert von"** | `link "Zitiert von: N"` (DE) / `link "Cited by N"` (EN) |
| PDF-Link | `.gs_or_ggsm a` | `link "[PDF] domain.tld"` |
| Nächste Seite | `#gs_n a` (letzter) | `link "Weiter"` (DE) / `link "Next"` (EN) |

**WICHTIG:** `.gs_fl` enthält auch "Speichern"/"Zitieren"-Buttons als `<a>` Tags — den Zitationen-Link immer per Textfilter identifizieren, NICHT einfach den ersten Link nehmen.

## Workflow

1. `browser_navigate` → `https://scholar.google.com`
2. `browser_snapshot` → Suchfeld identifizieren
3. `browser_type` → Query eingeben
4. `browser_press_key` → Enter
5. `browser_wait_for` → Warte auf `.gs_r` Elemente
6. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('.gs_r.gs_or.gs_scl')).map(r => {
  // Zitationen: Link filtern der "Cited by" oder "Zitiert von" enthält
  const citLink = Array.from(r.querySelectorAll('.gs_fl a'))
    .find(a => /Cited by|Zitiert von/i.test(a.textContent));
  return {
    title: r.querySelector('.gs_rt a')?.textContent || '',
    url: r.querySelector('.gs_rt a')?.href || '',
    authors_line: r.querySelector('.gs_a')?.textContent || '',
    snippet: r.querySelector('.gs_rs')?.textContent || '',
    citations: parseInt(citLink?.textContent?.match(/\d+/)?.[0] || '0'),
    pdf_url: r.querySelector('.gs_or_ggsm a')?.href || ''
  };
})
```
7. Autoren-Zeile parsen: Format ist `AUTOR1, AUTOR2 - VENUE, JAHR - PUBLISHER`
8. Bei Bedarf: `browser_click` → "Weiter"/"Next" für Seite 2 (max 2 Seiten)

## Bekannte Probleme

- **Anti-Scraping:** Google blockiert Bots aggressiv. **2-3 Sekunden Pause** zwischen Aktionen.
- **CAPTCHA:** Bei Erkennung → `browser_take_screenshot` → User informieren, Partial Results zurückgeben.
- **Rate Limit:** Max 20 Ergebnisse (2 Seiten) pro Session.
- **Kein API-Key:** Google Scholar hat keine offizielle API.
- **IP-Blocking:** Nach ~100 Requests pro Tag kann die IP gesperrt werden.
