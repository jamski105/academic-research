# Spec: Chunk D — OA-Site-Subagenten (Ticket #81)

**Milestone:** v6.2 Wave 1, Stage 2  
**Branch:** feat/v6.2-D-oa-subagents  
**Ticket:** #81 — F16 — OA-Site-Subagenten: tib-fetcher, oapen-fetcher, doabooks-fetcher, kvk-fetcher

---

## Ziel

Vier OA-Site-Subagenten als Markdown-Agent-Dateien unter `agents/` implementieren.
Jeder Agent bedient genau eine Site per `browser-use` (kein curl/wget/direkter HTTP).
Output-Schema ist durch L0 gesperrt (5 Status-Werte).

---

## Output-Schema (gesperrt, L0-Note)

```json
{
  "status": "success" | "pickup_required" | "captcha" | "no_match" | "metadata_only",
  "source_subagent": "<agent-name>",
  "pdf_path": "<lokaler Pfad>",      // nur bei status=success
  "url": "<Detailseite>",            // bei metadata_only / no_match
  "tries": [],                       // optional, Retry-History
  "reason": "<Freitext>"             // optional, bei Fehlern
}
```

`metadata_only` = Buch gefunden, aber kein Volltext verfügbar.
`pickup_required` = Nur Bibliotheks-Standort bekannt (KVK-Spezialfall).

---

## Agenten

### 1. `agents/tib-fetcher.md`

- **model:** sonnet
- **maxTurns:** 15
- **tools:** `[Bash(browser-use:*), Read, Write]`
- **browser-guide:** `config/browser_guides/tib.md`
- Flow: TIB-Suche (`tib.eu/de/suchen?query=…`) → Titel/Autor/Jahr-Match → Detailseite
- OA-Filter: "Open Access"-Badge oder "Volltext"-Block auf Detailseite prüfen
- Download: `browser-use download` auf PDF-Link → `$OUTPUT_PATH`
- Validation: Magic-Bytes `%PDF`, Größe > 10 KB
- Fallback: `{status: metadata_only, source_subagent: tib-fetcher, url: <detailseite>}`
- Verbote im System-Prompt: kein curl/wget, keine direkten HTTP-Calls, keine fingierten Treffer

### 2. `agents/oapen-fetcher.md`

- **model:** sonnet
- **maxTurns:** 12
- **tools:** `[Bash(browser-use:*), Read, Write]`
- **browser-guide:** `config/browser_guides/oapen.md`
- Flow: oapen.org-Suche → Detailseite → "Download PDF"-Button
- OA-Invariante: oapen.org ist reine OA-Plattform → alle Treffer sind per Definition OA
- Download: `browser-use download` → `$OUTPUT_PATH`
- Validation: Magic-Bytes, Größe > 10 KB
- Fallback: `{status: metadata_only, source_subagent: oapen-fetcher, url: <detailseite>}`

### 3. `agents/doabooks-fetcher.md`

- **model:** sonnet
- **maxTurns:** 12
- **tools:** `[Bash(browser-use:*), Read, Write]`
- **browser-guide:** `config/browser_guides/doab.md`
- Flow: directory.doabooks.org-Suche via Browser (kein REST) → Detailseite → externer Volltext-Link
- OA-Invariante: DOAB listet nur OA-Bücher; Volltext-Link kann aber fehlen
- Download: Weiternavigation zu externem Provider (OAPEN, Verlag) → `browser-use download`
- Fallback: `{status: metadata_only, source_subagent: doabooks-fetcher, url: <detailseite>}`

### 4. `agents/kvk-fetcher.md`

- **model:** sonnet
- **maxTurns:** 12
- **tools:** `[Bash(browser-use:*), Read, Write]`
- **browser-guide:** `config/browser_guides/kvk.md`
- Flow: kvk.bibliothek.kit.edu-Suche → 80+ Kataloge → OA/Volltext-Treffer identifizieren
- OA-Filter: KVK ist Meta-Katalog (nicht ausschließlich OA); Agent filtert auf Volltext-Links/OA-Indikatoren
- Bei Volltext-Link: Download-Versuch → `{status: success, pdf_path: ...}`
- Bei reinem Bibliotheks-Nachweis: `{status: metadata_only, source_subagent: kvk-fetcher, url: ..., reason: "Standorte: [BSB München, UB Berlin, ...]"}`
- KVK-spezifisch: Standort-Info im `reason`-Feld; Master-Agent entscheidet Pickup-Liste-Eintrag

---

## Test-Strategie (TDD)

**Datei:** `tests/test_oa_fetchers.py`

Drei Test-Klassen:

1. **Frontmatter-Validierung** — alle 4 Agent-Dateien vorhanden, YAML-Frontmatter syntaktisch korrekt, Pflichtfelder gesetzt (`name`, `model: sonnet`, `maxTurns`, `tools` mit browser-use)
2. **Output-Schema-Validierung** — Mock-Outputs aller 5 Status-Werte gegen Schema validieren (JSON-Struktur, Pflichtfelder)
3. **Verbots-Check** — Agent-Dateien dürfen keine curl/wget/direkten HTTP-Calls enthalten; `browser-use`-Referenz muss vorhanden sein

---

## Evals

**Verzeichnis:** `evals/oa-fetchers/evals.json`

4 Eval-Cases (je 1 bekanntes OA-Buch pro Plattform):

| ID | Platform | Fixture |
|---|---|---|
| `oa-01` | TIB | "Open Access und Wissenschaftliches Publizieren" (ISBN 978-3-86541-416-5) |
| `oa-02` | OAPEN | "Open Access Publishing in European Networks" (DOI 10.5281/zenodo.3700985 o.ä.) |
| `oa-03` | DOAB | Springer-OA-Buch z.B. "The Open Access Advantage" |
| `oa-04` | KVK | Buch mit bekanntem Bibliotheks-Nachweis → erwartet `metadata_only` + Standort |

---

## Dateien (file boundary)

```
agents/tib-fetcher.md           (NEU)
agents/oapen-fetcher.md         (NEU)
agents/doabooks-fetcher.md      (NEU)
agents/kvk-fetcher.md           (NEU)
tests/test_oa_fetchers.py       (NEU)
evals/oa-fetchers/evals.json    (NEU)
specs/v6.2/D.md                 (diese Datei)
specs/v6.2/D-plan.md            (folgt)
```

---

## Abhängigkeiten

- **Chunk A** (`feat/v6.2-A-browser-guides`): Browser-Guides in `config/browser_guides/` — status `implementation_complete`; Guides via `git show` lesbar
- **Chunk G** (#80 Master-Agent): kommt später; Output-Schema ist aber bereits gesperrt
- Kein Vault-Zugriff, keine MCP-Server-Calls in diesen Agenten

---

## Akzeptanzkriterien (Abgleich #81)

- [x] 4 Agent-Files mit korrektem Frontmatter
- [x] model: sonnet, tools mit browser-use:*, maxTurns gesetzt
- [x] OA-Filter-Logik für jede Plattform spezifisch beschrieben
- [x] Verbote im System-Prompt verankert
- [x] browser-guide-Referenz auf `config/browser_guides/<site>.md`
- [x] Output-Schema einheitlich (5 Status-Werte)
- [x] 4 Eval-Cases
- [x] Tests: Frontmatter + Schema-Validierung + Verbots-Check
