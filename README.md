# Academic Research v5

Modulares akademisches Forschungs-Toolkit für Claude Code. 13 selbstaktivierende Skills, 5D-Scoring mit Cluster-Zuweisung, Excel-Export, Anti-KI-Stil-Erkennung und Multi-Source-Literatursuche.

## Halozination bei Zitatextraktion

Überprüfe immer alle Zitate von der Zitatextraktion oder vordere Claude auf alles zu überprüfen

## Was ist neu in v5?

**v5.0.0** (Breaking) — Architektur-Bereinigung:
- Browser-Automation von **Playwright-MCP auf `browser-use`-CLI** umgestellt (schnellerer Setup, weniger Dependencies).
- Excel-Generierung an **externes `document-skills:xlsx` Plugin** delegiert statt eigener Python-Pipeline.
- **Drei redundante Python-Skripte** (`citations.py`, `style_analysis.py`, `ranking.py`) gelöscht; Logik in Skills/Agents inlined.

**v5.0.1** — `/academic-research:setup` wurde zum vollständigen One-Click-Installer (installiert `browser-use` automatisch via `uv` oder `pipx`).

Vollständige Migration siehe [CHANGELOG.md](CHANGELOG.md).

<details>
<summary>Historisch: Was v4 gegenüber v3 brachte</summary>

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

</details>

## Voraussetzungen

Minimal — alles Weitere erledigt `/academic-research:setup` (siehe Installation).

- **Python 3.10+** (empfohlen: 3.11+)
- **Claude Code** (CLI, aktuelle Version)
- Einer von: **`uv`** oder **`pipx`** (für die automatische `browser-use`-Installation). Fehlt beides, funktioniert das Plugin trotzdem — die Browser-Suchmodule werden dann übersprungen. Install-Hinweise:
  ```bash
  brew install pipx                                      # macOS, Linux
  # ODER
  curl -LsSf https://astral.sh/uv/install.sh | sh        # plattformübergreifend
  ```

### Was `/setup` automatisch installiert

| Komponente | Zweck |
|---|---|
| `~/.academic-research/venv/` | Isolierte Python-Umgebung |
| `httpx`, `PyPDF2`, `pyyaml` | Python-Pakete aus `scripts/requirements.txt` |
| `browser-use` CLI | Browser-Automation via `uv tool install` oder `pipx install` |
| Claude-Code-Permissions | Einträge in `~/.claude/settings.local.json` |

### Was zusätzlich manuell nötig ist

- **`document-skills` Plugin** (nur wenn `/academic-research:excel` genutzt wird). Claude Code erlaubt keinem Plugin, andere Plugins zu installieren — der Befehl muss direkt im Claude-Prompt laufen:
  ```
  /plugin install document-skills@anthropic-agent-skills
  ```
- **`browser-use` Claude-Skill** unter `~/.claude/skills/browser-use/` (nur wenn noch nicht vorhanden). Dieser Skill wird von Anthropic separat distribuiert. Das Setup gibt eine Warnung aus, wenn er fehlt.

## Installation

### 1. Plugin installieren

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

### 2. Setup ausführen

```
/academic-research:setup
```

Ein Aufruf, sechs Schritte: Datenverzeichnis, Python-venv, Python-Pakete, `browser-use` CLI, Skill/Plugin-Checks, Permissions. Jeder Schritt meldet `✅` oder `⚠️` mit konkretem Hinweis bei Fehlen. Idempotent — mehrfacher Aufruf ist sicher.

<details>
<summary>Manueller Aufruf (ohne Slash-Command)</summary>

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

</details>

### 3. document-skills installieren (nur für `/excel`)

Einmalig in Claude Code:

```
/plugin install document-skills@anthropic-agent-skills
```

Das Setup warnt beim ersten Start, wenn das Plugin fehlt. Ohne das Plugin bleibt `/academic-research:excel` nicht nutzbar; alle anderen Commands laufen weiter.

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

Vollständiger Installer: venv, Python-Pakete, `browser-use` CLI (Auto-Install via `uv`/`pipx`), Claude-Skill- und Plugin-Checks, Permissions. Idempotent — mehrfach aufrufbar.

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

## Scripts (4 Python-Module)

Deterministische Logik ohne LLM-Aufruf, ausgeführt im isolierten venv (`~/.academic-research/venv/`). Frühere Skripte für Scoring, Zitatformatierung, Excel und Stil-Analyse wurden in Skills/Agents verlagert (siehe CHANGELOG v5.0.0).

| Script | Funktion |
|--------|----------|
| `search.py` | API-Aufrufe an 7 Quellen parallel (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv) |
| `dedup.py` | Deduplizierung nach DOI-Match + Titel-Ähnlichkeit (Levenshtein) |
| `pdf.py` | PDF-Download (5-Tier-Fallback) + Textextraktion (PyPDF2) + TF-IDF-Volltextindex |
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
| **Zugang** | 15% | Open Access=1.0, Institutional=0.8, DOI=0.5, URL=0.2 |

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

### Browser-Module (`browser-use` CLI)

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
| `config/browser_guides/*.md` | `browser-use`-Hinweise pro Datenbank (URL, Auth, Anti-Scraping-Warnungen) |

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
├── .claude-plugin/plugin.json       # Plugin-Manifest v5.0.0
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
├── scripts/                         # 4 Python-Module + Setup-Helper
│   ├── search.py, dedup.py, pdf.py, text_utils.py
│   ├── configure_permissions.py, setup.sh, requirements.txt
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

### Evals (ab v5.2.0)

Pro Skill und Agent gibt es eine Evals-Suite unter `tests/evals/` mit zugehörigen JSON-Daten in `evals/<component>/`.

**Lokaler Lauf:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
~/.academic-research/venv/bin/python -m pytest tests/evals/ -v
```

**Quality-Evals** vergleichen `with_skill` vs `without_skill` und erwarten ≥ 20 Prozentpunkte PASS-Rate-Delta (sonst rechtfertigt das Skill seine Existenz nicht).

**Trigger-Evals** prüfen Undertriggering (Recall ≥ 85 %) und Overtriggering (FPR ≤ 10 %) mit 20 Prompts pro Skill.

**Kein CI-Trigger** — Evals laufen lokal vor jedem Release, Reports werden manuell unter `docs/evals/` committet (API-Kosten vermeiden).

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Python venv not found" | `/academic-research:setup` ausführen |
| "Missing dependencies" | `~/.academic-research/venv/bin/pip install -r scripts/requirements.txt` |
| Browser-Module funktionieren nicht | `uv tool install browser-use && browser-use doctor` |
| Keine Ergebnisse bei Suche | Breitere Query verwenden, `--mode quick` testen |
| Excel leer | Zuerst `/academic-research:search` ausführen |
| Semantic Scholar 429 | SS_API_KEY Umgebungsvariable setzen |

## Lizenz

MIT
