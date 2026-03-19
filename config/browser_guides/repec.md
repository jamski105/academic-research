# REPEC/IDEAS — Browser Navigation Guide

## URL-Schema

- **Startseite:** `https://ideas.repec.org/`
- **Suche:** Formular-POST an `https://ideas.repec.org/cgi-bin/htsearch2` — NICHT direkt per URL aufrufbar
- **Paper-Detail:** `https://ideas.repec.org/a/HANDLE.html` (Journal Articles) oder `https://ideas.repec.org/p/HANDLE.html` (Working Papers)

**WICHTIG:** Die alte Such-URL `/cgi-bin/htsearch?q=QUERY` funktioniert NICHT mehr. Die Suche muss ueber das Formular auf der Startseite ausgeloest werden.

## Selektoren

### Startseite + Suchformular

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input[name="q"]` | `textbox "Search econ literature"` |
| Such-Button | — | `button "Search"` |

### Suchergebnisse (nach Formular-Submit)

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Ergebnis-Container | `ol.list-group` | — |
| Einzelnes Ergebnis | `ol.list-group > li.list-group-item` | `listitem` |
| Titel-Link | `li a[href*="/a/"], li a[href*="/p/"]` | `link "Paper Title"` |
| Treffer-Anzahl | — | Text "Found N results for ..." |
| Pagination | `ul.pagination button` | `button "1"`, `button "2"`, ... |

**Ergebnis-Struktur pro `li`:**
- CSS-Klasse `downfree` = Volltext frei verfuegbar, `downnone` = kein Download
- Format: `Autoren (Jahr): Titel-Link` + `<hr>` + Abstract + `RePEc:handle`

### Suchfilter (Dropdowns auf Ergebnisseite)

| Filter | Accessibility | Optionen |
|--------|--------------|----------|
| Typ | `combobox` (erstes) | All, Articles, Papers, Chapters, Books, Software |
| Suche in | `combobox "In:"` | Whole record, Abstract, Keywords, Title, Author |
| Sortierung | `combobox "Sort by:"` | Relevance, Most recent, Most cited, ... |
| Von Jahr | `combobox "From:"` | Any Year, 2025, 2024, ... |
| Bis Jahr | `combobox "To:"` | Any Year, 2025, 2024, ... |

### Detail-Seite

| Element | CSS-Selektor | Beschreibung |
|---------|-------------|--------------|
| Titel | `#title`, `h1` | Paper-Titel |
| Autoren | `#authorlist li` | Autorennamen (als Text, nicht als Links) |
| Abstract | `#abstract-body` | Abstract-Text |
| Download-Links | `#download a` | Volltext-Links (im "Download"-Tab) |
| Zitationen | `#cites` | Zitations-Sektion (im "Citations"-Tab) |
| BibTeX-Export | `#biblio-body` | Suggested Citation + Export-Formular |

**Tab-Struktur:** Detail-Seiten nutzen Tabs: "Author & abstract" (Standard), "Download", "Citations", "Related works & more", "Corrections".

## Workflow

### Suche

1. `browser_navigate` → `https://ideas.repec.org/`
2. `browser_snapshot` → Suchfeld identifizieren (`textbox "Search econ literature"`)
3. `browser_type` → Query eingeben, `submit: true`
4. `browser_snapshot` → Ergebnisse pruefen
5. `browser_evaluate` → Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('ol.list-group > li.list-group-item')).map(li => {
  const links = Array.from(li.querySelectorAll('a'));
  const titleLink = links.find(a => a.href.match(/ideas\.repec\.org\/(a|p|h|b)\//));
  const fullText = li.textContent || '';
  const yearMatch = fullText.match(/\((\d{4})\)/);
  const authorMatch = fullText.match(/^(.+?)\(\d{4}\)/);
  const repecMatch = fullText.match(/(RePEc:\S+)/);
  const hr = li.querySelector('hr');
  let abstract = '';
  if (hr) {
    let node = hr.nextSibling;
    while (node && !node.textContent?.includes('RePEc:')) {
      abstract += node.textContent || '';
      node = node.nextSibling;
    }
  }
  return {
    title: titleLink?.textContent?.trim() || '',
    url: titleLink?.href || '',
    authors: authorMatch?.[1]?.trim().replace(/\s*&\s*/g, '; ') || '',
    year: yearMatch?.[1] || '',
    abstract: abstract.trim(),
    repec_handle: repecMatch?.[1] || '',
    has_fulltext: li.classList.contains('downfree')
  };
})
```
6. Bei Bedarf: Pagination via `browser_click` auf Button "2", "3" etc.

### Detail-Seiten scrapen

Fuer jedes Ergebnis die Detail-Seite oeffnen:

1. `browser_navigate` → Paper-URL
2. `browser_evaluate`:
```javascript
({
  title: document.querySelector('#title, h1')?.textContent?.trim() || '',
  authors: Array.from(document.querySelectorAll('#authorlist li')).map(li => li.textContent?.trim()),
  abstract: document.querySelector('#abstract-body')?.textContent?.trim() || '',
  download_links: Array.from(document.querySelectorAll('#download a')).map(a => ({
    text: a.textContent?.trim(),
    url: a.href
  })),
  repec_handle: document.body.textContent?.match(/(RePEc:\S+)/)?.[1] || ''
})
```

## Bekannte Probleme

- **Kein direkter URL-Zugang zur Suche:** POST-Formular erforderlich, `/cgi-bin/htsearch` ist veraltet
- **Alte Website mit Bootstrap:** Einfaches HTML, keine JavaScript-SPA — gut fuer Scraping
- **Wenig Metadaten in Suchergebnissen:** Abstract ist inline, aber Detail-Seite hat mehr Infos
- **Tab-Navigation auf Detail-Seiten:** Download-Links sind im "Download"-Tab, der ggf. erst geklickt werden muss
- **Rate Limit:** Moderate Limits, 1-2 Sekunden Pause zwischen Requests
- **Working Papers:** Viele Ergebnisse sind Working Papers ohne Peer Review
- **Kein DOI in Suchergebnissen:** DOIs muessen ggf. von der Detail-Seite extrahiert werden
