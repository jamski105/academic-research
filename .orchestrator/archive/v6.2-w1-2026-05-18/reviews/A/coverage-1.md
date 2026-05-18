# Coverage Report — Chunk A / PR #131 / Iteration 1

**Ticket:** #87 — v6.2 · F16 — Browser-Guides für Buch-Download
**Spec:** /Users/j65674/Repos/academic-research-v6.2-A/specs/v6.2/A.md
**PR:** #131 (state: OPEN)
**Date:** 2026-05-18

---

## AC Summary

ACs from issue #87 / improved ticket 87.draft.md + spec A.md:

1. `config/browser_guides/tib.md` existiert mit vollständiger Pflichtstruktur
2. `config/browser_guides/oapen.md` existiert mit vollständiger Pflichtstruktur
3. `config/browser_guides/doab.md` existiert mit vollständiger Pflichtstruktur
4. `config/browser_guides/degruyter.md` existiert mit vollständiger Pflichtstruktur
5. `config/browser_guides/nationallizenzen.md` existiert mit vollständiger Pflichtstruktur
6. `config/browser_guides/ebook-central.md` existiert mit vollständiger Pflichtstruktur
7. `config/browser_guides/kvk.md` existiert mit vollständiger Pflichtstruktur
8. `config/browser_guides/springer.md` auf Buch-Download-Flow aktualisiert
9. Alle 8 Guides verwenden dieselbe Abschnittsstruktur (5 H2: Login-Flow · Discovery-Pfad · Volltext-Lokation · Pickup-Triggers · Bekannte Fallstricke)
10. Jeder korrespondierende Subagent in #81/#82 enthält expliziten Verweis (`browser-guide: <pfad>`)

Note: Spec A.md §"Nicht in Scope" explizit ausschließt Test-Suite ("documentation-only; keine automatisierten Tests erforderlich"). ACs sind daher reine Docs-Existence/Structure-Checks.

---

## Per-AC Coverage

### AC1: `config/browser_guides/tib.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/tib.md` — ADDED, 52 Zeilen
- H2-Abschnitte vorhanden: `## Login-Flow`, `## Discovery-Pfad`, `## Volltext-Lokation`, `## Pickup-Triggers`, `## Bekannte Fallstricke` (alle 5, in korrekter Reihenfolge)
- Header enthält URL (`https://www.tib.eu`), Auth, Anti-Scraping-Einschätzung (Spec-Anforderung erfüllt)

---

### AC2: `config/browser_guides/oapen.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/oapen.md` — ADDED, 43 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://www.oapen.org`), Auth (keine), Anti-Scraping (niedrig)

---

### AC3: `config/browser_guides/doab.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/doab.md` — ADDED, 50 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://www.doabooks.org`), Auth (keine), Anti-Scraping (niedrig)

---

### AC4: `config/browser_guides/degruyter.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/degruyter.md` — ADDED, 60 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://www.degruyter.com`), Auth (Shibboleth/IP/OA), Anti-Scraping (mittel)

---

### AC5: `config/browser_guides/nationallizenzen.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/nationallizenzen.md` — ADDED, 57 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://www.nationallizenzen.de`), Auth (DFN-AAI/Shibboleth), Anti-Scraping (niedrig/mittel)

---

### AC6: `config/browser_guides/ebook-central.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/ebook-central.md` — ADDED, 57 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://ebookcentral.proquest.com`), Auth (Shibboleth/HAN/IP), Anti-Scraping (niedrig)

---

### AC7: `config/browser_guides/kvk.md` mit Pflichtstruktur

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/kvk.md` — ADDED, 66 Zeilen
- H2-Abschnitte alle 5 vorhanden in korrekter Reihenfolge
- Header: URL (`https://kvk.bibliothek.kit.edu`), Auth (keine/Fernleihe), Anti-Scraping (niedrig)

---

### AC8: `config/browser_guides/springer.md` auf Buch-Download-Flow aktualisiert

**Status: PASS**

Evidence:
- PR diff: `config/browser_guides/springer.md` — MODIFIED (+54 Zeilen)
- Neuer `## Buch-Download`-Block nach bestehendem v6.0-Inhalt hinzugefügt
- Block enthält `springer-book-fetcher`-kompatiblen Flow (URL-Muster, Login-Flow, Discovery, Volltext-Lokation, Pickup-Triggers, Bekannte Fallstricke)

Hinweis: Spec A.md §Konsistenz (Zeile 169) fordert "5 neue H2-Abschnitte als zusammenhängender ## Buch-Download-Block". Die PR-Implementierung verwendet `## Buch-Download` als H2-Wrapper und die 5 Sub-Abschnitte als `### H3`. Dies weicht leicht von der Formulierung "5 neue H2" ab, entspricht aber dem inhaltlichen Intent (Spec Zeile 49: "Der springer.md-Update ergänzt diese Abschnitte nach dem bestehenden v6.0-Inhalt unter einem eigenen ## Buch-Download-Block"). Die H3-Lösung ist sinnvoller (vermeidet H2-Konflikte mit dem Artikel-Guide-Teil) und deckt alle 5 Pflicht-Abschnitte ab — kein funktionaler Mangel.

---

### AC9: Alle 8 Guides verwenden dieselbe Abschnittsstruktur

**Status: PASS**

Evidence:
- grep auf PR diff nach `^+## ` zeigt für alle 7 neuen Guides jeweils exakt 5 H2-Abschnitte in Reihenfolge: Login-Flow, Discovery-Pfad, Volltext-Lokation, Pickup-Triggers, Bekannte Fallstricke
- Springer-Update: H3-Entsprechungen aller 5 Abschnitte im `## Buch-Download`-Block (konsistente Benamung)
- Konsistenz-Anforderung des Spec (Status-Felder `success | pickup_required | captcha | no_match`) in allen Guides referenziert (jeder Guide enthält `status: pickup_required`, die meisten auch `status: captcha` und `status: no_match`)

---

### AC10: Subagenten in #81/#82 enthalten `browser-guide: <pfad>`-Verweis

**Status: FAIL**

Evidence:
- PR diff enthält **keine Änderungen an Agent-Dateien** — `gh pr diff 131 | grep "^diff --git"` zeigt nur `config/browser_guides/` und `specs/v6.2/` Dateien
- Das `agents/`-Verzeichnis enthält nur vorhandene Agenten (`figure-verifier.md`, `quality-reviewer.md`, `query-generator.md`, `quote-extractor.md`, `relevance-scorer.md`) — keine tib-fetcher, oapen-fetcher, springer-book-fetcher, book-fetcher oder ähnliche Subagenten
- Die korrespondierenden Subagenten aus #81/#82 existieren noch nicht im Repository (Chunks D und E sind noch nicht geliefert)

Gap: AC fordert, dass bestehende Subagenten einen expliziten `browser-guide: <pfad>`-Verweis erhalten. Da die Subagenten (Chunks D/E) noch nicht existieren, ist dieser AC technisch nicht erfüllbar ohne Ahead-of-Schedule-Arbeit. Spec A.md §"Nicht in Scope" schließt "Subagenten-Implementierungen (Chunk D und E)" aus — die Frage ist ob die Rück-Referenz aus AC10 dennoch Chunk A zugeordnet ist oder Chunk D/E.

Bewertung: AC10 ist im Ticket #87 explizit aufgeführt und nicht unter "Nicht in Scope" des Specs ausgeschlossen (Spec schließt nur Implementierungen aus, nicht Referenz-Updates). Da die Subagenten-Dateien noch nicht existieren, kann dieser AC erst bei Chunk D/E geschlossen werden. Dies ist ein **bekannter Abhängigkeits-Gap**, kein Implementierungsfehler des PR.

---

## Overall Assessment

| AC | Status | Note |
|----|--------|------|
| AC1 tib.md vollständig | PASS | |
| AC2 oapen.md vollständig | PASS | |
| AC3 doab.md vollständig | PASS | |
| AC4 degruyter.md vollständig | PASS | |
| AC5 nationallizenzen.md vollständig | PASS | |
| AC6 ebook-central.md vollständig | PASS | |
| AC7 kvk.md vollständig | PASS | |
| AC8 springer.md Buch-Update | PASS | H3 statt H2 in Buch-Download — inhaltlich korrekt |
| AC9 einheitliche Struktur | PASS | |
| AC10 Subagenten-Backreferences | FAIL | Subagenten existieren noch nicht (Chunks D/E); strukturelle Abhängigkeit, kein Chunk-A-Implementierungsfehler |

**Verdict:** PARTIAL — 9/10 ACs covered. AC10-Lücke ist eine bekannte Cross-Chunk-Abhängigkeit (Subagenten erst in D/E), keine Regression in diesem PR. Docs-only chunk ohne Test-Anforderung (Spec §"Nicht in Scope" explizit).

**Recommendation:** merge — AC10 ist durch Chunk D/E zu erfüllen; die Browser-Guide-Dateien sind vollständig und korrekt implementiert.
