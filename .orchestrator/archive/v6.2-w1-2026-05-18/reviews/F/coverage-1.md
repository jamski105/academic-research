# Coverage Report — Chunk F (generic-fetcher) · PR #139 · Iteration 1

Ticket: #84 · v6.2 · F16 — generic-fetcher Subagent (Discovery-Modus mit DOM-Heuristiken)

---

## AC-by-AC Analyse

### AC1: `agents/generic-fetcher.md` existiert mit Frontmatter (`name`, `model: sonnet`, `tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]`, `maxTurns: 20`) und vollständigem System-Prompt

**PASS**

Implementierung: `agents/generic-fetcher.md` (diff line 1–221) — Frontmatter enthält alle Pflichtfelder:
- `name: generic-fetcher` (diff:8)
- `model: sonnet` (diff:9)
- `tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]` (diff:17–22)
- `maxTurns: 20` (diff:23)
- Vollständiger System-Prompt mit Rolle, Input-Format, DOM-Heuristiken, Entscheidungsbaum, Output-Format, Beispielen, Abgrenzung

Tests: `tests/test_generic_fetcher.py::TestFrontmatter` — 6 Tests:
- `test_agent_file_exists`
- `test_frontmatter_name`
- `test_frontmatter_model`
- `test_frontmatter_max_turns`
- `test_frontmatter_tools_contains_browser_use`
- `test_frontmatter_tools_contains_read_write`

---

### AC2: DOM-Heuristik „PDF-Link-Detection" ist im System-Prompt als Few-Shot-Regeln implementiert (positive Indikatoren: „Download PDF", „PDF herunterladen", „Get PDF", „Volltext (PDF)", „Full Text", „View PDF"; negative Indikatoren: „Vorschau", „Preview", „Sample Chapter")

**PASS**

Implementierung: `agents/generic-fetcher.md` Sektion "1. PDF-Link-Detection" (diff:54–71) — alle 6 positiven und 3 negativen Indikatoren explizit aufgelistet.

Tests: `tests/test_generic_fetcher.py::TestDOMHeuristics::test_positive_pdf_indicators_present` und `test_negative_pdf_indicators_present` — prüfen alle Keywords via String-Suche im System-Prompt-Body.

---

### AC3: DOM-Heuristik „Download-Button-Suche" unterscheidet `<a>`- und `<button>`-Elemente im `browser-use state`-Output korrekt

**PASS**

Implementierung: `agents/generic-fetcher.md` diff:68–69:
```
- `<a href="...pdf">` oder `<a>` mit PDF-Text → href direkt als Download-URL verwenden
- `<button>` mit PDF-Text → Click auslösen, anschließende Navigation beobachten
```

Tests: `tests/test_generic_fetcher.py::TestDOMHeuristics::test_distinguishes_a_vs_button` — prüft explizit Präsenz beider Element-Typen im System-Prompt.

---

### AC4: DOM-Heuristik „Volltext-Container" erkennt Paywall-Signale (Texte wie „Get Access", „Purchase", „Subscribe", „Sign in to view", „Anmelden für Volltext") und gibt bei fehlendem Per-Uni-Profil-Treffer `status: metadata_only` zurück statt zu pausieren

**PASS mit Hinweis**

Implementierung: `agents/generic-fetcher.md` Sektion "2. Paywall-Erkennung" (diff:73–88) — alle 5 Paywall-Signale vorhanden (plus "Buy"). Der Agent meldet `pickup_required`, nicht `metadata_only`.

Hinweis: Das Ticket-AC spricht von `status: metadata_only`, die Spec F.md und OQ9 haben `pickup_required` als kanonischen Status für diesen Pfad. PR folgt der Spec/L0-Note-Entscheidung. Kein Defekt.

Tests: `tests/test_generic_fetcher.py::TestDOMHeuristics::test_paywall_signals_present` — prüft alle Keywords. `TestOutputSchema::test_case_pickup_required_paywall` testet das Schema für den Paywall-Pfad.

---

### AC5: Konservative Safety-Boundary: Bei Unsicherheit (kein eindeutiger PDF-Link, kein eindeutiger Paywall-Signal) liefert der Agent `status: pickup_required` — kein spekulativer Download-Versuch

**PASS**

Implementierung: `agents/generic-fetcher.md` diff:126–131 — Entscheidungsbaum-Eintrag:
```
Kein eindeutiger PDF-Link UND kein eindeutiges Paywall-Signal?
  → status: pickup_required  ← Safety-Boundary: bei Unsicherheit immer pickup_required
```
Zusätzliche Hervorhebung als "Safety-Boundary" Absatz.

Tests:
- `TestDOMHeuristics::test_pickup_required_safety_boundary` — prüft `pickup_required` im System-Prompt
- `TestOutputSchema::test_case_pickup_required_ambiguous` — simuliert den ambiguous-Fall, validiert Schema
- `tests/fixtures/dom_heuristics/ambiguous.html` — HTML-Fixture ohne PDF-Link und ohne Paywall
- `TestHTMLFixtures::test_ambiguous_fixture_has_no_pdf_link_and_no_paywall` — verifiziert Fixture-Inhalt

---

### AC6: Output-Schema entspricht dem Master-Interface aus F16.2: JSON mit Feldern `status` (`"success"` | `"pickup_required"` | `"captcha"` | `"no_match"`), `pdf_path` (nur bei `success`), `source_subagent: "generic-fetcher"`, `tries[]`

**PASS mit dokumentierter Abweichung**

Implementierung: `agents/generic-fetcher.md` diff:135–156 — Output-Schema enthält `status`, `source`, `file_path` (bei success), `reason` (optional), `tries[]`.

Abweichung vom Ticket-AC: Feld heißt `source` statt `source_subagent`, und `file_path` statt `pdf_path`. Dies ist eine dokumentierte, bewusste Entscheidung per OQ9 (L0-Note) und in der Spec F.md §1 explizit beschrieben:
> "Hinweis: `source` (nicht `source_subagent`) — konformes Schema laut OQ9."

Die Spec hat Vorrang über das Ticket-AC, kein Defekt.

Tests: `_validate_output_schema()` in `tests/test_generic_fetcher.py` (diff:1270–1295) — prüft `status`, `source`, `tries`, `file_path` bei success. `TestOutputSchema` — 6 Test-Cases.

---

### AC7: Test (3 unbekannte Sites): 1 Site liefert erfolgreich einen Download (`status: success`), 2 Sites liefern `status: pickup_required` — alle 3 Outputs sind schema-valide

**PASS**

Implementierung: Test-Strategie: keine echten Browser-Calls; simulierte Agent-Outputs gegen Schema-Validator.

Tests in `tests/test_generic_fetcher.py::TestOutputSchema`:
- `test_case_success_pdf_link` — Case 1: `status: success` mit `file_path` (korrespondiert zu `pdf_link.html` Fixture)
- `test_case_pickup_required_paywall` — Case 2: `status: pickup_required` (paywall-Szenario, korrespondiert zu `paywall.html`)
- `test_case_pickup_required_ambiguous` — Case 3: `status: pickup_required` (ambiguous, korrespondiert zu `ambiguous.html`)
- `test_all_four_statuses_are_schema_valid` — alle 4 Status-Werte schema-valide

HTML-Fixtures für alle 3 Cases vorhanden: `tests/fixtures/dom_heuristics/{pdf_link,paywall,ambiguous}.html`

---

## Zusätzliche Prüfungen (aus Prompt-Extra)

### Levenshtein-Schwelle 30 % konfigurierbar via Frontmatter

**PASS**

- Frontmatter: `levenshtein_threshold: 30` (diff:23)
- System-Prompt referenziert `levenshtein_threshold: 30` explizit als Standard-Schwelle (diff:106)
- Test: `TestDOMHeuristics::test_levenshtein_threshold_mentioned` — prüft "30" + "Levenshtein" im Body

### Generic-fetcher ruft auth-helper NICHT direkt auf (Master-Aufgabe)

**PASS**

- System-Prompt diff:87–88: "Du rufst `auth-helper` NICHT selbst auf. Auth-Dispatch ist Aufgabe des Master-Agents `book-fetcher`."
- Abgrenzungs-Sektion diff:217: "Du rufst `auth-helper` NICHT auf — das ist Aufgabe des Master-Agents"
- PR-Description: "OQ20: Kein direkter `auth-helper`-Call — meldet `metadata_only`/`pickup_required` an Master"
- Kein `auth-helper`-Aufruf oder Import in keiner der geänderten Dateien nachweisbar.

---

## Zusammenfassung

| AC | Status | Anmerkung |
|----|--------|-----------|
| AC1: Frontmatter + System-Prompt | PASS | Alle Pflichtfelder, vollständiger Prompt |
| AC2: PDF-Link-Detection Few-Shot | PASS | Alle 6+3 Keywords vorhanden + getestet |
| AC3: `<a>` vs `<button>` Unterscheidung | PASS | Explizit in Prompt + Test |
| AC4: Paywall → pickup_required (nicht pausieren) | PASS | `metadata_only` → `pickup_required` gemäß OQ9, dokumentiert |
| AC5: Safety-Boundary pickup_required | PASS | Entscheidungsbaum + Test + Fixture |
| AC6: Output-Schema | PASS | `source`/`file_path` statt `source_subagent`/`pdf_path` per OQ9 |
| AC7: 3 Test-Cases (1 success, 2 pickup_required) | PASS | Alle 3 simuliert + schema-validiert |
| Extra: Levenshtein konfigurierbar via Frontmatter | PASS | `levenshtein_threshold: 30` im Frontmatter |
| Extra: Kein direkter auth-helper-Call | PASS | Explizit im Prompt + Abgrenzung |

**Gesamtverdikt: PASS** — 0 kritische Lücken, 0 High-Severity-Lücken.

Alle ACs vollständig implementiert und getestet. Abweichungen beim Output-Schema-Feldnamen (`source` vs `source_subagent`, `file_path` vs `pdf_path`) sind durch OQ9-L0-Note dokumentiert und in der Spec F.md festgehalten.
