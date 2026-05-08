"""
tests/test_files_api_helper.py

TDD-Tests fuer scripts/files_api_helper.py (Chunk B, Ticket #65 + #66).

Manuelle Token-Vergleichs-Doku (AC -75%):
    Architektonisch garantiert: file_id ist ein ~20-Zeichen-String, base64 eines
    5-MB-PDFs ergibt ~100k Input-Tokens. Token-Ersparnis >> 75%.
    Zum manuellen Verifizieren:
        export ANTHROPIC_API_KEY=...
        python -c "
        from scripts.files_api_helper import ensure_uploaded
        import anthropic
        c = anthropic.Anthropic()
        fid = ensure_uploaded('tests/fixtures/sample.pdf', c)
        print('file_id:', fid)
        "
    Dann zwei API-Calls mit resp.usage vergleichen (base64 vs. file_id).
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes() -> bytes:
    """Minimales gültiges PDF (PDF-Magie-Bytes + EOF)."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


def _write_pdf(tmp_path: Path, content: bytes = None) -> Path:
    p = tmp_path / "test.pdf"
    p.write_bytes(content or _make_pdf_bytes())
    return p


def _make_client_mock(file_id: str = "file_abc123") -> MagicMock:
    """Mock-Anthropic-Client mit funktionierendem beta.files.upload."""
    client = MagicMock()
    upload_result = MagicMock()
    upload_result.id = file_id
    client.beta.files.upload.return_value = upload_result
    return client


# ---------------------------------------------------------------------------
# Test 1: Cache-Miss loest Upload aus
# ---------------------------------------------------------------------------

def test_cache_miss_triggers_upload(tmp_path):
    from scripts.files_api_helper import ensure_uploaded

    pdf = _write_pdf(tmp_path)
    cache_file = tmp_path / "pdf_status.json"
    client = _make_client_mock("file_new_001")

    result = ensure_uploaded(pdf, client, cache_file=cache_file)

    assert result == "file_new_001"
    client.beta.files.upload.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: Cache-Hit verhindert Re-Upload
# ---------------------------------------------------------------------------

def test_cache_hit_skips_upload(tmp_path):
    from scripts.files_api_helper import ensure_uploaded
    import hashlib

    pdf = _write_pdf(tmp_path)
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    cache_file = tmp_path / "pdf_status.json"

    # Cache vorher befüllen
    cache_data = {
        sha: {
            "file_id": "file_cached_999",
            "uploaded_at": "2099-01-01T00:00:00",  # weit in der Zukunft
        }
    }
    cache_file.write_text(json.dumps(cache_data))

    client = _make_client_mock()

    result = ensure_uploaded(pdf, client, cache_file=cache_file, ttl_days=30)

    assert result == "file_cached_999"
    client.beta.files.upload.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: TTL-Ablauf loest Re-Upload aus
# ---------------------------------------------------------------------------

def test_ttl_expiry_triggers_reupload(tmp_path):
    from scripts.files_api_helper import ensure_uploaded
    import hashlib

    pdf = _write_pdf(tmp_path)
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    cache_file = tmp_path / "pdf_status.json"

    # Cache-Eintrag ist 40 Tage alt (> ttl_days=30)
    cache_data = {
        sha: {
            "file_id": "file_old_expired",
            "uploaded_at": "2025-01-01T00:00:00",  # weit in der Vergangenheit
        }
    }
    cache_file.write_text(json.dumps(cache_data))

    client = _make_client_mock("file_fresh_reuploaded")

    result = ensure_uploaded(pdf, client, cache_file=cache_file, ttl_days=30)

    assert result == "file_fresh_reuploaded"
    client.beta.files.upload.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: Feature-Flag OFF -> None zurückgeben, kein Upload
# ---------------------------------------------------------------------------

def test_fallback_when_flag_off(tmp_path):
    from scripts.files_api_helper import ensure_uploaded

    pdf = _write_pdf(tmp_path)
    client = _make_client_mock()

    with patch.dict(os.environ, {"ACADEMIC_FILES_API": "0"}):
        result = ensure_uploaded(pdf, client, cache_file=tmp_path / "pdf_status.json")

    assert result is None
    client.beta.files.upload.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: Beta-Header wird korrekt gesetzt
# ---------------------------------------------------------------------------

def test_beta_header_present(tmp_path):
    from scripts.files_api_helper import ensure_uploaded

    pdf = _write_pdf(tmp_path)
    cache_file = tmp_path / "pdf_status.json"
    client = _make_client_mock("file_header_check")

    # Sicherstellen, dass Flag ON ist
    env = {k: v for k, v in os.environ.items() if k != "ACADEMIC_FILES_API"}
    with patch.dict(os.environ, env, clear=True):
        ensure_uploaded(pdf, client, cache_file=cache_file)

    call_kwargs = client.beta.files.upload.call_args
    # extra_headers muss beta-Flag enthalten
    extra_headers = call_kwargs.kwargs.get("extra_headers") or (
        call_kwargs.args[1] if len(call_kwargs.args) > 1 else {}
    )
    assert "anthropic-beta" in str(call_kwargs), (
        f"Beta-Header fehlt im upload-Call: {call_kwargs}"
    )


# ---------------------------------------------------------------------------
# Test 6: relevance-scorer.md enthaelt ttl=1h
# ---------------------------------------------------------------------------

def test_agent_cache_ttl_1h_relevance_scorer():
    agent_file = Path(__file__).parent.parent / "agents" / "relevance-scorer.md"
    assert agent_file.exists(), f"Datei nicht gefunden: {agent_file}"
    content = agent_file.read_text()
    assert '"ttl": "1h"' in content or "'ttl': '1h'" in content, (
        "relevance-scorer.md muss cache_control mit ttl=1h enthalten"
    )


# ---------------------------------------------------------------------------
# Test 7: quote-extractor.md enthaelt ttl=1h
# ---------------------------------------------------------------------------

def test_agent_cache_ttl_1h_quote_extractor():
    agent_file = Path(__file__).parent.parent / "agents" / "quote-extractor.md"
    assert agent_file.exists(), f"Datei nicht gefunden: {agent_file}"
    content = agent_file.read_text()
    assert '"ttl": "1h"' in content or "'ttl': '1h'" in content, (
        "quote-extractor.md muss cache_control mit ttl=1h enthalten"
    )


# ---------------------------------------------------------------------------
# Test 8: quality-reviewer.md enthaelt ttl=1h
# ---------------------------------------------------------------------------

def test_agent_cache_ttl_1h_quality_reviewer():
    agent_file = Path(__file__).parent.parent / "agents" / "quality-reviewer.md"
    assert agent_file.exists(), f"Datei nicht gefunden: {agent_file}"
    content = agent_file.read_text()
    assert '"ttl": "1h"' in content or "'ttl': '1h'" in content, (
        "quality-reviewer.md muss cache_control mit ttl=1h enthalten"
    )


# ---------------------------------------------------------------------------
# Test 9: quote-extractor.md dokumentiert source.type: "file"
# ---------------------------------------------------------------------------

def test_quote_extractor_file_source_documented():
    agent_file = Path(__file__).parent.parent / "agents" / "quote-extractor.md"
    content = agent_file.read_text()
    assert '"type": "file"' in content, (
        "quote-extractor.md muss source.type: \"file\" als primären Pfad dokumentieren"
    )


# ---------------------------------------------------------------------------
# Test 10: quote-extractor.md dokumentiert base64-Fallback
# ---------------------------------------------------------------------------

def test_quote_extractor_base64_fallback_documented():
    agent_file = Path(__file__).parent.parent / "agents" / "quote-extractor.md"
    content = agent_file.read_text()
    # base64 als Fallback muss noch vorhanden sein
    assert '"type": "base64"' in content, (
        "quote-extractor.md muss base64-Fallback dokumentieren"
    )
    # Und als Fallback bezeichnet
    assert "Fallback" in content or "fallback" in content, (
        "quote-extractor.md muss Fallback-Begriff enthalten"
    )
