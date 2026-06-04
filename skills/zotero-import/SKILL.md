---
name: zotero-import
description: >
  Verwende diesen Skill wenn der User Zotero-Items in den Vault importieren möchte.
  Trigger-Phrasen: "Zotero importieren", "Bibliothek einlesen", "Bibliothek synchronisieren", "Zotero sync".
  Holt Items und PDF-Attachments aus einer Zotero-Library via pyzotero.
  Dedupliziert via DOI/ISBN ("Prüfung / Deduplication" via normalisierten Identifikatoren).
  Lädt PDFs in die Files-API hoch und cached file_ids. Read-only — kein Push zurück.
triggers:
  - "Zotero importieren"
  - "Bibliothek synchronisieren"
  - "Zotero sync"
  - "Zotero-Bibliothek importieren"
tools:
  - Bash
security:
  - api_key_source: "~/.academic-research/config.yaml (0600)"
  - network_allowlist: ["api.zotero.org"]
  - no_push_to_zotero: true
---

# Zotero-Import Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Blöcke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfährst.

## Zweck

Holt alle Items und PDF-Attachments aus einer Zotero-Library (user oder group)
und importiert sie in den academic-research Vault. Idempotent: wiederholter
Aufruf erstellt keine Duplikate (Items mit DOI/ISBN).

## Voraussetzungen

### 1. pyzotero installieren

```bash
pip install 'pyzotero>=1.5'
```

### 2. Config anlegen

Datei: `~/.academic-research/config.yaml`

```yaml
zotero_api_key: "DEIN_ZOTERO_API_KEY"
zotero_library_id: "DEINE_LIBRARY_ID"
zotero_library_type: "group"   # oder "user"
```

Permissions setzen (Pflicht):

```bash
chmod 0600 ~/.academic-research/config.yaml
```

**Hinweis:** Der API-Key ist ein persönliches Credential. Er wird niemals geloggt,
in den Vault geschrieben oder im PR-Diff sichtbar.

### 3. Zotero API-Key erstellen

1. https://www.zotero.org/settings/keys aufrufen
2. "Create new private key" → Read-only für die gewünschte Library
3. Key in config.yaml eintragen

## Verwendung

### Automatisch (Skill-Trigger)

Claude erkennt folgende Phrasen und führt den Import aus:
- "Zotero importieren"
- "Bibliothek synchronisieren"
- "Zotero sync"

### Manuell

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/zotero-import/scripts/zotero_pull.py \
  --config ~/.academic-research/config.yaml \
  --db vault.db
```

## Verhalten

1. Config laden und 0600-Permissions prüfen
2. Alle Items aus Zotero holen (paginiert via `zot.everything()`)
3. Für jedes Item: DOI/ISBN-Dedup gegen Vault
4. Neue Items: `vault.add_paper()` + ggf. PDF-Attachment herunterladen
5. PDFs: `vault.ensure_file()` → Files-API-Upload + file_id cachen
6. Ergebnis ausgeben: N importiert, M übersprungen, Fehler

## Sicherheitshinweise

- **Read-only**: Kein Schreiben zurück nach Zotero
- **Netz-Allowlist**: Nur `api.zotero.org` (via pyzotero)
- **Credentials**: Nur in `~/.academic-research/config.yaml` mit 0600

## Bekannte Einschränkungen

- Items ohne DOI und ISBN können nicht dedupliziert werden — sie werden bei
  jedem Import neu angelegt
- Nur das erste PDF-Attachment pro Item wird verarbeitet
- Annotations, Notes und verschachtelte Attachments werden nicht importiert
