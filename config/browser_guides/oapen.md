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
