# Academic Research v4

Modulares akademisches Forschungs-Toolkit für Claude Code. 13 selbstaktivierende Skills, 5D-Scoring mit Cluster-Zuweisung, Excel-Export, Anti-KI-Stil-Erkennung und Multi-Source-Literatursuche.

## Was ist neu in v4?

| Feature | v3 | v4 |
|---------|----|----|
| Architektur | Monolithische 7-Phasen-Pipeline | 13 modulare, selbstaktivierende Skills |
| Scoring | 4 Dimensionen | **5 Dimensionen** (+ Zugang) |
| Cluster | Keine | **4 Cluster** (Kern/Ergänzung/Hintergrund/Methoden) |
| Excel | Nicht vorhanden | **Professionelle Excel** (4 Sheets, Farben, Diagramme) |
| Stil-Prüfung | Nicht vorhanden | **Anti-KI-Detection** (9 Metriken) |
| Zitierformate | Nur BibTeX | **5 Formate** (APA7, IEEE, Harvard, Chicago, BibTeX) |
| Kontext | Nur `config.local.md` | **Claude Memory** (persistent, sessionübergreifend) |
| Auslösung | Nur `/research` Command | **Automatische Aktivierung** durch Konversation |

## Voraussetzungen

- **Python 3.9+** (empfohlen: 3.11+)
- **Claude Code** (CLI, aktuelle Version)
- **Node.js 18+** (für Playwright Browser-Module, optional)

### Python-Pakete

| Paket | Version | Zweck |
|-------|---------|-------|
| `httpx` | ≥0.25.0 | HTTP-Client für API-Suche |
| `PyPDF2` | ≥3.0.0 | PDF-Textextraktion |
| `openpyxl` | ≥3.1.0 | Excel-Generierung |
| `pyyaml` | ≥6.0 | YAML-Konfiguration |

## Installation

### 1. Marketplace hinzufügen & Plugin installieren

Öffne Claude Code in einem beliebigen Projekt und führe folgende Befehle aus:

```
# Marketplace registrieren (einmalig)
/plugin marketplace add jamski105/academic-research

# Plugin installieren
/plugin install academic-research@academic-research
```

Das Plugin wird global installiert und steht in **allen** Projekten zur Verfügung — du musst Claude Code nicht im Plugin-Repo öffnen.

**Update auf neue Versionen:**
```
/plugin update academic-research
```

<details>
<summary>Alternative: Lokale Entwicklung (aus geklontem Repo)</summary>

```bash
cd ~/Repos
git clone https://github.com/jamski105/academic-research.git
```

```bash
# Claude Code mit Plugin-Dir starten (lädt direkt vom Dateisystem)
claude --plugin-dir ~/Repos/academic-research
```

Änderungen im Repo sind sofort wirksam — kein Cache, kein Marketplace nötig.

</details>

### 2. Python-Umgebung einrichten

```
# Automatisch via Setup-Command in Claude Code:
/academic-research:setup
```

Das Setup erstellt die venv, installiert alle Dependencies und verifiziert die Installation.

<details>
<summary>Manuelles Setup</summary>

```bash
mkdir -p ~/.academic-research/{sessions,pdfs}
python3 -m venv ~/.academic-research/venv
~/.academic-research/venv/bin/pip install httpx PyPDF2 openpyxl pyyaml
```

</details>

### 3. Playwright installieren (optional, für Browser-Module)

```bash
npx playwright install chromium --with-deps
```

Ohne Playwright funktionieren alle **API-basierten** Suchquellen (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv). Browser-Module (Google Scholar, Springer, OECD, RePEc, OPAC) erfordern Playwright.

### 4. Permissions konfigurieren

```
/academic-research:setup
```

Das Setup-Command konfiguriert auch die nötigen Permissions automatisch. Alternativ manuell:

```bash
python3 scripts/configure_permissions.py
```

## Quick Start

```
# In Claude Code:

# 1. Akademischen Kontext einrichten (einmalig)
"Ich schreibe eine Bachelorarbeit über IT Lean Governance an der Leibniz FH"
→ Academic Context Skill aktiviert sich automatisch

# 2. Literatur suchen
/academic-research:search "DevOps Governance" --mode standard

# 3. Excel generieren
/academic-research:excel

# 4. Stil prüfen
"Prüfe diesen Text auf KI-Muster"
→ Style Evaluator Skill aktiviert sich automatisch
```

---

## Commands (5 Slash-Commands)

Commands werden explizit per `/academic-research:name` aufgerufen.

### `/academic-research:search`

Literatursuche über 7 APIs parallel, mit optionaler Query-Expansion und Browser-Modulen.

**Syntax:** `/academic-research:search "query" [--mode MODE] [--modules LIST] [--limit N] [--no-expand] [--no-browser]`

| Argument | Default | Beschreibung |
|----------|---------|-------------|
| `query` | (Pflicht) | Suchbegriff |
| `--mode` | `standard` | `quick` (4 APIs), `standard` (7 APIs), `deep` (7 APIs + Browser), `metadata` (ohne PDFs) |
| `--modules` | (aus Mode) | Komma-getrennte Modulliste überschreibt Mode-Auswahl |
| `--limit` | `50` | Max. Ergebnisse pro Modul |
| `--no-expand` | `false` | Query-Generator Agent überspringen, rohe Query nutzen |
| `--no-browser` | `false` | Browser-Module überspringen (nur API) |

**Modi im Detail:**

| Mode | Module | Top-N | PDFs | Beschreibung |
|------|--------|-------|------|-------------|
| `quick` | crossref, openalex, semantic_scholar, arxiv | 15 | Ja | Schnelle Suche |
| `standard` | 7 APIs (+ econbiz, econstor, base) | 25 | Ja | Standard (empfohlen) |
| `deep` | 7 APIs + Browser-Module | 40 | Ja | Systematische Suche |
| `metadata` | 7 APIs | 25 | Nein | Nur Metadaten |

**Pipeline:** Query-Expansion → API-Suche → Browser-Suche → Deduplizierung → 5D-Ranking → LLM-Relevanz → Top-N-Selektion → Ergebnistabelle

**Beispiele:**
```
/academic-research:search "DevOps Governance"
/academic-research:search "Machine Learning" --mode quick
/academic-research:search "IT Compliance" --mode deep
/academic-research:search "Cloud Computing" --modules crossref,semantic_scholar --limit 30
```

### `/academic-research:score`

Re-Scoring und Cluster-Zuweisung auf bereits gefundene Papers.

**Syntax:** `/academic-research:score [papers.json] [--query "..."] [--mode MODE]`

Nutzt die 5D-Scoring-Engine (siehe unten) und weist Cluster zu. Kann auf die letzte Session oder eine beliebige papers.json angewandt werden.

### `/academic-research:excel`

Professionelle Excel-Datei aus gescorten Papers generieren.

**Syntax:** `/academic-research:excel [--papers papers.json] [--output name.xlsx] [--context]`

Erzeugt 4 Sheets:

1. **Literaturübersicht** — Alle Papers mit 5D-Scores, Cluster-Farbcodierung, Score-Ampel
2. **Cluster-Analyse** — Statistik pro Cluster mit Balkendiagramm
3. **Kapitel-Zuordnung** — Papers zugeordnet zu Gliederungskapiteln (mit `--context`)
4. **Datenblatt** — Verstecktes Rohdaten-Sheet

### `/academic-research:setup`

Richtet die Python-Umgebung ein: venv, Dependencies, Playwright, Permissions. Führt alle Schritte automatisch aus und verifiziert die Installation.

### `/academic-research:history`

Zeigt vergangene Recherche-Sessions aus `~/.academic-research/sessions/`.

**Syntax:** `/academic-research:history [query | date | stats]`

- Ohne Argument: alle Sessions als Tabelle
- Mit Query-Text: Sessions nach Suchbegriff filtern
- Mit Datum: Details einer bestimmten Session
- `stats`: Aggregierte Statistiken

---

## Skills (13 selbstaktivierende)

Skills aktivieren sich **automatisch**, wenn Claude passende Keywords in der Konversation erkennt. Kein manueller Aufruf nötig — einfach natürlich formulieren.

### Kern-Skills

| Skill | Aktiviert bei | Funktion | Ressourcen |
|-------|-------------|----------|------------|
| **Academic Context** | "meine Arbeit", "mein Thema", "Thesis", "Forschungsfrage" | Speichert Thesis-Kontext (Thema, Gliederung, Methodik, Fortschritt) persistent in Claude Memory | — |
| **Advisor** | "Gliederung", "Exposé", "Struktur", "Kapitelplanung" | Interaktive Gliederungs- und Exposé-Erstellung im Dialog | `expose-template.md` |
| **Chapter Writer** | "Kapitel schreiben", "verfassen", "entwerfen", "Textarbeit" | Kapitel-Entwurf mit Literatur, Zitaten und Kontext aus der Gliederung | — |
| **Citation Extraction** | "Zitate finden", "zitieren", "Literaturverzeichnis" | Zitat-Extraktion aus PDFs, Formatierung in APA7/IEEE/Harvard/Chicago/BibTeX | `citation-styles.md` |

### Qualitäts-Skills

| Skill | Aktiviert bei | Funktion | Ressourcen |
|-------|-------------|----------|------------|
| **Style Evaluator** | "Text prüfen", "Stil-Check", "KI-Erkennung", "menschlich klingen" | 9-Metriken Textanalyse + Anti-AI-Detection mit Verbesserungsvorschlägen | `scoring-rubric.md` |
| **Plagiarism Check** | "Plagiat prüfen", "Textähnlichkeit", "zu nah am Original" | Quellen-Nähe-Erkennung, Paraphrase-Check gegen Originaltexte | — |
| **Submission Checker** | "formale Prüfung", "abgabefertig", "Formatierung prüfen" | Formale Anforderungen validieren (Leibniz FH spezifisch: Deckblatt, Ränder, Erklärung) | `leibniz-fh-requirements.md` |
| **Source Quality Audit** | "Quellenqualität", "Quellen-Check", "peer-reviewed Anteil" | Quellenbalance-Analyse: Peer-Review-%, Alter, Diversität, Empfehlungen | — |

### Planungs-Skills

| Skill | Aktiviert bei | Funktion | Ressourcen |
|-------|-------------|----------|------------|
| **Literature Gap Analysis** | "Literaturlücken", "fehlende Quellen", "Abdeckung prüfen" | Per-Kapitel Abdeckungsbericht: welche Kapitel brauchen mehr Literatur | — |
| **Methodology Advisor** | "Methodik", "Forschungsdesign", "qualitativ vs quantitativ" | Methodenwahl mit Vergleich, Begründungshilfe und Dokumentation | `methodology-catalog.md` |
| **Research Question Refiner** | "Forschungsfrage formulieren", "Fragestellung präzisieren" | Forschungsfrage schärfen: zu breit/eng/unbeantwortbar erkennen, Teilfragen ableiten | — |

### Finalisierungs-Skills

| Skill | Aktiviert bei | Funktion | Ressourcen |
|-------|-------------|----------|------------|
| **Title Generator** | "Titel suchen", "Titelvorschläge", "Arbeitstitel" | 5–7 Titeloptionen mit Begründung aus fertiger Arbeit generieren | — |
| **Abstract Generator** | "Abstract schreiben", "Zusammenfassung", "Management Summary" | Abstract DE+EN, Keywords, Management Summary aus fertigem Text | — |

---

## Agents (3 LLM-Subagents)

Agents werden von Commands/Skills als Subagents gestartet für Aufgaben, die LLM-Urteilskraft erfordern.

| Agent | Model | Genutzt von | Aufgabe |
|-------|-------|-------------|---------|
| **query-generator** | Haiku | `search` Command | Expandiert eine Suchanfrage in modulspezifische Suchbegriffe |
| **relevance-scorer** | Sonnet | `search` + `score` Commands | Semantische Relevanz-Bewertung (0–1) in 10er-Batches |
| **quote-extractor** | Sonnet | `citation-extraction` Skill | Extrahiert relevante Zitate aus PDF-Volltext |

---

## Scripts (8 Python-Module)

Deterministische Logik ohne LLM-Aufruf, ausgeführt im isolierten venv (`~/.academic-research/venv/`).

| Script | Funktion |
|--------|----------|
| `search.py` | API-Aufrufe an 7 Quellen parallel (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv) |
| `ranking.py` | 5D-Scoring-Berechnung + Cluster-Zuweisung nach konfigurierbaren Schwellwerten |
| `dedup.py` | Deduplizierung nach DOI-Match + Titel-Ähnlichkeit (Levenshtein) |
| `pdf.py` | PDF-Download + Textextraktion (PyPDF2) |
| `citations.py` | Zitationsformatierung in 5 Stilen (APA7, IEEE, Harvard, Chicago, BibTeX) |
| `excel.py` | Excel-Generierung mit 4 Sheets, Farbcodierung, Diagrammen (openpyxl) |
| `style_analysis.py` | 9-Metriken Textanalyse für Anti-KI-Detection |
| `text_utils.py` | Shared Text-Utilities (Normalisierung, Tokenisierung) |

---

## 5D Scoring System

Jedes Paper wird nach 5 Dimensionen bewertet:

| Dimension | Gewicht | Berechnung |
|-----------|---------|------------|
| **Relevanz** | 35% | Keyword-Match in Titel (70%) + Abstract (30%) + Phrasen-Bonus |
| **Aktualität** | 20% | Exponentieller Verfall, 5-Jahre Halbwertzeit |
| **Qualität** | 15% | Zitationen/Jahr mit Log-Skalierung |
| **Autorität** | 15% | Venue-Reputation (IEEE=1.0, Mid=0.7, Other=0.4) |
| **Zugang** | 15% | Open Access=1.0, Institutional=0.8, DOI=0.6, URL=0.2 |

### Cluster-Zuweisung

| Cluster | Kriterien | Beschreibung |
|---------|-----------|-------------|
| 🟢 **Kernliteratur** | Score ≥ 0.75, Relevanz ≥ 0.80 | Muss zitiert werden |
| 🔵 **Ergänzungsliteratur** | Score ≥ 0.50, Relevanz ≥ 0.50 | Unterstützend, Vertiefung |
| ⚪ **Hintergrundliteratur** | Score ≥ 0.30 | Grundlagen, Standards |
| 🟡 **Methodenliteratur** | Methodik-Keywords erkannt | Methodik-Begründung |

---

## Suchquellen (14)

### API-Module (automatisch, parallel)

| Modul | Quelle | Disziplin |
|-------|--------|-----------|
| CrossRef | DOI-Registry | Alle |
| OpenAlex | OpenAlex Katalog | Alle |
| Semantic Scholar | Semantic Scholar | Alle |
| BASE | Bielefeld Academic Search | Alle |
| EconBiz | ZBW Suchportal | Wirtschaft |
| EconStor | OA Wirtschafts-Repo | Wirtschaft |
| arXiv | arXiv Preprints | CS, ML, Physik, Mathe |

### Browser-Module (Playwright MCP)

| Modul | Quelle | Auth |
|-------|--------|------|
| Google Scholar | Google | Keine |
| Springer | Springer Nature | HAN optional |
| OECD | OECD.org | Keine |
| RePEc | IDEAS/RePEc | Keine |
| OPAC | Leibniz FH Bibliothek | Login |
| EBSCO | EBSCO Publication Finder | HAN |
| ProQuest | ProQuest Dissertationen | HAN |

---

## Konfiguration

| Datei | Zweck |
|-------|-------|
| `config/scoring.yaml` | 5D-Gewichtungen und Cluster-Schwellwerte (anpassbar) |
| `config/browser_guides/*.md` | Playwright-Navigationsanleitungen pro Datenbank (Scholar, Springer, OECD, ...) |

## Memory-System

Der akademische Kontext wird in Claude Memory gespeichert und überlebt Sessions:

| Datei | Inhalt |
|-------|--------|
| `academic_context.md` | Thesis-Profil, Gliederung, Forschungsfrage, Fortschritt |
| `literature_state.md` | Literatur-Statistik, Kapitelzuordnung, Lücken |
| `writing_state.md` | Aktuelles Kapitel, Wortzahl, Style-Scores |

## Verzeichnisstruktur

```
academic-research/
├── .claude-plugin/plugin.json       # Plugin-Manifest v4.0.0
├── skills/                          # 13 selbstaktivierende Skills
│   ├── academic-context/SKILL.md
│   ├── advisor/SKILL.md + expose-template.md
│   ├── chapter-writer/SKILL.md
│   ├── style-evaluator/SKILL.md + scoring-rubric.md
│   ├── citation-extraction/SKILL.md + citation-styles.md
│   ├── submission-checker/SKILL.md + leibniz-fh-requirements.md
│   ├── methodology-advisor/SKILL.md + methodology-catalog.md
│   ├── ...                          # (6 weitere Skills)
├── commands/                        # 5 Slash-Commands
├── agents/                          # 3 LLM-Agents
├── scripts/                         # 8 Python-Module
│   ├── search.py, ranking.py, dedup.py, pdf.py
│   ├── citations.py, excel.py, style_analysis.py, text_utils.py
├── config/                          # YAML-Konfiguration + Browser-Guides
├── hooks/                           # SessionStart-Hook (venv-Check)
└── tests/                           # Unit-Tests
```

## Entwicklung

### Tests ausführen

```bash
~/.academic-research/venv/bin/pip install pytest
~/.academic-research/venv/bin/python -m pytest tests/ -v
```

### Scoring anpassen

Bearbeite `config/scoring.yaml` — Gewichtungen und Cluster-Schwellwerte sind dort konfigurierbar.

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Python venv not found" | `/academic-research:setup` ausführen |
| "Missing dependencies" | `~/.academic-research/venv/bin/pip install -r scripts/requirements.txt` |
| Browser-Module funktionieren nicht | `npx playwright install chromium --with-deps` |
| Keine Ergebnisse bei Suche | Breitere Query verwenden, `--mode quick` testen |
| Excel leer | Zuerst `/academic-research:search` ausführen |
| Semantic Scholar 429 | SS_API_KEY Umgebungsvariable setzen |

## Lizenz

MIT
