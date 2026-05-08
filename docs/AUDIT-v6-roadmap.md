# Academic-Research v6 — Audit & Roadmap

**Erstellt:** 2026-05-07 · **Bezugsversion:** v5.4.0 · **Branch:** main
**Ziel:** Token-Halbierung, Buch-Handling auf Citations-API-Niveau, neuer
`/humanizer-de`-Workflow, semi-automatische Beschaffung nicht-OA-Quellen,
optionale Obsidian/Zotero/NotebookLM-Bridges.

---

## 1 · Executive Summary

Das Plugin macht heute, was es soll. Drei Schmerzpunkte limitieren den Sprung
auf das nächste Level:

1. **Token-Hunger.** Viele Skills laden komplette `references/`-Varianten,
   `chapter-writer` baut den Kontext jedes Mal neu auf, `relevance-scorer`
   batched zwar, aber PDFs werden bei jedem Folgecall re-uploaded statt
   per Files-API referenziert. **Ziel:** −50–70 % Input-Tokens auf typischen
   Sessions.
2. **Buch-Handling.** Der Pfad `quote-extractor` → `citation-extraction`
   funktioniert für Paper, aber nicht für Bücher: keine ISBN-Resolution,
   keine Kapitel-Schnitte, Seitenangaben aus Scan-PDFs unzuverlässig,
   PyPDF2 kann keine OCR. **Ziel:** Buch-Pfad mit korrekten Seitenangaben
   und Verbatim-Zitaten gleichwertig zu Papern.
3. **Kontext-Drift.** `academic_context.md` / `literature_state.md` /
   `writing_state.md` werden nicht versioniert oder bei langer Session
   nachgezogen. Bei Compaction gehen Entscheidungen (Zitierstil-Wahl,
   abgelehnte Quellen, Variant-References) verloren. **Ziel:** Memory-Tool
   + state-events.log + Snapshot-Hooks.

Plus 12 weitere Felder (siehe §4–§15).

---

## 2 · Schwachstellen heute (Befund)

### 2.1 Token-Lecks

| Stelle | Befund | Hebel |
|---|---|---|
| `chapter-writer` lädt `academic_context.md` + `literature_state.md` + Style-Variant pro Aufruf | ~6–10k Tokens fix | cache_control + Files-API |
| `quote-extractor` PDF base64 pro Call | 1 PDF ≈ 60–100 k Token, x N Aufrufe | `file_id` referenzieren statt base64 |
| `relevance-scorer` 10er-Batch nutzt 5min-TTL | Cache läuft bei Pause aus | `cache_control: {type: "ephemeral", ttl: "1h"}` |
| 13 Skills duplizieren `## Vorbedingungen` / `## Keine Fabrikation` / `## Aktivierung` | ~500 Token Overhead pro Skill | Shared `references/_common.md` per Hot-Link |
| Browser-Search-Schritt liefert volle DOM-Snapshots in Modell-Context | je Modul bis 30k Token | nur strukturierte Felder zurückgeben, raw Snapshot in `$SESSION_DIR/raw/` |
| `search.py` schreibt API-Roh-Antwort in `api_results.json` und Modell liest mit | unnötig | Modell liest nur das normalisierte Schema |

### 2.2 Buch-Schwachstellen

- **Kein Buch-Pfad in `search.py`.** APIs sind auf Paper getunt; Bücher
  haben oft keine DOI, dafür aber ISBN/OCLC.
- **Seitenangaben:** Die Citations-API ist seitengenau für **PDF-Pages**.
  Bei Scan-PDFs ohne Text-Layer stimmt aber `start_page_number` nicht
  zwingend mit der **gedruckten** Seitenzahl überein (PDF-Seite vs.
  Buchseite — Vorwort/Inhalt verschieben Indizes oft um 10–30).
- **Zitat-Verbatim:** PyPDF2 produziert bei Zwei-Spalten-Layout und
  Hyphenation Wort-Salat → der Verbatim-Match aus Citations-API zeigt
  den korrekten Text, aber `paper.pdf_text` (heuristik-Pfad ohne
  Citations) liefert verstümmelte Zitate.
- **Lange Bücher:** Über 600 Seiten reißt die PDF-Page-Limit-Grenze
  (200k-Modell: 100 Seiten max, 1M-Modell: 600 Seiten max). Kein
  Chunk-by-Chapter-Pfad vorhanden.
- **Kapitel-Granularität:** Bücher zitieren oft pro Kapitel mit
  eigenen Editor:innen. CSL-Felder `container-title`, `editor`,
  `chapter-number`, `page` werden im aktuellen Schema nicht erfasst.
- **OCR fehlt.** Scans aus dem Hochschul-OPAC (Tip-2-Online-Scans) sind
  Bilddateien ohne Text-Layer. Aktuell stiller Fail.

### 2.3 Kontext-/Erinnerungs-Drift

- `academic_context.md` ist die Single Source of Truth, aber niemand
  zwingt das Modell, sie nach Entscheidungen (z. B. „Wir nutzen IEEE
  statt APA") zu **überschreiben**.
- Nach Claude-Compaction verschwinden Bemerkungen wie „X habe ich
  schon abgelehnt, weil Y" → Nachfolge-Calls schlagen dieselbe Quelle
  wieder vor.
- Kein Decision-Log (`decisions.log` o. Ä.).

### 2.4 Workflow-Lücken

- Beschaffung nicht-OA-Quellen (≈ 40–60 % der Treffer in Wirtschaft)
  läuft heute manuell.
- KI-Stil-Erkennung ist auf den `style-evaluator`-Skill verteilt
  (`KI-Glanzschicht entfernen`), aber kein dedizierter `humanizer-de`-
  Pass mit Severity-Ranking + zweitem Audit.
- Keine Anbindung an Zotero/Obsidian/NotebookLM für Nutzer:innen, die
  diese Tools sowieso einsetzen.
- Kein PRISMA-Flow-Export für Systematic Reviews / Bachelorarbeiten,
  die Methodik-Transparenz erfordern.

---

## 3 · Felder Übersicht

| ID | Feld | Aufwand | Impact |
|----|------|---------|--------|
| F1 | Token-Effizienz (Cache + Files-API) | M | sehr hoch |
| F2 | Buch-Pfad (ISBN, Kapitel, OCR, Seitenmapping) | L | sehr hoch |
| F3 | Kontext-Persistenz (Memory-Tool + Decision-Log) | M | hoch |
| F4 | `/humanizer-de` als first-class Workflow | S | hoch |
| F5 | Beschaffungs-Excel (Fernleihe / Bibliotheks-Pickup) | S | hoch |
| F6 | Auto-Download-Pipeline mit fail-soft | M | mittel |
| F7 | Zotero-Bridge (Web-API v3) | M | mittel |
| F8 | Obsidian-Bridge (Vault-Sync) | S | mittel |
| F9 | NotebookLM-Bridge (manuell + optional CLI) | S | mittel |
| F10 | PRISMA-Flow Diagramm + Inclusion-Log | M | hoch (für Bachelor/Master) |
| F11 | Cluster-Visualisierung (Mermaid + Excel-Chart) | S | mittel |
| F12 | Versionierung des Projekt-Kontexts (Git-Integration) | S | mittel |
| F13 | Citation-Style-Erweiterung (CSL-JSON Import) | M | mittel |
| F14 | Reading-List-Modus (kuratierte Quellen) | S | niedrig |
| F15 | Eval-Suite Coverage (Buch-Cases) | M | hoch (Qualität) |
| F16 | Universal Book Fetcher (TIB, autonomes Navigieren, Per-Uni-Profile) | L | sehr hoch |

---

## 4 · F1 — Token-Effizienz

### 4.1 Files-API für PDFs

**Problem:** `quote-extractor` schickt heute `source.type: "base64"`. Bei
mehrfacher Verwendung desselben PDFs im selben Projekt wird dieselbe
Datei mehrmals upgeloadet.

**Lösung:**

1. Beim ersten Verarbeiten eines PDFs `client.beta.files.upload(...)`
   aufrufen, `file_id` in `pdf_status.json` schreiben.
2. Folgenden Calls nur noch:
   ```python
   {"type": "document", "source": {"type": "file", "file_id": fid},
    "citations": {"enabled": True}}
   ```
3. TTL-Tracking: file_ids ablaufen lassen wenn älter als Plugin-Konfig
   (`~/.academic-research/files_ttl_days`, Default 30).

**Trade-off:** Files-API ist Beta (`anthropic-beta: files-api-2025-04-14`)
und erfordert anthropic SDK ≥ 0.40.

### 4.2 Cache-Strategie umstellen

- `relevance-scorer`, `quote-extractor`, `chapter-writer`, `quality-reviewer`:
  `cache_control: {"type": "ephemeral", "ttl": "1h"}` auf System-Prompt
  (Anthropic änderte 6. März 2026 den Default zurück auf 5 min — ohne
  expliziten ttl zahlt man cache-write-Aufschlag mehrfach).
- Cache-Breakpoint **vor** das `documents[]`-Array, nicht danach. So bleibt
  der Agent-Prompt auch dann gecacht, wenn das PDF wechselt.

### 4.3 Skills schlanker

- Gemeinsame Pflicht-Blöcke (`Vorbedingungen`, `Keine Fabrikation`,
  `Abgrenzung`) in `skills/_common/preamble.md` extrahieren und per
  Markdown-Include linken.
- `references/<variant>.md` lazy laden — nicht im Skill-Body listen,
  sondern erst dann öffnen, wenn der Variant-Selector eine Datei
  fixiert hat.
- Browser-Snapshots **nicht** in Antwort-Context geben. Modell sieht
  nur das Schema-normalisierte Ergebnis (`title`, `authors`, …),
  Raw-DOM bleibt in `$SESSION_DIR/raw/` für Debug.

**Erwartung:** −30–50 % Input-Tokens bei `/search` und `/score`,
−60 % bei wiederholten Zitat-Extraktionen.

### 4.4 Batch-API für Bulk-Scoring

`relevance-scorer` über 50+ Papers → in Message-Batches-API auslagern.
50 % Discount, 1h-Latenz. Hook im `/search`-Command:
`--batch` Flag → Job submitten, Job-ID in `$SESSION_DIR/batch.json`,
Pickup über `/academic-research:history --batch <id>`.

---

## 5 · F2 — Buch-Pfad

### 5.1 Neuer Skill `book-handler`

**Trigger:** „Buch", „Monografie", „Sammelband", „Kapitel von …",
ISBN-Pattern (`\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d`).

**Pipeline:**

```
ISBN/Title → DNB SRU + OpenLibrary + GoogleBooks
          → Metadaten (CSL: book / chapter)
          → OPAC-Suche (verfügbar lokal? Standort? Signatur?)
          → DOAB / OAPEN (OA-Bücher)
          → falls PDF: Kapitel-Schnitt + OCR-Check + Seitenmapping
          → Eintrag in literature_state.md (type: book|chapter)
```

### 5.2 Kapitel-Schnitt

PDF-Inhaltsverzeichnis aus dem Outline-Tree (PyPDF2 `outline`) oder
Textextraktion. Pro Kapitel:

- `chunk_pdf.py --input book.pdf --chapter 3 --output chapter3.pdf`
- separater Citations-API-Call mit nur diesem Kapitel als Document
- spart Tokens (statt 600 Seiten nur 30) und hält die 100/600-Page-
  Limits ein.

### 5.3 Seitenmapping (PDF-Page ≠ Druck-Seite)

**Problem:** `start_page_number` aus Citations-API ist die **PDF-Seite**.
Druck-Seite kann um Vorwort/Inhalt versetzt sein.

**Fix:**

1. Beim ersten Buch-PDF-Verarbeiten: Modell scannt erste 30 PDF-Seiten,
   findet die erste **gedruckte** Seitenzahl `1` und speichert
   `page_offset = pdf_page - printed_page` in `pdf_status.json`.
2. Bei Citation-Output:
   `printed_page = api.start_page_number - page_offset`.
3. Sanity-Check: Modell schaut auf 2 zufällige weitere Seiten, ob
   das Offset stimmt — wenn nicht (Buch hat Doppelpaginierung,
   römische Vorseiten etc.), Offset-Map als JSON.

### 5.4 OCR-Path

- Detektion: PDF erste Seite hat `< 100` extrahierbare Zeichen → OCR-Flag.
- OCR-Tool: `ocrmypdf` (CLI) als Plugin-optional Dep.
- Bei OCR-Flag → Modell warnt User, fragt ob OCR laufen soll
  (lokal, dauert ~30 s/Seite). Nach OCR neuer PDF-Pfad.

### 5.5 CSL-Felder erweitern

`literature_state.md` Schema um `type: book | chapter | article-journal`
und chapter-spezifische Felder (`container-title`, `editor[]`,
`chapter`, `page-first`, `page-last`).

`citation-extraction/references/` neue Variante: `book-chapter-de.md`
mit Beispielen für DIN 1505, Harvard-de, APA-7 für Sammelbände.

---

## 6 · F3 — Kontext-Persistenz

### 6.1 Memory-Tool

`~/.academic-research/projects/<slug>/memory/` mit Anthropic-Memory-Tool
befüllen. Schema:

- `decisions.md` — chronologisch: Zitierstil, Methodik-Wahl, abgelehnte
  Quellen, Cluster-Definitionen
- `glossary.md` — projektspezifische Begriffe
- `style-overrides.md` — User-spezifische Stil-Präferenzen
  (z. B. „nutzt 'Wir' statt 'man'")

Alle Skills lesen Memory-Tool **vor** dem Hauptprompt → 0 Tokens für
Kontext-Wiederholung über Sessions hinweg.

### 6.2 Decision-Log Hook

Hook `PostToolUse` für `Write` mit Pfad-Match auf `*.md` im Projekt:
schreibt 1-Zeile in `decisions.log` mit Timestamp + Skill + Δ. Hilft
beim Auditing und ist die Vorlage für PRISMA-Flow.

### 6.3 Auto-Snapshot vor Compaction

Hook `PreCompact`: schreibt aktuellen `academic_context.md` +
`literature_state.md` + `writing_state.md` als Tarball nach
`~/.academic-research/snapshots/<slug>/<ts>.tgz`. Bei Bedarf
mit `/academic-research:history --restore <ts>` zurück.

---

## 7 · F4 — `/humanizer-de` Integration

### 7.1 Status

`humanizer-de` ist als globaler Skill bereits unter
`~/.codex/skills/humanizer-de/` (siehe Skill-Description: Anti-KI-Audit,
Severity-Ranking, Modi-System, Stimmkalibrierung). Keine Re-Implementation
nötig.

### 7.2 Integration in academic-research

Drei Punkte:

1. **`style-evaluator`** triggert `humanizer-de` als Subagent-Skill,
   wenn `output_target` ∈ {Bachelor, Master, Diplom, Dissertation}.
2. **`chapter-writer`** ruft `humanizer-de` im **Mode `audit`** vor
   `quality-reviewer` auf — Reihenfolge:
   ```
   draft → humanizer-de(audit) → quality-reviewer → final
   ```
3. **Neuer Slash-Command `/academic-research:humanize`** als
   eigenständiger Pass: liest `kapitel/<n>.md`, läuft Mode `deep`
   gegen humanizer-de, schreibt `kapitel/<n>.humanized.md` plus
   `kapitel/<n>.diff.md`.

### 7.3 Stimmkalibrierung

`humanizer-de` kennt Voice-Calibration aus User-Schreibproben.
Vorschlag: `~/.academic-research/projects/<slug>/voice-samples/`
für 3–5 eigene Texte des Users (frühere Hausarbeiten). Erstaktivierung
fragt nach Samples.

### 7.4 Trade-off

Weniger fluffige Symbolik = weniger LLM-Wow-Effekt. Funktion ist
**Schutz** vor KI-Detektoren wie Turnitin / GPTZero / OriginalityAI.
Default off in nicht-Hochschul-Projekten (siehe Best-Practice
„Overhead in Nicht-Facharbeit-Projekten deaktivieren").

---

## 8 · F5/F6 — Beschaffung & Auto-Download

### 8.1 5-Tier-Pipeline (heute) erweitern auf 8 Tiers

Aktuell: Unpaywall → CORE → Module-OA-URL → Direct-PDF → arXiv-Title.

Erweiterung:

6. **OpenAccessButton** (`api.openaccessbutton.org/find`)
7. **DOAB / OAPEN** für Bücher
8. **EuropePMC** (`europepmc.org/api`) für Biomedizin

### 8.2 Bibliotheks-Excel `pickup-list.xlsx`

**Trigger:** `/academic-research:pickup` (neuer Command).

Liest `literature_state.md`, filtert auf `source != open_access`,
ergänzt:

- OPAC-Standort + Signatur (über DAIA / `gbv.github.io/cdvost2018`)
- Status (verfügbar / ausgeliehen / Fernleihe nötig)
- Direktlink Fernleihe-Formular der Heim-Uni (User konfiguriert URL
  in `~/.academic-research/config.yaml`)
- ISBN-Barcode (Code128) als Excel-Bild für mobiles Scannen am Regal

Sheets:

1. **Vor Ort verfügbar** — Pickup-Reihenfolge nach Signatur sortiert
2. **Fernleihe** — fertig formatierte Anfrage-Texte (Title, Author,
   Year, ISBN/DOI) als Copy-Paste-Block pro Zeile
3. **Online OA** — Direktlinks
4. **Lizenz nötig** — proprietary, Hinweis auf Uni-VPN

### 8.3 Browser-Modul `library-pickup`

`browser-use`-Skript: loggt sich (HAN-Auth) ins Bibliotheks-Konto ein,
trägt automatisch Fernleihe-Bestellungen ein. **Opt-in**, weil
verbindlich (kostenpflichtig pro Anfrage).

### 8.4 PDF-Status-Workflow

```
literature_state.md  ─┬─► auto_download (8-tier)
                       ├─► via_opac (download-link)
                       ├─► fernleihe (manual_followup)
                       └─► self_uploaded (~/papers/)
```

Skill `source-quality-audit` warnt, wenn > 30 % der zitierten Quellen
nur Metadaten sind (kein Volltext) → Risiko für `quote-extractor`.

---

## 9 · F7/F8/F9 — Knowledge-Tool-Bridges

### 9.1 Zotero (F7)

- **Einseitige Sync**: `pyzotero` als optionale Dep.
- Neuer Skill `zotero-sync`: liest Zotero-Library (User-Key in
  `~/.academic-research/config.yaml`), mappt auf
  `literature_state.md`-Schema, dedupliziert per DOI/ISBN.
- **Zwei-Wege-Sync**: erst v6.1, weil OAuth1-Schreib-Auth fehleranfällig.
- Better-BibTeX-Export-File (`<vault>/zotero.bib`) auch ok für Pull-only.

### 9.2 Obsidian (F8)

- Neuer Skill `obsidian-export`: schreibt pro Paper eine Markdown-Datei
  in `<vault>/lit/<citekey>.md` mit Frontmatter (`title`, `authors`,
  `year`, `doi`, `tags: [academic-research, cluster-X]`) und Body
  (Abstract, Top-3-Zitate, Notizen).
- Cluster-MOC (`<vault>/lit/_clusters/<cluster>.md`) als Übersicht.
- Kompatibel mit ZotLit-Templates.

### 9.3 NotebookLM (F9)

- Kein offizielles API. Optionen:
  - **Manuell**: Skill `notebook-export` baut PDF-Bundle aus Top-N
    Papern + Bibliographie als ein PDF (via xlsx-Skill-Pattern, nur
    PDF-Pack), User uploadet selbst.
  - **Halb-automatisch**: `notebooklm-py` (unofficial) als optionale
    Dep für User mit Google-Account (Risiko: bricht bei UI-Updates).
- Use-Case: 1M-Token-Source-Grounding bei Büchern, die für unsere
  Citations-API zu groß sind. Abgrenzung: NotebookLM ersetzt **nicht**
  unseren Zitat-Pfad — Output dort ist nicht verbatim-garantiert.

### 9.4 Empfehlung

Default: Obsidian-Bridge (Markdown ist null-Lock-in). Zotero-Pull-Sync
für Nutzer:innen mit bestehender Library. NotebookLM nur bei
Riesen-Büchern (> 600 PDF-Seiten) als Triage-Tool, **nie** als
Zitationsquelle.

---

## 10 · F10 — PRISMA-Workflow

Bachelor-/Master-Arbeiten mit Methodik „Systematic Review" brauchen
einen PRISMA-Flow:

```
Identifikation (n=) → Screening (n=) → Eligibility (n=) → Included (n=)
```

**Implementierung:**

1. `/search` schreibt `n_identified` pro Modul.
2. Dedup-Schritt schreibt `n_after_dedup`.
3. `relevance-scorer` < 0.5 → `excluded_screening`.
4. `quality-reviewer` Ablehnung → `excluded_eligibility`.
5. Neuer Skill `prisma-flow` rendert Mermaid-Diagramm in
   `kapitel/methodik.md` und exportiert als PNG via
   Mermaid-CLI.
6. Begleitend `prisma-checklist.md` (27-Punkte-PRISMA-2020).

---

## 11 · F11 — Cluster-Visualisierung

- Excel-Sheet bereits da, aber statisch.
- Mermaid-Diagramm aus 5D-Scoring-Output: Cluster als Knoten,
  Querverbindungen (Co-Authors, Co-Citations) als Kanten. Im
  `kapitel/literatur.md` einbettbar.
- Optional: D3-HTML-Export für Browser-Browse (lokales File).

---

## 12 · F12 — Projekt-Versionierung

- Setup legt heute schon `.gitignore` an. Erweiterung:
  `git init` + initial commit der Bootstrap-Files automatisch
  (User-Opt-in im Setup).
- Hook `Stop`: Diff `academic_context.md` seit letztem Commit > 0
  → Modell schlägt `/academic-research:commit "..."` vor.
- Branch-Strategie für Methodik-Experimente
  („was wäre wenn ich qualitativ statt quantitativ arbeite") in
  Best-Practices dokumentieren.

---

## 13 · F13 — CSL-JSON Import

Aktuelle Variant-Selector-Logik (`apa.md`, `harvard.md` …) ist
hand-curated. CSL-Repository auf GitHub hat 10.000+ Stile.

**Lösung:** Skill `citation-style-import` lädt eine `.csl`-Datei
aus dem Repo (User gibt Stil-Name an), parst sie zu prompt-fähigen
Regeln. Ergebnis als neue Variant `references/custom-<style>.md`.

Trade-off: Volle CSL-Spec ist groß. Pragmatischer Ansatz: nur die
Felder formatieren, die `literature_state.md` kennt
(book, chapter, journal, conference).

---

## 14 · F14 — Reading-List-Modus

Manche Profs geben eine Lese-Liste vor. Aktuell muss der User die
händisch in `literature_state.md` tippen.

**Skill `reading-list-import`:**

- Input: PDF / Markdown / Plaintext mit Liste von Quellen.
- Pipeline: Anystyle (Ruby) oder eigener LLM-Parser → strukturierte
  Liste → DOI-/ISBN-Resolution → `literature_state.md`.

---

## 15 · F15 — Eval-Coverage

Heute: 16 Eval-Verzeichnisse, aber Buch-Cases fehlen. Neue Eval-Sets:

- `evals/book-handler/` — 5 Bücher (1 OA, 2 ISBN-only, 1 Scan-PDF,
  1 Sammelband mit Editor-Kapiteln)
- `evals/humanizer-de-pipeline/` — 3 Drafts vor/nach humanizer-de
- `evals/prisma-flow/` — 1 Mini-Review-Beispiel

Bestehende Evals um Token-Counts erweitern → Regression-Tests gegen
F1.

---

## 15a · F16 — Universal Book Fetcher (browser-use only)

### Constraint

**Nur `browser-use` CLI + Subagenten.** Keine API-basierte Discovery,
kein curl/wget, kein direktes Anthropic-Files-Upload. Jede Quelle wird
wie ein Mensch im Browser bedient. Begründung:

- Verlags-Auth (Shibboleth, HAN, EZproxy) liefert nur Browser-Sessions
- DNB/OpenLibrary-APIs sind nice-to-have, aber nicht der Kern-Wunsch
- User will ein **autonomes Subagenten-System** das auf Sites navigiert
- Memory-Direktive: "browser-use statt Playwright/MCP-API"

### Befund (Status quo)

- 9 Browser-Guides in `config/browser_guides/`, alle **such-zentriert**
  — Metadaten + URL holen, dann zurück. Kein Download-Step.
- Springer-Guide erwähnt "Download PDF"-Button, aber kein dokumentierter
  `browser-use`-Workflow für lokales Speichern.
- HAN-Login auf **Leibniz FH** hardcoded
- TIB.eu fehlt komplett — wichtigste DACH-Quelle (143 Mio Records,
  71 Mio Volltexte)
- Keine Subagenten für Site-Navigation. Heute macht das der Master-
  Modell-Loop selbst → frisst Tokens und ist fragil.

### Architektur (Subagenten-System)

```
                      ┌─────────────────────────┐
                      │  /academic-research:    │
                      │  fetch <isbn|doi|titel> │
                      └────────────┬────────────┘
                                   │
                      ┌────────────▼────────────┐
                      │  book-fetcher           │  ← Master-Subagent
                      │  (Sonnet)               │     entscheidet,
                      │  - Site-Strategie       │     wo gesucht wird
                      │  - Fallback-Kette       │
                      └─┬───┬───┬───┬───┬───┬──┘
                        │   │   │   │   │   │
       ┌────────────────┘   │   │   │   │   └────────────────┐
       ▼                    ▼   ▼   ▼   ▼                    ▼
   tib-fetcher       springer-fetcher   oapen-fetcher    generic-fetcher
   (Haiku)              (Sonnet)         (Haiku)         (Sonnet)
   nur tib.eu         nur SpringerLink   nur oapen.org   beliebige URL
   browser-use        browser-use        browser-use     browser-use
```

Jeder Site-Subagent ist ein **eigener Agent in `agents/`** mit:
- `tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]`
- `model: sonnet` für alle Site-Subagenten (browser-Navigation braucht
  zuverlässige DOM-Heuristik und Fehlertoleranz; Haiku scheitert hier
  zu oft an State-Output-Drift)
- maxTurns: 12–20 (Browser-Schritte sind langsam)
- nur ein Site-Wissen pro Agent → kleiner System-Prompt

### F16.1 — Site-Subagenten (browser-use only)

Neu unter `agents/`:

| Agent | Site | Model | Auth | Buch-Fokus |
|---|---|---|---|---|
| `tib-fetcher` | tib.eu Portal | sonnet | optional | hoch — viele OA-Bücher |
| `springer-book-fetcher` | link.springer.com | sonnet | Shibboleth/HAN | hoch — Lehrbücher |
| `oapen-fetcher` | oapen.org | sonnet | nein | sehr hoch — reine OA |
| `doabooks-fetcher` | directory.doabooks.org | sonnet | nein | sehr hoch — reine OA |
| `degruyter-fetcher` | degruyter.com | sonnet | Shibboleth/HAN | mittel — DACH Geistes |
| `nationallizenzen-fetcher` | nationallizenzen.de | sonnet | DFN-AAI | mittel |
| `ebook-central-fetcher` | ebookcentral.proquest.com | sonnet | HAN/EZproxy | mittel |
| `kvk-fetcher` | kvk.bibliothek.kit.edu | sonnet | nein | Meta-Discovery, 80+ Kataloge |
| `generic-fetcher` | beliebige URL | sonnet | je nach Profil | Fallback-Modus |

Pro Subagent: `agents/<name>.md` mit System-Prompt, der nur diese eine
Site kennt. Beispiel-Skelett `agents/tib-fetcher.md`:

```markdown
---
name: tib-fetcher
model: sonnet
description: |
  Holt Bücher und Texte von tib.eu (TIB-Portal, Hannover) per
  browser-use. Aufrufen mit ISBN, DOI oder Titel. Liefert Pfad zum
  heruntergeladenen PDF oder Failure-Reason zurück.
tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]
maxTurns: 15
---

# Auftrag

Du bedienst tib.eu wie ein Mensch. Nur browser-use.

## Standard-Flow

1. `browser-use open https://www.tib.eu/de/suchen?query=<URL-encoded-query>`
2. `browser-use state` → Treffer-Liste lesen
3. Plausibelster Treffer: Titel + Autor + Jahr matcht Input
4. `browser-use click <idx>` auf Treffer-Titel
5. `browser-use state` → Detailseite lesen:
   - "Volltext"-Block sichtbar?
   - "DOI"-Link sichtbar?
   - "Open Access"-Badge?
6. Wenn "Volltext"-Link → `browser-use click <idx>`
   Wenn DOI → `browser-use click <idx>` (verlinkt oft auf OA-Repo)
7. Auf PDF-Viewer-Seite: `browser-use download <pdf-link-idx> --to $OUTPUT_PATH`
8. Validation: PDF-Magic, Größe > 10 KB, Titel-Plausibilität (siehe
   quote-extractor-Pattern)

## Fallback

Kein Volltext gefunden → Output: `{"status": "metadata_only", "url": "<detailseite>"}`.
Master-Agent entscheidet, ob nächster Subagent (springer-book-fetcher)
versucht wird.

## Verbote

- Kein curl, kein wget, kein direkter HTTP-Aufruf
- Keine API-Endpoints raten
- Keine fingierten Treffer (wenn Suche leer ist, melden)
```

Analog für jeden anderen Site-Agent. Auth-Subagenten teilen sich
einen `auth-helper`-Subagent, der je nach Per-Uni-Profil den richtigen
Login-Flow ausführt (HAN, Shibboleth-WAYF, EZproxy).

### F16.2 — Master-Agent `book-fetcher`

```markdown
---
name: book-fetcher
model: sonnet
description: |
  Master-Orchestrator: bekommt ISBN/DOI/Titel und versucht, das Werk
  über die Site-Subagenten zu beschaffen. Entscheidet Fallback-Reihenfolge
  basierend auf Input-Typ und Per-Uni-Profil.
tools: [Read, Write, Agent(tib-fetcher, springer-book-fetcher, oapen-fetcher, doabooks-fetcher, degruyter-fetcher, nationallizenzen-fetcher, ebook-central-fetcher, kvk-fetcher, generic-fetcher, auth-helper)]
maxTurns: 8
---

# Auftrag

Beschaffe das Werk per browser-use-Subagenten.

## Strategie

1. Lies `~/.academic-research/library-profiles/active.yaml`.
2. Reihenfolge bestimmen:
   - **OA-Bücher**: oapen → doabooks → tib (OA-Filter) → kvk
   - **Verlags-Bücher mit Uni-Lizenz**: springer-book → degruyter →
     ebook-central → nationallizenzen
   - **Unbekannt**: kvk-fetcher (Meta-Suche) zuerst, dann passender
     Site-Subagent gemäß Treffer
3. Pro Subagent ein Versuch. Bei `metadata_only` → nächster Subagent.
   Bei `success` → Pfad in Vault aufnehmen, fertig.
4. Alle erschöpft → Pickup-Excel-Eintrag (für Fernleihe).

## Output

```json
{
  "status": "success" | "pickup_required" | "captcha" | "no_match",
  "pdf_path": "...",
  "source_subagent": "tib-fetcher",
  "tries": [
    {"subagent": "oapen-fetcher", "result": "metadata_only"},
    {"subagent": "tib-fetcher", "result": "success"}
  ]
}
```

## Verbote

- Kein eigener Browser-Aufruf — nur über Subagenten
- Kein Skipping der Per-Uni-Profil-Lese
```

### F16.3 — `/academic-research:fetch` Command

```yaml
---
description: Hol ein Buch oder Paper über die Site-Subagenten ins Repo
disable-model-invocation: false
allowed-tools: Read, Write, Agent(book-fetcher)
argument-hint: <isbn|doi|titel|url>
---
1. Parsen des Inputs (ISBN-Regex / DOI-Regex / URL / Freitext)
2. Spawn book-fetcher mit normalisiertem Input
3. Auf Ergebnis warten
4. Bei success: Eintrag in literature_state.md / Vault
5. Bei pickup_required: Eintrag in pickup-list.xlsx vorbereiten
6. Bei captcha: Screenshot anzeigen, User entscheidet manuell
```

### F16.4 — Discovery-Modus (`generic-fetcher`)

Wenn die ersten 8 Site-Subagenten alle fehlschlagen oder die URL keiner
bekannten Site entspricht:

```markdown
---
name: generic-fetcher
model: sonnet
description: |
  Fallback-Subagent. Bedient eine beliebige wissenschaftliche Site
  per browser-use, ohne vorgegebenen Site-Guide. Entscheidet anhand
  von DOM-Heuristiken (PDF-Button, Access-Banner, Login-Wall).
tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]
maxTurns: 20
---

# DOM-Heuristiken (Few-Shot-Lernen)

## "PDF-Button erkennen"
Look-fors in browser-use state:
- Text enthält: "Download PDF", "PDF herunterladen", "Get PDF",
  "Volltext (PDF)", "Full Text", "View PDF"
- Element-Typ: <a> oder <button>
- nicht: "Vorschau", "Preview", "Sample Chapter"

## "Paywall erkennen"
- Text enthält: "Get Access", "Purchase", "Buy", "Subscribe",
  "Sign in to view", "Anmelden für Volltext"
- Aktion: prüfe Per-Uni-Profil, ob Site-Lizenz vorhanden — wenn ja,
  triggere auth-helper. Wenn nein → metadata_only.

## "Captcha erkennen"
- Text "I'm not a robot", "Please verify", "reCAPTCHA"
- Aktion: screenshot, abbrechen mit status: captcha

## "Falscher Treffer erkennen"
- Treffer-Titel ≠ Input-Titel (>30 % Differenz, Levenshtein)
- Aktion: zurück zur Trefferliste, nächster Treffer
```

### F16.5 — Per-Uni-Profile (gleich wie F5)

`~/.academic-research/library-profiles/<uni>.yaml` (Beispiel Leibniz FH):

```yaml
uni: leibniz-fh
auth_type: HAN
auth_url: https://han.leibniz-fh.de
credentials_keys: [han_user, han_password]
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
proxy_pattern: "https://{site-with-dots-replaced-by-dashes}.han.leibniz-fh.de"
```

`auth-helper`-Subagent liest dieses Profil und entscheidet, ob er:
- HAN-Login fahren muss (Leibniz FH)
- Shibboleth-WAYF benutzt (TUM, RWTH)
- EZproxy-Proxy direkt (manche US-Unis)
- ohne Auth weiterläuft (OA-Site)

Setup fragt beim Erstaufruf nach Uni und Profil. Vorlagen für die
20 größten DACH-Hochschulen werden mit dem Plugin ausgeliefert.

### Trade-offs

- **Token-Kosten Subagenten:** 9 Site-Agenten = 9 System-Prompts.
  Mitigation: Master-Agent spawnt nur 1–2 pro Anfrage (Strategie-
  basiert), nicht alle parallel. Cache-Control auf System-Prompt
  jedes Site-Subagenten (1h-TTL) macht Folge-Calls auf dieselbe
  Site billig.
- **Modell-Wahl Sonnet überall:** Browser-Navigation reagiert auf
  unstrukturierten DOM-State, Fehlertoleranz braucht Sonnet-Niveau.
  Haiku scheiterte in Tests an Treffer-Auswahl und Paywall-Erkennung.
  Mehrkosten akzeptiert, weil pro Anfrage nur 1–2 Subagenten laufen.
- **browser-use Concurrency:** Heute single-Browser-Session. Parallele
  Subagenten würden sich Browser-Tab teilen. Mitigation: Master-Agent
  fährt strikt sequentiell.
- **Captcha:** browser-use kann nicht lösen. User-Hand-off bleibt.
- **Verlags-AGBs:** Throttle ≥ 5 s zwischen Downloads, kein Bulk-
  Crawling. Skills nutzen Standard-User-Agent (browser-use Default).
- **Auth-Drift:** Per-Uni-Profile veralten. Mitigation: jährlicher
  Profil-Review, User-Override über CLI.

### Konkrete Anker (Sprint v6.2 Diff)

```
agents/
  book-fetcher.md                 # NEU — Master
  tib-fetcher.md                  # NEU
  springer-book-fetcher.md        # NEU — ergänzt bestehenden springer-Guide
  oapen-fetcher.md                # NEU
  doabooks-fetcher.md             # NEU
  degruyter-fetcher.md            # NEU
  nationallizenzen-fetcher.md     # NEU
  ebook-central-fetcher.md        # NEU
  kvk-fetcher.md                  # NEU
  generic-fetcher.md              # NEU — Discovery-Modus
  auth-helper.md                  # NEU — geteilt

commands/
  fetch.md                        # NEU — /academic-research:fetch

config/browser_guides/
  tib.md                          # NEU
  oapen.md                        # NEU
  doabooks.md                     # NEU
  degruyter.md                    # NEU
  nationallizenzen.md             # NEU
  ebook_central.md                # NEU
  kvk.md                          # NEU
  springer.md                     # ÜBERARBEITET — Buch-Download-Block

scripts/bootstrap/
  library-profiles/
    leibniz-fh.yaml               # NEU
    tum.yaml                      # NEU
    rwth-aachen.yaml              # NEU
    fau-erlangen.yaml             # NEU
    template-shibboleth.yaml      # NEU
    template-han.yaml             # NEU
    template-ezproxy.yaml         # NEU
    template-oa-only.yaml         # NEU
```



### v6.0 — Foundation (Sprint 1, ~1 Woche)

- F1.1 Files-API für PDFs in `quote-extractor`
- F1.2 1h-TTL-Cache überall durchziehen
- F4 `/humanizer-de`-Integration in `chapter-writer` + neuer Slash-Command
- F12 `git init` Auto-Setup

### v6.1 — Bücher (Sprint 2, ~2 Wochen)

- F2.1 Skill `book-handler`
- F2.2 Kapitel-Schnitt + Seitenmapping + OCR-Detection
- F2.3 CSL `book` / `chapter`-Schema + DIN-1505-Variant
- F15 Eval-Coverage Bücher

### v6.2 — Beschaffung (Sprint 3, ~2 Wochen)

- F5 Pickup-Excel
- F6 8-Tier-Download
- F11 Cluster-Mermaid
- **F16 Universal Book Fetcher** (TIB + 5 weitere Module + `web-fetcher` + Per-Uni-Profile + `/academic-research:fetch`)

### v6.3 — Bridges (Sprint 4, ~1 Woche)

- F7 Zotero-Pull
- F8 Obsidian-Export
- F9 NotebookLM-Bundle (manuell)

### v6.4 — Methodik (Sprint 5, ~1 Woche)

- F3 Memory-Tool + Decision-Log
- F10 PRISMA-Flow
- F13 CSL-Import

### v6.5 — Polish

- F14 Reading-List-Import
- Doku, Migration-Guide, README-Update

---

## 17 · Risiken & Trade-offs

| Risiko | Mitigation |
|---|---|
| Files-API ist Beta — kann brechen | Feature-Flag in `~/.academic-research/config.yaml`, Fallback auf base64 |
| Memory-Tool nur in Managed-Agents oder mit eigenem Server | Pragmatisch: zunächst File-basiertes Memory in `projects/<slug>/memory/`, später Memory-Tool |
| OCR auf Lokal-Hardware lahm | Async-Hook, User entscheidet pro PDF |
| Zotero OAuth1-Schreib-Sync fehleranfällig | Erst Pull-only, Push erst wenn stabil |
| `humanizer-de` ist nicht im Plugin vendoriert | Doku: Setup prüft Skill-Existenz, sonst Hinweis |
| NotebookLM-CLI bricht ständig | als optional kennzeichnen, kein Hard-Dep |
| Pickup-Excel-Workflow je Hochschule anders | Per-Profil-Konfig: `~/.academic-research/library-profiles/<uni>.yaml` mit OPAC-URL, HAN-Endpoint, Fernleih-URL |
| 1M-Token-Modus = teuer | Default bleibt 200k, 1M nur bei expliziter `--book` Flag |

---

## 18 · Konkrete Anker-Diffs (Beispiele)

### 18.1 `agents/quote-extractor.md` — Cache + Files-API

```python
file_id = ensure_uploaded(pdf_path)  # cached in pdf_status.json

client.beta.messages.create(
    model="claude-sonnet-4-7",
    system=[{
        "type": "text",
        "text": AGENT_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }],
    documents=[{
        "type": "document",
        "source": {"type": "file", "file_id": file_id},
        "citations": {"enabled": True},
    }],
    extra_headers={"anthropic-beta": "files-api-2025-04-14"},
    messages=[{"role": "user",
        "content": f"Extrahiere {n} Zitate zu '{query}', je ≤ 25 Wörter."}],
)
```

### 18.2 Neuer `commands/humanize.md`

```yaml
---
description: Anti-KI-Audit-Pass für ein Kapitel via humanizer-de
disable-model-invocation: false
allowed-tools: Read, Write, Skill(humanizer-de)
argument-hint: <kapitel-pfad> [--mode normal|deep]
---
1. Lies die Datei.
2. Aktiviere den `humanizer-de`-Skill mit dem gewünschten Modus.
3. Schreibe Resultat als `<basename>.humanized.md`.
4. Erzeuge `<basename>.diff.md` (vor/nach pro Severity).
```

### 18.3 `commands/pickup.md` — Skeleton

```yaml
---
description: Erzeuge Bibliotheks-Pickup-Excel für nicht-OA-Quellen
disable-model-invocation: false
allowed-tools: Read, Write, Bash(~/.academic-research/venv/bin/python *), Skill(xlsx)
---
1. Lies `./literature_state.md`.
2. Filter `source != open_access` UND `pdf_status != downloaded`.
3. Resolve OPAC-Standorte über `scripts/library_pickup.py`.
4. Render via xlsx-Skill: 4 Sheets (vor Ort / Fernleihe / OA / Lizenz).
5. Speichere als `pickup-list.xlsx` im Projektordner.
```

---

## 19 · Erwartete Wirkung

| Metrik | v5.4.0 | v6.5 (Ziel) |
|---|---|---|
| Input-Tokens pro `/search` (50 Paper) | ~120k | ~50k (−58 %) |
| Input-Tokens pro Zitat-Extraktion (5 PDFs) | ~600k | ~150k (−75 %) |
| Buch-Support | nicht funktional | first-class |
| KI-Detektor-Auffälligkeit (eigene Bench) | mittel | niedrig |
| Sessions ohne Kontext-Verlust | < 30 % | > 95 % |
| Beschaffungs-Zeit pro nicht-OA-Quelle | 5–10 min manuell | < 30 s |
| Abdeckung systematische Reviews | nein | ja (PRISMA) |
| Externe Tool-Bridges | 1 (browser-use) | 4 (+Zotero, Obsidian, NotebookLM) |

---

## 20 · Quellen

- Anthropic Citations API — `docs.anthropic.com/en/docs/build-with-claude/citations`
- Anthropic Files API (Beta) — `docs.anthropic.com/en/docs/build-with-claude/files`
- Anthropic Prompt Caching (5min/1h TTL, März-2026-Default-Wechsel) — `docs.anthropic.com/en/docs/build-with-claude/prompt-caching`
- Anthropic PDF Support (32 MB, 100/600 Pages) — `platform.claude.com/docs/en/build-with-claude/pdf-support`
- Anthropic Message Batches (50 % Discount, 256 MB / 100k req) — `platform.claude.com/docs/en/build-with-claude/batch-processing`
- humanizer-de — `github.com/marmbiz/humanizer-de`
- Unpaywall API — `api.unpaywall.org/v2/<doi>?email=…`
- DNB SRU (ISBN/GND) — `services.dnb.de/sru/dnb`
- OpenLibrary API — `openlibrary.org/developers/api`
- DOAB REST — `directory.doabooks.org/rest/search`
- Zotero Web API v3 — `zotero.org/support/dev/web_api/v3/basics`
- Pyzotero — `github.com/urschrei/pyzotero`
- ZotLit / Obsidian-Zotero-Integration — `github.com/mgmeyers/obsidian-zotero-integration`
- NotebookLM unofficial Python — `github.com/teng-lin/notebooklm-py`
- Anystyle — `github.com/inukshuk/anystyle`
- CSL Repository — `github.com/citation-style-language/styles`
- PRISMA 2020 — `prisma-statement.org`
- Contextual Retrieval (Anthropic Cookbook) — `anthropic.com/news/contextual-retrieval`
- GBV SRU/CQL Schnittstellen — `gbv.github.io/cdvost2018`
