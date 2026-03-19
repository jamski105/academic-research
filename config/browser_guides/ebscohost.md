# EBSCO Publication Finder — Browser Navigation Guide

## Zweck

Publication Finder ist ein **Journal-/Zeitschriftenverzeichnis** der Leibniz FH.
Es durchsucht **Publikationstitel** (Zeitschriften, Datenbanken), NICHT einzelne Artikel.

**Fuer Artikelsuche:** OPAC (`opac.md`) nutzen — liefert Artikel mit HAN-Proxy-Links zu EBSCO-Datenbanken.

## URL-Schema

- **Direktzugang:** `https://publications.ebsco.com/?custId=ns259564&groupId=main&profileId=pfui`
- **Suche:** `https://publications.ebsco.com/?search=QUERY&searchField=titlename&searchtype=contains&custId=ns259564&groupId=main&profileId=pfui`
- **Detail:** `https://publications.ebsco.com/details/{ID}?custId=ns259564&groupId=main&profileId=pfui`
- **Datenbanken:** `https://publications.ebsco.com/databases?custId=ns259564&groupId=main&profileId=pfui`

**Parameter:** `custId=ns259564&groupId=main&profileId=pfui` immer mitgeben (Leibniz FH Kennung).

## Login

**Gastzugang:** Suche und Metadaten sind ohne Login verfuegbar.
**Vollzugriff:** Datenbank-Links (z.B. "Business Source Premier") leiten ueber HAN-Server → Microsoft OAuth.

1. `browser_navigate` → Direktzugang-URL
2. `browser_snapshot` → Pruefen ob Login-Banner erscheint
3. Falls Vollzugriff auf Datenbanken noetig:
   - **STOPP** → User informieren:
     ```
     EBSCO-Datenbankzugang erfordert HAN-Login.
     Bitte klicken Sie auf den Datenbank-Link und melden Sie sich ueber Microsoft an.
     Ich warte auf die erfolgreiche Anmeldung.
     ```
   - `browser_wait_for` → Warte auf Redirect (Timeout: 120s)
4. Fuer reine Journal-Suche ist kein Login noetig

**WICHTIG:** Datenbank-Links leiten ueber `login.lfh.hh-han.com` (HAN OpenID Connect) → Microsoft OAuth weiter. Credentials NIEMALS automatisch eingeben.

## Selektoren

**ACHTUNG:** Publication Finder ist eine React-SPA mit CSS Modules (gehashte Klassennamen).
CSS-Klassen wie `results_title__DjBne` aendern sich bei jedem Build.
**Stabile Selektoren:** `data-auto`-Attribute und Accessibility-Labels verwenden!

### Startseite

| Element | Accessibility / data-auto | Beschreibung |
|---------|--------------------------|--------------|
| Suchfeld | `textbox "Titel suchen"` | Journal-Titel-Suche |
| Such-Button | `button "Suche"` | Suche ausloesen |
| Suchfeld-Typ | `button "Wählen Sie das Suchfeld aus Titel"` | Dropdown: Titel, ISSN, Verlag |
| Suchtyp | `button "Wählen Sie den Suchtyp aus Enthält"` | Dropdown: Enthaelt, Beginnt mit, Exakt |
| Ressourcentyp | `button "Wählen Sie den Ressourcentyp aus Alle"` | Filter: Alle, Zeitschrift, Buch, etc. |
| Login-Banner | `link "Willkommen Gast. Melden Sie sich an..."` | EBSCO OAuth Login |
| Datenbanken-Link | `link "Datenbanken durchsuchen"` | Zur Datenbank-Uebersicht |

### Suchergebnisse

| Element | Accessibility / data-auto | Beschreibung |
|---------|--------------------------|--------------|
| Ergebnis-Card | `[data-auto="card"]` (`section.eb-card`) | Ein Journal-Eintrag |
| Metadaten | `[data-auto="metadata-container"]` | Metadaten-Wrapper pro Ergebnis |
| Titel + Link | `h3 a` innerhalb `[data-auto="card"]` | Journal-Titel mit Link zu Detail |
| Peer-Review | `[data-auto="article-type"]` | Badge: "Peer-Reviewed" + Typ ("Zeitschrift") |
| Card-Footer | `[data-auto="card-footer"]` | "Details anzeigen"-Link |
| Ergebnis-Anzahl | `heading "Ergebnisse: 1-N von M"` | h2-Heading ueber Ergebnissen |
| Filter-Panel | `[data-auto="filter-flyout"]` | Sidebar mit Filtern |
| Naechste Seite | `[data-auto="results-nav-next"]` | Pagination: naechste Seite |
| Vorherige Seite | `[data-auto="results-nav-previous"]` | Pagination: vorherige Seite |

### Filter (Sidebar)

| Filter | Accessibility | Optionen |
|--------|--------------|----------|
| Beschraenken auf | `[data-auto="filter-section-toggle"]` | Peer-Reviewed, Volltext |
| Ressourcen | `[data-auto="filter-section-toggle"]` | Zeitschrift, Buch, Report, etc. |
| Themen | `[data-auto="filter-section-toggle"]` | LoC-Klassifikation (Social Sciences, Commerce, ...) |
| Datenbanken | `[data-auto="filter-section-toggle"]` | Business Source Premier, etc. |

## Workflow

### Journal-Suche

1. `browser_navigate` → `https://publications.ebsco.com/?search=QUERY&searchField=titlename&searchtype=contains&custId=ns259564&groupId=main&profileId=pfui`
   - `searchField=titlename` (Titel), `searchField=isxn` (ISSN), `searchField=publishername` (Verlag)
2. `browser_snapshot` → Ergebnisse pruefen
3. `browser_evaluate` → Journal-Daten extrahieren:
```javascript
Array.from(document.querySelectorAll('[data-auto="card"]')).map(card => {
  const titleEl = card.querySelector('h3 a');
  const fullText = card.textContent || '';
  const issnMatch = fullText.match(/ISSN:\s*([\d-X]+(?:;\s*[\d-X]+)*)/i);
  const publisherMatch = fullText.match(/Verlag:\s*(.+?)(?:Alternativer|ISSN|Thema|$)/s);
  const subjectMatch = fullText.match(/Thema[^:]*:\s*(.+?)(?:Verlag|ISSN|Alternativer|$)/s);
  const isPeerReviewed = fullText.includes('Peer-Reviewed');
  // Datenbank-Links (z.B. "Business Source Premier", "EBSCO Open Access Journals")
  const dbLinks = Array.from(card.querySelectorAll('a'))
    .filter(a => a.href.includes('external-link'))
    .map(a => a.textContent.trim());
  return {
    title: titleEl?.textContent?.trim() || '',
    url: titleEl?.href || '',
    issn: issnMatch?.[1]?.trim() || '',
    publisher: publisherMatch?.[1]?.trim() || '',
    subject: subjectMatch?.[1]?.trim() || '',
    is_peer_reviewed: isPeerReviewed,
    databases: dbLinks,
    has_fulltext: fullText.includes('Volltextzugriff'),
    source_module: 'ebsco'
  };
})
```
4. Bei Bedarf: Pagination via `browser_click` auf `[data-auto="results-nav-next"]`

### ISSN-Suche

Um zu pruefen ob ein bestimmtes Journal verfuegbar ist:

1. Suchfeld-Typ umschalten: `browser_click` auf `button "Wählen Sie das Suchfeld aus Titel"`
2. `browser_click` → "ISSN" waehlen
3. ISSN eingeben und suchen

## Datenbanken (Leibniz FH)

**Lizenzierte Datenbanken (erfordern HAN-Login):**
- **Business Source Premier** — Wirtschaftswissenschaftliche Volltexte
- **Computers & Applied Sciences Complete** — Informatik und Technik

**Oeffentliche Datenbanken (kein Login noetig):**
- Academic Journals, AgEcon Search, Bentham Open, De Gruyter Brill Open Journals, u.v.m.

**Artikelsuche in EBSCO-Datenbanken:**
Publication Finder durchsucht nur Journal-Titel. Fuer die Suche nach einzelnen Artikeln:
1. **OPAC** (`opac.md`) → Findet Artikel und liefert HAN-Proxy-Links zu EBSCO-Datenbanken
2. **Crossref/OpenAlex/Semantic Scholar** → Findet Artikel und DOIs, Volltextzugriff dann via OPAC/HAN

## Bekannte Probleme

- **Kein Artikelsuche:** Publication Finder durchsucht NUR Zeitschriften-/Publikationstitel, NICHT Artikelinhalte
- **CSS Modules:** Alle CSS-Klassen sind gehasht (`results_title__DjBne`) und aendern sich bei jedem Build — NUR `data-auto`-Attribute und Accessibility-Labels verwenden!
- **Datenbank-Links via HAN:** Klick auf Datenbank-Link (z.B. "Business Source Premier") leitet ueber `login.lfh.hh-han.com` → Microsoft OAuth
- **React-SPA:** Seite laedt asynchron, `browser_wait_for` nach Navigation verwenden
- **Suchfeld-Default:** Standard ist "Titel" + "Enthaelt" — fuer ISSN-Suche muss Dropdown umgestellt werden
- **Gastzugang limitiert:** Metadaten sichtbar, aber Datenbank-Direktlinks erfordern Login
- **Ergebnis-Zaehler:** Format `heading "Ergebnisse: 1-N von M"` als h2-Element
