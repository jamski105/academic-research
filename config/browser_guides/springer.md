# Springer Link — Navigation Guide

**URL:** https://link.springer.com
**Auth:** keine für Metadaten; Volltext je nach Lizenz (Open Access oder Campus-Zugriff)
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig — Springer ist kooperativ.

## Hinweise

- Suchleiste im Header; Direkt-URL `?query=<QUERY>&content-type=Article` für nur-Article-Ergebnisse.
- Jede Ergebniszeile enthält Open-Access-Indikator ("Open Access" als Badge) — bei `browser-use state` als Text sichtbar.
- DOI steht in der URL der Detailseite (`/article/10.xxxx/...`).
- Für Volltext-PDF: Button "Download PDF" auf Detailseite. Bei fehlender Berechtigung stattdessen "Access options"-Button.

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
  - Nur kapitelweiser Download verfügbar (kein Vollbuch) — ggf. kapitelweise
    als Fallback akzeptieren, Master entscheidet.
- `status: captcha` wenn CAPTCHA erscheint.
- `status: no_match` wenn ISBN/DOI nicht auf Springer gefunden.

### Bekannte Fallstricke

- Springer unterscheidet `/book/` (Gesamtbuch) von `/chapter/` (Einzelkapitel) —
  DOI-Lookup muss auf Buchebene landen.
- Einige Bücher nur als eBook ohne freien PDF-Export (nur Online-Lese-Zugriff).
- Rate-Limiting bei schnellen Zugriffen — 2–3 Sekunden Pause empfohlen.
- OA-Badge im Suchergebnis bedeutet nicht immer vollständige PDF-Verfügbarkeit
  (teils nur Abstract OA).
