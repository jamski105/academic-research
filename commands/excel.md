---
description: Generate or update a literature Excel spreadsheet via the vendored xlsx skill
disable-model-invocation: true
allowed-tools: Read, Write
argument-hint: [--papers papers.json] [--output literature.xlsx] [--context]
---

# Literatur-Excel-Generator

Erstellt ein formatiertes Excel-Workbook aus gescorten Papers. Die eigentliche Excel-Generierung übernimmt der plugin-intern vendorierte `xlsx`-Skill unter `${CLAUDE_PLUGIN_ROOT}/skills/xlsx/` — keine externe Plugin-Installation nötig.

## Verwendung

- `/academic-research:excel` — Aus letzter Session generieren
- `/academic-research:excel --papers papers.json --output my_literature.xlsx`
- `/academic-research:excel --context` — Kapitel-Zuordnung aus akademischem Kontext mitnehmen

## Voraussetzung

Der `xlsx`-Skill ist im Plugin eingebunden (`skills/xlsx/`) und steht ohne weitere Installation zur Verfügung. Das Setup benötigt `python3` mit `openpyxl` — wird über `/academic-research:setup` mit installiert.

## Erwartete Sheets

1. **Literaturübersicht** — Vollständige Paperliste mit 5D-Scores, Clustern, farbcodiert
2. **Cluster-Analyse** — Statistik pro Cluster mit Balkendiagramm
3. **Kapitel-Zuordnung** — Papers den Gliederungskapiteln zugeordnet (benötigt `--context`)
4. **Datenblatt** — Rohdaten für programmatischen Zugriff

## Umsetzung

### Schritt 1: Papers lokalisieren

```bash
if [ -z "$PAPERS" ]; then
  LATEST=$(ls -t ~/.academic-research/sessions/ | head -1)
  PAPERS=~/.academic-research/sessions/$LATEST/ranked.json
fi
```

### Schritt 2: Input strukturieren

Lies die Paper-Daten aus `$PAPERS` (JSON-Array mit Feldern `title`, `authors`, `year`, `doi`, `total_score`, `cluster`, `relevance_score`, `recency_score`, `quality_score`, `authority_score`, `access_score`, `venue`, `source_module`).

Wenn `--context` gesetzt:
- Lies `./academic_context.md` aus dem Projekt-Ordner; extrahiere die `Gliederung`
- Berechne pro Paper die zugeordneten Kapitel (Keyword-Match zwischen `title`/`abstract` und Kapitelüberschriften)

### Schritt 3: xlsx-Skill aktivieren

Der vendorierte `xlsx`-Skill liegt unter `${CLAUDE_PLUGIN_ROOT}/skills/xlsx/SKILL.md`. Wende ihn auf die strukturierten Paper-Daten an.

**Input:** Strukturierte Paper-Daten (siehe Schritt 2) plus Sheet-Spezifikation (welche Sheets, welche Spalten, welche Farbcodierung).

**Output:** `$OUTPUT` (Default: `~/.academic-research/sessions/$LATEST/literature.xlsx`).

**Sheet-Spezifikation:**

- **Literaturübersicht**: Spalten `Titel | Autoren | Jahr | Venue | DOI | Gesamt | Relevanz | Aktualität | Qualität | Autorität | Zugang | Cluster`. Farbcodierung je Cluster (Kern = grün, Ergänzung = blau, Hintergrund = grau, Methoden = gelb).
- **Cluster-Analyse**: Aggregatstatistik pro Cluster (Anzahl, Durchschnittsscore, Jahresverteilung) + eingebettetes Balkendiagramm.
- **Kapitel-Zuordnung** (nur bei `--context`): Mapping Kapitel → Papers.
- **Datenblatt**: Alle Rohdatenfelder in flachem Tabellenformat.

### Schritt 4: Ergebnis präsentieren

Ausgabepfad und Zusammenfassung anzeigen (Anzahl Papers, Cluster-Verteilung, Dateigröße).
