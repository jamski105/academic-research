# Spec: Chunk B — Per-Uni-Profile (v6.2 F16.5)

**Ticket:** #86
**Branch:** feat/v6.2-B-uni-profile
**Stand:** 2026-05-13

---

## Ziel

Bereitstellung von 5 DACH-Hochschul-Profil-Templates (`config/library-profiles/`) mit validiertem
JSON-Schema, pytest-Tests und einem re-run-fähigen Onboard-Hook, der das aktive Profil nach
`~/.academic-research/library-profiles/active.yaml` schreibt.

Der `auth-helper`-Subagent (Chunk C) liest `active.yaml` und wählt den passenden Auth-Flow.

---

## YAML-Schema (Pflichtfelder)

```yaml
uni: <string>                  # Maschinen-lesbarer Schlüssel, slug-format
auth_type: <enum>              # Shibboleth | EZproxy | HAN | oa-only
auth_url: <string>             # URL des WAYF/IdP/HAN-Endpoints
licensed_sites:                # Liste erlaubter Auth-Hosts (Allowlist für auth-helper)
  - <hostname>
bib_pickup_url: <string>       # OPAC-URL für Abholung / Fernleihe-Formular
```

Optionale Felder:

```yaml
proxy_pattern: <string>        # Nur HAN/EZproxy — Proxy-URL-Muster mit {site}-Platzhalter
credentials_keys: [<string>]   # Schlüsselnamen für OS-Keychain (nur HAN/EZproxy)
```

---

## 5 initiale Profile

| Datei | Uni | auth_type | Bemerkung |
|---|---|---|---|
| `tum.yaml` | TU München | Shibboleth | WAYF: shibboleth.tum.de |
| `fu-berlin.yaml` | FU Berlin | Shibboleth | WAYF: shibboleth.fu-berlin.de |
| `eth-zurich.yaml` | ETH Zürich | Shibboleth | SWITCHaai-WAYF |
| `uni-wien.yaml` | Uni Wien | Shibboleth | ACOnet-WAYF |
| `uni-hamburg.yaml` | Uni Hamburg | Shibboleth | DFN-AAI-WAYF |

Alle 5 Profile nutzen `Shibboleth` (OQ24: `proxy_pattern` entfällt bei Shibboleth).

`licensed_sites` pro Profil: realistische Allowlist der wichtigsten lizenzierten Hosts
(Springer, De Gruyter, Ebook Central, TIB, JSTOR etc.) — kann vom `auth-helper` überschrieben werden.

---

## JSON-Schema (`_schema.json`)

JSON-Schema (Draft-07) validiert:
- Pflichtfelder: `uni`, `auth_type`, `auth_url`, `licensed_sites`, `bib_pickup_url`
- `auth_type` als Enum: `["Shibboleth", "EZproxy", "HAN", "oa-only"]`
- `licensed_sites`: Array of strings, minItems: 1
- `proxy_pattern` und `credentials_keys` optional

---

## Tests (`tests/test_library_profiles.py`)

TDD — Testfälle:
1. **Positiv-Test:** Alle 5 Profile validieren gegen `_schema.json` ohne Fehler
2. **Negativ-Test (fehlendes Pflichtfeld):** Profil ohne `bib_pickup_url` → ValidationError
3. **Negativ-Test (ungültiger auth_type):** Profil mit `auth_type: LDAP` → ValidationError
4. **Negativ-Test (leere licensed_sites):** Profil mit `licensed_sites: []` → ValidationError
5. **active.yaml-Test:** Onboard-Skript schreibt `active.yaml` korrekt (Inhalt = tum.yaml)

---

## Onboard-Hook (`hooks/onboard-project-uni-prompt.sh`)

Konvention: Shell-Skript im `hooks/`-Verzeichnis (analog zu vorhandener `hooks/`-Struktur;
kein `commands/`-Slot belegt, da kein Slash-Command benötigt).

Verhalten:
1. Listet verfügbare Profile aus `config/library-profiles/` (alle `*.yaml` außer `_schema.json`)
2. Zeigt Auswahlmenü (nummeriert)
3. Schreibt gewähltes Profil als `active.yaml` nach `~/.academic-research/library-profiles/`
4. Re-run-fähig: überschreibt `active.yaml` bei erneutem Aufruf
5. Nicht-interaktiver Modus: `--profile <slug>` Flag für CI/Scripting

---

## Abgrenzung zu Chunk C

Chunk B liefert:
- Schema-Definition + 5 Profile
- `_schema.json` für Validierung
- `hooks/onboard-project-uni-prompt.sh` (schreibt `active.yaml`)
- Tests für Schema-Validierung und Onboard-Skript

Chunk C (`auth-helper`) konsumiert `active.yaml` — keine Änderungen an `auth-helper`-Logik hier.

---

## Datei-Boundary

```
config/library-profiles/tum.yaml
config/library-profiles/fu-berlin.yaml
config/library-profiles/eth-zurich.yaml
config/library-profiles/uni-wien.yaml
config/library-profiles/uni-hamburg.yaml
config/library-profiles/_schema.json
tests/test_library_profiles.py
hooks/onboard-project-uni-prompt.sh
specs/v6.2/B.md          (diese Datei)
specs/v6.2/B-plan.md     (Implementierungsplan)
```
