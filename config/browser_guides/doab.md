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
