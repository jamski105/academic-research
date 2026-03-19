# Neue Browser-Module hinzufügen

Browser-Module sind Datenbanken ohne offene API, die per Playwright MCP durchsucht werden.
Das Plugin ist modular aufgebaut: Neue Module erfordern keinen Code — nur Konfiguration in 3 Dateien.

---

## 3 Schritte

### Schritt 1: Modul in `config/search_modules.yaml` registrieren

Neuen Eintrag unter `modules:` hinzufuegen:

```yaml
  mein_modul:
    enabled: true                    # false = deaktiviert
    tier: 1                          # 1 = frei/institutionell, 2 = HAN-Server noetig
    type: browser                    # browser = Playwright MCP
    search_url: "https://example.com/search?q="
    description: "Beschreibung der Datenbank"
    browser_guide: mein_modul.md     # Dateiname des Browser Guides
    disciplines: [economics, business]  # Optional: nur bei passenden Themen aktiv
    # auth: han                      # Optional: wenn HAN-Login noetig
```

**Felder:**

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `enabled` | Ja | `true`/`false` — kann vom User ueberschrieben werden |
| `tier` | Ja | `1` = frei, `2` = HAN-Server noetig |
| `type` | Ja | Immer `browser` fuer Playwright-Module |
| `search_url` | Ja | Basis-URL fuer die Suche (Query wird angehaengt) |
| `description` | Ja | Kurzbeschreibung fuer Logging und Status |
| `browser_guide` | Ja | Dateiname in `config/browser_guides/` |
| `disciplines` | Nein | Array — Modul nur aktiv bei passenden Themen |
| `auth` | Nein | `han` wenn HAN-Server-Login noetig |
| `databases` | Nein | Sub-Datenbanken (z.B. EBSCO: business_source_premier, econlit) |
| `han_pdf_url` | Nein | HAN-URL-Template fuer PDF-Download |

### Schritt 2: Browser Guide erstellen

Neue Datei unter `config/browser_guides/mein_modul.md` anlegen.
Nutze folgendes Template:

```markdown
# Mein Modul — Browser Navigation Guide

## URL-Schema

- **Suche:** `https://example.com/search?q=QUERY`
- **Detail:** `https://example.com/paper/{ID}`
- **PDF:** `https://example.com/pdf/{ID}`

## Selektoren

| Element | CSS-Selektor | Accessibility |
|---------|-------------|---------------|
| Suchfeld | `input[name="q"]` | `textbox "Search"` |
| Ergebnis-Container | `.result-item` | — |
| Titel + Link | `.result-title a` | `link "Paper Title"` |
| Autoren | `.result-authors` | — |
| Jahr | `.result-year` | — |
| PDF-Link | `.pdf-download a` | `link "PDF"` |
| Naechste Seite | `.pagination .next` | `link "Next"` |

## Workflow

1. `browser_navigate` → `https://example.com/search?q=QUERY`
2. `browser_wait_for` → Warte auf `.result-item` Elemente
3. `browser_evaluate` → Daten extrahieren:
   ```javascript
   Array.from(document.querySelectorAll('.result-item')).map(r => ({
     title: r.querySelector('.result-title a')?.textContent || '',
     url: r.querySelector('.result-title a')?.href || '',
     authors: r.querySelector('.result-authors')?.textContent || '',
     year: r.querySelector('.result-year')?.textContent || '',
     pdf_url: r.querySelector('.pdf-download a')?.href || ''
   }))
   ```
4. Ergebnisse in Paper-Format parsen
5. Bei Bedarf: `browser_click` → "Next" fuer weitere Seiten

## Bekannte Probleme

- **Rate Limiting:** Max X Requests pro Minute
- **Login:** Falls noetig, beschreiben wie der Login-Flow funktioniert
- **Anti-Scraping:** Welche Massnahmen die Seite hat
```

**Tipps fuer Selektoren:**
- Nutze `browser_snapshot` um den Accessibility Tree zu sehen — dort sind die richtigen Selektoren
- `browser_evaluate` mit `document.querySelectorAll()` fuer CSS-Selektoren
- Accessibility-Labels (z.B. `link "PDF"`) sind stabiler als CSS-Klassen

### Schritt 3: Testen

```bash
# Modul isoliert testen (nur dieses Modul durchsuchen)
/research "test query" --modules mein_modul --mode quick
```

Pruefen:
- Ergebnisse werden gefunden und als Papers formatiert
- DOI/Titel/Autoren/Jahr korrekt extrahiert
- PDF-URLs vorhanden (falls OA)
- Keine Fehler im Session-Log

---

## Login-Flow Patterns

### Kein Login (frei zugaenglich)
Die meisten Tier-1-Module. Einfach navigieren und extrahieren.

### OAuth (eigener Flow)
Beispiel: EBSCO. Der Login laeuft ueber die eigene OAuth-Seite der Datenbank.
Im Guide beschreiben: URL, Login-Button-Selektor, Redirect-Erkennung.

### HAN-Server (Microsoft OAuth)
Fuer institutionelle Zugaenge. Im Guide:
1. `auth: han` in `search_modules.yaml` setzen
2. Im Browser Guide auf `han_login.md` verweisen
3. Der Agent navigiert zur HAN-URL, stoppt, wartet auf manuellen Login

### IP-basiert / bibid
Beispiel: EZB. Zugang ueber IP-Range der Institution oder bibid-Parameter in der URL.
Kein Login noetig, aber nur aus dem Uni-Netz erreichbar.

---

## Beispiel: JSTOR hinzufuegen

```yaml
# config/search_modules.yaml
  jstor:
    enabled: true
    tier: 1
    type: browser
    search_url: "https://www.jstor.org/action/doBasicSearch?Query="
    description: "JSTOR — Zeitschriften und Buecher (Suche frei, Volltext teils OA)"
    browser_guide: jstor.md
```

Dann `config/browser_guides/jstor.md` mit Selektoren und Workflow erstellen.
Dann testen: `/research "test" --modules jstor --mode quick`

---

## Referenzen

- Bestehende Guides: `config/browser_guides/` (9 Guides: 8 Datenbanken + HAN-Login)
- Modul-Registry: `config/search_modules.yaml`
- Browser Searcher Agent: `agents/browser-searcher.md`
- Architektur-Uebersicht: `ARCHITECTURE.md`
