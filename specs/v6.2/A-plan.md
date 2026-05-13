# Browser-Guides v6.2 (Chunk A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 7 neue Browser-Guide-Markdown-Dateien unter `config/browser_guides/` erstellen und `springer.md` um einen Buch-Download-Block ergänzen, alle mit einheitlicher 5-H2-Pflichtstruktur.

**Architecture:** Reine Markdown-Dokumentation ohne Code. Einheitliche Struktur (Login-Flow · Discovery-Pfad · Volltext-Lokation · Pickup-Triggers · Bekannte Fallstricke) in allen 8 Guides. Konsistenz-Nachweis durch Sichtprüfung (grep-basiert).

**Tech Stack:** Markdown. Keine Abhängigkeiten. Kein Code.

**Konsistenz-Anforderung (alle 8 Guides):**
Jeder der 7 neuen Guides enthält exakt diese 5 H2-Abschnitte:
- `## Login-Flow`
- `## Discovery-Pfad`
- `## Volltext-Lokation`
- `## Pickup-Triggers`
- `## Bekannte Fallstricke`

`springer.md`-Update: diese 5 Abschnitte als `## Buch-Download`-Block (sub-H3) nach bestehendem v6.0-Inhalt.

---

### Task 1: `tib.md` — TIB Hannover

**Files:**
- Create: `config/browser_guides/tib.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/tib.md`:

```markdown
# TIB Hannover — Browser-Guide (Buch-Download)

**URL:** https://www.tib.eu
**Auth:** keine für OA-Titel; TIB-Konto für Download-Kontingente (optional)
**Anti-Scraping:** niedrig — TIB ist kooperativ.

## Login-Flow

1. `browser-use open https://www.tib.eu`
2. Für OA-Titel: kein Login erforderlich — direkt zu Discovery-Pfad.
3. Für kontingentierte Downloads: "Anmelden"-Link oben rechts klicken.
4. `browser-use state` → Formular finden (Felder "Benutzername" / "Passwort").
5. Credentials eingeben, "Anmelden"-Button klicken.
6. Auf Weiterleitung zur Suchseite warten.

## Discovery-Pfad

1. Suchfeld im Header: Titel, ISBN oder DOI eingeben.
2. `browser-use state` → Suchergebnisse prüfen.
3. Filter "Medientyp: Bücher/Monografien" im linken Panel setzen.
4. Open-Access-Badge ("Open Access" oder OA-Symbol) in Ergebniszeile prüfen.
5. Auf Treffer klicken → Detailseite öffnet.

Alternativ per DOI-Direktlink: `https://doi.org/10.xxxx/...` → TIB löst auf und
leitet auf Detailseite weiter.

## Volltext-Lokation

- Auf der Detailseite: Button "PDF herunterladen" oder "Download PDF" suchen.
- `browser-use state` → Button-Index identifizieren, klicken.
- TIB kann auf externe Repositorien (OAPEN, Verlagsseite) weiterleiten —
  Ziel-URL prüfen, ggf. dortigen Guide verwenden.
- Dateiname nach Download: meist `<DOI-suffix>.pdf` oder Titelbasiert.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Download-Button fehlt auf Detailseite.
  - "Nur im Lesesaal verfügbar"-Hinweis sichtbar.
  - TIB-Konto-Login für Download verlangt wird (kein Konto konfiguriert).
  - Server-Fehler 5xx oder leere Downloadseite nach Klick.
- `status: captcha` wenn CAPTCHA-Bild in `browser-use state` sichtbar ist →
  Screenshot sichern, User informieren.
- `status: no_match` wenn Suche 0 Treffer liefert.

## Bekannte Fallstricke

- TIB unterscheidet eigenen Bestand vs. externe Verlinkung — ein Treffer in TIB
  bedeutet nicht, dass TIB den Volltext hostet.
- Rate-Limiting bei >10 Downloads/Minute — 2–3 Sekunden Pause zwischen Requests.
- DOI-Resolver leitet manchmal auf Verlags-Landing-Page statt Direktdownload.
- Einige Titel nur als Print-Exemplar verfügbar → `pickup_required`.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/tib.md
```

Erwartete Ausgabe (exakt diese 5 Zeilen):
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/tib.md
git commit -m "docs(A): Browser-Guide TIB Hannover (v6.2 #87)"
```

---

### Task 2: `oapen.md` — OAPEN

**Files:**
- Create: `config/browser_guides/oapen.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/oapen.md`:

```markdown
# OAPEN — Browser-Guide (Buch-Download)

**URL:** https://www.oapen.org
**Auth:** keine (Open-Access-Repositorium)
**Anti-Scraping:** niedrig — OAPEN ist öffentlich zugänglich.

## Login-Flow

Kein Login erforderlich. Alle Inhalte sind Open Access.

1. `browser-use open https://www.oapen.org`
2. Direkt zur Discovery fortfahren.

## Discovery-Pfad

1. Suchfeld im Header: Titel, Autor oder ISBN eingeben.
2. `browser-use state` → Suchergebnisse prüfen.
3. Alternativ per DOI-Direktlink: `https://doi.org/10.xxxx/...` → OAPEN-Detailseite.
4. Alternativ per Handle: `https://library.oapen.org/handle/<handle>`.
5. Auf Treffer klicken → Detailseite mit Metadaten und Download-Button.

## Volltext-Lokation

- Auf der Detailseite: Button "Download PDF" suchen.
- `browser-use state` → Button-Index identifizieren, klicken.
- PDF liegt direkt auf OAPEN-Servern — keine Weiterleitung zu externen Seiten.
- Dateiname: meist `<handle>.pdf` oder titelbasiert.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Download-Button fehlt (seltener Fehlerfall).
  - Server-Fehler 5xx oder leere Download-Antwort.
  - Handle-URL gibt 404 zurück (Buch entfernt oder umgezogen).
- `status: no_match` wenn Suche 0 Treffer liefert.

## Bekannte Fallstricke

- Handle-URLs und DOI-URLs können auf unterschiedliche Seiten zeigen — beide
  versuchen falls eine 404 liefert.
- Verwaiste Handles (Buch nachträglich entfernt) geben 404 ohne Redirect.
- OAPEN enthält nur OA-Bücher — wenn Titel nicht gefunden, ist er vermutlich nicht OA.
- Große PDFs (>50 MB) können Timeout auslösen — Download-Fortschritt überwachen.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/oapen.md
```

Erwartete Ausgabe:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/oapen.md
git commit -m "docs(A): Browser-Guide OAPEN (v6.2 #87)"
```

---

### Task 3: `doab.md` — Directory of Open Access Books

**Files:**
- Create: `config/browser_guides/doab.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/doab.md`:

```markdown
# DOAB — Directory of Open Access Books — Browser-Guide

**URL:** https://www.doabooks.org
**Auth:** keine (Verzeichnis-Service, kein eigener Volltext)
**Anti-Scraping:** niedrig — DOAB ist öffentlich.

## Login-Flow

Kein Login erforderlich. DOAB ist ein Metadaten-Aggregator ohne eigenen Volltext.

1. `browser-use open https://www.doabooks.org`
2. Direkt zur Discovery fortfahren.

## Discovery-Pfad

1. Suchfeld auf der Startseite: Titel, Autor, ISBN oder DOI eingeben.
2. `browser-use state` → Suchergebnisse prüfen.
3. Filter "Publisher", "Language", "Subject" im linken Panel optional setzen.
4. Auf Treffer klicken → Metadaten-Detailseite öffnet.
5. Volltext-Link auf Detailseite suchen (Feld "PDF" oder "Download" oder
   "Publisher URL").

## Volltext-Lokation

- DOAB hostet **keinen** Volltext direkt — alle Download-Links zeigen auf externe
  Repositorien (OAPEN, Verlagsseite, Zenodo, etc.).
- `browser-use state` → "Download"-Link-Index identifizieren, klicken.
- Weiterleitung zu externem Provider → dortigen Browser-Guide verwenden:
  - OAPEN-Link → `oapen.md`
  - Springer-Link → `springer.md` (Buch-Download-Abschnitt)
  - De Gruyter-Link → `degruyter.md`
  - Unbekannter Provider → `generic-fetcher`-Subagent

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Volltext-Link zeigt auf Paywall oder lizenzierte Seite.
  - Kein Volltext-Link auf Detailseite vorhanden (nur Metadaten).
  - Externer Provider gibt 404 oder Access-Denied zurück.
- `status: no_match` wenn Suche 0 Treffer liefert.

## Bekannte Fallstricke

- DOAB ist Aggregator, nicht Repositorium — immer Weiterleitung zum Volltext.
- Manche Einträge haben nur Metadaten ohne Volltext-Link (Verlag hat noch nicht
  geliefert).
- Link-Rot: Einige ältere Einträge verweisen auf inzwischen umgezogene oder
  gelöschte URLs.
- DOAB-Suche ist weniger präzise als direktes ISBN-/DOI-Lookup — DOI-Direktsuche
  bevorzugen wenn möglich.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/doab.md
```

Erwartete Ausgabe:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/doab.md
git commit -m "docs(A): Browser-Guide DOAB (v6.2 #87)"
```

---

### Task 4: `degruyter.md` — De Gruyter

**Files:**
- Create: `config/browser_guides/degruyter.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/degruyter.md`:

```markdown
# De Gruyter — Browser-Guide (Buch-Download)

**URL:** https://www.degruyter.com
**Auth:** Shibboleth/IP-basiert (Institutionszugang) ODER kein Login für OA-Titel
**Anti-Scraping:** mittel — CAPTCHA bei schnellen Requests möglich.

## Login-Flow

**Für OA-Titel:** kein Login erforderlich — direkt zu Discovery-Pfad.

**Für lizenzierte Titel (Institutionszugang):**

1. `browser-use open https://www.degruyter.com`
2. "Sign in" / "Anmelden"-Button oben rechts klicken.
3. `browser-use state` → "Sign in via institution" / "Über Institution anmelden"
   suchen, klicken.
4. Shibboleth-Redirect: Hochschule im Dropdown wählen.
5. Hochschul-Login-Formular ausfüllen (Credentials aus Uni-Profil).
6. Auf Weiterleitung zurück zu DeGruyter warten — angemeldeter Status prüfen.

## Discovery-Pfad

1. Suchfeld im Header: Titel, ISBN oder DOI eingeben.
2. `browser-use state` → Filter "Content Type: Books" im linken Panel setzen.
3. OA-Badge ("Open Access") in Ergebniszeile prüfen.
4. Auf Treffer klicken → Buchdetailseite öffnet.
5. Alternativ per DOI-Direktlink: `https://doi.org/10.1515/...` →
   DeGruyter-Detailseite.

## Volltext-Lokation

- Auf der Buchdetailseite: Button "PDF herunterladen" suchen.
  - OA-Titel: Button direkt verfügbar ohne Login.
  - Lizenzierte Titel: Button nur nach erfolgreichem Institutionszugang.
- `browser-use state` → Button-Index identifizieren.
- Achtung: Buchseite (`/book/<isbn>`) vs. Kapitelseite (`/document/<doi>`):
  - Buchseite → "Download all chapters as PDF" oder Einzelkapitel.
  - Kapitelseite → "PDF herunterladen" für einzelnes Kapitel.
- Vollbuch-Download bevorzugen wenn vorhanden.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Auth-Wall / "Access options" statt Download-Button sichtbar.
  - Institutionszugang nicht konfiguriert oder Shibboleth fehlgeschlagen.
  - Nur Online-Lese-Option vorhanden (kein PDF-Download).
- `status: captcha` wenn CAPTCHA in `browser-use state` erkennbar →
  Screenshot sichern, User informieren.
- `status: no_match` wenn Suche 0 Treffer liefert.

## Bekannte Fallstricke

- Buch-DOI und Kapitel-DOI sind verschieden — `/book/<isbn>` ist der
  Buchkanon-Einstiegspunkt, `/document/<doi>` für einzelne Kapitel.
- Einzelne Kapitel können lizenziert sein, obwohl das Buch selbst OA ist —
  immer Buchseite prüfen, nicht nur Kapitelseite.
- CAPTCHA erscheint bei >5 schnellen Requests in Folge — mind. 3 Sekunden Pause.
- Shibboleth-Redirect ist mehrstufig: DeGruyter → DFN-AAI → Hochschule →
  zurück — vollständigen Redirect abwarten.
- Einige Bücher nur als eBook ohne freien PDF-Export verfügbar (DRM).
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/degruyter.md
```

Erwartete Ausgabe:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/degruyter.md
git commit -m "docs(A): Browser-Guide De Gruyter (v6.2 #87)"
```

---

### Task 5: `nationallizenzen.md` — Nationallizenzen DFG

**Files:**
- Create: `config/browser_guides/nationallizenzen.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/nationallizenzen.md`:

```markdown
# Nationallizenzen DFG — Browser-Guide (Buch-Download)

**URL:** https://www.nationallizenzen.de
**Auth:** DFN-AAI / Shibboleth mit Hochschulkonto (mehrstufig)
**Anti-Scraping:** niedrig auf Nationallizenzen-Portal; mittel beim Ziel-Verlag.

## Login-Flow

Nationallizenzen selbst sind kein Download-Portal — sie ermöglichen Zugang zu
Verlags-Plattformen via Shibboleth.

1. Ziel-Verlagsseite öffnen (z. B. Springer, Wiley — aus Discovery-Ergebnis).
2. Auf der Verlagsseite: "Sign in via institution" oder "Institutional login" klicken.
3. DFN-AAI-Seite öffnet: Hochschule im Suchfeld eingeben oder aus Liste wählen.
4. Hochschul-IdP-Login-Seite: Credentials eingeben (Credentials aus Uni-Profil).
5. Auf Weiterleitung zurück zum Verlag warten.
6. Zugang geprüft → Volltext-Lokation.

## Discovery-Pfad

1. `browser-use open https://www.nationallizenzen.de`
2. Suche im Nationallizenzen-Katalog: Titel, ISBN, DOI oder Verlag.
3. `browser-use state` → Treffer prüfen; Verlags-Link in Trefferdetails notieren.
4. Auf Verlags-Link klicken → Verlagsseite öffnet (Springer, Wiley, etc.).
5. Auf der Verlagsseite weiter im verlagsspezifischen Guide verfahren
   (`springer.md`, etc.).

Alternativ: DOI-Direktlink verwenden — falls Nationallizenz gilt, wird Zugang
nach Shibboleth-Auth gewährt.

## Volltext-Lokation

- Volltext liegt beim jeweiligen Verlag, nicht bei Nationallizenzen.
- Nach erfolgreicher Shibboleth-Auth: Download-Button auf Verlagsseite erscheint.
- Verlagsspezifische Guides für die Volltext-Lokation verwenden:
  - Springer → `springer.md` (Buch-Download-Block)
  - De Gruyter → `degruyter.md`
  - Wiley → verlagseigene URL-Muster

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Hochschule nicht in der betreffenden Nationallizenz enthalten.
  - Shibboleth-Flow schlägt fehl (IdP nicht erreichbar, falsche Credentials).
  - Erscheinungsjahr außerhalb des Nationallizenz-Zeitraums (meist vor 2015).
  - Verlag gibt trotz Auth Access-Denied zurück.
- `status: captcha` wenn Verlag CAPTCHA zeigt nach Auth.
- `status: no_match` wenn Titel nicht im Nationallizenzen-Katalog.

## Bekannte Fallstricke

- Nationallizenzen gelten nur für bestimmte Erscheinungsjahre — häufig bis 2007–2015
  je nach Verlagsvertrag. Neuerscheinungen sind nicht enthalten.
- Auth-Redirect ist mehrstufig: Verlag → Nationallizenzen-Redirect → DFN-AAI →
  Hochschul-IdP → zurück — vollständigen Flow abwarten (kann 10–15 Sekunden dauern).
- Nicht jede Hochschule hat alle Nationallizenzen aktiviert — Uni-Profil prüfen.
- Einige Verlage erfordern zusätzlich Cookie-Akzeptanz vor dem Auth-Flow.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/nationallizenzen.md
```

Erwartete Ausgabe:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/nationallizenzen.md
git commit -m "docs(A): Browser-Guide Nationallizenzen DFG (v6.2 #87)"
```

---

### Task 6: `ebook-central.md` — Ebook Central (ProQuest)

**Files:**
- Create: `config/browser_guides/ebook-central.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/ebook-central.md`:

```markdown
# Ebook Central (ProQuest) — Browser-Guide (Buch-Download)

**URL:** https://ebookcentral.proquest.com
**Auth:** Shibboleth / HAN / IP-basiert (Institutionszugang)
**Anti-Scraping:** niedrig (lizenzierter Zugriff), aber Session-Timeout nach Inaktivität.

## Login-Flow

1. `browser-use open https://ebookcentral.proquest.com`
2. "Sign in" oben rechts klicken.
3. `browser-use state` → "Sign in through your institution" suchen, klicken.
4. Hochschule im Suchfeld eingeben oder aus Liste wählen.
5. Shibboleth-Login: Hochschul-Credentials eingeben (aus Uni-Profil).
6. Auf Weiterleitung zurück zu Ebook Central warten.

Alternativ via HAN-Proxy: `han_login.md` zuerst ausführen, dann
`https://han.<uni-domain>/ebookcentral` aufrufen.

## Discovery-Pfad

1. Suchfeld im Header: Titel, Autor, ISBN eingeben.
2. `browser-use state` → Suchergebnisse prüfen.
3. Filter im linken Panel: "Subject", "Publication Date", "Language".
4. Trefferdetailseite öffnen → Lizenz- und Download-Optionen prüfen.
5. Alternativ über OPAC-Link: OPAC-Eintrag enthält oft Direktlink zu Ebook Central.

## Volltext-Lokation

- Auf Detailseite: "Full Book Download" suchen (wenn Lizenz vorhanden).
- `browser-use state` → Button-Index identifizieren, klicken.
- Falls "Full Book Download" fehlt: "Download Chapter" für kapitelweisen Download.
- Online-Reader ("Read Online") ist kein Download-Äquivalent — nicht verwenden.
- DRM-Hinweis prüfen: "Adobe DRM" bedeutet verschlüsseltes PDF.

## Pickup-Triggers

- `status: pickup_required` wenn:
  - Nur Online-Reader verfügbar (kein "Full Book Download"-Button).
  - DRM-PDF mit Adobe-Encryption (nicht archivierbar).
  - Download-Limit erreicht (z. B. "You have reached the maximum number of
    checkouts").
  - Session-Timeout während Download.
- `status: captcha` wenn CAPTCHA sichtbar.
- `status: no_match` wenn ISBN nicht im Katalog.

## Bekannte Fallstricke

- DRM-PDFs (Adobe Digital Editions) sind technisch downloadbar, aber nicht
  ohne Adobe-Software lesbar und nicht langfristig archivierbar — als
  `pickup_required` behandeln.
- Download-Limit pro User/Tag variiert je Lizenzvertrag (meist 20–50 Seiten
  oder 1 Kapitel/Tag bei Pay-per-Use).
- Session-Timeout nach ~15 Minuten Inaktivität → neu anmelden.
- "Full Book Download" nur bei Institutional-Ownership-Lizenzen — bei
  Short-Term-Loan-Lizenzen nur kapitelweise.
- Einige Institutionen haben Ebook Central nur über HAN eingerichtet, nicht
  direkt — HAN-Flow dann pflichtmäßig.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/ebook-central.md
```

Erwartete Ausgabe:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/ebook-central.md
git commit -m "docs(A): Browser-Guide Ebook Central ProQuest (v6.2 #87)"
```

---

### Task 7: `kvk.md` — Karlsruher Virtueller Katalog

**Files:**
- Create: `config/browser_guides/kvk.md`

- [ ] **Step 1: Datei erstellen**

Inhalt von `config/browser_guides/kvk.md`:

```markdown
# KVK — Karlsruher Virtueller Katalog — Browser-Guide

**URL:** https://kvk.bibliothek.kit.edu
**Auth:** keine für Metadaten-Abfrage; Fernleihe/Bestellung verlangen Bibliothekskonto
**Anti-Scraping:** niedrig — KVK ist öffentlicher Dienst.

## Login-Flow

Für reine Standort-/Verfügbarkeitsabfragen kein Login erforderlich.

Für Fernleihe / Direktbestellung (nicht automatisiert):
1. Bibliotheks-OPAC der gewählten Bibliothek aufrufen.
2. Dort mit Bibliothekskonto anmelden.
3. Fernleihe-Formular ausfüllen — **nicht automatisch auslösen**,
   nur Standort-Info für Pickup-Liste zurückgeben.

## Discovery-Pfad

1. `browser-use open https://kvk.bibliothek.kit.edu`
2. Suchformular ausfüllen: ISBN (bevorzugt), Titel oder Autor.
3. Datenbanken auswählen (Standard: HEIDI, BVB, GBV, SWB — alle aktivieren).
4. "Suchen"-Button klicken.
5. `browser-use state` → Ergebnisliste mit Bibliotheksbeständen prüfen.
6. Für jeden Treffer: Bibliotheks-Name, Standort, Signatur notieren.

## Volltext-Lokation

KVK liefert **keinen Volltext** — gibt ausschließlich Standort-Informationen zurück.

Output-Format für Pickup-Liste:
```json
{
  "status": "pickup_required",
  "kvk_hits": [
    {
      "library": "Bayerische Staatsbibliothek",
      "location": "München",
      "call_number": "4 Ph.pr. 123",
      "loan_type": "vor_ort"
    }
  ]
}
```

Master-Agent entscheidet, welche Bibliotheken in die Pickup-Liste aufgenommen werden.

## Pickup-Triggers

- KVK-Subagent liefert **immer** `status: pickup_required` — KVK ist
  Standort-Finder, kein Downloader.
- Pickup-Daten enthalten: Bibliotheksname, Ort, Signatur, Ausleihbarkeit
  (Lesesaal, Ausleihe, Fernleihe).
- `status: no_match` wenn KVK 0 Treffer in allen Datenbanken liefert.

## Bekannte Fallstricke

- KVK zeigt physische UND digitale Bestände gemischt — "Online-Ressource"-Treffer
  verweisen auf Volltext-URLs (können als sekundäre Discovery genutzt werden).
- Nicht jede Bibliothek hat Online-Bestellung aktiviert — Fernleihe manuell.
- Signatur-Format variiert stark je Bibliothek — nur als Referenz zurückgeben,
  nicht parsen.
- Einige Datenbanken haben Ladezeiten >5 Sekunden — KVK wartet auf alle
  Teilbibliotheken, bevor Ergebnisse angezeigt werden.
- Timeout bei sehr breiten Suchen (viele Datenbanken aktiv) — ggf. Suche
  auf GBV + BVB einschränken.
```

- [ ] **Step 2: Konsistenz prüfen**

```bash
grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/kvk.md
```

Erwartete Ausgabe (5 Abschnitte; der Code-Block im Volltext-Lokation-Abschnitt
enthält kein `^## `, daher exakt 5):
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 3: Commit**

```bash
git add config/browser_guides/kvk.md
git commit -m "docs(A): Browser-Guide KVK Karlsruher Virtueller Katalog (v6.2 #87)"
```

---

### Task 8: `springer.md` — Update (Buch-Download-Block)

**Files:**
- Modify: `config/browser_guides/springer.md`

- [ ] **Step 1: Bestehenden Inhalt prüfen**

```bash
cat /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/springer.md
```

Erwartete v6.0-Inhalte: URL, Auth, Anti-Scraping-Info, Hinweise-Abschnitt.
Den Buch-Download-Block **nach** diesem Inhalt anhängen.

- [ ] **Step 2: Buch-Download-Block anhängen**

Folgenden Block am Ende der Datei `config/browser_guides/springer.md` anhängen:

```markdown

---

## Buch-Download

*Ergänzung v6.2 — kompatibel mit `springer-book-fetcher`-Subagent.*

**URL-Muster:** `https://link.springer.com/book/10.xxxx/978-...`

### Login-Flow

Für OA-Bücher: kein Login erforderlich.

Für Campus-lizenzierte Bücher:
1. IP-basierter Zugang: aus dem Hochschulnetz oder VPN → automatisch erkannt.
2. Shibboleth: "Sign in" → "Sign in via your institution" → Hochschule wählen →
   Hochschul-Credentials eingeben → Weiterleitung zurück zu Springer.

### Discovery-Pfad

1. Suche auf `https://link.springer.com` mit Filter `content-type=Book`:
   `https://link.springer.com/search?query=<TITEL>&content-type=Book`
2. `browser-use state` → Treffer prüfen; OA-Badge erkennen.
3. Auf Buchtitel klicken → `/book/<doi>`-Seite öffnet.
4. Alternativ per DOI-Direktlink oder ISBN-Lookup via
   `https://link.springer.com/search?query=<ISBN>`.

### Volltext-Lokation

- Auf der Buchseite (`/book/...`): Button "Download book PDF" suchen.
- `browser-use state` → Button-Index identifizieren, klicken.
- Falls Vollbuch-Download nicht verfügbar: kapitelweiser Download über
  "Download chapter PDF" auf den Kapitel-Unterseiten.
- Buch-DOI (`/book/10.xxxx/...`) und Kapitel-DOI (`/chapter/10.xxxx/...`)
  sind verschieden — immer Buchseite als Einstieg verwenden.

### Pickup-Triggers

- `status: pickup_required` wenn:
  - "Access denied" oder "Buy access" statt Download-Button.
  - Kein "Download book PDF"-Button auf Buchseite.
  - Nur Kapitelweise-Download (kein Vollbuch) — ggf. kapitelweise als
    Fallback akzeptieren, Master entscheidet.
- `status: captcha` wenn CAPTCHA erscheint.
- `status: no_match` wenn ISBN/DOI nicht auf Springer gefunden.

### Bekannte Fallstricke

- Springer unterscheidet `/book/` (Gesamtbuch) von `/chapter/` (Einzelkapitel) —
  DOI-Lookup muss auf Buchebene landen.
- Einige Bücher nur als eBook ohne freien PDF-Export (nur Online-Lese-Zugriff).
- Rate-Limiting bei schnellen Zugriffen — 2–3 Sekunden Pause empfohlen.
- OA-Badge im Suchergebnis bedeutet nicht immer vollständige PDF-Verfügbarkeit
  (teils nur Abstract OA).
```

- [ ] **Step 3: Konsistenz prüfen**

```bash
grep "^## \|^### " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/springer.md
```

Erwartete Ausgabe (v6.0-Abschnitt + neuer Buch-Block):
```
## Hinweise
## Buch-Download
### Login-Flow
### Discovery-Pfad
### Volltext-Lokation
### Pickup-Triggers
### Bekannte Fallstricke
```

- [ ] **Step 4: Commit**

```bash
git add config/browser_guides/springer.md
git commit -m "docs(A): Browser-Guide Springer — Buch-Download-Block ergänzt (v6.2 #87)"
```

---

### Task 9: Gesamtkonsistenz-Check und Status-Update

**Files:**
- Modify: `specs/v6.2/A-plan.md` (dieses Dokument — nur Status-Update)

- [ ] **Step 1: Alle 8 Guides auf Pflichtstruktur prüfen**

```bash
for f in tib oapen doab degruyter nationallizenzen ebook-central kvk; do
  echo "=== $f.md ===";
  grep "^## " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/${f}.md;
done
```

Erwartete Ausgabe für jeden der 7 neuen Guides:
```
## Login-Flow
## Discovery-Pfad
## Volltext-Lokation
## Pickup-Triggers
## Bekannte Fallstricke
```

- [ ] **Step 2: Springer-Update-Block prüfen**

```bash
grep "^## \|^### " /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/springer.md
```

Erwartete Ausgabe:
```
## Hinweise
## Buch-Download
### Login-Flow
### Discovery-Pfad
### Volltext-Lokation
### Pickup-Triggers
### Bekannte Fallstricke
```

- [ ] **Step 3: Alle Guide-Dateien vorhanden**

```bash
ls /Users/j65674/Repos/academic-research-v6.2-A/config/browser_guides/
```

Muss enthalten: `tib.md`, `oapen.md`, `doab.md`, `degruyter.md`,
`nationallizenzen.md`, `ebook-central.md`, `kvk.md`, `springer.md`
(plus vorhandene v6.0-Guides).

- [ ] **Step 4: status.yaml aktualisieren**

Im Worktree-Haupt-Repo (nicht im Worktree selbst, da gitignored):
status.yaml Chunk A → phase: `implementation_complete`,
last_signal_from_l1.kind: `implementation_complete`.

- [ ] **Step 5: Abschluß-Commit**

```bash
git add specs/v6.2/A-plan.md
git commit -m "docs(A): Plan für Browser-Guides Chunk A (v6.2 #87)"
```

---

## Konsistenz-Anmerkung (Anforderung aus Ticket)

Alle 8 Guides teilen **dieselben 5 H2-Abschnitte** (gemäß Pflichtstruktur):

| Guide | Login-Flow | Discovery-Pfad | Volltext-Lokation | Pickup-Triggers | Bekannte Fallstricke |
|---|---|---|---|---|---|
| tib.md | H2 | H2 | H2 | H2 | H2 |
| oapen.md | H2 | H2 | H2 | H2 | H2 |
| doab.md | H2 | H2 | H2 | H2 | H2 |
| degruyter.md | H2 | H2 | H2 | H2 | H2 |
| nationallizenzen.md | H2 | H2 | H2 | H2 | H2 |
| ebook-central.md | H2 | H2 | H2 | H2 | H2 |
| kvk.md | H2 | H2 | H2 | H2 | H2 |
| springer.md (Update) | H3 in ## Buch-Download | H3 | H3 | H3 | H3 |

`springer.md` kapselt die 5 Sub-Abschnitte unter einem `## Buch-Download`-H2,
um den bestehenden v6.0-Artikel-Inhalt nicht zu vermischen.
