# Spec: Chunk C — auth-helper Subagent (v6.2)

**Ticket:** #83 — F16 — `auth-helper` Subagent (HAN, Shibboleth, EZproxy, DFN-AAI)
**Security-labeled:** ja
**Branch:** `feat/v6.2-C-auth-helper`
**Depends on:** B (Uni-Profile-Schema aus `feat/v6.2-B-uni-profile`)

---

## Zweck

`auth-helper` ist ein wiederverwendbarer Subagent, der SSO-Logins fuer DACH-Hochschul-Bibliotheken ausfuehrt. Er wird von Verlags-Subagenten (#82) aufgerufen, bevor ein Zugriff auf lizenzierte Inhalte versucht wird. Er liest das aktive Per-Uni-Profil, erkennt die Auth-Methode und startet — falls noetig — den Login-Flow ausschliesslich via `browser-use`.

---

## Architektur

```
Aufrufer (z.B. springer-book, ebook-central)
  │
  └─► auth-helper
        ├── (1) Liest ~/.academic-research/library-profiles/active.yaml
        ├── (2) Ermittelt auth_type (Shibboleth | EZproxy | HAN | oa-only)
        ├── (3) Prueft licensed_sites-Allowlist fuer die Ziel-URL
        ├── (4) Falls auth_type != oa-only:
        │     ├── Liest Credentials aus Profil-Datei (0600)
        │     └── Fuehrt Login-Flow via browser-use aus
        └── (5) Gibt Session-Status zurueck (authenticated | auth_failed | not_required)
```

---

## Auth-Typ-Erkennung

Reihenfolge (Precedence):
1. `auth_type`-Feld aus `active.yaml` (autoritativ)
2. URL-Pattern-Matching als Fallback (fuer Robustheit bei fehlenden Profilen)

URL-Pattern-Matching-Regeln:
- `.han.` im Hostname → HAN
- `wayf.` oder `shibboleth` oder `/idp/` im Pfad → Shibboleth
- `ezproxy` im Hostname → EZproxy
- `dfn-aai` oder `.aai.dfn.de` → DFN-AAI (wird als Shibboleth behandelt — DFN-AAI ist Shibboleth-basiert)
- Kein Match + keine Login-Anforderung erkennbar → oa-only (kein Login)

---

## Input-Format (vom Aufrufer)

```json
{
  "target_url": "https://link.springer.com/book/10.1007/978-3-031-12345-6",
  "profile_path": "~/.academic-research/library-profiles/active.yaml"
}
```

`profile_path` ist optional (Default: `~/.academic-research/library-profiles/active.yaml`).

---

## Output-Format

### Erfolg (authenticated)
```json
{
  "status": "authenticated",
  "auth_type": "Shibboleth",
  "uni": "tum",
  "session_context": "browser-use session handle (kein Cookie-Dump)"
}
```

### Kein Login noetig (oa-only)
```json
{
  "status": "not_required",
  "auth_type": "oa-only",
  "uni": null
}
```

### Fehlgeschlagener Login
```json
{
  "status": "auth_failed",
  "reason": "bad_credentials | account_locked | site_unavailable | wrong_method"
}
```

**Sicherheitsregel:** `session_context` enthaelt NUR den `browser-use`-Session-Handle (opaque). Cookies und Passwort-Strings erscheinen NICHT im Output.

---

## Credential-Handling (Sicherheits-Kern)

### Speicherung
- Credentials werden in der Profil-Datei unter `~/.academic-research/library-profiles/` gespeichert, mit `chmod 0600` (owner-only).
- Feld `credentials_keys` im Profil (aus B-Schema) listet die Schluessel (z.B. `[han_user, han_password]`).
- Werte werden direkt im Profil-YAML gespeichert (Sprint 1; OS-Keychain ist out-of-scope).
- Profile-Datei wird beim Lesen auf `0600`-Perms geprueft; bei falschen Perms → Fehler mit Hinweis.

### Verbatim-Schutz
- Credentials duerfen NICHT in `session_context`, logs, oder Agenten-Output-Strings erscheinen.
- Der Agent wird angewiesen: NIEMALS Passwort-Werte ausgeben oder loggen.
- Der PreToolUse-Verbatim-Guard (bestehend in `hooks/verbatim-guard.mjs`) sichert Write-Aufrufe ab.

### Allowlist-Pruefung
- `licensed_sites` aus dem Profil definiert, fuer welche Hosts ein Login versucht wird.
- Login NUR fuer Hosts in `licensed_sites` — niemals fuer unbekannte Hosts.

---

## Login-Flows (browser-use)

### HAN (Leibniz FH, u.a.)
1. Baue HAN-Proxy-URL aus `proxy_pattern` + Ziel-Host
2. Navigiere zur HAN-Login-Seite
3. Fuege `han_user` und `han_password` in Formular ein (via browser-use `type`)
4. Submit → pruefe Redirect auf Ziel-Site

### Shibboleth / DFN-AAI (TUM, FU Berlin, u.a.)
1. Navigiere zu `auth_url` (WAYF oder direkt zum IdP)
2. Waehle Institution (falls WAYF-Auswahl noetig) via `uni`-Feld aus Profil
3. Fuege Credentials in Shibboleth-Login-Form ein
4. Submit → pruefe Redirect und Session-Cookie (kein Cookie-Dump in Output)

### EZproxy
1. Navigiere zu `auth_url`
2. Login-Formular mit Credentials ausfuellen
3. Submit → pruefe Redirect

### oa-only / none
- Kein Login-Versuch. Gib sofort `{status: not_required}` zurueck.

---

## Session-Management

- Session-Timeout wird durch `browser-use`-Signale erkannt (kein fixer Timer, OQ17-Default).
- Wenn `browser-use` eine Session-Expiry signalisiert: auth-helper re-authentifiziert.
- Kein Session-Persist ueber Plugin-Invocations hinaus (out-of-scope laut Ticket).

---

## Fehlerbehandlung

| Situation | Status | reason |
|---|---|---|
| Falsches Passwort / Login abgelehnt | `auth_failed` | `bad_credentials` |
| Konto gesperrt (nach n Fehlversuchen) | `auth_failed` | `account_locked` |
| Site nicht erreichbar / Timeout | `auth_failed` | `site_unavailable` |
| Profil hat anderen auth_type als URL | `auth_failed` | `wrong_method` |
| CAPTCHA aufgetaucht | `captcha` | (kein reason-Feld) |

CAPTCHA → der Agent gibt `{status: captcha}` zurueck und haelt an (User-Hand-off, out-of-scope fuer auto-solve).

---

## Agenten-Datei-Spezifikation

Datei: `agents/auth-helper.md`

Frontmatter:
```yaml
name: auth-helper
model: sonnet
tools: [Bash(browser-use:*), Bash(browser-use *), Read, Write]
maxTurns: 12
```

---

## Tests

Datei: `tests/test_auth_helper.py`

Testklassen:
1. **`TestAuthTypeDetection`** — Unit-Tests fuer `detect_auth_type(profile, url)`
   - Profil mit `auth_type: Shibboleth` → gibt `Shibboleth` zurueck (Profil-Prio)
   - Profil ohne `auth_type`, URL mit `wayf.` → gibt `Shibboleth`
   - URL mit `.han.` → gibt `HAN`
   - URL mit `ezproxy` → gibt `EZproxy`
   - Kein Match → gibt `oa-only`
   - `auth_type: oa-only` im Profil → gibt `oa-only` (kein Login)

2. **`TestCredentialSecurity`** — Sicherheitstests
   - Test: Nach `load_credentials(profile_path)` enthaelt der Rueckgabewert keine Passwort-Strings im `repr()` / `str()` (kein versehentliches Logging)
   - Test: `check_profile_permissions()` schlaegt fehl bei `0644`-Datei, besteht bei `0600`
   - Test: Schema-Validierung schlaegt fehl, wenn ein Profil versucht, Credentials direkt einzubetten (statt via `credentials_keys`)

3. **`TestShibbolethMockFlow`** — Mock-Browser-Flow (Haupt-Akzeptanztest)
   - Laedt Mock-HTML aus `tests/fixtures/shibboleth_mock/`
   - Simuliert Shibboleth-Login → `status: authenticated`
   - Prueft: Testausgabe enthaelt NICHT den Test-Passwort-String (`grep`-Assertion)
   - Prueft: Session-Output enthaelt keine serialisierten Cookies

4. **`TestNoLoginForOASites`** — Pass-through
   - `auth_type: oa-only` → `status: not_required`, kein browser-use-Aufruf

Fixtures:
- `tests/fixtures/shibboleth_mock/login.html` — Shibboleth-IdP-Login-Seite (Mock)
- `tests/fixtures/shibboleth_mock/wayf.html` — WAYF-Auswahl (Mock)
- `tests/fixtures/shibboleth_mock/success.html` — Redirect-Ziel nach Login

---

## Sicherheits-Checkliste (Plan-Gate)

- [ ] Credentials erscheinen nicht in `agent_output` JSON
- [ ] Credentials erscheinen nicht in stdout/logs
- [ ] `session_context` serialisiert keine Cookies
- [ ] Profile-Datei-Perms werden auf `0600` geprueft
- [ ] Schema-Validation verhindert Literal-Credentials in Profilen
- [ ] `licensed_sites`-Allowlist wird vor Login-Versuch geprueft
- [ ] `oa-only`-Erkennung verhindert unnoetigen Login

---

## Dateien

| Datei | Status |
|---|---|
| `agents/auth-helper.md` | NEU |
| `tests/test_auth_helper.py` | NEU |
| `tests/fixtures/shibboleth_mock/login.html` | NEU |
| `tests/fixtures/shibboleth_mock/wayf.html` | NEU |
| `tests/fixtures/shibboleth_mock/success.html` | NEU |
| `specs/v6.2/C.md` | diese Datei |
| `specs/v6.2/C-plan.md` | naechster Schritt |
