# Setup Guide — Academic Research Plugin

Ausfuehrliche Anleitung zu Systemvoraussetzungen, Installation und Troubleshooting.

---

## Systemvoraussetzungen

| Voraussetzung | Version | Wofuer | Ohne geht... |
|---|---|---|---|
| **Claude Code** | aktuell | Plugin-Host, LLM-Orchestrierung | Gar nichts |
| **Python** | 3.10+ | API-Suche, PDF-Parsing, Ranking, Export | Gar nichts |
| **Node.js / npx** | 18+ | Playwright MCP starten, Chromium installieren | Nur API-Module (`--mode quick`) |
| **Playwright Chromium** | (auto) | Browser-basierte Suche (Scholar, EBSCO, Springer...) | Nur API-Module (`--mode quick`) |

**Nicht benoetigt:**
- Kein Google Chrome / kein eigener Browser — Playwright bringt einen eigenen Chromium mit
- Kein globales Python-Package-Management — alles laeuft im isolierten venv
- Keine Datenbank — alles sind JSON-Dateien in `~/.academic-research/`

### Voraussetzungen pruefen

```bash
python3 --version   # ≥ 3.10
node --version      # ≥ 18.0
npx --version       # kommt mit Node.js
```

**macOS:** Python 3 kommt mit Xcode Command Line Tools (`xcode-select --install`) oder via Homebrew (`brew install python`). Node.js via Homebrew (`brew install node`) oder nvm.

**Linux:** `sudo apt install python3 python3-venv nodejs npm` (Debian/Ubuntu) oder aequivalent.

**Windows:** WSL2 empfohlen. Python und Node.js via System-Installer oder winget.

---

## Installation Schritt fuer Schritt

### Schritt 1: Plugin registrieren

```bash
claude plugin install academic-research
```

Das registriert das Plugin in Claude Code:
- Liest `.claude-plugin/plugin.json` (Manifest: Name, Version, Beschreibung)
- Registriert alle Slash-Commands aus `commands/` (z.B. `/research`, `/academic:setup`)
- Laedt Agents aus `agents/`, Skills aus `skills/`, Hooks aus `hooks/`
- Wendet Tool-Permissions aus `settings.json` an (z.B. Python-Scripts ohne Nachfrage)

**Zu diesem Zeitpunkt ist noch nichts installiert** — kein Python-Environment, keine Dependencies, kein Browser. Das Plugin ist nur *registriert*.

Fuer lokale Entwicklung alternativ:
```bash
claude --plugin-dir ./academic-research
```

### Schritt 2: Setup ausfuehren

```bash
/academic:setup
```

Das fuehrt `scripts/setup.sh` aus und erledigt alles Weitere automatisch:

#### 2a: Verzeichnisstruktur anlegen

```
~/.academic-research/
├── sessions/         ← Recherche-Sessions (eine pro /research Aufruf)
├── pdfs/             ← Heruntergeladene PDFs
├── citations.bib     ← Globale Zitationsdatenbank
├── annotations.json  ← Tags und Notizen zu Papers
├── fulltext_index.json ← Volltextindex ueber alle PDFs
└── sessions/index.json ← Session-Verzeichnis fuer /academic:history
```

#### 2b: Python Virtual Environment

```bash
python3 -m venv ~/.academic-research/venv
```

Erstellt eine **isolierte Python-Installation** unter `~/.academic-research/venv/`.
Damit kollidieren die Plugin-Dependencies nicht mit anderen Python-Projekten auf dem System.

Alle Python-Scripts des Plugins laufen ueber `~/.academic-research/venv/bin/python` —
nie ueber das System-Python.

#### 2c: Python-Dependencies

```bash
~/.academic-research/venv/bin/pip install httpx PyPDF2
```

Nur 2 Packages (definiert in `scripts/requirements.txt`):

| Package | Version | Wofuer |
|---|---|---|
| **httpx** | ≥ 0.25.0 | HTTP-Client fuer alle API-Aufrufe (CrossRef, OpenAlex, Semantic Scholar, Unpaywall, CORE, BASE, EconBiz, EconStor) |
| **PyPDF2** | ≥ 3.0.0 | PDF-Text-Extraktion fuer Volltextindex und Zitat-Extraktion |

#### 2d: Playwright Chromium (optional, aber empfohlen)

```bash
npx playwright install chromium --with-deps
```

- **`chromium`** — Playwright laedt eine speziell gebaute Chromium-Version herunter (~150-200 MB)
- **`--with-deps`** — installiert System-Dependencies die Chromium braucht (auf Linux: `libx11`, `libgbm`, etc.; auf macOS typischerweise nicht noetig)

**Dieser Schritt braucht Node.js/npx.** Falls nicht vorhanden, zeigt das Setup:
```
⚠️  Node.js/npx not found — browser search modules will not work
    Install Node.js 18+ and rerun /academic:setup
```

---

## Playwright MCP — wie funktioniert das?

Playwright MCP ist ein **MCP-Server** (Model Context Protocol), der Claude Code erlaubt, einen echten Browser zu steuern. Zwei Komponenten arbeiten zusammen:

### Der MCP-Server

In der Claude Code MCP-Konfiguration (`.claude.json` oder globale Settings) ist der Playwright MCP-Server registriert:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

Claude Code startet diesen Server **automatisch beim Sessionstart** via `npx`. Der Server stellt Tools bereit:

| Tool | Funktion |
|---|---|
| `browser_navigate` | URL oeffnen |
| `browser_snapshot` | Accessibility Tree der Seite lesen |
| `browser_evaluate` | JavaScript auf der Seite ausfuehren (Daten extrahieren) |
| `browser_click` | Element anklicken |
| `browser_fill_form` | Formularfelder ausfuellen |
| `browser_wait_for` | Auf Element/Zustand warten |

### Der Chromium-Browser

Playwright bringt seinen **eigenen Chromium** mit — unabhaengig von Chrome, Firefox, Safari auf dem System. Vorteile:

- **Reproduzierbar:** Immer dieselbe Browser-Version, egal was auf dem System installiert ist
- **Headless:** Laeuft unsichtbar im Hintergrund, kein Fenster noetig
- **Steuerbar:** Volle Kontrolle ueber Navigation, Cookies, Formulare

### Der Flow im Betrieb

```
Claude Code startet
  │
  ├─► Playwright MCP Server startet (npx @playwright/mcp)
  │     └─► Chromium-Instanz bereit (headless)
  │
  └─► User: /research "query" --mode standard
        │
        ├─► Phase 3A: API-Module (Python, kein Browser noetig)
        │
        └─► Phase 3B: Browser-Module
              │
              ├─► browser-searcher Agent erhaelt Browser-Guide (z.B. google_scholar.md)
              ├─► browser_navigate → https://scholar.google.com/scholar?q=query
              ├─► browser_snapshot → Accessibility Tree lesen
              ├─► browser_evaluate → JavaScript: Ergebnisse aus DOM extrahieren
              └─► Ergebnisse als Paper-JSON zurueck an Coordinator
```

---

## Graceful Degradation

Das Plugin ist so gebaut, dass es auch mit Teilinstallation funktioniert:

| Szenario | Was funktioniert | Was fehlt |
|---|---|---|
| **Volle Installation** | Alles: 14 Module, 6-Tier PDF, Browser-Suche | — |
| **Ohne Node.js / Playwright** | API-Module: CrossRef, OpenAlex, S2, BASE, EconBiz, EconStor. PDF Tiers 1-4. `--mode quick` | Browser-Module: Google Scholar, EBSCO, Springer, OPAC, RePEc, OECD. PDF Tiers 5-6 |
| **Ohne HAN-Server** | Alle Tier-1-Module, freie PDFs | ProQuest (Tier 2), lizenzierter Volltext (Springer E-Books) |

Das Setup-Script gibt Feedback:
```
✅ Python environment: ready
✅ Playwright (Chromium): ready
```
oder:
```
✅ Python environment: ready
⚠️  Node.js/npx not found — browser search modules will not work
```

---

## Troubleshooting

### `python3: command not found`

Python 3 ist nicht installiert.

- **macOS:** `xcode-select --install` oder `brew install python`
- **Linux:** `sudo apt install python3 python3-venv`

### `npx: command not found`

Node.js ist nicht installiert. Browser-Module funktionieren nicht, aber API-Suche geht trotzdem.

- **macOS:** `brew install node`
- **Linux:** `sudo apt install nodejs npm`
- Alternative: [nvm](https://github.com/nvm-sh/nvm) fuer versionsunabhaengige Installation

### `Playwright browser install failed`

Chromium konnte nicht installiert werden.

```bash
# Manuell versuchen mit Ausgabe:
npx playwright install chromium --with-deps

# Oder nur Chromium ohne System-Dependencies:
npx playwright install chromium
```

Auf Linux fehlen moeglicherweise System-Libraries:
```bash
# Debian/Ubuntu:
sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxdamage1
```

### `pip install` schlaegt fehl

```bash
# venv manuell neu erstellen:
rm -rf ~/.academic-research/venv
python3 -m venv ~/.academic-research/venv
~/.academic-research/venv/bin/pip install httpx PyPDF2
```

### Plugin-Commands nicht verfuegbar

```bash
# Plugin-Registrierung pruefen:
claude plugin list

# Neu registrieren:
claude plugin install academic-research
```

---

## Deinstallation

```bash
# Plugin aus Claude Code entfernen:
claude plugin uninstall academic-research

# Alle Daten loeschen (Sessions, PDFs, Zitationen):
rm -rf ~/.academic-research
```
