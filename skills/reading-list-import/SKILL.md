---
name: reading-list-import
description: >
  Verwende diesen Skill wenn der User eine Leseliste, Bibliographie oder
  Quellenliste (PDF, Markdown, Plaintext) in den Vault importieren möchte.
  Trigger-Phrasen: "Importiere Reading List", "Prof-Liste einlesen",
  "Bibliographie importieren", "Literaturliste einlesen",
  "Literaturliste importieren", "Quellenliste",
  "Reading List importieren".
  Parst Referenzen via LLM (Sonnet), resolvet DOI/ISBN ("Auflösung / Resolution"
  via Crossref + DNB) und schreibt in den Vault (vault.add_paper).
  Optional: anystyle (Ruby) als Backend.
triggers:
  - "Importiere Reading List"
  - "Reading List importieren"
  - "Prof-Liste einlesen"
  - "Bibliographie importieren"
  - "Literaturliste einlesen"
  - "Quellenliste importieren"
  - "Leseliste einlesen"
tools:
  - Bash
  - Read
security:
  - api_key_source: "~/.academic-research/config.yaml (0600)"
  - network_allowlist:
      - "api.crossref.org"
      - "services.dnb.de"
      - "openlibrary.org"
      - "www.googleapis.com"
---

# Reading-List-Import Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Zweck

Importiert eine Referenzliste (Literaturliste, Reading List, Bibliographie)
eines Professors oder aus einem Paper in den academic-research Vault.
Unterstützt PDF, Markdown und Plaintext. Dedupliziert via DOI/ISBN.

## Voraussetzungen

### 1. Abhängigkeiten

```bash
pip install anthropic requests lxml
# Optional für PDF:
pip install pypdf
# Optional: anystyle (Ruby-Gem) für strukturiertes Parsen
gem install anystyle-cli
```

### 2. Anthropic API-Key

```yaml
# ~/.academic-research/config.yaml (chmod 0600)
anthropic_api_key: "sk-ant-..."
```

### 3. Vault-Datenbank vorhanden

Der Vault muss initialisiert sein (z.B. via `vault.init_schema()`).

## Verwendung

### Automatisch (Skill-Trigger)

Claude erkennt folgende Phrasen:
- "Importiere Reading List"
- "Prof-Liste einlesen"
- "Bibliographie importieren"
- "Literaturliste einlesen"

### Manuell

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/reading-list-import/scripts/parse_list.py \
  --file /Pfad/zur/Literaturliste.pdf \
  --db ~/.academic-research/projects/meine-arbeit/vault.db
```

### Unterstützte Formate

- `.pdf` — Text wird via pypdf oder pdfminer.six extrahiert
- `.md` / `.markdown` — direkt eingelesen
- `.txt` — direkt eingelesen

Erwartete Inhalts-Formate: APA, BibTeX-Snippets, Plain-Stil.
Detaillierte Format-Hinweise: `${CLAUDE_PLUGIN_ROOT}/skills/reading-list-import/references/format-hints.md`

## Pipeline

```
Datei-Eingabe
    ↓
Text-Extraktion (pypdf für PDF, direkt für md/txt)
    ↓
LLM-Parser (Sonnet): Text → [{author, title, year, doi, isbn, ...}]
    ↓  (optional: anystyle-Fallback)
DOI-Resolution: Crossref-API → CSL-JSON
    ↓
ISBN-Resolution: DNB SRU + OpenLibrary + GoogleBooks → CSL-JSON
    ↓
Fallback: minimales CSL-JSON aus geparsten Daten
    ↓
Vault.add_paper() für jeden Eintrag (Dedup via DOI/ISBN)
    ↓
Ergebnis: N importiert, M übersprungen, Fehler
```

### Anystyle (optional)

Falls `anystyle` installiert ist, dient es als vorgelagerter Parser.
Claude prüft die Verfügbarkeit automatisch:

```bash
# Prüfe ob anystyle verfügbar
anystyle --version 2>/dev/null && echo "verfügbar" || echo "nicht installiert"
```

Bei Verfügbarkeit parst anystyle initial; der LLM-Parser prüft
und vervollständigt das Ergebnis.

## Verhalten

1. Datei-Pfad entgegennehmen (Argument oder via User-Frage)
2. Format erkennen und Text extrahieren
3. LLM-Parser aufrufen (Sonnet) — extrahiert strukturierte Liste
4. Für jeden Eintrag: DOI/ISBN resolven → CSL-JSON
5. `vault.add_paper()` aufrufen (idempotent: Dedup via DOI/ISBN)
6. Bei Mehrdeutigkeit (_ambiguous: true): AskUserQuestion-Tool nutzen
7. Ergebnis melden: N importiert, M übersprungen

## Mehrdeutigkeiten

Wenn der LLM-Parser mehrere mögliche Quellen für einen Eintrag findet
(z.B. gleichnamige Arbeiten verschiedener Autoren), wird der User via
`AskUserQuestion` gefragt:

```
Mehrdeutiger Eintrag: "Language Models" von Radford, A.
Welche Quelle ist gemeint?
  [0] Language Models are Few-Shot Learners (DOI: 10.48550/arXiv.2005.14165)
  [1] Language Models are Unsupervised Multitask Learners (DOI: kein DOI)
Auswahl (Nummer):
```

## Sicherheitshinweise

- **Read-only Netz**: Nur lesende API-Zugriffe (Crossref, DNB, OpenLibrary)
- **Kein Schreiben in externe Systeme**: Nur Vault lokal
- **Credentials**: Anthropic-Key nur aus `~/.academic-research/config.yaml` (0600)
- **Keine PDFs heruntergeladen**: Nur Metadaten werden im Vault gespeichert

## Bekannte Einschränkungen

- Einträge ohne DOI und ISBN können nicht dedupliziert werden;
  sie werden bei erneutem Import neu angelegt
- PDF-Extraktion erfordert pypdf oder pdfminer.six
- Scan-PDFs (keine Textschicht) können nicht verarbeitet werden;
  OCR muss vorgelagert werden
- anystyle erfordert Ruby-Umgebung (optional, kein Pflicht-Dep)
- Netz-Ausfälle führen zu Fallback auf LLM-generiertes CSL-JSON
