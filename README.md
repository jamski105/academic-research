# Academic Research v5.4

[![Version](https://img.shields.io/badge/version-5.4.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-8A2BE2.svg)](https://code.claude.com/docs/en/plugins)
[![Skills](https://img.shields.io/badge/skills-13-orange.svg)](#skills-13-selbstaktivierend)
[![Tests](https://img.shields.io/badge/tests-95%20passing-success.svg)](#entwicklung-und-evals)

**Dein Forschungs-Assistent in Claude Code — von der Themenfindung bis zur Abgabe.**

Ein modulares Claude-Code-Plugin für akademische Arbeiten (Facharbeit, Bachelor-, Master-, Doktorarbeit). Durchsucht 14 wissenschaftliche Quellen parallel, bewertet Literatur in fünf Dimensionen, generiert Exposés und Kapitelentwürfe, prüft Zitate, Stil und Formalia — alles direkt im Terminal über natürliche Sprache oder Slash-Commands.

> [!WARNING]
> **Zitate immer gegenprüfen.** Die `citation-extraction` arbeitet mit der Claude-Citations-API und liefert seitengenaue Belege — trotzdem können Modelle halluzinieren. Prüfe jedes Zitat im Originaltext oder bitte Claude explizit darum (*„Alle Zitate gegen die Quell-PDFs verifizieren"*), bevor du es in deine Arbeit übernimmst. Das gilt besonders für Seitenzahlen, Autorennamen und Erscheinungsjahre.

---

## Inhalt

1. [Für wen ist das?](#für-wen-ist-das)
2. [Was kann das Plugin?](#was-kann-das-plugin)
3. [Voraussetzungen](#voraussetzungen)
4. [Installation (Schritt für Schritt)](#installation-schritt-für-schritt)
5. [Update auf v5.4 (von älteren Versionen)](#update-auf-v54-von-älteren-versionen)
6. [Alte Dateien löschen](#alte-dateien-löschen)
7. [Erstes Projekt aufsetzen — Walkthrough](#erstes-projekt-aufsetzen--walkthrough)
8. [Best Practices](#best-practices)
9. [Commands (5 Slash-Commands)](#commands-5-slash-commands)
10. [Skills (13 selbstaktivierend)](#skills-13-selbstaktivierend)
11. [Agents (4 LLM-Subagents)](#agents-4-llm-subagents)
12. [Scripts (Python-Hintergrund)](#scripts-python-hintergrund)
13. [5D-Scoring und Cluster](#5d-scoring-und-cluster)
14. [Suchquellen (14)](#suchquellen-14)
15. [Kontext-Dateien im Projekt](#kontext-dateien-im-projekt)
16. [Troubleshooting](#troubleshooting)
17. [Entwicklung und Evals](#entwicklung-und-evals)
18. [Was ist neu in v5?](#was-ist-neu-in-v5)
19. [Glossar (für Erstnutzer)](#glossar-für-erstnutzer)
20. [Lizenz und Weiterführendes](#lizenz-und-weiterführendes)

---

## Für wen ist das?

- **Studierende**, die eine Bachelor-, Master- oder Hausarbeit schreiben und einen strukturierten Rechercheprozess brauchen.
- **Doktorand\*innen**, die systematische Literaturreviews durchführen und Lücken in der Literatur identifizieren.
- **Schüler\*innen**, die eine Facharbeit schreiben und sauber zitieren lernen wollen.
- **Alle**, die Claude Code bereits nutzen und akademisches Schreiben mit KI-Unterstützung professionalisieren möchten.

Das Plugin ist auf die FH Leibniz vorkonfiguriert (Formalia), lässt sich aber über `references/<variant>.md` auf andere Hochschulen anpassen.

## Was kann das Plugin?

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
| **Stil-Check + KI-Erkennung** | `style-evaluator` | *„Prüf den Text auf KI-Muster und Passivüberhang."* |
| **Plagiatsnähe prüfen** | `plagiarism-check` | *„Liegt der Absatz zu nah am Original?"* |
| **Abstract und Keywords** | `abstract-generator` | *„Schreib mir ein IMRaD-Abstract."* |
| **Titel vorschlagen** | `title-generator` | *„Ich brauche 5 Titelvorschläge."* |
| **Formalia prüfen (FH Leibniz)** | `submission-checker` | *„Ist meine Arbeit abgabefertig?"* |

## Voraussetzungen

Minimal — alles Weitere erledigt das Setup automatisch.

| Komponente | Warum | Installation |
|-----------|-------|--------------|
| **Claude Code** | CLI zum Ausführen | [Installations-Anleitung](https://code.claude.com/docs/en/quickstart) |
| **Python 3.10+** | Für deterministische Such- und Dedup-Logik | `brew install python@3.11` (macOS) |
| **`uv` oder `pipx`** | Für die automatische `browser-use`-Installation | `brew install pipx` oder `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Git** | Für Plugin-Marketplace-Install | auf macOS/Linux meist vorinstalliert |

Fehlt `uv`/`pipx` nur, funktioniert das Plugin trotzdem — die Browser-Module werden dann übersprungen und nur die sieben API-Quellen durchsucht.

## Installation (Schritt für Schritt)

### Schritt 1 — Plugin-Marketplace registrieren

Öffne Claude Code in einem beliebigen Ordner und führe im Prompt aus:

```
/plugin marketplace add jamski105/academic-research
```

Dieser Schritt ist einmalig pro System. Der Marketplace ist jetzt bekannt — du kannst das Plugin (und künftige Updates) direkt daraus installieren.

### Schritt 2 — Plugin installieren

```
/plugin install academic-research@academic-research
```

Das Plugin landet global unter `~/.claude/plugins/cache/academic-research/` und ist ab sofort in **allen** Claude-Code-Sessions verfügbar (egal in welchem Projektordner du arbeitest).

> **Kein eigenes Repo nötig.** Du musst das Plugin-Repository *nicht* selbst klonen — der Marketplace zieht sich alles nötige automatisch.

### Schritt 3 — Setup ausführen (installiert Abhängigkeiten)

```
/academic-research:setup
```

Dieser Command:

1. Legt `~/.academic-research/` als Daten-Verzeichnis an (Sessions, PDFs).
2. Erzeugt ein isoliertes Python-venv unter `~/.academic-research/venv/`.
3. Installiert Python-Pakete (`httpx`, `PyPDF2`, `pyyaml`, `anthropic`).
4. Installiert `browser-use`-CLI automatisch via `uv tool install browser-use` oder `pipx install browser-use`.
5. Prüft, ob der `browser-use`-Claude-Skill und das `document-skills`-Plugin vorhanden sind, und warnt wenn nicht.
6. Trägt Permissions in `~/.claude/settings.local.json` ein.
7. **Wenn der aktuelle Ordner leer ist:** fragt, ob eine Facharbeit-Struktur angelegt werden soll (*„Hier einen Facharbeit-Arbeitsordner initialisieren?"* → `y`). Legt dann `academic_context.md`, `CLAUDE.md`, `.gitignore`, `kapitel/`, `literatur/`, `pdfs/` an.

Das Setup ist **idempotent** — du kannst es beliebig oft aufrufen, ohne etwas zu beschädigen.

### Schritt 4 — document-skills installieren (für Excel-Export)

Nur wenn du `/academic-research:excel` nutzen willst:

```
/plugin install document-skills@anthropic-agent-skills
```

Ohne dieses Plugin bleiben alle anderen Features funktionsfähig — nur der Excel-Export braucht es.

### Schritt 5 — browser-use Skill (optional, für Google Scholar & Co.)

Der `browser-use`-Claude-Skill liegt unter `~/.claude/skills/browser-use/`. Falls er fehlt, warnt das Setup. Er ermöglicht Suchen über Google Scholar, Springer, OECD, RePEc, OPAC, EBSCO und ProQuest. Anthropic distribuiert den Skill separat — eine Google-Suche nach *„claude browser-use skill"* führt zu den aktuellen Installationshinweisen.

### Alternative — Lokale Entwicklung (aus geklontem Repo)

Wenn du am Plugin-Code selbst arbeiten willst:

```bash
cd ~/Repos
git clone https://github.com/jamski105/academic-research.git
claude --plugin-dir ~/Repos/academic-research
```

Änderungen im Repo sind sofort wirksam — kein Cache, kein Marketplace nötig.

## Update auf v5.4 (von älteren Versionen)

### Von einer v5.x-Version

```
/plugin update academic-research
```

Danach in **jedem** deiner Facharbeit-Ordner einmal:

```
/academic-research:setup
```

Das stellt sicher, dass neue Dependencies (z. B. `anthropic>=0.40`) nachgezogen werden und die projekt-lokale Struktur aktuell ist.

### Von v4.x → v5.4 (Breaking)

v5.0.0 hat drei Dinge umgestellt:

1. **Browser-Automation**: Playwright-MCP → `browser-use`-CLI.
2. **Excel-Generierung**: eigene Python-Pipeline → externes `document-skills`-Plugin.
3. **Drei Python-Skripte gelöscht**: Logik ist jetzt in Skills/Agents inline.

v5.3.0 hat zusätzlich den Kontext umgestellt:

4. **Kontext-Dateien**: Claude-Memory → projekt-lokal (`./academic_context.md` im Ordner).

**Update-Schritte:**

```
# 1. Plugin updaten
/plugin update academic-research

# 2. Alte Playwright-MCP-Permissions wegwerfen: in ~/.claude/settings.local.json
#    alle "mcp__playwright__*"-Einträge entfernen, ODER /setup neu laufen lassen (überschreibt).

# 3. Venv neu bauen (wegen openpyxl, das nicht mehr gebraucht wird)
rm -rf ~/.academic-research/venv

# 4. Setup neu laufen lassen — installiert browser-use, neue Deps
/academic-research:setup

# 5. document-skills installieren (für Excel)
/plugin install document-skills@anthropic-agent-skills

# 6. Im Facharbeit-Ordner: Kontext aus Memory in Projekt migrieren
cd ~/Pfad/zur/Arbeit
/academic-research:setup
# → fragt: "Bestehenden Kontext in Claude-Memory gefunden. Kopieren?" → y
```

Details siehe [CHANGELOG.md](CHANGELOG.md) unter [5.0.0] und [5.3.0].

### Von v3.x → v5.4 (großer Sprung)

v3 war eine monolithische 7-Phasen-Pipeline. v4 hat das in 13 modulare Skills zerlegt, v5 hat weitere Breaking Changes gebracht. **Saubersten Weg: komplett deinstallieren, neu installieren.**

```
# 1. Altes Plugin entfernen
/plugin uninstall academic-research
```

Dann die Rest-Aufräumarbeit, siehe nächster Abschnitt [Alte Dateien löschen](#alte-dateien-löschen).

Danach:

```
# 2. Neu installieren
/plugin marketplace add jamski105/academic-research
/plugin install academic-research@academic-research
/academic-research:setup
/plugin install document-skills@anthropic-agent-skills
```

## Alte Dateien löschen

Wenn du von v3 oder v4 kommst (oder einfach aufräumen willst), sind das die Stellen, an denen sich Altlasten sammeln können:

### 1. Alte Plugin-Caches

```bash
# macOS / Linux
rm -rf ~/.claude/plugins/cache/academic-research      # falls vom /plugin uninstall nicht entfernt
rm -rf ~/.claude/plugins/cache/anthropic-agent-skills/document-skills  # nur wenn du document-skills NICHT mehr willst
```

### 2. Alte Python-Venv (aus v3/v4)

```bash
rm -rf ~/.academic-research/venv
```

Wird beim nächsten `/academic-research:setup` automatisch neu gebaut.

### 3. Alte Playwright-MCP-Reste (nur wenn du von v4.x kommst)

```bash
# macOS
rm -rf ~/.playwright-mcp/
rm -rf ~/Library/Caches/ms-playwright/

# Linux
rm -rf ~/.playwright-mcp/
rm -rf ~/.cache/ms-playwright/
```

Und in `~/.claude/settings.local.json` alle `mcp__playwright__*`-Permissions manuell löschen (oder `/academic-research:setup` neu laufen lassen — das überschreibt die Liste).

### 4. Memory-basierter Kontext aus v4 / frühem v5 (nur wenn du mit v5.3+ arbeitest)

Der alte Memory-Kontext liegt unter `~/.claude/projects/<projekt-hash>/memory/`. **Nicht blind löschen** — zuerst migrieren:

```
cd ~/Pfad/zur/Arbeit
/academic-research:setup
# → "Bestehenden Kontext in Claude-Memory gefunden. Kopieren?" → y
```

Nach erfolgreicher Migration (`./academic_context.md` liegt im Projektordner) kannst du die Memory-Dateien optional löschen. Das Plugin liest sie ohnehin nicht mehr.

### 5. Deine alten Session-Daten (optional)

`~/.academic-research/sessions/` enthält deine Recherche-Historie. **Nur löschen, wenn du sie wirklich nicht mehr brauchst** — die sind sonst verloren.

```bash
rm -rf ~/.academic-research/sessions/   # ⚠️ endgültig
```

### 6. Sanity-Check

Nach dem Aufräumen:

```
/plugin list
```

Sollte `academic-research@academic-research 5.4.x` zeigen und sonst nur das, was du explizit installiert hast.

## Erstes Projekt aufsetzen — Walkthrough

Ein kompletter Durchlauf von leerem Ordner bis zur ersten Kapitel-Rohfassung.

### 1. Ordner anlegen und Setup starten

```bash
mkdir ~/Facharbeit-DevOps && cd ~/Facharbeit-DevOps
```

In Claude Code:

```
/academic-research:setup
```

Antworte auf *„Hier einen Facharbeit-Arbeitsordner initialisieren?"* mit `y`. Das Plugin legt jetzt an:

```
Facharbeit-DevOps/
├── academic_context.md     # Dein Thesis-Profil (leere Stubs)
├── CLAUDE.md               # Plugin-Anleitung für Claude (generiert)
├── .gitignore              # sinnvolle Defaults (pdfs/, sessions/, etc.)
├── kapitel/                # für Kapitelentwürfe
│   └── .gitkeep
├── literatur/              # für exportierte Excel-Dateien
│   └── .gitkeep
└── pdfs/                   # für heruntergeladene Paper (gitignored)
    └── .gitkeep
```

### 2. Kontext einrichten

Einfach natürliche Sprache:

```
Ich schreibe eine Bachelorarbeit über DevOps-Governance
im deutschen Mittelstand. Leibniz FH, Wirtschaftsinformatik, 60 Seiten.
```

Der `academic-context`-Skill springt automatisch an und fragt durch:

- Forschungsfrage (falls noch unklar — sonst wird sie gleich gespeichert)
- Arbeitstyp, Hochschule, Disziplin
- Methodik (oder *„noch offen"*)
- Geplante Gliederung

Ergebnis: `./academic_context.md` ist gefüllt. Alle anderen Skills lesen von hier.

### 3. Forschungsfrage schärfen (falls nötig)

```
Ist meine Forschungsfrage gut? „Wie wirkt sich DevOps auf KMU aus?"
```

`research-question-refiner` prüft Spezifität, Beantwortbarkeit, Falsifizierbarkeit und gibt 2–3 geschärfte Alternativen.

### 4. Methodik wählen

```
Welche Methodik passt: qualitative Fallstudie oder quantitative Umfrage?
```

`methodology-advisor` scort beide Optionen auf 4 Dimensionen (Machbarkeit, Datenzugang, Passung, Zeitbudget) und empfiehlt eine.

### 5. Exposé und Gliederung bauen

```
Jetzt das Exposé und eine Gliederung.
```

`advisor` führt dich iterativ zu einer validierten Gliederung (≥ 3 Hauptkapitel, ≥ 15 Quellen-Schätzung, Forschungsfrage ≤ 25 Wörter).

### 6. Literatur suchen

```
/academic-research:search "DevOps Governance Mittelstand KMU" --mode standard
```

Das sucht parallel in 7 APIs, dedupliziert, scort auf 5 Dimensionen, lässt den `relevance-scorer`-Agent eine LLM-Relevanz bewerten und liefert eine Top-25-Tabelle. PDFs landen in `~/.academic-research/pdfs/`.

Für tiefe Systematik (mit Browser-Modulen: Google Scholar, Springer, OECD etc.):

```
/academic-research:search "IT Compliance KMU" --mode deep
```

### 7. Papers bewerten und Excel exportieren

```
/academic-research:score
/academic-research:excel
```

Excel landet in `literatur/` mit 4 Sheets (Übersicht, Cluster-Analyse, Kapitel-Zuordnung, Rohdaten).

### 8. Literatur-Lücken prüfen

```
Zeig mir, welche Kapitel zu wenig Quellen haben.
```

`literature-gap-analysis` geht Kapitel für Kapitel durch die Coverage und liefert konkrete Such-Queries für nachzuziehende Themen.

### 9. Kapitel schreiben

```
Schreib mir einen Entwurf für das Methodik-Kapitel.
```

`chapter-writer` nutzt `./literature_state.md` und die Claude-Citations-API für seitengenaue Belege. Output: `kapitel/03-methodik.md` (oder was du sagst).

### 10. Stil prüfen und Plagiatsnähe

```
Prüf diesen Text auf KI-Muster und Passivüberhang.
# [Text einfügen oder Datei angeben]

Liegt dieser Absatz zu nah am Original?
# [Absatz + Quelle]
```

### 11. Zitate formatieren

```
Erstelle mir ein Literaturverzeichnis im APA7-Stil aus allen Papern in pdfs/.
```

### 12. Abstract, Titel, Formalia-Check

```
Schreib ein IMRaD-Abstract (DE + EN).
Ich brauche 5 Titelvorschläge.
Ist die Arbeit abgabefertig? FH-Leibniz-Formalia prüfen.
```

### 13. Recherche-Historie einsehen

```
/academic-research:history
/academic-research:history "DevOps"
/academic-research:history stats
```

## Best Practices

### Kontext zuerst, Suche später

Immer erst `academic-context` füllen lassen, bevor du `/search` startest. Der `query-generator`-Agent nutzt Thema, Disziplin und Forschungsfrage, um deutlich bessere Suchbegriffe zu erzeugen. Ohne Kontext suchst du mit Roh-Query.

### Nutze Slash-Commands für deterministische Tasks, Skills für Gespräch

- **Slash-Commands** (`/search`, `/score`, `/excel`) — wenn du genau einen Task willst (Literaturliste ziehen, Excel exportieren).
- **Skills** (automatisch) — wenn du im Dialog bleibst und Claude die Entscheidung treffen soll, was als nächstes dran ist.

### Zitate doppelt prüfen

Trotz Citations-API: Halluzinationen sind nie ausgeschlossen. Nach jeder Zitat-Extraktion:

```
Verifiziere alle Zitate gegen die Quell-PDFs. Markiere jedes, bei dem
Seitenzahl, Wortlaut oder Autor nicht 1:1 übereinstimmt.
```

### Projektordner versionieren

`academic_context.md`, `CLAUDE.md` und deine Kapitel kannst du ins Git committen. `.gitignore` schließt `pdfs/`, `sessions/` und das Plugin-Cache aus — perfekt für Git-Workflows. Macht Rollback auf eine frühere Gliederung trivial.

### Einen Ordner pro Arbeit

Vermeide, dass sich zwei Thesen in einem Ordner kreuzen. Jede Arbeit bekommt einen eigenen Ordner mit eigenem `academic_context.md`. Das Plugin wird global geladen, aber der Kontext ist projekt-lokal — so entstehen keine Verwechslungen.

### Overhead in Nicht-Facharbeit-Projekten deaktivieren

Das Plugin wird global geladen — für Code-Projekte ist das meist unnötig. In `.claude/settings.local.json` im jeweiligen Projekt:

```json
{
  "enabledPlugins": {
    "academic-research@academic-research": false
  }
}
```

Die Datei ist via `.gitignore` nicht im Team-Repo — persönliche Override. Im Facharbeit-Ordner bleibt das Plugin default aktiv.

### Bestehenden Ordner nachträglich zur Facharbeit machen

```bash
cd ~/Pfad/zum/existierenden/Ordner
touch academic_context.md
```

Dann `/academic-research:setup`. Die Detection erkennt die Datei und zieht `CLAUDE.md`, `.gitignore`, Ordner idempotent nach — ohne vorhandene Daten zu überschreiben.

### Verwende `--mode quick` zum Screenen, `--mode deep` für Endgültiges

`quick` läuft nur auf 4 APIs (ohne Browser), liefert ~15 Paper — perfekt zum „mal reinschauen". `deep` macht systematisch auf allen 14 Quellen und dauert entsprechend länger.

### Bei Dead-Ends: Breitere Query

Wenn `/search` zu wenig liefert: keine Synonyme pressen, sondern einen allgemeineren Begriff. Oder `--no-expand` testen, um mit der Roh-Query zu suchen.

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
| `--no-expand` | `false` | Query-Generator-Agent überspringen, Roh-Query nutzen |
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

Nutzt die 5D-Scoring-Engine (siehe unten) und weist Cluster zu. Kann auf die letzte Session oder eine beliebige `papers.json` angewandt werden.

### `/academic-research:excel`

Professionelle Excel-Datei aus gescorten Papers generieren. **Benötigt das `document-skills`-Plugin.**

**Syntax:** `/academic-research:excel [--papers papers.json] [--output name.xlsx] [--context]`

Erzeugt 4 Sheets:

1. **Literaturübersicht** — Alle Papers mit 5D-Scores, Cluster-Farbcodierung, Score-Ampel
2. **Cluster-Analyse** — Statistik pro Cluster mit Balkendiagramm
3. **Kapitel-Zuordnung** — Papers zugeordnet zu Gliederungskapiteln (mit `--context`)
4. **Datenblatt** — Verstecktes Rohdaten-Sheet

### `/academic-research:setup`

Vollständiger Installer: venv, Python-Pakete, `browser-use`-CLI (Auto-Install via `uv`/`pipx`), Claude-Skill- und Plugin-Checks, Permissions, Projekt-Bootstrap. Idempotent — mehrfach aufrufbar.

### `/academic-research:history`

Zeigt vergangene Recherche-Sessions aus `~/.academic-research/sessions/`.

**Syntax:** `/academic-research:history [query | date | stats]`

- Ohne Argument: alle Sessions als Tabelle
- Mit Query-Text: Sessions nach Suchbegriff filtern
- Mit Datum: Details einer bestimmten Session
- `stats`: Aggregierte Statistiken

## Skills (13 selbstaktivierend)

Skills aktivieren sich **automatisch**, wenn Claude passende Keywords in der Konversation erkennt. Kein manueller Aufruf nötig — einfach natürlich formulieren.

### Kern-Skills (Thema → Kontext → Gliederung)

| Skill | Was es macht | Aktiviert bei | Ressourcen |
|-------|-------------|--------------|------------|
| **`academic-context`** | Bootet den akademischen Kontext (Thema, Forschungsfrage, Arbeitstyp, Methodik, Hochschule). Single Source of Truth in `./academic_context.md` für alle anderen Skills. | *„meine Arbeit"*, *„mein Thema"*, *„Thesis"*, *„Forschungsfrage"* | — |
| **`research-question-refiner`** | Verfeinert bestehende Forschungsfragen auf Spezifität, Beantwortbarkeit, Falsifizierbarkeit. Liefert 2–3 Alternativen pro Problem-Typ (zu weit / zu eng / nicht falsifizierbar). | *„Forschungsfrage formulieren"*, *„Fragestellung präzisieren"* | — |
| **`advisor`** | Baut, verfeinert und validiert Gliederungen und Exposés im Dialog. 7-Kriterien-PASS/FAIL-Check. | *„Gliederung"*, *„Exposé"*, *„Struktur"*, *„Kapitelplanung"* | `expose-template.md` |
| **`methodology-advisor`** | Berät bei der Methodenwahl mit 4-Dimensionen-Scoring (qualitativ, quantitativ, Mixed-Methods, Spezialverfahren). | *„welche Methodik"*, *„Forschungsdesign"*, *„qualitativ vs. quantitativ"* | `methodology-catalog.md` |

### Literatur-Skills (Quellen finden → bewerten → Lücken schließen)

| Skill | Was es macht | Aktiviert bei | Ressourcen |
|-------|-------------|--------------|------------|
| **`literature-gap-analysis`** | Per-Kapitel-Coverage-Bericht (Peer-Review-Anteil ≥ 80 %, Diversity ≥ 5 Autor\*innen-Gruppen, Recency ≥ 40 % ab 2020). Schlägt konkrete Such-Queries vor. | *„Literaturlücken"*, *„fehlende Quellen"*, *„Abdeckung prüfen"* | — |
| **`source-quality-audit`** | Bewertet Einzelquellen: Peer-Review-Status, Impact, Methodik, Predatory-Check. 5-Dimensionen-Score 0–100. | *„Quellenqualität"*, *„Peer-Review prüfen"*, *„Impact der Quelle"* | — |
| **`citation-extraction`** | Extrahiert Zitate aus PDFs via Citations-API, formatiert in APA7 / IEEE / Harvard / Chicago / DIN 1505 / BibTeX. Seitengenau. | *„Zitate finden"*, *„zitieren"*, *„Literaturverzeichnis erstellen"* | `references/<apa,harvard,chicago,din1505>.md` |

### Schreib-Skills (Kapitel → Stil → Plagiat)

| Skill | Was es macht | Aktiviert bei | Ressourcen |
|-------|-------------|--------------|------------|
| **`chapter-writer`** | Kapitel-Entwürfe (Einleitung, Theorieteil, Methodik, Empirie, Diskussion, Fazit) mit Zitaten aus `./literature_state.md`. | *„Kapitel schreiben"*, *„Einleitung"*, *„Theorieteil"*, *„Fazit"* | — |
| **`style-evaluator`** | 9-Metriken-Textanalyse + Anti-KI-Detection (Satzlänge, Passiv-Quote, Nominalstil, Füllwörter, Code-Switches). Rewrite-Vorschläge. | *„Stil prüfen"*, *„Schreibstil"*, *„KI-Erkennung"*, *„menschlich klingen"* | `references/<academic-de,academic-en>.md`, `scoring-rubric.md` |
| **`plagiarism-check`** | Textähnlichkeit via N-Gramm-Overlap gegen Quellen in `./literature_state.md`. Markiert unzureichend zitierte Paraphrasen. | *„Plagiat prüfen"*, *„Textähnlichkeit"*, *„zu nah am Original"* | — |

### Abschluss-Skills (Abstract → Titel → Abgabe)

| Skill | Was es macht | Aktiviert bei | Ressourcen |
|-------|-------------|--------------|------------|
| **`abstract-generator`** | Erzeugt Abstract (DE + EN), Keywords und Management-Summary aus fertiger Arbeit. IMRaD-konform. | *„Abstract schreiben"*, *„Zusammenfassung"*, *„Keywords"* | — |
| **`title-generator`** | 5–7 Titelvarianten (klassisch-akademisch, fragenbasiert, kreativ, ergebnisorientiert) mit Rationale und Stärke/Einschränkung. | *„Titel suchen"*, *„Titelvorschläge"*, *„Arbeitstitel"* | — |
| **`submission-checker`** | Formalia-Check vor Abgabe (Pflichtabschnitte, Seitenumfang, Formatierung, Quellenzahl, Erklärung). Default: FH Leibniz. | *„formale Prüfung"*, *„abgabefertig"*, *„Formatierung prüfen"* | `references/<fh-leibniz,uni-general,journal-ieee,journal-acm>.md` |

## Agents (4 LLM-Subagents)

Agents werden von Commands/Skills als Subagents gestartet für Aufgaben, die LLM-Urteilskraft erfordern.

| Agent | Model | Genutzt von | Aufgabe |
|-------|-------|-------------|---------|
| **`query-generator`** | Haiku | `/search` Command | Expandiert eine Suchanfrage in modulspezifische Suchbegriffe unter Berücksichtigung des Kontexts. |
| **`relevance-scorer`** | Sonnet | `/search` + `/score` Commands | Semantische Relevanz-Bewertung (0–1) in 10er-Batches mit Prompt-Caching. |
| **`quote-extractor`** | Sonnet | `citation-extraction` Skill | Extrahiert seitengenaue Zitate aus PDF-Volltext via Citations-API. |
| **`quality-reviewer`** | Sonnet | `chapter-writer`, `abstract-generator`, `advisor` | Evaluator-Optimizer-Pattern: prüft Output vor Finalisierung (`PASS` / `REVISE` + Fix-Liste). |

## Scripts (Python-Hintergrund)

Deterministische Logik ohne LLM-Aufruf, ausgeführt im isolierten venv unter `~/.academic-research/venv/`.

| Script | Funktion |
|--------|----------|
| `search.py` | API-Aufrufe an 7 Quellen parallel (CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz, EconStor, arXiv). |
| `dedup.py` | Deduplizierung nach DOI-Match + Titel-Ähnlichkeit (Levenshtein). |
| `pdf.py` | PDF-Download (5-Tier-Fallback) + Textextraktion (PyPDF2) + TF-IDF-Volltextindex. |
| `text_utils.py` | Shared Text-Utilities (Normalisierung, Tokenisierung). |
| `project_bootstrap.py` | Auto-Detect + Anlage der Facharbeit-Struktur (vom Setup aufgerufen). |
| `configure_permissions.py` | Trägt Bash-Permissions in `~/.claude/settings.local.json` ein. |
| `setup.sh` | Orchestriert den kompletten Setup-Flow. |

Frühere Skripte für Scoring, Zitatformatierung, Excel und Stil-Analyse wurden in Skills/Agents verlagert (siehe CHANGELOG v5.0.0).

## 5D-Scoring und Cluster

Jedes Paper wird nach 5 Dimensionen bewertet:

| Dimension | Gewicht | Berechnung |
|-----------|---------|------------|
| **Relevanz** | 35 % | Keyword-Match in Titel (70 %) + Abstract (30 %) + Phrasen-Bonus |
| **Aktualität** | 20 % | Exponentieller Verfall, 5-Jahre-Halbwertzeit |
| **Qualität** | 15 % | Zitationen/Jahr mit Log-Skalierung |
| **Autorität** | 15 % | Venue-Reputation (IEEE = 1.0, Mid = 0.7, Other = 0.4) |
| **Zugang** | 15 % | Open Access = 1.0, Institutional = 0.8, DOI = 0.5, URL = 0.2 |

### Cluster-Zuweisung

| Cluster | Kriterien | Beschreibung |
|---------|-----------|-------------|
| **Kernliteratur** | Score ≥ 0.75, Relevanz ≥ 0.80 | Muss zitiert werden |
| **Ergänzungsliteratur** | Score ≥ 0.50, Relevanz ≥ 0.50 | Unterstützend, Vertiefung |
| **Hintergrundliteratur** | Score ≥ 0.30 | Grundlagen, Standards |
| **Methodenliteratur** | Methodik-Keywords erkannt | Methodik-Begründung |

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

## Kontext-Dateien im Projekt

Der akademische Kontext liegt **git-versionierbar** im Projektordner (seit v5.3.0):

| Datei | Inhalt | Wird angelegt von |
|-------|--------|-------------------|
| `./academic_context.md` | Thesis-Profil, Gliederung, Forschungsfrage, Fortschritt | `academic-context` oder `/setup` |
| `./literature_state.md` | Literatur-Statistik, Kapitelzuordnung, Lücken | `citation-extraction` (lazy) |
| `./writing_state.md` | Aktuelles Kapitel, Wortzahl, Style-Scores | `chapter-writer` (lazy) |

Vor v5.3.0 lagen diese Dateien in Claude-Memory — die v5.3.0-Migration kopiert sie ins Projekt.

## Troubleshooting

### Venv-Pfad-Contract

Die Commands `/search` und `/history` erwarten die Python-Venv unter `~/.academic-research/venv/bin/python`. Dieser Pfad ist im `setup.sh` fest vorgegeben. Wer die Venv woanders anlegen möchte, muss `commands/search.md` und `commands/history.md` entsprechend patchen.

### Häufige Probleme

| Problem | Lösung |
|---------|--------|
| *„Python venv not found"* | `/academic-research:setup` ausführen |
| *„Missing dependencies"* | `~/.academic-research/venv/bin/pip install -r scripts/requirements.txt` |
| Browser-Module funktionieren nicht | `uv tool install browser-use && browser-use doctor` |
| Keine Ergebnisse bei Suche | Breitere Query verwenden; falls der `query-generator` zu eng expandiert hat: `--no-expand` setzen und mit der Roh-Query suchen |
| Excel leer | Zuerst `/academic-research:search` ausführen |
| Semantic Scholar 429-Fehler | `SS_API_KEY` Umgebungsvariable setzen |
| Skill triggert nicht automatisch | Keyword aus Trigger-Liste verwenden (siehe Skill-Tabelle) oder Skill explizit ansprechen (*„Nutze den advisor-Skill …"*) |
| `/academic-research:excel` scheitert mit *„document-skills nicht gefunden"* | `/plugin install document-skills@anthropic-agent-skills` |
| Kontext wird nicht geladen | `ls academic_context.md` — fehlt die Datei, `/academic-research:setup` in diesem Ordner laufen lassen |
| Plugin soll in Code-Projekten nicht mehr laden | In `.claude/settings.local.json` des Code-Projekts: `{"enabledPlugins": {"academic-research@academic-research": false}}` |

## Entwicklung und Evals

### Tests ausführen

```bash
~/.academic-research/venv/bin/pip install pytest
~/.academic-research/venv/bin/python -m pytest tests/ -v
```

Aktuell: **95 Tests grün**, inkl. Regression-Guards für Skill-Namen (`test_skill_naming.py`) und Cross-Referenzen (`test_cross_references.py`).

### Scoring anpassen

Die 5D-Scoring-Konfiguration ist inline im `relevance-scorer`-Agent dokumentiert.

### Evals (ab v5.2.0)

Pro Skill und Agent gibt es eine Evals-Suite unter `tests/evals/` mit zugehörigen JSON-Daten in `evals/<component>/`.

**Lokaler Lauf:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
~/.academic-research/venv/bin/python -m pytest tests/evals/ -v
```

- **Quality-Evals** vergleichen `with_skill` vs. `without_skill` und erwarten ≥ 20 Prozentpunkte PASS-Rate-Delta.
- **Trigger-Evals** prüfen Undertriggering (Recall ≥ 85 %) und Overtriggering (FPR ≤ 10 %) mit 20 Prompts pro Skill.

Kein CI-Trigger — Evals laufen lokal vor jedem Release; Reports werden unter `docs/evals/` committet (API-Kosten vermeiden).

## Was ist neu in v5?

**v5.0.0** (Breaking) — Architektur-Bereinigung:
- Browser-Automation auf `browser-use`-CLI umgestellt.
- Excel-Generierung an `document-skills:xlsx`-Plugin delegiert.
- Drei redundante Python-Skripte (`citations.py`, `style_analysis.py`, `ranking.py`) gelöscht.

**v5.0.1** — `/academic-research:setup` wurde One-Click-Installer (Auto-Install via `uv`/`pipx`).

**v5.1.x** — Anti-Fabrikations-Klauseln, Memory-Preconditions, Few-Shot-Paare, Umlaut-Varianten.

**v5.2.0** — Native Citations-API, Evals-Suite, `quality-reviewer`-Agent, Domain-organized References, Prompt-Caching.

**v5.3.0** (Breaking) — Projekt-Bootstrap + Kontext-Migration:
- `/academic-research:setup` erkennt leere Ordner und legt schlanke Facharbeit-Struktur an.
- Akademischer Kontext wandert von Claude-Memory in projekt-lokale Dateien.

**v5.4.0** — Final Review / Cookbook-Alignment:
- Skill-Namen auf kebab-case (Anthropic-Konvention).
- `## Übersicht` als erste H2 in allen 13 Skills.
- Few-Shot-Beispiele in 10 bisher few-shot-losen Skills.
- Cross-Referenzen in Prosa auf `` `kebab-case` ``.
- Dead Code weg (`settings.json`, `.mcp.json`, `templates/`, `config/scoring.yaml`).
- Neue Regression-Guards (`test_skill_naming`, `test_cross_references`).

Vollständige Migration siehe [CHANGELOG.md](CHANGELOG.md).

<details>
<summary>Historisch: Was v4 gegenüber v3 brachte</summary>

| Feature | v3 | v4 |
|---------|----|----|
| Architektur | Monolithische 7-Phasen-Pipeline | 13 modulare, selbstaktivierende Skills |
| Scoring | 4 Dimensionen | **5 Dimensionen** (+ Zugang) |
| Cluster | keine | **4 Cluster** (Kern/Ergänzung/Hintergrund/Methoden) |
| Excel | nicht vorhanden | **Professionelle Excel** (4 Sheets, Farben, Diagramme) |
| Stil-Prüfung | nicht vorhanden | **Anti-KI-Detection** (9 Metriken) |
| Zitierformate | nur BibTeX | **5 Formate** (APA7, IEEE, Harvard, Chicago, BibTeX) |
| Kontext | nur `config.local.md` | **Claude Memory** (in v5 projekt-lokal) |
| Auslösung | nur `/research`-Command | **Automatische Aktivierung** durch Konversation |

</details>

## Glossar (für Erstnutzer)

| Begriff | Was es bedeutet |
|---------|-----------------|
| **Abstract** | Kurzfassung der Arbeit (meist 150–300 Wörter), steht am Anfang. Enthält Thema, Methodik, Ergebnisse, Schlussfolgerung. |
| **IMRaD** | Standard-Struktur für wissenschaftliche Abstracts: **I**ntroduction, **M**ethods, **R**esults, **a**nd **D**iscussion. |
| **Peer-Review** | Wissenschaftlicher Gegenleseprozess: vor Publikation prüfen unabhängige Fach-Kolleg\*innen die Arbeit. Gilt als Qualitätssiegel. |
| **Predatory Journal** | Pseudo-wissenschaftliche Zeitschrift ohne seriöses Peer-Review; verlangt oft Gebühren und publiziert fast alles. Vermeiden. |
| **Exposé** | Kurzes Konzeptpapier (1–3 Seiten): Thema, Forschungsfrage, Methodik, Gliederung, Zeitplan. Üblich vor Bachelor-/Masterarbeiten. |
| **5D-Score** | Eigene Metrik dieses Plugins: Relevanz (35 %), Aktualität (20 %), Qualität (15 %), Autorität (15 %), Zugang (15 %). Ergibt 0–1. |
| **Cluster** | Gruppierung von Papern nach Rolle: Kern-, Ergänzungs-, Hintergrund-, Methodenliteratur. Hilft bei der Priorisierung. |
| **Skill** | Selbstaktivierende Claude-Erweiterung: Claude erkennt Keywords in deiner Nachricht und lädt die passende Anleitung automatisch. |
| **Agent** | LLM-Subprozess für spezielle Tasks (z. B. Relevanz-Bewertung). Wird von Commands oder Skills gestartet. |
| **Citations-API** | Anthropic-Feature: Claude markiert jede Aussage mit der Quell-Passage und Seitenzahl, statt frei zu formulieren. |
| **Prompt-Caching** | Wiederverwendet Teile des Prompts zwischen Aufrufen, spart Tokens und Zeit. Nutzt dieses Plugin für `relevance-scorer` und `quote-extractor`. |
| **HAN** | Hochschulauthentifizierungs-Netzwerk: Bibliotheks-Proxy für lizenzpflichtige Datenbanken (Springer, EBSCO, ProQuest). |
| **OPAC** | **O**nline **P**ublic **A**ccess **C**atalogue — Bibliothekskatalog einer Hochschule. |
| **BibTeX** | Textbasiertes Literatur-Format, primär für LaTeX. Andere Formate: APA7 (Psychologie/Sozialwiss.), IEEE (Technik), Harvard, Chicago, DIN 1505. |

## Lizenz und Weiterführendes

**Lizenz:** MIT (siehe [LICENSE](LICENSE))

**Plugin auf GitHub:** [github.com/jamski105/academic-research](https://github.com/jamski105/academic-research)

**Bug melden / Feature anfragen:** [GitHub Issues](https://github.com/jamski105/academic-research/issues)

**Referenzen:**

- [Anthropic Skill Spec](https://agentskills.io/specification) — offizielle Spec für Claude-Code-Skills.
- [Claude Code Plugins](https://code.claude.com/docs/en/plugins) — Plugin-Entwicklung und -Installation.
- [anthropics/skills Cookbook](https://github.com/anthropics/skills) — Referenz-Skills von Anthropic.
- [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) — Format für [CHANGELOG.md](CHANGELOG.md).
