# Spec · Chunk B · F1 Token-Tracks: Files-API + 1h-TTL-Cache

**Tickets:** #65 (Files-API), #66 (1h-TTL-Cache)
**Branch:** feat/v6.0-B
**Erstellt:** 2026-05-08

---

## 1 · Umfang

### #65 — Files-API für PDFs in quote-extractor

`quote-extractor` lädt dasselbe PDF derzeit bei jedem API-Call als base64 hoch
(~60–100k Tokens pro PDF). Die Files-API erlaubt einmaliges Hochladen, die
`file_id` wird in `pdf_status.json` gecacht; Folgecalls referenzieren nur die ID.

**Ziel:** -75 % Input-Tokens bei 5 PDFs × 3 Iterationen vs. base64.

### #66 — 1h-TTL-Cache

Seit 2026-03-06 ist der Anthropic-Default-TTL 5 Minuten. Ohne explizites
`ttl: "1h"` verfällt der Cache bei Batch-Pausen. Drei Agenten brauchen
explizites `cache_control: {type: "ephemeral", ttl: "1h"}` auf dem System-Prompt,
Breakpoint VOR dem `documents[]`-Array.

---

## 2 · Betroffene Dateien

| Datei | Aktion |
|---|---|
| `agents/quote-extractor.md` | modify — Files-API + 1h-TTL-Cache |
| `agents/relevance-scorer.md` | modify — 1h-TTL-Cache |
| `agents/quality-reviewer.md` | modify — 1h-TTL-Cache |
| `scripts/requirements.txt` | modify — anthropic>=0.40 (bereits gesetzt; verify) |
| `scripts/files_api_helper.py` | create — `ensure_uploaded()` mit TTL-Tracking |
| `tests/test_files_api_helper.py` | create — Mock-Tests |

---

## 3 · Offene Fragen (Entscheidungen)

### F1: Wo gehört `ensure_uploaded()`?

**Entscheidung: `scripts/files_api_helper.py`** (eigenständiges Modul).

**Begründung:**
- `agents/quote-extractor.md` ist ein Markdown-Agenten-Prompt, kein Python-Modul.
  Komplexe Logik (HTTP-Call, Cache-Datei, TTL-Check) gehört nicht in Prompt-Text.
- Konsistent mit dem bestehenden Pattern: `scripts/` enthält alle Python-Helper
  (`search.py`, `dedup.py`, `pdf_processor.py`, `project_bootstrap.py`).
- Testbar via `tests/test_files_api_helper.py` mit Mocks ohne SDK-Live-Calls.
- `agents/quote-extractor.md` referenziert die Funktion nur im API-Call-Schema-Block
  als Dokumentation (keine Ausführung im Prompt selbst).

### F2: Token-Vergleich-Methodik für -75%-AC

**Entscheidung: `tests/test_files_api_helper.py` Token-Counter-Block** mit Mock-Assertion.

**Begründung:**
- Eval-Suite braucht `ANTHROPIC_API_KEY` und ist für autonome Ausführung nicht geeignet.
- Log-Vergleich wäre fragil (kein reproduzierbarer Baseline im Repo).
- Stattdessen: Unit-Test verifiziert, dass bei `use_files_api=True` exakt 0 base64-Bytes
  an die API gesendet werden (Proxy-Beweis für Token-Einsparung). Das -75%-AC ist
  durch die Architektur garantiert: base64 einer 5MB-PDF ≈ 6.7MB/3bytes*4 ≈ ~100k Token,
  `file_id` ist ein String (~20 Token). Differenz >> 75%.
- Integration-Test-Dokumentation in `tests/test_files_api_helper.py` erklärt,
  wie ein manueller Eval-Lauf (mit Key) die Token-Zahlen prüft.

### F3: Test-Anker für `cache_read_input_tokens` (#66 AC)

**Entscheidung: Unit-Test `test_cache_read_path_validates_cached_tokens`** mit gemocktem Response-Objekt (Pfad a).

**Begründung:**
- Das AC aus #66 "Folgecall innerhalb 1h: `cache_read_input_tokens > 0`" ist deterministisch
  testbar: Der Code-Pfad, der einen API-Response auswertet, kann mit einem synthetischen
  `usage`-Objekt geprüft werden — kein Live-API-Key nötig.
- Mock-Pattern analog F2 (monkeypatch / `unittest.mock`), konsistent mit den übrigen
  `test_files_api_helper.py`-Tests.
- Test-Struktur: Erstelle ein Mock-Response-Objekt mit
  `usage.cache_read_input_tokens = 42`, übergib es an die Auswertungs-Logik,
  assert `result > 0`. Parallele Assertions mit `cache_read_input_tokens = 0`
  prüfen den Nicht-Cache-Hit-Pfad.
- Testname: `test_cache_read_path_validates_cached_tokens`
- Abgedeckter Codepfad: Helper/Utility-Funktion `extract_cache_read_tokens(response) -> int`,
  die `getattr(response.usage, "cache_read_input_tokens", 0)` wraps.

---

## 4 · Design: `scripts/files_api_helper.py`

```python
# Öffentliche API:
ensure_uploaded(
    pdf_path: str | Path,
    client: anthropic.Anthropic,
    cache_file: str | Path = "pdf_status.json",
    ttl_days: int = 30,
) -> str  # gibt file_id zurück

# Verhalten:
# 1. Liest cache_file (JSON dict: {sha256: {file_id, uploaded_at}})
# 2. SHA-256 des PDFs berechnen
# 3. Cache-Hit + nicht abgelaufen → file_id zurückgeben (kein Upload)
# 4. Cache-Miss oder abgelaufen → client.beta.files.upload(), cache schreiben
# 5. extra_headers werden intern gesetzt: {"anthropic-beta": "files-api-2025-04-14"}
```

**Cache-Schlüssel:** SHA-256 des PDF-Inhalts (nicht Pfad) — portabel, erkennt Umbenennungen.

**TTL:** `uploaded_at` ISO-Timestamp + `ttl_days` (Default 30, konfigurierbar via Parameter).

**Feature-Flag:** Wenn `ACADEMIC_FILES_API=0` (env) oder `client` ist None → Fallback.
Hilfsfunktion `should_use_files_api() -> bool` liest Env + SDK-Version-Check.

---

## 5 · Änderungen an Agenten-Markdown-Dateien

### `agents/quote-extractor.md`

Im Block `## Cache-Strategie` / `## Quellen-Bindung via Citations-API`:

1. **`source.type: "file"`** als primärer Pfad dokumentieren:
   ```json
   "source": {"type": "file", "file_id": "<aus ensure_uploaded()>"}
   ```
2. **Fallback base64** wenn Feature-Flag OFF:
   ```json
   "source": {"type": "base64", "media_type": "application/pdf", "data": "<base64>"}
   ```
3. **`cache_control`** auf `{"type": "ephemeral", "ttl": "1h"}` aktualisieren.
4. **Beta-Header** explizit dokumentieren: `extra_headers={"anthropic-beta": "files-api-2025-04-14"}`.

### `agents/relevance-scorer.md`

Im Block `## Cache-Strategie`:
- `cache_control` von `{"type": "ephemeral"}` auf `{"type": "ephemeral", "ttl": "1h"}` ändern.

### `agents/quality-reviewer.md`

Neuer Block `## Cache-Strategie` (fehlt noch vollständig):
- `cache_control: {"type": "ephemeral", "ttl": "1h"}` auf System-Prompt-Block, VOR `documents[]`.

---

## 6 · Acceptance Criteria (Checkliste)

| AC | Test |
|---|---|
| `ensure_uploaded()` lädt PDF einmal hoch, cached `file_id` | `test_files_api_helper.py::test_no_reupload_on_cache_hit` |
| Folgecall kein Re-Upload (SHA-256 Cache-Hit) | `test_files_api_helper.py::test_cache_hit_skips_upload` |
| TTL-Ablauf triggert Re-Upload | `test_files_api_helper.py::test_ttl_expiry_triggers_reupload` |
| Feature-Flag OFF → Fallback-Pfad, kein SDK-Call | `test_files_api_helper.py::test_fallback_when_flag_off` |
| beta-Header korrekt gesetzt | `test_files_api_helper.py::test_beta_header_present` |
| `relevance-scorer.md` enthält `"ttl": "1h"` | grep-Test in `test_files_api_helper.py` |
| `quote-extractor.md` enthält `"ttl": "1h"` | grep-Test |
| `quality-reviewer.md` enthält `"ttl": "1h"` | grep-Test |
| Breakpoint VOR `documents[]` | Dokumentiert in Agenten-Dateien, grep-Test |
| Folgecall innerhalb 1h: `cache_read_input_tokens > 0` | `test_files_api_helper.py::test_cache_read_path_validates_cached_tokens` (Mock: `usage.cache_read_input_tokens=42` → `extract_cache_read_tokens()` returns >0; `cache_read_input_tokens=0` → returns 0) |

---

## 7 · Nicht im Scope

- Chunk A (Vault MCP): `mcp/academic-vault/files_api.py` ist ein anderes Modul.
  `scripts/files_api_helper.py` deckt nur Chunk-B-Files ab.
- TTL-Konfig via `~/.academic-research/config.yaml`: Vorerst per Parameter/Env, keine
  globale Konfig-Datei (zu groß für diesen Chunk).
- Batch-API (#66 §4.4): Kein Scope für diesen Chunk.
- `anthropic>=0.40` in `requirements.txt` ist bereits gesetzt — nur verifizieren.
