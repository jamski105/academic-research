---
name: research
description: Academic research — searches across Semantic Scholar, CrossRef, OpenAlex, Google Scholar, BASE, EconBiz and more. Ranks papers, downloads PDFs, extracts quotes.
argument-hint: [research query]
---

# Academic Research Skill v3.0

**Command:** `/research "query"` or auto-triggered for academic research questions

---

## Entry Point

You are the **Research Skill Entry Point** for Academic Research Plugin v3.0.

### Step 1: Parse Arguments

Parse from `$ARGUMENTS`:
- **Query**: The research question (required)
- **--mode**: quick | standard | deep (default: standard)
- **--style**: apa7 | ieee | harvard | mla | chicago (default: from config or apa7)
- **--modules**: Comma-separated module override (optional)

Example: `/research "DevOps Governance" --mode deep --style ieee`

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

If MISSING: Tell user to run `/academic:setup` first, then stop.

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
- Spawn `query_generator` agent (Haiku)
- Save expanded queries to session dir

**Phase 3: Modular Search**
- Run API search script (parallel, all active API modules)
- Spawn `browser_searcher` agent (if browser modules active)
- Run deduplicator script
- Show per-module result counts

**Phase 4: Ranking**
- Run 5D scoring script
- Spawn `relevance_scorer` agent (Sonnet, batches of 10)
- Select top N papers

**Phase 5: PDF Download**
- Run pdf_resolver script (4-tier cross-platform)
- For Tier 4 failures: spawn `browser_searcher` for browser download
- **Never give up** — try all modules for each paper

**Phase 6: Quote Extraction**
- For each PDF: extract text, spawn `quote_extractor` agent
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
  /academic:review     — Literature Review generieren
  /academic:recommend  — Paper-Empfehlungen
  /academic:cite list  — Alle Zitate anzeigen
  /academic:history    — Vergangene Recherchen
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
