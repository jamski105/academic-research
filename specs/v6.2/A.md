# Spec: Chunk A — Browser-Guides für Buch-Download (v6.2)

**Ticket:** #87
**Chunk:** A
**Branch:** `feat/v6.2-A-browser-guides`
**Stand:** 2026-05-13

---

## Ziel

7 neue und 1 aktualisierter Browser-Guide unter `config/browser_guides/` als kanonische
Referenzdokumentation für die Site-Subagenten aus F16 (Audit-Roadmap §15a F16.1).

Die Guides beschreiben pro Site: wo der Volltext zu finden ist, welche Authentifizierung
nötig ist, welche Pickup-Trigger zu erwarten sind und welche Fallstricke existieren.

---

## Dateien

| Datei | Status |
|---|---|
| `config/browser_guides/tib.md` | NEU |
| `config/browser_guides/oapen.md` | NEU |
| `config/browser_guides/doab.md` | NEU |
| `config/browser_guides/degruyter.md` | NEU |
| `config/browser_guides/nationallizenzen.md` | NEU |
| `config/browser_guides/ebook-central.md` | NEU |
| `config/browser_guides/kvk.md` | NEU |
| `config/browser_guides/springer.md` | UPDATE (Buch-Download-Block ergänzen) |

---

## Pflichtstruktur (alle 8 Guides)

Jeder Guide muss exakt diese 5 H2-Abschnitte in dieser Reihenfolge enthalten:

```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

Abweichungen (z. B. Umbenennung, zusätzliche H2 vor/nach diesen) sind nur mit expliziter
Begründung erlaubt. Der `springer.md`-Update ergänzt diese Abschnitte **nach** dem
bestehenden v6.0-Inhalt unter einem eigenen `## Buch-Download`-Block.

---

## Guide-Inhalte (pro Site)

### TIB Hannover (`tib.md`)

- **URL:** https://www.tib.eu
- **Auth:** keine für OA-Bücher; TIB-Konto für Download-Kontingente (optional)
- **Discovery:** Suche über TIB-Portal, Filter "Bücher", Open-Access-Badge
- **Volltext:** Direktdownload-Button auf Detailseite (meist PDF); DOI-Redirect über
  `doi.org`
- **Pickup-Triggers:** `status: pickup_required` wenn Download-Button fehlt oder
  Konto-Login verlangt wird
- **Fallstricke:** Unterschied TIB-eigener Bestand vs. externes Repository (TIB leitet
  weiter); Rate-Limiting bei >10 Downloads/Minute

### OAPEN (`oapen.md`)

- **URL:** https://www.oapen.org
- **Auth:** keine (Open-Access-Repositorium)
- **Discovery:** Suche über OAPEN-Katalog, ISBN/DOI-Direktlink
- **Volltext:** "Download PDF"-Button auf Detailseite; auch über
  `library.oapen.org/handle/<handle>`
- **Pickup-Triggers:** nur bei technischen Fehlern (Server-Fehler 5xx, leere
  Download-Seite)
- **Fallstricke:** Handle-URLs und DOI-URLs zeigen teils unterschiedliche Seiten;
  verwaiste Handles (Buch entfernt) geben 404

### DOAB / Directory of Open Access Books (`doab.md`)

- **URL:** https://www.doabooks.org
- **Auth:** keine (Verzeichnis-Service)
- **Discovery:** Suche über DOAB-Katalog; DOAB liefert Metadaten + Link zum
  Verlagsserver
- **Volltext:** DOAB liefert keinen Direktdownload — Volltext-Link zeigt auf
  Verlags-/Repository-Seite (OAPEN, Springer, etc.)
- **Pickup-Triggers:** `status: pickup_required` wenn Verlags-Link auf Paywall zeigt
  oder kein Volltext-Link vorhanden
- **Fallstricke:** DOAB ist Aggregator, nicht Repositorium — immer Weiterleitung;
  manche Einträge haben nur Metadaten ohne Volltext-Link

### De Gruyter (`degruyter.md`)

- **URL:** https://www.degruyter.com
- **Auth:** Shibboleth/IP-basiert über Institutionszugang; ODER De-Gruyter-Konto für
  OA-Titel
- **Discovery:** Suche über DeGruyter-Portal, Filter "Books", OA-Badge; alternativ
  ISBN/DOI-Direktlink
- **Volltext:** "PDF herunterladen"-Button auf Buch- oder Kapitelseite; OA-Titel ohne
  Login direkt; lizenzierte Titel nur über Instituts-Auth
- **Pickup-Triggers:** `status: pickup_required` wenn Auth-Wall sichtbar und kein
  Instituts-Zugang konfiguriert
- **Fallstricke:** Kapitelweise vs. Vollbuch-Download; einzelne Kapitel können
  lizenziert sein, Buch selbst OA; CAPTCHA bei schnellen Requests

### Nationallizenzen DFG (`nationallizenzen.md`)

- **URL:** https://www.nationallizenzen.de
- **Auth:** DFN-AAI / Shibboleth mit Hochschulkonto; Anmeldung über
  nationallizenzen.de-Portal
- **Discovery:** Suche über Nationallizenzen-Katalog oder direkt bei beteiligten
  Verlagen (Springer, Wiley, etc.)
- **Volltext:** Weiterleitung zum Verlag nach erfolgreicher Shibboleth-Auth; Download
  direkt beim Verlag
- **Pickup-Triggers:** `status: pickup_required` wenn Hochschule nicht in Nationallizenz
  einbezogen oder Shibboleth-Flow schlägt fehl
- **Fallstricke:** Nationallizenz gilt nur für bestimmte Erscheinungsjahre (oft bis
  2007–2015); Neuerscheinungen nicht enthalten; Auth-Redirect ist mehrstufig

### Ebook Central (ProQuest) (`ebook-central.md`)

- **URL:** https://ebookcentral.proquest.com
- **Auth:** Shibboleth/HAN/IP-basiert über Institutionszugang
- **Discovery:** Suche über Ebook-Central-Plattform, ISBN/Titel-Filter; auch als Link
  aus OPAC erreichbar
- **Volltext:** "Full Book Download" (wenn Lizenz vorhanden) oder kapitelweiser
  Download; Online-Reader als Fallback
- **Pickup-Triggers:** `status: pickup_required` wenn nur Online-Reader (kein Download),
  oder DRM-Beschränkung (max. Seiten/Tage-Limit erreicht)
- **Fallstricke:** DRM-PDFs (Adobe DRM) sind nicht archivierbar; Download-Limit
  pro User/Tag; Session-Timeout nach Inaktivität

### KVK — Karlsruher Virtueller Katalog (`kvk.md`)

- **URL:** https://kvk.bibliothek.kit.edu
- **Auth:** keine für Metadaten-Abfrage; Fernleihe/Direktbestell-Links verlangen
  Bibliothekskonto
- **Discovery:** ISBN/Titel/Autor-Suche; KVK aggregiert OPAC-Bestände aus hunderten
  Bibliotheken
- **Volltext:** KVK liefert keinen Volltext — gibt Standort-Info zurück
  (welche Bibliotheken besitzen das Buch)
- **Pickup-Triggers:** immer `status: pickup_required` (KVK ist Standort-Finder,
  kein Downloader); Output enthält Bibliotheks-Standorte für Pickup-Liste
- **Fallstricke:** KVK zeigt physische UND digitale Bestände gemischt; Fernleihe-Link
  variiert je Bibliothek; nicht jede Bibliothek hat Online-Bestellung aktiviert

### Springer (Update) (`springer.md` — Buch-Download-Block)

- **Ergänzung zu:** bestehendem v6.0-Artikel-Guide
- **Neuer Block:** `## Buch-Download` mit `springer-book-fetcher`-kompatiblem Flow
- **URL-Muster:** `https://link.springer.com/book/10.xxxx/978-...`
- **Auth:** wie Artikel — OA ohne Login; Campus-Zugriff via IP/Shibboleth
- **Discovery:** Direktlink per ISBN→DOI-Lookup; oder Suche mit Filter
  `content-type=Book`
- **Volltext:** "Download book PDF"-Button auf Buchseite; alternativ
  kapitelweise über "Download chapter PDF"
- **Pickup-Triggers:** `status: pickup_required` wenn "Access denied" / kein
  PDF-Button
- **Fallstricke:** Springer unterscheidet Bücher (`/book/`) von Buchkapiteln
  (`/chapter/`); Buch-DOI und Kapitel-DOI sind verschieden; einige Bücher nur
  als eBook ohne freien PDF-Export

---

## Konsistenz-Anforderungen

- Alle 7 neuen Guides: exakt 5 H2-Abschnitte in der vorgeschriebenen Reihenfolge.
- Springer-Update: 5 neue H2-Abschnitte als zusammenhängender `## Buch-Download`-Block
  (unter der bestehenden v6.0-Struktur).
- Jeder Guide nennt im Header: URL, Auth-Typ, Anti-Scraping-Einschätzung.
- Pickup-Triggers beschreiben immer das erwartete `status`-Feld des Subagenten-Outputs
  (konsistent mit Master-Output-Schema: `success | pickup_required | captcha | no_match`).

---

## Nicht in Scope

- Subagenten-Implementierungen (Chunk D und E)
- Per-Uni-Profile (Chunk B)
- Tatsächliche HTTP-Requests oder browser-use-Session-Code
- Test-Suite (documentation-only; keine automatisierten Tests erforderlich)
