# v6.3 Wave 1 — Decomposition

**Strategie:** 2 Tickets → 2 Chunks (1 Chunk pro Ticket). Beide unabhängig, parallel implementierbar.

**Cap-Budget (per chunk):** max 15 Files, ~500 LoC, ~8h. Beide Chunks bleiben weit unter Cap.

**Dep-Graph:**
```
A  B
(unabhängig — können parallel)
```

---

## Chunk A — Zotero-Import (Ticket #88)

**Branch:** `feat/v6.3-A-zotero-import`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.3-A`
**Tickets:** #88

### Akzeptanzkriterien (verbatim)
- Test mit Zotero-Group-Library (50 Items): alle 50 in Vault
- Re-Run führt nicht zu Duplikaten
- PDFs in Files-API hochgeladen, file_ids gecached

### File-Boundary (max 15)
- `skills/zotero-import/SKILL.md` (neu) — Skill-Definition mit Triggern, Anleitung
- `skills/zotero-import/scripts/zotero_pull.py` (neu) — pyzotero-Wrapper, dedup-Logik
- `scripts/requirements.txt` (Edit) — Add `pyzotero>=1.5` als optionale Dep
- `mcp/academic_vault/server.py` (Edit, minimal) — neue Funktion `import_zotero_items(items: list[dict]) -> import_log` (optional, falls add_paper-Wrapper nötig); ODER `import_zotero_items` als Helper im Skill-Script
- `tests/test_zotero_import.py` (neu) — Unit-Tests: Mock pyzotero, Mock vault.add_paper, Test 50-Items-Group-Library + Re-Run-Idempotenz
- `tests/fixtures/zotero_library.json` (neu) — Mock-Antwort-Fixture (50 Items mit Mix aus Papern/Büchern, DOIs, ISBNs)
- `tests/fixtures/zotero_attachments/` (neu) — Mock-Attachment-PDFs (kleine 1-Seiter)
- `docs/skills/zotero-import.md` (neu, optional) — Konfig-Hinweise (`~/.academic-research/config.yaml`-Schema)

### Out-of-scope (explizit)
- Push zurück nach Zotero (kein API-Write, nur Read)
- Zotero-Local-DB-Zugriff (`zotero.sqlite`) — nur Web-API via pyzotero
- Migration/Sync-Daemon (manueller Trigger reicht in v6.3)

### Risiken
- pyzotero-Group-Library-API anders als User-Library (`library_type` muss korrekt sein)
- Credentials in Config: 0600-Permissions, niemals in Logs (siehe v6.2 C `auth-helper` als Referenz)
- Bei Mock-Fixture: keine echten Zotero-API-Calls in Tests

### Aufwandsschätzung
- ~6 Files, ~250 LoC, ~3h L1-Time

---

## Chunk B — NotebookLM-Bundle (Ticket #89)

**Branch:** `feat/v6.3-B-notebook-bundle`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.3-B`
**Tickets:** #89

### Akzeptanzkriterien (verbatim)
- 5 Paper × 30 S. → 1 Bundle-PDF mit allen Inhalten
- User-Doku verlinkt NotebookLM-Upload-Flow

### File-Boundary (max 15)
- `skills/notebook-bundle/SKILL.md` (neu) — Skill-Definition, Trigger ("NotebookLM-Bundle", "Bundle für NotebookLM erzeugen"), User-Warning bzgl Verbatim-Garantie
- `skills/notebook-bundle/scripts/bundle.py` (neu) — Bundle-Builder: liest Vault-Selection, konkateniert PDFs (PyPDF2-merge), generiert Bibliographie-Cover (1 Seite CSL-formatiert) und TOC (1 Seite)
- `skills/notebook-bundle/scripts/cover_pdf.py` (neu) — Cover-PDF-Generator: aus Paper-Liste eine 1-Seiten-PDF (Bibliographie + TOC mit Seitenzahlen)
- `tests/test_notebook_bundle.py` (neu) — Unit-Tests: 5 Mock-PDFs (je 30 Seiten Lorem-Ipsum), Verify Bundle hat alle 150 Seiten + Cover + TOC, Verify Output-Pfad-Pattern
- `tests/fixtures/notebook_bundle/` (neu) — 5 kleine PDFs (3-5 Seiten reichen für Test) + Vault-Selection-JSON
- `docs/skills/notebook-bundle.md` (neu, optional) — User-Doku: NotebookLM-Upload-Flow Schritt-für-Schritt, **Warnung dass NotebookLM-Antworten nicht verbatim-garantiert sind**

### Out-of-scope (explizit)
- Automatischer Upload zu NotebookLM (UI-Browser-Automation)
- Volltext-Extraction für eigene Bundle-Suche (NotebookLM macht das)
- OCR von gescannten PDFs (Annahme: PDFs sind text-extrahierbar; Skill warnt sonst)

### Risiken
- PDF-Merge-Größenlimits (NotebookLM hat 500MB pro Source). Bundle-PDF > 500MB → Skill teilt in Multi-Bundle auf
- Cover/TOC mit Reportlab oder Fpdf2: zusätzliche Dep? Lieber pure PyPDF2 + Text-Page-Helper, sonst pyfpdf<3MB
- Vault-Selection-API: Top-N pro Cluster via cluster-visualizer wiederverwenden ODER explizite Selection-Liste vom User

### Aufwandsschätzung
- ~6 Files, ~300 LoC, ~3h L1-Time

---

## Parallel-Dispatch-Plan

Phase 2: Beide Chunks (A + B) gleichzeitig spawnen — keine Dependencies, kein File-Overlap.
Phase 3 (Gates B + C): Parallel-Review pro Chunk.
Phase 4 (Polish + Code-Review): Parallel.
Phase 5 (PR + CI): Parallel.
Phase 6 (Coverage): Parallel.
Phase 7 (Merge): User-autorisiert (laut Session-Direktive), Dep-Order spielt keine Rolle da unabhängig.

## L0-Notes
- Beide Tickets als "GOOD" klassifiziert in Phase 0.5 → kein Improver-Run nötig.
- Vault-API stabil seit v5.x — keine Vault-Änderung erwartet (höchstens triviale `import_zotero_items`-Wrapper-Funktion).
- pyzotero ist optionale Dep — Skill prüft Vorhandensein und gibt klare Fehlermeldung bei fehlender Installation.
- NotebookLM-Bundle ist 100 % User-driven Manual-Flow — kein API-Aufruf, kein Auth-Bedarf.
