# Google Scholar — Navigation Guide

**URL:** https://scholar.google.com
**Auth:** keine
**Max. Ergebnisse:** 20 (2 Seiten à 10)
**Anti-Scraping:** **hoch** — Google blockiert Bots aggressiv. 2-3 Sekunden Pause zwischen Aktionen. Bei CAPTCHA: Screenshot machen, User informieren, Partial Results zurückgeben. Max. ~100 Requests/Tag pro IP.

## Hinweise

- URL-Parameter: `?q=<QUERY>` für Erstsuche, `?start=10&q=<QUERY>` für Seite 2.
- Nach `browser-use state` enthält jede Ergebniszeile mehrere Links: Titel, PDF, Zitationen ("Cited by N" / "Zitiert von N"), "Speichern", "Zitieren". **Nicht den ersten Link in der Ergebniszeile klicken** — wähle anhand des Link-Texts (z. B. "Cited by" enthält die Zitationszahl).
- Autoren-Zeile folgt dem Format `AUTOR1, AUTOR2 - VENUE, JAHR - PUBLISHER`. Parsing erfolgt durch den LLM aus dem `state`-Output.
- Kein API-Key, keine offizielle API. Scholar blockiert IPs nach Erkennung dauerhaft — vorsichtig einsetzen.
