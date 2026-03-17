# REPEC/IDEAS — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://ideas.repec.org/cgi-bin/htsearch?q=QUERY`
- **Erweiterte Suche:** `https://ideas.repec.org/cgi-bin/htsearch?q=QUERY&cmd=Search%21&ul=%2F&dt=range`
- **Paper-Detail:** `https://ideas.repec.org/p/HANDLE.html` oder `https://ideas.repec.org/a/HANDLE.html`
- **Working Papers:** `https://ideas.repec.org/p/...`
- **Journal Articles:** `https://ideas.repec.org/a/...`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input[name="q"]` | `textbox "Search"` |
| Such-Button | `input[type="submit"]` | `button "Search!"` |
| Ergebnis-Liste | `ol li, .result-item` | — |
| Ergebnis-Link | `ol li a, .result-title a` | `link "Paper Title"` |
| Paper-Titel (Detail) | `h1, #title` | — |
| Autoren (Detail) | `#author-body a` | — |
| Abstract (Detail) | `#abstract-body` | — |
| Download-Links (Detail) | `#download-body a` | `link "Download"` |

## Workflow

### Suche

1. `browser_navigate` → `https://ideas.repec.org/cgi-bin/htsearch?q=QUERY`
2. `browser_wait_for` → Ergebnisliste laden
3. `browser_snapshot` → Ergebnisse prüfen
4. `browser_evaluate` → Links extrahieren:
```javascript
Array.from(document.querySelectorAll('ol li')).map(li => ({
  title: li.querySelector('a')?.textContent?.trim() || li.textContent?.trim().split('\n')[0] || '',
  url: li.querySelector('a')?.href || ''
}))
```

### Detail-Seiten scrapen

Für jedes Ergebnis die Detail-Seite öffnen:

1. `browser_navigate` → Paper-URL
2. `browser_snapshot` → Metadaten extrahieren
3. `browser_evaluate`:
```javascript
({
  title: document.querySelector('h1, #title')?.textContent?.trim() || '',
  authors: Array.from(document.querySelectorAll('#author-body a')).map(a => a.textContent?.trim()),
  abstract: document.querySelector('#abstract-body')?.textContent?.trim() || '',
  download_links: Array.from(document.querySelectorAll('#download-body a')).map(a => ({
    text: a.textContent?.trim(),
    url: a.href
  }))
})
```

## Bekannte Probleme

- **Kein API:** REPEC hat kein öffentliches REST API, nur Browser-Zugang
- **Alte Website:** Einfaches HTML, keine JavaScript-SPA — gut für Scraping
- **Wenig Metadaten in Suchergebnissen:** Detail-Seite muss einzeln geladen werden
- **Rate Limit:** Moderate Limits, 1-2 Sekunden Pause zwischen Requests
- **Working Papers:** Viele Ergebnisse sind Working Papers ohne Peer Review
