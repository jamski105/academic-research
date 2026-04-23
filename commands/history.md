---
description: View past research sessions and their results
allowed-tools: Read, Bash(cat ~/.academic-research/*), Bash(ls ~/.academic-research/*), Bash(~/.academic-research/venv/bin/python *)
argument-hint: [optional: search query or date]
---

# Recherche-Verlauf

Vergangene Recherche-Sessions ansehen, die unter `~/.academic-research/sessions/` abgelegt sind.

## Verwendung

- `/academic-research:history` — Alle Sessions auflisten
- `/academic-research:history "DevOps"` — Sessions per Query durchsuchen
- `/academic-research:history 2026-03-17` — Details einer bestimmten Session anzeigen
- `/academic-research:history stats` — Aggregatstatistik anzeigen

## Umsetzung

1. Session-Index einlesen: `cat ~/.academic-research/sessions/index.json`
2. Wenn ein Argument übergeben wurde:
   - Datum → Session von diesem Tag finden, Details anzeigen
   - `"stats"` → Aggregatstatistik anzeigen
   - Sonst → Sessions per Query-Text durchsuchen
3. Ergebnisse als formatierte Tabelle ausgeben:

```
📚 Recherche-Verlauf

| # | Datum      | Query                  | Papers | PDFs  | Modus    |
|---|------------|------------------------|--------|-------|----------|
| 1 | 2026-03-17 | DevOps Governance      | 47     | 42/47 | standard |
| 2 | 2026-03-15 | AI Ethics              | 32     | 28/32 | deep     |
| 3 | 2026-03-10 | ML in Healthcare       | 25     | 20/25 | quick    |

Gesamt: 3 Sessions, 104 Papers, 90 PDFs
```

Für die Detailansicht ausgeben: Paperliste, Zitat-Anzahl, Modul-Verteilung, Dateipfade.
