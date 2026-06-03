# Changelog

Alle bemerkenswerten Änderungen an diesem Plugin werden hier dokumentiert.

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

---

## [6.5.1] — 2026-06-03

### Fixed

- **Vault-MCP-Server startet wieder (#217):** Drei sich gegenseitig blockierende Start-Ursachen behoben: (1) `.mcp.json` startet den Server jetzt mit der Projekt-venv (`${HOME}/.academic-research/venv/bin/python`) und setzt `PYTHONPATH=${CLAUDE_PLUGIN_ROOT}`; (2) `mcp>=1.0` + `sqlite-vec>=0.1.0` werden über `scripts/requirements.txt` ins venv installiert; (3) Namespace-Kollision mit dem `mcp`-SDK aufgelöst — lokales Paket `mcp/academic_vault/` → `academic_vault/` (Top-Level) verschoben, alle Referenzen (`.mcp.json`, Hooks, Skills, Tests) angepasst.
- **`/history --restore` repariert (#219):** Literal-Platzhalter `<PLUGIN_ROOT>` in `commands/history.md` durch `${CLAUDE_PLUGIN_ROOT}` ersetzt — der Pfad wird nun zur Laufzeit expandiert, `import academic_vault.server` schlägt nicht mehr fehl.

## [6.5.0] — 2026-05-18

### Added

- **Contextual Retrieval (#109):** Hybrid BM25 + vec0 mit Reciprocal-Rank-Fusion (RRF). 1-Satz-Kontext-Embedding vor jedem Chunk via Anthropic Prompt-Caching (1h-TTL). `vault.search(query, rerank=true)` für optionales Reranking.
- **Reading-List-Import (#95):** Neuer Skill `reading-list-import`. Input: PDF, Markdown oder Plaintext mit Quellenliste. LLM-Parser (Sonnet) → DOI/ISBN-Resolution → Vault. AskUserQuestion bei Mehrdeutigkeit. Anystyle (Ruby) als optionales Backend.
- **LaTeX-Export (#96):** Neuer Skill `latex-export`. Markdown-Kapitel → `.tex` (Pandoc optional, fallback custom Renderer). Bibliographie → `.bib` (biblatex, DIN-1505). Per-Uni-Template-Slot: `~/.academic-research/library-profiles/<uni>.tex.template`. Neuer Command `/academic-research:latex --kapitel <n>|all --output thesis.tex`. Verbatim-Validation auch auf `*.tex`-Outputs.
- **Topic-Brainstorm (#107):** Neuer Skill `topic-brainstorm`. Trigger: *„welches Thema?"*, *„Themenfindung"*. 3–5 Kandidaten mit Feasibility/Novelty/Career-Fit-Scores, je 2–3 Forschungsfragen + 1 Pilot-Paper-Set. Übergang zu `research-question-refiner`.
- **Grant / Poster / Response (#108):** Drei neue Output-Skills (Default-Off, Opt-in via `output_targets` in `academic_context.md`):
  - `grant-proposal`: DFG/BMBF/EU-Antragsstruktur mit Vault-Quellen
  - `conference-poster`: A0-Poster (LaTeX tikzposter / PowerPoint)
  - `reviewer-response`: Point-by-point Response-Letter
- **SciHub-Tier Opt-in (#97):** Optionaler Last-Resort-Fetcher. Default DEAKTIVIERT. Aktivierung via `/academic-research:setup` → explizite Opt-in-Frage. Provenance-Tag `provenance:scihub` im Vault. Output-Hinweis *„Quelle via SciHub bezogen — bitte zusätzlich legalen Zugriff klären."*
- **README + Docs Rewrite (#98):** Kompletter README-Rewrite für v6.x (Vault, Universal Book Fetcher, humanizer-de, Per-Uni-Profile, alle v6.x-Features). Neues `CHANGELOG.md` (alle v6.x-Releases). Neues `docs/MIGRATION-v5-to-v6.md`. Glossar-Erweiterung (Vault, Subagent, Site-Profile, Material-Passport, Contextual Retrieval, RRF, CSL, humanizer-de).

### Changed

- `vault.search()` unterstützt jetzt `rerank=true` für Cohere/Voyage-Reranking.
- `skills/style-evaluator/SKILL.md`: triggert `humanizer-de` als Subagent bei `output_target ∈ {Bachelor, Master, Diplom, Dissertation}`.

---

## [6.4.0] — 2026-05-18

### Added

- **Vault-Foundation (#148):** `vault.add_decision` / `vault.list_decisions`, `vault.add_score_snapshot` / `vault.get_score_history`, `vault.add_risk_of_bias` / `vault.list_risk_of_bias`, `vault.export_snapshot` / `vault.restore_snapshot`.
- **Material-Passport (#104):** `vault.export_material_passport` / `vault.lock_passport` / `vault.is_locked`. Neuer Skill `material-passport`. Repro-Lock verhindert nachträgliche Änderungen an gesperrten Artefakten.
- **PRISMA-Flow (#92):** Neuer Skill `prisma-flow`. Mermaid-Diagramm + 27-Punkte-PRISMA-2020-Checkliste. Integration in `/search` (schreibt `n_identified`, `n_after_dedup`) und `relevance-scorer` (`excluded_screening`).
- **Meta-Analysis (#150):** Neuer Agent `meta-analysis`. DerSimonian-Laird Random-Effects-Modell. Mermaid-Forest-Plot. Output via `scripts/meta_analysis.py`.
- **Risk-of-Bias (#100):** Neuer Agent `risk-of-bias`. Cochrane RoB 2, ROBINS-I, CASP Assessment. Ergebnisse in `vault.add_risk_of_bias()`.
- **Hooks-Stack (#91, #103):** Vier Hooks:
  - `pre-compact.mjs`: Snapshot-Backup vor Claude-Compaction nach `~/.academic-research/snapshots/`.
  - `post-tool-use-decisions.mjs`: Decision-Log für alle `*.md`-Schreiboperationen.
  - `mid-session-reinforcement.mjs`: Anti-Fabrikations-Erinnerung.
  - `verbatim-guard.mjs`: Blockt Kapitel-Writes mit nicht-verifizierten Zitaten.
  - `/academic-research:history --restore <ts>`: Snapshot-Restore.
- **Citation-Styles MLA/Vancouver/Springer-AD (#106):** Drei neue Varianten in `citation-extraction/references/`.
- **CSL-JSON Import (#93):** Neuer Skill `citation-style-import`. Lädt beliebige `.csl`-Datei aus CSL-Repository, parst zu promptfähigen Regeln, speichert als `references/custom-<style>.md`.
- **Batch-API für Bulk-Scoring (#94):** `--batch`-Flag für `/search` und `/score`. Job-ID in `$SESSION_DIR/batch.json`. 50 % Kostenreduktion bei > 50 Papers. Pickup via `/academic-research:history --batch <id>`.
- **Interactive Search Mode (#105):** Interaktiver Modus bei `/search --interactive`: schrittweise Filter, Query-Verfeinerung, Cluster-Vorschau.
- **Cluster-Visualisierung (#132):** Mermaid-Diagramm aus 5D-Scoring-Output. Einbettbar in `kapitel/literatur.md`.

### Changed

- `tests/baselines/skill_sizes.json`: aktualisiert für neue Skills.
- `scripts/requirements.txt`: `meta_analysis`-Dependencies ergänzt (scipy, numpy).

---

## [6.3.0] — 2026-05-16

### Added

- **Zotero-Import (#143):** Neuer Skill `zotero-import`. pyzotero-Pull-only (kein Push). DOI/ISBN-basierte Dedup gegen Vault. Konfiguration via `~/.academic-research/config.yaml` (Zotero API-Key, Library-ID).
- **NotebookLM-Bundle (#144):** Neuer Skill `notebook-bundle`. Packt PDF-Bundle aus Top-N-Papers + Bibliographie als ein PDF. Unterstützt Split-Modus für einzelne Dokumente. Für Bücher > 600 Seiten als Triage-Tool. Output-Pfad-Fix: Split-Modus respektiert `output_path`-Verzeichnis.

### Notes

- NotebookLM-Bundle ist kein Zitationsweg — kein Verbatim-Garantiepfad. Nur als Exploration-Tool gedacht.

---

## [6.2.0] — 2026-05-14

Wave 1: Universal Book Fetcher — 11 PRs (Tickets #131–#141).

### Added

- **Universal Book Fetcher — Site-Subagenten (#138):** 9 Browser-Subagenten für Buch-Download:
  - `tib-fetcher`, `springer-book`, `oapen-fetcher`, `doabooks-fetcher`, `degruyter`, `nationallizenzen`, `ebook-central`, `kvk-fetcher`, `generic-fetcher`
  - Jeder Subagent kennt nur seine Site. Nur `browser-use` CLI — kein curl/wget/direktes HTTP.
- **book-fetcher Master-Agent (#137):** Orchestriert Site-Subagenten. Strategie basiert auf Input-Typ (OA, Verlags, unbekannt) und Per-Uni-Profil. Strikt sequentiell (single Browser-Session).
- **auth-helper Subagent (#136):** Gemeinsamer Auth-Agent für alle Site-Subagenten. Unterstützt HAN, Shibboleth-WAYF, EZproxy, DFN-AAI.
- **Per-Uni-Profile (#133):** `library-profiles/<uni>.yaml`. Mitgelieferte Profile: Leibniz FH, TU München, RWTH Aachen, FAU Erlangen-Nürnberg. Templates: HAN, Shibboleth, EZproxy, OA-only. Setup fragt beim Erstaufruf nach Uni.
- **`/academic-research:fetch` Command (#140):** Parst ISBN/DOI/URL/Freitext, startet `book-fetcher`, schreibt Ergebnis in Vault. Bei `captcha`: Screenshot + User-Handoff. Bei `pickup_required`: Eintrag in Pickup-Liste.
- **`/academic-research:pickup` Command (#141):** Erzeugt Bibliotheks-Pickup-Excel aus nicht-OA-Quellen. 4 Sheets: Vor-Ort / Fernleihe / OA / Lizenz. OPAC-Standort + Code128-Barcode.
- **OA-Site-Subagenten (#134):** TIB, OAPEN, DOAB, KVK mit Tests und Evals.
- **Auto-Download-Pipeline 8-Tier (#135):** OpenAccessButton, DOAB, EuropePMC als Tiers 6–8. Ergänzt bestehende 5-Tier-Pipeline.
- **Browser-Guides (#131):** Neue Guides für TIB, OAPEN, DOAB, De Gruyter, Nationallizenzen, Ebook Central, KVK. Springer-Guide überarbeitet (Buch-Download-Block).
- **Cluster-Mermaid (#132):** Cluster-Visualisierung als Mermaid-Diagramm.

### Changed

- `config/browser_guides/springer.md`: Buch-Download-Flow ergänzt.

---

## [6.1.0] — 2026-05-13

Wave 1: Bücher, OCR, Seitenmapping, VLM, Evals — viele Features.

### Added

- **Eval-Coverage Bücher (#130):** 5 Test-Cases (1 OA, 2 ISBN-only, 1 Scan-PDF, 1 Sammelband). Token-Regression-Baseline unter `tests/evals/book-handler/`.
- **VLM Figure/Table Verification (#129):** Neuer Agent `figure-verifier`. Vault-Tools: `add_figure`, `get_figure`, `list_figures`. Verbatim-Guard prüft Abbildungsreferenzen. Eval-Skeleton mit 5 Cases.
- **Page-Mapping pdf_page → printed_page (#128):** `page_offset` in Vault. Sanity-Check über 2 Stichproben-Seiten. Unterstützung für Bücher mit Doppelpaginierung / römischen Vorseiten.
- **OCR-Detection + Trigger-Workflow (#127):** Detektion bei < 100 extrahierbaren Zeichen. `ocrmypdf`-Integration (optional). AskUserQuestion vor OCR-Start.

### Changed

- Vault: `set_ocr_done`, `update_pdf_path`, `set_page_offset`, `get_printed_page`, `add_figure`, `get_figure`, `list_figures` ergänzt.
- `skills/book-handler/SKILL.md`: Kapitel-Schnitt + Seitenmapping + OCR-Pfad integriert.

---

## [6.0.0] — 2026-05-09

Foundation-Release: Vault, Buch-Pfad, humanizer-de, Files-API.

### Added

- **Vault-MCP-Server (initial):** `mcp/academic_vault/` — SQLite mit FTS5 + sqlite-vec. Tools: `vault.search`, `vault.get_paper`, `vault.add_paper`, `vault.add_chapter`, `vault.add_quote`, `vault.find_quotes`, `vault.search_quote_text`, `vault.ensure_file`, `vault.stats`. Datenbank unter `~/.academic-research/projects/<slug>/vault.db`.
- **`book-handler` Skill:** ISBN/Titel → DNB SRU + OpenLibrary + GoogleBooks → Metadaten → OPAC-Suche → DOAB/OAPEN → Kapitel-Schnitt + OCR-Check. CSL-Felder `type: book | chapter`, `container-title`, `editor[]`, `chapter`, `page-first`, `page-last`.
- **`/academic-research:humanize` Command:** Anti-KI-Audit-Pass für Kapitel. Aktiviert `humanizer-de`-Skill im gewünschten Modus. Output: `<basename>.humanized.md` + `<basename>.diff.md`.
- **`humanizer-de`-Integration in `chapter-writer`:** Draft → `humanizer-de(audit)` → `quality-reviewer` → final.
- **`style-evaluator`-Integration:** Triggert `humanizer-de` als Subagent bei Bachelor/Master/Diplom/Dissertation.
- **Files-API für PDFs:** `vault.ensure_file()` lädt PDF zu Anthropic Files-API hoch, cached `file_id` mit TTL. `quote-extractor` nutzt `file_id` statt base64. Feature-Flag in `~/.academic-research/config.yaml`.
- **1h-TTL-Prompt-Caching:** `relevance-scorer`, `quote-extractor`, `chapter-writer`, `quality-reviewer`: `cache_control: {type: "ephemeral", ttl: "1h"}` auf System-Prompt (nach Anthropic-Default-Änderung März 2026).
- **`git init` Auto-Setup:** `/academic-research:setup` bietet optionalen `git init` + Initial-Commit der Bootstrap-Files.

### Changed

- `quote-extractor`: schreibt via `vault.add_quote()` statt JSON-Datei.
- `chapter-writer`: liest via `vault.find_quotes()` + `vault.search()`.
- `literature_state.md`: read-only Snapshot-Export aus Vault (nicht mehr Primary Source).

### Migration

- Bestehende `literature_state.md` kann via `/academic-research:setup --migrate-v5` in den Vault migriert werden.
- Vollständiger Guide: `docs/MIGRATION-v5-to-v6.md`.

---

## [5.4.0] — 2026-04-24

Finale Review-Runde gegen anthropics/skills Cookbook (Commit `5128e186`).

### Changed

- Skill-Namen auf kebab-case (alle 13 Skills): `Abstract Generator` → `abstract-generator` usw.
- `./`-Prefix für Kontext-Datei-Referenzen durchgängig.
- `## Übersicht` als erste H2 in allen 13 Skills (Cookbook-Pattern).
- Few-Shot-Beispiele (Schlecht/Gut mit Grund-Annotation) in 10 bisher few-shot-losen Skills.
- Skill-Cross-Referenzen in Prosa: Title Case → `` `kebab-case` ``.
- `chapter-writer`, `citation-extraction` Trigger erweitert.

### Fixed

- `submission-checker`: Legacy-Datei entfernt, Variant-Selector aktiviert.
- `methodology-advisor`: fehlender `## Abgrenzung`-Block ergänzt.
- `agents/query-generator.md`, `agents/relevance-scorer.md`: `tools: []` Allowlist ergänzt.
- `commands/history.md`: `disable-model-invocation: true` ergänzt.
- `agents/quality-reviewer.md`: ASCII-Umlaute → echte Umlaute.

### Removed

- `settings.json` (Root), `.mcp.json` (Root), `templates/` (Root), `config/scoring.yaml` (obsolet).

### Internal

- 2 neue Regression-Guards: `tests/test_skill_naming.py`, `tests/test_cross_references.py`.

---

## [5.3.0] — 2026-04-24

### ⚠️ BREAKING — Kontext-Ablage geändert

Der akademische Kontext wandert von Claude-Memory (`~/.claude/projects/<hash>/memory/`) in projekt-lokale Dateien (`./academic_context.md`).

### Added

- `/academic-research:setup` erweitert um Projekt-Bootstrap: leere Ordner → Facharbeit-Init; existierende Ordner → idempotent nachrüsten; Code-Repos → nur Environment-Setup.
- Generierte `CLAUDE.md` mit Skill-Delegations-Tabelle und Anti-Fabrikations-Regel.
- Migrations-Helper: `/setup` erkennt Memory-basierten Kontext, bietet Copy an.
- `scripts/project_bootstrap.py` (12 Tests in `tests/test_project_bootstrap.py`).

### Changed

- Alle 13 Skills + `query-generator`: lesen `./academic_context.md` statt Memory.

---

## [5.2.0] — 2026-04-23

### Added

- Native Citations-API in `quote-extractor`, `citation-extraction`, `chapter-writer`.
- Evals-Suite (`tests/evals/`) mit Quality-Evals und Trigger-Evals.
- `quality-reviewer`-Agent (Evaluator-Optimizer-Pattern).
- Domain-organized References in 3 Skills.
- Prompt-Caching in `relevance-scorer` + `quote-extractor`.

---

## [5.1.1] — 2026-04-23

### Fixed

- Abgrenzungs-Klauseln in 8 weiteren Skills.
- Duplikat-Precondition in `literature-gap-analysis` entfernt.
- Trigger-Überschneidung `"Forschungsfrage"` aufgelöst.

---

## [5.1.0] — 2026-04-23

### Added

- Anti-Fabrikations-Klauseln in allen 13 Skills.
- Memory-Precondition-Checks in 12 Skills.
- Few-Shot-Paare in 4 Skills.
- Skill-Abgrenzung zwischen `literature-gap-analysis` und `source-quality-audit`.
- Smoke-Test `tests/test_skills_manifest.py` (51 parametrisierte Tests).

### Changed

- Numerische Schwellen in 5 Skills (advisor, methodology-advisor, submission-checker, style-evaluator, literature-gap-analysis).
- Sprache einheitlich Deutsch in allen Skills/Commands/Agents.
- Umlaut-Varianten in allen 13 Skill-Trigger-Descriptions.

---

## [5.0.1] — 2026-04-23

### Changed

- `scripts/setup.sh` zu vollständigem One-Click-Installer ausgebaut. `browser-use` CLI Auto-Install via `uv`/`pipx`.

---

## [5.0.0] — 2026-04-23

> **⚠️ BREAKING:** Playwright → `browser-use`, Excel → `document-skills:xlsx`.

### Changed

- Browser-Automation von Playwright-MCP auf `browser-use`-CLI umgestellt.
- Excel-Generierung an externes `document-skills:xlsx`-Plugin delegiert (ab v5.5 plugin-intern vendoriert).

### Removed

- `scripts/citations.py`, `scripts/style_analysis.py`, `scripts/ranking.py`, `scripts/excel.py` gelöscht.
- Playwright-Konfiguration entfernt.

---

## [4.0.0] — vor 2026-04-23

Erstes getracktes Release. Monolithische 7-Phasen-Pipeline → 13 modulare Skills. Siehe Git-Historie für frühere Änderungen.

[6.5.0]: https://github.com/jamski105/academic-research/compare/v6.4.0...v6.5.0
[6.4.0]: https://github.com/jamski105/academic-research/compare/v6.3.0...v6.4.0
[6.3.0]: https://github.com/jamski105/academic-research/compare/v6.2.0...v6.3.0
[6.2.0]: https://github.com/jamski105/academic-research/compare/v6.1.0...v6.2.0
[6.1.0]: https://github.com/jamski105/academic-research/compare/v6.0.0...v6.1.0
[6.0.0]: https://github.com/jamski105/academic-research/compare/v5.4.0...v6.0.0
[5.4.0]: https://github.com/jamski105/academic-research/compare/v5.3.0...v5.4.0
[5.3.0]: https://github.com/jamski105/academic-research/compare/v5.2.0...v5.3.0
[5.2.0]: https://github.com/jamski105/academic-research/compare/v5.1.1...v5.2.0
[5.1.1]: https://github.com/jamski105/academic-research/compare/v5.1.0...v5.1.1
[5.1.0]: https://github.com/jamski105/academic-research/compare/v5.0.1...v5.1.0
[5.0.1]: https://github.com/jamski105/academic-research/compare/v5.0.0...v5.0.1
[5.0.0]: https://github.com/jamski105/academic-research/compare/v4.0.0...v5.0.0
