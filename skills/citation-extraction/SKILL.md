---
name: citation-extraction
description: Use this skill when the user needs to extract or format citations. Triggers on "Literaturverzeichnis erstellen / prüfen / generieren", "Zitate finden", "Bibliographie formatieren", "Zitation prüfen / pruefen", "citation extraction", "bibliography generation", or when raw PDFs need citation rendering (not chapter body writing — for that → `chapter-writer`). Extrahiert Zitate aus PDFs und liefert formatierte Bibliographien im Zitationsstil aus `./academic_context.md`.
compatibility: Claude API mit documents[] und citations.enabled
license: MIT
---

# Zitat-Extraktion

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Übersicht

Extrahiert und formatiert Zitate aus PDFs und Volltexten. Liefert
Literaturverzeichnisse im Zitationsstil aus `./academic_context.md`
(APA7, IEEE, Harvard etc.). Nutzt die Claude-API `documents[] + citations.enabled`.

## Abgrenzung

Extrahiert und formatiert wörtliche Zitate aus PDFs für einzelne Belege.
Für Kapitel-Prosa, die Belege in Argumentation einbaut → `chapter-writer`
(ruft `citation-extraction` bei Bedarf auf).

**BibTeX-Abgrenzung:** „BibTeX aus Vault" / „komplette Bibliographie als .bib"
→ `latex-export --bib`, nicht hierher (Details → `references/output-formats.md`).

## Variant-Selector

Lies `./academic_context.md`, Feld `Zitationsstil`. Lade die entsprechende Variant-Datei:

| Zitationsstil | Referenz-Datei |
|---------------|----------------|
| APA7 (Default) | `references/apa.md` |
| Harvard | `references/harvard.md` |
| Chicago | `references/chicago.md` |
| DIN 1505-2 | `references/din1505.md` |
| MLA | `references/mla.md` |
| Vancouver | `references/vancouver.md` |
| Springer Author-Date | `references/springer-author-date.md` |

Ist `Zitationsstil` leer → `apa.md`. Unbekannt → Rueckfrage. Lies `${CLAUDE_PLUGIN_ROOT}/skills/citation-extraction/references/<variant>.md`.

**Typ-basierte Erweiterung:** Je nach Quellen-`type` zusaetzliche Referenz laden;
deren Regeln haben Vorrang vor den generischen Artikel-Regeln.

| Quellen-Typ | Zusaetzliche Referenz |
|-------------|----------------------|
| `type: chapter` | `references/book-chapter-de.md` |
| `type: book` | `references/din1505.md` (Monografie-Sektion) |
| `type: article-journal` | (keine Zusatz-Referenz) |

## Citations-API

Liegen Quellen-PDFs im Session-Kontext, nutze den `documents`-Parameter der Claude-API statt Prompt-basierter Zitation. Vorteil: Zitate sind seitengenau, die API erzwingt die Quellenbindung.

**Wann verwenden:** mindestens 1 PDF im Session-Pfad und Zitierstil-Konversion
aus echtem Quelltext (nicht aus Metadaten).

**Wann nicht:** reiner Metadaten-zu-Zitat-Workflow → Prompt-basierte
Formatierung nach Variant-References.

**Output-Integration:** Seitenangaben aus `citations[].start_page_number` / `end_page_number` → Details in `references/output-formats.md`.

## Kontext-Dateien

- Lesen: `./academic_context.md` (Zitationsstil)
- Vault-Queries: `vault.find_quotes(paper_id, query)` für Zitate,
  `vault.get_quote(quote_id)` für Volldetails
- `./literature_state.md` nur lesen (read-only Snapshot-Export aus dem Vault —
  für manuellen Überblick; nicht schreiben)

## Core-Workflow

### 1. Extraktions-Scope bestimmen

Kläre, was der User braucht:

- **Vollextraktion** — Alle in der Session heruntergeladenen PDFs verarbeiten
- **Kapitelbezogen** — Zitate für ein bestimmtes Kapitel extrahieren
- **Quellenbezogen** — Aus einem oder mehreren bestimmten Papern extrahieren
- **Themenbezogen** — Zitate zu einem Konzept über alle Quellen hinweg suchen

### 2. Relevante Paper aus Vault laden

Rufe `vault.search(query, k=5)` auf, um die relevantesten Paper-IDs zur
Recherche-Query zu ermitteln. Für jeden paper_id:

1. `vault.find_quotes(paper_id, query=research_query, k=10)` aufrufen →
   liefert `[{quote_id, verbatim, pdf_page, section, ...}]`
2. Für detaillierte Zitat-Metadaten: `vault.get_quote(quote_id)`

Sind für ein Paper noch keine Vault-Zitate vorhanden (leere Liste), den
`quote-extractor`-Agent spawnen, um Zitate aus dem PDF zu ziehen und via
`vault.add_quote()` zu persistieren. PDFs werden via `vault.ensure_file(paper_id)`
als `file_id` übergeben — kein direktes `pdf_path` im Context.

### 3. Zitat-Extraktion

Wenn Vault-Zitate für ein Paper vorhanden sind, diese direkt verwenden — kein
Agent-Spawn nötig.

Fehlen Vault-Zitate, den Agent `quote-extractor` spawnen (definiert in
`${CLAUDE_PLUGIN_ROOT}/agents/quote-extractor.md`). Übergebe:

```json
{
  "paper": {
    "paper_id": "mueller2023",
    "title": "Paper Title",
    "doi": "10.xxxx/xxxxx"
  },
  "research_query": "derived from chapter title or user query",
  "max_quotes": 3,
  "max_words_per_quote": 25
}
```

Der Agent holt das PDF via `vault.ensure_file(paper_id)`, persistiert die
Zitate automatisch via `vault.add_quote()` und gibt `vault_quote_id` zurück.

Bei kapitelbezogener Extraktion den `research_query` aus Kapiteltitel und
Schlüsselkonzepten der Gliederung ableiten. Die Gliederungs-Struktur aus
`./academic_context.md` nutzen, um Paper zu Kapiteln zu matchen.

### 4. Qualitätsprüfung

Nach der Extraktion die Ergebnisse prüfen:

- Zitate mit `extraction_quality: "failed"` verwerfen
- Paper mit `possible_pdf_mismatch: true` für manuelles Review flaggen
- Prüfen, ob Zitate tatsächlich für das Zielkapitel/-thema relevant sind
- Duplikate über Paper hinweg entfernen (gleiche Idee, andere Formulierung)

Extrahierte Zitate dem User gruppiert nach Quelle präsentieren, je mit
Zitattext, Seitenzahl (falls verfügbar), Ursprungs-Abschnitt, Relevanz-Score
sowie Paper-Titel und Autoren.

### 5. Zitat-Formatierung

Formatiere Zitate inline nach dem in `./academic_context.md` konfigurierten Stil. Keine externe Skript-Pipeline — Claude generiert die Formate direkt aus den strukturierten Paper-Daten. Output-Formate → `references/output-formats.md`.

### 6. Kapitelzuordnung

Wenn Zitate für ein bestimmtes Kapitel extrahiert werden:

1. Zitate nach Relevanz für die Unterabschnitte gruppieren
2. Platzierung innerhalb der Kapitelstruktur vorschlagen
3. Unterabschnitte identifizieren, in denen noch stützende Evidenz fehlt
4. Bei Lücken weitere Literatursuche anbieten

### 7. Literaturstatus

Der Vault ist die Quelle der Wahrheit; `./literature_state.md` ist ein
read-only Snapshot — nicht beschreiben. Snapshot regenerieren:
```bash
node scripts/export-literature-state.mjs
```
Zitatanzahlen und Coverage über `vault.stats()` abfragen.

## Lückenerkennung

Während der Extraktion auf diese Muster achten:

- **Kapitel ohne Zitate** — Als literaturbedürftig flaggen
- **Kapitel mit nur einer Quelle** — Als potenziell unzureichend flaggen
- **Fehlende Gegenargumente** — Wenn alle Zitate dieselbe Position stützen, nach Gegenpositionen suchen
- **Veraltete Quellen** — Zitate aus Quellen älter als 10 Jahre flaggen, außer es sind Standardwerke

Bei erkannten Lücken `/search` mit gezielten Queries anbieten oder den Skill `literature-gap-analysis` für ein umfassendes Review triggern.

## Export-Formate

Unterstützte Output-Formate (BibTeX, Markdown, JSON; inline generiert, kein
externes Skript). Details und Ziel-Pfade → `references/output-formats.md`.

## Few-Shot-Beispiele

Gut/Schlecht-Beispiele zur Qualitätskalibrierung (APA7-Zitation,
Bibliography-Vollständigkeit) → `references/citation-examples.md`.

## Wichtige Regeln

- **Nie Zitate fabrizieren** — Nur Text nutzen, der direkt aus PDFs extrahiert wurde
- **Exakten Wortlaut bewahren** — Zitate müssen wörtlich der Quelle entsprechen
- **Seitenzahlen angeben** — Wenn verfügbar, immer Seitenzahlen mitführen
- **Zitationsstil respektieren** — Durchgehend den im akademischen Kontext konfigurierten Stil verwenden
- **Mismatches flaggen** — Stimmt ein PDF-Inhalt nicht mit dem erwarteten Paper überein, das melden
- **User bestätigt Zuordnungen** — Kapitel-Zitat-Zuordnungen vor dem Speichern freigeben lassen
