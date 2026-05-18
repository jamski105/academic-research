# v6.2 Wave 1 — Decomposition

**Stand:** 2026-05-13
**Wave:** 1 / 1 (alle 11 Tickets in einer Welle)
**Strategie:** Phasenweiser Spawn nach Dependency-Graph. Foundation-Chunks (A, B, F, J, K) starten parallel; Master & Command bauen sukzessive auf.

---

## Dependency-Graph

```
Wave 1 spawn (parallel):
  A (Browser-Guides)  ─┐
  B (Uni-Profile)     ─┤
  F (generic-fetcher) ─┤  ← startet ohne Wartezeit
  J (Tier-Pipeline)   ─┤
  K (Cluster-Mermaid) ─┘

Wave 2 (nach A bzw. B fertig):
  C (auth-helper)  ← B
  D (OA-Subs)      ← A
  E (Verlags-Subs) ← A, C
  
Wave 3:
  G (book-fetcher) ← D, E, F
  
Wave 4:
  H (/fetch cmd)   ← G
  
Wave 5:
  I (/pickup cmd)  ← H
```

L0 spawnt zunächst alle dep-freien Chunks parallel; nachfolgende Chunks werden auf `phase: pending` gesetzt und beim `merge-ready`-Signal des Vorgängers in `phase: spawned` überführt.

---

## Chunk A — Browser-Guides

**Ticket(s):** #87
**Branch:** `feat/v6.2-A-browser-guides`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-A`
**Spec:** `specs/v6.2/A.md`
**Depends on:** —

**File boundary (max 15):**
- `config/browser_guides/tib.md` (neu)
- `config/browser_guides/oapen.md` (neu)
- `config/browser_guides/doab.md` (neu)
- `config/browser_guides/degruyter.md` (neu)
- `config/browser_guides/nationallizenzen.md` (neu)
- `config/browser_guides/ebook-central.md` (neu)
- `config/browser_guides/kvk.md` (neu)
- `config/browser_guides/springer.md` (update — Buch-Download-Block ergänzen)
- `specs/v6.2/A.md`
- `specs/v6.2/A-plan.md`

**Geschätzte Größe:** 8 Markdown-Dateien × ~50 Zeilen = ~400 LoC

**L0-Notes für Spec-Phase:**
- **OQ26 entschieden:** Pfad ist `config/browser_guides/` (snake_case) — Convention existiert bereits seit v6.0
- Einheitliche Pflichtstruktur: Login-Flow · Discovery-Pfad · Volltext-Lokation · Pickup-Triggers · Bekannte Fallstricke
- `springer.md`-Update: bestehenden v6.0-Stand erhalten, Buch-Download-Block (`springer-book-fetcher`-kompatibel) ergänzen

---

## Chunk B — Per-Uni-Profile

**Ticket(s):** #86
**Branch:** `feat/v6.2-B-uni-profile`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-B`
**Spec:** `specs/v6.2/B.md`
**Depends on:** —

**File boundary (max 15):**
- `config/library-profiles/tum.yaml` (neu)
- `config/library-profiles/fu-berlin.yaml` (neu)
- `config/library-profiles/eth-zurich.yaml` (neu)
- `config/library-profiles/uni-wien.yaml` (neu)
- `config/library-profiles/uni-hamburg.yaml` (neu)
- `config/library-profiles/_schema.json` (JSON-Schema)
- `tests/test_library_profiles.py`
- `hooks/onboard-project-uni-prompt.sh` ODER `commands/onboard-uni.md` (Hook-Integration)
- `specs/v6.2/B.md`
- `specs/v6.2/B-plan.md`

**Geschätzte Größe:** ~9 Dateien, ~300 LoC

**L0-Notes:**
- **OQ23 entschieden:** Hochschulen = TU München, FU Berlin, ETH Zürich, Uni Wien, Uni Hamburg
- **OQ24 default:** `proxy_pattern` ist **optional** (nur HAN/EZproxy brauchen es; Shibboleth/oa-only nicht)
- **OQ25 default:** `active.yaml` wird via `onboard-project`-Hook (re-run-fähig) geschrieben

---

## Chunk C — auth-helper (security)

**Ticket(s):** #83
**Branch:** `feat/v6.2-C-auth-helper`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-C`
**Spec:** `specs/v6.2/C.md`
**Depends on:** B (Profil-Schema)

**File boundary (max 15):**
- `agents/auth-helper.md` (neu)
- `tests/test_auth_helper.py`
- `tests/fixtures/shibboleth_mock/` (Mock-HTML für Test)
- `specs/v6.2/C.md`
- `specs/v6.2/C-plan.md`

**Geschätzte Größe:** ~5 Dateien, ~350 LoC

**L0-Notes:**
- **Plan-Gate erzwingt (security):** Credential-Storage = Profil-Datei `0600` ODER OS-Keychain; **kein Logging von Credentials/Cookies**; **kein Vault-Persist von Sessions**; Allowlist-only Auth-Hosts via Per-Uni-Profil
- **OQ16 default:** Profil-Datei mit `0600`-Perms (erster Sprint); OS-Keychain-Optional für Sprint 2
- **OQ17 default:** Session-Timeout durch `browser-use`-Signale, kein fixer Timer
- **OQ18 default:** strukturierter Error-Output (`{status: auth_failed, reason}`) statt generischem Fehler

---

## Chunk D — OA-Site-Subagenten

**Ticket(s):** #81
**Branch:** `feat/v6.2-D-oa-subagents`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-D`
**Spec:** `specs/v6.2/D.md`
**Depends on:** A (Browser-Guides)

**File boundary (max 15):**
- `agents/tib-fetcher.md`
- `agents/oapen-fetcher.md`
- `agents/doabooks-fetcher.md`
- `agents/kvk-fetcher.md`
- `tests/test_oa_fetchers.py` (Schema + Mock-Discovery-Test pro Subagent)
- `evals/oa-fetchers/` (4 Eval-Cases, je 1 pro Subagent)
- `specs/v6.2/D.md`
- `specs/v6.2/D-plan.md`

**Geschätzte Größe:** ~9 Dateien, ~450 LoC

**L0-Notes:**
- Master-Output-Schema (s. Chunk G) = `{status: success|pickup_required|captcha|no_match, ...}`
- **OQ12 default:** Implementer wählt Eval-Bücher (z.B. Bibliothek-Klassiker mit garantierten OA-Treffern)
- **OQ13 default:** `kvk-fetcher` gibt Standort-Info im Output-JSON zurück (Master entscheidet, ob in pickup-list geschrieben wird) — Master ist Schicht-übergreifend

---

## Chunk E — Verlags-Site-Subagenten

**Ticket(s):** #82
**Branch:** `feat/v6.2-E-publisher-subagents`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-E`
**Spec:** `specs/v6.2/E.md`
**Depends on:** A (Browser-Guides), C (auth-helper)

**File boundary (max 15):**
- `agents/springer-book.md` (neu — kein bestehendes File, Audit-Diff war ungenau)
- `agents/degruyter.md`
- `agents/nationallizenzen.md`
- `agents/ebook-central.md`
- `tests/test_publisher_fetchers.py`
- `evals/publisher-fetchers/`
- `specs/v6.2/E.md`
- `specs/v6.2/E-plan.md`

**Geschätzte Größe:** ~9 Dateien, ~450 LoC

**L0-Notes:**
- **OQ15 entschieden:** Es existiert KEIN `agents/springer-*.md` aktuell (nur `config/browser_guides/springer.md`); `agents/springer-book.md` ist also **neu**
- **OQ14 default:** Bei fehlender Lizenz → `status: metadata_only` (analog tib-fetcher), Master entscheidet ob Eskalation oder Fallback

---

## Chunk F — generic-fetcher

**Ticket(s):** #84
**Branch:** `feat/v6.2-F-generic-fetcher`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-F`
**Spec:** `specs/v6.2/F.md`
**Depends on:** — (parallel zu A/B/J/K)

**File boundary (max 15):**
- `agents/generic-fetcher.md`
- `tests/test_generic_fetcher.py`
- `tests/fixtures/dom_heuristics/` (HTML-Fixtures mit Paywall/PDF-Button-Pattern)
- `specs/v6.2/F.md`
- `specs/v6.2/F-plan.md`

**Geschätzte Größe:** ~5 Dateien, ~250 LoC

**L0-Notes:**
- **OQ19 default:** Levenshtein-Schwelle = **30 %** als Default im System-Prompt, konfigurierbar via Frontmatter
- **OQ20 default:** Auth-Dispatch ist **Master-Aufgabe** (#80) — `generic-fetcher` meldet nur `metadata_only` bzw. `pickup_required` bei Paywall, Master entscheidet über `auth-helper`-Aufruf

---

## Chunk G — Master book-fetcher

**Ticket(s):** #80
**Branch:** `feat/v6.2-G-book-fetcher`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-G`
**Spec:** `specs/v6.2/G.md`
**Depends on:** D, E, F (Subagenten existieren), B (Profil-Schema)

**File boundary (max 15):**
- `agents/book-fetcher.md`
- `tests/test_book_fetcher.py` (Routing-Logik-Tests via Mock-Subagents)
- `tests/fixtures/book_fetcher_mocks/`
- `specs/v6.2/G.md`
- `specs/v6.2/G-plan.md`

**Geschätzte Größe:** ~5 Dateien, ~350 LoC

**L0-Notes:**
- **OQ9 entschieden:** Output-Schema = `{status: success | pickup_required | captcha | no_match, source, file_path?, reason?, tries[]}`
- **OQ10 default:** Captcha-Screenshot wird vom **Site-Subagenten** aufgezeichnet; Master leitet Pfad an aufrufenden Command (#85) weiter
- **OQ11 default:** `maxTurns: 8` als Default-Vorgabe, im Frontmatter konfigurierbar

---

## Chunk H — `/academic-research:fetch` Slash-Command

**Ticket(s):** #85
**Branch:** `feat/v6.2-H-fetch-cmd`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-H`
**Spec:** `specs/v6.2/H.md`
**Depends on:** G (book-fetcher existiert)

**File boundary (max 15):**
- `commands/fetch.md`
- `tests/test_fetch_command.py` (Input-Parser-Tests: ISBN/DOI/URL/Titel)
- `evals/fetch/` (3 Eval-Cases: ISBN, DOI, URL)
- `specs/v6.2/H.md`
- `specs/v6.2/H-plan.md`

**Geschätzte Größe:** ~7 Dateien, ~200 LoC

**L0-Notes:**
- **OQ21 default:** Bei `no_match` → ja, `pickup_required`-Eintrag anlegen (User bekommt klaren Folge-Pfad)
- **OQ22 default:** Eval-Struktur = `evals/fetch/` (analog zu bestehenden Eval-Verzeichnissen wie `evals/book-handler/`)

---

## Chunk I — `/academic-research:pickup` + Excel-Generation

**Ticket(s):** #77
**Branch:** `feat/v6.2-I-pickup-cmd`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-I`
**Spec:** `specs/v6.2/I.md`
**Depends on:** H (pickup_required-Integration mit `/fetch`)

**File boundary (max 15):**
- `commands/pickup.md`
- `scripts/barcode.py` (Code128-Generierung, z.B. via `python-barcode`-Lib)
- `tests/test_pickup_excel.py`
- `tests/fixtures/pickup/` (5 Test-Quellen)
- `specs/v6.2/I.md`
- `specs/v6.2/I-plan.md`

**Geschätzte Größe:** ~7 Dateien, ~300 LoC

**L0-Notes:**
- **OQ1 entschieden:** 4 Sheets nach **Verfügbarkeitsstatus**: `Vor Ort verfügbar`, `Fernleihe`, `Online OA`, `Lizenz nötig` (NICHT Quellentyp)
- **Excel-Generation:** ausschließlich via `document-skills:xlsx`-Skill (kein openpyxl/pandas, User-Memory)
- **OQ2 default:** Code128-Barcodes als **Zellbild** (Image-Embed) im Books-Sheet (`document-skills:xlsx` unterstützt embedded images via `insert_image`-API); reines Schriftart-Encoding ist Fallback
- **OQ3 default:** Alle Vault-Einträge der Auswahl in Pickup-Liste aufnehmen, Sheet-Zuordnung nach `availability_status` aus Vault-Metadaten (kein hartcodiertes OA-Filter)

---

## Chunk J — Auto-Download Tier-Pipeline-Erweiterung

**Ticket(s):** #78
**Branch:** `feat/v6.2-J-tier-pipeline`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-J`
**Spec:** `specs/v6.2/J.md`
**Depends on:** — (orthogonal zu F16-Kette)

**File boundary (max 15):**
- `scripts/pdf.py` (3 neue Funktionen: `tier_openaccessbutton`, `tier_doab`, `tier_europepmc` + erweiterte `resolve_pdf_url()`-Reihenfolge)
- `tests/test_pdf_tiers.py` (Mock-HTTP-Tests pro Tier: Erfolgs- + Leerfall)
- `evals/auto-download/v6.2-tier-eval.md` (20 Test-Quellen, Hit-Rate-Messung)
- `evals/auto-download/sources.yaml` (kuratierte Liste)
- `specs/v6.2/J.md`
- `specs/v6.2/J-plan.md`

**Geschätzte Größe:** ~6 Dateien, ~400 LoC

**L0-Notes:**
- **OQ4 default:** Biomedizin-DOI = DOI-Präfix-Allowlist (z.B. `10.1016/j.`-Elsevier-Biomed, `10.1186/`-BMC, `10.1371/`-PLOS, `10.3390/`-MDPI-Biology); konfigurierbar via `scripts/pdf.py:BIOMED_DOI_PREFIXES`
- **OQ5 default:** Implementer kuratiert die 20 Test-Quellen, kann v6.1-Eval-Material (5 Bücher) wiederverwenden + 15 Paper-Quellen aus bestehenden Test-Suites

---

## Chunk K — Cluster-Mermaid-Visualizer

**Ticket(s):** #79
**Branch:** `feat/v6.2-K-cluster-mermaid`
**Worktree:** `/Users/j65674/Repos/academic-research-v6.2-K`
**Spec:** `specs/v6.2/K.md`
**Depends on:** — (orthogonal)

**File boundary (max 15):**
- `skills/cluster-visualizer/SKILL.md`
- `skills/cluster-visualizer/scripts/render_mermaid.py`
- `tests/test_cluster_visualizer.py`
- `tests/fixtures/cluster_json/` (Test-Cluster mit 8 Papern)
- `specs/v6.2/K.md`
- `specs/v6.2/K-plan.md`

**Geschätzte Größe:** ~6 Dateien, ~300 LoC

**L0-Notes:**
- **OQ6 default:** Implementer liest existierendes Cluster-JSON-Schema (falls vorhanden; sonst neu definieren — derzeit keine `*cluster*`-Pfade in `skills/`/`commands/`/`scripts/`)
- **OQ7 default:** `mmdc` (Mermaid-CLI) **graceful degradieren**: bei fehlender Installation Mermaid-Quelltext zurückgeben mit Hinweis „PNG nicht erzeugt (`mmdc` nicht installiert)"
- **OQ8 default:** Mermaid-Output als **separate Datei** + Pfad-Return (User entscheidet beim Einsatz, ob in `kapitel/literatur.md` einbetten)

---

## Cap-Budget

- **Chunks gesamt:** 11
- **Worktrees parallel:** bis zu 5 (Wave 1: A, B, F, J, K)
- **Spec-Revisions cap:** 2 pro Chunk (max 22 Spec-Reviewer-Runs)
- **Plan-Revisions cap:** 2 pro Chunk (max 22 Plan-Reviewer-Runs)
- **CI-Fix-Iterations cap:** 3 pro Chunk

---

## Approval

**HARD GATE:** Phase 2 (L1-Spawn) startet erst nach explizitem User-Approve dieser `chunks.md`.
