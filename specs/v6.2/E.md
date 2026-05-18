# Chunk E — Verlags-Site-Subagenten (Spec)

**Ticket:** #82 · F16 — Verlags-Site-Subagenten: springer-book, degruyter, nationallizenzen, ebook-central
**Branch:** `feat/v6.2-E-publisher-subagents`
**Depends on:** A (Browser-Guides), C (auth-helper)

---

## Ziel

Vier neue Subagenten unter `agents/` die lizenzpflichtige Verlagsseiten per
`browser-use` navigieren. Jeder Agent kennt genau eine Plattform, delegiert
Auth an `auth-helper` und gibt ein einheitliches Output-Schema zurück.

---

## Geltungsbereich

### Neue Dateien

| Datei | Funktion |
|---|---|
| `agents/springer-book.md` | Springer Link Buch-Download (link.springer.com) |
| `agents/degruyter.md` | De Gruyter Buch-Download (degruyter.com) |
| `agents/nationallizenzen.md` | Nationallizenzen-Portal + Ziel-Verlags-Auth (nationallizenzen.de) |
| `agents/ebook-central.md` | Ebook Central ProQuest (ebookcentral.proquest.com) |
| `tests/test_publisher_fetchers.py` | Frontmatter-Validierung + Output-Schema-Check |
| `evals/publisher-fetchers/evals.json` | 4–5 Eval-Cases (je 1 pro Agent) |

---

## Output-Schema (locked, identisch mit Chunk D)

Jeder Agent gibt genau eines dieser JSON-Objekte zurück:

```json
{"status": "success",           "source_subagent": "<name>", "pdf_path": "<abs-pfad>", "url": "<seiten-url>"}
{"status": "pickup_required",   "source_subagent": "<name>", "url": "<seiten-url>", "reason": "<grund>"}
{"status": "captcha",           "source_subagent": "<name>", "reason": "CAPTCHA erkannt — Screenshot erstellt"}
{"status": "no_match",          "source_subagent": "<name>", "reason": "<grund>"}
{"status": "metadata_only",     "source_subagent": "<name>", "url": "<seiten-url>"}
```

`metadata_only` → Lizenz nicht im aktiven Uni-Profil (`licensed_sites`); Master entscheidet.

CSL-Felder im Output (wenn Metadaten bekannt):
- `type: book | chapter`
- `page-first`, `page-last` (nur für Kapitel)
- `container-title` (Buchtitel bei Kapitel)
- `editor[]` (bei Sammelband)

---

## Auth-Trigger-Vertrag

Wenn ein Agent eine Paywall-/Login-Wall im `browser-use state` erkennt
(Paywall-Banner, "Access options"-Button, Login-Wall, "Sign in to download"),
delegiert er **sofort** an `auth-helper`:

```bash
# Aufruf-Pattern (analog für alle 4 Agents):
Agent springer-book ruft auth-helper auf mit:
  target_url: <aktuelle Seiten-URL>
  profile_path: ~/.academic-research/library-profiles/active.yaml

auth-helper gibt zurück:
  {status: "authenticated", auth_type: "Shibboleth", uni: "<uni>", session_context: "browser-use:active:<uni>"}
  ODER
  {status: "auth_failed", reason: "<grund>"}
  ODER
  {status: "captcha"}
  ODER
  {status: "not_required", auth_type: "oa-only"}
```

Nach `authenticated`: erneuter Versuch auf derselben Seite.
Nach `auth_failed` oder `captcha`: sofort stoppen, entsprechenden Status zurückgeben.

---

## Per-Agent-Spezifikation

### springer-book

- **Site:** `https://link.springer.com`
- **Browser-Guide:** `config/browser_guides/springer.md` (Buch-Download-Block, Chunk A)
- **Auth-Methode (aus Profil):** Shibboleth oder IP-basiert
- **Auth-Trigger:** `browser-use state` zeigt "Access options"-Button ODER fehlendes "Download book PDF"
- **Lizenz-Check:** `link.springer.com` in `licensed_sites`
- **Kein Profil-Eintrag:** → `status: metadata_only`

### degruyter

- **Site:** `https://www.degruyter.com`
- **Browser-Guide:** `config/browser_guides/degruyter.md` (Chunk A)
- **Auth-Methode:** Shibboleth/DFN-AAI (Institutionszugang) oder kein Login (OA)
- **Auth-Trigger:** Auth-Wall nach Discovery-Klick ODER "Sign in via institution" sichtbar auf Buchseite
- **OA-Filter:** OA-Badge im Suchergebnis erkennbar → kein Auth-Helper-Aufruf
- **Lizenz-Check:** `degruyter.com` in `licensed_sites`
- **Kein Profil-Eintrag:** → `status: metadata_only`

### nationallizenzen

- **Site:** `https://www.nationallizenzen.de` (Discovery) + Verlags-Redirect
- **Browser-Guide:** `config/browser_guides/nationallizenzen.md` (Chunk A)
- **Auth-Methode:** DFN-AAI / Shibboleth (Nationallizenzen-spezifisch)
- **Auth-Trigger:** Ziel-Verlagsseite zeigt Paywall nach Nationallizenzen-Redirect
- **Besonderheit:** Discovery auf nationallizenzen.de, Download auf Verlags-Plattform
- **Lizenz-Check:** `nationallizenzen.de` in `licensed_sites`
- **Kein Profil-Eintrag:** → `status: metadata_only`

### ebook-central

- **Site:** `https://ebookcentral.proquest.com`
- **Browser-Guide:** `config/browser_guides/ebook-central.md` (Chunk A)
- **Auth-Methode:** Shibboleth ODER HAN-Proxy (je nach Uni-Profil `auth_type`)
- **Auth-Trigger:** "Sign in through your institution" nach Ebook-Central-Öffnung
- **DRM-Sonderfall:** Adobe-DRM-PDFs → `status: pickup_required` (nicht archivierbar)
- **Download-Limit:** Wenn "maximum checkouts reached" → `status: pickup_required`
- **Lizenz-Check:** `ebookcentral.proquest.com` in `licensed_sites`
- **Kein Profil-Eintrag:** → `status: metadata_only`

---

## Frontmatter-Anforderungen (alle 4 Agents)

```yaml
---
name: <agent-name>
model: sonnet
description: |
  <einzeiliger Beschreibungstext>
tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]
maxTurns: 15
browser-guide: config/browser_guides/<guide-name>.md
---
```

Pflichtfelder: `name`, `model`, `tools`, `maxTurns`, `browser-guide`.

---

## Test-Strategie

`tests/test_publisher_fetchers.py` prüft **ohne Live-Browser**:

1. **Frontmatter-Validierung:** Alle 4 Agent-Dateien haben Pflichtfelder
2. **Output-Schema-Struktur:** Alle `status`-Werte sind im Enum definiert
3. **browser-guide-Referenz:** Referenzierter Guide existiert (via `feat/v6.2-A-browser-guides`)
4. **Auth-Trigger-Dokumentation:** Jede Agent-Datei enthält Paywall-Trigger-Beschreibung
5. **Tool-Restriction:** Jede Agent-Datei deklariert `browser-use`-Tools

Tests laufen auf `pytest` ohne Anthropic-API-Key (keine Live-Agenten-Calls).

---

## Eval-Cases (`evals/publisher-fetchers/evals.json`)

5 Cases, je ~1 pro Agent + 1 kombiniert:

| ID | Agent | Input | Erwartung |
|---|---|---|---|
| pf-01 | springer-book | ISBN `9783662441527` (Springer OA-Buch) | `status` in Enum |
| pf-02 | degruyter | ISBN `9783110711479` (De Gruyter OA) | `status` in Enum |
| pf-03 | nationallizenzen | ISBN `9783428139521` (Duncker & Humblot NL) | `status` in Enum |
| pf-04 | ebook-central | ISBN `9780262036603` (MIT Press on EBC) | `status` in Enum |
| pf-05 | springer-book | `no_match`-Pfad mit fake ISBN | `status: no_match` |

---

## Abhängigkeiten

- Chunk A (`feat/v6.2-A-browser-guides`): Guides unter `config/browser_guides/`
- Chunk C (`feat/v6.2-C-auth-helper`): `agents/auth-helper.md` als Aufruf-Referenz
- v6.1: CSL-Schema für `type: book | chapter`

---

## Out of Scope

- `book-fetcher` Master-Agent (Chunk G)
- `auth-helper`-Implementierung (Chunk C)
- Per-Uni-Profile (Chunk B)
- OA-Subagenten (Chunk D)
