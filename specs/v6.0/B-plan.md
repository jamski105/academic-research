# Plan · Chunk B · F1 Token-Tracks

**TDD-First. Ein Commit pro Task.**

---

## Task 1 — Test-Skelett + Failing Tests (TDD-Anker)

Datei: `tests/test_files_api_helper.py`

Tests schreiben, die ALLE fehlschlagen (Modul existiert noch nicht):

1. `test_cache_miss_triggers_upload` — kein Cache → Upload-Call erwartet
2. `test_cache_hit_skips_upload` — SHA-256 im Cache → kein Upload-Call
3. `test_ttl_expiry_triggers_reupload` — abgelaufener Cache-Eintrag → Re-Upload
4. `test_fallback_when_flag_off` — env `ACADEMIC_FILES_API=0` → liefert `None`
5. `test_beta_header_present` — `client.beta.files.upload` mit korrekten kwargs aufgerufen
6. `test_agent_cache_ttl_1h_relevance_scorer` — grep `"ttl": "1h"` in `agents/relevance-scorer.md`
7. `test_agent_cache_ttl_1h_quote_extractor` — grep `"ttl": "1h"` in `agents/quote-extractor.md`
8. `test_agent_cache_ttl_1h_quality_reviewer` — grep `"ttl": "1h"` in `agents/quality-reviewer.md`
9. `test_quote_extractor_file_source_documented` — grep `"type": "file"` in `agents/quote-extractor.md`
10. `test_quote_extractor_base64_fallback_documented` — grep `"type": "base64"` + `"Fallback"` in `agents/quote-extractor.md`

Commit: `test: failing tests for files_api_helper + agent cache_control checks`

---

## Task 2 — `scripts/files_api_helper.py` implementieren

Öffentliche API: `ensure_uploaded(pdf_path, client, cache_file, ttl_days) -> str | None`

Implementierung macht Tests 1–5 grün:
- SHA-256 aus Dateiinhalt
- JSON-Cache lesen/schreiben
- TTL-Check via `uploaded_at` ISO-Timestamp
- `client.beta.files.upload(file=open(pdf_path, "rb"), extra_body={"filename": ...})` — Beta-Header via `extra_headers`
- `should_use_files_api() -> bool`: prüft `ACADEMIC_FILES_API != "0"`

Commit: `feat(#65): scripts/files_api_helper.py — ensure_uploaded() mit SHA-256-Cache`

---

## Task 3 — `agents/relevance-scorer.md` aktualisieren

Änderung im Block `## Cache-Strategie`:
```python
"cache_control": {"type": "ephemeral", "ttl": "1h"},
```
(war: `{"type": "ephemeral"}` ohne ttl)

Test 6 wird grün.

Commit: `feat(#66): relevance-scorer — cache_control ttl=1h`

---

## Task 4 — `agents/quote-extractor.md` aktualisieren

Änderungen:
1. Block `## Quellen-Bindung via Citations-API` — primären source-Pfad auf `"type": "file"` umstellen + Fallback base64 dokumentieren
2. `cache_control` auf `{"type": "ephemeral", "ttl": "1h"}`
3. Beta-Header `extra_headers={"anthropic-beta": "files-api-2025-04-14"}` im Code-Beispiel
4. Verweis auf `ensure_uploaded()` aus `scripts/files_api_helper.py`

Tests 7, 9, 10 werden grün.

Commit: `feat(#65,#66): quote-extractor — Files-API source.type:file + ttl=1h cache`

---

## Task 5 — `agents/quality-reviewer.md` aktualisieren

Neuen Block `## Cache-Strategie` am Ende hinzufügen (vor `## Strategie` einschieben, sodass Breakpoint VOR documents[]):
```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[{
        "type": "text",
        "text": AGENT_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }],
    messages=[{"role": "user", "content": json.dumps(input)}],
)
```

Test 8 wird grün.

Commit: `feat(#66): quality-reviewer — cache_control ttl=1h`

---

## Task 6 — `scripts/requirements.txt` verifizieren + ggf. fixieren

`anthropic>=0.40` bereits gesetzt → nur verify. Falls Abweichung: fixieren.

Kein separater Commit (falls bereits korrekt); sonst:
Commit: `chore: requirements.txt verify anthropic>=0.40`

---

## Task 7 — Volle Test-Suite grün

```bash
cd /Users/j65674/Repos/academic-research-v6.0-B
pytest tests/test_files_api_helper.py -v
pytest tests/ -v --ignore=tests/evals
```

Alle Tests müssen grün sein.

---

## Task 8 — Code-Simplifier-Polish

- `git diff main -- scripts/files_api_helper.py tests/test_files_api_helper.py` als Basis
- Inline-Kommentare prüfen, unnötige Variablen entfernen
- Kein Ruff/Black (kein Lint-Config im Repo)
- Commit: `chore: code-simplifier polish`

---

## Commit-Reihenfolge

```
1. test: failing tests (TDD-Anker)
2. feat(#65): files_api_helper.py
3. feat(#66): relevance-scorer ttl=1h
4. feat(#65,#66): quote-extractor Files-API + ttl=1h
5. feat(#66): quality-reviewer ttl=1h
6. (optional) chore: requirements.txt
7. chore: code-simplifier polish
```

---

## LOC-Budget

| Datei | Est. LOC |
|---|---|
| `scripts/files_api_helper.py` | ~90 |
| `tests/test_files_api_helper.py` | ~120 |
| 3x agent .md (diffs klein) | ~30 |
| **Total** | **~240** |

Innerhalb des 250-LOC-Budgets.
