# Spec · Chunk W2-B · Vault Hook — Verbatim-Validation

**Ticket:** #64
**Branch:** feat/v6.0-W2-B
**Erstellt:** 2026-05-12

---

## 1 · Ziel

Ein `PreToolUse`-Hook, der verhindert, dass Claude halluzinierte Zitate in
Kapitel-Dateien schreibt. Jeder Anführungszeichen-Span in einem `Write`-Tool-Call
wird gegen den Vault geprüft — kein übereinstimmendes Zitat → Block.

---

## 2 · Scope

| Datei | Aktion |
|---|---|
| `hooks/verbatim-guard.mjs` | NEU — PreToolUse-Hook |
| `hooks/hooks.json` | EDIT — PreToolUse-Eintrag hinzufügen |
| `mcp/academic_vault/db.py` | EDIT — `search_quote_text()` hinzufügen |
| `mcp/academic_vault/server.py` | EDIT — `vault.search_quote_text` MCP-Tool |
| `evals/verbatim-guard/` | NEU — 10 Test-Cases + Runner-Doku |

---

## 3 · Hook-Lifecycle

```
Claude ruft Write(path, content) auf
         │
         ▼
PreToolUse-Hook: hooks/verbatim-guard.mjs
         │
         ├─ 1. Pfad-Match prüfen: kapitel/*.md | *.tex
         │      → kein Match → allow (exit 0)
         │
         ├─ 2. Bypass-Flag prüfen: content enthält "<!-- vault-guard: skip -->"
         │      → gefunden → allow (exit 0)
         │
         ├─ 3. Quote-Spans extrahieren (Parser)
         │      → keine Spans → allow (exit 0)
         │
         ├─ 4. Für jeden Span: vault.search_quote_text(verbatim)
         │      → Treffer vorhanden → allow (weiter zu nächstem Span)
         │      → kein Treffer → Block + Fehlermeldung
         │
         └─ → Alle Spans verifiziert → allow (exit 0)
```

---

## 4 · Pfad-Matching

Glob-Patterns (case-sensitive):
- `kapitel/*.md` — Kapitel-Markdown-Dateien
- `*.tex` — LaTeX-Dateien (im Repo-Root oder überall)

Implementierung: `micromatch`-Lib vermeiden (ESM-Only-Constraint).
Stattdessen: Einfacher String-Test mit `path.endsWith('.tex')` und
`path.includes('kapitel/') && path.endsWith('.md')`.

---

## 5 · Quote-Parser

### Unterstützte Span-Typen

| Typ | Beispiel |
|---|---|
| ASCII double quotes | `"…"` |
| Deutsch typografisch | `„…"` |
| Guillemets | `«…»` |
| LaTeX | `` ``…'' `` |

### Mindestlänge

Spans < 10 Zeichen werden ignoriert (Rauschen / Einzelwörter wie "AI").

### Regex-Pattern

```js
const QUOTE_RE = /(?:"([^"]{10,})")|(?:„([^"]{10,})")|(?:«([^»]{10,})»)|(?:``([^']{10,})'')/g;
```

Jeder Match liefert den inneren Text (capture group 1–4).

---

## 6 · Vault-Lookup

### `search_quote_text(verbatim, threshold=0.8)` — Semantik

- Sucht in `quotes.verbatim` nach Übereinstimmung.
- Methode: normalisierter Substring-Check (LIKE `%<verbatim>%`).
- Bei Partial-Matches (Hook erhält gekürzte Zitate): Mindestens 80 % der
  Zeichen des Hook-Spans müssen im gefundenen verbatim enthalten sein.
- Gibt `[{quote_id, verbatim, paper_id}]` zurück (leer wenn kein Treffer).

### MCP-Aufruf aus Hook

Der Hook ruft den Vault **nicht** über MCP auf (MCP läuft in Claude-Prozess,
nicht in Hook-Prozess). Stattdessen: Direkter SQLite-Aufruf via Python-Subprocess
oder HTTP-Fallback.

**Gewählter Ansatz: Python-Subprocess**

```js
const result = execFileSync('python3', [
  '-c',
  `import sys, json; sys.path.insert(0, '${vaultSrcDir}');
   from mcp.academic_vault.server import search_quote_text
   print(json.dumps(search_quote_text(sys.argv[1], sys.argv[2])))`,
  dbPath, verbatim
], { encoding: 'utf-8' });
```

Wenn Python/Vault nicht verfügbar: Hook warnt und lässt durch (fail-open).

### `vault.search_quote_text` in db.py + server.py

```python
def search_quote_text(db_path: str, verbatim: str, k: int = 5) -> list[dict]:
    """Sucht Quotes nach verbatim-Substring. Gibt [{quote_id, verbatim, paper_id}] zurueck."""
```

---

## 7 · Bypass-Flag

Wenn der zu schreibende Content `<!-- vault-guard: skip -->` enthält (als
HTML-Kommentar, case-sensitive), überspringt der Hook alle Prüfungen.

---

## 8 · Block-Verhalten

Bei einem nicht verifizierten Span sendet der Hook auf stderr:

```
[Vault-Guard] BLOCKIERT: Zitat nicht im Vault verifiziert.
Zitat: "…"
Bitte Zitat über vault.add_quote() / quote-extractor einpflegen.
```

Exit-Code: 2 (Claude-Code-Protokoll: Block).

---

## 9 · Vault-Lookup-Implementierung: `search_quote_text`

In `mcp/academic_vault/db.py`:

```python
def search_quote_text(self, verbatim: str, k: int = 5) -> list[dict]:
    """LIKE-Suche in quotes.verbatim. Gibt [{quote_id, verbatim, paper_id}] zurueck."""
    conn = self._get_conn()
    own_conn = self._conn is None
    rows = conn.execute(
        "SELECT quote_id, verbatim, paper_id FROM quotes WHERE verbatim LIKE ? LIMIT ?",
        (f"%{verbatim}%", k),
    ).fetchall()
    if own_conn:
        conn.close()
    return [dict(r) for r in rows]
```

In `mcp/academic_vault/server.py`: freie Funktion `search_quote_text(db_path, verbatim, k)` +
MCP-Tool `vault.search_quote_text`.

---

## 10 · Eval-Set

10 Test-Cases in `evals/verbatim-guard/cases.json`.

| # | Typ | Erwartung |
|---|---|---|
| 1–5 | Echte Quotes (im Vault gespeichert) | PASS |
| 6–10 | Erfundene Quotes (nicht im Vault) | BLOCK |

Runner-Dokumentation: `evals/verbatim-guard/README.md`.

Smoke-Test: `node hooks/verbatim-guard.mjs < evals/verbatim-guard/cases.json` (vereinfachter Einzel-Lauf).

---

## 11 · hooks.json-Änderung

```json
"PreToolUse": [
  {
    "matcher": "Write",
    "hooks": [
      {
        "type": "command",
        "command": "node /PLUGIN_ROOT/hooks/verbatim-guard.mjs",
        "timeout": 15
      }
    ]
  }
]
```

Pfad nutzt `${CLAUDE_PLUGIN_ROOT}` (analog zu SessionStart-Hook).

---

## 12 · Nicht im Scope

- FTS5-Index auf `quotes`-Tabelle (LIKE-Suche reicht für MVP).
- Semantische Ähnlichkeitssuche (sqlite-vec, Embeddings).
- Konfigurierbare Threshold-Parameter (Hard-coded 80 % Substring-Match).
- Integration-Tests mit Live-Vault (brauchen `ANTHROPIC_API_KEY`).
