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
- Dateiname nach Download: meist `<DOI-suffix>.pdf` oder titelbasiert.

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
