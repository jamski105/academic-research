# Spec — Chunk J: Auto-Download Tier-Pipeline-Erweiterung (F6)

**Ticket:** #78 — v6.2 · F6 — Auto-Download-Pipeline auf 8 Tiers erweitern
**Branch:** `feat/v6.2-J-tier-pipeline`
**Datum:** 2026-05-13

---

## Ziel

Die bestehende 5-Tier-Fallback-Pipeline in `scripts/pdf.py` wird um drei neue Tiers
(OpenAccessButton, DOAB, EuropePMC) erweitert. Ziel: ≥ 70 % Hit-Rate bei 20 kuratierten
Testquellen (Bücher, Biomedizin-DOIs, allgemeine OA-Paper).

---

## Neue Tier-Funktionen

### `tier_openaccessbutton(client, doi) → str | None`  — Tier 6

- Ruft `https://api.openaccessbutton.org/find?id=<doi>` auf.
- Gibt die erste PDF-URL aus dem Response-Feld `data.url` zurück oder `None`.
- Bei HTTP-Fehler: Exception propagieren (analog bestehende Tiers).

### `tier_doab(client, isbn_or_title) → str | None`  — Tier 7

- Ruft `https://directory.doabooks.org/rest/search?query=<isbn_or_title>&expand=bitstreams` auf.
- Parst das JSON-Array: erstes Element mit `bitstreams`-Eintrag `mimeType == "application/pdf"`.
- Gibt `retrieveLink` der gefundenen Bitstream zurück (ggf. mit Basis-URL `https://directory.doabooks.org` voranstellen, falls relativ).
- Bei leerer Trefferliste oder fehlendem PDF: `None`.

### `tier_europepmc(client, doi) → str | None`  — Tier 8

- Ruft `https://www.europepmc.org/backend/europepmc/findByQuery.do?query=DOI:<doi>&format=json&resulttype=core&pageSize=1` auf.
- Parst `resultList.result[0].fullTextUrlList.fullTextUrl[]`: wählt ersten Eintrag mit `documentStyle == "pdf"` und `availability == "Open access"`.
- Gibt die `url` zurück oder `None`.

---

## `resolve_pdf_url()` — Erweiterung

Neue Aufruf-Reihenfolge (Bücher vorgezogen für Tier 7):

```
Tier 1: Unpaywall          (DOI)
Tier 2: CORE               (DOI)
Tier 3: Module OA URLs     (paper metadata)
Tier 4: Direct URL         (paper metadata)
Tier 5: arXiv Title Search (title)
─── Bücher-Priorisierung ───
Tier 7: DOAB               (isbn oder title) — wenn paper.get("type") in {"book","chapter"}
Tier 6: OpenAccessButton   (DOI)
─── Allgemeiner Fallback ───
Tier 7: DOAB               (isbn oder title) — wenn nicht bereits versucht
Tier 8: EuropePMC          (DOI) — wenn DOI mit einem BIOMED_DOI_PREFIXES-Eintrag beginnt, oder als letzter Fallback
```

Implementierungs-Hinweis: Es ist einfacher, die Logik als geordnete Liste von
`(condition, callable)` zu schreiben, statt verschachtelte ifs. Die Funktion
`resolve_pdf_url` gibt weiterhin `(url, source_tier, error)` zurück.

---

## Biomedizin-DOI-Präfix-Liste

```python
BIOMED_DOI_PREFIXES = [
    "10.1016/j.",   # Elsevier Biomedical
    "10.1186/",     # BMC
    "10.1371/",     # PLOS
    "10.3390/",     # MDPI Biology
]
```

Diese Konstante steht in `scripts/pdf.py` direkt nach den Modul-Importen.

---

## Datei-Grenze

| Datei | Aktion |
|---|---|
| `scripts/pdf.py` | Erweitern (3 neue Funktionen + aktualisierte `resolve_pdf_url`) |
| `tests/test_pdf_tiers.py` | Neu anlegen |
| `docs/evals/v6.2-tier-eval.md` | Neu anlegen |
| `evals/auto-download/sources.yaml` | Neu anlegen |
| `specs/v6.2/J.md` | Diese Datei |
| `specs/v6.2/J-plan.md` | Plan (nächste Datei) |

---

## Unit-Tests (Überblick)

Datei: `tests/test_pdf_tiers.py`

Mock-Strategie: `unittest.mock.patch` auf `httpx.Client.get` (analog `test_ocr_detection.py`).
Jeder Tier hat mindestens zwei Tests:
- **Erfolgsfall**: Mock gibt valide JSON-Response zurück, Funktion gibt URL-String zurück.
- **Leerfall**: Mock gibt leere Trefferliste/fehlendes Feld zurück, Funktion gibt `None`.

Zusätzlich: Integration-Test für `resolve_pdf_url()`:
- Bücher-Priorisierung: DOAB wird vor OpenAccessButton versucht wenn `type == "book"`.
- EuropePMC aktiviert sich bei Biomedizin-DOI-Präfix.

---

## Eval

- 20 kuratierte Testquellen in `evals/auto-download/sources.yaml`.
  - 5 Bücher (aus v6.1-Eval-Material).
  - 8 Biomedizin-Paper (DOI-Präfixe 10.1016/j., 10.1186/, 10.1371/, 10.3390/).
  - 7 allgemeine OA-Paper (Crossref/arXiv/OpenAlex).
- Eval läuft **offline** (kein Live-API-Call in CI): sources.yaml enthält `expected_hit: true/false`.
- Eval-Report: `docs/evals/v6.2-tier-eval.md` gemäß `docs/evals/TEMPLATE.md`.
- Hit-Rate-Schwelle: ≥ 70 % (14/20).

---

## Nicht in Scope

- Browser-basierter Download (F16).
- Änderungen am `book-handler`-Skill oder OCR-Pipeline.
- Änderungen an der Bibliotheks-Excel (F5).
