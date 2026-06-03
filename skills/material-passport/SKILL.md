---
name: material-passport
description: >
  Verwende diesen Skill wenn der User ein Reproduzierbarkeits-Manifest erstellen
  oder das Projekt fuer die Abgabe finalisieren moechte.
  Trigger-Phrasen: "Reproduzierbarkeits-Manifest / Material-Passport erstellen",
  "Artefakt sichern", "Abgabe vorbereiten", "Vault sperren", "Repro-Lock", "material-passport.json".
  Exporttyp: "Prüfung / Validation" via JSON-Schema.
  Exportiert alle relevanten Metadaten (paper_ids, DOIs, Scores, Algo-Version,
  Modellversionen, PDF-Hashes, Decision-Snapshot) als material-passport.json
  und ergaenzt kapitel/methodik.md automatisch um einen Reproduzierbarkeits-Block.
triggers:
  - "Reproduzierbarkeits-Manifest"
  - "Material-Passport erstellen"
  - "Abgabe vorbereiten"
  - "Vault sperren"
  - "Repro-Lock"
  - "material-passport.json"
  - "Reproduzierbarkeit dokumentieren"
tools:
  - Bash
---

# Material-Passport Skill

> **Gemeinsames Preamble laden:** Lies `skills/_common/preamble.md`
> und befolge alle dort definierten Bloecke (Vorbedingungen, Keine Fabrikation,
> Aktivierung, Abgrenzung), bevor du mit diesem Skill-spezifischen Inhalt
> fortfaehrst.

---

## Zweck

Erstellt einen vollstaendigen Material-Passport fuer das Forschungsprojekt:

- **material-passport.json** — maschinenlesbares Manifest mit allen Metadaten
- **kapitel/methodik.md** — erhaelt automatisch einen `## Reproduzierbarkeit`-Block
- **Repro-Lock** (optional) — sperrt den Vault nach Abgabe read-only

Der Passport ermoeglicht vollstaendige Reproduzierbarkeit: Dritte koennen nachvollziehen,
welche Paper, Scores, Algorithmus-Version und Modellversionen verwendet wurden.

---

## Trigger-Erkennung

Aktiviert bei:
- "Reproduzierbarkeits-Manifest erstellen"
- "Material-Passport"
- "Abgabe vorbereiten"
- "Vault fuer Abgabe sperren" / "Repro-Lock"
- "material-passport.json generieren"
- "Reproduzierbarkeit dokumentieren"

---

## Systemanforderungen

1. **Vault-DB** vorhanden (Standard: `vault.db` im CWD oder via `VAULT_DB_PATH`)
2. **Paper im Vault** eingetragen (via `vault.add_paper`)
3. **kapitel/methodik.md** existiert (wird ggf. angelegt)
4. Python-Abhaengigkeiten installiert: `pip install -r scripts/requirements.txt`

---

## Workflow

### Schritt 1: User-Anfrage verstehen

Klaere bei Bedarf:
- Soll der Vault nach dem Export **gesperrt** werden? (Repro-Lock — irreversibel)
  Wenn unklar: **immer nachfragen** bevor `--lock` gesetzt wird.
- Projekt-Slug (Standard: aus Vault-DB oder aktuelles Verzeichnis)

### Schritt 2: build_passport.py ausfuehren

**Ohne Repro-Lock** (normaler Export):
```bash
python skills/material-passport/scripts/build_passport.py \
  --db vault.db \
  --slug <projekt-slug> \
  --output-dir . \
  --methodik kapitel/methodik.md
```

**Mit Repro-Lock** (Vault nach Export sperren):
```bash
python skills/material-passport/scripts/build_passport.py \
  --db vault.db \
  --slug <projekt-slug> \
  --output-dir . \
  --methodik kapitel/methodik.md \
  --lock
```

> **Achtung:** Der Repro-Lock ist **irreversibel**. Sobald `--lock` gesetzt wurde,
> koennen keine weiteren Paper oder Decisions in den Vault geschrieben werden.
> Den User **explizit bestaetigen lassen**, bevor `--lock` ausgefuehrt wird.

### Schritt 3: Ergebnis an User melden

Ausgabe nach erfolgreichem Export:
```
Material-Passport exportiert: ./material-passport.json
methodik.md aktualisiert: kapitel/methodik.md
```

Vollstaendige Meldung an User:
```
Material-Passport erstellt:
  Datei:   ./material-passport.json
  Slug:    <projekt-slug>
  Paper:   <N> eingetragen
  DOIs:    <M> mit DOI
  Decisions: <K> aktive Entscheidungen

kapitel/methodik.md wurde um '## Reproduzierbarkeit' ergaenzt.
```

Bei aktivem Repro-Lock zusaetzlich:
```
Vault gesperrt (Repro-Lock aktiv).
Keine weiteren Aenderungen am Vault moeglich.
```

---

## Fehlerfaelle

| Situation | Meldung | Massnahme |
|-----------|---------|-----------|
| Vault bereits gesperrt | `FEHLER: Vault fuer Slug '...' ist gesperrt` | Kein erneuter Export — Vault ist read-only |
| Vault-DB nicht gefunden | `FEHLER: ...` | Pfad pruefen oder `VAULT_DB_PATH` setzen |
| methodik.md nicht schreibbar | `WARNUNG: methodik.md konnte nicht aktualisiert werden` | Berechtigungen pruefen; Passport wurde trotzdem erstellt |

---

## material-passport.json — Inhalt

Das JSON-Dokument enthaelt:

| Feld | Beschreibung |
|------|-------------|
| `slug` | Projekt-Slug |
| `paper_ids` | Liste aller Paper-IDs im Vault |
| `dois` | Liste aller vorhandenen DOIs |
| `download_tier` | `full` (PDFs vorhanden) oder `metadata-only` |
| `scores_5d` | Aktuelle 5D-Scores je Paper |
| `score_algo_version` | Version des Scoring-Algorithmus |
| `plugin_version` | Version des academic-research Plugins |
| `model_versions` | Eingesetzte KI-Modellversionen |
| `per_uni_profile_hash` | Hash des Uni-Bewertungsprofils (optional) |
| `decisions_snapshot` | Snapshot aller aktiven Decisions |
| `pdf_sha256_hashes` | SHA-256-Hashes aller vorhandenen PDFs |
| `created_at` | Unix-Timestamp des Exports |
| `passport_hash` | SHA-256 ueber alle uebrigen Felder |

Das Dokument wird gegen das JSON-Schema in
`academic_vault/material-passport.schema.json` validiert.

---

## Abgrenzung

- Kein automatisches Backup oder Archivierung — nur Export
- Kein Hochladen in externe Systeme
- Repro-Lock nur mit expliziter User-Bestaetigung
- Kein Loeschen vorhandener Vault-Daten
- JSON-Schema-Validierung erfolgt intern; bei Validierungsfehler wird kein File geschrieben
