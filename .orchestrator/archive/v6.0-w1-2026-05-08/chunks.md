# v6.0 Wave 1 Decomposition

## Order

1. chunk-A (depends on: -)
2. chunk-B (depends on: -)
3. chunk-C (depends on: -)
4. chunk-D (depends on: -)
5. chunk-E (depends on: -)
6. chunk-F (depends on: A, B, C)
7. chunk-G (depends on: B, D)
8. chunk-H (depends on: A, F, E)

**Chunk-I (#55 Baseline-Eval) deferred to a later wave** per user-decision.
Reason: requires interactive `ANTHROPIC_API_KEY` and is a one-time documentation
update unrelated to v6.0 functional changes.

## chunk-A: Vault MCP-Server Skeleton

- Tickets: #62
- Files (max 15):
  - `mcp/academic-vault/__init__.py` (create)
  - `mcp/academic-vault/server.py` (create) — MCP-Tool-Set v1
  - `mcp/academic-vault/schema.sql` (create) — papers, quotes, quote_embeddings, decisions, notes, papers_fts
  - `mcp/academic-vault/db.py` (create) — SQLite-Connection + sqlite-vec Loader + FTS5-Fallback
  - `mcp/academic-vault/files_api.py` (create) — Anthropic-Files-API-Client mit `file_id`-Cache + TTL-Tracking
  - `mcp/academic-vault/migrate.py` (create) — `literature_state.md` + lokale PDFs → SQLite-Initial-Seed
  - `mcp/academic-vault/requirements.txt` (create) — sqlite-vec, anthropic≥0.40
  - `.mcp.json` (create or modify) — Server-Eintrag academic-vault
  - `tests/test_vault_skeleton.py` (create) — Smoke-Tests aller Tools
- Estimated LOC: ~500 (knapp am Cap-Limit)
- Estimated effort: ~8h
- Dependencies: none
- Notes:
  - LOC am Cap-Limit. Bei Überschreitung Spec aufteilen in A1 (schema+db+migrate) + A2 (MCP-Tools+files_api).
  - sqlite-vec Extension: load_extension() + Fallback auf reine FTS5 wenn nicht verfügbar.
  - `vault.add_quote` MUSS Quotes ohne `api_response_id` ablehnen (Halluzinationsschutz).
  - User-Decisions: keine direkt für diesen Chunk.

## chunk-B: F1 Token-Tracks (Files-API + 1h-TTL-Cache)

- Tickets: #65, #66
- Files (max 15):
  - `agents/quote-extractor.md` (modify) — `source.type: "file"` mit `file_id`, `cache_control: ttl=1h`, beta-Header
  - `agents/relevance-scorer.md` (modify) — `cache_control: ttl=1h`
  - `agents/quality-reviewer.md` (modify) — `cache_control: ttl=1h`
  - `scripts/requirements.txt` (modify) — `anthropic>=0.40`
  - `scripts/files_api_helper.py` (create) — `ensure_uploaded(pdf_path)` mit `pdf_status.json`-Cache
  - `tests/test_files_api_helper.py` (create) — Mock-Tests für ensure_uploaded
- Estimated LOC: ~250
- Estimated effort: ~4h
- Dependencies: none
- Notes:
  - Beide Tickets touchieren `agents/quote-extractor.md` → kombiniert um Sequencing zu vermeiden.
  - Feature-Flag-OFF Pfad: graceful Fallback auf base64.
  - Cache-Breakpoint VOR `documents[]`-Array.
  - Open Q (deferred): Token-Vergleich-Methodik für -75%-AC. L1 entscheidet im Spec (vorgeschlagen: pytest mit Token-Counter im Test-Log).
  - Open Q (deferred): `ensure_uploaded`-Location → vorgeschlagen `scripts/files_api_helper.py` als saubere Trennung.

## chunk-C: Skills schlanker — Shared preamble

- Tickets: #67
- Files (max 15):
  - `skills/_common/preamble.md` (create) — 4 Pflicht-Blöcke
  - `skills/<skill-1..13>/SKILL.md` (modify) — alle 13 Skills, preamble-Reference statt lokale Duplikate
  - `tests/test_skills_manifest.py` (modify) — neuer Token-Counter-Check
- Estimated LOC: ~300
- Estimated effort: ~5h
- Dependencies: none
- Notes:
  - 14 Files. Auf 13 Skills aufgepasst — wenn Skill-Anzahl wächst, Cap überschreiten.
  - Open Q (deferred): Include-Mechanismus (Frontmatter `include:`, Symlink, Copy-on-build) — L1 entscheidet im Spec basierend auf Claude-Code-Plugin-Manifest-Support.
  - Open Q (deferred): -500 Token-Messung-Basis (kompilierter Prompt vs. .md-Rohgröße) — L1 entscheidet im Spec.
  - Browser-Modul-Anpassung: Raw-DOM in `$SESSION_DIR/raw/` statt Modell-Context.

## chunk-D: /humanize Slash-Command

- Tickets: #69
- Files (max 15):
  - `commands/humanize.md` (create) — YAML-Frontmatter + Skill(humanizer-de) + Auto-Install-Logik
  - `tests/test_humanize_command.py` (create) — Smoke-Tests für Output-File-Erzeugung
- Estimated LOC: ~120
- Estimated effort: ~2h
- Dependencies: none
- Notes:
  - User-Decisions: Default-Modus = `normal`. humanizer-de fehlend → Auto-Install vom Marketplace.
  - Voice-Calibration optional: `~/.academic-research/projects/<slug>/voice-samples/`.
  - Output: `<basename>.humanized.md` + `<basename>.diff.md` (severity-gegliedert).

## chunk-E: git init Auto-Setup im Bootstrap

- Tickets: #70
- Files (max 15):
  - `scripts/project_bootstrap.py` (modify) — Frage „Git aktivieren?" + git init + initial commit
  - `scripts/bootstrap/gitignore.fragment` (modify) — `pdfs/`, `sessions/`, `credentials.json`
  - `hooks/hooks.json` (modify) — Stop-Hook Diff-Check auf academic_context.md
  - `tests/test_project_bootstrap.py` (modify) — neuer Test für git-init-Pfad + graceful-skip
- Estimated LOC: ~150
- Estimated effort: ~3h
- Dependencies: none
- Notes:
  - User-Decisions: Nur fresh-Pfad (kein idempotent-Pfad-Anbieten). Stop-Hook nur wenn Git-Repo erkannt.
  - Touchiert `hooks/hooks.json` — sequenziert mit chunk-H (Vault-Hook).

## chunk-I: Baseline-Eval-Run v5.2.0

- Tickets: #55
- Files (max 15):
  - `docs/evals/2026-04-23-summary.md` (modify) — Baseline-Gap-Block füllen
- Estimated LOC: ~50 (reine Doku)
- Estimated effort: ~1h (plus Eval-Laufzeit ~30min via API)
- Dependencies: none
- Notes:
  - **REQUIRES INTERACTIVE EXECUTION:** `ANTHROPIC_API_KEY` muss vom User gesetzt werden, dann `pytest tests/evals/ -v` lokal laufen.
  - L1 kann Eval-Lauf nicht autonom starten (kostet API-Tokens, braucht User-Owned Key).
  - L0-Strategie: L1 bereitet Report-Skeleton + Stub-Werte vor; User füllt nach manuellem Eval-Lauf die echten Zahlen ein.
  - Alternative: Chunk komplett user-handled, kein L1-Spawn.

## chunk-F: Vault-Pipeline-Integration (quote-extractor + chapter-writer auf Vault)

- Tickets: #63
- Files (max 15):
  - `agents/quote-extractor.md` (modify) — schreibt via `vault.add_quote(api_response_id=...)`
  - `skills/citation-extraction/SKILL.md` (modify) — liest via `vault.find_quotes()` + `vault.get_quote()`
  - `skills/chapter-writer/SKILL.md` (modify) — liest via `vault.search()` + `vault.find_quotes()` statt full literature_state.md
- Estimated LOC: ~200
- Estimated effort: ~4h
- Dependencies: A (Vault MCP-Server), B (quote-extractor.md sequenz), C (chapter-writer SKILL.md sequenz)
- Notes:
  - Sequenziert nach A/B/C wegen Datei-Overlaps und Vault-Verfügbarkeit.
  - AC: chapter-writer < 2k Token Boilerplate (vorher ~10k); identische Zitat-Qualität bei -75 % Tokens.

## chunk-G: humanizer-de Pipeline-Integration

- Tickets: #68
- Files (max 15):
  - `agents/chapter-writer.md` (modify) — ruft humanizer-de im Mode `audit` vor quality-reviewer
  - `agents/quality-reviewer.md` (modify) — Reihenfolge nach humanizer-de respektieren
  - `scripts/setup.sh` o.Ä. (modify) — Skill-Existenz-Check humanizer-de
- Estimated LOC: ~100
- Estimated effort: ~2h
- Dependencies: B (quality-reviewer.md sequenz), D (humanize-Command existiert mit Auto-Install)
- Notes:
  - Trigger: `output_target ∈ {Bachelor, Master, Diplom, Dissertation}` aus `./academic_context.md`.
  - Bypass-Flag: `humanizer_de: off` in `./academic_context.md`.
  - Default off in onboard-project ohne Hochschul-Marker.
  - Closes (TEMP): #59.

## chunk-H: Vault Hook Verbatim-Guard

- Tickets: #64
- Files (max 15):
  - `hooks/verbatim-guard.mjs` (create) — PreToolUse für Write `kapitel/*.md`, `*.tex`
  - `hooks/hooks.json` (modify) — verbatim-guard registrieren
  - `tests/test_verbatim_guard.py` (create) — 10 Test-Cases (5 echt / 5 erfunden)
- Estimated LOC: ~200
- Estimated effort: ~4h
- Dependencies: A (Vault MCP für search_quote_text), F (Vault-Pipeline-Integration füllt Vault), E (hooks.json sequenz)
- Notes:
  - Parser für Anführungszeichen-Spans: `"…"`, `„…"`, `«…»`, `` `…' ``.
  - Lookup gegen `vault.search_quote_text(verbatim)`.
  - Bypass-Flag: `<!-- vault-guard: skip -->`.
  - AC: Echte Quotes 100% pass, erfundene 100% block, FPR < 5%.
