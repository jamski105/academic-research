"""Tests for Batch-API (#94):
  - scripts/batch_api.py module exists and is importable
  - submit_batch() creates a batch from paper list and returns job_id
  - save_batch_job() writes batch.json to session_dir
  - load_batch_job() reads batch.json back
  - threshold: only triggered for >= 50 papers
  - --batch flag documented in commands/search.md
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------

def test_batch_api_importable():
    """scripts/batch_api.py must be importable."""
    import batch_api  # noqa: F401


def test_batch_api_has_submit_batch():
    """batch_api must expose submit_batch()."""
    import batch_api
    assert hasattr(batch_api, "submit_batch"), "submit_batch missing from batch_api"
    assert callable(batch_api.submit_batch)


def test_batch_api_has_save_batch_job():
    """batch_api must expose save_batch_job()."""
    import batch_api
    assert hasattr(batch_api, "save_batch_job")
    assert callable(batch_api.save_batch_job)


def test_batch_api_has_load_batch_job():
    """batch_api must expose load_batch_job()."""
    import batch_api
    assert hasattr(batch_api, "load_batch_job")
    assert callable(batch_api.load_batch_job)


# ---------------------------------------------------------------------------
# Threshold test
# ---------------------------------------------------------------------------

def test_batch_threshold_constant():
    """BATCH_THRESHOLD must be 50."""
    import batch_api
    assert batch_api.BATCH_THRESHOLD == 50


# ---------------------------------------------------------------------------
# save/load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_batch_job(tmp_path):
    """save_batch_job writes, load_batch_job reads back the same data."""
    import batch_api
    job_data = {
        "batch_id": "msgbatch_abc123",
        "query": "DevOps",
        "n_papers": 75,
        "status": "submitted",
        "created_at": "2026-05-18T10:00:00Z",
    }
    session_dir = str(tmp_path)
    batch_api.save_batch_job(session_dir, job_data)

    loaded = batch_api.load_batch_job(session_dir)
    assert loaded["batch_id"] == "msgbatch_abc123"
    assert loaded["n_papers"] == 75
    assert loaded["query"] == "DevOps"


def test_save_batch_job_writes_batch_json(tmp_path):
    """save_batch_job must write to <session_dir>/batch.json."""
    import batch_api
    job_data = {"batch_id": "test_id", "status": "submitted"}
    batch_api.save_batch_job(str(tmp_path), job_data)
    batch_json = tmp_path / "batch.json"
    assert batch_json.exists()
    content = json.loads(batch_json.read_text())
    assert content["batch_id"] == "test_id"


# ---------------------------------------------------------------------------
# submit_batch with mocked Anthropic client
# ---------------------------------------------------------------------------

def test_submit_batch_returns_job_id():
    """submit_batch() returns a dict with batch_id and status."""
    import batch_api

    # Build 50 minimal paper dicts
    papers = [
        {"title": f"Paper {i}", "abstract": f"Abstract {i}", "doi": f"10.1/{i}"}
        for i in range(50)
    ]

    mock_response = MagicMock()
    mock_response.id = "msgbatch_test001"

    with patch("batch_api.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.beta.messages.batches.create.return_value = mock_response

        result = batch_api.submit_batch(papers, query="DevOps Governance", model="claude-haiku-4-5")

    assert "batch_id" in result
    assert result["batch_id"] == "msgbatch_test001"
    assert result["n_papers"] == 50


def test_submit_batch_skips_when_below_threshold():
    """submit_batch raises ValueError when fewer than BATCH_THRESHOLD papers."""
    import batch_api
    papers = [{"title": f"Paper {i}", "abstract": ""} for i in range(49)]
    try:
        batch_api.submit_batch(papers, query="test")
        assert False, "Expected ValueError for < 50 papers"
    except ValueError as e:
        assert "50" in str(e)


# ---------------------------------------------------------------------------
# Batch-Abholung (#228): get_batch_status / fetch_batch_results
# ---------------------------------------------------------------------------

def test_batch_api_has_get_batch_status():
    """batch_api must expose get_batch_status() for --batch pickup."""
    import batch_api
    assert hasattr(batch_api, "get_batch_status")
    assert callable(batch_api.get_batch_status)


def test_batch_api_has_fetch_batch_results():
    """batch_api must expose fetch_batch_results() for --batch pickup."""
    import batch_api
    assert hasattr(batch_api, "fetch_batch_results")
    assert callable(batch_api.fetch_batch_results)


def test_get_batch_status_returns_processing_status():
    """get_batch_status() returns the API processing_status string."""
    import batch_api

    mock_batch = MagicMock()
    mock_batch.processing_status = "ended"

    with patch("batch_api.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.beta.messages.batches.retrieve.return_value = mock_batch

        status = batch_api.get_batch_status("msgbatch_test001")

    assert status == "ended"
    mock_client.beta.messages.batches.retrieve.assert_called_once_with("msgbatch_test001")


def test_fetch_batch_results_parses_scores():
    """fetch_batch_results() maps custom_id -> parsed relevance score."""
    import batch_api

    def _entry(custom_id, text, rtype="succeeded"):
        block = MagicMock()
        block.type = "text"
        block.text = text
        message = MagicMock()
        message.content = [block]
        result = MagicMock()
        result.type = rtype
        result.message = message
        entry = MagicMock()
        entry.custom_id = custom_id
        entry.result = result
        return entry

    entries = [
        _entry("paper_0", '{"score": 0.9}'),
        _entry("paper_1", '{"score": 0.1}'),
        _entry("paper_2", "not json"),          # unparsable -> skipped
        _entry("paper_3", '{"score": 0.5}', rtype="errored"),  # failed -> skipped
    ]

    with patch("batch_api.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.beta.messages.batches.results.return_value = iter(entries)

        scores = batch_api.fetch_batch_results("msgbatch_test001")

    assert scores == {"paper_0": 0.9, "paper_1": 0.1}


# ---------------------------------------------------------------------------
# commands/search.md contains --batch flag
# ---------------------------------------------------------------------------

def test_search_md_has_batch_flag():
    """commands/search.md must document the --batch flag."""
    search_md = REPO_ROOT / "commands" / "search.md"
    content = search_md.read_text(encoding="utf-8")
    assert "--batch" in content, "commands/search.md missing --batch flag documentation"
