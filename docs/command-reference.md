# Kommandoreferenz — Academic Research Plugin

Vollstaendige Uebersicht aller Commands und Flags.

---

## /research "query"

Hauptcommand: Startet die 7-Phasen-Recherche-Pipeline.

**Syntax:** `/research "query" [--mode MODE] [--style STYLE] [--modules LIST] [--no-pdfs] [--no-browser]`

| Flag | Werte | Default | Beschreibung |
|------|-------|---------|-------------|
| `--mode` | `quick`, `standard`, `deep`, `metadata` | `standard` | Recherche-Tiefe und Modulauswahl |
| `--style` | `apa7`, `ieee`, `harvard`, `mla`, `chicago` | `apa7` (oder aus Config) | Zitationsstil fuer Export |
| `--modules` | Komma-getrennte Liste | (aus Mode) | Nur bestimmte Module nutzen |
| `--no-pdfs` | (Flag, kein Wert) | `false` | Kein PDF-Download, keine Zitat-Extraktion |
| `--no-browser` | (Flag, kein Wert) | `false` | Alle Browser-Module ueberspringen (Phase 3B + Tiers 5-6); nur API-Suche |

**Beispiele:**
```bash
/research "DevOps Governance"
/research "Machine Learning Testing" --mode deep --style ieee
/research "AI Ethics" --modules semantic_scholar,crossref,base
/research "Cloud Computing" --no-pdfs
/research "Wirtschaftsinformatik" --mode metadata
/research "Network Security" --no-browser
```

### Research Modes

| Mode | Module | Top-N | Zeitlimit | PDF | Zitate | Einsatz |
|------|--------|-------|-----------|-----|--------|---------|
| `quick` | 3 APIs (CrossRef, OpenAlex, S2) | 15 | 60s | Ja | Ja | Schnelle Uebersicht |
| `standard` | Alle Tier 1 (6 API + 6 Browser) | 25 | 180s | Ja | Ja | Standard-Recherche |
| `deep` | Alle Tiers inkl. HAN | 40 | 300s | Ja | Ja | Systematische Reviews |
| `metadata` | Alle Tier 1 | 25 | 90s | Nein | Nein | Reine Literaturliste |

---

## /academic-research:setup

Richtet die Python-Umgebung und Playwright ein.

**Syntax:** `/academic-research:setup`

Keine Flags. Fuehrt automatisch aus:
1. Erstellt `~/.academic-research/` Verzeichnis
2. Erstellt Python venv
3. Installiert Dependencies (httpx, PyPDF2)
4. Installiert Playwright Chromium

Ausfuehrliche Anleitung mit Systemvoraussetzungen, Playwright-Erklaerung und Troubleshooting: `setup-guide.md`

---

## /academic-research:context

Konfiguriert das akademische Profil (interaktiv).

**Syntax:** `/academic-research:context [university name]`

| Argument | Optional | Beschreibung |
|----------|----------|-------------|
| University name | Ja | Vorausfuellung des Universitaetsnamens |

Fragt interaktiv nach:
- Universitaet
- Studiengang / Disziplin
- Zitationsstil (Default fuer `/research`)
- Ausgabesprache
- HAN-Server (aktiviert/deaktiviert)
- Bevorzugte Module

Speichert nach: `~/.academic-research/config.local.md`

---

## /academic-research:cite [action]

Verwaltet Zitationen, Tags und Notizen.

**Syntax:** `/academic-research:cite ACTION [--doi DOI] [--tag TAG] [--note "TEXT"] [--format FORMAT] [--output FILE]`

### Actions

| Action | Beschreibung | Beispiel |
|--------|-------------|---------|
| `list` | Alle Papers anzeigen | `/academic-research:cite list` |
| `list --tag TAG` | Nach Tag filtern | `/academic-research:cite list --tag important` |
| `list --status STATUS` | Nach Status filtern | `/academic-research:cite list --status unread` |
| `search "query"` | Volltextsuche in Zitationen | `/academic-research:cite search "governance"` |
| `export` | Bibliographie exportieren | `/academic-research:cite export --format bibtex` |
| `add DOI` | Paper manuell hinzufuegen | `/academic-research:cite add 10.1109/ICSE.2023.00042` |
| `tag PAPER_ID "tag"` | Tag vergeben | `/academic-research:cite tag paper_123 "important"` |
| `note PAPER_ID "text"` | Notiz hinzufuegen | `/academic-research:cite note paper_123 "Kapitel 3"` |

### Export-Formate

| Format | Beschreibung |
|--------|-------------|
| `bibtex` | BibTeX (.bib) |
| `apa7` | Formatierter APA7-Text |
| `ieee` | Formatierter IEEE-Text |

---

## /academic-research:history

Zeigt vergangene Recherche-Sessions.

**Syntax:** `/academic-research:history [query | date | stats]`

| Argument | Beschreibung | Beispiel |
|----------|-------------|---------|
| (keins) | Alle Sessions auflisten | `/academic-research:history` |
| `"query"` | Sessions nach Query durchsuchen | `/academic-research:history "DevOps"` |
| `YYYY-MM-DD` | Session von bestimmtem Datum | `/academic-research:history 2026-03-17` |
| `stats` | Aggregierte Statistiken | `/academic-research:history stats` |

---

## /academic-research:review

Generiert einen Literaturreview-Entwurf.

**Syntax:** `/academic-research:review [SESSION_ID] [--sessions "id1,id2"] [--style STYLE]`

| Flag | Werte | Default | Beschreibung |
|------|-------|---------|-------------|
| `SESSION_ID` | Timestamp | Letzte Session | Bestimmte Session |
| `--sessions` | Komma-getrennte Timestamps | — | Mehrere Sessions kombinieren |
| `--style` | `narrative`, `systematic`, `thematic` | `narrative` | Review-Stil |

**Beispiele:**
```bash
/academic-research:review
/academic-research:review 2026-03-17_14-30-00
/academic-research:review --sessions "2026-03-17,2026-03-15" --style thematic
```

---

## /academic-research:recommend

Paper-Empfehlungen basierend auf Recherche-Historie.

**Syntax:** `/academic-research:recommend [SESSION_ID]`

| Argument | Optional | Beschreibung |
|----------|----------|-------------|
| `SESSION_ID` | Ja | Empfehlungen nur fuer bestimmte Session |

Nutzt Co-Citation-Analyse via Semantic Scholar API.
Zeigt Top 10 empfohlene Papers.

---

## /academic-research:search-pdfs "query"

Volltextsuche ueber alle heruntergeladenen PDFs.

**Syntax:** `/academic-research:search-pdfs "query" [--limit N]`

| Flag | Default | Beschreibung |
|------|---------|-------------|
| `--limit` | `10` | Maximale Anzahl Treffer |

**Beispiel:**
```bash
/academic-research:search-pdfs "machine learning" --limit 20
```

---

## Globale Konfiguration

Alle Defaults koennen ueber `/academic-research:context` gesetzt werden.
Inline-Flags ueberschreiben immer die Config-Defaults.

**Prioritaet:** Inline-Flag > config.local.md > Plugin-Default

**Config-Datei:** `~/.academic-research/config.local.md`
**Beispiel:** `examples/academic-research.local.md`