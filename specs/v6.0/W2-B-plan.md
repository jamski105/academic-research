# Plan · Chunk W2-B · Verbatim-Guard PreToolUse Hook

**TDD-First. Ein Commit pro Task.**

---

## Task 1 — `vault.search_quote_text` in db.py + server.py (TDD)

**Warum zuerst:** Hook braucht diese Funktion. TDD: Eval-Cases testen die
Vault-Funktion direkt via Python. Eval-Cases = "Tests" (kein Test-Framework).

### 1a. Failing Eval-Cases schreiben (RED)

Datei: `evals/verbatim-guard/cases.json` (10 Cases mit expected)
Datei: `evals/verbatim-guard/runner.py` (Mini-Runner, der Cases ausführt)

Runner läuft OHNE vault.search_quote_text (ImportError) → Failure sichtbar.

### 1b. Implementation (GREEN)

- `mcp/academic_vault/db.py`: `search_quote_text(self, verbatim, k=5)` hinzufügen
- `mcp/academic_vault/server.py`: freie Funktion + MCP-Tool `vault.search_quote_text`

Runner läuft DURCH (Cases 1–5 pass, Cases 6–10 block).

Commit: `feat(v6.0/W2-B): vault.search_quote_text — LIKE-Suche in quotes.verbatim`

---

## Task 2 — Eval-Set vollständig schreiben

Datei: `evals/verbatim-guard/cases.json` — 10 Cases
Datei: `evals/verbatim-guard/README.md` — Runner-Doku + Smoke-Test-Anleitung

Cases-Format:
```json
[
  {
    "id": 1,
    "type": "real",
    "quote_text": "...",
    "in_vault": true,
    "expected": "pass"
  },
  ...
]
```

Commit: `feat(v6.0/W2-B): evals/verbatim-guard — 10 Test-Cases + Runner-Doku`

---

## Task 3 — Quote-Parser + Pfad-Match-Logik (TDD)

Eval-Cases testen den Parser implizit über den Hook. Aber der Hook existiert
noch nicht → erst Hook-Eingabe-Format definieren.

Hook liest von stdin: JSON-Objekt (Claude-Code PreToolUse-Format):
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "kapitel/01-einleitung.md",
    "content": "...„Zitat"..."
  }
}
```

Task: Quote-Parser als eigenständige Funktion isolieren + in
`evals/verbatim-guard/runner.py` testen.

Kein separater Commit (wird in Task 4 commitet).

---

## Task 4 — `hooks/verbatim-guard.mjs` implementieren

Lifecycle (aus Spec §3):
1. Pfad-Match
2. Bypass-Flag
3. Quote-Parser
4. Vault-Lookup via Python-Subprocess
5. Block oder Allow

Implementierung:
- ESM-Modul
- `process.stdin` lesen → JSON parsen
- Subprocess-Call: `python3 -c "..."` mit `execFileSync`
- Fail-open wenn Python/Vault nicht verfügbar (Warnung auf stderr, exit 0)
- Block: stderr-Nachricht auf Deutsch + exit 2

Commit: `feat(v6.0/W2-B): hooks/verbatim-guard.mjs — PreToolUse Verbatim-Guard`

---

## Task 5 — hooks.json registrieren

`hooks/hooks.json`: `PreToolUse`-Eintrag für Write hinzufügen.

Commit: `feat(v6.0/W2-B): hooks.json — PreToolUse verbatim-guard registrieren`

---

## Task 6 — Smoke-Test 2 Cases durchlaufen

```bash
# Case 1: echtes Zitat (expect: allow)
echo '{"tool_name":"Write","tool_input":{"file_path":"kapitel/01.md","content":"„<echtes-zitat>""}}' \
  | node hooks/verbatim-guard.mjs

# Case 6: erfundenes Zitat (expect: block)
echo '{"tool_name":"Write","tool_input":{"file_path":"kapitel/01.md","content":"„<erfundenes-zitat>""}}' \
  | node hooks/verbatim-guard.mjs
```

Kein Commit. Nur Verifikation.

---

## Task 7 — Eval-Runner ausführen (alle 10 Cases)

```bash
python3 evals/verbatim-guard/runner.py
```

Erwartet: 5/5 real pass, 5/5 invented block. FPR = 0/5 = 0 % < 5 % AC.

Kein Commit. Nur Verifikation.

---

## Task 8 — Code-Simplifier-Polish

- diff vs. base: `git diff main -- hooks/verbatim-guard.mjs mcp/academic_vault/db.py mcp/academic_vault/server.py`
- Unnötige Variablen, verbesserliche Kommentare prüfen
- Commit: `chore: code-simplifier polish W2-B`

---

## Commit-Reihenfolge

```
1. feat(v6.0/W2-B): vault.search_quote_text
2. feat(v6.0/W2-B): evals/verbatim-guard — Test-Cases + Runner
3. feat(v6.0/W2-B): hooks/verbatim-guard.mjs
4. feat(v6.0/W2-B): hooks.json PreToolUse registrieren
5. chore: code-simplifier polish W2-B
```

---

## LOC-Budget

| Datei | Est. LOC |
|---|---|
| `hooks/verbatim-guard.mjs` | ~120 |
| `mcp/academic_vault/db.py` (delta) | ~15 |
| `mcp/academic_vault/server.py` (delta) | ~20 |
| `evals/verbatim-guard/cases.json` | ~80 |
| `evals/verbatim-guard/runner.py` | ~60 |
| `evals/verbatim-guard/README.md` | ~30 |
| **Total** | **~325** |
