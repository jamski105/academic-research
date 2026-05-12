# Vault Phase 2 — W2-A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle Lese-/Schreibpfade in quote-extractor, citation-extraction und chapter-writer auf Vault-MCP-Tool-Calls umstellen, sodass kein direkter PDF- oder literature_state.md-Schreibpfad mehr in den Primärworkflows existiert.

**Architecture:** Markdown-Datei-Edits an drei bestehenden Skill/Agent-Dateien + ein neues Export-Skript. Kein Build-System. Smoke-Checks via grep. Token-Count nach jeder chapter-writer-Änderung prüfen.

**Tech Stack:** Markdown (Skill/Agent-Instruktionen), Node.js ESM (Export-Skript), Bash (Smoke-Checks), git.

---

## File Map

| Datei | Änderungstyp | Verantwortlichkeit |
|---|---|---|
| `agents/quote-extractor.md` | Modify | vault.ensure_file() als Primärpfad; vault.add_quote() als Persistenz; base64 bleibt Fallback |
| `skills/citation-extraction/SKILL.md` | Modify | §2–3 auf vault.find_quotes()/get_quote() umstellen; §7 kein Schreiben in literature_state.md |
| `skills/chapter-writer/SKILL.md` | Modify | §1 Kontext laden via vault.search()+vault.find_quotes(); literature_state.md nur noch Snapshot-Hinweis |
| `scripts/export-literature-state.mjs` | Create | Vault-Snapshot → ./literature_state.md schreiben |
| `scripts/export-literature-state.sh` | Create | Thin-Wrapper um das .mjs-Skript |
| `docs/AUDIT-v6-vault.md` | Modify | §5 Phase 2 Status-Marker auf "implemented" |

---

## Task 1: quote-extractor — vault.ensure_file() als Primärpfad

**Files:**
- Modify: `agents/quote-extractor.md` — Abschnitt "Quellen-Bindung via Citations-API"

**TDD-Light-Ansatz:** Da kein Unit-Test-Framework existiert, ist der "failing test" ein grep-Smoke-Check, der den alten Zustand beweist, dann der neue Zustand nach der Änderung geprüft wird.

- [ ] **Step 1: Smoke-Check Ist-Zustand dokumentieren**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "ensure_uploaded\|files_api_helper\|pdf_status.json" agents/quote-extractor.md
```

Erwartung: Mindestens 2 Treffer (alter `ensure_uploaded`-Pfad referenziert `scripts/files_api_helper.py`).

- [ ] **Step 2: Abschnitt "Quellen-Bindung via Citations-API" ersetzen**

Ersetze in `agents/quote-extractor.md` den Abschnitt "API-Call-Schema (Files-API, Primärpfad)" durch die folgende Vault-Version. Der base64-Fallback bleibt unverändert erhalten.

Alter Text (zu ersetzen, Zeilen ~49–68):
```markdown
**API-Call-Schema (Files-API, Primärpfad):**
```python
# file_id einmalig hochladen, dann cachen (scripts/files_api_helper.py)
file_id = ensure_uploaded(pdf_path, client)  # cached in pdf_status.json

client.beta.messages.create(
    model="claude-sonnet-4-6",
    system=[{
        "type": "text",
        "text": AGENT_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }],
    documents=[{
        "type": "document",
        "source": {"type": "file", "file_id": file_id},
        "citations": {"enabled": True},
    }],
    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    messages=[{"role": "user", "content": f"Extrahiere 2 Zitate zur Query '<query>', max 25 Woerter."}],
)
```

**Fallback (base64) wenn Feature-Flag OFF oder `ensure_uploaded()` gibt `None` zurück:**
```

Neuer Text:
```markdown
**API-Call-Schema (Files-API via Vault, Primärpfad):**
```python
# file_id aus Vault holen (gecacht, kein Re-Upload wenn TTL gültig)
file_id = vault.ensure_file(paper_id)  # MCP-Tool-Call

client.beta.messages.create(
    model="claude-sonnet-4-6",
    system=[{
        "type": "text",
        "text": AGENT_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }],
    documents=[{
        "type": "document",
        "source": {"type": "file", "file_id": file_id},
        "citations": {"enabled": True},
    }],
    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    messages=[{"role": "user", "content": f"Extrahiere 2 Zitate zur Query '<query>', max 25 Woerter."}],
)
```

**Fallback (base64) wenn `vault.ensure_file()` `None` zurückgibt oder Vault nicht verfügbar:**
```

- [ ] **Step 3: Feature-Flag-Zeile anpassen**

Ändere die Feature-Flag-Zeile (aktuell ~Zeile 88):
```
**Feature-Flag:** `ACADEMIC_FILES_API=0` → base64-Fallback ohne API-Overhead.
`should_use_files_api()` aus `scripts/files_api_helper.py` prüft das Flag.
```

Neue Version:
```
**Feature-Flag:** `ACADEMIC_FILES_API=0` → base64-Fallback ohne API-Overhead.
Vault-Verfügbarkeit: `vault.ensure_file()` gibt `None` zurück wenn kein file_id
im Cache → automatischer Fallback auf base64.
```

- [ ] **Step 4: Smoke-Check neuer Zustand**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "vault.ensure_file" agents/quote-extractor.md
grep -n "ensure_uploaded\|files_api_helper\|pdf_status.json" agents/quote-extractor.md
```

Erwartung: `vault.ensure_file` mindestens 1 Treffer. `ensure_uploaded`/`files_api_helper`/`pdf_status.json` 0 Treffer.

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add agents/quote-extractor.md
git commit -m "feat(v6.0/W2-A): quote-extractor — vault.ensure_file() als PDF-Primärpfad"
```

---

## Task 2: quote-extractor — vault.add_quote() als Persistenz-Pfad

**Files:**
- Modify: `agents/quote-extractor.md` — neuer Abschnitt "Vault-Persistenz" nach dem Output-Format-Abschnitt

- [ ] **Step 1: Smoke-Check Ist-Zustand**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "vault.add_quote\|add_quote\|JSON.*schreib\|write.*json" agents/quote-extractor.md
```

Erwartung: `vault.add_quote` 0 Treffer (noch nicht vorhanden).

- [ ] **Step 2: Neuen Abschnitt "Vault-Persistenz" nach "## Output-Format" einfügen**

Füge nach dem `## Output-Format`-Abschnitt (nach Zeile ~147 "...`citation-extraction`-Skill, die zitierte Stelle seitengenau nachzuschlagen.") folgenden neuen Abschnitt ein:

```markdown
---

## Vault-Persistenz

Nach der Extraktion **jeden** Quote via `vault.add_quote()` persistieren:

```python
quote_id = vault.add_quote(
    paper_id=paper_id,               # aus dem Input-Objekt
    verbatim=quote["text"],          # exakter Wortlaut
    extraction_method="citations-api",
    api_response_id=response.id,     # Anthropic Request-ID aus der API-Antwort
    pdf_page=quote["page"],          # aus citations[].start_page_number
    section=quote["section"],
    context_before=quote["context_before"],
    context_after=quote["context_after"],
)
```

**Wichtig:**
- `api_response_id` ist **Pflicht** bei `extraction_method="citations-api"` —
  der Vault wirft einen Fehler wenn das Feld leer ist.
- Die zurückgegebene `quote_id` in das Output-JSON aufnehmen:
  jedes Quote-Objekt erhält ein zusätzliches Feld `"vault_quote_id": "<uuid>"`.
- Kein JSON-File schreiben — der Vault ist der einzige Persistenz-Pfad.

**Output-Ergänzung (quote-Objekt):**
```json
{
  "text": "Governance frameworks ensure DevOps compliance across distributed teams.",
  "page": 3,
  "section": "Introduction",
  "word_count": 10,
  "relevance_score": 0.95,
  "reasoning": "Directly addresses governance in DevOps context",
  "context_before": "Large organizations face challenges...",
  "context_after": "This requires clear policy definition...",
  "vault_quote_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```
```

- [ ] **Step 3: Cache-Strategie-Abschnitt anpassen**

Im Abschnitt "Cache-Strategie (Prompt-Caching fuer Batch-PDFs)" (Zeile ~183ff.)
den Python-Code-Block aktualisieren, sodass er `vault.ensure_file(paper_id)` statt
`ensure_uploaded(pdf_path, client)` verwendet:

Alter Code-Block:
```python
client.beta.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {
            "type": "text",
            "text": "<Agent-System-Prompt>",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ],
    # Cache-Breakpoint ist VOR documents[] — der Agent-Prompt wird gecacht,
    # das PDF-Dokument variiert pro Call ohne Cache-Invalidierung.
    documents=[{"type": "document", "source": {"type": "file", "file_id": file_id}, "citations": {"enabled": true}}],
    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    messages=[{"role": "user", "content": f"Extrahiere 2 Zitate zur Query '{query}'"}],
)
```

Neuer Code-Block:
```python
file_id = vault.ensure_file(paper_id)  # gecacht im Vault, kein Re-Upload

client.beta.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {
            "type": "text",
            "text": "<Agent-System-Prompt>",
            "cache_control": {"type": "ephemeral", "ttl": "1h"},
        }
    ],
    # Cache-Breakpoint ist VOR documents[] — der Agent-Prompt wird gecacht,
    # das PDF-Dokument variiert pro Call ohne Cache-Invalidierung.
    documents=[{"type": "document", "source": {"type": "file", "file_id": file_id}, "citations": {"enabled": true}}],
    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    messages=[{"role": "user", "content": f"Extrahiere 2 Zitate zur Query '{query}'"}],
)
```

- [ ] **Step 4: tools-Frontmatter aktualisieren**

Frontmatter-Zeile aktuell: `tools: [Read]`

Vault-Tool-Calls brauchen MCP-Zugriff. Ändere:
```yaml
tools: [Read, mcp__academic_vault__vault_ensure_file, mcp__academic_vault__vault_add_quote]
```

- [ ] **Step 5: Smoke-Check neuer Zustand**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "vault.add_quote" agents/quote-extractor.md
grep -n "api_response_id" agents/quote-extractor.md
grep -n "vault_quote_id" agents/quote-extractor.md
```

Erwartung: Je mindestens 1 Treffer.

- [ ] **Step 6: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add agents/quote-extractor.md
git commit -m "feat(v6.0/W2-A): quote-extractor — vault.add_quote() Persistenz + api_response_id"
```

---

## Task 3: citation-extraction — Vault-Lesepfad (vault.find_quotes / vault.get_quote)

**Files:**
- Modify: `skills/citation-extraction/SKILL.md` — §2 PDFs lokalisieren, §3 Zitat-Extraktion, §7 Literaturstatus

- [ ] **Step 1: Smoke-Check Ist-Zustand**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "pdf_text\|pdfs/\|literature_state.md.*chreib\|Schreiben.*literature" skills/citation-extraction/SKILL.md
grep -n "vault.find_quotes\|vault.get_quote" skills/citation-extraction/SKILL.md
```

Erwartung: Erste Zeile mehrere Treffer (alter PDF-Pfad), zweite Zeile 0 Treffer.

- [ ] **Step 2: Abschnitt "## Kontext-Dateien" ersetzen**

Alter Text:
```markdown
## Kontext-Dateien

- Lesen: `./academic_context.md` (Zitationsstil), `./literature_state.md` (Quellen, PDFs)
- Schreiben: `./literature_state.md` (Zitatanzahl, Extraktionsstatus aktualisieren)
```

Neuer Text:
```markdown
## Kontext-Dateien

- Lesen: `./academic_context.md` (Zitationsstil)
- Vault-Queries: `vault.find_quotes(paper_id, query)` für Zitate,
  `vault.get_quote(quote_id)` für Volldetails
- `./literature_state.md` nur lesen (read-only Snapshot-Export aus dem Vault —
  für manuellen Überblick; nicht schreiben)
```

- [ ] **Step 3: §2 "PDFs lokalisieren" ersetzen**

Alter Text (§2, Zeilen ~72–75):
```markdown
### 2. PDFs lokalisieren

Lies `./literature_state.md`, um zu ermitteln, welche Paper ein heruntergeladenes PDF haben. PDFs liegen unter `~/.academic-research/sessions/*/pdfs/`.

Verweist der User auf Paper ohne PDFs, biete an, `/search` zu triggern, um sie zu finden und herunterzuladen.
```

Neuer Text:
```markdown
### 2. Relevante Paper aus Vault laden

Rufe `vault.search(query, k=5)` auf, um die relevantesten Paper-IDs zur
Recherche-Query zu ermitteln. Für jeden Paper-ID:

1. `vault.find_quotes(paper_id, query=research_query, k=10)` aufrufen →
   liefert `[{quote_id, verbatim, pdf_page, section, ...}]`
2. Für detaillierte Zitat-Metadaten: `vault.get_quote(quote_id)`

Sind für ein Paper noch keine Vault-Zitate vorhanden (leere Liste), den
`quote-extractor`-Agent spawnen, um Zitate aus dem PDF zu ziehen und via
`vault.add_quote()` zu persistieren. PDFs werden via `vault.ensure_file(paper_id)`
als `file_id` übergeben — kein direktes `pdf_path` im Context.
```

- [ ] **Step 4: §3 "Zitat-Extraktion" anpassen**

Ersetze das Input-JSON für den quote-extractor-Agent-Spawn (Zeilen ~79–92):

Alter Text:
```markdown
Für jedes PDF den Agent `quote-extractor` spawnen (definiert in `${CLAUDE_PLUGIN_ROOT}/agents/quote-extractor.md`). Übergebe:

```json
{
  "paper": {
    "title": "Paper Title",
    "doi": "10.xxxx/xxxxx",
    "pdf_text": "...extracted PDF text..."
  },
  "research_query": "derived from chapter title or user query",
  "max_quotes": 3,
  "max_words_per_quote": 25
}
```
```

Neuer Text:
```markdown
Wenn Vault-Zitate für ein Paper vorhanden sind, diese direkt verwenden — kein
Agent-Spawn nötig.

Fehlen Vault-Zitate, den Agent `quote-extractor` spawnen (definiert in
`${CLAUDE_PLUGIN_ROOT}/agents/quote-extractor.md`). Übergebe:

```json
{
  "paper": {
    "paper_id": "mueller2023",
    "title": "Paper Title",
    "doi": "10.xxxx/xxxxx"
  },
  "research_query": "derived from chapter title or user query",
  "max_quotes": 3,
  "max_words_per_quote": 25
}
```

Der `quote-extractor`-Agent holt das PDF via `vault.ensure_file(paper_id)` —
kein `pdf_text` im Context mehr nötig. Extrahierte Zitate werden vom Agent
automatisch via `vault.add_quote()` persistiert und mit `vault_quote_id` im
Output zurückgegeben.
```

- [ ] **Step 5: §7 "Literaturstatus aktualisieren" ersetzen**

Alter Text (§7, Zeilen ~144–150):
```markdown
### 7. Literaturstatus aktualisieren

Nach Extraktion und Formatierung:

1. `./literature_state.md` lesen (veraltete Überschreibungen vermeiden)
2. Pro-Quelle-Felder aktualisieren: Zitatanzahl, Extraktionsqualität, zugewiesene Kapitel
3. Aggregierte Statistiken aktualisieren: extrahierte Zitate gesamt, Coverage-Prozentsatz
```

Neuer Text:
```markdown
### 7. Literaturstatus

Nach Extraktion und Formatierung: Der Vault ist die Quelle der Wahrheit.
`./literature_state.md` ist ein read-only Snapshot-Export — nicht beschreiben.

Zum Regenerieren des Snapshots:
```bash
node scripts/export-literature-state.mjs
```

Der Snapshot dient nur zur manuellen Übersicht. Zitatanzahlen und Coverage
werden im Vault über `vault.stats()` abgefragt.
```

- [ ] **Step 6: Smoke-Check neuer Zustand**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
grep -n "vault.find_quotes\|vault.get_quote\|vault.search\|vault.ensure_file" skills/citation-extraction/SKILL.md
grep -n "pdf_text\|pdfs/" skills/citation-extraction/SKILL.md
```

Erwartung: Erste Zeile >= 4 Treffer. Zweite Zeile 0 Treffer.

- [ ] **Step 7: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add skills/citation-extraction/SKILL.md
git commit -m "feat(v6.0/W2-A): citation-extraction — Vault-Lesepfad via find_quotes/get_quote"
```

---

## Task 4: chapter-writer — vault.search() + vault.find_quotes() statt literature_state.md

**Files:**
- Modify: `skills/chapter-writer/SKILL.md` — §"Kontext-Dateien", §1 "Kontext laden", §3 "Kapitelplanung", §"Zitat-Einbindung via Citations-API"

- [ ] **Step 1: Smoke-Check Ist-Zustand + Token-Baseline**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
wc -w skills/chapter-writer/SKILL.md
grep -n "literature_state.md" skills/chapter-writer/SKILL.md
grep -n "vault.search\|vault.find_quotes" skills/chapter-writer/SKILL.md
```

Erwartung: `literature_state.md` mehrere Treffer (Lesen UND Schreiben), `vault` 0 Treffer.
Wortanzahl notieren als Baseline.

- [ ] **Step 2: "## Kontext-Dateien" ersetzen**

Alter Text:
```markdown
## Kontext-Dateien

- Lesen: `./academic_context.md` (Forschungsfrage, Gliederung), `./literature_state.md` (Quellen), `./writing_state.md` (Fortschritt)
- Schreiben: `./writing_state.md` — Wortzahlen und Kapitelstatus aktualisieren
```

Neuer Text:
```markdown
## Kontext-Dateien

- Lesen: `./academic_context.md` (Forschungsfrage, Gliederung, Zitationsstil),
  `./writing_state.md` (Fortschritt)
- Vault-Queries: `vault.search(query, k=5)` für relevante Paper,
  `vault.find_quotes(paper_id, query, k=3)` für Zitat-Kandidaten
- Schreiben: `./writing_state.md` — Wortzahlen und Kapitelstatus aktualisieren
- `./literature_state.md` nicht laden (ist read-only Snapshot — bei Bedarf
  via `node scripts/export-literature-state.mjs` regenerieren)
```

- [ ] **Step 3: §1 "Kontext laden" ersetzen**

Alter Text (§1, Zeilen ~80–83):
```markdown
### 1. Kontext laden

Lies alle drei Kontext-Dateien. Fehlt `./academic_context.md`: `academic-context`-Skill triggern. Fehlt Gliederung: `advisor`-Skill vorschlagen. Extrahiere Ziel-Kapitel, Quellen, Zitationsstil, Sprache, vorhandene Entwürfe.
```

Neuer Text:
```markdown
### 1. Kontext laden

Lies `./academic_context.md` und `./writing_state.md`.
Fehlt `./academic_context.md`: `academic-context`-Skill triggern.
Fehlt Gliederung: `advisor`-Skill vorschlagen.

Quellen nicht aus `literature_state.md` laden — stattdessen Vault-Queries
verwenden (Schritt 3 unten). So werden nur relevante Quellen geladen,
nicht die komplette Literaturliste.
```

- [ ] **Step 4: §3 "Kapitelplanung" um Vault-Quellen-Mapping ergänzen**

Im Abschnitt "### 3. Kapitelplanung" (nach "Bevor geschrieben wird, erstelle einen kurzen internen Plan:")
den Schritt "2. **Quellen-Mapping**" ersetzen:

Alter Text:
```markdown
2. **Quellen-Mapping** — Welche Quellen stützen welche Abschnitte
```

Neuer Text:
```markdown
2. **Quellen-Mapping via Vault** — Vault-Queries pro Unterabschnitt:
   ```
   vault.search("<Kapitelthema>", k=5)
   → [paper_id, snippet] für relevante Paper

   vault.find_quotes(paper_id, query="<Unterabschnitts-Frage>", k=3)
   → [verbatim, page, quote_id] für Zitat-Kandidaten
   ```
   Ergebnis: maximal ~1700 Token Quellen-Kontext statt vollständigem
   `literature_state.md`-Dump (~8–15 k Token).
```

- [ ] **Step 5: §"Zitat-Einbindung via Citations-API" (Workflow) ersetzen**

Alter Workflow-Block (Zeilen ~185–192):
```markdown
**Workflow:**
1. `./literature_state.md` lesen — welche PDFs liegen im Session-Pfad?
2. API-Call mit `documents[]`-Anhaengen, `citations.enabled: true`
3. Output-Text enthaelt `citations[]`-Bloecke — diese im Kapitel-Text als Inline-Zitate nach Variant-Zitierstil (aus `./academic_context.md`) rendern.

**Fallback:** Sind keine PDFs verfuegbar (nur Metadaten), nutze den herkoemmlichen Prompt-Workflow aus dem vorangehenden Abschnitt.
```

Neuer Text:
```markdown
**Workflow:**
1. `vault.search("<Kapitelthema>", k=5)` → relevante `paper_id`s
2. Pro paper_id: `vault.find_quotes(paper_id, query, k=3)` → Zitat-Kandidaten
3. Pro Paper: `vault.ensure_file(paper_id)` → `file_id` für Citations-API
4. API-Call mit `documents[]` (file_id), `citations.enabled: true`
5. Output-Text enthält `citations[]`-Blöcke — als Inline-Zitate nach
   Variant-Zitierstil aus `./academic_context.md` rendern.

**Fallback:** Gibt `vault.ensure_file()` `None` zurück (kein PDF im Vault),
nutze den Vault-Zitat-Text (`verbatim`) direkt als Prompt-basiertes Zitat
ohne Citations-API-Erzwingung.
```

- [ ] **Step 6: Smoke-Check neuer Zustand + Token-Count**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
wc -w skills/chapter-writer/SKILL.md
grep -n "vault.search\|vault.find_quotes\|vault.ensure_file" skills/chapter-writer/SKILL.md
grep -c "literature_state.md" skills/chapter-writer/SKILL.md
```

Erwartung:
- `vault.*` >= 5 Treffer
- `literature_state.md` Vorkommen: nur noch 1 (der read-only-Hinweis), nicht als Primär-Lese-Anweisung
- Wortanzahl: notieren für PR-Body Token-Vergleich

- [ ] **Step 7: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add skills/chapter-writer/SKILL.md
git commit -m "feat(v6.0/W2-A): chapter-writer — vault.search()+find_quotes() statt literature_state.md"
```

---

## Task 5: scripts/export-literature-state.mjs erstellen

**Files:**
- Create: `scripts/export-literature-state.mjs`
- Create: `scripts/export-literature-state.sh`

- [ ] **Step 1: Smoke-Check — Datei existiert noch nicht**

```bash
ls /Users/j65674/Repos/academic-research-W2-A/scripts/export-literature-state.mjs 2>&1
```

Erwartung: "No such file or directory"

- [ ] **Step 2: export-literature-state.mjs erstellen**

Erstelle `scripts/export-literature-state.mjs` mit folgendem Inhalt:

```javascript
#!/usr/bin/env node
/**
 * export-literature-state.mjs
 *
 * Generiert ./literature_state.md als read-only Snapshot-Export aus dem Vault.
 * Aufruf: node scripts/export-literature-state.mjs [--output ./literature_state.md]
 *
 * Voraussetzungen:
 *   - academic-vault MCP-Server läuft (python -m mcp.academic_vault.server)
 *   - VAULT_DB_PATH gesetzt oder vault.db im CWD
 *
 * Hinweis: Dieses Skript ruft den Vault direkt via Python-Modul auf,
 * da kein MCP-HTTP-Client in diesem Repo verfügbar ist.
 * Für MCP-basierte Umgebungen: vault.search() + vault.get_paper() Tool-Calls verwenden.
 */

import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const OUTPUT_PATH = process.argv[2] === "--output"
  ? resolve(process.argv[3] ?? "./literature_state.md")
  : resolve("./literature_state.md");

const VAULT_DB = process.env.VAULT_DB_PATH ?? "vault.db";

/**
 * Ruft ein Python-Snippet gegen den Vault auf und gibt JSON zurück.
 */
function vaultQuery(pythonSnippet) {
  const script = `
import sys, json
sys.path.insert(0, '.')
from mcp.academic_vault.server import search_papers, get_paper, find_quotes, get_stats
${pythonSnippet}
`;
  try {
    const result = execSync(`python3 -c "${script.replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`, {
      env: { ...process.env, VAULT_DB_PATH: VAULT_DB },
      encoding: "utf-8",
    });
    return JSON.parse(result.trim());
  } catch (e) {
    console.error("[export-literature-state] Vault-Query fehlgeschlagen:", e.message);
    return null;
  }
}

/**
 * Holt alle Paper aus dem Vault (via FTS5-Wildcard-Suche).
 */
function getAllPapers() {
  return vaultQuery(`
db_path = '${VAULT_DB}'
try:
    from mcp.academic_vault.db import VaultDB
    db = VaultDB(db_path)
    conn = VaultDB._open(db_path)
    rows = conn.execute("SELECT paper_id, csl_json, pdf_path, file_id, type FROM papers ORDER BY added_at DESC").fetchall()
    conn.close()
    print(json.dumps([dict(r) for r in rows]))
except Exception as e:
    print(json.dumps([]))
`);
}

/**
 * Holt Zitat-Count pro Paper.
 */
function getQuoteCount(paperId) {
  return vaultQuery(`
db_path = '${VAULT_DB}'
try:
    from mcp.academic_vault.db import VaultDB
    conn = VaultDB._open(db_path)
    row = conn.execute("SELECT COUNT(*) as cnt FROM quotes WHERE paper_id = ?", ('${paperId}',)).fetchone()
    conn.close()
    print(json.dumps(row['cnt'] if row else 0))
except Exception as e:
    print(json.dumps(0))
`);
}

function formatPaperEntry(paper, quoteCount) {
  let csl = {};
  try { csl = JSON.parse(paper.csl_json); } catch {}

  const title = csl.title ?? paper.paper_id;
  const authors = (csl.author ?? [])
    .map(a => `${a.family ?? ""}${a.given ? `, ${a.given}` : ""}`)
    .join("; ") || "Unbekannt";
  const year = csl.issued?.["date-parts"]?.[0]?.[0] ?? "o.J.";
  const doi = csl.DOI ?? paper.doi ?? "";
  const pdfStatus = paper.file_id
    ? `gecacht (file_id: ${paper.file_id.slice(0, 8)}…)`
    : paper.pdf_path
    ? `lokal: ${paper.pdf_path}`
    : "kein PDF";

  return `### ${paper.paper_id}

- **Titel:** ${title}
- **Autoren:** ${authors}
- **Jahr:** ${year}
${doi ? `- **DOI:** ${doi}\n` : ""}- **PDF-Status:** ${pdfStatus}
- **Zitate im Vault:** ${quoteCount ?? 0}
`;
}

// --- Main ---

console.log("[export-literature-state] Lese Vault:", VAULT_DB);

const papers = getAllPapers();

if (!papers || papers.length === 0) {
  console.warn("[export-literature-state] Keine Paper im Vault gefunden. Snapshot leer.");
  const empty = `# Literatur-Snapshot\n\n_Generiert via \`node scripts/export-literature-state.mjs\` — ${new Date().toISOString()}_\n\n> Vault enthält noch keine Paper. Bitte zuerst \`vault.add_paper()\` aufrufen.\n`;
  writeFileSync(OUTPUT_PATH, empty, "utf-8");
  process.exit(0);
}

const lines = [
  "# Literatur-Snapshot",
  "",
  `> **Read-only Export** aus dem Vault — generiert ${new Date().toISOString()}`,
  `> Vault: \`${VAULT_DB}\` · ${papers.length} Paper`,
  "> Zum Regenerieren: \`node scripts/export-literature-state.mjs\`",
  "> **Nicht manuell bearbeiten** — Änderungen werden beim nächsten Export überschrieben.",
  "",
  "---",
  "",
];

for (const paper of papers) {
  const quoteCount = getQuoteCount(paper.paper_id);
  lines.push(formatPaperEntry(paper, quoteCount));
}

const content = lines.join("\n");
writeFileSync(OUTPUT_PATH, content, "utf-8");
console.log(`[export-literature-state] Snapshot geschrieben: ${OUTPUT_PATH} (${papers.length} Paper)`);
```

- [ ] **Step 3: export-literature-state.sh erstellen**

Erstelle `scripts/export-literature-state.sh` mit folgendem Inhalt:

```bash
#!/usr/bin/env bash
# export-literature-state.sh — Thin-Wrapper um export-literature-state.mjs
# Aufruf: ./scripts/export-literature-state.sh [--output ./literature_state.md]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node "${SCRIPT_DIR}/export-literature-state.mjs" "$@"
```

```bash
chmod +x /Users/j65674/Repos/academic-research-W2-A/scripts/export-literature-state.sh
```

- [ ] **Step 4: Smoke-Check — Skript ist syntaktisch valide**

```bash
node --input-type=module --check < /Users/j65674/Repos/academic-research-W2-A/scripts/export-literature-state.mjs && echo "SYNTAX OK"
```

Erwartung: "SYNTAX OK" (kein Fehler).

- [ ] **Step 5: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add scripts/export-literature-state.mjs scripts/export-literature-state.sh
git commit -m "feat(v6.0/W2-A): scripts/export-literature-state — Vault-Snapshot-Exporter"
```

---

## Task 6: AUDIT-v6-vault.md §5 Status-Marker setzen

**Files:**
- Modify: `docs/AUDIT-v6-vault.md` — §5 Phase 2

- [ ] **Step 1: Phase-2-Block lokalisieren**

```bash
grep -n "Phase 2\|phase 2\|Skill-Anpassung" /Users/j65674/Repos/academic-research-W2-A/docs/AUDIT-v6-vault.md
```

Erwartung: Zeilen mit "Phase 2 — Skill-Anpassung" sichtbar.

- [ ] **Step 2: Phase-2-Marker hinzufügen**

Ersetze im §5-Block den Phase-2-Eintrag:

Alter Text:
```markdown
**Phase 2 — Skill-Anpassung (Sprint v6.0)**
- `quote-extractor` schreibt in `vault.add_quote()` statt JSON-File
- `chapter-writer` liest via `vault.find_quotes()`
- Hook für Verbatim-Validation
```

Neuer Text:
```markdown
**Phase 2 — Skill-Anpassung (Sprint v6.0)** ✅ implementiert in W2-A (feat/v6.0-W2-A)
- `quote-extractor` schreibt in `vault.add_quote()` statt JSON-File ✅
- `chapter-writer` liest via `vault.find_quotes()` + `vault.search()` ✅
- PDFs via `vault.ensure_file()` als file_id ✅
- `literature_state.md` nur noch read-only Snapshot-Export ✅
- Hook für Verbatim-Validation → Phase 2b / W2-B (#64)
```

- [ ] **Step 3: Smoke-Check**

```bash
grep -n "implementiert\|W2-A" /Users/j65674/Repos/academic-research-W2-A/docs/AUDIT-v6-vault.md
```

Erwartung: Mindestens 1 Treffer mit "W2-A".

- [ ] **Step 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git add docs/AUDIT-v6-vault.md
git commit -m "docs(v6.0/W2-A): AUDIT-v6-vault §5 Phase 2 als implementiert markieren"
```

---

## Task 7: Gesamtverifikation + Token-Count für PR-Body

**Files:** keine neuen Änderungen — nur Verifikation

- [ ] **Step 1: Alle AC grep-Checks ausführen**

```bash
cd /Users/j65674/Repos/academic-research-W2-A

echo "=== AC-1: quote-extractor vault.ensure_file ===" && grep -n "vault.ensure_file" agents/quote-extractor.md
echo "=== AC-2: quote-extractor vault.add_quote + api_response_id ===" && grep -n "vault.add_quote\|api_response_id" agents/quote-extractor.md
echo "=== AC-3: citation-extraction vault calls ===" && grep -n "vault.find_quotes\|vault.get_quote\|vault.search" skills/citation-extraction/SKILL.md
echo "=== AC-4: citation-extraction kein pdf_text/pdfs/ ===" && grep -n "pdf_text\|pdfs/" skills/citation-extraction/SKILL.md || echo "CLEAN"
echo "=== AC-5: chapter-writer vault calls ===" && grep -n "vault.search\|vault.find_quotes\|vault.ensure_file" skills/chapter-writer/SKILL.md
echo "=== AC-6: chapter-writer kein literature_state Schreiben ===" && grep -n "literature_state" skills/chapter-writer/SKILL.md
echo "=== AC-7: export-skript existiert ===" && ls scripts/export-literature-state.mjs scripts/export-literature-state.sh
```

Alle Checks müssen passen (keine unerwarteten alten Pfade).

- [ ] **Step 2: Token-Count für PR-Body**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
echo "=== Word Counts ===" && wc -w agents/quote-extractor.md skills/citation-extraction/SKILL.md skills/chapter-writer/SKILL.md
echo "=== Geschätzte Token (×1.3) ==="
```

Notiere die Werte. Berechne: `Wörter × 1.3 = geschätzte Token`.

- [ ] **Step 3: Finale Commit-History prüfen**

```bash
cd /Users/j65674/Repos/academic-research-W2-A
git log --oneline feat/v6.0-W2-A ^main
```

Erwartung: 6–7 Commits (spec, + je 1 pro Task).

---

## Selbsttest der Plan-Vollständigkeit

| AC | Task | Abgedeckt? |
|---|---|---|
| AC-1: vault.ensure_file in quote-extractor | Task 1 | ✅ |
| AC-2: vault.add_quote + api_response_id | Task 2 | ✅ |
| AC-3: citation-extraction vault.find_quotes/get_quote | Task 3 | ✅ |
| AC-4: PDFs via vault.ensure_file (file_id, kein base64) | Tasks 1+3+4 | ✅ |
| AC-5: literature_state.md read-only + export-skript | Tasks 3+4+5 | ✅ |
| AC-6: chapter-writer Token < 2000 | Task 4+7 | ✅ |
| AC-7: Token-Count Vor/Nach im PR-Body | Task 7 | ✅ |
| Audit-Marker §5 | Task 6 | ✅ |
