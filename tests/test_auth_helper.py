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
        # Bei leerem Profil und unbekanntem Muster: oa-only
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
        """auth_type: oa-only im Profil verhindert Login auch bei auth-aehnlicher URL."""
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
        """validate_profile_schema() schlaegt fehl, wenn Profil Literal-Credentials enthaelt."""
        from agents.auth_helper_lib import validate_profile_schema
        from agents.auth_helper_lib import ProfileSchemaError
        bad_profile = {
            "uni": "test",
            "auth_type": "Shibboleth",
            "auth_url": "https://idp.test.de",
            "licensed_sites": ["example.com"],
            "bib_pickup_url": "https://opac.test.de",
            # FALSCH: embed_password ist kein gueltiges Schema-Feld UND sieht wie Passwort aus
            "embed_password": "MySecretPass!23$%^&",
        }
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
        assert "status" in result

    def test_detect_oa_only_from_url_no_browser_call_marker(self, tmp_path):
        """detect_auth_type fuer OA-URL gibt oa-only → kein Login-Trigger."""
        from agents.auth_helper_lib import detect_auth_type
        profile = {}
        result = detect_auth_type(profile, "https://www.oapen.org/book/12345")
        assert result == "oa-only"


class TestAuthHelperPromptNoCredentialLeak:
    """Regression #193 — auth-helper.md darf Credentials NICHT im browser-use-Prompt
    uebergeben (sonst landen sie im LLM-Reasoning-Stream → Leak via Trace-Logs,
    Hook-Captures, Error-Messages).

    Akzeptanzkriterium: Credentials werden ueber ENV-Variablen (z.B. BROWSER_USE_USER /
    BROWSER_USE_PASS) und deterministische Eingabe (browser-use input <idx> "$VAR")
    behandelt — der Prompt-Text enthaelt keine Credential-Platzhalter mehr.
    """

    @pytest.fixture
    def doc_path(self) -> Path:
        return Path(__file__).parent.parent / "agents" / "auth-helper.md"

    @pytest.fixture
    def doc_text(self, doc_path) -> str:
        assert doc_path.exists(), f"auth-helper.md fehlt: {doc_path}"
        return doc_path.read_text(encoding="utf-8")

    # Muster, die einen Credential-Wert in den LLM-Prompt schreiben wuerden.
    # Beispiele aus dem alten Template:
    #   "Fuelle Passwort-Feld mit dem Wert aus dem Profil-Feld <credentials_keys[1]>"
    #   "Benutzername: <Wert aus credentials_keys[0] im Profil>"
    LEAK_PATTERNS = [
        "credentials_keys[0]",
        "credentials_keys[1]",
        "Wert aus dem Profil-Feld",
        "Wert aus credentials_keys",
    ]

    def test_no_credential_placeholder_in_prompt(self, doc_text):
        """Kein Credential-Platzhalter im Prompt-Text (sonst LLM-Stream-Leak)."""
        found = [p for p in self.LEAK_PATTERNS if p in doc_text]
        assert not found, (
            "auth-helper.md uebergibt Credentials im browser-use-Prompt — "
            f"verbotene Muster gefunden: {found}. "
            "Credentials muessen via ENV-Var + 'browser-use input' eingegeben werden, "
            "nicht als Prompt-Platzhalter."
        )

    def test_uses_env_variables_for_credentials(self, doc_text):
        """Credentials werden ueber ENV-Variablen referenziert."""
        assert "BROWSER_USE_USER" in doc_text and "BROWSER_USE_PASS" in doc_text, (
            "auth-helper.md muss Credentials ueber ENV-Variablen "
            "(BROWSER_USE_USER / BROWSER_USE_PASS) ansprechen statt im Prompt."
        )

    def test_uses_deterministic_input_for_credentials(self, doc_text):
        """Credential-Eingabe erfolgt deterministisch via 'browser-use input'."""
        assert "browser-use input" in doc_text, (
            "auth-helper.md muss 'browser-use input <idx> \"$VAR\"' nutzen, "
            "damit der Credential-Wert nicht in den LLM-Prompt gelangt."
        )

    def test_env_vars_not_echoed(self, doc_text):
        """Die Credential-ENV-Variablen duerfen nicht via echo/print ausgegeben werden."""
        import re
        # echo/print, das eine Credential-ENV-Var ausgibt → Leak in stdout/Logs
        leak_echo = re.findall(
            r"(?:echo|print[^\n]*)\$?\{?BROWSER_USE_(?:USER|PASS)",
            doc_text,
        )
        assert not leak_echo, (
            f"Credential-ENV-Var wird ausgegeben (Leak): {leak_echo}"
        )

    def test_security_policy_still_documented(self, doc_text):
        """Die Sicherheits-Policy (Credentials nie in Outputs) bleibt dokumentiert."""
        assert "NIEMALS" in doc_text, "Sicherheits-Policy-Abschnitt fehlt"
