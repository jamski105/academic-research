# Spec W2-A — Vault Phase 2: quote-extractor & chapter-writer auf Vault umstellen

**Ticket:** #63  
**Chunk:** W2-A  
**Branch:** feat/v6.0-W2-A  
**Datum:** 2026-05-12

---

## Kontext

Wave 1 hat `mcp/academic_vault/` mit SQLite-Schema und MCP-Tools geliefert
(`vault.search`, `vault.get_paper`, `vault.add_paper`, `vault.ensure_file`,
`vault.add_quote`, `vault.find_quotes`, `vault.get_quote`, `vault.stats`).

Wave 2 / W2-A verdrahtet die bestehenden Skills und Agents gegen diesen Vault.
Heute laufen alle Lese-/Schreibpfade über Markdown-Dateien und base64-PDFs im
Context — mit ~8–15 k Token Boilerplate pro chapter-writer-Aufruf.

**Ziel:** Gezielte Vault-Tool-Calls statt Context-Stuffing → ~83 % Token-Ersparnis.

---

## Acceptance Criteria und Verifikation

### AC-1: quote-extractor schreibt via vault.add_quote()

**Was:** `agents/quote-extractor.md` enthält keinen JSON-File-Schreibpfad mehr.
Extrahierte Zitate werden ausschliesslich via `vault.add_quote()` mit gefülltem
`api_response_id`-Feld persistiert.

**Wo:** `agents/quote-extractor.md` — Abschnitt "Output-Format" und
"Cache-Strategie" überarbeiten; neuen Abschnitt "Vault-Persistenz" hinzufügen.

**Verifikation:** `grep -n "json\|JSON\|write\|schreib" agents/quote-extractor.md`
findet keinen Datei-Schreibpfad mehr. `grep "vault.add_quote" agents/quote-extractor.md`
liefert mindestens einen Treffer mit `api_response_id`.

---

### AC-2: citation-extraction liest via vault.find_quotes() / vault.get_quote()

**Was:** `skills/citation-extraction/SKILL.md` ersetzt den direkten PDF-Lesepfad
durch `vault.find_quotes()` + `vault.get_quote()`. Schritt "2. PDFs lokalisieren"
und "3. Zitat-Extraktion" werden auf Vault-Calls umgestellt.

**Wo:** `skills/citation-extraction/SKILL.md` — Abschnitte "Kontext-Dateien",
"Core-Workflow §2–3" und "Literaturstatus aktualisieren" (§7) anpassen.

**Verifikation:**
- `grep "pdf_text\|pdfs/" skills/citation-extraction/SKILL.md` findet keine
  direkten PDF-Lesepfade mehr als primären Workflow.
- `grep "vault.find_quotes\|vault.get_quote" skills/citation-extraction/SKILL.md`
  findet mindestens zwei Treffer.

---

### AC-3: chapter-writer liest via vault.search() + vault.find_quotes()

**Was:** `skills/chapter-writer/SKILL.md` ersetzt das vollständige Laden von
`literature_state.md` durch gezielte Vault-Calls:
- `vault.search(query, k=5)` für relevante Paper-IDs
- `vault.find_quotes(paper_id, query, k=3)` für Zitat-Kandidaten

**Wo:** `skills/chapter-writer/SKILL.md` — Abschnitte "Kontext-Dateien",
"Core-Workflow §1 Kontext laden" und "§3 Kapitelplanung" anpassen.

**Verifikation:**
- `grep "literature_state.md" skills/chapter-writer/SKILL.md` findet keine
  primären Lese-Anweisungen mehr (nur noch Snapshot-Hinweis).
- `grep "vault.search\|vault.find_quotes" skills/chapter-writer/SKILL.md`
  findet mindestens zwei Treffer.
- Token-Count des Boilerplate-Abschnitts (Kontext laden + Quellen) < 2000 Token.

---

### AC-4: PDFs via vault.ensure_file() als file_id

**Was:** In `agents/quote-extractor.md` wird `vault.ensure_file(paper_id)` für
den Primärpfad genutzt. Der base64-Fallback bleibt erhalten, wird aber explizit
als Fallback markiert (wenn `vault.ensure_file()` keinen file_id liefert).

**Wo:** `agents/quote-extractor.md` — Abschnitt "Quellen-Bindung via Citations-API".

**Verifikation:**
- `grep "vault.ensure_file" agents/quote-extractor.md` findet mindestens einen Treffer.
- Primärpfad-Beschreibung referenziert `file_id` aus Vault, nicht `pdf_path` direkt.

---

### AC-5: literature_state.md nur noch read-only Snapshot-Export

**Was:** Kein Skill und kein Agent schreibt direkt in `literature_state.md`.
Ein neues Skript `scripts/export-literature-state.mjs` generiert die Datei
als Snapshot aus dem Vault (via `vault.search` + `vault.get_paper`).

**Wo:**
- `agents/quote-extractor.md`: Schreib-Referenz auf `literature_state.md` entfernen
- `skills/citation-extraction/SKILL.md`: §7 "Literaturstatus aktualisieren" →
  `literature_state.md` nur noch lesen, nicht schreiben; Hinweis auf Export-Skript
- `skills/chapter-writer/SKILL.md`: `literature_state.md`-Schreibpfad entfernen
- `scripts/export-literature-state.mjs` (NEU): Node.js ESM-Skript, ruft
  Vault-MCP-Tools auf und schreibt Snapshot in `./literature_state.md`

**Verifikation:**
- `grep -n "literature_state" agents/quote-extractor.md` findet keine
  Schreib-Anweisungen mehr.
- `scripts/export-literature-state.mjs` existiert und enthält einen sinnvollen
  Kommentar-Block + Skript-Rumpf.

---

### AC-6: Token-Boilerplate in chapter-writer < 2000 Token

**Was:** Der Boilerplate-Abschnitt (Kontext laden, Quellen-Lookup) in
`skills/chapter-writer/SKILL.md` liegt nach der Migration unter 2000 Token.

**Verifikation:** Manueller Token-Count via `wc -w skills/chapter-writer/SKILL.md`
als Proxy (1 Wort ≈ 1,3 Token). Exakter Count via `tiktoken` oder manueller
Schätzung und Dokumentation im PR-Body.

---

### AC-7: Eval — identische Zitat-Qualität bei -75 % Tokens

**Was:** Kein automatisierter Eval in diesem Ticket. Stattdessen: manueller
Token-Count-Snapshot (v5.4-Baseline vs. v6.0-Post-Migration) im PR-Body
dokumentiert. Vor/Nach-Vergleich in Worten und geschätzten Token.

**Verifikation:** PR-Body enthält Tabelle mit Baseline-Token-Count und
Post-Migration-Count, Differenz >= 75 %.

---

## Out of Scope

- `PreToolUse`-Hook für Verbatim-Validation auf `kapitel/*.md` → Chunk W2-B (#64)
- `zotero-import`-Skill → Phase 3 (#future)
- Automatisierte Eval-Suite → #55 (manueller API-Key-Run, deferred)

---

## Technische Entscheidungen

### Vault-Tool-Call-Muster (chapter-writer)

```
1. vault.search(query, k=5)           → [paper_id, snippet, score]  ≈ 200 Token
2. vault.find_quotes(paper_id, k=3)   → [verbatim, page, quote_id]  ≈ 1500 Token total
```

Statt: `literature_state.md` (alle Stubs) + PDF-Auszüge ≈ 8–15 k Token.

### export-literature-state.mjs

Node.js ESM-Skript (kein Python, passt besser zu JS-Hooks-Konvention des Repos).
Liest via `@anthropic-ai/mcp-client` oder direkt via HTTP den Vault-MCP-Server.
Schreibt `./literature_state.md` als Markdown-Snapshot.

**Alternative:** Shell-Skript `scripts/export-literature-state.sh` als Thin-Wrapper
um das mjs-Skript (für einfachen Aufruf ohne `node`-Präfix).

### Keine neuen Python-Skripte

Laut infra-brief: "Plugin-Design bevorzugt Agenten/Skills über Python-Skripte."
Das Export-Skript ist eine Ausnahme (Datei-Export, kein Agent/Skill sinnvoll),
aber wird als ESM-Skript (`.mjs`) implementiert, nicht Python.

---

## Dateigrenze (File Boundary)

Zu ändern:
- `agents/quote-extractor.md`
- `skills/citation-extraction/SKILL.md`
- `skills/chapter-writer/SKILL.md`
- `scripts/export-literature-state.mjs` (NEU)
- `scripts/export-literature-state.sh` (NEU, optional als Thin-Wrapper)
- `docs/AUDIT-v6-vault.md` (§5 Phase 2 Status-Marker auf "implemented")
- `specs/v6.0/W2-A.md` (diese Datei)
- `specs/v6.0/W2-A-plan.md` (Plan)

Nicht zu ändern (Hard Boundary):
- Alles ausserhalb der obigen Liste
- `hooks/verbatim-guard.mjs` → W2-B
- `agents/quality-reviewer.md` → W2-C

---

## Token-Baseline (Vor-Migration)

Geschätzte Token-Zahlen vor Migration (v5.4):

| Komponente | Wörter (wc -w) | Est. Token (×1.3) |
|---|---|---|
| `skills/chapter-writer/SKILL.md` gesamt | ~900 | ~1170 |
| `agents/quote-extractor.md` gesamt | ~650 | ~845 |
| `skills/citation-extraction/SKILL.md` gesamt | ~750 | ~975 |

**Laufzeit-Boilerplate** (chapter-writer pro Aufruf, v5.4):
- `literature_state.md` laden: ~3000–8000 Token (je nach Projektgröße)
- PDF-Auszüge per base64: ~5000–12000 Token pro PDF
- **Total Boilerplate: ~8000–15000 Token**

**Post-Migration-Ziel:**
- Vault-Tool-Calls: ~200 + ~1500 = ~1700 Token
- Reduzierung: ~83 % (weit über dem -75 %-Ziel aus AC-7)
