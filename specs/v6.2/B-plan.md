# Per-Uni-Profile (Chunk B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** JSON-Schema-validierte YAML-Profile für 5 DACH-Hochschulen + Onboard-Hook der `active.yaml` schreibt + pytest-Suite mit Positiv- und Negativ-Fällen.

**Architecture:** `config/library-profiles/` enthält 5 YAML-Profile + `_schema.json`. Alle Profile werden via `jsonschema`-Bibliothek gegen das Schema validiert. Ein Shell-Skript `hooks/onboard-project-uni-prompt.sh` schreibt das ausgewählte Profil nach `~/.academic-research/library-profiles/active.yaml`. Tests in `tests/test_library_profiles.py` decken Validierung (positiv/negativ) und Hook-Verhalten ab.

**Tech Stack:** Python 3.x, `jsonschema` (PyPI), `PyYAML`, `pytest`, bash

---

## File Map

| Datei | Aktion | Zweck |
|---|---|---|
| `config/library-profiles/_schema.json` | Create | JSON-Schema Draft-07 für Profile |
| `config/library-profiles/tum.yaml` | Create | TU München — Shibboleth |
| `config/library-profiles/fu-berlin.yaml` | Create | FU Berlin — Shibboleth |
| `config/library-profiles/eth-zurich.yaml` | Create | ETH Zürich — SWITCHaai |
| `config/library-profiles/uni-wien.yaml` | Create | Uni Wien — ACOnet |
| `config/library-profiles/uni-hamburg.yaml` | Create | Uni Hamburg — DFN-AAI |
| `hooks/onboard-project-uni-prompt.sh` | Create | Profil-Auswahl → active.yaml |
| `tests/test_library_profiles.py` | Create | pytest-Suite |

---

### Task 1: JSON-Schema + Failing Tests schreiben (RED)

**Files:**
- Create: `tests/test_library_profiles.py`
- Create: `config/library-profiles/_schema.json` (leer/unvollständig — Tests müssen erst rot sein)

- [ ] **Schritt 1: Leeres Schema anlegen (damit Import nicht bricht)**

```json
{}
```

Datei: `config/library-profiles/_schema.json`

- [ ] **Schritt 2: Failing Tests schreiben**

Datei: `tests/test_library_profiles.py`

```python
"""Tests fuer Per-Uni-Profile (Chunk B, v6.2 F16.5)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Pfade relativ zum Repo-Root
REPO_ROOT = Path(__file__).parent.parent
PROFILES_DIR = REPO_ROOT / "config" / "library-profiles"
SCHEMA_PATH = PROFILES_DIR / "_schema.json"
PROFILE_SLUGS = ["tum", "fu-berlin", "eth-zurich", "uni-wien", "uni-hamburg"]
HOOK_PATH = REPO_ROOT / "hooks" / "onboard-project-uni-prompt.sh"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_profile(slug: str) -> dict:
    with open(PROFILES_DIR / f"{slug}.yaml") as f:
        return yaml.safe_load(f)


# ── Positiv-Tests ────────────────────────────────────────────────────────────

class TestProfilesValidPositiv:
    """Alle 5 Profile muessen gegen _schema.json valide sein."""

    def test_tum_valid(self):
        from jsonschema import validate
        validate(instance=load_profile("tum"), schema=load_schema())

    def test_fu_berlin_valid(self):
        from jsonschema import validate
        validate(instance=load_profile("fu-berlin"), schema=load_schema())

    def test_eth_zurich_valid(self):
        from jsonschema import validate
        validate(instance=load_profile("eth-zurich"), schema=load_schema())

    def test_uni_wien_valid(self):
        from jsonschema import validate
        validate(instance=load_profile("uni-wien"), schema=load_schema())

    def test_uni_hamburg_valid(self):
        from jsonschema import validate
        validate(instance=load_profile("uni-hamburg"), schema=load_schema())


# ── Negativ-Tests ────────────────────────────────────────────────────────────

class TestSchemaValidierungNegativ:
    """Schema muss bei fehlenden/falschen Pflichtfeldern ValidationError werfen."""

    def _base_profile(self) -> dict:
        """Minimales gueltiges Profil als Ausgangsbasis fuer Negativ-Tests."""
        return {
            "uni": "test-uni",
            "auth_type": "Shibboleth",
            "auth_url": "https://shibboleth.example.de",
            "licensed_sites": ["link.springer.com"],
            "bib_pickup_url": "https://opac.example.de",
        }

    def test_fehlendes_bib_pickup_url(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        del profile["bib_pickup_url"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_uni(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        del profile["uni"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_auth_type(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        del profile["auth_type"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_ungültiger_auth_type(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        profile["auth_type"] = "LDAP"  # nicht im Enum
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_leere_licensed_sites(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        profile["licensed_sites"] = []  # minItems: 1
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_auth_url(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        del profile["auth_url"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlende_licensed_sites(self):
        from jsonschema import ValidationError, validate
        profile = self._base_profile()
        del profile["licensed_sites"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())


# ── Onboard-Hook-Tests ───────────────────────────────────────────────────────

class TestOnboardHook:
    """Hook schreibt active.yaml korrekt."""

    def test_hook_file_exists(self):
        assert HOOK_PATH.exists(), f"Hook nicht gefunden: {HOOK_PATH}"

    def test_hook_ist_ausfuehrbar(self):
        assert os.access(HOOK_PATH, os.X_OK), f"Hook nicht ausfuehrbar: {HOOK_PATH}"

    def test_hook_schreibt_active_yaml(self, tmp_path):
        """--profile <slug> Flag schreibt active.yaml in tmp_path."""
        active_dir = tmp_path / "library-profiles"
        active_dir.mkdir()
        active_yaml = active_dir / "active.yaml"

        result = subprocess.run(
            ["bash", str(HOOK_PATH), "--profile", "tum", "--output-dir", str(active_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook Fehler: {result.stderr}"
        assert active_yaml.exists(), "active.yaml wurde nicht erstellt"

        with open(active_yaml) as f:
            content = yaml.safe_load(f)
        assert content["uni"] == "tum"
        assert content["auth_type"] == "Shibboleth"

    def test_hook_active_yaml_ist_valide(self, tmp_path):
        """Das von Hook geschriebene active.yaml validiert gegen Schema."""
        from jsonschema import validate
        active_dir = tmp_path / "library-profiles"
        active_dir.mkdir()

        subprocess.run(
            ["bash", str(HOOK_PATH), "--profile", "tum", "--output-dir", str(active_dir)],
            capture_output=True,
        )

        with open(active_dir / "active.yaml") as f:
            content = yaml.safe_load(f)
        validate(instance=content, schema=load_schema())
```

- [ ] **Schritt 3: Tests laufen lassen — müssen ROT sein**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/test_library_profiles.py -v 2>&1 | head -60
```

Erwartetes Ergebnis: Mehrere FAIL/ERROR — Schema leer, Profile fehlen noch.

- [ ] **Schritt 4: Commit (rote Tests + leeres Schema)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
git add tests/test_library_profiles.py config/library-profiles/_schema.json
git commit -m "test(B): failing tests fuer Per-Uni-Profile (TDD red)"
```

---

### Task 2: JSON-Schema implementieren (GREEN für Schema-Validierung)

**Files:**
- Modify: `config/library-profiles/_schema.json`

- [ ] **Schritt 1: Vollständiges JSON-Schema schreiben**

Datei: `config/library-profiles/_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LibraryProfile",
  "description": "Per-Uni-Profil fuer academic-research book-fetcher (F16.5)",
  "type": "object",
  "required": ["uni", "auth_type", "auth_url", "licensed_sites", "bib_pickup_url"],
  "additionalProperties": true,
  "properties": {
    "uni": {
      "type": "string",
      "description": "Maschinen-lesbarer Schluessel (slug-format, z.B. tum)"
    },
    "auth_type": {
      "type": "string",
      "enum": ["Shibboleth", "EZproxy", "HAN", "oa-only"],
      "description": "Auth-Mechanismus der Hochschule"
    },
    "auth_url": {
      "type": "string",
      "description": "URL des WAYF/IdP/HAN-Endpoints"
    },
    "licensed_sites": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "description": "Allowlist der lizenzierten Hosts fuer auth-helper"
    },
    "bib_pickup_url": {
      "type": "string",
      "description": "OPAC-URL fuer Abholung oder Fernleihe-Formular"
    },
    "proxy_pattern": {
      "type": "string",
      "description": "Proxy-URL-Muster (nur HAN/EZproxy, z.B. https://{site}.han.example.de)"
    },
    "credentials_keys": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Schluessel fuer OS-Keychain (nur HAN/EZproxy)"
    }
  }
}
```

- [ ] **Schritt 2: Negativ-Tests grün prüfen (Profile fehlen noch)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/test_library_profiles.py::TestSchemaValidierungNegativ -v
```

Erwartetes Ergebnis: Alle 7 Negativ-Tests PASS. Positiv-Tests noch FAIL (Profile fehlen).

---

### Task 3: 5 YAML-Profile erstellen (GREEN für Positiv-Tests)

**Files:**
- Create: `config/library-profiles/tum.yaml`
- Create: `config/library-profiles/fu-berlin.yaml`
- Create: `config/library-profiles/eth-zurich.yaml`
- Create: `config/library-profiles/uni-wien.yaml`
- Create: `config/library-profiles/uni-hamburg.yaml`

- [ ] **Schritt 1: TU München**

Datei: `config/library-profiles/tum.yaml`

```yaml
# TU München — Shibboleth (TUM-WAYF)
uni: tum
auth_type: Shibboleth
auth_url: https://www.shibboleth.tum.de/idp/shibboleth
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
  - jstor.org
  - wiley.com
  - tandfonline.com
  - sciencedirect.com
bib_pickup_url: https://opac.ub.tum.de
```

- [ ] **Schritt 2: FU Berlin**

Datei: `config/library-profiles/fu-berlin.yaml`

```yaml
# FU Berlin — Shibboleth (DFN-AAI)
uni: fu-berlin
auth_type: Shibboleth
auth_url: https://idm.fu-berlin.de/idp/shibboleth
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
  - jstor.org
  - wiley.com
  - tandfonline.com
  - sciencedirect.com
bib_pickup_url: https://www.ub.fu-berlin.de/service/fernleihe/
```

- [ ] **Schritt 3: ETH Zürich**

Datei: `config/library-profiles/eth-zurich.yaml`

```yaml
# ETH Zuerich — Shibboleth (SWITCHaai)
uni: eth-zurich
auth_type: Shibboleth
auth_url: https://aai.ethz.ch/idp/shibboleth
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
  - jstor.org
  - wiley.com
  - tandfonline.com
  - sciencedirect.com
  - research4life.org
bib_pickup_url: https://www.nebis.ch/de/suchen/
```

- [ ] **Schritt 4: Uni Wien**

Datei: `config/library-profiles/uni-wien.yaml`

```yaml
# Uni Wien — Shibboleth (ACOnet)
uni: uni-wien
auth_type: Shibboleth
auth_url: https://idp.univie.ac.at/idp/shibboleth
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
  - jstor.org
  - wiley.com
  - tandfonline.com
  - sciencedirect.com
bib_pickup_url: https://usearch.univie.ac.at/
```

- [ ] **Schritt 5: Uni Hamburg**

Datei: `config/library-profiles/uni-hamburg.yaml`

```yaml
# Uni Hamburg — Shibboleth (DFN-AAI)
uni: uni-hamburg
auth_type: Shibboleth
auth_url: https://idp.uni-hamburg.de/idp/shibboleth
licensed_sites:
  - link.springer.com
  - degruyter.com
  - ebookcentral.proquest.com
  - tib.eu
  - jstor.org
  - wiley.com
  - tandfonline.com
  - sciencedirect.com
bib_pickup_url: https://www.sub.uni-hamburg.de/recherche/fernleihe.html
```

- [ ] **Schritt 6: Positiv-Tests grün prüfen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/test_library_profiles.py::TestProfilesValidPositiv -v
```

Erwartetes Ergebnis: Alle 5 Positiv-Tests PASS.

- [ ] **Schritt 7: Commit (Schema + Profile)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
git add config/library-profiles/
git commit -m "feat(B): JSON-Schema + 5 DACH-Hochschul-Profile (TUM, FU Berlin, ETH, Wien, Hamburg)"
```

---

### Task 4: Onboard-Hook implementieren (GREEN für Hook-Tests)

**Files:**
- Create: `hooks/onboard-project-uni-prompt.sh`

- [ ] **Schritt 1: Hook-Skript schreiben**

Datei: `hooks/onboard-project-uni-prompt.sh`

```bash
#!/usr/bin/env bash
# onboard-project-uni-prompt.sh
# Zeigt verfuegbare Uni-Profile und schreibt das gewaehlte nach active.yaml
#
# Aufruf (interaktiv):   ./hooks/onboard-project-uni-prompt.sh
# Aufruf (nicht-interaktiv): ./hooks/onboard-project-uni-prompt.sh --profile tum
# Aufruf (Test):         ./hooks/onboard-project-uni-prompt.sh --profile tum --output-dir /tmp/test
#
# Legt active.yaml an unter: ~/.academic-research/library-profiles/active.yaml
# (oder --output-dir, falls angegeben)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROFILES_DIR="${REPO_ROOT}/config/library-profiles"

SELECTED_PROFILE=""
OUTPUT_DIR="${HOME}/.academic-research/library-profiles"

# ── Argumente parsen ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      SELECTED_PROFILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unbekanntes Argument: $1" >&2
      exit 1
      ;;
  esac
done

# ── Verfuegbare Profile sammeln ───────────────────────────────────────────────
mapfile -t PROFILE_FILES < <(
  find "${PROFILES_DIR}" -maxdepth 1 -name "*.yaml" ! -name "_*" | sort
)

if [[ ${#PROFILE_FILES[@]} -eq 0 ]]; then
  echo "Fehler: Keine Profile gefunden in ${PROFILES_DIR}" >&2
  exit 1
fi

declare -a SLUGS
for f in "${PROFILE_FILES[@]}"; do
  SLUGS+=("$(basename "$f" .yaml)")
done

# ── Profil-Auswahl ────────────────────────────────────────────────────────────
if [[ -z "${SELECTED_PROFILE}" ]]; then
  echo ""
  echo "academic-research: Universitaets-Profil auswaehlen"
  echo "─────────────────────────────────────────────────"
  for i in "${!SLUGS[@]}"; do
    echo "  $((i+1))) ${SLUGS[$i]}"
  done
  echo ""
  read -rp "Nummer eingeben [1-${#SLUGS[@]}]: " CHOICE
  if ! [[ "${CHOICE}" =~ ^[0-9]+$ ]] || \
     [[ "${CHOICE}" -lt 1 ]] || \
     [[ "${CHOICE}" -gt ${#SLUGS[@]} ]]; then
    echo "Ungueltige Auswahl: ${CHOICE}" >&2
    exit 1
  fi
  SELECTED_PROFILE="${SLUGS[$((CHOICE-1))]}"
fi

# ── Profil-Datei pruefen ──────────────────────────────────────────────────────
PROFILE_FILE="${PROFILES_DIR}/${SELECTED_PROFILE}.yaml"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  echo "Fehler: Profil '${SELECTED_PROFILE}' nicht gefunden (${PROFILE_FILE})" >&2
  exit 1
fi

# ── Output-Verzeichnis anlegen ────────────────────────────────────────────────
mkdir -p "${OUTPUT_DIR}"
chmod 700 "${OUTPUT_DIR}"

# ── active.yaml schreiben ─────────────────────────────────────────────────────
ACTIVE_YAML="${OUTPUT_DIR}/active.yaml"
cp "${PROFILE_FILE}" "${ACTIVE_YAML}"
chmod 600 "${ACTIVE_YAML}"

echo "Profil '${SELECTED_PROFILE}' aktiviert: ${ACTIVE_YAML}"
```

- [ ] **Schritt 2: Hook ausfuehrbar machen**

```bash
chmod +x /Users/j65674/Repos/academic-research-v6.2-B/hooks/onboard-project-uni-prompt.sh
```

- [ ] **Schritt 3: Hook-Tests grün prüfen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/test_library_profiles.py::TestOnboardHook -v
```

Erwartetes Ergebnis: Alle 4 Hook-Tests PASS.

- [ ] **Schritt 4: Alle Tests grün prüfen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/test_library_profiles.py -v
```

Erwartetes Ergebnis: Alle Tests PASS (0 failures).

- [ ] **Schritt 5: Commit (Hook)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
git add hooks/onboard-project-uni-prompt.sh
git commit -m "feat(B): Onboard-Hook fuer Uni-Profil-Auswahl (--profile Flag)"
```

---

### Task 5: Spec-Dateien committen

- [ ] **Schritt 1: Specs committen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
git add specs/v6.2/B.md specs/v6.2/B-plan.md
git commit -m "docs(B): Spec + Plan fuer Per-Uni-Profile (Chunk B)"
```

---

### Task 6: Gesamte Test-Suite prüfen (Regression)

- [ ] **Schritt 1: Alle Tests laufen lassen**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-B
~/.academic-research/venv/bin/python -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -20
```

Erwartetes Ergebnis: 0 failures. (Neue Tests: 16 in test_library_profiles.py)

---

## Dependency-Hinweis

`jsonschema` muss im venv vorhanden sein. Check:

```bash
~/.academic-research/venv/bin/python -c "import jsonschema; print(jsonschema.__version__)"
```

Falls nicht installiert:
```bash
~/.academic-research/venv/bin/pip install jsonschema
```

`pyyaml` muss ebenfalls vorhanden sein (laut infra-brief ist `yaml` Teil des venv).
