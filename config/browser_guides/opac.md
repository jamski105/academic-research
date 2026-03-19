# OPAC Leibniz FH — Browser Navigation Guide

## URL-Schema

- **Startseite:** `https://lbsvz2.gbv.de/DB=57/LNG=DU/`
- **Suche:** `https://lbsvz2.gbv.de/DB=57/LNG=DU/CMD?ACT=SRCHA&IKT=1016&SRT=YOP&TRM={QUERY}`
- **Detail:** Titel-Link in Ergebnisliste anklicken (PPN-basiert)
- **Suchtypen:** IKT=1016 (Alle Wörter), IKT=4 (Titel), IKT=1004 (Person), IKT=21 (Schlagwort)

## Login

**OPAC erfordert Bibliotheks-Anmeldung vor der Nutzung.**

1. `browser_navigate` → `https://lbsvz2.gbv.de/DB=57/LNG=DU/`
2. `browser_snapshot` → Login-Link suchen ("Anmelden", "Login", "Mein Konto")
3. **STOPP** → User informieren:
   ```
   OPAC-Login erforderlich.
   Bitte melden Sie sich im Browser-Fenster mit Ihrem Bibliothekskonto an.
   Ich warte auf die erfolgreiche Anmeldung.
   ```
4. `browser_wait_for` → Warte auf Anmelde-Bestätigung (Timeout: 120s)
   - Erkennungszeichen: "Abmelden"-Link sichtbar, oder Nutzername in Header
5. `browser_snapshot` → Verifiziere eingeloggten Zustand

**WICHTIG:** Credentials NIEMALS automatisch eingeben.

## Selektoren

| Element | Accessibility / CSS | Beschreibung |
|---------|-------------------|--------------|
| Suchfeld | ref=e84, `input[name="TRM"]` | Freitext-Suchfeld |
| Such-Button | ref=e87, `input[value="Suchen"]` | Suche ausloesen |
| Suchtyp-Dropdown | Combobox neben Suchfeld | IKT-Auswahl (Alle Woerter, Titel, etc.) |
| Ergebnis-Tabelle | `table` mit Ergebnis-Rows | Trefferliste |
| Titel-Link | `a` in Titel-Zelle | Link zur Detailansicht |
| Volltext-Link | `a[href*="han.com"]`, `a[href*="doi.org"]` | HAN-Proxy oder DOI-Link |
| Naechste Seite | `a[href*="NXT"]`, Link "Weiter" | Pagination |
| Anzahl Treffer | Text "Treffer X - Y von Z" | Ergebnis-Count |

## Workflow

### Suche

1. `browser_navigate` → `https://lbsvz2.gbv.de/DB=57/LNG=DU/CMD?ACT=SRCHA&IKT=1016&SRT=YOP&TRM={QUERY}`
   - Query URL-encodieren (Leerzeichen → `+`)
2. `browser_snapshot` → Trefferliste pruefen
3. Falls "0 Treffer" → leeres Ergebnis-Array zurueckgeben
4. `browser_evaluate` → Metadaten aus Ergebnis-Tabelle extrahieren
5. Fuer jeden Treffer: Detailseite oeffnen → erweiterte Metadaten extrahieren

### Detailseite — Metadaten extrahieren

Auf der Detailseite stehen die Felder als Tabellen-Zeilen:

| Feld-Label | Extrahieren als |
|-----------|----------------|
| "Titel" | `title` |
| "Person/en" | `authors` (Array, Komma-getrennt) |
| "Ausgabe" | `edition` |
| "Veroeffentlichungsangabe" | `publisher`, `year` (parsen) |
| "ISBN" | `isbn` |
| "DOI" | `doi` |
| "Schlagwoerter" | `keywords` |
| "Sprache" | `language` |
| "Inhalt" → "Volltext" | `pdf_url` (HAN-Proxy-URL oder DOI-Link) |

**JavaScript fuer Metadaten-Extraktion:**
```javascript
const rows = document.querySelectorAll('table tr, .data tr');
const data = {};
rows.forEach(r => {
  const label = r.querySelector('td:first-child, th')?.textContent?.trim();
  const value = r.querySelector('td:last-child')?.textContent?.trim();
  if (label && value) data[label] = value;
});
// Volltext-Links extrahieren
const links = Array.from(document.querySelectorAll('a[href*="han.com"], a[href*="doi.org"]'));
data.fulltext_urls = links.map(a => ({ url: a.href, text: a.textContent.trim() }));
data;
```

### Volltext-Links auswerten

OPAC-Ergebnisse enthalten oft HAN-Proxy-Links zu:
- **Springer:** `http://lfh.hh-han.com/han/springer-e-books-*/doi.org/{DOI}`
- **EBSCO:** Links zu Business Source Premier / EconLit
- **ProQuest:** `http://lfh.hh-han.com/han/proquest/...`
- **Direkt-DOI:** `https://doi.org/{DOI}`

Diese Links werden als `pdf_url` im Paper-Output gespeichert.
Der PDF-Download ueber HAN-Links erfolgt in Phase 5 via `han_login.md`.

## Bekannte Probleme

- **Einzeltreffer-Redirect:** Bei nur 1 Treffer springt OPAC direkt zur Detailansicht statt die Trefferliste zu zeigen
- **GBV PICA System:** Altes tabellenbasiertes Layout, keine modernen CSS-Klassen
- **Session-Timeout:** Login-Session kann nach Inaktivitaet ablaufen
- **URL-Encoding:** Sonderzeichen in Query muessen URL-encodiert werden
- **Pagination:** Ergebnisse auf mehrere Seiten verteilt, "Weiter"-Link folgen
- **Volltext nicht immer vorhanden:** Nicht jedes OPAC-Ergebnis hat Volltext-Links
- **DOI-Feld:** DOI steht unter dem Label "Identifier", nicht "DOI" — Format: `DOI: 10.1007/...`
- **Ergebnis-Zaehler:** Format "X von Y" in `strong`-Element (z.B. "1 von 1", "Treffer 1 - 10 von 42")
- **Selektoren koennen variieren:** GBV PICA nutzt keine stabilen CSS-Klassen — bei Problemen `browser_snapshot` nutzen um aktuelle Struktur zu inspizieren
