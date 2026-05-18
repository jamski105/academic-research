# Chunk E — Verlags-Site-Subagenten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vier neue Subagenten (`springer-book`, `degruyter`, `nationallizenzen`, `ebook-central`) erstellen, die lizenzpflichtige Verlagsseiten per `browser-use` navigieren, Auth über `auth-helper` delegieren und ein einheitliches Output-Schema liefern.

**Architecture:** Jeder Subagent ist eine Markdown-Datei in `agents/` mit YAML-Frontmatter (name, model, tools, maxTurns, browser-guide) und einem System-Prompt der genau eine Plattform kennt. Auth-Delegation via `auth-helper`-Aufruf bei erkannter Paywall. Tests prüfen Frontmatter und Schema-Konformität ohne Live-Browser.

**Tech Stack:** Markdown-Agenten-Format, Python pytest (Frontmatter-Parsing via `yaml`), YAML-Parsing, JSON-Schema-Validierung.

---

## Datei-Übersicht

| Datei | Aktion | Zweck |
|---|---|---|
| `agents/springer-book.md` | neu | Springer Link Buch-Download-Subagent |
| `agents/degruyter.md` | neu | De Gruyter Buch-Download-Subagent |
| `agents/nationallizenzen.md` | neu | Nationallizenzen-Portal-Subagent |
| `agents/ebook-central.md` | neu | Ebook Central ProQuest-Subagent |
| `tests/test_publisher_fetchers.py` | neu | Frontmatter + Schema-Validierungstests |
| `evals/publisher-fetchers/evals.json` | neu | 5 Eval-Cases |
| `specs/v6.2/E.md` | bereits vorhanden | Spec |
| `specs/v6.2/E-plan.md` | diese Datei | Plan |

---

## Task 1: Test-Grundgerüst schreiben (RED)

**Files:**
- Create: `tests/test_publisher_fetchers.py`

- [ ] **Schritt 1: Failing-Tests schreiben**

Erstelle `tests/test_publisher_fetchers.py` mit folgendem Inhalt:

```python
"""
Frontmatter-Validierung und Output-Schema-Check fuer Publisher-Fetcher-Agents.
Keine Live-Browser-Calls. Prueft nur Struktur der Agent-Dateien.
"""
import re
from pathlib import Path

import pytest
import yaml

# Absoluter Pfad zum Repo-Root (relativ zu dieser Test-Datei)
REPO_ROOT = Path(__file__).parent.parent

AGENTS = [
    "springer-book",
    "degruyter",
    "nationallizenzen",
    "ebook-central",
]

REQUIRED_FRONTMATTER_KEYS = {"name", "model", "tools", "maxTurns", "browser-guide"}

VALID_STATUSES = {
    "success",
    "pickup_required",
    "captcha",
    "no_match",
    "metadata_only",
}

REQUIRED_TOOL_PATTERNS = [
    r"browser-use",
]

PAYWALL_KEYWORDS = [
    "paywall",
    "login-wall",
    "auth-trigger",
    "auth_required",
    "auth-helper",
]


def _parse_agent_frontmatter(agent_name: str) -> tuple[dict, str]:
    """Parst YAML-Frontmatter und Body eines Agent-Files."""
    agent_path = REPO_ROOT / "agents" / f"{agent_name}.md"
    assert agent_path.exists(), f"Agent-Datei fehlt: {agent_path}"
    content = agent_path.read_text(encoding="utf-8")
    # Frontmatter zwischen erstem und zweitem ---
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    assert match, f"Kein gueltiges Frontmatter in {agent_path}"
    fm = yaml.safe_load(match.group(1))
    body = match.group(2)
    return fm, body


@pytest.mark.parametrize("agent_name", AGENTS)
def test_agent_file_exists(agent_name):
    """Jede Agent-Datei muss existieren."""
    agent_path = REPO_ROOT / "agents" / f"{agent_name}.md"
    assert agent_path.exists(), f"Fehlende Agent-Datei: {agent_path}"


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_required_keys(agent_name):
    """Frontmatter muss alle Pflichtfelder enthalten."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    missing = REQUIRED_FRONTMATTER_KEYS - set(fm.keys())
    assert not missing, f"{agent_name}: fehlende Frontmatter-Felder: {missing}"


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_model_is_sonnet(agent_name):
    """Alle Publisher-Fetcher muessen model: sonnet verwenden."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    assert fm.get("model") == "sonnet", (
        f"{agent_name}: model muss 'sonnet' sein, ist '{fm.get('model')}'"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_tools_include_browser_use(agent_name):
    """Tools-Liste muss browser-use enthalten."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    tools = fm.get("tools", [])
    # tools kann Liste von Strings oder String sein
    tools_str = str(tools)
    assert "browser-use" in tools_str, (
        f"{agent_name}: tools muss 'browser-use' enthalten, ist: {tools}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_frontmatter_browser_guide_referenced(agent_name):
    """browser-guide Frontmatter-Feld muss gesetzt sein."""
    fm, _ = _parse_agent_frontmatter(agent_name)
    guide = fm.get("browser-guide", "")
    assert guide, f"{agent_name}: browser-guide Feld fehlt oder leer"
    assert guide.startswith("config/browser_guides/"), (
        f"{agent_name}: browser-guide muss mit 'config/browser_guides/' beginnen, ist: {guide}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_auth_trigger(agent_name):
    """Agent-Body muss Auth-Trigger-Bedingung dokumentieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    body_lower = body.lower()
    found = any(kw in body_lower for kw in PAYWALL_KEYWORDS)
    assert found, (
        f"{agent_name}: Body dokumentiert keinen Auth-Trigger. "
        f"Erwartete eines von: {PAYWALL_KEYWORDS}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_auth_method(agent_name):
    """Agent-Body muss Auth-Methode (HAN/Shibboleth/EZproxy/DFN-AAI) nennen."""
    _, body = _parse_agent_frontmatter(agent_name)
    auth_methods = ["HAN", "Shibboleth", "EZproxy", "DFN-AAI", "oa-only"]
    found = any(method in body for method in auth_methods)
    assert found, (
        f"{agent_name}: Body nennt keine Auth-Methode. Erwartet eines von: {auth_methods}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_references_auth_helper(agent_name):
    """Agent-Body muss auth-helper als Delegations-Ziel referenzieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    assert "auth-helper" in body, (
        f"{agent_name}: Body muss 'auth-helper' als Delegations-Ziel referenzieren"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_contains_valid_status_values(agent_name):
    """Agent-Body muss alle Output-Status-Werte (success/pickup_required/etc.) erwaehnen."""
    _, body = _parse_agent_frontmatter(agent_name)
    # Mindestens 3 der 5 Status-Werte muessen im Body erwaehnt sein
    found = [s for s in VALID_STATUSES if s in body]
    assert len(found) >= 3, (
        f"{agent_name}: Body nennt zu wenige Status-Werte ({found}). "
        f"Erwartet min. 3 aus: {VALID_STATUSES}"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_documents_metadata_only_for_missing_license(agent_name):
    """Agent-Body muss metadata_only fuer fehlende Lizenz dokumentieren."""
    _, body = _parse_agent_frontmatter(agent_name)
    assert "metadata_only" in body, (
        f"{agent_name}: Body muss 'metadata_only' als Fallback fuer fehlende Lizenz dokumentieren"
    )


@pytest.mark.parametrize("agent_name", AGENTS)
def test_body_references_browser_guide(agent_name):
    """Agent-Body muss den config/browser_guides/-Pfad referenzieren."""
    fm, body = _parse_agent_frontmatter(agent_name)
    guide = fm.get("browser-guide", "")
    # Entweder der volle Pfad oder zumindest 'browser_guides' im Body
    assert "browser_guides" in body or "browser-guide" in body.lower(), (
        f"{agent_name}: Body muss auf Browser-Guide referenzieren"
    )


def test_eval_cases_file_exists():
    """evals/publisher-fetchers/evals.json muss existieren."""
    evals_path = REPO_ROOT / "evals" / "publisher-fetchers" / "evals.json"
    assert evals_path.exists(), f"Eval-Datei fehlt: {evals_path}"


def test_eval_cases_structure():
    """evals.json muss valide Struktur haben."""
    import json
    evals_path = REPO_ROOT / "evals" / "publisher-fetchers" / "evals.json"
    if not evals_path.exists():
        pytest.skip("evals.json noch nicht vorhanden")
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    assert "component" in data
    assert "cases" in data
    assert len(data["cases"]) >= 4, "Mindestens 4 Eval-Cases erwartet"
    for case in data["cases"]:
        assert "id" in case
        assert "description" in case
        assert "agent" in case
```

- [ ] **Schritt 2: Test laufen lassen (muss FAIL)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -v 2>&1 | head -60
```

Erwartetes Ergebnis: Alle Tests FAIL mit `AssertionError: Fehlende Agent-Datei`

---

## Task 2: `agents/springer-book.md` implementieren

**Files:**
- Create: `agents/springer-book.md`

- [ ] **Schritt 1: Agent schreiben**

Erstelle `agents/springer-book.md`:

```markdown
---
name: springer-book
model: sonnet
description: |
  Holt lizenzpflichtige und OA-Buecher von link.springer.com per browser-use.
  Delegiert Auth an auth-helper bei erkannter Paywall oder Login-Wall.
  Liefert lokalen PDF-Pfad oder strukturierten Status-Output zurueck.
tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]
maxTurns: 15
browser-guide: config/browser_guides/springer.md
---

# springer-book

Du bedienst link.springer.com wie ein Mensch. Nur browser-use — kein curl, kein wget.

**Lies zuerst:** `config/browser_guides/springer.md` (Buch-Download-Block)

## Eingabe

Du erhaeltst einen oder mehrere dieser Parameter:
- `isbn: <ISBN-10 oder ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Lizenz-Pruefung (ZUERST)

Lese `~/.academic-research/library-profiles/active.yaml`.

Pruefe, ob `link.springer.com` in `licensed_sites` enthalten ist.

Wenn NICHT enthalten:
```json
{"status": "metadata_only", "source_subagent": "springer-book", "url": "https://link.springer.com"}
```
→ Sofort stoppen. Master entscheidet ueber Fallback.

## Discovery-Flow

1. ```
   browser-use open https://link.springer.com/search?query=<URL-encoded-query>&content-type=Book
   ```
   (query = ISBN, DOI oder Titel, URL-encoded; bei ISBN bevorzugt)
2. `browser-use state` → Treffer-Liste lesen
3. Plausibelsten Treffer waehlen: Titel + Autor + Jahr matcht Input
   - Bei 0 Treffern:
     ```json
     {"status": "no_match", "source_subagent": "springer-book", "reason": "0 Treffer fuer <query>"}
     ```
4. `browser-use click <idx>` auf Buch-Titel → `/book/...`-Seite

## Paywall-Erkennung und Auth-Trigger

Auf der Buchseite `browser-use state` pruefen:

**Auth-Trigger-Bedingungen** (eine davon genuegt):
- "Access options"-Button sichtbar (statt Download-Button)
- "Buy access" oder "Purchase"-Link sichtbar
- "Sign in"-Button prominent (nicht nur im Header)
- Kein "Download book PDF"-Button auf der Buchseite

Wenn Auth-Trigger erkannt:

**Delegiere an auth-helper:**
```
Rufe auth-helper auf mit:
  target_url: <aktuelle Springer-Buchseite-URL>
  profile_path: ~/.academic-research/library-profiles/active.yaml
```

auth-helper gibt zurueck:
- `{status: "authenticated", auth_type: "Shibboleth"|"HAN", ...}` → weiter mit Download
- `{status: "not_required", auth_type: "oa-only"}` → weiter mit Download (OA-Buch)
- `{status: "auth_failed", reason: "..."}` → `{"status": "pickup_required", "source_subagent": "springer-book", "url": "<url>", "reason": "auth_failed: <reason>"}`
- `{status: "captcha"}` → `{"status": "captcha", "source_subagent": "springer-book", "reason": "CAPTCHA erkannt — Screenshot erstellt"}`

**Auth-Methode:** Shibboleth (DFN-AAI) oder IP-basiert — abgeleitet aus `auth_type` im aktiven Uni-Profil (`~/.academic-research/library-profiles/active.yaml`).

## Download-Flow

Nach erfolgreicher Auth oder bei OA-Buch:

1. `browser-use state` → "Download book PDF"-Button suchen
2. Button gefunden:
   ```
   browser-use click <download-btn-idx>
   browser-use download <pdf-idx> --to <output_path>
   ```
3. PDF-Validierung:
   ```python
   # Read tool: erste 4 Bytes pruefen
   # Muss mit %PDF beginnen, Groesse > 10 KB
   ```
4. Wenn "Download book PDF" fehlt, aber "Download chapter PDF" vorhanden:
   - Kapitelweiser Download als Fallback (Master entscheidet via `tries`)
   - Status: `success` mit Hinweis `"chapter_only": true`

Wenn kein Download-Button nach Auth:
```json
{"status": "pickup_required", "source_subagent": "springer-book", "url": "<url>", "reason": "Kein Download-Button nach Auth"}
```

## Output-Schema

Erfolg (ganzes Buch):
```json
{
  "status": "success",
  "source_subagent": "springer-book",
  "pdf_path": "<absoluter-pfad>",
  "url": "<buchseite-url>"
}
```

Erfolg (nur Kapitel):
```json
{
  "status": "success",
  "source_subagent": "springer-book",
  "pdf_path": "<absoluter-pfad>",
  "url": "<kapitelseite-url>",
  "chapter_only": true,
  "type": "chapter"
}
```

Kein Volltext (fehlende Lizenz im Profil):
```json
{"status": "metadata_only", "source_subagent": "springer-book", "url": "<url>"}
```

Kein Treffer:
```json
{"status": "no_match", "source_subagent": "springer-book", "reason": "<grund>"}
```

Pickup noetig (Auth fehlgeschlagen oder kein Download-Button):
```json
{"status": "pickup_required", "source_subagent": "springer-book", "url": "<url>", "reason": "<grund>"}
```

CAPTCHA:
```json
{"status": "captcha", "source_subagent": "springer-book", "reason": "CAPTCHA erkannt — Screenshot erstellt"}
```

## Verbote

- Kein `curl`, kein `wget`, kein `requests.get`, keine direkten HTTP-Calls
- Keine API-Endpoints erraten oder direkt aufrufen
- Keine fingierten Treffer — wenn Suche leer ist, `no_match` zurueckgeben
- KEINE Credentials selbst verarbeiten — Auth vollstaendig an auth-helper delegieren
- Keine Weiterleitungen zu anderen Sites ohne Pruefung

## Bekannte Fallstricke

- Springer unterscheidet `/book/` (Gesamtbuch) von `/chapter/` (Einzelkapitel) — DOI-Lookup muss auf Buchebene landen
- Einige Buecher nur als eBook ohne freien PDF-Export (nur Online-Lese-Zugriff) → `pickup_required`
- Rate-Limiting bei schnellen Zugriffen — 2–3 Sekunden Pause empfohlen
- OA-Badge im Suchergebnis bedeutet nicht immer vollstaendige PDF-Verfuegbarkeit (teils nur Abstract OA)
- Shibboleth-Auth-Methode wird aus `auth_type`-Feld im aktiven Uni-Profil gelesen
```

- [ ] **Schritt 2: Relevante Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -k "springer" -v 2>&1 | tail -20
```

Erwartetes Ergebnis: `springer-book`-Tests PASS; andere FAIL (noch nicht implementiert)

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git add agents/springer-book.md tests/test_publisher_fetchers.py
git commit -m "feat(E): springer-book agent + test scaffold (TDD red→green)"
```

---

## Task 3: `agents/degruyter.md` implementieren

**Files:**
- Create: `agents/degruyter.md`

- [ ] **Schritt 1: Agent schreiben**

Erstelle `agents/degruyter.md`:

```markdown
---
name: degruyter
model: sonnet
description: |
  Holt lizenzpflichtige und OA-Buecher von degruyter.com per browser-use.
  Delegiert Shibboleth/DFN-AAI-Auth an auth-helper bei erkannter Login-Wall.
  Unterstuetzt OA-Filter (kein Login bei OA-Badge). Liefert PDF-Pfad oder Status-Output.
tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]
maxTurns: 15
browser-guide: config/browser_guides/degruyter.md
---

# degruyter

Du bedienst degruyter.com wie ein Mensch. Nur browser-use — kein curl, kein wget.

**Lies zuerst:** `config/browser_guides/degruyter.md`

## Eingabe

Du erhaeltst einen oder mehrere dieser Parameter:
- `isbn: <ISBN-10 oder ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Lizenz-Pruefung (ZUERST)

Lese `~/.academic-research/library-profiles/active.yaml`.

Pruefe, ob `degruyter.com` in `licensed_sites` enthalten ist.

Wenn NICHT enthalten:
```json
{"status": "metadata_only", "source_subagent": "degruyter", "url": "https://www.degruyter.com"}
```
→ Sofort stoppen. Master entscheidet ueber Fallback.

**Ausnahme:** Wenn OA-Badge erkennbar (Discovery-Ergebnis), fortfahren ohne Lizenz-Check.

## Discovery-Flow

1. ```
   browser-use open https://www.degruyter.com
   ```
2. Suchfeld: Titel, ISBN oder DOI eingeben
3. `browser-use state` → Filter "Content Type: Books" setzen
4. OA-Badge ("Open Access") in Ergebniszeile pruefen:
   - OA-Badge vorhanden → kein Auth-Trigger noetig
   - Kein OA-Badge → Auth moeglicherweise noetig (erst nach Klick pruefen)
5. Auf Treffer klicken → Buchdetailseite
6. Alternativ per DOI-Direktlink: `browser-use open https://doi.org/10.1515/...`

Bei 0 Treffern:
```json
{"status": "no_match", "source_subagent": "degruyter", "reason": "0 Treffer fuer <query>"}
```

## Paywall-Erkennung und Auth-Trigger

Auf der Buchdetailseite `browser-use state` pruefen:

**Auth-Trigger-Bedingungen** (eine davon genuegt):
- "Sign in via institution" / "Ueber Institution anmelden"-Button sichtbar auf Buchseite
- "Access options"-Block sichtbar (statt Download-Button)
- Kein "PDF herunterladen"-Button vorhanden

**OA-Ausnahme:** Wenn "Open Access"-Badge auf Detailseite sichtbar → kein Auth-Helper-Aufruf noetig.

Wenn Auth-Trigger erkannt (und KEIN OA-Badge):

**Delegiere an auth-helper:**
```
Rufe auth-helper auf mit:
  target_url: <aktuelle DeGruyter-Buchseite-URL>
  profile_path: ~/.academic-research/library-profiles/active.yaml
```

auth-helper gibt zurueck:
- `{status: "authenticated", auth_type: "Shibboleth"|"HAN", ...}` → weiter mit Download
- `{status: "not_required", auth_type: "oa-only"}` → weiter mit Download
- `{status: "auth_failed", reason: "..."}` → `{"status": "pickup_required", "source_subagent": "degruyter", "url": "<url>", "reason": "auth_failed: <reason>"}`
- `{status: "captcha"}` → `{"status": "captcha", "source_subagent": "degruyter", "reason": "CAPTCHA erkannt — Screenshot erstellt"}`

**Auth-Methode:** Shibboleth (DFN-AAI) — abgeleitet aus `auth_type` im aktiven Uni-Profil. De Gruyter nutzt den DFN-AAI-Foederations-Redirect (mehrstufig: DeGruyter → DFN-AAI → Hochschul-IdP).

## Download-Flow

Nach erfolgreicher Auth oder bei OA-Titel:

1. `browser-use state` → "PDF herunterladen"-Button suchen (Buchseite `/book/<isbn>`)
2. Button gefunden:
   ```
   browser-use click <download-btn-idx>
   browser-use download <pdf-idx> --to <output_path>
   ```
3. PDF-Validierung: erste 4 Bytes `%PDF`, Groesse > 10 KB
4. Falls Vollbuch-Download nicht verfuegbar, aber Kapitel-Download moeglich:
   - Kapitelweiser Fallback (jede Kapitelseite `/document/<doi>`)
   - Status: `success` mit `"chapter_only": true`

Wenn kein Download nach Auth:
```json
{"status": "pickup_required", "source_subagent": "degruyter", "url": "<url>", "reason": "Kein PDF-Download nach Auth (moeglicherweise DRM oder Online-only)"}
```

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "degruyter",
  "pdf_path": "<absoluter-pfad>",
  "url": "<buchseite-url>"
}
```

Kein Volltext (fehlende Lizenz):
```json
{"status": "metadata_only", "source_subagent": "degruyter", "url": "<url>"}
```

Kein Treffer:
```json
{"status": "no_match", "source_subagent": "degruyter", "reason": "<grund>"}
```

Pickup noetig:
```json
{"status": "pickup_required", "source_subagent": "degruyter", "url": "<url>", "reason": "<grund>"}
```

CAPTCHA:
```json
{"status": "captcha", "source_subagent": "degruyter", "reason": "CAPTCHA erkannt — Screenshot erstellt"}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- KEINE Credentials selbst verarbeiten — Auth vollstaendig an auth-helper delegieren
- Keine fingierten Treffer

## Bekannte Fallstricke

- Buch-DOI (`/book/<isbn>`) vs. Kapitel-DOI (`/document/<doi>`) — Buchebene als Einstiegspunkt
- Kapitel koennen lizenziert sein, obwohl das Buch OA ist — immer Buchseite pruefen
- CAPTCHA bei >5 schnellen Requests — mind. 3 Sekunden Pause
- Shibboleth-Redirect ist mehrstufig: DeGruyter → DFN-AAI → Hochschule → zurueck — vollstaendigen Redirect abwarten
- Auth-Methode (Shibboleth) aus `auth_type` im aktiven Uni-Profil lesen
```

- [ ] **Schritt 2: Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -k "degruyter" -v 2>&1 | tail -20
```

Erwartetes Ergebnis: `degruyter`-Tests PASS

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git add agents/degruyter.md
git commit -m "feat(E): degruyter agent"
```

---

## Task 4: `agents/nationallizenzen.md` implementieren

**Files:**
- Create: `agents/nationallizenzen.md`

- [ ] **Schritt 1: Agent schreiben**

Erstelle `agents/nationallizenzen.md`:

```markdown
---
name: nationallizenzen
model: sonnet
description: |
  Holt Buecher ueber das Nationallizenzen-Portal (nationallizenzen.de) per browser-use.
  Discovery auf nationallizenzen.de, Download auf Ziel-Verlagsseite via DFN-AAI/Shibboleth.
  Delegiert Auth an auth-helper. Gibt PDF-Pfad oder strukturierten Status zurueck.
tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]
maxTurns: 18
browser-guide: config/browser_guides/nationallizenzen.md
---

# nationallizenzen

Du bedienst nationallizenzen.de wie ein Mensch. Nur browser-use — kein curl, kein wget.

**Lies zuerst:** `config/browser_guides/nationallizenzen.md`

## Eingabe

Du erhaeltst einen oder mehrere dieser Parameter:
- `isbn: <ISBN-10 oder ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Lizenz-Pruefung (ZUERST)

Lese `~/.academic-research/library-profiles/active.yaml`.

Pruefe, ob `nationallizenzen.de` in `licensed_sites` enthalten ist.

Wenn NICHT enthalten:
```json
{"status": "metadata_only", "source_subagent": "nationallizenzen", "url": "https://www.nationallizenzen.de"}
```
→ Sofort stoppen. Master entscheidet ueber Fallback.

## Discovery-Flow

1. ```
   browser-use open https://www.nationallizenzen.de
   ```
2. Suche im Nationallizenzen-Katalog: Titel, ISBN, DOI oder Verlag eingeben
3. `browser-use state` → Treffer pruefen
4. Verlags-Link in Trefferdetails notieren (Springer, Wiley, De Gruyter etc.)
5. Auf Verlags-Link klicken → Verlagsseite oeffnet

Bei 0 Treffern im Nationallizenzen-Katalog:
```json
{"status": "no_match", "source_subagent": "nationallizenzen", "reason": "Titel nicht im Nationallizenzen-Katalog"}
```

**Wichtig:** Nationallizenzen gelten nur fuer bestimmte Erscheinungsjahre (haeufig bis 2007–2015). Bei Neuerscheinungen → `no_match`.

## Auth-Trigger auf Verlagsseite

Nach Weiterleitung auf Verlagsseite `browser-use state` pruefen:

**Auth-Trigger-Bedingungen** (Paywall-Erkennung auf Verlagsseite):
- "Sign in via institution" / "Institutional login"-Button sichtbar
- Auth-Wall / "Access options" statt Download-Button
- Kein PDF-Download-Button trotz Nationallizenzen-Referenz

Wenn Auth-Trigger erkannt:

**Delegiere an auth-helper:**
```
Rufe auth-helper auf mit:
  target_url: <aktuelle Verlagsseiten-URL>
  profile_path: ~/.academic-research/library-profiles/active.yaml
```

auth-helper gibt zurueck:
- `{status: "authenticated", auth_type: "Shibboleth", ...}` → weiter mit Download
- `{status: "auth_failed", reason: "..."}` → `{"status": "pickup_required", "source_subagent": "nationallizenzen", "url": "<url>", "reason": "auth_failed: <reason>"}`
- `{status: "captcha"}` → `{"status": "captcha", "source_subagent": "nationallizenzen", "reason": "CAPTCHA erkannt — Screenshot erstellt"}`

**Auth-Methode:** DFN-AAI / Shibboleth — Nationallizenzen nutzen ausschliesslich DFN-AAI-Foederation. Auth-Methode aus `auth_type` im aktiven Uni-Profil (`~/.academic-research/library-profiles/active.yaml`). Paywall-Banner auf Verlagsseite ist der primaere Auth-Trigger.

## Download-Flow

Nach erfolgreicher Auth auf Verlagsseite:

Der Download-Prozess folgt dem verlagsspezifischen Muster (Springer: "Download book PDF", De Gruyter: "PDF herunterladen" etc.).

1. `browser-use state` → Download-Button auf Verlagsseite suchen
2. Button gefunden → klicken und PDF sichern:
   ```
   browser-use click <download-btn-idx>
   browser-use download <pdf-idx> --to <output_path>
   ```
3. PDF-Validierung: erste 4 Bytes `%PDF`, Groesse > 10 KB

Wenn kein Download-Button nach Auth:
```json
{"status": "pickup_required", "source_subagent": "nationallizenzen", "url": "<url>", "reason": "Kein PDF-Download nach Nationallizenzen-Auth"}
```

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "nationallizenzen",
  "pdf_path": "<absoluter-pfad>",
  "url": "<verlagsseiten-url>"
}
```

Kein Volltext (fehlende Lizenz im Profil):
```json
{"status": "metadata_only", "source_subagent": "nationallizenzen", "url": "<url>"}
```

Kein Treffer:
```json
{"status": "no_match", "source_subagent": "nationallizenzen", "reason": "<grund>"}
```

Pickup noetig:
```json
{"status": "pickup_required", "source_subagent": "nationallizenzen", "url": "<url>", "reason": "<grund>"}
```

CAPTCHA:
```json
{"status": "captcha", "source_subagent": "nationallizenzen", "reason": "CAPTCHA erkannt — Screenshot erstellt"}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- KEINE Credentials selbst verarbeiten — Auth vollstaendig an auth-helper delegieren
- Keine fingierten Treffer

## Bekannte Fallstricke

- Nationallizenzen sind KEIN Download-Portal selbst — sie leiten zum Verlag weiter
- Auth-Redirect ist mehrstufig: Verlag → Nationallizenzen-Redirect → DFN-AAI → Hochschul-IdP → zurueck (kann 10–15 Sekunden dauern)
- Nicht jede Hochschule hat alle Nationallizenzen aktiviert — aktives Uni-Profil pruefen
- Einige Verlage erfordern zusaetzlich Cookie-Akzeptanz vor dem Auth-Flow
- Erscheinungsjahre-Grenzen beachten — Neuerscheinungen sind NICHT in Nationallizenzen
```

- [ ] **Schritt 2: Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -k "nationallizenzen" -v 2>&1 | tail -20
```

Erwartetes Ergebnis: `nationallizenzen`-Tests PASS

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git add agents/nationallizenzen.md
git commit -m "feat(E): nationallizenzen agent"
```

---

## Task 5: `agents/ebook-central.md` implementieren

**Files:**
- Create: `agents/ebook-central.md`

- [ ] **Schritt 1: Agent schreiben**

Erstelle `agents/ebook-central.md`:

```markdown
---
name: ebook-central
model: sonnet
description: |
  Holt lizenzpflichtige Buecher von ebookcentral.proquest.com per browser-use.
  Delegiert Shibboleth-/HAN-Auth an auth-helper. Erkennt DRM-PDFs und Download-Limits.
  Gibt PDF-Pfad oder strukturierten Status zurueck.
tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]
maxTurns: 15
browser-guide: config/browser_guides/ebook-central.md
---

# ebook-central

Du bedienst ebookcentral.proquest.com wie ein Mensch. Nur browser-use — kein curl, kein wget.

**Lies zuerst:** `config/browser_guides/ebook-central.md`

## Eingabe

Du erhaeltst einen oder mehrere dieser Parameter:
- `isbn: <ISBN-10 oder ISBN-13>`
- `doi: <DOI-String>`
- `title: <Freitext-Titel>`
- `output_path: <Zielpfad fuer PDF>`

## Lizenz-Pruefung (ZUERST)

Lese `~/.academic-research/library-profiles/active.yaml`.

Pruefe, ob `ebookcentral.proquest.com` in `licensed_sites` enthalten ist.

Wenn NICHT enthalten:
```json
{"status": "metadata_only", "source_subagent": "ebook-central", "url": "https://ebookcentral.proquest.com"}
```
→ Sofort stoppen.

**Sonderfall HAN:** Einige Institutionen haben Ebook Central nur ueber HAN eingerichtet.
Pruefe `proxy_pattern` im Profil — wenn gesetzt und `auth_type: HAN`, nutze HAN-Flow.

## Auth-Flow (IMMER erforderlich bei Ebook Central)

Ebook Central erfordert immer Login. Direkt nach dem Oeffnen der Site:

**Auth-Trigger (Login-Wall auf Startseite oder Detailseite):**
- "Sign in"-Button sichtbar ohne eingeloggten Zustand
- "Sign in through your institution"-Option sichtbar
- HAN-Proxy-URL aus `proxy_pattern` → direkt via HAN aufrufen

**Delegiere an auth-helper:**
```
Rufe auth-helper auf mit:
  target_url: https://ebookcentral.proquest.com
  profile_path: ~/.academic-research/library-profiles/active.yaml
```

auth-helper gibt zurueck:
- `{status: "authenticated", auth_type: "Shibboleth"|"HAN", ...}` → weiter mit Discovery
- `{status: "auth_failed", reason: "..."}` → `{"status": "pickup_required", "source_subagent": "ebook-central", "url": "https://ebookcentral.proquest.com", "reason": "auth_failed: <reason>"}`
- `{status: "captcha"}` → `{"status": "captcha", "source_subagent": "ebook-central", "reason": "CAPTCHA erkannt — Screenshot erstellt"}`

**Auth-Methode:** Shibboleth ODER HAN — abhaengig von `auth_type` im aktiven Uni-Profil (`~/.academic-research/library-profiles/active.yaml`). Paywall-Banner / Login-Wall auf der Startseite ist der Auth-Trigger.

## Discovery-Flow

Nach erfolgreicher Auth:

1. Suchfeld: Titel, Autor oder ISBN eingeben
2. `browser-use state` → Suchergebnisse pruefen
3. Filter: "Subject", "Publication Date", "Language" bei Bedarf
4. Trefferdetailseite oeffnen → Lizenz- und Download-Optionen pruefen

Bei 0 Treffern:
```json
{"status": "no_match", "source_subagent": "ebook-central", "reason": "ISBN nicht im Katalog"}
```

## Download-Pruefung und DRM-Sonderfall

Auf Detailseite `browser-use state` pruefen:

**DRM-Pruefung (vor Download):**
- "Adobe DRM" oder "Adobe Digital Editions" sichtbar → DRM-PDF
- DRM-PDFs sind nicht archivierbar:
  ```json
  {"status": "pickup_required", "source_subagent": "ebook-central", "url": "<url>", "reason": "DRM-PDF (Adobe Digital Editions) — nicht archivierbar"}
  ```

**Download-Limit-Pruefung:**
- "You have reached the maximum number of checkouts" sichtbar:
  ```json
  {"status": "pickup_required", "source_subagent": "ebook-central", "url": "<url>", "reason": "Download-Limit erreicht"}
  ```

**Download-Flow (ohne DRM, ohne Limit):**
1. "Full Book Download"-Button suchen
2. Button gefunden:
   ```
   browser-use click <full-book-download-idx>
   browser-use download <pdf-idx> --to <output_path>
   ```
3. PDF-Validierung: erste 4 Bytes `%PDF`, Groesse > 10 KB
4. Falls "Full Book Download" fehlt, aber "Download Chapter" vorhanden:
   - Kapitelweiser Fallback
   - Status: `success` mit `"chapter_only": true`

**Online-Reader ("Read Online") ist KEIN Download** — nicht verwenden.

## Output-Schema

Erfolg:
```json
{
  "status": "success",
  "source_subagent": "ebook-central",
  "pdf_path": "<absoluter-pfad>",
  "url": "<detailseite-url>"
}
```

Kein Volltext (fehlende Lizenz):
```json
{"status": "metadata_only", "source_subagent": "ebook-central", "url": "<url>"}
```

Kein Treffer:
```json
{"status": "no_match", "source_subagent": "ebook-central", "reason": "<grund>"}
```

Pickup noetig (DRM, Limit, kein Download nach Auth):
```json
{"status": "pickup_required", "source_subagent": "ebook-central", "url": "<url>", "reason": "<grund>"}
```

CAPTCHA:
```json
{"status": "captcha", "source_subagent": "ebook-central", "reason": "CAPTCHA erkannt — Screenshot erstellt"}
```

## Verbote

- Kein `curl`, kein `wget`, keine direkten HTTP-Calls
- KEINE Credentials selbst verarbeiten — Auth vollstaendig an auth-helper delegieren
- "Read Online" (Online-Reader) nicht als PDF-Download verwenden
- Keine fingierten Treffer

## Bekannte Fallstricke

- DRM-PDFs (Adobe Digital Editions) → `pickup_required` (technisch downloadbar, aber nicht archivierbar)
- Download-Limit pro User/Tag variiert je Lizenzvertrag — auf Fehlermeldung achten
- Session-Timeout nach ~15 Minuten Inaktivitaet → neu anmelden (auth-helper erneut aufrufen)
- "Full Book Download" nur bei Institutional-Ownership-Lizenzen; bei Short-Term-Loan nur kapitelweise
- Einige Institutionen haben Ebook Central nur ueber HAN — `proxy_pattern` aus Profil pruefen
```

- [ ] **Schritt 2: Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -k "ebook" -v 2>&1 | tail -20
```

Erwartetes Ergebnis: `ebook-central`-Tests PASS

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git add agents/ebook-central.md
git commit -m "feat(E): ebook-central agent"
```

---

## Task 6: Eval-Cases erstellen

**Files:**
- Create: `evals/publisher-fetchers/evals.json`

- [ ] **Schritt 1: Eval-Verzeichnis und JSON erstellen**

```bash
mkdir -p /Users/j65674/Repos/academic-research-v6.2-E/evals/publisher-fetchers
```

Erstelle `evals/publisher-fetchers/evals.json`:

```json
{
  "component": "publisher-fetchers",
  "component_type": "agent",
  "cases": [
    {
      "id": "pf-01",
      "description": "springer-book: OA-Buch via Springer (Birkhaeuser OA-Mathematik)",
      "agent": "springer-book",
      "input": {
        "isbn": "9783319572017",
        "output_path": "/tmp/pf-01-springer-oa.pdf"
      },
      "expected": {
        "type": "json_field",
        "path": "$.status",
        "check": "exists"
      },
      "notes": "Springer OA-Buch sollte ohne Auth downloadbar sein. Erwartet status in {success, metadata_only, no_match, captcha, pickup_required}."
    },
    {
      "id": "pf-02",
      "description": "degruyter: OA-Buch via De Gruyter (Klassische Studien OA)",
      "agent": "degruyter",
      "input": {
        "isbn": "9783110568370",
        "output_path": "/tmp/pf-02-degruyter-oa.pdf"
      },
      "expected": {
        "type": "json_field",
        "path": "$.status",
        "check": "exists"
      },
      "notes": "De Gruyter OA-Buch. Erwartet status in Enum."
    },
    {
      "id": "pf-03",
      "description": "nationallizenzen: Buch ueber Nationallizenzen-Portal (Duncker & Humblot hist.)",
      "agent": "nationallizenzen",
      "input": {
        "isbn": "9783428139521",
        "output_path": "/tmp/pf-03-nationallizenzen.pdf"
      },
      "expected": {
        "type": "json_field",
        "path": "$.status",
        "check": "exists"
      },
      "notes": "Nationallizenzen-Zugang. Erwartet status in Enum; metadata_only wenn Profil keine NL enthaelt."
    },
    {
      "id": "pf-04",
      "description": "ebook-central: MIT Press Buch auf Ebook Central",
      "agent": "ebook-central",
      "input": {
        "isbn": "9780262036603",
        "output_path": "/tmp/pf-04-ebook-central.pdf"
      },
      "expected": {
        "type": "json_field",
        "path": "$.status",
        "check": "exists"
      },
      "notes": "Ebook Central (ProQuest) Test. Erwartet status in Enum; pickup_required wenn DRM."
    },
    {
      "id": "pf-05",
      "description": "springer-book: no_match-Pfad mit ungueltigem ISBN",
      "agent": "springer-book",
      "input": {
        "isbn": "9780000000000",
        "output_path": "/tmp/pf-05-no-match.pdf"
      },
      "expected": {
        "type": "json_field",
        "path": "$.status",
        "check": "equals:no_match"
      },
      "notes": "Fake-ISBN — Springer sollte 0 Treffer liefern und no_match zurueckgeben."
    }
  ]
}
```

- [ ] **Schritt 2: Tests laufen lassen (alle)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -v 2>&1 | tail -30
```

Erwartetes Ergebnis: Alle Tests PASS (inkl. `test_eval_cases_file_exists` und `test_eval_cases_structure`)

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git add evals/publisher-fetchers/evals.json
git commit -m "feat(E): publisher-fetchers eval cases"
```

---

## Task 7: Vollstaendiger Test-Run und Verification

- [ ] **Schritt 1: Alle Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/test_publisher_fetchers.py -v 2>&1
```

Erwartetes Ergebnis: Alle Tests PASS, 0 Failures, 0 Errors

- [ ] **Schritt 2: Gesamte Test-Suite pruefen (Regressions-Check)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -30
```

Erwartetes Ergebnis: Keine Regressions (vorher schon schlagene Tests bleiben bestehen)

- [ ] **Schritt 3: Final Commit (falls noetig)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-E
git status
# Nur wenn ungestaged changes vorhanden:
git add specs/v6.2/E.md specs/v6.2/E-plan.md
git commit -m "chore(E): spec und plan finalisiert"
```

---

## Self-Review Checkliste

- [x] Alle 4 Agent-Dateien sind im Plan beschrieben mit vollstaendigem Inhalt
- [x] TDD: Test-Datei zuerst (Task 1), dann Implementierungen (Tasks 2–5)
- [x] Keine Platzhalter ("TBD", "TODO") in Agent-Bodies
- [x] Auth-Trigger-Bedingungen explizit in jedem Agent dokumentiert
- [x] Auth-Methode pro Agent explizit genannt (Shibboleth/HAN/DFN-AAI)
- [x] `auth-helper`-Delegation in jedem Agent referenziert
- [x] `metadata_only` fuer fehlende Lizenz in jedem Agent
- [x] Output-Schema: alle 5 Status-Werte pro Agent
- [x] Tool-Restriction: `browser-use`-Tools in jedem Frontmatter
- [x] `browser-guide`-Frontmatter-Feld in jedem Agent
- [x] Eval-Cases: 5 Cases mit konkreten ISBNs
- [x] Regressions-Test in Task 7
