# Academic Research v6.5

[![CI](https://github.com/jamski105/academic-research/actions/workflows/ci.yml/badge.svg)](https://github.com/jamski105/academic-research/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jamski105/academic-research/branch/main/graph/badge.svg)](https://codecov.io/gh/jamski105/academic-research)
[![Version](https://img.shields.io/badge/version-6.5.0-blue.svg)](CHANGELOG.md)
[![Skills](https://img.shields.io/badge/skills-28-orange.svg)](#skills-übersicht)
[![Tests](https://img.shields.io/badge/tests-963%20passing%20%2F%201111%20collected-success.svg)](#entwicklung-und-evals)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-8A2BE2.svg)](https://code.claude.com/docs/en/plugins)

**Dein Forschungs-Assistent in Claude Code — von der Themenfindung bis zur Abgabe.**

Ein modulares Claude-Code-Plugin für akademische Arbeiten (Facharbeit, Bachelor-, Master-, Doktorarbeit). Durchsucht 14 wissenschaftliche Quellen parallel, bewertet Literatur in fünf Dimensionen, generiert Exposés und Kapitelentwürfe, prüft Zitate, Stil und Formalia — alles direkt im Terminal über natürliche Sprache oder Slash-Commands.

Seit v6.0 hat das Plugin einen eigenen **Vault-MCP-Server** (SQLite + FTS5 + sqlite-vec) für halluzinationsfreie Zitate, einen **Universal Book Fetcher** (8-Tier-Pipeline), tiefen **humanizer-de**-Workflow, **Per-Uni-Profile** für Hochschulzugänge und viele weitere Features — alles mit minimalem Token-Verbrauch.

> [!WARNING]
> **Zitate immer gegenprüfen.** Die `citation-extraction` arbeitet mit der Claude-Citations-API und liefert seitengenaue Belege — trotzdem können Modelle halluzinieren. Prüfe jedes Zitat im Originaltext oder bitte Claude explizit darum (*„Alle Zitate gegen die Quell-PDFs verifizieren"*), bevor du es in deine Arbeit übernimmst. Das gilt besonders für Seitenzahlen, Autorennamen und Erscheinungsjahre.

---

<!-- SCIHUB-DISCLAIMER-BLOCK: Nicht verschieben, nicht entfernen. G ergaenzt diesen Block in Welle 2 nur, aendert ihn nicht. -->
> [!CAUTION]
> **SciHub-Tier (F18) — Optionaler Last-Resort: Rechtlich umstritten, deine Verantwortung**
>
> Dieses Plugin kann optional SciHub als letzten Fallback nutzen, wenn alle anderen Quellen (Open Access,
> institutionelle Lizenzen, Fernleihe) keinen Zugang liefern.
>
> **SciHub ist per Default DEAKTIVIERT.** Aktivierung nur nach explizitem Opt-in beim Setup:
>
> ```
> /academic-research:setup
> # → Frage: "SciHub-Tier aktivieren? (Rechtlich umstritten — Nutzung auf deine eigene Verantwortung)"
> ```
>
> - SciHub operiert rechtlich in einer umstrittenen Zone — die Nutzung kann in deinem Land gegen das Urheberrecht verstossen.
> - Jeder via SciHub bezogene Volltext wird im Vault mit `provenance:scihub` getaggt.
> - Im Output erscheint stets der Hinweis: *"Quelle via SciHub bezogen — bitte zusätzlich legalen Zugriff klären."*
> - **Du trägst die alleinige rechtliche Verantwortung für die Nutzung des SciHub-Tiers.**
<!-- END SCIHUB-DISCLAIMER-BLOCK -->

---

## Inhalt

1. [Für wen ist das?](#für-wen-ist-das)
2. [Was kann das Plugin?](#was-kann-das-plugin)
3. [Voraussetzungen](#voraussetzungen)
4. [Installation](#installation)
5. [Update auf v6.5 (Migration von v5)](#update-auf-v65--migration-von-v5)
6. [Walkthrough — Erstes Projekt](#walkthrough--erstes-projekt)
7. [Commands / Slash-Commands](#commands--slash-commands)
8. [Skills (28 selbstaktivierend)](#skills-übersicht)
9. [Agents (LLM-Subagents)](#agents)
10. [Vault-MCP-Server](#vault-mcp-server)
11. [5D-Scoring und Cluster](#5d-scoring-und-cluster)
12. [Suchquellen (14)](#suchquellen-14)
13. [Hooks-Stack](#hooks-stack)
14. [Per-Uni-Profile](#per-uni-profile)
15. [Glossar](#glossar)
16. [Troubleshooting](#troubleshooting)
17. [Entwicklung und Evals](#entwicklung-und-evals)
18. [Lizenz](#lizenz)

---

## Für wen ist das?

- **Studierende**, die eine Bachelor-, Master- oder Hausarbeit schreiben und einen strukturierten Rechercheprozess brauchen.
- **Doktorand\*innen**, die systematische Literaturreviews durchführen, Risk-of-Bias bewerten und PRISMA-Flows erstellen.
- **Schüler\*innen**, die eine Facharbeit schreiben und sauber zitieren lernen wollen.
- **Alle**, die Claude Code bereits nutzen und akademisches Schreiben mit KI-Unterstützung professionalisieren möchten.

Das Plugin kommt mit vorkonfigurierten **Per-Uni-Profilen** für ETH Zürich, FU Berlin, TU München, Universität Hamburg und Universität Wien. Weitere Profile sind einfach hinzufügbar.

---

## Was kann das Plugin?

### Kernfunktionen (alle Versionen)

| Aufgabe | Womit | Beispiel-Prompt |
|---------|-------|-----------------|
| **Thema und Forschungsfrage schärfen** | `academic-context` + `research-question-refiner` | *„Ich schreibe über DevOps-Governance im Mittelstand — hilf mir, die Forschungsfrage zu präzisieren."* |
| **Gliederung und Exposé bauen** | `advisor` | *„Erstelle mir ein Exposé und eine Gliederung."* |
| **Methodik wählen und begründen** | `methodology-advisor` | *„Qualitative Fallstudie oder quantitative Umfrage — was passt besser?"* |
| **Literatur finden (14 Quellen parallel)** | `/academic-research:search` | `/academic-research:search "IT-Compliance KMU" --mode deep` |
| **Papers bewerten (5D-Scoring + Cluster)** | `/academic-research:score` | `/academic-research:score` |
| **Excel-Übersicht generieren** | `/academic-research:excel` | `/academic-research:excel` |
| **Literatur-Lücken finden** | `literature-gap-analysis` | *„Zeig mir Kapitel, die zu wenig Quellen haben."* |
| **Quellen auf Peer-Review prüfen** | `source-quality-audit` | *„Wie viele meiner Quellen sind Peer-Reviewed?"* |
| **Kapitel entwerfen** | `chapter-writer` | *„Schreib mir einen Entwurf für den Theorieteil."* |
| **Zitate aus PDFs extrahieren** | `citation-extraction` | *„Erstelle ein Literaturverzeichnis im APA7-Stil."* |
| **Stil-Check + KI-Erkennung** | `style-evaluator` + `humanizer-de` | *„Prüf den Text auf KI-Muster und Passivüberhang."* |
| **Plagiatsnähe prüfen** | `plagiarism-check` | *„Liegt der Absatz zu nah am Original?"* |
| **Abstract und Keywords** | `abstract-generator` | *„Schreib mir ein IMRaD-Abstract."* |
| **Titel vorschlagen** | `title-generator` | *„Ich brauche 5 Titelvorschläge."* |
| **Formalia prüfen** | `submission-checker` | *„Ist meine Arbeit abgabefertig?"* |

### v6.x-Neuheiten

| Feature | Seit | Beschreibung |
|---------|------|-------------|
| **Vault MCP** | v6.0 | SQLite-Backend mit FTS5 + sqlite-vec: Zitate, Entscheidungen, Risk-of-Bias, Score-Historie, Material-Passport. Halluzinationsschutz via Verbatim-Validation-Hook. |
| **Universal Book Fetcher** | v6.2 | 8-Tier-Download-Pipeline mit 10 Site-Subagenten (TIB, Springer, De Gruyter, OAPEN, DOAB, KVK, Ebook Central, Nationallizenzen, generischer Fallback). Autarke Browser-Navigation via `browser-use`. |
| **humanizer-de** | v6.0 | Anti-KI-Audit-Pass mit Severity-Ranking und Stimmkalibrierung. Schützt vor Turnitin / GPTZero / OriginalityAI-Detection. |
| **Per-Uni-Profile** | v6.2 | `config/library-profiles/<uni>.yaml` konfiguriert HAN, Shibboleth, EZproxy, lizenzierte Sites. 5 Profile (eth-zurich, fu-berlin, tum, uni-hamburg, uni-wien) mitgeliefert. |
| **PRISMA-Flow** | v6.4 | Mermaid-Diagramm + PRISMA-2020-Checkliste für Systematic Reviews. |
| **Meta-Analysis** | v6.4 | DerSimonian-Laird Random-Effects mit Mermaid-Forest-Plot. |
| **Risk-of-Bias** | v6.4 | Cochrane RoB 2 / ROBINS-I / CASP Assessment Agent. |
| **Material-Passport** | v6.4 | Unveränderlicher Artefakt-Passport mit Repro-Lock. |
| **NotebookLM-Bundle** | v6.3 | PDF-Pack für manuelle NotebookLM-Uploads (Riesen-Bücher >600 Seiten). |
| **Zotero-Import** | v6.3 | pyzotero-Pull-only mit DOI/ISBN-Dedup in den Vault. |
| **Hooks-Stack** | v6.4 | 7 Hook-Events: PreToolUse, PostToolUse, PreCompact, Notification, PostCompact, SessionStart, Stop. |
| **LaTeX-Export** | v6.5 | Markdown-Kapitel → `.tex`, Bibliographie → `.bib` (biblatex DIN-1505). Per-Uni-Template-Slot. |
| **Contextual Retrieval** | v6.5 | Hybrid BM25 + vec0 mit Reciprocal-Rank-Fusion. Anthropic-Contextual-Embedding-Cache. |
| **Topic-Brainstorm** | v6.5 | 3-5 Kandidaten mit Feasibility/Novelty/Career-Fit-Scores + Pilot-Paper-Sets. |
| **Reading-List-Import** | v6.5 | PDF/Markdown/Plaintext-Listen → DOI/ISBN-Auflösung → Vault. |
| **Grant / Poster / Response** | v6.5 | Grant-Proposal (DFG/BMBF/EU), Conference-Poster (LaTeX tikzposter), Reviewer-Response-Letter. Default-Off, Opt-in via `output_targets`. |
| **CSL-JSON Import** | v6.4 | Beliebige CSL-Stile aus dem CSL-Repository laden. |
| **Citation-Styles** | v6.4 | MLA, Vancouver, Springer Author-Date (zusätzlich zu APA7/IEEE/Harvard/Chicago/DIN 1505). |

---

## Voraussetzungen

| Komponente | Warum | Installation |
|-----------|-------|--------------|
| **Claude Code** | CLI zum Ausführen | [Installations-Anleitung](https://code.claude.com/docs/en/quickstart) |
| **Python 3.11+** (entwickelt + getestet mit 3.14) | Vault-MCP-Server, Suchskripte | `brew install python@3.11` (macOS) |
| **`uv` oder `pipx`** | Für die automatische `browser-use`-Installation | `brew install pipx` oder `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Git** | Plugin-Marketplace-Install | auf macOS/Linux meist vorinstalliert |

**Optionale Abhängigkeiten:**

- `ocrmypdf` (OCR für Scan-PDFs ohne Text-Layer): `brew install ocrmypdf`
- `pyzotero` (für Zotero-Import): wird automatisch via `pip` installiert, wenn benötigt.

---

## Installation

### Schritt 1 — Plugin-Marketplace registrieren

```
/plugin marketplace add jamski105/academic-research
```

Dieser Schritt ist einmalig pro System.

### Schritt 2 — Plugin installieren

```
/plugin install academic-research@academic-research
```

Das Plugin landet global unter `~/.claude/plugins/cache/academic-research/` und ist in **allen** Claude-Code-Sessions verfügbar.

### Schritt 3 — Setup ausführen

```
/academic-research:setup
```

Dieser Command:

1. Legt `~/.academic-research/` als Daten-Verzeichnis an.
2. Erzeugt ein isoliertes Python-venv unter `~/.academic-research/venv/`.
3. Installiert Python-Pakete (httpx, PyPDF2, pyyaml, anthropic, openpyxl, pandas, sqlite-vec u.a.).
4. Installiert `browser-use`-CLI automatisch via `uv tool install browser-use` oder `pipx install browser-use`.
5. Richtet den Vault-MCP-Server ein (`academic_vault/`).
6. Fragt nach **Hochschul-Profil** (Opt-in für Per-Uni-Konfiguration).
7. Fragt nach **SciHub-Tier-Aktivierung** (Default: aus).
8. Trägt Permissions in `~/.claude/settings.local.json` ein.
9. Fragt (bei leerem Ordner): *„Hier einen Facharbeit-Arbeitsordner initialisieren?"* → `y`

Das Setup ist **idempotent** — mehrfach aufrufbar.

### Schritt 4 — Per-Uni-Profil auswählen (optional, empfohlen)

```
/academic-research:setup
# → "Hochschul-Profil auswählen?" → Deine Hochschule wählen oder eigenes Profil anlegen
```

Ohne Profil funktioniert das Plugin vollständig — nur die lizenzpflichtigen Bibliotheks-Zugänge (HAN, Shibboleth, EZproxy) stehen nicht zur Verfügung.

---

## Update auf v6.5 — Migration von v5

Vollständiger Guide: [docs/MIGRATION-v5-to-v6.md](docs/MIGRATION-v5-to-v6.md)

**Kurzversion (von v5.x):**

```bash
# 1. Plugin updaten
/plugin update academic-research

# 2. Vault einrichten (MCP-Server-Init)
/academic-research:setup

# 3. Existierende Literatur migrieren (optional)
/academic-research:setup --migrate-v5
# → Fragt: "literature_state.md in Vault migrieren?" → y
```

**Von v4.x oder älter:** Erst vollständig deinstallieren, dann neu installieren (v5.0 war Breaking — Browser-Automation und Excel-Generierung wurden komplett umgestellt). Details im [Migration-Guide](docs/MIGRATION-v5-to-v6.md).

---

## Walkthrough — Erstes Projekt

Ein vollständiger Durchlauf mit v6.x-Features.

### 1. Ordner anlegen und Setup starten

```bash
mkdir ~/Facharbeit-DevOps && cd ~/Facharbeit-DevOps
```

In Claude Code:

```
/academic-research:setup
```

Antworte auf *„Hier einen Facharbeit-Arbeitsordner initialisieren?"* mit `y`. Das Plugin legt an:

```
Facharbeit-DevOps/
├── academic_context.md     # Thesis-Profil (leere Stubs)
├── CLAUDE.md               # Plugin-Anleitung für Claude (generiert)
├── .gitignore              # sinnvolle Defaults
├── kapitel/
├── literatur/
└── pdfs/
```

### 2. Kontext einrichten

```
Ich schreibe eine Bachelorarbeit über DevOps-Governance
im deutschen Mittelstand. Leibniz FH, Wirtschaftsinformatik, 60 Seiten.
```

Der `academic-context`-Skill fragt durch: Forschungsfrage, Arbeitstyp, Hochschule, Disziplin, Methodik, Gliederung.

### 3. Thema finden (neu in v6.5)

Noch kein Thema? Der `topic-brainstorm`-Skill hilft:

```
Ich studiere Wirtschaftsinformatik im 5. Semester — welches Thema könnte passen?
```

Liefert 3–5 Kandidaten mit Feasibility/Novelty/Career-Fit-Scores und je 2–3 Forschungsfragen.

### 4. Forschungsfrage schärfen

```
Ist meine Forschungsfrage gut? „Wie wirkt sich DevOps auf KMU aus?"
```

`research-question-refiner` prüft Spezifität, Beantwortbarkeit, Falsifizierbarkeit.

### 5. Literatur suchen

```
/academic-research:search "DevOps Governance Mittelstand KMU" --mode standard
```

Sucht parallel in 7 APIs, dedupliziert, scort auf 5 Dimensionen. PDFs landen in `~/.academic-research/pdfs/`.

Für systematische Suche mit Browser-Modulen (Google Scholar, Springer, TIB usw.):

```
/academic-research:search "IT Compliance KMU" --mode deep
```

### 6. Buch beschaffen (neu in v6.2)

```
/academic-research:fetch "IT-Governance im Mittelstand" --isbn 978-3-658-12345-6
```

Der `book-fetcher`-Agent probiert automatisch TIB, Springer, OAPEN, KVK und andere Quellen gemäß deinem Per-Uni-Profil.

### 7. Literaturliste aus Dozenten-Handout importieren (neu in v6.5)

```
/academic-research:search --import-list literaturliste.pdf
```

Oder über den `reading-list-import`-Skill: *„Importiere diese Quellenliste ins Vault."*

### 8. Vault abfragen

```
Welche Quellen im Vault behandeln IT-Governance?
```

Der Vault antwortet mit Snippet + Seite, ohne dass PDFs erneut hochgeladen werden.

### 9. Papers bewerten und Excel exportieren

```
/academic-research:score
/academic-research:excel
```

### 10. Kapitel schreiben

```
Schreib mir einen Entwurf für das Methodik-Kapitel.
```

`chapter-writer` nutzt Vault-Zitate via `vault.find_quotes()` — seitengenau, halluzinationsgeprüft.

### 11. Anti-KI-Audit mit humanizer-de

```
/academic-research:humanize kapitel/03-methodik.md --mode deep
```

Erzeugt `kapitel/03-methodik.humanized.md` + `kapitel/03-methodik.diff.md` mit Severity-Ranking der KI-Muster.

### 12. PRISMA-Flow (für Systematic Reviews)

```
Erstelle den PRISMA-Flow für meine Literaturrecherche.
```

`prisma-flow`-Skill rendert das Mermaid-Diagramm und die 27-Punkte-Checkliste.

### 13. Abstract, Titel, Formalia-Check

```
Schreib ein IMRaD-Abstract (DE + EN).
Ich brauche 5 Titelvorschläge.
Ist die Arbeit abgabefertig? FH-Leibniz-Formalia prüfen.
```

### 14. LaTeX-Export (neu in v6.5)

```
/academic-research:latex --kapitel all --output thesis.tex
```

Erzeugt `thesis.tex` + `thesis.bib` (biblatex, DIN-1505-Stil).

---

## Commands / Slash-Commands

Commands werden explizit per `/academic-research:<name>` aufgerufen.

| Command | Beschreibung |
|---------|-------------|
| `/academic-research:search` | Literatursuche über 7 APIs + optional 7 Browser-Module |
| `/academic-research:score` | Re-Scoring und Cluster-Zuweisung |
| `/academic-research:excel` | Professionelle Excel-Datei (4 Sheets) |
| `/academic-research:setup` | Installer: venv, Browser, Vault, Hooks, Per-Uni-Profil |
| `/academic-research:history` | Recherche-Sessions einsehen |
| `/academic-research:fetch` | Buch/Paper via Site-Subagenten beschaffen |
| `/academic-research:pickup` | Bibliotheks-Pickup-Excel für nicht-OA-Quellen |
| `/academic-research:humanize` | Anti-KI-Audit-Pass via humanizer-de |
| `/academic-research:latex` | LaTeX-Export (`*.tex` + `*.bib`) |

### `/academic-research:search`

**Syntax:** `/academic-research:search "query" [--mode MODE] [--modules LIST] [--limit N] [--no-expand] [--no-browser]`

| Mode | Module | Top-N | Beschreibung |
|------|--------|-------|-------------|
| `quick` | 4 APIs | 15 | Schnelle Suche |
| `standard` | 7 APIs | 25 | Empfohlen |
| `deep` | 7 APIs + 7 Browser-Module | 40 | Systematisch |
| `metadata` | 7 APIs | 25 | Ohne PDFs |

### `/academic-research:fetch`

**Syntax:** `/academic-research:fetch <isbn|doi|titel|url> [--uni <profil>]`

Startet `book-fetcher`-Agent mit konfigurierbarer Fallback-Kette:
OA-Bücher (OAPEN → DOAB → TIB → KVK), Verlags-Bücher (Springer → De Gruyter → Ebook Central → Nationallizenzen).

---

## Skills-Übersicht

Skills aktivieren sich **automatisch** wenn Claude passende Keywords erkennt. Insgesamt **28 Skills** mit eigener `SKILL.md` (Claude-Code-Discovery-Count, inkl. dem vendored `xlsx/`). Das Verzeichnis `skills/_common/` enthält nur geteilte Markdown-Fragmente und zählt nicht als Skill.

### Kern-Skills

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `academic-context` | *„meine Arbeit"*, *„Thesis"*, *„Forschungsfrage"* | Bootet akademischen Kontext in `./academic_context.md` |
| `research-question-refiner` | *„Forschungsfrage formulieren"*, *„präzisieren"* | Verfeinert auf Spezifität, Beantwortbarkeit, Falsifizierbarkeit |
| `advisor` | *„Gliederung"*, *„Exposé"*, *„Struktur"* | Baut Gliederungen und Exposés im Dialog (7-Kriterien-Check) |
| `methodology-advisor` | *„welche Methodik"*, *„Forschungsdesign"* | Berät bei Methodenwahl (4-Dimensionen-Scoring) |
| `topic-brainstorm` | *„welches Thema"*, *„Themenfindung"* | 3–5 Kandidaten mit Feasibility/Novelty/Career-Fit |

### Literatur-Skills

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `literature-gap-analysis` | *„Literaturlücken"*, *„fehlende Quellen"* | Per-Kapitel-Coverage-Bericht |
| `source-quality-audit` | *„Quellenqualität"*, *„Peer-Review prüfen"* | 5-Dimensionen-Score 0–100 |
| `citation-extraction` | *„Zitate finden"*, *„Literaturverzeichnis erstellen"* | Citations-API, seitengenau, 8 Formate |
| `zotero-import` | *„Zotero importieren"*, *„Bibliothek einlesen"* | pyzotero-Pull mit Vault-Dedup |
| `reading-list-import` | *„Literaturliste importieren"*, *„Quellenliste"* | PDF/Markdown/Text → Vault |
| `citation-style-import` | *„eigenen Zitierstil"*, *„CSL laden"* | CSL-Repository → Vault-Stilregeln |

### Schreib-Skills

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `chapter-writer` | *„Kapitel schreiben"*, *„Einleitung"*, *„Fazit"* | Kapitel-Entwürfe mit Vault-Zitaten |
| `style-evaluator` | *„Stil prüfen"*, *„KI-Erkennung"* | 9-Metriken-Analyse + Anti-KI-Detection |
| `plagiarism-check` | *„Plagiat prüfen"*, *„zu nah am Original"* | N-Gramm-Overlap gegen Vault-Quellen |
| `humanizer-de` | *„humanisieren"*, *„menschlicher klingen"* | Anti-KI-Audit mit Severity-Ranking |

### Methodik-Skills

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `prisma-flow` | *„PRISMA"*, *„Systematic Review"*, *„Flussdiagramm"* | Mermaid-Flow + 27-Punkte-Checkliste |
| `material-passport` | *„Material-Passport"*, *„Artefakt sichern"* | Unveränderlicher Repro-Passport |

### Output-Skills (opt-in via `output_targets`)

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `grant-proposal` | *„Förderantrag"*, *„DFG"*, *„BMBF"*, *„EU-Antrag"* | DFG/BMBF/EU-Antrag mit Vault-Quellen |
| `conference-poster` | *„Poster"*, *„Konferenz-Poster"* | A0-Poster (LaTeX tikzposter / PowerPoint) |
| `reviewer-response` | *„Response-Letter"*, *„Reviewer-Kommentare"* | Point-by-point Response |

### Abschluss-Skills

| Skill | Aktiviert bei | Beschreibung |
|-------|--------------|-------------|
| `abstract-generator` | *„Abstract schreiben"*, *„Zusammenfassung"* | IMRaD-konform, DE + EN |
| `title-generator` | *„Titelvorschläge"*, *„Arbeitstitel"* | 5–7 Varianten mit Rationale |
| `submission-checker` | *„abgabefertig"*, *„Formalia prüfen"* | Formalia-Check, Default: FH Leibniz |

---

## Agents

Agents werden als LLM-Subagents von Commands oder Skills gestartet.

| Agent | Model | Genutzt von | Aufgabe |
|-------|-------|-------------|---------|
| `query-generator` | Haiku | `/search` | Expandiert Suchquery auf Modulebene |
| `relevance-scorer` | Sonnet | `/search`, `/score` | Semantische Relevanz 0–1, 10er-Batches mit Prompt-Caching |
| `quote-extractor` | Sonnet | `citation-extraction` | Verbatim-Zitate via Citations-API + Vault-Write |
| `quality-reviewer` | Sonnet | `chapter-writer`, `abstract-generator` | Evaluator-Optimizer-Pattern (PASS/REVISE) |
| `book-fetcher` | Sonnet | `/fetch` | Master-Orchestrator: entscheidet Fallback-Reihenfolge für Site-Subagenten |
| `tib-fetcher` | Sonnet | `book-fetcher` | tib.eu per browser-use |
| `springer-book` | Sonnet | `book-fetcher` | link.springer.com per browser-use + HAN |
| `oapen-fetcher` | Sonnet | `book-fetcher` | oapen.org per browser-use |
| `doabooks-fetcher` | Sonnet | `book-fetcher` | directory.doabooks.org per browser-use |
| `degruyter` | Sonnet | `book-fetcher` | degruyter.com per browser-use + Shibboleth |
| `nationallizenzen` | Sonnet | `book-fetcher` | nationallizenzen.de per browser-use |
| `ebook-central` | Sonnet | `book-fetcher` | ebookcentral.proquest.com per browser-use |
| `kvk-fetcher` | Sonnet | `book-fetcher` | KVK Meta-Suche (80+ Kataloge) |
| `generic-fetcher` | Sonnet | `book-fetcher` | Discovery-Fallback, DOM-Heuristiken |
| `auth-helper` | Sonnet | alle Site-Agents | HAN / Shibboleth-WAYF / EZproxy Login-Flow |
| `risk-of-bias` | Sonnet | `prisma-flow` | Cochrane RoB 2 / ROBINS-I / CASP |
| `meta-analysis` | Sonnet | direkt | DerSimonian-Laird Random-Effects + Forest-Plot |
| `figure-verifier` | Sonnet | `chapter-writer` | VLM-basierte Abbildungsverifikation |
| `scihub-fetcher` | Sonnet | `book-fetcher` | SciHub-Tier (nur bei `scihub_optin: true`) |

---

## Vault-MCP-Server

Der **Vault** (`academic_vault/`) ist die Kernkomponente seit v6.0. Er ersetzt die flachen Markdown-Dateien durch eine SQLite-Datenbank mit FTS5-Volltext-Index und sqlite-vec für semantische Suche.

**Datenbank:** `~/.academic-research/projects/<slug>/vault.db`

### MCP-Tools (alle 28)

Der Server registriert **28 MCP-Tools** (`@mcp.tool`). Maßgebliche Code-Referenz: [`academic_vault/server.py`](academic_vault/server.py) (Funktion `_build_mcp_server`). Die folgenden Tabellen sind nach Kategorie geordnet; Signatur mit Default-Werten, Beschreibung und Beispiel-Call.

**Suche & Papers**

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.search(query, type=None, k=5, rerank=False)` | Hybrid-Suche (BM25 + vec0 + RRF); `rerank=True` aktiviert Voyage/Cohere | `vault.search("transformer attention", k=10)` |
| `vault.get_paper(paper_id)` | Paper-Metadaten + `pdf_status` | `vault.get_paper("vaswani2017")` |
| `vault.add_paper(paper_id, csl_json, pdf_path=None, doi=None, isbn=None, page_offset=0, editor=None, chapter=None, page_first=None, page_last=None, container_title=None, parent_paper_id=None)` | Upsert eines Papers; `type` aus `csl_json` | `vault.add_paper("vaswani2017", csl_json, doi="10.5555/...")` |
| `vault.add_chapter(parent_paper_id, chapter_number, csl_json, paper_id=None, pdf_path=None, page_first=None, page_last=None)` | Legt Kapitel als Kind-Paper an; gibt `paper_id` zurück | `vault.add_chapter("book2020", 3, csl_json, page_first=45)` |
| `vault.ensure_file(paper_id)` | PDF → Anthropic Files-API; gibt gecachte `file_id` zurück | `vault.ensure_file("vaswani2017")` |
| `vault.stats()` | DB-Counts + Token-Ersparnis-Schätzung | `vault.stats()` |

**Zitate (Quotes)**

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.add_quote(paper_id, verbatim, extraction_method, api_response_id=None, pdf_page=None, printed_page=None, section=None, context_before=None, context_after=None)` | Fügt Verbatim-Zitat mit Provenance ein; `extraction_method="citations-api"` erfordert `api_response_id` | `vault.add_quote("vaswani2017", "Attention is all you need", "citations-api", api_response_id="resp_1")` |
| `vault.search_quote_text(verbatim, k=5)` | LIKE-Volltextsuche in `quotes.verbatim` (prüft, ob ein Zitat existiert) | `vault.search_quote_text("Attention is all", k=3)` |
| `vault.find_quotes(paper_id, query=None, k=10)` | Gibt Quotes für ein Paper zurück (optional Ähnlichkeitssuche) | `vault.find_quotes("vaswani2017", query="self-attention")` |
| `vault.get_quote(quote_id)` | Vollständiger Quote-Record | `vault.get_quote("q_42")` |

**Figures & Tabellen** (v6.1 Figure-Verifier)

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.add_figure(paper_id, page=None, caption=None, vlm_description=None, data_extracted_json=None)` | Fügt Figure/Tabelle ein; gibt `figure_id` zurück | `vault.add_figure("vaswani2017", page=3, caption="Fig. 1: Architecture")` |
| `vault.get_figure(figure_id)` | Gibt Figure-Record zurück oder `None` | `vault.get_figure("fig_7")` |
| `vault.list_figures(paper_id)` | Alle Figures eines Papers, nach `page` sortiert | `vault.list_figures("vaswani2017")` |

**OCR-Pipeline & Seitenzählung** (v6.1)

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.set_ocr_done(paper_id, value=1)` | Setzt `ocr_done`-Flag (`1`=OCR durchgeführt) | `vault.set_ocr_done("scan2019")` |
| `vault.update_pdf_path(paper_id, new_path)` | Aktualisiert den PDF-Pfad nach OCR | `vault.update_pdf_path("scan2019", "/data/scan2019_ocr.pdf")` |
| `vault.set_page_offset(paper_id, offset)` | Setzt `page_offset` (Bücher mit Vorseiten/Vorwort) | `vault.set_page_offset("book2020", 12)` |
| `vault.get_printed_page(paper_id, pdf_page)` | Berechnet gedruckte Seite: `pdf_page - page_offset` | `vault.get_printed_page("book2020", 25)` |

**Decision-Log & Ausschlüsse**

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.add_decision(category=None, text="", rationale=None)` | Fügt Entscheidung ins Decision-Log ein; gibt `decision_id` zurück | `vault.add_decision(category="scope", text="Nur Studien ab 2015", rationale="Aktualität")` |
| `vault.list_decisions(category=None, active_only=True)` | Gibt Decisions zurück (optionaler `category`-Filter) | `vault.list_decisions(category="scope")` |
| `vault.add_excluded_source(paper_id, reason=None)` | Fügt `paper_id` zu `excluded_sources` (verhindert Re-Vorschlag) | `vault.add_excluded_source("smith2010", reason="off-topic")` |
| `vault.is_excluded(paper_id)` | Prüft, ob `paper_id` ausgeschlossen ist | `vault.is_excluded("smith2010")` |

**Risk-of-Bias & Score-Historie** (v6.4)

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.add_risk_of_bias(paper_id, study_type, domain_scores)` | Fügt RoB-Assessment ein (`domain_scores` als JSON-String); gibt `assessment_id` zurück | `vault.add_risk_of_bias("rct2018", "RCT", '{"randomization":"low"}')` |
| `vault.list_risk_of_bias(paper_id=None)` | Gibt RoB-Assessments zurück (optional nach `paper_id` gefiltert) | `vault.list_risk_of_bias("rct2018")` |
| `vault.add_score_snapshot(paper_id, session_id, scores)` | Fügt Score-Snapshot ein (`scores` als JSON-String); gibt `snapshot_id` zurück | `vault.add_score_snapshot("rct2018", "sess_1", '{"relevance":0.8}')` |
| `vault.get_score_history(paper_id, k=None)` | Score-History eines Papers (neueste zuerst) | `vault.get_score_history("rct2018", k=5)` |

**Material-Passport & Lock** (v6.4)

| Tool (Signatur mit Defaults) | Beschreibung | Beispiel-Call |
|------|-------------|------|
| `vault.export_material_passport(slug, output_dir=".", score_algo_version="1.0", plugin_version="6.4")` | Exportiert `material-passport.json`; gibt Dateipfad zurück | `vault.export_material_passport("mein-projekt")` |
| `vault.lock_passport(slug)` | Setzt Vault-Lock für `slug` (macht Vault read-only) | `vault.lock_passport("mein-projekt")` |
| `vault.is_locked(slug)` | Prüft, ob der Vault für `slug` gelockt ist | `vault.is_locked("mein-projekt")` |

### Halluzinationsschutz

Der `verbatim-guard`-Hook prüft jeden `Write`-Aufruf auf `kapitel/*.md`: enthaltene Zitate werden gegen den Vault geprüft. Unbekannte Zitate werden geblockt mit Hinweis *„Zitat nicht im Vault — bitte über `quote-extractor` ziehen"*.

---

## 5D-Scoring und Cluster

Jedes Paper wird nach 5 Dimensionen bewertet (0–1):

| Dimension | Gewicht | Berechnung |
|-----------|---------|------------|
| **Relevanz** | 35 % | Keyword-Match Titel (70 %) + Abstract (30 %) + Phrasen-Bonus |
| **Aktualität** | 20 % | Exponentieller Verfall, 5-Jahre-Halbwertzeit |
| **Qualität** | 15 % | Zitationen/Jahr, Log-Skalierung |
| **Autorität** | 15 % | Venue-Reputation (IEEE = 1.0, Mid = 0.7, Other = 0.4) |
| **Zugang** | 15 % | Open Access = 1.0, Institutional = 0.8, DOI = 0.5, URL = 0.2 |

### Cluster

| Cluster | Kriterien | Rolle |
|---------|-----------|-------|
| **Kernliteratur** | Score ≥ 0.75, Relevanz ≥ 0.80 | Muss zitiert werden |
| **Ergänzungsliteratur** | Score ≥ 0.50, Relevanz ≥ 0.50 | Vertiefung |
| **Hintergrundliteratur** | Score ≥ 0.30 | Grundlagen, Standards |
| **Methodenliteratur** | Methodik-Keywords erkannt | Methodik-Begründung |

---

## Suchquellen (14)

### API-Module (automatisch, parallel)

| Modul | Quelle | Disziplin |
|-------|--------|-----------|
| CrossRef | DOI-Registry | Alle |
| OpenAlex | OpenAlex-Katalog | Alle |
| Semantic Scholar | Semantic Scholar | Alle |
| BASE | Bielefeld Academic Search | Alle |
| EconBiz | ZBW Suchportal | Wirtschaft |
| EconStor | OA-Wirtschafts-Repo | Wirtschaft |
| arXiv | arXiv Preprints | CS, ML, Physik, Mathe |

### Browser-Module (`browser-use`-CLI)

| Modul | Quelle | Auth |
|-------|--------|------|
| Google Scholar | Google | keine |
| Springer | Springer Nature | HAN optional |
| OECD | OECD.org | keine |
| RePEc | IDEAS/RePEc | keine |
| OPAC | Leibniz FH Bibliothek | Login |
| EBSCO | EBSCO Publication Finder | HAN |
| ProQuest | ProQuest Dissertationen | HAN |

---

## Hooks-Stack

Das Plugin konfiguriert 7 Events in `hooks/hooks.json` (5 Skript-Dateien + 1 Inline-Bash):

| Hook | Event | Beschreibung |
|------|-------|-------------|
| `verbatim-guard.mjs` | `PreToolUse(Write)` | Blockt Kapitel-Writes mit nicht-verifizierten Zitaten |
| `post-tool-use-decisions.mjs` | `PostToolUse(Write)` | Decision-Log: jede `.md`-Änderung wird protokolliert |
| `pre-compact.mjs` | `PreCompact` | Snapshot-Backup vor Claude-Compaction |
| `mid-session-reinforcement.mjs` | `Notification` | Erinnerung an Anti-Fabrikations-Regeln (nach ~20 Nachrichten) |
| `mid-session-reinforcement.mjs` | `PostCompact` | Erinnerung an Anti-Fabrikations-Regeln nach Compaction |
| `onboard-project-uni-prompt.sh` | `SessionStart` | Prüft Python-venv-Bereitschaft beim Session-Start |
| *(Inline-Bash)* | `Stop` | Hinweis bei ungesicherten `academic_context.md`-Änderungen |

---

## Per-Uni-Profile

Profile liegen unter `config/library-profiles/<uni>.yaml` und konfigurieren Bibliotheks-Auth für den `book-fetcher` und Browser-Module.

**Mitgelieferte Profile:**

| Profil | Hochschule | Auth-Typ |
|--------|-----------|----------|
| `eth-zurich.yaml` | ETH Zürich | Shibboleth |
| `fu-berlin.yaml` | Freie Universität Berlin | Shibboleth |
| `tum.yaml` | TU München | Shibboleth |
| `uni-hamburg.yaml` | Universität Hamburg | Shibboleth |
| `uni-wien.yaml` | Universität Wien | Shibboleth |

### Profil aktivieren

```bash
# Vorhandenes Profil als Ausgangsbasis kopieren und anpassen
cp config/library-profiles/tum.yaml \
   ~/.academic-research/library-profiles/meine-uni.yaml
# → uni, auth_url, credentials_keys, licensed_sites eintragen

# Als aktives Profil setzen
/academic-research:setup --uni meine-uni
```

---

## Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Vault** | SQLite-basierter MCP-Server des Plugins. Speichert Papers, Verbatim-Zitate, Entscheidungen, RoB-Assessments und Score-Historie. Ersetzt `literature_state.md` als Single Source of Truth. |
| **Subagent** | LLM-Unteragent, der von einem Skill oder Command gestartet wird, um eine spezialisierte Aufgabe zu erledigen (z. B. ein Site-Subagent für Buch-Download auf tib.eu). |
| **Site-Profile** | YAML-Konfiguration einer Hochschule, die Auth-Typ (HAN/Shibboleth/EZproxy), lizenzierte Seiten und Zugangsdaten-Keys beschreibt. Wird von `auth-helper` und `book-fetcher` genutzt. |
| **Material-Passport** | Unveränderlicher Metadaten-Passport für ein Artefakt (Paper, Kapitel). Kann via `vault.lock_passport()` eingefroren werden — danach keine Änderungen mehr möglich. |
| **Contextual Retrieval** | Anthropic-Pattern: vor jedem Chunk-Embedding wird ein 1-Satz-Kontext angehängt (via Prompt-Caching). Verbessert Recall@10 deutlich vs. Vanilla-vec0. |
| **Decision-Log** | Append-only-Protokoll aller `.md`-Änderungen und Entscheidungen. Wird vom Hook `post-tool-use-decisions.mjs` (PostToolUse) automatisch befüllt; programmatisch via `vault.add_decision(text, category)`. |
| **Vault-Lock** | Read-only-Sperre des Vault. Nach `vault.lock_passport(paper_id)` sind keine Schreibzugriffe mehr möglich — Grundlage für reproduzierbare Abgaben (siehe Repro-Lock, Skill `material-passport`). |
| **Repro-Lock** | Reproduzierbarkeits-Sperre des Skills `material-passport`: friert den Material-Passport ein und sperrt den Vault read-only (Vault-Lock), damit Dritte den Stand exakt nachvollziehen können. |
| **OCR-Detection** | Automatische Prüfung, ob ein PDF einen Text-Layer besitzt (`scripts/pdf.py:detect_needs_ocr`). Fehlt der Layer, schlägt das Plugin OCR via `ocrmypdf` vor. |
| **page_offset** | Differenz zwischen PDF-Seitenzahl und gedruckter Seitenzahl bei Büchern mit Vorseiten (`printed_page = pdf_page - offset`). Wird von `scripts/page_offset.py` ermittelt und vom `book-handler` für seitengenaue Zitate genutzt. |
| **output_targets** | Opt-in-Eintrag im Projekt-State, der Default-Off-Output-Skills (`grant-proposal`, `conference-poster`, `reviewer-response`) aktiviert. Nur wenn der passende Wert gesetzt ist, läuft der jeweilige Skill (v6.5-Opt-in-Pattern). |
| **PRISMA** | Preferred Reporting Items for Systematic Reviews and Meta-Analyses — Standard-Framework für Transparent-Reporting. Das Plugin generiert PRISMA-2020-konforme Mermaid-Flussdiagramme. |
| **HAN** | Hochschulauthentifizierungs-Netzwerk — Bibliotheks-Proxy für lizenzpflichtige Datenbanken. |
| **RRF** | Reciprocal-Rank-Fusion — Methode zum Zusammenführen von BM25- und vec0-Rankings im Vault. |
| **Abstract** | Kurzfassung der Arbeit (150–300 Wörter), IMRaD-konform. |
| **IMRaD** | Introduction, Methods, Results, and Discussion — Standard für wissenschaftliche Abstracts. |
| **Peer-Review** | Wissenschaftlicher Begutachtungsprozess vor Publikation. |
| **5D-Score** | Eigene Metrik: Relevanz (35 %), Aktualität (20 %), Qualität (15 %), Autorität (15 %), Zugang (15 %). |
| **Cluster** | Gruppierung von Papers: Kern-, Ergänzungs-, Hintergrund-, Methodenliteratur. |
| **Skill** | Selbstaktivierende Claude-Erweiterung. Claude erkennt Keywords und lädt die passende Anleitung. |
| **BibTeX** | Textbasiertes Literatur-Format für LaTeX. Andere Formate: APA7, IEEE, Harvard, Chicago, DIN 1505, MLA, Vancouver, Springer Author-Date. |
| **CSL** | Citation Style Language — XML-basiertes Format für Zitierstile. 10.000+ Stile im CSL-Repository. |
| **humanizer-de** | Globaler Skill für Anti-KI-Audit deutschsprachiger Texte. Schützt vor Turnitin/GPTZero/OriginalityAI. |

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| *„Python venv not found"* | `/academic-research:setup` ausführen |
| *„Vault not initialized"* | `/academic-research:setup` — initialisiert MCP-Server |
| *„Missing dependencies"* | `~/.academic-research/venv/bin/pip install -r scripts/requirements.txt` |
| Browser-Module funktionieren nicht | `uv tool install browser-use && browser-use doctor` |
| Keine Ergebnisse bei Suche | Breitere Query; `--no-expand` für Roh-Query |
| Vault-Suche liefert keine Treffer | `vault.stats()` prüfen — evtl. `--migrate-v5` nötig |
| `book-fetcher` schlägt immer fehl | Per-Uni-Profil prüfen: `cat ~/.academic-research/library-profiles/active.yaml` |
| Verbatim-Guard blockt Kapitel-Write | Zitat via `quote-extractor` aus PDF holen, dann nochmal versuchen |
| Excel leer | Zuerst `/academic-research:search` ausführen |
| Semantic Scholar 429-Fehler | `SS_API_KEY` Umgebungsvariable setzen |
| Skill triggert nicht | Keyword aus Trigger-Liste verwenden oder Skill explizit ansprechen |
| Plugin soll in Code-Projekten nicht laden | `.claude/settings.local.json`: `{"enabledPlugins": {"academic-research@academic-research": false}}` |
| Kontext wird nicht geladen | `ls academic_context.md` — fehlt → `/academic-research:setup` in diesem Ordner |

---

## Entwicklung und Evals

### Tests ausführen

```bash
~/.academic-research/venv/bin/python -m pytest tests/ -v
```

Aktuell: **1111 Tests gesammelt**, davon **963 bestanden** und 148 übersprungen (`pytest --collect-only` für die Gesamtzahl). Enthalten sind Regression-Guards (`test_skill_naming.py`, `test_cross_references.py`, `test_skills_manifest.py`).

Die Kern-Suite ist **offline-hermetisch** und läuft ohne Netzwerk. Übersprungen werden Tests, die externe Abhängigkeiten brauchen: API-basierte Evals unter `tests/evals/` setzen einen `ANTHROPIC_API_KEY` voraus (Network/External), und einige Integrations-Tests werden ohne installierte optionale Pakete (z.B. `requests`, `sqlite-vec`) automatisch geskippt.

### pre-commit (empfohlen)

Für lokale Hygiene wird `pre-commit` empfohlen. Die Konfiguration liegt in
[`.pre-commit-config.yaml`](.pre-commit-config.yaml) und blockt versehentlich
committete große Dateien, neue Submodule und private Schlüssel. OS-Artefakte wie
`.DS_Store` werden bereits über `.gitignore` ausgeschlossen.

```bash
pip install pre-commit
pre-commit install
```

### Evals

```bash
export ANTHROPIC_API_KEY=sk-ant-...
~/.academic-research/venv/bin/python -m pytest tests/evals/ -v
```

- **Quality-Evals:** `with_skill` vs. `without_skill`, Schwelle: Δ ≥ 20 pp PASS-Rate (enforced via `eval_runner.check_quality_delta`, konfigurierbar über `EVAL_DELTA_THRESHOLD`, Default `0.20`).
- **Trigger-Evals:** Recall ≥ 85 %, FPR ≤ 10 % je Skill.

Kein CI-Trigger — Evals laufen lokal vor jedem Release. Reports unter `docs/evals/`.

---

## Lizenz

**Lizenz:** MIT (siehe [LICENSE](LICENSE))

**Plugin auf GitHub:** [github.com/jamski105/academic-research](https://github.com/jamski105/academic-research)

**Bug melden / Feature anfragen:** [GitHub Issues](https://github.com/jamski105/academic-research/issues)

**Referenzen:**

- [Anthropic Skill Spec](https://agentskills.io/specification)
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [anthropics/skills Cookbook](https://github.com/anthropics/skills)
- [Keep a Changelog](https://keepachangelog.com/de/1.1.0/)
- [Contextual Retrieval (Anthropic)](https://anthropic.com/news/contextual-retrieval)
- [PRISMA 2020](https://prisma-statement.org)
