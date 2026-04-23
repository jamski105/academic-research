---
name: Citation Extraction
description: Dieser Skill wird genutzt, wenn der User Zitate und Quellenangaben aus akademischen PDFs extrahieren, formatieren oder verwalten möchte. Triggers on "Zitate finden", "zitieren", "Quellenarbeit", "Belege suchen", "citations", "Zitate extrahieren", "quote extraction", "Literaturverzeichnis", "bibliography", oder wenn ein anderer Skill feststellt, dass Zitatdaten für ein Kapitel gebraucht werden.
---

# Zitat-Extraktion

Extrahiert relevante Zitate aus akademischen PDFs, formatiert sie im gewünschten Stil und organisiert Zitatdaten nach Kapitel. Nutzt den Agent `quote-extractor` für die Extraktion und die Inline-Zitationslogik (siehe Abschnitt "Zitat-Formatierung" unten).

## Aktivierung dieses Skills

- Der User möchte Zitate oder Belege aus heruntergeladenen PDFs extrahieren
- Der User braucht eine Bibliografie oder ein Literaturverzeichnis
- Der User sucht Belege für eine konkrete Aussage oder ein bestimmtes Kapitel
- Der User möchte Zitate nach Kapitel oder Thema ordnen

## Memory-Dateien

### Lesen

- `academic_context.md` — Gliederungsstruktur, Zitationsstil, Forschungsfrage
- `literature_state.md` — Verfügbare Quellen, PDF-Download-Status, Kapitelzuordnungen

### Schreiben

- `literature_state.md` — Zitatanzahl und Extraktionsstatus pro Quelle aktualisieren

## Voraussetzungen

Existiert `academic_context.md` nicht, informiere den User und triggere zuerst den Academic-Context-Skill. Der Zitationsstil muss vor der Formatierung bekannt sein.

## Core-Workflow

### 1. Extraktions-Scope bestimmen

Kläre, was der User braucht:

- **Vollextraktion** — Alle in der Session heruntergeladenen PDFs verarbeiten
- **Kapitelbezogen** — Zitate für ein bestimmtes Kapitel extrahieren
- **Quellenbezogen** — Aus einem oder mehreren bestimmten Papern extrahieren
- **Themenbezogen** — Zitate zu einem Konzept über alle Quellen hinweg suchen

### 2. PDFs lokalisieren

Lies `literature_state.md`, um zu ermitteln, welche Paper ein heruntergeladenes PDF haben. PDFs liegen unter `~/.academic-research/sessions/*/pdfs/`.

Verweist der User auf Paper ohne PDFs, biete an, `/search` zu triggern, um sie zu finden und herunterzuladen.

### 3. Zitat-Extraktion

Für jedes PDF den Agent `quote-extractor` spawnen (definiert in `${CLAUDE_PLUGIN_ROOT}/agents/quote-extractor.md`). Übergebe:

```json
{
  "paper": {
    "title": "Paper Title",
    "doi": "10.xxxx/xxxxx",
    "pdf_text": "...extracted PDF text..."
  },
  "research_query": "derived from chapter title or user query",
  "max_quotes": 3,
  "max_words_per_quote": 25
}
```

Bei kapitelbezogener Extraktion den `research_query` aus Kapiteltitel und Schlüsselkonzepten der Gliederung ableiten. Die Gliederungs-Struktur aus `academic_context.md` nutzen, um Paper zu Kapiteln zu matchen.

### 4. Qualitätsprüfung

Nach der Extraktion die Ergebnisse prüfen:

- Zitate mit `extraction_quality: "failed"` verwerfen
- Paper mit `possible_pdf_mismatch: true` für manuelles Review flaggen
- Prüfen, ob Zitate tatsächlich für das Zielkapitel/-thema relevant sind
- Duplikate über Paper hinweg entfernen (gleiche Idee, andere Formulierung)

Extrahierte Zitate dem User gruppiert nach Quelle präsentieren, mit:

- Zitattext
- Seitenzahl (falls verfügbar)
- Ursprungs-Abschnitt
- Relevanz-Score
- Paper-Titel und Autoren

### 5. Zitat-Formatierung

Formatiere Zitate inline nach dem in `academic_context.md` konfigurierten Stil. Keine externe Skript-Pipeline — Claude generiert die Formate direkt aus den strukturierten Paper-Daten.

#### Unterstützte Stile

| Stil | In-Text-Beispiel | Bibliografie-Beispiel |
|------|-------------------|-----------------------|
| APA7 | (Müller, 2023, S. 45) | Müller, H. (2023). *Title*. Journal, 12(3), 44-67. |
| IEEE | [1, p. 45] | [1] H. Müller, "Title," *Journal*, vol. 12, no. 3, pp. 44-67, 2023. |
| Harvard | (Müller 2023, p. 45) | Müller, H. 2023, 'Title', *Journal*, vol. 12, no. 3, pp. 44-67. |
| Chicago | (Müller 2023, 45) | Müller, H. 2023. "Title." *Journal* 12 (3): 44-67. |
| BibTeX | `\cite{mueller2023}` | `@article{mueller2023, author={Müller, H.}, title={Title}, ...}` |

#### Output-Formate

Claude erzeugt bei Bedarf:
- **In-text-Zitat** — exakt im konfigurierten Stil mit Seitenzahl
- **Literaturverzeichnis-Eintrag** — formatiert pro Quelle
- **BibTeX-Datei** — für LaTeX-Integration (in `~/.academic-research/citations.bib` persistieren)
- **Markdown-Bibliografie** — für Review, sortiert nach Autor/Jahr
- **JSON** — wenn andere Skills die Daten strukturiert brauchen

### 6. Kapitelzuordnung

Wenn Zitate für ein bestimmtes Kapitel extrahiert werden:

1. Zitate nach Relevanz für die Unterabschnitte gruppieren
2. Platzierung innerhalb der Kapitelstruktur vorschlagen
3. Unterabschnitte identifizieren, in denen noch stützende Evidenz fehlt
4. Bei Lücken weitere Literatursuche anbieten

### 7. Literaturstatus aktualisieren

Nach Extraktion und Formatierung:

1. `literature_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Pro-Quelle-Felder aktualisieren: Zitatanzahl, Extraktionsqualität, zugewiesene Kapitel
3. Aggregierte Statistiken aktualisieren: extrahierte Zitate gesamt, Coverage-Prozentsatz

## Lückenerkennung

Während der Extraktion auf diese Muster achten:

- **Kapitel ohne Zitate** — Als literaturbedürftig flaggen
- **Kapitel mit nur einer Quelle** — Als potenziell unzureichend flaggen
- **Fehlende Gegenargumente** — Wenn alle Zitate dieselbe Position stützen, nach Gegenpositionen suchen
- **Veraltete Quellen** — Zitate aus Quellen älter als 10 Jahre flaggen, außer es sind Standardwerke

Bei erkannten Lücken `/search` mit gezielten Queries anbieten oder den Skill "Literature Gap Analysis" für ein umfassendes Review triggern.

## Export-Formate

Diese Output-Formate werden unterstützt (inline generiert, kein externes Skript):

- **BibTeX** — für LaTeX-Integration
- **Markdown** — für Review und manuelles Editieren
- **JSON** — für die programmatische Nutzung durch andere Skills

## Wichtige Regeln

- **Nie Zitate fabrizieren** — Nur Text nutzen, der direkt aus PDFs extrahiert wurde
- **Exakten Wortlaut bewahren** — Zitate müssen wörtlich der Quelle entsprechen
- **Seitenzahlen angeben** — Wenn verfügbar, immer Seitenzahlen mitführen
- **Zitationsstil respektieren** — Durchgehend den im akademischen Kontext konfigurierten Stil verwenden
- **Mismatches flaggen** — Stimmt ein PDF-Inhalt nicht mit dem erwarteten Paper überein, das melden
- **User bestätigt Zuordnungen** — Kapitel-Zitat-Zuordnungen vor dem Speichern freigeben lassen
