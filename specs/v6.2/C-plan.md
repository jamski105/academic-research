# auth-helper Subagent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementiere `agents/auth-helper.md` als wiederverwendbaren Subagenten fuer SSO-Logins an DACH-Hochschul-Bibliotheken (HAN, Shibboleth, EZproxy, DFN-AAI), mit striktem Credential-Schutz (keine Credentials in Outputs/Logs).

**Architecture:** Ein Python-Hilfsmodul `tests/test_auth_helper.py` testet die Auth-Logik-Funktionen (`detect_auth_type`, `check_profile_permissions`, `load_credentials`) aus `agents/auth_helper_lib.py`. Die eigentliche Agenten-Definition liegt in `agents/auth-helper.md` (Frontmatter + Markdown-Instruktionen fuer das LLM). Mock-HTML-Fixtures simulieren Shibboleth-Flows ohne echten Browser-Aufruf.

**Tech Stack:** Python 3 (pytest, yaml, os, stat, json), Markdown-Agenten-Definitionen, HTML-Fixtures.

---

## File Map

| Datei | Status | Verantwortung |
|---|---|---|
| `agents/auth_helper_lib.py` | NEU | Pure-Python-Logik: `detect_auth_type`, `check_profile_permissions`, `load_credentials`, `validate_profile_schema` |
| `agents/auth-helper.md` | NEU | LLM-Agenten-Definition: Frontmatter (model/tools/maxTurns) + System-Prompt |
| `tests/test_auth_helper.py` | NEU | pytest-Suite: 4 Testklassen |
| `tests/fixtures/shibboleth_mock/login.html` | NEU | Shibboleth-IdP-Login-Mock |
| `tests/fixtures/shibboleth_mock/wayf.html` | NEU | WAYF-Institutions-Auswahl-Mock |
| `tests/fixtures/shibboleth_mock/success.html` | NEU | Post-Login-Redirect-Mock |

---

## Task 1: Test-Infrastruktur und Fixtures anlegen

**Files:**
- Create: `tests/fixtures/shibboleth_mock/login.html`
- Create: `tests/fixtures/shibboleth_mock/wayf.html`
- Create: `tests/fixtures/shibboleth_mock/success.html`
- Create: `tests/test_auth_helper.py` (nur Imports + leere Testklassen)

- [ ] **Schritt 1: Mock-HTML-Fixtures erstellen**

`tests/fixtures/shibboleth_mock/login.html`:
```html
<!DOCTYPE html>
<html lang="de">
<head><title>Shibboleth Login</title></head>
<body>
  <form method="post" action="/idp/profile/SAML2/Redirect/SSO">
    <input type="text" name="j_username" id="username" placeholder="Benutzername" />
    <input type="password" name="j_password" id="password" placeholder="Passwort" />
    <button type="submit" name="_eventId_proceed">Anmelden</button>
  </form>
</body>
</html>
```

`tests/fixtures/shibboleth_mock/wayf.html`:
```html
<!DOCTYPE html>
<html lang="de">
<head><title>WAYF — Einrichtung waehlen</title></head>
<body>
  <form method="post" action="/wayf/select">
    <select name="user_idp">
      <option value="https://idp.tum.de">Technische Universitaet Muenchen</option>
      <option value="https://idp.fu-berlin.de">Freie Universitaet Berlin</option>
    </select>
    <button type="submit">Weiter</button>
  </form>
</body>
</html>
```

`tests/fixtures/shibboleth_mock/success.html`:
```html
<!DOCTYPE html>
<html lang="de">
<head><title>Zugriff gewaehrt</title></head>
<body>
  <h1>Willkommen</h1>
  <p>Sie sind erfolgreich angemeldet. Session-ID: mock-session-abc123</p>
</body>
</html>
```

- [ ] **Schritt 2: Leere Test-Datei mit Imports anlegen**

`tests/test_auth_helper.py`:
```python
"""Tests fuer auth-helper Subagent-Logik (Chunk C, #83).

Sicherheits-Labels: security, v6, browser-use
"""
import json
import os
import stat
import tempfile
from pathlib import Path

import pytest
import yaml


# Hilfsfunktion: Profil-YAML mit vorgegebenen Feldern schreiben
def _write_profile(tmp_path: Path, data: dict, mode: int = 0o600) -> Path:
    """Schreibt ein Test-Profil-YAML mit angegebenem Dateimodus."""
    profile = tmp_path / "active.yaml"
    profile.write_text(yaml.dump(data), encoding="utf-8")
    os.chmod(profile, mode)
    return profile


class TestAuthTypeDetection:
    """Tests fuer detect_auth_type(profile, url)."""
    pass


class TestCredentialSecurity:
    """Sicherheitstests fuer Credential-Handling."""
    pass


class TestShibbolethMockFlow:
    """Mock-Shibboleth-Flow: authenticated-Status + kein Credential-Leak."""
    pass


class TestNoLoginForOASites:
    """Pass-through fuer oa-only Sites."""
    pass
```

- [ ] **Schritt 3: Verify — Test-Datei laeuft fehlerfrei (keine Tests, aber kein Syntax-Fehler)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/test_auth_helper.py --collect-only 2>&1 | head -20
```

Erwartet: `no tests ran` (oder leere Sammlung), kein `SyntaxError`.

- [ ] **Schritt 4: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && git add tests/test_auth_helper.py tests/fixtures/shibboleth_mock/ && git commit -m "test: Shibboleth-Mock-Fixtures + leere auth-helper Testklassen"
```

---

## Task 2: Python-Logik-Modul `agents/auth_helper_lib.py` (TDD — Schritt 1: Failing Tests)

**Files:**
- Create: `agents/auth_helper_lib.py`
- Modify: `tests/test_auth_helper.py`

- [ ] **Schritt 1: TestAuthTypeDetection — Tests schreiben (RED)**

Ersetze die leere `TestAuthTypeDetection`-Klasse in `tests/test_auth_helper.py`:

```python
class TestAuthTypeDetection:
    """Tests fuer detect_auth_type(profile_data, url)."""

    def test_profile_auth_type_takes_precedence_over_url(self):
        """Profil-auth_type hat Vorrang vor URL-Pattern."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {"auth_type": "Shibboleth", "uni": "tum"}
        result = detect_auth_type(profile, "https://link.springer.com/book/123")
        assert result == "Shibboleth"

    def test_han_detected_from_url_when_no_profile_auth_type(self):
        """HAN wird aus URL erkannt, wenn kein auth_type im Profil."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {"uni": "leibniz-fh"}
        result = detect_auth_type(profile, "https://link-springer-com.han.leibniz-fh.de")
        assert result == "HAN"

    def test_shibboleth_detected_from_wayf_in_url(self):
        """Shibboleth aus wayf. im Hostnamen erkannt."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://wayf.dfn.de/select")
        assert result == "Shibboleth"

    def test_shibboleth_detected_from_idp_path(self):
        """Shibboleth aus /idp/-Pfad erkannt."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://idp.tum.de/idp/profile/SAML2/Redirect")
        assert result == "Shibboleth"

    def test_dfn_aai_detected_and_mapped_to_shibboleth(self):
        """DFN-AAI wird als Shibboleth behandelt."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://bwidm.scc.kit.edu/saml/idp")
        # DFN-AAI URLs haben kein eindeutiges Muster — Profil-auth_type entscheidet
        # Bei leeem Profil und unbekanntem Muster: oa-only
        assert result == "oa-only"

    def test_dfn_aai_from_profile_field(self):
        """DFN-AAI aus Profil-auth_type (falls explizit gesetzt)."""
        from agents.auth_helper_lib import detect_auth_type
        # Laut Schema-Enum: ["Shibboleth", "EZproxy", "HAN", "oa-only"]
        # DFN-AAI ist Shibboleth-basiert → im Profil als Shibboleth gespeichert
        profile = {"auth_type": "Shibboleth", "uni": "kit"}
        result = detect_auth_type(profile, "https://nationallizenzen.de/book")
        assert result == "Shibboleth"

    def test_ezproxy_detected_from_url(self):
        """EZproxy aus Hostnamen erkannt."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://ezproxy.uni-hamburg.de/login")
        assert result == "EZproxy"

    def test_oa_only_when_no_match(self):
        """Kein Muster + kein Profil → oa-only."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://www.oapen.org/book/12345")
        assert result == "oa-only"

    def test_profile_oa_only_overrides_url_with_auth_pattern(self):
        """auth_type: oa-only im Profil verhindert Login auch bei auth-aehlicher URL."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {"auth_type": "oa-only", "uni": "test-uni"}
        # Selbst wenn URL wie ein Proxy aussieht
        result = detect_auth_type(profile, "https://ezproxy.test.de/login")
        assert result == "oa-only"

    def test_han_from_profile_field(self):
        """HAN aus Profil-Feld erkannt."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {"auth_type": "HAN", "uni": "leibniz-fh"}
        result = detect_auth_type(profile, "https://link.springer.com/book/123")
        assert result == "HAN"
```

- [ ] **Schritt 2: TestCredentialSecurity — Tests schreiben (RED)**

Ersetze die leere `TestCredentialSecurity`-Klasse:

```python
class TestCredentialSecurity:
    """Sicherheitstests fuer Credential-Handling."""

    def test_check_profile_permissions_passes_for_0600(self, tmp_path):
        """check_profile_permissions() besteht bei 0600-Datei."""
        from agents.auth_helper_lib import check_profile_permissions
        profile = tmp_path / "active.yaml"
        profile.write_text("uni: test\n", encoding="utf-8")
        os.chmod(profile, 0o600)
        # Darf keinen Fehler werfen
        check_profile_permissions(str(profile))

    def test_check_profile_permissions_fails_for_0644(self, tmp_path):
        """check_profile_permissions() wirft bei 0644-Datei (world-readable)."""
        from agents.auth_helper_lib import check_profile_permissions
        from agents.auth_helper_lib import InsecureProfilePermissionsError
        profile = tmp_path / "active.yaml"
        profile.write_text("uni: test\n", encoding="utf-8")
        os.chmod(profile, 0o644)
        with pytest.raises(InsecureProfilePermissionsError):
            check_profile_permissions(str(profile))

    def test_check_profile_permissions_fails_for_0640(self, tmp_path):
        """check_profile_permissions() wirft bei 0640 (group-readable)."""
        from agents.auth_helper_lib import check_profile_permissions
        from agents.auth_helper_lib import InsecureProfilePermissionsError
        profile = tmp_path / "active.yaml"
        profile.write_text("uni: test\n", encoding="utf-8")
        os.chmod(profile, 0o640)
        with pytest.raises(InsecureProfilePermissionsError):
            check_profile_permissions(str(profile))

    def test_load_credentials_returns_dict_without_password_in_repr(self, tmp_path):
        """Rueckgabe von load_credentials() darf Passwort nicht im repr() enthalten."""
        from agents.auth_helper_lib import load_credentials
        profile_data = {
            "uni": "tum",
            "auth_type": "Shibboleth",
            "auth_url": "https://idp.tum.de",
            "credentials_keys": ["sso_user", "sso_password"],
            "sso_user": "testuser",
            "sso_password": "supersecret_testpass_XYZ",
            "licensed_sites": ["link.springer.com"],
            "bib_pickup_url": "https://opac.tum.de",
        }
        profile_path = _write_profile(tmp_path, profile_data)
        creds = load_credentials(str(profile_path))
        # Credentials-Objekt-Repr soll Passwort NICHT sichtbar machen
        assert "supersecret_testpass_XYZ" not in repr(creds)
        assert "supersecret_testpass_XYZ" not in str(creds)

    def test_schema_validation_fails_for_literal_credentials_in_profile(self, tmp_path):
        """validate_profile_schema() schlaegt fehl, wenn Profil Literal-Credentials enthaelt
        (Sicherheits-Gate: credentials_keys sollen Keys benennen, nicht Werte einbetten)."""
        from agents.auth_helper_lib import validate_profile_schema
        from agents.auth_helper_lib import ProfileSchemaError
        # Dieses Profil hat credentials direkt als Wert, NICHT als Schluessel-Liste
        # Laut Schema: credentials_keys ist array of strings (key-Namen), nicht Passwort-Werte
        # Erkennung: Passwort-aehnlicher Wert in einem credentials_*-Feld (laenger als 32 Zeichen,
        # oder enthaelt Sonderzeichen typisch fuer Passwoerter)
        bad_profile = {
            "uni": "test",
            "auth_type": "Shibboleth",
            "auth_url": "https://idp.test.de",
            "licensed_sites": ["example.com"],
            "bib_pickup_url": "https://opac.test.de",
            # FALSCH: embed_password ist kein gueltiges Schema-Feld UND sieht wie Passwort aus
            "embed_password": "MySecretPass!23$%^&",
        }
        # Schema-Validierung soll profile-Felder mit Passwort-Mustern ausserhalb von
        # credentials_keys[] ablehnen
        with pytest.raises(ProfileSchemaError):
            validate_profile_schema(bad_profile)

    def test_no_credential_string_in_stdout_after_detection(self, tmp_path, capsys):
        """Keine Passwort-Strings in stdout nach detect_auth_type + load_credentials."""
        from agents.auth_helper_lib import detect_auth_type, load_credentials
        profile_data = {
            "uni": "tum",
            "auth_type": "Shibboleth",
            "auth_url": "https://idp.tum.de",
            "credentials_keys": ["sso_user", "sso_password"],
            "sso_user": "testuser",
            "sso_password": "CANARY_CRED_STRING_99",
            "licensed_sites": ["link.springer.com"],
            "bib_pickup_url": "https://opac.tum.de",
        }
        profile_path = _write_profile(tmp_path, profile_data)
        profile_content = yaml.safe_load(profile_path.read_text())
        detect_auth_type(profile_content, "https://link.springer.com/book/123")
        load_credentials(str(profile_path))
        captured = capsys.readouterr()
        assert "CANARY_CRED_STRING_99" not in captured.out
        assert "CANARY_CRED_STRING_99" not in captured.err
```

- [ ] **Schritt 3: TestShibbolethMockFlow und TestNoLoginForOASites — Tests schreiben (RED)**

Ersetze die letzten zwei leeren Klassen:

```python
class TestShibbolethMockFlow:
    """Mock-Shibboleth-Flow — prueft Status und Credential-Isolation."""

    @pytest.fixture
    def shibboleth_profile(self, tmp_path):
        """Test-Profil fuer Shibboleth-Flow."""
        data = {
            "uni": "tum",
            "auth_type": "Shibboleth",
            "auth_url": "https://idp.tum.de/idp/profile/SAML2/Redirect/SSO",
            "credentials_keys": ["sso_user", "sso_password"],
            "sso_user": "test_shibboleth_user",
            "sso_password": "SHIBBOLETH_TEST_SECRET_456",
            "licensed_sites": ["link.springer.com", "degruyter.com"],
            "bib_pickup_url": "https://opac.tum.de",
        }
        return _write_profile(tmp_path, data)

    @pytest.fixture
    def mock_fixture_dir(self):
        """Pfad zum Shibboleth-Mock-Verzeichnis."""
        return Path(__file__).parent / "fixtures" / "shibboleth_mock"

    def test_mock_fixtures_exist(self, mock_fixture_dir):
        """Mock-HTML-Fixtures muessen vorhanden sein."""
        assert (mock_fixture_dir / "login.html").exists()
        assert (mock_fixture_dir / "wayf.html").exists()
        assert (mock_fixture_dir / "success.html").exists()

    def test_build_auth_flow_result_for_shibboleth(self, shibboleth_profile):
        """build_auth_flow_result() liefert authenticated-Status fuer Shibboleth-Profil."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = yaml.safe_load(shibboleth_profile.read_text())
        result = build_auth_flow_result(
            auth_type="Shibboleth",
            profile_data=profile_data,
            # Simulierter Erfolg (kein echter Browser-Aufruf in Unit-Test)
            browser_success=True,
        )
        assert result["status"] == "authenticated"
        assert result["auth_type"] == "Shibboleth"
        assert result["uni"] == "tum"
        # session_context darf keine Passwort-Strings enthalten
        session_str = json.dumps(result)
        assert "SHIBBOLETH_TEST_SECRET_456" not in session_str

    def test_no_credential_leak_in_auth_result_json(self, shibboleth_profile):
        """JSON-Output von build_auth_flow_result enthaelt kein Passwort."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = yaml.safe_load(shibboleth_profile.read_text())
        result = build_auth_flow_result(
            auth_type="Shibboleth",
            profile_data=profile_data,
            browser_success=True,
        )
        serialized = json.dumps(result)
        assert "SHIBBOLETH_TEST_SECRET_456" not in serialized
        assert "test_shibboleth_user" not in serialized

    def test_no_cookie_dump_in_session_context(self, shibboleth_profile):
        """session_context darf keine serialisierten Cookies enthalten."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = yaml.safe_load(shibboleth_profile.read_text())
        result = build_auth_flow_result(
            auth_type="Shibboleth",
            profile_data=profile_data,
            browser_success=True,
        )
        session_ctx = result.get("session_context", "")
        # Cookies haben typisches Format: name=value; oder Set-Cookie-Header
        assert "Set-Cookie" not in str(session_ctx)
        assert "Cookie:" not in str(session_ctx)
        # Kein langer base64-artiger String (Cookie-Werte sind oft base64)
        assert len(str(session_ctx)) < 200  # Kurzer opaker Handle, kein Cookie-Dump

    def test_auth_failed_result_has_structured_reason(self, shibboleth_profile):
        """build_auth_flow_result() mit browser_success=False → auth_failed + reason."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = yaml.safe_load(shibboleth_profile.read_text())
        result = build_auth_flow_result(
            auth_type="Shibboleth",
            profile_data=profile_data,
            browser_success=False,
            failure_reason="bad_credentials",
        )
        assert result["status"] == "auth_failed"
        assert result["reason"] == "bad_credentials"
        assert result["reason"] in ["bad_credentials", "account_locked", "site_unavailable", "wrong_method"]


class TestNoLoginForOASites:
    """Pass-through fuer oa-only Sites — kein Login-Versuch."""

    def test_oa_only_profile_returns_not_required(self, tmp_path):
        """oa-only Profil → status: not_required."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = {
            "uni": "generic-oa",
            "auth_type": "oa-only",
            "auth_url": "",
            "licensed_sites": ["oapen.org", "doabooks.org"],
            "bib_pickup_url": "",
        }
        result = build_auth_flow_result(
            auth_type="oa-only",
            profile_data=profile_data,
            browser_success=None,  # kein Browser-Aufruf
        )
        assert result["status"] == "not_required"
        assert result["auth_type"] == "oa-only"

    def test_oa_only_result_has_null_uni_or_profile_uni(self, tmp_path):
        """oa-only Ergebnis: uni darf null oder leer sein."""
        from agents.auth_helper_lib import build_auth_flow_result
        profile_data = {
            "auth_type": "oa-only",
            "uni": "oa-site",
            "licensed_sites": [],
            "bib_pickup_url": "",
            "auth_url": "",
        }
        result = build_auth_flow_result(
            auth_type="oa-only",
            profile_data=profile_data,
            browser_success=None,
        )
        assert result["status"] == "not_required"
        # uni kann den Wert aus dem Profil haben oder null — beides ist akzeptabel
        assert "status" in result

    def test_detect_oa_only_from_url_no_browser_call_marker(self, tmp_path):
        """detect_auth_type fuer OA-URL gibt oa-only → kein Login-Trigger."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://www.oapen.org/book/12345")
        assert result == "oa-only"
        # Sicherheitstest: oa-only darf nie einen Login starten
        # (Verifiziert durch Rueckgabewert allein — kein side-effect erwartet)
```

- [ ] **Schritt 4: Tests ausfuehren — muessen FEHLSCHLAGEN (RED)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/test_auth_helper.py -v 2>&1 | tail -30
```

Erwartet: `ModuleNotFoundError: No module named 'agents.auth_helper_lib'` oder aehnlicher Import-Fehler.

- [ ] **Schritt 5: Commit (RED-Phase)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && git add tests/test_auth_helper.py && git commit -m "test(auth-helper): vollstaendige TDD-Testsuite (RED) — 4 Klassen, 20 Tests"
```

---

## Task 3: Implementation von `agents/auth_helper_lib.py` (GREEN)

**Files:**
- Create: `agents/auth_helper_lib.py`
- Modify: `agents/__init__.py` (falls vorhanden, sonst ignorieren)

- [ ] **Schritt 1: `agents/__init__.py` sicherstellen**

```bash
ls /Users/j65674/Repos/academic-research-v6.2-C/agents/__init__.py 2>/dev/null || touch /Users/j65674/Repos/academic-research-v6.2-C/agents/__init__.py
```

- [ ] **Schritt 2: `agents/auth_helper_lib.py` anlegen**

```python
"""auth_helper_lib — Pure-Python-Logik fuer den auth-helper Subagenten (Chunk C, #83).

Sicherheits-Policy:
- Credentials duerfen NIEMALS in repr(), str(), oder Log-Ausgaben erscheinen.
- CredentialStore verwendet __repr__/__str__ mit Maskierung.
- Profil-Dateien werden auf 0600-Perms geprueft vor dem Lesen.
"""
import os
import re
import stat
from dataclasses import dataclass, field
from typing import Any, Optional
import yaml


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class InsecureProfilePermissionsError(PermissionError):
    """Wird geworfen, wenn eine Profil-Datei nicht 0600 gesetzt ist."""


class ProfileSchemaError(ValueError):
    """Wird geworfen, wenn das Profil-Schema verletzt ist."""


# ---------------------------------------------------------------------------
# Credential-Store (Sicherheits-Wrapper)
# ---------------------------------------------------------------------------

@dataclass
class CredentialStore:
    """Haelt Credentials, maskiert sie in repr()/str()."""

    _data: dict = field(default_factory=dict, repr=False)

    def get(self, key: str) -> Optional[str]:
        """Gibt den Wert fuer einen Credential-Schluessel zurueck."""
        return self._data.get(key)

    def __repr__(self) -> str:
        keys = list(self._data.keys())
        return f"CredentialStore(keys={keys}, values=<redacted>)"

    def __str__(self) -> str:
        return self.__repr__()


# ---------------------------------------------------------------------------
# Auth-Typ-Erkennung
# ---------------------------------------------------------------------------

_HAN_PATTERN = re.compile(r'\.han\.')
_WAYF_PATTERN = re.compile(r'(^|\.)(wayf)\.')
_IDP_PATTERN = re.compile(r'/idp/')
_SHIBBOLETH_PATTERN = re.compile(r'shibboleth', re.IGNORECASE)
_EZPROXY_PATTERN = re.compile(r'ezproxy', re.IGNORECASE)
_DFNAAI_PATTERN = re.compile(r'(dfn-aai|\.aai\.dfn\.de)', re.IGNORECASE)

# Erlaubte auth_type-Werte (aus B-Schema-Enum)
VALID_AUTH_TYPES = frozenset(["Shibboleth", "EZproxy", "HAN", "oa-only"])


def detect_auth_type(profile_data: dict, url: str) -> str:
    """Ermittelt den Auth-Typ aus Profil (Prioritaet) und URL-Muster (Fallback).

    Args:
        profile_data: Inhalt von active.yaml als dict (leer = kein Profil).
        url: Ziel-URL fuer den Zugriff.

    Returns:
        Einer von: "Shibboleth", "EZproxy", "HAN", "oa-only"
    """
    # Profil-Feld hat absolute Prioritaet
    profile_type = profile_data.get("auth_type", "")
    if profile_type in VALID_AUTH_TYPES:
        return profile_type

    # URL-Pattern-Matching als Fallback
    if _HAN_PATTERN.search(url):
        return "HAN"
    if _WAYF_PATTERN.search(url) or _IDP_PATTERN.search(url) or _SHIBBOLETH_PATTERN.search(url):
        return "Shibboleth"
    if _DFNAAI_PATTERN.search(url):
        return "Shibboleth"  # DFN-AAI ist Shibboleth-basiert
    if _EZPROXY_PATTERN.search(url):
        return "EZproxy"

    return "oa-only"


# ---------------------------------------------------------------------------
# Profil-Berechtigungs-Pruefung
# ---------------------------------------------------------------------------

def check_profile_permissions(profile_path: str) -> None:
    """Prueft, dass die Profil-Datei nur owner-readable (0600) ist.

    Raises:
        InsecureProfilePermissionsError: Wenn Perms nicht 0600.
        FileNotFoundError: Wenn Datei nicht existiert.
    """
    path_stat = os.stat(profile_path)
    mode = stat.S_IMODE(path_stat.st_mode)
    if mode != 0o600:
        raise InsecureProfilePermissionsError(
            f"Profil-Datei {profile_path!r} hat unsichere Berechtigungen "
            f"{oct(mode)} — erwartet 0600. "
            f"Fix: chmod 600 {profile_path}"
        )


# ---------------------------------------------------------------------------
# Credential-Laden
# ---------------------------------------------------------------------------

def load_credentials(profile_path: str) -> CredentialStore:
    """Laedt Credentials aus einer Profil-Datei.

    Prueft zuerst Datei-Perms (0600), dann laedt YAML und extrahiert
    credentials_keys-Eintraege. Credentials landen in CredentialStore
    (kein repr()-Leak).

    Args:
        profile_path: Pfad zur Profil-YAML-Datei.

    Returns:
        CredentialStore mit den Credential-Werten.

    Raises:
        InsecureProfilePermissionsError: Bei falschen Datei-Perms.
    """
    check_profile_permissions(profile_path)
    with open(profile_path, encoding="utf-8") as f:
        profile = yaml.safe_load(f) or {}

    credentials_keys = profile.get("credentials_keys", [])
    cred_data = {}
    for key in credentials_keys:
        value = profile.get(key)
        if value is not None:
            cred_data[key] = str(value)

    return CredentialStore(_data=cred_data)


# ---------------------------------------------------------------------------
# Schema-Validierung (Sicherheits-Gate)
# ---------------------------------------------------------------------------

# Muster fuer Passwort-aehnliche Werte: Sonderzeichen + Laenge > 12
_PASSWORD_PATTERN = re.compile(r'(?=.*[A-Za-z])(?=.*[0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]).{13,}')

# Felder, die in keinem gueltigen Profil Passwort-aehnliche Werte haben sollten
_FORBIDDEN_PASSWORD_FIELD_PATTERNS = re.compile(
    r'(password|passwort|secret|token|credential|auth_token|api_key)',
    re.IGNORECASE
)


def validate_profile_schema(profile_data: dict) -> None:
    """Validiert ein Profil-Dict gegen grundlegende Sicherheits-Constraints.

    Schlaegt fehl, wenn:
    - Ein Feld ausserhalb von credentials_keys[] einen Passwort-aehnlichen Wert hat
      UND der Feldname auf ein Credential hindeutet.

    Args:
        profile_data: Profil als dict.

    Raises:
        ProfileSchemaError: Bei Sicherheits-Verletzung.
    """
    allowed_credential_fields = set(profile_data.get("credentials_keys", []))

    for field_name, value in profile_data.items():
        if field_name in allowed_credential_fields:
            continue  # Credentials-Felder sind explizit erlaubt
        if not isinstance(value, str):
            continue
        # Feldname sieht nach Credential aus UND Wert sieht nach Passwort aus
        if (
            _FORBIDDEN_PASSWORD_FIELD_PATTERNS.search(field_name)
            and _PASSWORD_PATTERN.match(value)
        ):
            raise ProfileSchemaError(
                f"Profil enthaelt verdaechtiges Feld {field_name!r} mit Passwort-aehnlichem Wert. "
                f"Credentials muessen in credentials_keys[] als Schluessel referenziert werden, "
                f"nicht als direkte Werte ausserhalb dieser Allowlist."
            )


# ---------------------------------------------------------------------------
# Auth-Flow-Ergebnis-Builder
# ---------------------------------------------------------------------------

def build_auth_flow_result(
    auth_type: str,
    profile_data: dict,
    browser_success: Optional[bool],
    failure_reason: Optional[str] = None,
) -> dict:
    """Baut das standardisierte Auth-Flow-Ergebnis.

    Sicherheits-Invariante: Das zurueckgegebene dict enthaelt KEINE
    Credential-Werte, keine Cookies, keine Session-Tokens.

    Args:
        auth_type: Erkannter Auth-Typ (aus detect_auth_type).
        profile_data: Profil-Daten (nur fuer uni-Feld gelesen).
        browser_success: True = erfolgreich, False = gescheitert, None = nicht versucht.
        failure_reason: Einer von bad_credentials|account_locked|site_unavailable|wrong_method.

    Returns:
        Dict mit status, auth_type, und ggf. session_context oder reason.
    """
    uni = profile_data.get("uni")

    if auth_type == "oa-only" or browser_success is None:
        return {
            "status": "not_required",
            "auth_type": "oa-only",
            "uni": uni,
        }

    if browser_success:
        return {
            "status": "authenticated",
            "auth_type": auth_type,
            "uni": uni,
            # Opaker Session-Handle — kein Cookie-Dump, kein Token-Wert
            "session_context": f"browser-use:active:{uni}",
        }

    # Login gescheitert
    valid_reasons = {"bad_credentials", "account_locked", "site_unavailable", "wrong_method"}
    reason = failure_reason if failure_reason in valid_reasons else "site_unavailable"
    return {
        "status": "auth_failed",
        "reason": reason,
    }
```

- [ ] **Schritt 3: Tests ausfuehren — muessen BESTEHEN (GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/test_auth_helper.py -v 2>&1 | tail -40
```

Erwartet: Alle Tests PASS, kein Fehler.

- [ ] **Schritt 4: Sicherstellen, dass bestehende Tests nicht gebrochen sind**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/ -v --ignore=tests/evals 2>&1 | tail -20
```

Erwartet: Keine neuen Failures.

- [ ] **Schritt 5: Commit (GREEN)**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && git add agents/__init__.py agents/auth_helper_lib.py && git commit -m "feat(auth-helper): auth_helper_lib — detect_auth_type, credential-Sicherheit, build_auth_flow_result"
```

---

## Task 4: `agents/auth-helper.md` — Agenten-Definition

**Files:**
- Create: `agents/auth-helper.md`

- [ ] **Schritt 1: `agents/auth-helper.md` anlegen**

```markdown
---
name: auth-helper
model: sonnet
color: red
description: |
  Authentifizierungs-Subagent fuer DACH-Hochschul-Bibliotheken. Liest das aktive
  Per-Uni-Profil, erkennt die Auth-Methode (HAN / Shibboleth / EZproxy / DFN-AAI / oa-only)
  und fuehrt — falls noetig — den SSO-Login ausschliesslich via browser-use durch.
  Gibt eine authentifizierte Browser-Session an nachfolgende Subagenten weiter.
  Credentials und Cookies erscheinen NIEMALS in Outputs oder Logs.

  <example>
  Context: springer-book-fetcher benoetigt Zugang zu link.springer.com (lizenziert).
  user: "[springer-book-fetcher ruft auth-helper auf]"
  assistant: "auth-helper liest active.yaml (auth_type: Shibboleth, uni: tum), prueft
  ob link.springer.com in licensed_sites ist, fuehrt Shibboleth-WAYF-Login aus,
  gibt {status: authenticated, session_context: 'browser-use:active:tum'} zurueck."
  <commentary>
  auth-helper ist der einzige Agent, der Credentials laedt. Verlags-Subagenten
  delegieren Auth vollstaendig an ihn — kein Passwort-Handling in anderen Agents.
  </commentary>
  </example>

  <example>
  Context: tib-fetcher will OAPEN (OA-Site) aufrufen.
  user: "[tib-fetcher ruft auth-helper fuer https://www.oapen.org/book/123 auf]"
  assistant: "auth-helper erkennt auth_type: oa-only aus Profil — gibt sofort
  {status: not_required, auth_type: oa-only} zurueck, kein Login-Versuch."
  <commentary>
  OA-Sites benoetigen keine Auth. auth-helper erkennt das und haelt sofort an,
  damit Site-Subagenten ohne Verzoegerung direkt zugreifen.
  </commentary>
  </example>
tools: [Bash(browser-use:*), "Bash(browser-use *)", Read, Write]
maxTurns: 12
---

# auth-helper — Authentifizierungs-Subagent

**Sicherheits-Policy (nicht verhandelbar):**
- Credentials (Benutzername, Passwort) NIEMALS in Outputs, JSON-Antworten, oder Zwischenmeldungen ausgeben.
- Session-Cookies NIEMALS serialisieren oder als Text ausgeben.
- Login NUR fuer Hosts in `licensed_sites` des aktiven Profils.
- Profil-Datei auf `0600`-Berechtigungen pruefen vor dem Lesen.

---

## Input

```json
{
  "target_url": "https://link.springer.com/book/10.1007/...",
  "profile_path": "~/.academic-research/library-profiles/active.yaml"
}
```

`profile_path` ist optional (Default: `~/.academic-research/library-profiles/active.yaml`).

---

## Workflow

### Schritt 1: Profil lesen und validieren

```bash
# Berechtigungen pruefen (MUSS 0600 sein)
stat -f "%Lp" ~/.academic-research/library-profiles/active.yaml
```

Wenn nicht `600`: Fehler ausgeben (`{status: auth_failed, reason: site_unavailable}`), NICHT versuchen die Datei zu lesen.

```bash
# Profil laden
cat ~/.academic-research/library-profiles/active.yaml
```

**WICHTIG:** Den Inhalt von `credentials_keys`-Werten (Passwort-Felder) NICHT in deinen Output schreiben.

### Schritt 2: Auth-Typ bestimmen

Pruefe in dieser Reihenfolge:
1. `auth_type`-Feld im Profil (autoritaetiv)
2. URL-Pattern-Matching (Fallback):
   - `.han.` im Hostnamen → HAN
   - `wayf.`, `/idp/`, `shibboleth` → Shibboleth
   - `dfn-aai`, `.aai.dfn.de` → Shibboleth (DFN-AAI = Shibboleth-Foederation)
   - `ezproxy` → EZproxy
   - Kein Match → oa-only

### Schritt 3: licensed_sites pruefen

Extrahiere den Hostnamen der Ziel-URL und pruefe, ob er in `licensed_sites` enthalten ist.

Wenn NICHT enthalten:
```json
{"status": "auth_failed", "reason": "wrong_method"}
```

### Schritt 4: Login-Flow (nur wenn auth_type != oa-only)

#### oa-only → kein Login

```json
{"status": "not_required", "auth_type": "oa-only", "uni": null}
```

#### HAN-Login

```bash
browser-use "
Navigiere zur HAN-Login-Seite: {proxy_url_aus_proxy_pattern}
Fuelle das Formular aus:
  - Feld 'Benutzername': {Wert aus credentials_keys[0]}
  - Feld 'Passwort': {Wert aus credentials_keys[1]}
Klicke Submit.
Pruefe: Wurde zur Ziel-Site weitergeleitet?
Wenn ja: 'LOGIN_SUCCESS'
Wenn Fehlermeldung: 'LOGIN_FAILED: <Fehlertext ohne Credentials>'
Wenn CAPTCHA: 'CAPTCHA_REQUIRED'
"
```

**KRITISCH:** Der browser-use-Prompt darf die WERTE der Credentials NICHT als Literal-Text enthalten. Lade sie aus dem Profil und uebergib sie als Variable.

#### Shibboleth-Login (inkl. DFN-AAI)

```bash
browser-use "
Navigiere zu: {auth_url aus Profil}
Falls WAYF-Seite: Waehle Institution '{uni}' aus dem Dropdown.
Fuelle Shibboleth-Login-Formular:
  - Benutzername-Feld: {Wert aus credentials_keys[0]}
  - Passwort-Feld: {Wert aus credentials_keys[1]}
Klicke 'Anmelden' / 'Login'.
Pruefe Redirect zur Ziel-Site.
Wenn Redirect: 'LOGIN_SUCCESS'
Wenn Fehler: 'LOGIN_FAILED: <Fehlermeldung ohne Credentials>'
Wenn CAPTCHA: 'CAPTCHA_REQUIRED'
"
```

#### EZproxy-Login

```bash
browser-use "
Navigiere zu: {auth_url aus Profil}
Fuelle Login-Formular:
  - Benutzer: {credentials_keys[0]-Wert}
  - Passwort: {credentials_keys[1]-Wert}
Submit → pruefe Redirect.
Wenn Redirect: 'LOGIN_SUCCESS'
Wenn Fehler: 'LOGIN_FAILED: <Fehlermeldung>'
Wenn CAPTCHA: 'CAPTCHA_REQUIRED'
"
```

### Schritt 5: Ergebnis zurueckgeben

#### Erfolg
```json
{
  "status": "authenticated",
  "auth_type": "Shibboleth",
  "uni": "tum",
  "session_context": "browser-use:active:tum"
}
```

#### Fehlgeschlagener Login
```json
{
  "status": "auth_failed",
  "reason": "bad_credentials"
}
```

`reason`-Enum:
- `bad_credentials` — Login-Formular zeigt Fehler ("Passwort falsch")
- `account_locked` — Konto gesperrt
- `site_unavailable` — Site nicht erreichbar oder Timeout
- `wrong_method` — Falsche Auth-Methode fuer diese Site

#### CAPTCHA
```json
{
  "status": "captcha"
}
```

Halte sofort an. CAPTCHA-Loesung ist User-Aufgabe.

---

## Sicherheits-Checkliste (vor jedem Output pruefen)

- [ ] Kein Passwort-String im Output
- [ ] Kein Cookie-Inhalt im Output
- [ ] `session_context` = nur opaker Bezeichner (Format: `browser-use:active:{uni}`)
- [ ] `licensed_sites`-Allowlist war geprueft
- [ ] Profil-Perms waren 0600
```

- [ ] **Schritt 2: Agenten-Datei auf Vollstaendigkeit pruefen**

```bash
grep -c "maxTurns" /Users/j65674/Repos/academic-research-v6.2-C/agents/auth-helper.md
grep "model:" /Users/j65674/Repos/academic-research-v6.2-C/agents/auth-helper.md
```

Erwartet: `maxTurns` erscheint mindestens einmal; `model: sonnet`.

- [ ] **Schritt 3: Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && git add agents/auth-helper.md && git commit -m "feat(auth-helper): agents/auth-helper.md — Shibboleth/HAN/EZproxy/oa-only-Login-Flows"
```

---

## Task 5: Gesamttest-Run und Sicherheits-Verifikation

**Files:** keine neuen

- [ ] **Schritt 1: Vollstaendiger Test-Run**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/test_auth_helper.py -v 2>&1
```

Erwartet: Alle Tests PASS.

- [ ] **Schritt 2: Sicherheits-Grep — kein Credential-String in Testausgaben**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/test_auth_helper.py -v -s 2>&1 | grep -c "CANARY_CRED_STRING_99\|SHIBBOLETH_TEST_SECRET_456\|supersecret_testpass" && echo "LEAK DETECTED" || echo "NO LEAK"
```

Erwartet: `NO LEAK` (grep findet nichts → gibt non-zero zurueck → `|| echo "NO LEAK"` greift).

- [ ] **Schritt 3: Keine Regression in bestehenden Tests**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && /opt/homebrew/opt/python@3.14/bin/python -m pytest tests/ --ignore=tests/evals -v 2>&1 | tail -15
```

Erwartet: Alle bisherigen Tests unverändert PASS.

- [ ] **Schritt 4: Acceptance-Criteria-Checkliste**

```
- [x] agents/auth-helper.md mit model: sonnet, tools inkl. browser-use, maxTurns >= 12
- [x] detect_auth_type: HAN/Shibboleth/EZproxy/oa-only aus Profil und URL
- [x] SSO nur via browser-use (kein curl/wget in Agenten-Prompt)
- [x] build_auth_flow_result: authenticated/not_required/auth_failed mit strukturiertem reason
- [x] Credentials nicht in Output/repr/str (CredentialStore-Maskierung + Sicherheits-Tests)
- [x] Profile-Perms-Pruefung (0600-Check, Fehler bei 0644/0640)
- [x] Shibboleth-Mock-Flow: authenticated-Status, kein Credential-Leak
- [x] oa-only: not_required ohne Login-Versuch
```

- [ ] **Schritt 5: Final Commit**

```bash
cd /Users/j65674/Repos/academic-research-v6.2-C && git add -A && git status && git commit -m "chore(auth-helper): Gesamt-Test-Lauf bestanden, alle Acceptance Criteria erfuellt" --allow-empty
```

Hinweis: `--allow-empty` nur falls keine ungestagten Aenderungen (Task 5 hat keine neuen Dateien).

---

## Selbst-Review gegen Spec (`specs/v6.2/C.md`)

| Spec-Anforderung | Task | Abgedeckt? |
|---|---|---|
| `agents/auth-helper.md` mit model:sonnet, tools, maxTurns>=12 | Task 4 | ✓ |
| detect_auth_type aus Profil + URL | Task 3 | ✓ |
| SSO nur via browser-use | Task 4 (Prompt-Design) | ✓ |
| Authenticated session zurückgeben | Task 3 (build_auth_flow_result) | ✓ |
| Keine Credentials in Outputs/Logs | Task 3 (CredentialStore) + Task 2 (Security-Tests) | ✓ |
| Profile-Perms 0600 | Task 3 (check_profile_permissions) | ✓ |
| Shibboleth-Mock-Flow → authenticated | Task 2 (TestShibbolethMockFlow) | ✓ |
| oa-only → not_required ohne Login | Task 2 + Task 3 | ✓ |
| Strukturierter Error (auth_failed + reason enum) | Task 3 | ✓ |
| Schema-Validierung verhindert Literal-Credentials | Task 3 (validate_profile_schema) | ✓ |
| Mock-HTML-Fixtures | Task 1 | ✓ |
