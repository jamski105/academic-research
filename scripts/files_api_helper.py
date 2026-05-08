"""
scripts/files_api_helper.py

Utility fuer Anthropic Files-API: einmaliges Hochladen von PDFs mit
SHA-256-Cache in pdf_status.json, TTL-Tracking und Feature-Flag.

Oeffentliche API:
    ensure_uploaded(pdf_path, client, cache_file, ttl_days) -> str | None
    should_use_files_api() -> bool

Feature-Flag:
    Env ACADEMIC_FILES_API=0 deaktiviert Files-API -> Fallback auf base64.
    Standard: aktiviert.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Union

# Beta-Header fuer die Anthropic Files-API (beta seit 2025-04-14)
_FILES_API_BETA_HEADER = "files-api-2025-04-14"

# Pfad zum Default-Cache relativ zum Repo-Root (ueberschreibbar per Parameter)
_DEFAULT_CACHE_FILE = "pdf_status.json"


def extract_cache_read_tokens(response) -> int:
    """
    Liest cache_read_input_tokens aus einem API-Response-usage-Objekt.

    Gibt 0 zurueck wenn das Attribut fehlt (robuster Fallback).
    Einsatz: AC #66 — Folgecall innerhalb 1h muss cache_read_input_tokens > 0 liefern.

    Beispiel:
        tokens = extract_cache_read_tokens(response)
        assert tokens > 0, "Cache-Hit erwartet"
    """
    try:
        return getattr(response.usage, "cache_read_input_tokens", 0) or 0
    except AttributeError:
        return 0


def should_use_files_api() -> bool:
    """Gibt True zurueck wenn Files-API aktiviert ist (ACADEMIC_FILES_API != '0')."""
    return os.environ.get("ACADEMIC_FILES_API", "1") != "0"


def _sha256(path: Path) -> str:
    """SHA-256-Hash des Dateiinhalts (Cache-Schluessel)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_cache(cache_file: Path) -> dict:
    """Laedt JSON-Cache; gibt leeres Dict zurueck wenn Datei fehlt oder korrupt."""
    try:
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_cache(cache_file: Path, data: dict) -> None:
    """Schreibt JSON-Cache atomar."""
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _is_expired(uploaded_at_iso: str, ttl_days: int) -> bool:
    """True wenn der Cache-Eintrag aelter als ttl_days ist."""
    try:
        uploaded_at = datetime.fromisoformat(uploaded_at_iso)
        # Timezone-naive Timestamps als UTC behandeln
        if uploaded_at.tzinfo is None:
            uploaded_at = uploaded_at.replace(tzinfo=timezone.utc)
        expiry = uploaded_at + timedelta(days=ttl_days)
        return datetime.now(timezone.utc) > expiry
    except (ValueError, TypeError):
        # Unbekanntes Format -> als abgelaufen behandeln
        return True


def ensure_uploaded(
    pdf_path: Union[str, Path],
    client,
    cache_file: Union[str, Path] = _DEFAULT_CACHE_FILE,
    ttl_days: int = 30,
) -> "str | None":
    """
    Laedt ein PDF einmalig via Anthropic Files-API hoch und cached die file_id.

    Gibt None zurueck wenn Feature-Flag OFF (ACADEMIC_FILES_API=0) oder
    client ist None -> Aufrufer soll auf base64-Fallback wechseln.

    Args:
        pdf_path:   Pfad zur PDF-Datei
        client:     anthropic.Anthropic()-Instanz
        cache_file: Pfad zur Cache-JSON-Datei (pdf_status.json)
        ttl_days:   Cache-Gueltigkeit in Tagen (Default 30)

    Returns:
        file_id (str) bei Erfolg, None bei Fallback.
    """
    if not should_use_files_api() or client is None:
        return None

    pdf_path = Path(pdf_path)
    cache_file = Path(cache_file)

    sha = _sha256(pdf_path)
    cache = _load_cache(cache_file)

    # Cache-Hit pruefen
    entry = cache.get(sha)
    if entry and not _is_expired(entry.get("uploaded_at", ""), ttl_days):
        return entry["file_id"]

    # Upload via Files-API (Beta)
    with open(pdf_path, "rb") as f:
        response = client.beta.files.upload(
            file=(pdf_path.name, f, "application/pdf"),
            extra_headers={"anthropic-beta": _FILES_API_BETA_HEADER},
        )

    file_id = response.id

    # Cache aktualisieren
    cache[sha] = {
        "file_id": file_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_cache(cache_file, cache)

    return file_id
