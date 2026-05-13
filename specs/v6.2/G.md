# Spec: G — Master-Agent book-fetcher (v6.2, #80)

## Ziel

Implementierung des Master-Orchestrators `agents/book-fetcher.md` für das
Universal-Book-Fetcher-System (F16). Der Master-Agent koordiniert alle
spezialisierten Subagenten sequentiell, ohne selbst Browser-Aufrufe zu machen.

---

## Agent-Definition (`agents/book-fetcher.md`)

### Frontmatter (LOCKED)

```yaml
name: book-fetcher
model: sonnet
tools: [Read, Write, "Agent(doabooks-fetcher)", "Agent(oapen-fetcher)", "Agent(tib-fetcher)", "Agent(kvk-fetcher)", "Agent(springer-book)", "Agent(degruyter)", "Agent(nationallizenzen)", "Agent(ebook-central)", "Agent(auth-helper)", "Agent(generic-fetcher)"]
maxTurns: 8
```

Kein `Bash`, kein direkter HTTP-Zugriff.

---

## Input-Parser

Der Agent erkennt vier Eingabetypen:

| Typ | Erkennungs-Pattern |
|-----|-------------------|
| ISBN | `\b97[89][- ]?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?\d\b` oder ISBN-10 `\b\d{9}[\dX]\b` |
| DOI | Beginnt mit `10\.` gefolgt von `\d{4,}/` |
| URL | Beginnt mit `http://` oder `https://` |
| Freitext/Titel | Alles andere |

Die normalisierte Eingabe wird als `identifier` + `identifier_type` intern verwendet.

---

## Profil-Lesen

Vor dem Routing liest der Agent:

```
~/.academic-research/library-profiles/active.yaml
```

Relevante Felder: `licensed_sites` (Liste der lizenzierten Hosts).

---

## Routing-Logik (LOCKED)

### Schritt 1: OA-Subagenten (sequentiell)

Reihenfolge: `doabooks-fetcher` → `oapen-fetcher` → `tib-fetcher` → `kvk-fetcher`

- Jeder Subagent erhält: `{isbn/doi/title/url, output_path}`
- Bei `status: success` → sofort stoppen, Ergebnis zurückgeben
- Bei `status: no_match` → nächsten OA-Subagenten versuchen
- Bei `status: metadata_only` → notieren, nächsten OA-Subagenten versuchen

### Schritt 2: Verlags-Subagenten (nur wenn alle OA `metadata_only` oder `no_match`)

Aktivierungsbedingung: ≥1 OA-Subagent hat `metadata_only` UND Site ist in `licensed_sites`.

Domain-zu-Subagent-Mapping:
- `link.springer.com` → `springer-book`
- `degruyter.com` → `degruyter`
- `nationallizenzen.de` → `nationallizenzen`
- `ebookcentral.proquest.com` → `ebook-central`

Bei ISBN/DOI/Titel (keine URL): alle vier Verlags-Subagenten in Reihenfolge versuchen,
sofern der Host in `licensed_sites` ist.

**Auth-Retry-Logik:**
- Verlags-Subagent gibt `auth_required` zurück →
  1. Rufe `auth-helper` auf mit `{target_url, profile_path}`
  2. Bei `{status: authenticated}`: Selben Verlags-Subagenten nochmals aufrufen (einmalig)
  3. Bei `{status: captcha}`: Master gibt `{status: captcha, ...}` zurück
  4. Bei `{status: auth_failed}`: Nächsten Verlags-Subagenten versuchen

### Schritt 3: Fallback generic-fetcher

Wenn weder OA- noch Verlags-Subagenten `success` liefern:
- Rufe `generic-fetcher` auf mit `{url?, title?, doi?, isbn?, output_path}`
- `url`: beste bekannte URL aus vorherigen `metadata_only`-Responses

---

## Output-Schema (LOCKED)

```json
{
  "status": "success" | "pickup_required" | "captcha" | "no_match",
  "source": "<subagent-name>",
  "file_path": "<absoluter-pfad-zu-pdf>",
  "reason": "<optionale-beschreibung>",
  "tries": [
    {"subagent": "<name>", "status": "<status>", "ts": "<iso8601>"}
  ]
}
```

### Status-Mapping

| Subagent-Status | Master-Status (Logik) |
|---|---|
| `success` | `success` |
| `metadata_only` (alle OA + kein lizenzierter Verlags-Subagent) | `no_match` |
| `metadata_only` (OA) + `auth_required` / `auth_failed` (Verlag) | `pickup_required` |
| `pickup_required` (generic-fetcher) | `pickup_required` |
| `captcha` (irgendein Subagent) | `captcha` |
| alle `no_match` | `no_match` |

### `pickup_required`-Hinweis

Bei `pickup_required` enthält der Output zusätzlich:
```json
{
  "pickup_hint": {
    "bib_pickup_url": "<aus active.yaml>",
    "identifier": "<isbn/doi/titel>",
    "identifier_type": "<isbn|doi|title|url>"
  }
}
```

---

## Tests (`tests/test_book_fetcher.py`)

### Test 1: ISBN → doabooks-fetcher zuerst aufgerufen

Input: `"isbn: 978-3-16-148410-0"`
Mock: `doabooks-fetcher` gibt `success` zurück.
Assert: `tries[0].subagent == "doabooks-fetcher"`, `status == "success"`.

### Test 2: OA alle `metadata_only` + Springer lizenziert → springer-book folgt

Input: `"isbn: 978-3-662-54347-6"`, Profil mit `licensed_sites: ["link.springer.com"]`
Mock: alle OA-Subagenten → `metadata_only`, `springer-book` → `success`.
Assert: OA-Reihenfolge in `tries`, dann `springer-book` in `tries`, `status == "success"`.

### Test 3: auth_required → auth-helper → Retry

Input: ISBN, Profil mit Springer lizenziert.
Mock: alle OA → `metadata_only`, `springer-book` → `auth_required`, `auth-helper` → `authenticated`, `springer-book` (Retry) → `success`.
Assert: `tries` enthält `auth-helper`, dann `springer-book` (zweites Mal), `status == "success"`.

### Test 4: Captcha propagiert

Mock: `doabooks-fetcher` → `captcha`.
Assert: Master gibt `status == "captcha"` zurück.

### Test 5: Alle scheitern → generic-fetcher → pickup_required

Mock: alle OA → `no_match`, keine lizenzierten Verlags-Sites, `generic-fetcher` → `pickup_required`.
Assert: `status == "pickup_required"`, `pickup_hint` vorhanden.

---

## Datei-Grenzen

| Datei | Neu/Modify |
|---|---|
| `agents/book-fetcher.md` | NEU |
| `tests/test_book_fetcher.py` | NEU |
| `tests/fixtures/book_fetcher_mocks/` | NEU |
| `specs/v6.2/G.md` | DIESE DATEI |
| `specs/v6.2/G-plan.md` | FOLGT |

---

## Out of Scope

- Implementierung der Subagenten selbst (C/D/E/F bereits erledigt)
- `/academic-research:fetch` Slash-Command (Chunk H)
- Per-Uni-Profil-Templates (Chunk B)
- Parallele Subagenten-Ausführung (explizit ausgeschlossen)
