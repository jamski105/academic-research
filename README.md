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

### 1. Plugin installieren

```bash
# Als lokales Plugin (Entwicklung)
cd ~/Repos
git clone https://github.com/jamski105/academic-research.git
# In Claude Code: Plugin über Verzeichnis laden

# Oder via Marketplace (wenn verfügbar)
```

### 2. Python-Umgebung einrichten

```bash
# Automatisch via Setup-Command in Claude Code:
/academic-research:setup

# Oder manuell:
mkdir -p ~/.academic-research/{sessions,pdfs}
python3 -m venv ~/.academic-research/venv
~/.academic-research/venv/bin/pip install -r scripts/requirements.txt
```

### 3. Playwright installieren (optional, für Browser-Module)

```bash
npx playwright install chromium --with-deps
```

Ohne Playwright funktionieren alle **API-basierten** Suchquellen (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv). Browser-Module (Google Scholar, Springer, OECD, RePEc, OPAC) erfordern Playwright.

### 4. Permissions konfigurieren

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

## Skills (13 selbstaktivierende)

Skills aktivieren sich **automatisch** wenn Claude den passenden Kontext erkennt. Kein manueller Aufruf nötig.

### Kern-Skills

| Skill | Aktiviert bei | Funktion |
|-------|-------------|----------|
| **Academic Context** | "meine Arbeit", "mein Thema", "Thesis" | Verwaltet Thesis-Kontext in Claude Memory |
| **Advisor** | "Gliederung", "Exposé", "Struktur" | Interaktive Gliederungs- und Exposé-Erstellung |
| **Chapter Writer** | "Kapitel schreiben", "verfassen" | Kapitel-Entwurf mit Zitaten und Kontext |
| **Citation Extraction** | "Zitate finden", "zitieren" | Zitat-Extraktion aus PDFs (APA7, IEEE, Harvard, Chicago) |

### Qualitäts-Skills

| Skill | Aktiviert bei | Funktion |
|-------|-------------|----------|
| **Style Evaluator** | "Text prüfen", "Stil-Check", "KI-Erkennung" | 9-Metriken Textanalyse + Anti-AI-Detection |
| **Plagiarism Check** | "Plagiat prüfen", "Textähnlichkeit" | Quellen-Nähe-Erkennung |
| **Submission Checker** | "formale Prüfung", "abgabefertig" | Formale Anforderungen (Leibniz FH spezifisch) |
| **Source Quality Audit** | "Quellenqualität", "Quellen-Check" | Quellenbalance-Analyse (Peer-Review %, Alter, Diversität) |

### Planungs-Skills

| Skill | Aktiviert bei | Funktion |
|-------|-------------|----------|
| **Literature Gap Analysis** | "Literaturlücken", "fehlende Quellen" | Per-Kapitel Abdeckungsbericht |
| **Methodology Advisor** | "Methodik", "Forschungsdesign" | Methodenwahl und -begründung |
| **Research Question Refiner** | "Forschungsfrage formulieren" | Forschungsfrage präzisieren |

### Finalisierungs-Skills

| Skill | Aktiviert bei | Funktion |
|-------|-------------|----------|
| **Title Generator** | "Titel suchen", "Titelvorschläge" | Titeloptionen aus fertiger Arbeit |
| **Abstract Generator** | "Abstract schreiben", "Zusammenfassung" | Abstract DE+EN, Keywords, Management Summary |

## Commands (3 Slash-Commands)

| Command | Beschreibung |
|---------|-------------|
| `/academic-research:search "query"` | Literatursuche über 7 APIs (+ Browser optional) |
| `/academic-research:score` | 5D-Scoring + Cluster-Zuweisung |
| `/academic-research:excel` | Professionelle Literatur-Excel generieren |

### Search-Optionen

```
/academic-research:search "DevOps Governance" --mode standard
/academic-research:search "Machine Learning" --mode quick --limit 30
/academic-research:search "IT Compliance" --mode deep
```

| Mode | Module | Top-N | PDFs | Beschreibung |
|------|--------|-------|------|-------------|
| `quick` | 4 APIs | 15 | Ja | Schnelle Suche |
| `standard` | 7 APIs | 25 | Ja | Standard (empfohlen) |
| `deep` | 7 APIs + Browser | 40 | Ja | Systematische Suche |
| `metadata` | 7 APIs | 25 | Nein | Nur Metadaten |

## 5D Scoring System

Jedes Paper wird nach 5 Dimensionen bewertet:

| Dimension | Gewicht | Berechnung |
|-----------|---------|------------|
| **Relevanz** | 35% | Keyword-Match in Titel (70%) + Abstract (30%) |
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

## Excel-Format

Die generierte Excel hat 4 Sheets:

1. **Literaturübersicht** — Alle Papers mit 5D-Scores, Cluster-Farbcodierung, Score-Ampel
2. **Cluster-Analyse** — Statistik pro Cluster mit Balkendiagramm
3. **Kapitel-Zuordnung** — Papers zugeordnet zu Gliederungskapiteln
4. **Datenblatt** — Verstecktes Rohdaten-Sheet

## Memory-System

Der akademische Kontext wird in Claude Memory gespeichert und überlebt Sessions:

| Datei | Inhalt |
|-------|--------|
| `academic_context.md` | Thesis-Profil, Gliederung, Forschungsfrage, Fortschritt |
| `literature_state.md` | Literatur-Statistik, Kapitelzuordnung, Lücken |
| `writing_state.md` | Aktuelles Kapitel, Wortzahl, Style-Scores |

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

## Konfiguration

### `config/scoring.yaml`
5D-Gewichtungen und Cluster-Schwellwerte. Anpassbar.

### `config/search_modules.yaml`
Suchquellen-Registry: welche Module existieren, welcher Tier, welche Disziplin.

### `config/research_modes.yaml`
Mode-Definitionen: quick/standard/deep/metadata mit Modul-Listen und Limits.

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
│   ├── ...                          # (8 weitere Skills)
├── commands/                        # 3 Slash-Commands + setup + history
├── agents/                          # 4 LLM-Agents
├── scripts/                         # 8 Python-Module
│   ├── search.py, ranking.py, dedup.py, pdf.py
│   ├── citations.py, excel.py, style_analysis.py, text_utils.py
├── config/                          # YAML-Konfiguration + Browser-Guides
├── tests/                           # 54 Tests
└── docs/                            # Architektur + Setup-Guide
```

## Entwicklung

### Tests ausführen

```bash
~/.academic-research/venv/bin/pip install pytest
~/.academic-research/venv/bin/python -m pytest tests/ -v
```

### Neues Suchmodul hinzufügen

Siehe [docs/adding-browser-modules.md](docs/adding-browser-modules.md).

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
