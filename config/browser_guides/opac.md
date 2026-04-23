# OPAC — Leibniz FH Bibliotheks-Katalog — Navigation Guide

**URL (über HAN):** https://han.leibniz-fh.de → OPAC (Bibliothek)
**Auth:** HAN-Login (siehe `han_login.md`) optional — OPAC ist teils ohne Login abfragbar; Volltexte und Fernleihe brauchen Login.
**Max. Ergebnisse:** 20
**Anti-Scraping:** niedrig.

## Hinweise

- OPAC bildet den physischen und elektronischen Bestand der Leibniz-FH-Bibliothek ab. Für die meisten Themen weniger ergiebig als EBSCO/ProQuest, aber unverzichtbar für Bücher und institutionelle Schriftenreihen.
- Suchmaske ähnelt einem klassischen Bibliothekskatalog: Suchbegriff, Suchfeld (Titel/Autor/Schlagwort), Bool'sche Verknüpfung.
- Ergebnisse zeigen Verfügbarkeit und Signatur (z. B. "Nur vor Ort", "Ausleihbar", "Online-Zugang").
- Für Online-Zugang → Link "Zum elektronischen Volltext" — leitet oft über HAN auf externen Provider weiter.
- Fernleihe über "Anfordern"-Button nach Login. Nicht automatisiert auslösen — nur Metadaten extrahieren.

## Fehlerbehandlung

- "Keine Treffer" bei generischer Suche → Synonyme/alternative Schlagwörter versuchen.
- Server-Fehler → OPAC-Wartungsfenster prüfen (oft Sonntagnacht), später retry.
