# Architektur — Academic Research Plugin v3.0

Automatisierte akademische Literaturrecherche als Claude Code Plugin.
Das Plugin durchläuft 7 Phasen: Query-Expansion → Multi-Source-Suche →
Deduplizierung → 4D-Ranking → PDF-Download → Zitat-Extraktion → Export.
Deterministische Arbeit erledigen Python-Scripts, Urteilsaufgaben LLM-Agents.

---

## Komponentenmodell

```
User
  │
  ▼
Commands (/academic-research:*)         ← 7 Slash-Commands als Einstiegspunkte
  │
  ▼
Skill (/research)              ← Workflow-Orchestrierung (inline, nicht als Agent)
  │                               Parst Argumente, liest coordinator.md als Referenz
  │
  ├─► Subagents (Haiku/Sonnet) ← LLM-Tasks: Query-Expansion, Scoring, Extraktion
  ├─► Python Scripts            ← Deterministische Logik: API-Search, Ranking, Export
  └─► Playwright MCP            ← Browser-Automation für geschützte Quellen
        │
        ▼
      Config (YAML + Browser Guides)
```

**Commands** = User-Einstiegspunkte mit eigenen Tool-Permissions.
**Skill** = Orchestriert die 7-Phasen-Pipeline inline (liest `coordinator.md` als Referenz).
**Agents** = LLM-gesteuerte Tasks mit definiertem I/O-Format.
**Scripts** = Reproduzierbare Python-CLI-Tools, über venv ausgeführt.
**Config** = YAML-Registry für Module und Modi, Markdown-Guides für Browser-Navigation.

---

## 7-Phasen-Pipeline

| Phase | Beschreibung | Ausführung | Input | Output |
|-------|-------------|------------|-------|--------|
| 1 Setup | Session-Verzeichnis anlegen, Config laden | Coordinator | User-Query, Mode | `metadata.json` |
| 2 Query-Expansion | Suchbegriffe für jedes Modul generieren | `query-generator` (Haiku) | Query, Module-Liste | `queries.json` |
| 3A API-Suche | Parallele Abfrage aller API/OAI-PMH-Module | `search_apis.py` | Queries, Module-Liste | `api_results.json` |
| 3B Browser-Suche | Playwright-gesteuerte Suche (Scholar, EBSCO…) | `browser-searcher` (Sonnet) | Queries, Browser Guides | → append `api_results.json` |
| 3C Known-Works | Gezielte Suche nach bekannten Werken | `search_apis.py` | Known-Works-Queries | → merge `api_results.json` |
| 3D Deduplizierung | DOI/Titel-Matching, Merge der Ergebnisse | `deduplicator.py` | `api_results.json` | `deduped.json` |
| 4 Ranking | 4D-Score + LLM-Relevanz + Top-N-Selektion | `ranking.py` + `relevance-scorer` (Sonnet) | `deduped.json` | `ranked.json` → `papers.json` |
| 5 PDF-Download | 6-Tier-Strategie (API → Browser → HAN) | `pdf_resolver.py` + `browser-searcher` | `papers.json` | `pdfs/*.pdf`, `pdf_status.json` |
| 6 Zitat-Extraktion | PDF-Text extrahieren, Zitate finden | `quote-extractor` (Sonnet) | `pdf_texts.json` | `quotes.json` |
| 7 Export | BibTeX, JSON, Markdown + globaler Merge | `export.py`, `citation_manager.py`, `fulltext_index.py` | `papers.json`, `pdf_status.json`, `quotes.json` | `export.*`, `manual_acquisition.md`, `index.json` |

**Kernprinzip:** `papers.json` ist die kanonische Paperliste ab Phase 4 — alle folgenden Phasen lesen daraus.

**Metadata-Mode / `--no-pdfs`:** Phase 5 und 6 werden uebersprungen. Export enthalt nur Metadaten ohne Zitate.

---

## Datenfluss einer Session

```
Phase 1 ──► metadata.json
Phase 2 ──► queries.json
                │
Phase 3A ──► api_results.json ◄── Phase 3B (append)
                │                    ◄── Phase 3C (merge)
Phase 3D ──► deduped.json
                │
Phase 4  ──► ranked.json ──► papers.json  (Top N: quick=15, standard=25, deep=40)
                                │
Phase 5  ──► pdf_status.json    │
             pdfs/*.pdf         │
                │               │
Phase 6  ──► pdf_texts.json ──► quotes.json
                                │
Phase 7  ──► export.json        │
             export.bib         │
             export.md          │
             manual_acquisition.md  (falls PDFs fehlen)
             index.json         (Session-Index aktualisiert)
```

---

## Agents

| Agent | Model | Aufgabe | Input | Output |
|-------|-------|---------|-------|--------|
| `coordinator` | Opus | 7-Phasen-Referenzdokument (wird von Skill inline gelesen, nicht als Agent gespawnt) | — | — |
| `query-generator` | Haiku | Query → modulspezifische Suchbegriffe | Query, Module-Liste | `queries.json` |
| `browser-searcher` | Sonnet | Playwright-Suche + PDF-Download via Browser | Query/Papers, Browser Guides | Paper-JSON / PDFs |
| `relevance-scorer` | Sonnet | Semantische Relevanz-Bewertung (10er-Batches) | Papers + Query | Scores (0–1) |
| `quote-extractor` | Sonnet | Zitate aus PDF-Text extrahieren (max 3 parallel) | PDF-Text + Query | Zitat-Array |
| `review-writer` | Opus | Literaturreview-Generierung (on demand) | Papers + Quotes | Markdown-Review |

Alle Subagents werden mit `IGNORE ALL PRIOR CONVERSATION CONTEXT` gestartet, um Context-Bleeding zu verhindern.

---

## Python Scripts

| Script | Wichtigste Args | Liest | Schreibt |
|--------|----------------|-------|----------|
| `search_apis.py` | `--query`, `--modules`, `--limit`, `--output` | — | `api_results.json` |
| `deduplicator.py` | `--papers`, `--output` | `api_results.json` | `deduped.json` |
| `ranking.py` | `--papers`, `--query`, `--mode`, `--output`, `--w-{relevance,recency,quality,authority}` | `deduped.json` | `ranked.json` |
| `pdf_resolver.py` | `--papers`, `--output-dir`, `--output`, `--email` | `papers.json` | `pdf_status.json`, `pdfs/*.pdf` |
| `export.py` | `--session-dir`, `--format`, `--pdf-status` | `papers.json`, `pdf_status.json`, `quotes.json` | `export.*`, `manual_acquisition.md` |
| `citation_manager.py` | `--action {list,add,tag,note,export,search,merge}`, `--session-dir`, `--tag`, `--doi`, `--format`, `--output` | `papers.json` | `~/.academic-research/citations.bib` |
| `fulltext_index.py` | `--action {index,search}`, `--pdf-dir`, `--query`, `--limit` | `pdfs/*.pdf` | `~/.academic-research/fulltext_index.json` |

Alle Scripts laufen über `~/.academic-research/venv/bin/python`. Setup via `/academic-research:setup` (`scripts/setup.sh`).
Ausfuehrliche Anleitung: `setup-guide.md`

---

## Suchmodule

Definiert in `config/search_modules.yaml`. Drei Typen:

| Typ | Ausführung | Module |
|-----|-----------|--------|
| **api** | `search_apis.py` (httpx) | CrossRef, OpenAlex, Semantic Scholar, BASE, EconBiz |
| **oai-pmh** | `search_apis.py` (XML) | EconStor |
| **browser** | `browser-searcher` (Playwright) | Google Scholar, RePEc, OECD, EBSCO, Springer, OPAC, EZB*, Destatis*, ProQuest* |

*\* = standardmäßig deaktiviert*

**Tier 1** (frei / institutioneller Direktzugang): Alle Module außer ProQuest.
**Tier 2** (erfordert HAN-Server-Proxy): ProQuest.

Mode-Aktivierung: `quick` = 3 APIs · `standard` = alle Tier 1 · `deep` = alle Tiers.
Details: `config/search_modules.yaml`

---

## 4D-Ranking

```
Score = 0.4 × Relevanz + 0.2 × Aktualität + 0.2 × Qualität + 0.2 × Autorität
```

| Dimension | Berechnung | Bereich |
|-----------|-----------|---------|
| **Relevanz** | Keyword-Abdeckung: Titel (70%) + Abstract (30%) | 0–1 |
| **Aktualität** | Exponentieller Decay, Halbwertszeit 5 Jahre: `2^(-(Δ/5))` | 0–1 |
| **Qualität** | Zitationen/Jahr mit Log-Skalierung: `log(cit_per_year+1) / log(201)` | 0–1 |
| **Autorität** | Venue-Heuristik: Top (IEEE, ACM…) = 1.0, Mid = 0.7, Sonstige = 0.4 | 0–1 |

**Stufe 2: LLM-Relevanz** (nach 4D-Scoring, via `relevance-scorer` Agent):
- Semantische Bewertung durch Sonnet in 10er-Batches
- Score wird in Gesamtranking gemergt (Re-Ranking)

**Deep-Mode Portfolio-Adjustments** (nach 4D + LLM Scoring):
- Venue-Konzentration: −0.05 ab dem 4. Paper derselben Venue
- Source-Diversität: +0.03 für unterrepräsentierte Suchmodule

Details: `config/research_modes.yaml`

---

## PDF-Resolution (6 Tiers)

| Tier | Quelle | Methode | Automatisiert |
|------|--------|---------|---------------|
| 1 | Unpaywall | API (DOI → OA-URL) | ✅ `pdf_resolver.py` |
| 2 | CORE | API (DOI → Download-URL) | ✅ `pdf_resolver.py` |
| 3 | Modul-OA-URLs | Aus Suchergebnis-Metadaten | ✅ `pdf_resolver.py` |
| 4 | Direkt-URL | URL endet auf `.pdf` | ✅ `pdf_resolver.py` |
| 5 | EBSCO / Springer / EZB | Browser via HAN/OAuth/IP | 🔧 `browser-searcher` |
| 6 | ProQuest | Browser via HAN (Dissertationen) | 🔧 `browser-searcher` |

Tiers 1–4 laufen immer. Tiers 5–6 nur in `standard`/`deep` Mode fuer fehlgeschlagene Papers.

Die PDF-Resolution ist modular aufgebaut. Neue Download-Wege koennen ueber Browser Guides
hinzugefuegt werden — siehe `adding-browser-modules.md`.

---

## Persistenz

**Session-Daten** — pro Recherche unter `~/.academic-research/sessions/<timestamp>/`:
```
metadata.json, queries.json, api_results.json, deduped.json,
ranked.json, papers.json, pdf_status.json, pdf_texts.json,
quotes.json, export.json, export.bib, export.md,
manual_acquisition.md, pdfs/
```

**Globale Daten** — unter `~/.academic-research/`:
```
citations.bib          ← Globale Zitationsdatenbank (Merge aller Sessions)
annotations.json       ← Manuelle Notizen/Tags zu Papers
fulltext_index.json    ← Volltextindex über alle PDFs
sessions/index.json    ← Session-Verzeichnis für /academic-research:history
config.local.md        ← User-Konfiguration (Uni, Disziplin, Stil)
venv/                  ← Python Virtual Environment
```

---

## Fehlerbehandlung

**Kernprinzip:** "Log and continue" — keine Phase bricht den gesamten Workflow ab.

| Fehlertyp | Strategie |
|-----------|-----------|
| Script non-zero Exit | stderr loggen, nächste Phase fortsetzen |
| Agent-Timeout | Fallback (z.B. nur 4D-Score ohne LLM-Relevanz) |
| Keine Papers gefunden | User informieren, breiteren Query vorschlagen |
| Keine PDFs downloadbar | Metadaten + Zitationen trotzdem exportieren |
| HAN-Login-Timeout | Tier 5–6 überspringen, mit vorhandenen PDFs fortfahren |
| Alle Module fehlgeschlagen | Exit Code 1, Fehlerdetails pro Modul anzeigen |

---

## Browser Guides

Vorgefertigte Navigationsanleitungen fuer den `browser-searcher` Agent.
Liegen unter `config/browser_guides/` und beschreiben Schritt fuer Schritt,
wie eine bestimmte Datenbank per Playwright MCP durchsucht wird.

Browser-Module sind **modular**: Neue Quellen koennen ohne Code-Aenderung hinzugefuegt werden.
Anleitung: `adding-browser-modules.md`

| Guide | Datenbank | Besonderheit |
|-------|-----------|-------------|
| `ebscohost.md` | EBSCO Publication Finder (Journal-Verzeichnis) | Gastzugang, Datenbank-Links via HAN. React-SPA mit CSS Modules — nur `data-auto`-Attribute als Selektoren |
| `springer.md` | Springer Nature | Suche frei (`.app-card-open` Cards), Volltext via HAN. Cookie-Consent erforderlich |
| `google_scholar.md` | Google Scholar | Anti-Scraping, DE/EN Locale-Handling. Citations via Regex-Filter |
| `repec.md` | IDEAS/RePEc | Form-POST Suche (`htsearch2`), kein URL-Zugang. `downfree`/`downnone` CSS-Klassen |
| `oecd.md` | OECD (ehem. iLibrary) | SPA (React/Next.js), BEM-Selektoren. Domain: `oecd.org` (nicht `oecd-ilibrary.org`) |
| `han_login.md` | HAN-Server (generisch) | Mehrstufiger Microsoft OAuth (DE Locale). Redirect-Kette: HAN → OpenID → Microsoft |
| `proquest.md` | ProQuest | Dissertationen, Tier 2. `.resultItem` + `.truncatedResultsTitle`. Cookie-Banner |
| `destatis.md` | Destatis | Statistiken (deaktiviert) |
| `opac.md` | Leibniz FH OPAC | Bibliothekskonto-Login, GBV PICA System. Gateway zu EBSCO/Springer/ProQuest via HAN |

---

## Commands

Vollstaendige Kommandoreferenz mit allen Flags: `command-reference.md`

| Command | Beschreibung |
|---------|-------------|
| `/research "query"` | 7-Phasen-Recherche (Flags: `--mode`, `--style`, `--modules`, `--no-pdfs`) |
| `/academic-research:setup` | Python-Umgebung einrichten (venv, Dependencies) |
| `/academic-research:context` | Akademisches Profil konfigurieren (Uni, Disziplin, Stil) |
| `/academic-research:cite` | Zitationen verwalten (list, search, export, add, tag, note) |
| `/academic-research:history` | Vergangene Sessions anzeigen |
| `/academic-research:review` | Literaturreview aus Session(s) generieren |
| `/academic-research:recommend` | Paper-Empfehlungen basierend auf Recherche-Historie |
| `/academic-research:search-pdfs` | Volltextsuche ueber alle heruntergeladenen PDFs |

---

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| `setup-guide.md` | Systemvoraussetzungen, Installation, Playwright MCP, Troubleshooting |
| `command-reference.md` | Alle Commands, Flags und Syntax |
| `adding-browser-modules.md` | Anleitung: Neue Browser-Module hinzufuegen |
| `../README.md` | Uebersicht, Installation, Quick Start |
