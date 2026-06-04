# Issue-Board-Audit — academic-research (Stand 2026-06-03)

Erzeugt aus dem orchestrierten Audit-Workflow (`wf_790b500e-3c9`): 74 Agenten,
9 Issue-Audit-Gruppen + 8 Subsystem-Scans + adversarische Gegenprüfung jedes
Findings + Vollständigkeits-Zweitdurchlauf. Jede Behauptung ist gegen den
aktuellen Code (Branch `main`) verifiziert.

> **Status dieses Files:** untracked Arbeitsdokument. Quelle der Wahrheit für die
> anschließende Board-Erstellung. Kann nach Umsetzung gelöscht oder committet werden.

---

## 1. Audit der 51 offenen Issues — Notwendigkeit

| Urteil | Anzahl | Issues |
|---|---|---|
| **STILL_VALID → KEEP** | 47 | 55, 166–169, 171–209 (außer 170), 212, 213, 215 |
| **PARTIAL → EDIT_SCOPE** | 4 | 170, 210, 211, 214 |
| **ALREADY_FIXED → CLOSE** | 0 | — |
| **INVALID/STALE** | 0 | — |

**Kernaussage: Kein einziges offenes Issue ist obsolet.** 47 bestehen unverändert,
4 sind teil-gefixt und sollten im Scope reduziert werden:

- **#170** (latex-export NEEDS-FIX): Description-Vagueness + Verbatim-Guard-`*.tex`
  sind **behoben**. Offen bleiben: Skript-Pfade ohne `${CLAUDE_PLUGIN_ROOT}`,
  citation-extraction-Abgrenzung, explizite Fehlerpfade. → Scope auf diese 3 Punkte.
- **#210** (CHANGELOG): Hook-Stack ist inzwischen vollständig gelistet → Hauptklage
  hinfällig. **Real bleibt:** v6.5.0 und v6.4.0 tragen beide `2026-05-18`. → Scope auf
  Datum-Korrektur.
- **#211** (README-Glossar): `Contextual Retrieval` + `RRF` sind ergänzt. → Scope auf
  die 6 fehlenden Begriffe (Decision-Log, Vault-Lock, OCR-Detection, Repro-Lock,
  output_targets, …).
- **#214** (Code-Hygiene-Bündel): L1 (hook string-concat) + L2 (tar-Portabilität)
  **behoben**. → Scope auf L3 (LIKE-ESCAPE) + README-Pfad-Klarheit.

---

## 2. Wurzel von „Plugin funktioniert nicht": Vault-MCP-Server startet auf KEINEM Pfad

Drei eigenständige, je belegte Critical-Bugs blockieren zusammen jeden Startweg:

1. **`.mcp.json:4` startet mit blankem `python`** — auflösbar auf irgendein
   `python` im PATH (hier `~/.browser-use-env/bin/python`), nicht die Projekt-venv.
   → `ModuleNotFoundError: No module named 'mcp.academic_vault'`.
2. **`mcp>=1.0` (FastMCP) fehlt in `scripts/requirements.txt`** — nur diese Datei
   installiert `setup.sh` ins venv. Das SDK steht ausschließlich in
   `mcp/academic_vault/requirements.txt`, die nie referenziert wird.
   → `RuntimeError: mcp SDK nicht installiert`.
3. **`mcp/`-Verzeichnis kollidiert mit dem installierten `mcp`-SDK-Paket** — sobald
   das SDK da ist, löst `python -m mcp.academic_vault.server` auf das SDK-Paket auf
   statt aufs lokale `mcp/`. → erneut `ModuleNotFoundError`. **Dilemma:** ohne SDK →
   RuntimeError, mit SDK → ModuleNotFoundError. Erfordert Umbenennung des lokalen
   `mcp/`-Pakets (z. B. `vault/` oder `src/academic_vault/`) oder `pip install -e .`.

Direkt-Test der Agenten: `~/.academic-research/venv/bin/python -m mcp.academic_vault.server`
→ `RuntimeError: mcp SDK nicht installiert`; nach `pip install mcp` → `ModuleNotFoundError`.

→ **Empfehlung: ein Umbrella-Release-Blocker (v6.5.1) mit 3 Checkpunkten**, da alle drei
für ein funktionierendes „Server startet" gemeinsam gefixt werden müssen.

---

## 3. Neue, verifizierte Probleme (Pass 1: 27 real & neu von 56 Funden; 25 überlappend, 4 widerlegt)

### CRITICAL
| # | Subsystem | Datei | Problem |
|---|---|---|---|
| N1 | hooks/config | `.mcp.json:4` | siehe §2.1 — bare `python` |
| N2 | scripts | `scripts/export-literature-state.mjs:37-65` | **Shell-Injection** via `VAULT_DB_PATH`: Backtick/`$()` werden nicht escaped (nur `\ " \n`), Wert fließt in `execSync('python3 -c "...")`. Fix: Python in separates `.py` auslagern, Pfad als Argument/Env statt Code-String. |

### HIGH
| # | Subsystem | Datei | Problem |
|---|---|---|---|
| N3 | agents | `agents/risk-of-bias.md:29` | `tools: [Read]`, aber Workflow ruft `vault.get_paper/add_quote/add_risk_of_bias/search` → Persistenz blockiert. |
| N4 | agents | `doabooks/kvk/oapen/tib-fetcher.md` | nur `Bash(browser-use:*)` (Colon) deklariert, Workflow nutzt Space-Syntax `browser-use open …` → alle Befehle Permission-Denied. |
| N5 | commands | `commands/history.md:75` | Literal `'<PLUGIN_ROOT>/mcp'` statt `${CLAUDE_PLUGIN_ROOT}` → `--restore` bricht mit ModuleNotFoundError. |
| N6 | commands | `commands/excel.md:4` | `allowed-tools: Read, Write` — `Bash(ls …)` (Z.35) + `Skill(xlsx)` (Z.50) fehlen → Excel-Export bricht. |
| N7 | hooks | `hooks/hooks.json:5,17` | beide Hooks matchen nur `Write`; **Edit-Tool umgeht verbatim-guard + decision-log** → Halluzinationsschutz aushebelbar. |
| N8 | docs | `docs/MIGRATION-v5-to-v6.md:58,319` | verweist auf nicht existentes `scripts/migrate_v5.py`. |
| N9 | skills | `skills/prisma-flow/SKILL.md:70` | dokumentierter Import `skills.prisma_flow.…` falsch (Verzeichnis hat Bindestrich, kein `__init__.py`) → ModuleNotFoundError. |
| N10 | vault | `mcp/academic_vault/server.py:369,387` | `supersede_decision` + `list_excluded_sources` sind nicht als `@mcp.tool` registriert → über MCP nicht aufrufbar. |

### MEDIUM
| # | Subsystem | Datei | Problem |
|---|---|---|---|
| N11 | commands | `commands/search.md:107,133` | Schritt 7 ≡ Schritt 9 (Relevanz-Scoring doppelt) → doppelter Scorer-Aufruf/Kosten. |
| N12 | commands | `commands/history.md:4` | `--batch`-Flag wird von `search.md` referenziert, in `history.md` aber undokumentiert/ohne Verhalten. |
| N13 | docs | `docs/MIGRATION-v5-to-v6.md:22,119,132` | dieselben Hook-Fehler wie README ('vier Hooks', 'SessionMid') — **#205 deckt nur README**. → an #205 anhängen. |
| N14 | scripts | `scripts/requirements.txt:6-7` | `pandas` + `openpyxl` nie in `scripts/*.py` genutzt (~50 MB unnötig). |
| N15 | scripts | `scripts/search.py:421` | arXiv-API über `http://` (pdf.py:142 nutzt korrekt `https://`) → MITM. |
| N16 | scripts | `scripts/search.py:358-396` | EconStor-OAI-Fallback `ListRecords` ohne Set/Limit → lädt kompletten Repo-Dump in Memory. |
| N17 | scripts | `scripts/configure_permissions.py:44` | nicht-atomares `write_text()` auf `~/.claude/settings.local.json` → Datenverlust bei Abbruch. |
| N18 | tests | `tests/evals/eval_runner.py:54-62` | kein `temperature=0`; Trigger-Evals N=10 mit 85%/10%-Schwellen → flaky CI. |
| N19 | vault | `mcp/academic_vault/db.py` (~30 Methoden) | SQLite-`conn.close()` nicht in `finally` → Connection-Leak bei Exception (WAL wächst). |
| N20 | vault | `mcp/academic_vault/server.py:279-284` | `add_chapter`: `except: pass` bei Malformed-JSON → Kapitel wird als `article-journal` gespeichert (Kette zu #213). |

### LOW
| # | Subsystem | Datei | Problem |
|---|---|---|---|
| N21 | commands | `commands/search.md:4` | `quote-extractor` in `allowed-tools`, aber nie aufgerufen. |
| N22 | scripts | `scripts/setup.sh:89-95` | Abschnitt-Nummerierung springt 5 → 7 (Schritt 6 fehlt). |
| N23 | skills | `skills/xlsx/scripts/office/validators/base.py:47` | Pfad-Tippfehler `fouth-edition` (×3). (xlsx ist vendored — ggf. wontfix/upstream.) |
| N24 | skills | book-handler, cluster-visualizer, citation-style-import, zotero-import, notebook-bundle | ASCII-Substitution im Body — **#175 nennt nur 2 Skills**. → an #175 anhängen. |
| N25 | skills | notebook-bundle, zotero-import `description:` | ASCII-Substitution in **Trigger-Phrasen** der description → Erkennungsrate. → an #175 anhängen. |
| N26 | tests | `evals/verbatim-guard/runner.py` | 10 Vault-Lookup-Cases nie in pytest integriert → laufen nie in CI. |
| N27 | vault | `mcp/academic_vault/retrieval.py:228` | `apply_reranker` gibt im Fallback `candidates` statt `enriched` zurück (`text`-Feld verloren). |

---

## 4. Zweitdurchlauf (Completeness) — zusätzliche Funde

| # | Schwere | Datei | Problem | Zuordnung |
|---|---|---|---|---|
| C1 | CRITICAL | `scripts/requirements.txt` | `mcp>=1.0`/`sqlite-vec` fehlen → siehe §2.2 | **→ Umbrella N1** |
| C2 | CRITICAL | `mcp/` | Namespace-Kollision mit SDK → siehe §2.3 | **→ Umbrella N1** |
| C3 | HIGH | `scripts/setup.sh:95` | `setup.md` dokumentiert SciHub-Opt-in (Schritt 7), in `setup.sh` **unimplementiert**; `test_scihub_optin.py` testet nur den .md-Text. | neu |
| C4 | MEDIUM | `.gitignore` + `scripts/bootstrap/gitignore.fragment` | `vault.db`/`*.db` nicht ignoriert → PII-DB versehentlich committbar. | **→ an #190 anhängen** |
| C5 | MEDIUM | `evals/` | 9 weitere Pre-v6.5-Skills ohne Eval-Verzeichnis (14/28 ganz ohne); `test_rest_evals.py:31` skippt still. | **→ an #198 anhängen** |
| C6 | LOW | `LICENSE:3` | „Copyright (c) 2026 Jonas" (nur Vorname) vs. „Jonas Ahler" im Manifest. | neu |

---

## 5. Vorgeschlagene Board-Aktionen

**Neue Issues anlegen (empfohlene Milestones):**

- **v6.5.1 (Release-Blocker):** N1-Umbrella (Server-Start, 3 Checkpunkte: .mcp.json,
  requirements, mcp-Namespace), N2 (Shell-Injection), N5 (history `<PLUGIN_ROOT>`),
  N7 (Edit-Hook-Bypass).
- **v6.5.2:** N3, N4, N6, N8, N9, N10, N11, N12, N15, N17, N18, N20, N27, C3.
- **v6.6:** N14, N16, N19, N21, N22, N23, N26, C6.

**In bestehende Issues einpflegen (Scope/Kommentar):**
- N13 → **#205**; N24 + N25 → **#175**; C4 → **#190**; C5 → **#198**; N20 verlinken mit **#213**.

**Scope-Edits an teil-gefixten Issues:** #170, #210, #211, #214 (siehe §1).

**Nichts zu schließen.**

---

## 5b. Umgesetzt am 2026-06-03 (Board-Stand: 77 offene Issues)

**26 neue Issues angelegt:**

| Milestone | Issues |
|---|---|
| v6.5.1 (Blocker) | #217 (N1 Server-Start), #218 (N2 Shell-Injection), #219 (N5 history `<PLUGIN_ROOT>`), #220 (N7 Edit-Hook-Bypass) |
| v6.5.2 | #221 (N3), #222 (N4), #223 (N6), #224 (N8), #225 (N9), #226 (N10), #227 (N11), #228 (N12), #229 (N15), #230 (N17), #231 (N18), #232 (N20), #233 (N27), #234 (C3) |
| v6.6 | #235 (N14), #236 (N16), #237 (N19), #238 (N21), #239 (N22), #240 (N23), #241 (N26), #242 (C6) |

**4 Kommentare angehängt:** #175 (N24+N25 ASCII), #190 (C4 vault.db gitignore), #198 (C5 9 weitere Skills), #205 (N13 Migration-Guide-Hooks).

**4 Scope-Edits (Body):** #170, #210, #211, #214 (Scope-Update-Notiz vorangestellt).

Milestone-Verteilung danach: v6.5.1 = 14 · v6.5.2 = 35 · v6.6 = 27 · v6.0 = 1.

---

## 6. Signal-Qualität
- 25 weitere Funde waren **real, aber bereits durch ein offenes Issue abgedeckt** →
  bestätigt, dass die bestehenden Issues korrekt sind.
- 4 Funde wurden in der Gegenprüfung **widerlegt** und verworfen.
