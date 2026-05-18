# Migration Guide: v5.x → v6.x

**Gilt für:** Alle Versionen ≥ v5.0 → v6.5  
**Erstellt:** 2026-05-18 · **Bezug:** CHANGELOG.md, docs/AUDIT-v6-vault.md

---

## 1. Was ist neu in v6?

v6 ist keine reine Erweiterung — es ist eine Architektur-Veränderung. Die größten Unterschiede:

| Bereich | v5.x | v6.x |
|---------|------|------|
| **Literatur-Speicherung** | `literature_state.md` (flaches Markdown) | **Vault-MCP-Server** (SQLite + FTS5 + sqlite-vec) |
| **Zitat-Pfad** | `quote-extractor` → JSON-Datei | `quote-extractor` → `vault.add_quote()` |
| **Kapitel schreiben** | `chapter-writer` liest `literature_state.md` | `chapter-writer` nutzt `vault.find_quotes()` |
| **Halluzinationsschutz** | Soft (Hinweise in Skills) | **Hart** — `verbatim-guard`-Hook blockt unbekannte Zitate |
| **Buch-Handling** | Nicht unterstützt | `book-handler`-Skill + `book-fetcher`-Agent (8-Tier) |
| **Hochschul-Zugänge** | Nur Leibniz FH hardcoded | **Per-Uni-Profile** (`library-profiles/<uni>.yaml`) |
| **Token-Effizienz** | base64-PDFs bei jedem Aufruf | Files-API-Cache + 1h-TTL Prompt-Caching |
| **Entscheidungs-Persistenz** | Verloren nach Session-Compaction | `vault.add_decision()` + Decision-Log-Hook |
| **Hooks** | Keine | 4 Hooks: verbatim-guard, pre-compact, post-tool-use-decisions, mid-session-reinforcement |

**Kompatibilität:** `literature_state.md` bleibt als read-only Snapshot-Export aus dem Vault erhalten. Bestehende Markdown-Workflows laufen weiter — sie schreiben nur nicht mehr in die Datei.

---

## 2. `literature_state.md` → Vault migrieren

### Was passiert bei der Migration?

Das Migrations-Skript liest `literature_state.md` aus deinem Projekt-Ordner und fügt alle gefundenen Quellen als `papers`-Einträge in den Vault ein. PDFs werden, falls vorhanden, ebenfalls registriert.

### Automatische Migration

Im Projekt-Ordner:

```
/academic-research:setup --migrate-v5
```

Das Setup fragt:

```
literature_state.md gefunden (42 Einträge).
In Vault migrieren? [y/n] → y

Migriere... 42/42 Einträge übertragen.
PDFs registriert: 38/42 (4 ohne lokale PDF-Datei, nur Metadaten).
literature_state.md bleibt als Backup erhalten.
```

### Manuelle Migration (Fallback)

Falls die automatische Migration nicht klappt:

```bash
~/.academic-research/venv/bin/python scripts/migrate_v5.py \
  --literature-state ./literature_state.md \
  --vault ~/.academic-research/projects/<slug>/vault.db
```

### Nach der Migration prüfen

```
vault.stats()
```

Sollte die migrierten Papers anzeigen. Dann Probe-Suche:

```
Welche Quellen im Vault behandeln [dein Thema]?
```

### Kann ich `literature_state.md` danach löschen?

Nein — nicht nötig, aber auch kein Problem. Das Plugin liest sie weiterhin als Snapshot-Export, schreibt aber nur noch in den Vault. Wenn du sie löscht, fehlt sie als manueller Blick-Überblick — aber alle Funktionen laufen über den Vault.

---

## 3. Skill-Änderungen

### Neue Skills in v6.x

| Skill | Seit | Zweck |
|-------|------|-------|
| `book-handler` | v6.0 | ISBN/Titel → Metadaten → OPAC → PDF-Verarbeitung |
| `zotero-import` | v6.3 | pyzotero-Pull mit Vault-Dedup |
| `notebook-bundle` | v6.3 | PDF-Pack für NotebookLM |
| `prisma-flow` | v6.4 | PRISMA-2020-Diagramm + Checkliste |
| `material-passport` | v6.4 | Repro-Lock für Artefakte |
| `citation-style-import` | v6.4 | CSL-Stile aus CSL-Repository laden |
| `cluster-visualizer` | v6.4 | Mermaid-Cluster-Diagramm |
| `latex-export` | v6.5 | Markdown → `.tex` + `.bib` |
| `reading-list-import` | v6.5 | Listen → Vault |
| `topic-brainstorm` | v6.5 | Themen-Kandidaten mit Scores |
| `grant-proposal` | v6.5 | DFG/BMBF/EU-Antragsstruktur (opt-in) |
| `conference-poster` | v6.5 | A0-Poster-Layout (opt-in) |
| `reviewer-response` | v6.5 | Point-by-point Response-Letter (opt-in) |
| `humanizer-de` | v6.0 | Anti-KI-Audit (als globaler Skill integriert) |

### Modifizierte Skills

| Skill | Was änderte sich |
|-------|-----------------|
| `chapter-writer` | Liest via `vault.find_quotes()` statt `literature_state.md`. Ruft `humanizer-de(audit)` vor `quality-reviewer` auf. |
| `citation-extraction` | Schreibt Zitate via `vault.add_quote()`. 3 neue Formate: MLA, Vancouver, Springer Author-Date. |
| `style-evaluator` | Triggert `humanizer-de` als Subagent bei akademischen Abschlussarbeiten. |
| `source-quality-audit` | Warnt wenn > 30 % der Quellen nur Metadaten (kein Volltext). |

### Unveränderte Skills (rückwärtskompatibel)

`academic-context`, `research-question-refiner`, `advisor`, `methodology-advisor`, `literature-gap-analysis`, `plagiarism-check`, `abstract-generator`, `title-generator`, `submission-checker` — keine Breaking Changes.

---

## 4. Hooks installieren

v6.x installiert vier Hooks. Das Setup erledigt das automatisch. Zur manuellen Überprüfung:

```bash
cat ~/.claude/plugins/cache/academic-research/hooks/hooks.json
```

Sollte vier Einträge zeigen:

| Hook | Trigger | Zweck |
|------|---------|-------|
| `verbatim-guard.mjs` | `PreToolUse(Write)` für `kapitel/*.md` | Zitat-Validation gegen Vault |
| `pre-compact.mjs` | `PreCompact` | Snapshot-Backup vor Compaction |
| `post-tool-use-decisions.mjs` | `PostToolUse(Write)` für `*.md` | Decision-Log |
| `mid-session-reinforcement.mjs` | `SessionMid` | Anti-Fabrikations-Erinnerung |

### Manuelle Hook-Aktivierung

Falls die Hooks nicht automatisch registriert wurden:

```
/academic-research:setup
```

Das Setup re-registriert alle Hooks idempotent.

### verbatim-guard verhält sich anders als erwartet?

Der `verbatim-guard` blockt Kapitel-Writes, wenn ein Zitat im Text nicht im Vault gefunden wird. Das ist kein Bug — das ist der Halluzinationsschutz:

```
# Blockiert, weil Zitat nicht verifiziert
chapter-writer → Write(kapitel/02-theorie.md) → verbatim-guard → BLOCKED

# Lösung: Zitat erst aus PDF holen
"Extrahiere dieses Zitat aus dem PDF."
→ quote-extractor → vault.add_quote() → verbatim in Vault
→ chapter-writer → Write → verbatim-guard → OK
```

---

## 5. Per-Uni-Profil aktivieren

Per-Uni-Profile konfigurieren Bibliotheks-Zugänge (HAN, Shibboleth, EZproxy) und lizenzierte Sites für den `book-fetcher`.

### Schritt 1 — Setup mit Profil-Auswahl

```
/academic-research:setup
# → "Hochschul-Profil auswählen?" → ja
# → Liste der verfügbaren Profile
```

Oder direkt:

```
/academic-research:setup --uni leibniz-fh
```

Verfügbare Profile: `leibniz-fh`, `tum`, `rwth-aachen`, `fau-erlangen`, `template-han`, `template-shibboleth`, `template-ezproxy`, `template-oa-only`.

### Schritt 2 — Eigenes Profil anlegen

```bash
cp ~/.claude/plugins/cache/academic-research/library-profiles/template-han.yaml \
   ~/.academic-research/library-profiles/meine-uni.yaml
```

Datei anpassen (`uni`, `auth_url`, `credentials_keys`, `licensed_sites`):

```yaml
uni: meine-uni
display_name: "Meine Hochschule"
auth_type: HAN
auth_url: https://han.meine-uni.de
credentials_keys:
  - han_user
  - han_password
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
proxy_pattern: "https://{site-with-dots-replaced-by-dashes}.han.meine-uni.de"
```

### Schritt 3 — Profil aktivieren

```
/academic-research:setup --uni meine-uni
```

Das erzeugt `~/.academic-research/library-profiles/active.yaml`.

### Zugangsdaten hinterlegen

Zugangsdaten gehören **nicht** in die YAML-Datei. Sie werden beim ersten Buch-Fetch interaktiv abgefragt und verschlüsselt unter `~/.academic-research/config.yaml` gespeichert:

```yaml
credentials:
  han_user: "vorname.nachname"
  han_password: "<verschlüsselt>"
```

Die Verschlüsselung nutzt macOS Keychain (macOS) bzw. GNOME Keyring (Linux) wenn verfügbar, sonst Base64 (kein echter Schutz — nur für lokale Nutzung).

---

## 6. Vault einrichten

### Automatisch (empfohlen)

```
/academic-research:setup
```

Richtet `mcp/academic_vault/` ein, erstellt `vault.db` unter `~/.academic-research/projects/<slug>/vault.db` und registriert den MCP-Server.

### Vault-Status prüfen

```
vault.stats()
```

Ausgabe (Beispiel):

```
papers: 42
quotes: 187
decisions: 12
score_snapshots: 89
figures: 23
db_size: 4.2 MB
files_api_cached: 38
```

### Vault für neues Projekt initialisieren

In jedem neuen Facharbeit-Ordner:

```
/academic-research:setup
```

Das Setup erkennt den Ordner und legt automatisch einen projekt-spezifischen Vault an (Slug aus Ordner-Name abgeleitet).

### Vault-Backup und Restore

```bash
# Manuelles Backup
/academic-research:history --snapshot

# Restore eines bestimmten Snapshots
/academic-research:history --restore 2026-05-10T14:30:00
```

Automatische Backups werden vom `pre-compact.mjs`-Hook vor jeder Claude-Compaction unter `~/.academic-research/snapshots/<slug>/` abgelegt.

---

## 7. SciHub-Opt-in (optional)

SciHub ist **per Default DEAKTIVIERT**. Opt-in nur nach expliziter Bestätigung beim Setup:

```
/academic-research:setup
# → "SciHub-Tier aktivieren? (Rechtlich umstritten — Nutzung auf deine eigene Verantwortung)"
# → nur bei y wird der scihub-fetcher-Agent aktiviert
```

### Was passiert bei Aktivierung?

- `scihub_optin: true` in `~/.academic-research/library-profiles/active.yaml`
- `book-fetcher` fügt SciHub als letzten Fallback hinzu (nach allen anderen Tiers)
- Jeder via SciHub geholte Volltext bekommt im Vault `provenance: scihub`
- Im Output erscheint der Hinweis: *„Quelle via SciHub bezogen — bitte zusätzlich legalen Zugriff klären."*

### Opt-in rückgängig machen

```bash
# Manuell in active.yaml
sed -i 's/scihub_optin: true/scihub_optin: false/' \
  ~/.academic-research/library-profiles/active.yaml
```

Oder `/academic-research:setup` erneut ausführen — der Setup-Wizard fragt neu nach.

> [!CAUTION]
> SciHub operiert rechtlich in einer umstrittenen Zone. Die Nutzung kann in deinem Land gegen das Urheberrecht verstoßen. Du trägst die alleinige rechtliche Verantwortung.

---

## 8. Troubleshooting

### Migration schlägt fehl: `literature_state.md` nicht parsbar

```bash
# Zeige die ersten 50 Zeilen zur Fehleranalyse
head -50 ./literature_state.md

# Migration mit Verbose-Logging
~/.academic-research/venv/bin/python scripts/migrate_v5.py \
  --literature-state ./literature_state.md \
  --vault ~/.academic-research/projects/<slug>/vault.db \
  --verbose
```

Häufigste Ursache: Unvollständige `## [paper_id]`-Blöcke in der Datei. Im Verbose-Modus werden die fehlerhaften Einträge angezeigt.

### Vault nicht gefunden nach Update

```
/academic-research:setup
```

Setup re-initialisiert den Vault-MCP-Server und alle Abhängigkeiten.

### book-fetcher schlägt für alle Quellen fehl

1. Per-Uni-Profil prüfen: `cat ~/.academic-research/library-profiles/active.yaml`
2. `browser-use doctor` — prüft Browser-Installation
3. auth-helper testen: `"/academic-research:fetch --test-auth"`

### verbatim-guard blockiert zu aggressiv

Der Guard prüft exakten String-Match. Bei leichten Abweichungen (Leerzeichen, Anführungszeichen-Typ):

```
"Verifiziere dieses Zitat gegen den Vault und korrigiere es falls nötig."
[Zitat einfügen]
```

`quote-extractor` holt das korrekte Verbatim aus dem PDF und schreibt es in den Vault.

### humanizer-de nicht gefunden

`humanizer-de` ist ein globaler Skill — nicht plugin-intern. Setup prüft Existenz und warnt falls er fehlt:

```
/academic-research:setup
# → prüft, ob humanizer-de-Skill verfügbar ist
# → falls nicht: Hinweis mit Installations-Link
```

### Hooks werden nicht ausgeführt

```bash
# Hooks-Status prüfen
cat ~/.claude/plugins/cache/academic-research/hooks/hooks.json

# Oder in Claude Code
/academic-research:setup
# → "Hooks neu registrieren?" → y
```

### `vault.stats()` zeigt 0 papers nach Migration

Das Migrations-Skript erzeugt die DB nicht selbst — sie muss vorher vom Setup initialisiert worden sein:

```bash
# Reihenfolge beachten:
# 1. Setup laufen lassen (initialisiert vault.db)
/academic-research:setup

# 2. Dann migrieren
/academic-research:setup --migrate-v5
```

---

## Schnell-Referenz: Häufige v5-Kommandos in v6

| v5-Workflow | v6-Äquivalent |
|-------------|--------------|
| `chapter-writer` lädt `literature_state.md` | Vault liefert Zitate automatisch via `vault.find_quotes()` |
| Manuelle Zitat-Suche in PDF | *„Extrahiere Zitat auf Seite X aus [Paper]."* → `quote-extractor` → Vault |
| Buch manuell raussuchen | `/academic-research:fetch "[Titel]"` |
| Literaturliste von Doz. abtippen | *„Importiere diese Quellenliste:"* + Inhalt → `reading-list-import` |
| Keine Entscheidungs-Persistenz | Entscheidungen automatisch via Decision-Log-Hook |
| Stil-Check | `/academic-research:humanize kapitel/03.md` |
| Kein PRISMA | *„Erstelle PRISMA-Flow"* → `prisma-flow`-Skill |
