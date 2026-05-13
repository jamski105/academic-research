# Spec: Chunk F — F16.4 generic-fetcher Subagent

## Ziel

Fallback-Subagent für die F16-Beschaffungspipeline. Operiert ohne Site-spezifisches
Wissen und entscheidet anhand von DOM-Heuristiken (PDF-Button-Erkennung, Paywall-
Erkennung, Captcha-Erkennung, Titelabgleich), ob ein Download möglich ist oder
`pickup_required` gemeldet wird.

## Scope (file boundary)

| Datei | Aktion |
|---|---|
| `agents/generic-fetcher.md` | CREATE |
| `tests/test_generic_fetcher.py` | CREATE |
| `tests/fixtures/dom_heuristics/pdf_link.html` | CREATE |
| `tests/fixtures/dom_heuristics/paywall.html` | CREATE |
| `tests/fixtures/dom_heuristics/ambiguous.html` | CREATE |
| `specs/v6.2/F.md` | CREATE (diese Datei) |
| `specs/v6.2/F-plan.md` | CREATE |

---

## 1. Agent-Datei `agents/generic-fetcher.md`

### Frontmatter

```yaml
name: generic-fetcher
model: sonnet
description: |
  Fallback-Subagent. Bedient eine beliebige wissenschaftliche Site per browser-use,
  ohne vorgegebenen Site-Guide. Entscheidet anhand von DOM-Heuristiken
  (PDF-Button, Access-Banner, Login-Wall), ob ein Download möglich ist.
tools:
  - Bash(browser-use:*)
  - Bash(browser-use *)
  - Read
  - Write
maxTurns: 20
levenshtein_threshold: 30
```

### System-Prompt Gliederung

1. **Rolle** — Fallback-Discovery-Agent ohne Site-Guide
2. **Input-Format** — JSON `{url, title, doi?, isbn?}`
3. **DOM-Heuristiken** (Few-Shot-Regeln):
   - PDF-Link-Detection (Positive + Negative Indikatoren)
   - Download-Button-Suche (`<a>` vs. `<button>` aus browser-use state)
   - Volltext-Container / Paywall-Erkennung
   - Captcha-Erkennung
   - Falscher-Treffer-Erkennung (Levenshtein ≤ 30 % Differenz = OK)
4. **Entscheidungsbaum** — wann success / pickup_required / captcha / no_match
5. **Output-Schema**
6. **Safety-Boundary** — bei Unsicherheit immer pickup_required

### DOM-Heuristiken (Few-Shot-Regeln)

#### PDF-Link-Detection
Positive Indikatoren (Treffer):
- "Download PDF", "PDF herunterladen", "Get PDF", "Volltext (PDF)", "Full Text", "View PDF"

Negative Indikatoren (kein Treffer):
- "Vorschau", "Preview", "Sample Chapter"

Element-Typen: `<a href="*.pdf">` oder `<button>` mit PDF-Text.
Bei `<a>`: href direkt als Download-URL verwenden.
Bei `<button>`: Click auslösen, anschließende Navigation beobachten.

#### Paywall-Erkennung / Volltext-Container
Signale:
- "Get Access", "Purchase", "Buy", "Subscribe", "Sign in to view", "Anmelden für Volltext"
- Aktion: Per-Uni-Profil prüfen — wenn kein Lizenz-Treffer → `status: metadata_only` melden
  (Auth-Dispatch ist Aufgabe des Master-Agents, nicht des generic-fetcher)

#### Captcha-Erkennung
Signale:
- "I'm not a robot", "Please verify", "reCAPTCHA"
- Aktion: Screenshot, abbrechen mit `status: captcha`

#### Falscher-Treffer-Erkennung
- Treffer-Titel vs. Input-Titel: Levenshtein-Differenz > 30 % → kein Treffer
- Default-Schwelle 30 %, konfigurierbar via `levenshtein_threshold` Frontmatter
- Bei falschem Treffer: zurück zur Trefferliste, nächster Eintrag

### Entscheidungsbaum

```
Seite geladen?
  nein → status: no_match
  ja →
    Captcha? → status: captcha (+ screenshot)
    PDF-Link (positiv, kein negativ)? → Download → status: success + file_path
    Paywall (kein Profil-Treffer)? → status: pickup_required
    Kein eindeutiger Hinweis → status: pickup_required (Safety-Boundary)
```

### Output-Schema

Kanonisches Schema (OQ9):

```json
{
  "status": "success | pickup_required | captcha | no_match",
  "source": "generic-fetcher",
  "file_path": "<nur bei success>",
  "reason": "<optionale Erläuterung>",
  "tries": ["<beschreibung versuch 1>", "..."]
}
```

**Hinweis:** `source` (nicht `source_subagent`) — konformes Schema laut OQ9. Das
Ticket-Acceptance-Criterion nennt `source_subagent`, die L0-Note OQ9 hat `source` als
kanonisch. Implementierung folgt L0-Note.

---

## 2. Tests `tests/test_generic_fetcher.py`

Die Tests prüfen:
1. **Frontmatter-Validierung** — agent-Datei hat alle Pflichtfelder (`name`, `model`,
   `tools`, `maxTurns`)
2. **Schema-Validierung (3 Cases)** — simuliert Agent-Output gegen Pydantic/dict-Schema:
   - Case 1: `status: success` mit `file_path` (clear PDF link)
   - Case 2: `status: pickup_required` (paywall, kein Profil)
   - Case 3: `status: pickup_required` (ambiguous, kein klarer Link)
3. **DOM-Heuristik Text-Checks** — prüft, dass der System-Prompt die definierten
   Schlüsselwörter (positive/negative Indikatoren) enthält

### Test-Strategie

Keine echten Browser-Calls — Tests arbeiten auf:
- YAML-Frontmatter aus `agents/generic-fetcher.md` (via `yaml` Parser)
- Markdown-Text des System-Prompts (via string search)
- Fixture-HTML-Dateien als Referenz für DOM-Heuristik-Beispiele

---

## 3. HTML-Fixtures `tests/fixtures/dom_heuristics/`

| Datei | Inhalt | Erwartetes Ergebnis |
|---|---|---|
| `pdf_link.html` | Seite mit `<a>Download PDF</a>` | success |
| `paywall.html` | Seite mit "Get Access" Banner | pickup_required |
| `ambiguous.html` | Seite ohne klaren PDF-Link und ohne Paywall | pickup_required |

---

## 4. Abgrenzung

- Auth-Dispatch (auth-helper aufrufen) → **Master-Agent** Chunk G, nicht generic-fetcher
- Captcha lösen → nicht möglich, immer `status: captcha`
- Site-spezifische Navigation → dedizierte Site-Subagenten (D, E)
- Direkte HTTP-Calls (curl, requests) → verboten, nur browser-use

---

## 5. Abhängigkeiten

- Keine Code-Abhängigkeiten (nur Markdown-Agent-Datei + pytest-Tests)
- Voraussetzung: Python venv mit `pytest`, `pyyaml`, `python-Levenshtein` (nur für Tests)

---

## 6. Offene Punkte (bereits entschieden durch L0-Notes)

- Levenshtein-Schwelle: **30 %** default (OQ19)
- Auth-Dispatch: **Master** (OQ20) — generic-fetcher meldet nur pickup_required
- Output-Schema `source`-Feld: kanonisch `source` (OQ9), nicht `source_subagent`
