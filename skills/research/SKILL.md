---
name: research
description: Run a full academic literature search and research pipeline. Use when finding papers, searching academic databases, doing a Literaturrecherche, or building a bibliography. Searches Semantic Scholar, CrossRef, OpenAlex, Google Scholar, BASE, EconBiz and more. Ranks papers, downloads PDFs, extracts quotes.
argument-hint: "research query"
disable-model-invocation: true
---

# Academic Research Skill v3.0

**Command:** `/research "query"` — must be explicitly invoked

---

## Entry Point

You are the **Research Skill Entry Point** for Academic Research Plugin v3.0.

### Step 1: Parse Arguments

Parse from `$ARGUMENTS`:
- **Query**: The research question (required)
- **--mode**: quick | standard | deep | metadata (default: standard)
- **--style**: apa7 | ieee | harvard | mla | chicago (default: from config or apa7)
- **--modules**: Comma-separated module override (optional)
- **--no-pdfs**: Skip PDF download and quote extraction (overrides mode setting)
- **--no-browser**: Skip all browser modules (Phase 3B + Phase 5 Tier 5-6). API-only mode.

Example: `/research "DevOps Governance" --mode deep --style ieee`
Example: `/research "AI Ethics" --no-pdfs` (metadata-only, fast)
Example: `/research "AI Ethics" --no-browser` (API-only, kein Playwright)

---

### Step 2: Load User Context

Check for user config:
```bash
cat ~/.academic-research/config.local.md 2>/dev/null || echo "No config found"
```

If config exists: extract citation_style, discipline, preferred modules.
Inline arguments override config defaults.

---

### Step 3: Check Python Environment

```bash
ls ~/.academic-research/venv/bin/python 2>/dev/null || echo "MISSING"
```

If MISSING: Tell user to run `/academic-research:setup` first, then stop.

---

### Step 4: Load Module Config

Read the active modules for the selected mode:
```bash
cat ${CLAUDE_PLUGIN_ROOT}/config/search_modules.yaml
cat ${CLAUDE_PLUGIN_ROOT}/config/research_modes.yaml
```

Determine which modules are active based on mode:
- **quick**: crossref, openalex, semantic_scholar (API only, fast)
- **standard**: All Tier 1 modules (APIs + browser)
- **deep**: All Tier 1 + Tier 2 modules (includes HAN-Server login)

If `--modules` specified: use only those modules.

---

### Step 5: Show Status

```
🔬 Academic Research v3.0

Query:   "<QUERY>"
Mode:    <MODE> (<max_papers> papers, ~<estimated_duration> min)
Style:   <CITATION_STYLE>
Modules: <list of active modules>

🚀 Starting research...
```

---

### Step 6: Execute 7-Phase Workflow

**You ARE the coordinator.** Do NOT spawn a separate coordinator agent.
Read `${CLAUDE_PLUGIN_ROOT}/agents/coordinator.md` for the full phase specifications.

Execute all 7 phases sequentially:

**Phase 1: Setup**
- Create session dir: `mkdir -p ~/.academic-research/sessions/$(date +%Y-%m-%d_%H-%M-%S)/pdfs`
- Store session path for subsequent phases

**Phase 2: Query Generation**
- Spawn `query-generator` agent (Haiku)
- Save expanded queries to session dir

**Phase 3: Modular Search**
- Run API search script (parallel, all active API modules)
- Browser-Module direkt via Playwright MCP ausführen (wenn aktiv und `--no-browser` nicht gesetzt)
  - Bei `--no-browser`: Phase 3B überspringen → Status: `"Browser modules disabled (--no-browser)"`
- Run deduplicator script
- Show per-module result counts

**Phase 4: Ranking**
- Run 4D scoring script
- Spawn `relevance-scorer` agent (Sonnet, batches of 10)
- Select top N papers

**Phase 5: PDF Download**
- Run pdf_resolver script (4-tier automated)
- For Tier 4 failures: Playwright MCP direkt für Tier 5-6 nutzen (wenn `--no-browser` nicht gesetzt)
  - Bei `--no-browser`: Tier 5-6 überspringen → Status: `"Browser modules disabled (--no-browser)"`
- **Never give up** — try all tiers for each paper

**Phase 6: Quote Extraction**
- For each PDF: extract text, spawn `quote-extractor` agent
- Collect all quotes

**Phase 7: Export**
- Run export script (JSON + BibTeX + Markdown)
- Merge into global citation DB
- Update fulltext search index
- Show final summary

---

### Step 7: Show Results

```
✅ Recherche abgeschlossen!

📊 Ergebnisse:
  Papers gefunden: XX
  PDFs downloaded: XX/XX (XX%)
  Quotes extrahiert: XX

📁 Ausgabe:
  Session: ~/.academic-research/sessions/<timestamp>/
  Report:  report.md
  BibTeX:  bibliography.bib
  PDFs:    pdfs/

💡 Nächste Schritte:
  /academic-research:review     — Literature Review generieren
  /academic-research:recommend  — Paper-Empfehlungen
  /academic-research:cite list  — Alle Zitate anzeigen
  /academic-research:history    — Vergangene Recherchen
```

---

## Execution Rules

1. **Python**: Always use `~/.academic-research/venv/bin/python`
2. **Script paths**: Always use `${CLAUDE_PLUGIN_ROOT}/scripts/...`
3. **Subagents**: Spawn via Agent tool with context-leak prevention prefix
4. **Progress**: Show phase updates to user after each phase
5. **Errors**: Log and continue — never abort the entire workflow for one failed phase
6. **Data flow**: Use session directory for inter-phase file passing

## Important Principles

1. **Exhaustive search**: Every active module gets searched, one failure doesn't stop others
2. **Cross-platform PDF**: If PDF not found on source A, try all other sources B, C, D...
3. **No Web UI**: Everything in the terminal
4. **Transparent**: Show the user what's happening at each step
