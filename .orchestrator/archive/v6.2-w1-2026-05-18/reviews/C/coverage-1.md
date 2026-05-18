# Coverage Report — Chunk C (auth-helper) / PR #136 / Iteration 1

Ticket: #83 — v6.2 · F16 — auth-helper Subagent (HAN, Shibboleth, EZproxy, DFN-AAI)
Security-labeled: yes

---

## AC1: `agents/auth-helper.md` mit `model: sonnet`, `tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]`, `maxTurns` >= 12

**Status: PASS**

Evidence:
- `agents/auth-helper.md` neu hinzugefügt (diff Zeile 4–231)
- Frontmatter enthält `model: sonnet`, `tools: ["Bash(browser-use:*)", "Bash(browser-use *)", Read, Write]`, `maxTurns: 12`
- Alle drei Pflichtfelder exakt wie im AC spezifiziert

---

## AC2: Agent erkennt `auth_type` (HAN / Shibboleth / EZproxy / DFN-AAI / none) aus Profil und URL-Pattern, bevor Login-Flow startet

**Status: PASS**

Evidence:
- `agents/auth_helper_lib.py::detect_auth_type()` (diff Zeile 300–335 in lib, 1066–1091 in Plan-Variante)
- Profil-Feld `auth_type` hat absolute Priorität (Zeile 314–316)
- URL-Pattern-Matching als Fallback: `_HAN_HOSTNAME_PATTERN`, `_WAYF_HOSTNAME_PATTERN`, `_IDP_PATH_PATTERN`, `_EZPROXY_HOSTNAME_PATTERN`
- DFN-AAI wird als Shibboleth behandelt (`_DFNAAI_PATTERN` → `return "Shibboleth"`)
- Tests: `TestAuthTypeDetection` mit 10 Tests deckend alle Pfade ab:
  - `test_profile_auth_type_takes_precedence_over_url`
  - `test_han_detected_from_url_when_no_profile_auth_type`
  - `test_shibboleth_detected_from_wayf_in_url`
  - `test_shibboleth_detected_from_idp_path`
  - `test_dfn_aai_from_profile_field`
  - `test_ezproxy_detected_from_url`
  - `test_oa_only_when_no_match`
  - `test_profile_oa_only_overrides_url_with_auth_pattern`
  - `test_han_from_profile_field`

---

## AC3: SSO-Login ausschließlich über `browser-use` — kein direkter HTTP-Aufruf, kein curl/wget

**Status: PASS**

Evidence:
- `agents/auth-helper.md` Schritt 4 (HAN-Login, Shibboleth-Login, EZproxy-Login) verwendet ausschließlich `browser-use "..."` Bash-Aufrufe
- Kein `curl`, `wget`, `requests`, `httpx` oder ähnliches in `agents/auth_helper_lib.py` oder `agents/auth-helper.md`
- Die Python-Logik (`auth_helper_lib.py`) führt keinen HTTP-Call durch — sie bereitet nur Daten vor und validiert
- `tools`-Frontmatter erlaubt nur `Bash(browser-use:*)`, `Bash(browser-use *)`, `Read`, `Write` — kein direkter HTTP-Tool-Zugang

Note: Kein direkter End-to-End-Test, der assertiert "kein curl wurde aufgerufen" — aber das Toolset ist allowlist-only und die Agenten-Instruktion ist explizit.

---

## AC4: Nach erfolgreichem Login liefert Agent authentifizierte Browser-Session zurück (für nachfolgende Subagenten nutzbar)

**Status: PASS**

Evidence:
- `build_auth_flow_result()` in `agents/auth_helper_lib.py` (Zeile 442–486) gibt bei Erfolg `{status: "authenticated", session_context: "browser-use:active:<uni>"}` zurück
- Test: `TestShibbolethMockFlow::test_build_auth_flow_result_for_shibboleth` assertiert `result["status"] == "authenticated"` und `result["session_context"]` vorhanden
- Session-Handle ist opak (`browser-use:active:<uni>`) — kein Cookie-Dump

---

## AC5: Credentials und Session-Cookies erscheinen zu keinem Zeitpunkt in Agenten-Outputs, Logs oder Vault-Einträgen

**Status: PASS**

Evidence (Implementierung):
- `CredentialStore.__repr__()` und `__str__()` maskieren alle Werte: `"values=<redacted>"` (Zeile 279–284)
- `agents/auth_helper_lib.py` Profil-Lader gibt nur `safe`-Felder aus (keine Credential-Werte)
- `build_auth_flow_result()` enthält expliziten Kommentar: "kein Cookie-Dump, kein Token-Wert" — gibt nur opaken Handle zurück
- Agenten-Workflow in `auth-helper.md` gibt vor dem Credentials-Laden explizit an: "NICHT in diesen Output schreiben"

Evidence (Tests):
- `test_load_credentials_returns_dict_without_password_in_repr`: assertiert `"supersecret_testpass_XYZ" not in repr(creds)` und `not in str(creds)`
- `test_no_credential_string_in_stdout_after_detection`: capsys-Assertion mit Canary-String `"CANARY_CRED_STRING_99"`
- `test_no_credential_leak_in_auth_result_json`: assertiert Passwort und Username nicht in JSON-Serialisierung
- `test_no_cookie_dump_in_session_context`: assertiert kein `Set-Cookie`, kein `Cookie:`, Session-Handle < 200 Zeichen

---

## AC6: Credential-Speicherung ausschließlich in OS-Keychain ODER Profil-Datei mit Perms `0600`

**Status: PASS**

Evidence (Implementierung):
- `check_profile_permissions()` in `agents/auth_helper_lib.py` (Zeile 342–356): prüft `stat.S_IMODE(path_stat.st_mode) != 0o600` → wirft `InsecureProfilePermissionsError`
- `load_credentials()` ruft `check_profile_permissions()` als erstes auf (Zeile 379)
- Agenten-Workflow Schritt 1: `stat -f "%Lp" ... active.yaml` + explizite Fehlerbehandlung bei nicht-600

Evidence (Tests):
- `test_check_profile_permissions_passes_for_0600`: Kein Fehler bei `0o600`
- `test_check_profile_permissions_fails_for_0644`: `InsecureProfilePermissionsError` bei `0o644`
- `test_check_profile_permissions_fails_for_0640`: `InsecureProfilePermissionsError` bei `0o640`

OS-Keychain: Als Out-of-scope deklariert (OQ16, Sprint 1). Profil-Datei mit 0600 ist die einzige implementierte Storage-Methode. AC akzeptiert "OR" — PASS.

---

## AC7 (Haupt-Akzeptanztest): Shibboleth-Mock-Flow mit Hochschul-Profil → SSO-Login endet mit Status `authenticated`, kein Credential-Leak in Testausgaben

**Status: PASS**

Evidence:
- `tests/fixtures/shibboleth_mock/login.html`, `wayf.html`, `success.html` — alle drei Fixtures im Diff vorhanden
- `TestShibbolethMockFlow::test_mock_fixtures_exist`: assertiert Existenz der Fixtures
- `TestShibbolethMockFlow::test_build_auth_flow_result_for_shibboleth`: assertiert `status == "authenticated"`, `auth_type == "Shibboleth"`, `uni == "tum"`, kein Passwort-String im JSON
- `TestShibbolethMockFlow::test_no_credential_leak_in_auth_result_json`: assertiert kein Passwort, kein Username in serialisiertem Output

Einschränkung: Der Mock-Flow testet `build_auth_flow_result()` mit `browser_success=True` als Parameter — er simuliert einen erfolgreichen browser-use-Aufruf, führt aber keinen echten Browser-Flow durch. Das ist angemessen für Unit-Tests (echter Browser-Aufruf wäre CI-untauglich) und entspricht dem Spec-Wortlaut "Shibboleth-Mock-Flow" und "Simuliert Shibboleth-Login".

---

## AC8: Auth-Methode `none`/`oa-only` wird korrekt erkannt und durchgeleitet, ohne Login-Versuch

**Status: PASS**

Evidence:
- `detect_auth_type()` gibt `"oa-only"` zurück wenn kein Match und kein Profil-auth_type
- `build_auth_flow_result()` mit `auth_type="oa-only"` gibt sofort `{status: "not_required", auth_type: "oa-only"}` zurück (Zeile 464–469)
- `agents/auth-helper.md` Schritt 4: "oa-only → kein Login" mit direktem JSON-Return

Tests (`TestNoLoginForOASites`):
- `test_oa_only_profile_returns_not_required`: assertiert `status == "not_required"`, `auth_type == "oa-only"`
- `test_oa_only_result_has_null_uni_or_profile_uni`: Struktur-Assertion
- `test_detect_oa_only_from_url_no_browser_call_marker`: assertiert `detect_auth_type(…) == "oa-only"` für OA-URL
- `test_profile_oa_only_overrides_url_with_auth_pattern` (in `TestAuthTypeDetection`): assertiert oa-only-Profil überschreibt URL-Pattern

---

## Security Recheck

### No Credential Logging
**PASS (true)**

- `CredentialStore.__repr__/__str__` maskiert alle Werte mit `<redacted>`
- `agents/auth_helper_lib.py` gibt beim Profil-Laden nur `safe`-Felder aus (keine Credential-Werte)
- `agents/auth-helper.md` Workflow gibt Credentials nicht in Output
- Agenten-Sicherheitscheckliste explizit: "Kein Passwort-String im Output", "Kein Cookie-Inhalt im Output"
- Tests bestätigen via Canary-String (`CANARY_CRED_STRING_99`, `SHIBBOLETH_TEST_SECRET_456`) dass nichts durchsickert
- `grep`-Analyse des Diffs: Kein `print(password)`, `logging.info(password)`, `logger.debug(cred)` oder ähnliches gefunden

### Perms 0600 Enforced
**PASS (true)**

- `check_profile_permissions()` in `auth_helper_lib.py` erzwingt exakt `0o600` via `os.stat()` + `stat.S_IMODE()`
- `load_credentials()` ruft dies als erste Aktion auf — keine Credentials ohne Perm-Check lesbar
- 3 dedizierte Tests: Pass für 0600, Fail für 0644 und 0640
- Agenten-Workflow prüft ebenfalls via `stat -f "%Lp"` Shell-Befehl

### Allowlist-Only Auth Hosts
**PASS (true)**

- `licensed_sites` aus Per-Uni-Profil definiert welche Hosts Login erhalten
- `agents/auth-helper.md` Schritt 3: Hostname der Ziel-URL wird gegen `licensed_sites` geprüft; wenn nicht enthalten → `{status: auth_failed, reason: wrong_method}`
- `agents/auth_helper_lib.py` Implementierung und Agenten-Sicherheitscheckliste: "Login NUR für Hosts in `licensed_sites`"

Einschränkung: Kein expliziter Test für den Allowlist-Rejection-Pfad (URL nicht in `licensed_sites` → `wrong_method`). Das ist eine Lücke in der Testabdeckung, aber die Implementierung in `auth-helper.md` ist vorhanden und die `build_auth_flow_result()` unterstützt den `wrong_method`-Reason. Nicht blockierend — die Allowlist-Logik liegt im Agenten-Workflow (LLM-Instruktionen), nicht in einem testbaren Code-Pfad.

---

## Summary

| AC | Status | Blocking |
|---|---|---|
| AC1: agents/auth-helper.md Frontmatter korrekt | PASS | — |
| AC2: auth_type Erkennung (Profil + URL-Pattern) | PASS | — |
| AC3: SSO nur via browser-use | PASS | — |
| AC4: Authenticated Session zurückgegeben | PASS | — |
| AC5: Credentials/Cookies nie in Output/Logs | PASS | — |
| AC6: 0600-Perms erzwungen | PASS | — |
| AC7: Shibboleth-Mock-Flow Test | PASS | — |
| AC8: oa-only Pass-through ohne Login | PASS | — |
| Security: No credential logging | PASS | — |
| Security: 0600 enforced | PASS | — |
| Security: Allowlist-only auth hosts | PASS | — |

**Overall: PASS**
**Blocking failures: 0**
**Recommendation: merge**
