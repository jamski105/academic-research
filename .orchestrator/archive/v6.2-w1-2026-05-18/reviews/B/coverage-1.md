# COVERAGE REPORT — Chunk B / PR #133

**Ticket:** #86 — v6.2 · F16 — Per-Uni-Profile (4-5 DACH-Hochschul-Templates)
**Spec:** /Users/j65674/Repos/academic-research-v6.2-B/specs/v6.2/B.md
**Iteration:** 1
**Date:** 2026-05-18

---

## AC1: YAML-Schema in `specs/v6.2/f16-5-per-uni-profiles.md` definiert und JSON-Schema validierbar

**Status: PARTIAL**

- `config/library-profiles/_schema.json` ist im Diff vorhanden (Draft-07, alle Pflichtfelder korrekt, Enum-Constraint, minItems:1 für licensed_sites, Hostname-Pattern-Regex). Technisch vollständig und JSON-Schema-validierbar.
- ABER: Ticket-AC1 fordert explizit den Spec-Pfad `specs/v6.2/f16-5-per-uni-profiles.md`. Dieser Pfad fehlt im PR-Diff komplett. Stattdessen existiert `specs/v6.2/B.md` (allgemeine Chunk-Spec) und `specs/v6.2/B-plan.md`.
- Die Schema-Definition selbst ist in `specs/v6.2/B.md` (im Diff) und in `_schema.json` enthalten — inhaltlich erfüllt, aber falscher Dateiname laut Ticket.
- Evidence: `config/library-profiles/_schema.json` (Diff-Zeilen 7–52), `specs/v6.2/B.md` (Diff-Zeilen 879–928). Fehlend: `specs/v6.2/f16-5-per-uni-profiles.md`.

---

## AC2: 5 initiale Profile unter `config/library-profiles/` (TU München, FU Berlin, ETH Zürich, Uni Wien, Uni Hamburg)

**Status: PASS**

- Alle 5 Profile im Diff: `tum.yaml` (Diff:94–113), `fu-berlin.yaml` (Diff:74–93), `eth-zurich.yaml` (Diff:53–73), `uni-wien.yaml` (Diff:134–153), `uni-hamburg.yaml` (Diff:114–133).
- Alle unter `config/library-profiles/` abgelegt.

---

## AC3: Jedes Profil enthält Pflichtfelder `uni`, `auth_type`, `auth_url`, `licensed_sites`, `bib_pickup_url`

**Status: PASS**

- Alle 5 Profile enthalten sämtliche Pflichtfelder.
- Beispiel tum.yaml: `uni: tum`, `auth_type: Shibboleth`, `auth_url: https://www.shibboleth.tum.de/idp/shibboleth`, `licensed_sites` (8 Einträge), `bib_pickup_url: https://opac.ub.tum.de`.
- Evidence: `config/library-profiles/tum.yaml` (Diff:99–113), alle anderen Profile analog.
- Tests bestätigen: `TestProfilesValidPositiv` — 5 Tests (test_tum_valid, test_fu_berlin_valid, test_eth_zurich_valid, test_uni_wien_valid, test_uni_hamburg_valid) in `tests/test_library_profiles.py:1017–1030`.

---

## AC4: `onboard-project`-Hook zeigt Profil-Auswahl und schreibt gewähltes Profil nach `~/.academic-research/library-profiles/active.yaml`

**Status: PASS**

- `hooks/onboard-project-uni-prompt.sh` (Diff:154–244) implementiert:
  - Interaktives Auswahlmenü (nummerierte Liste aller `*.yaml` ohne `_*`)
  - `--profile <slug>` Flag für nicht-interaktiven Modus
  - `--output-dir` Flag für CI/Test
  - Schreibt via `cp + chmod 600` nach `${OUTPUT_DIR}/active.yaml`
  - Re-run-fähig (überschreibt bei erneutem Aufruf)
- Hook ist ausführbar (mode 100755 im Diff)
- Tests: `TestOnboardHook::test_hook_schreibt_active_yaml` und `test_hook_active_yaml_ist_valide` in `tests/test_library_profiles.py:1116–1147` — prüfen returncode=0, Datei-Existenz, Inhalt (`uni: tum`, `auth_type: Shibboleth`) und Schema-Validität.

---

## AC5: `auth-helper`-Agent (#83) liest `active.yaml` und verzweigt Auth-Flow

**Status: PASS (Out-of-Scope für Chunk B)**

- Laut Spec `B.md` §"Abgrenzung zu Chunk C": Chunk B liefert Profile + Schema + Hook. `auth-helper` (Chunk C) konsumiert `active.yaml` — keine Änderungen an auth-helper-Logik in diesem PR.
- Dieser AC wird in Chunk C (Issue #83) implementiert, nicht in PR #133.
- Das Interface (Format von `active.yaml`) ist durch die 5 Profile und das Schema vollständig spezifiziert.

---

## AC6: JSON-Schema-Validierung schlägt fehl bei fehlendem Pflichtfeld; pytest deckt Positiv- und Negativ-Case ab

**Status: PASS**

- Schema-Constraint: `"required": ["uni", "auth_type", "auth_url", "licensed_sites", "bib_pickup_url"]` in `_schema.json:12`.
- Negativ-Tests in `tests/test_library_profiles.py`:
  - `test_fehlendes_bib_pickup_url` (Zeile 1048)
  - `test_fehlendes_uni` (Zeile 1054)
  - `test_fehlendes_auth_type` (Zeile 1059)
  - `test_ungültiger_auth_type` (LDAP → ValidationError, Zeile 1064)
  - `test_leere_licensed_sites` (minItems:1, Zeile 1069)
  - `test_fehlendes_auth_url` (Zeile 1074)
  - `test_fehlende_licensed_sites` (Zeile 1079)
  - `test_wildcard_host_abgelehnt` (Zeile 1090) — Bonus
  - `test_url_als_host_abgelehnt` (Zeile 1097) — Bonus
- Positiv-Tests: 5 × `test_*_valid` (Zeilen 1017–1030).
- PR-Body: "18/18 tests passed".

---

## Zusammenfassung

| AC | Status | Lücke |
|---|---|---|
| AC1: Schema-Spec in `specs/v6.2/f16-5-per-uni-profiles.md` | PARTIAL | Datei fehlt; Schema-Inhalt in `B.md` + `_schema.json` vorhanden |
| AC2: 5 Profile unter `config/library-profiles/` | PASS | — |
| AC3: Pflichtfelder in allen Profilen | PASS | — |
| AC4: Onboard-Hook + active.yaml | PASS | — |
| AC5: auth-helper-Routing (Chunk C) | PASS | Out-of-Scope Chunk B, Chunk C zuständig |
| AC6: pytest Positiv + Negativ | PASS | — |

**Blocking failures:** 0
**Non-blocking gaps:** 1 (AC1: fehlender Spec-Dateiname `f16-5-per-uni-profiles.md` — inhaltlich durch `B.md` abgedeckt, formaler Benennungsfehler)
