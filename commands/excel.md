---
description: Generate or update a literature Excel spreadsheet via the document-skills:xlsx skill
disable-model-invocation: true
allowed-tools: Read, Write
argument-hint: [--papers papers.json] [--output literature.xlsx] [--context]
---

# Literatur-Excel-Generator

Erstellt ein formatiertes Excel-Workbook aus gescorten Papers. Die eigentliche Excel-Generierung übernimmt der extern installierte `document-skills:xlsx`-Skill (siehe README-Prerequisites).

## Verwendung

- `/academic-research:excel` — Aus letzter Session generieren
- `/academic-research:excel --papers papers.json --output my_literature.xlsx`
- `/academic-research:excel --context` — Kapitel-Zuordnung aus akademischem Kontext mitnehmen

## Voraussetzung

`document-skills:xlsx` muss installiert sein:

```
/plugin install document-skills@anthropic-agent-skills
```

Wenn nicht installiert: SessionStart-Hook warnt beim Start; dieser Command bricht klar ab, wenn der Skill beim Aufruf fehlt.

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

### Schritt 2: Verfügbarkeit des xlsx-Skills prüfen

```bash
if [ ! -d "$HOME/.claude/plugins/cache/anthropic-agent-skills/document-skills" ]; then
  echo "❌ document-skills:xlsx nicht installiert."
  echo "   Install: /plugin install document-skills@anthropic-agent-skills"
  exit 1
fi
```

### Schritt 3: Input strukturieren

Lies die Paper-Daten aus `$PAPERS` (JSON-Array mit Feldern `title`, `authors`, `year`, `doi`, `total_score`, `cluster`, `relevance_score`, `recency_score`, `quality_score`, `authority_score`, `access_score`, `venue`, `source_module`).

Wenn `--context` gesetzt:
- Lies `academic_context.md` aus Memory; extrahiere die `Gliederung`
- Berechne pro Paper die zugeordneten Kapitel (Keyword-Match zwischen `title`/`abstract` und Kapitelüberschriften)

### Schritt 4: xlsx-Skill aktivieren

Rufe den `document-skills:xlsx`-Skill mit klarer Input/Output-Spezifikation auf:

**Input:** Strukturierte Paper-Daten (siehe Schritt 3) plus Sheet-Spezifikation (welche Sheets, welche Spalten, welche Farbcodierung).

**Output:** `$OUTPUT` (Default: `~/.academic-research/sessions/$LATEST/literature.xlsx`).

**Sheet-Spezifikation:**

- **Literaturübersicht**: Spalten `Titel | Autoren | Jahr | Venue | DOI | Gesamt | Relevanz | Aktualität | Qualität | Autorität | Zugang | Cluster`. Farbcodierung je Cluster (Kern = grün, Ergänzung = blau, Hintergrund = grau, Methoden = gelb).
- **Cluster-Analyse**: Aggregatstatistik pro Cluster (Anzahl, Durchschnittsscore, Jahresverteilung) + eingebettetes Balkendiagramm.
- **Kapitel-Zuordnung** (nur bei `--context`): Mapping Kapitel → Papers.
- **Datenblatt**: Alle Rohdatenfelder in flachem Tabellenformat.

### Schritt 5: Ergebnis präsentieren

Ausgabepfad und Zusammenfassung anzeigen (Anzahl Papers, Cluster-Verteilung, Dateigröße).
