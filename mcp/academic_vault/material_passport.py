"""Material Passport Builder und JSON-Schema-Validation (v6.4, Ticket #104).

Erstellt einen Material-Passport-Dict und validiert ihn gegen das JSON-Schema
in material-passport.schema.json.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

_SCHEMA_FILE = Path(__file__).parent / "material-passport.schema.json"


def build_passport(
    slug: str,
    paper_ids: list[str],
    dois: list[str],
    scores_5d: dict[str, Any],
    score_algo_version: str,
    plugin_version: str,
    model_versions: dict[str, str],
    per_uni_profile_hash: Optional[str],
    decisions_snapshot: list[dict],
    pdf_hashes: dict[str, str],
) -> dict:
    """Erstellt den Material-Passport-Dict.

    Der passport_hash wird ueber alle uebrigen Felder berechnet.
    """
    passport: dict[str, Any] = {
        "slug": slug,
        "paper_ids": paper_ids,
        "dois": dois,
        "download_tier": "full" if pdf_hashes else "metadata-only",
        "scores_5d": scores_5d,
        "score_algo_version": score_algo_version,
        "plugin_version": plugin_version,
        "model_versions": model_versions,
        "per_uni_profile_hash": per_uni_profile_hash,
        "decisions_snapshot": decisions_snapshot,
        "pdf_sha256_hashes": pdf_hashes,
        "created_at": int(time.time()),
    }
    # Hash ueber serialisiertes Passport-Dict (ohne passport_hash selbst)
    passport_bytes = json.dumps(passport, sort_keys=True, ensure_ascii=False).encode("utf-8")
    passport["passport_hash"] = hashlib.sha256(passport_bytes).hexdigest()
    return passport


def validate_passport(data: dict) -> None:
    """Validiert passport-Dict gegen das JSON-Schema.

    Wirft jsonschema.ValidationError bei Fehler.
    Wirft ImportError wenn jsonschema nicht installiert ist — dann wird
    Validierung uebersprungen (soft-fail).
    """
    try:
        import jsonschema
    except ImportError:
        # jsonschema nicht installiert — Validierung uebersprungen
        return

    schema = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
