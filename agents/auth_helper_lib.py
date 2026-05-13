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
from typing import Optional
from urllib.parse import urlparse
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

_HAN_HOSTNAME_PATTERN = re.compile(r'\.han\.')
_WAYF_HOSTNAME_PATTERN = re.compile(r'(^|\.)(wayf)\.')
_IDP_PATH_PATTERN = re.compile(r'/idp/')
_EZPROXY_HOSTNAME_PATTERN = re.compile(r'ezproxy', re.IGNORECASE)

# Erlaubte auth_type-Werte (aus B-Schema-Enum)
VALID_AUTH_TYPES = frozenset(["Shibboleth", "EZproxy", "HAN", "oa-only"])


def detect_auth_type(profile_data: dict, url: str) -> str:
    """Ermittelt den Auth-Typ aus Profil (Prioritaet) und URL-Muster (Fallback).

    Matching-Strategie: Hostname und Pfad werden separat ausgewertet, um
    False-Positives bei Substrings zu vermeiden.

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

    # URL parsen fuer robustes Hostname-Matching
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        path = parsed.path or ""
    except Exception:
        hostname = ""
        path = ""

    # URL-Pattern-Matching als Fallback (Hostname-basiert)
    if _HAN_HOSTNAME_PATTERN.search(hostname):
        return "HAN"
    if _WAYF_HOSTNAME_PATTERN.search(hostname):
        return "Shibboleth"
    if _IDP_PATH_PATTERN.search(path):
        return "Shibboleth"
    if _EZPROXY_HOSTNAME_PATTERN.search(hostname):
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
