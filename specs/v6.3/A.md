# Spec — Chunk A: Zotero-Import (#88)

## Ziel

Skill `zotero-import` holt Items und PDF-Attachments aus einer Zotero-Library
(user oder group) via pyzotero, dedupliziert gegen den Vault (DOI/ISBN),
lädt PDFs in die Files-API hoch und cacht file_ids.

---

## Architektur

### Komponenten

| Datei | Rolle |
|---|---|
| `skills/zotero-import/SKILL.md` | Skill-Defintion (Trigger, LLM-Instruktionen, Tool-Whitelist) |
| `skills/zotero-import/scripts/zotero_pull.py` | Pure-Python-Logik (kein LLM), aufrufbar via `python zotero_pull.py` |
| `scripts/requirements.txt` | `pyzotero>=1.5` (optional, Kommentar) |
| `tests/test_zotero_import.py` | pytest-Suite, 6+ Tests |
| `tests/fixtures/zotero_library.json` | 50-Item-Mock-Library |
| `tests/fixtures/zotero_attachments/` | 2 minimale Mock-PDFs |

MCP-Server (`mcp/academic_vault/server.py`) wird **nicht** geändert —
`add_paper` und `ensure_file` sind bereits vorhanden und werden direkt
aus `zotero_pull.py` importiert.

---

## Config

Pfad: `~/.academic-research/config.yaml`
Permissions: 0600 — Skript prüft beim Start, wirft `PermissionError` bei abweichenden Perms.

Relevante Felder:
```yaml
zotero_api_key: "..."        # Niemals loggen
zotero_library_id: "12345"
zotero_library_type: "group" # oder "user"
```

---

## zotero_pull.py — Datenfluss

```
1. load_config(path) → prüft 0600, liest yaml
2. ZoteroPuller(api_key, library_id, library_type)
3. puller.fetch_items(limit=None) → Liste[ZoteroItem]
4. puller.fetch_attachments(item_key) → Liste[ZoteroAttachment]
5. deduplicate_against_vault(items, db_path) → neue Items (ohne DOI/ISBN-Treffer im Vault)
6. für jedes neue Item:
   a. add_paper(db_path, paper_id, csl_json, doi=..., isbn=..., pdf_path=None)
   b. für jedes PDF-Attachment:
      - Datei temporär herunterladen (pyzotero download_attachments)
      - add_paper(..., pdf_path=local_path)
      - ensure_file(db_path, paper_id, api_key=anthropic_api_key)
7. Rückgabe: ImportResult(imported=N, skipped=M, errors=[...])
```

---

## Dedup-Logik

`deduplicate_against_vault(items, db_path)`:
- Für jedes Item: normalisiere DOI (lowercase, strip https://doi.org/)
- SELECT paper_id FROM papers WHERE doi = ? (normiert)
- Wenn kein DOI: gleiche Logik für ISBN
- Wenn kein Treffer → Item ist neu
- Items ohne DOI und ISBN werden **immer** importiert (kein DOI = keine eindeutige Dedup-Basis)

---

## Sicherheits-Constraints (HART)

- `zotero_api_key` erscheint NIEMALS in: Logs, Vault-DB, PR-Diffs, Test-Fixtures
- Config-Datei: 0600-Check beim Load (analog v6.2 auth-helper-Pattern)
- Tests: pyzotero vollständig gemockt, keine echten API-Calls
- Allowlist: nur `api.zotero.org` (pyzotero kümmert sich; im SKILL.md dokumentiert)

---

## Tests (6 min.)

| Test | Was |
|---|---|
| `test_smoke_import_single_item` | 1 Item → 1 Paper im Vault |
| `test_50_items_all_imported` | 50-Item-Fixture → alle 50 im Vault |
| `test_rerun_no_duplicates` | 2. Pull → 0 neue Papers (alle per DOI/ISBN dedupliziert) |
| `test_missing_doi_always_imported` | Item ohne DOI/ISBN → trotzdem importiert |
| `test_pdf_attachment_uploaded_file_id_cached` | PDF-Attachment → ensure_file gecalled, file_id nicht leer |
| `test_config_perm_check` | config.yaml mit 0644 → PermissionError |

---

## SKILL.md — Trigger

```
Trigger: "Zotero importieren", "Bibliothek synchronisieren", "Zotero sync"
```

Instruktion: Skill ruft `python skills/zotero-import/scripts/zotero_pull.py`
auf und gibt ImportResult zurück.

---

## Out of Scope

- Push zurück nach Zotero
- Bidirektionale Sync
- Annotations/Notes aus Zotero
- OAuth — nur API-Key
