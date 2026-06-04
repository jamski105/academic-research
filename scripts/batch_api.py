#!/usr/bin/env python3
"""Anthropic Message Batches API wrapper for bulk relevance scoring.

Usage:
  from batch_api import submit_batch, save_batch_job, load_batch_job

  job = submit_batch(papers, query="DevOps", model="claude-haiku-4-5")
  save_batch_job(session_dir, job)

  # later (pickup via /history --batch <id>)
  job = load_batch_job(session_dir)
  if get_batch_status(job["batch_id"]) == "ended":
      scores = fetch_batch_results(job["batch_id"])
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

BATCH_THRESHOLD = 50
_BATCH_JSON = "batch.json"

_SCORING_SYSTEM = (
    "Du bist ein Relevanz-Bewerter für akademische Literatur. "
    "Bewerte die Relevanz eines Papers für eine Suchanfrage auf einer Skala von 0.0 bis 1.0. "
    "Antworte ausschließlich mit einem JSON-Objekt: {\"score\": <float>}"
)


def _build_request(paper: dict[str, Any], query: str, custom_id: str, model: str) -> dict[str, Any]:
    """Build a single Message Batches API request for one paper."""
    title = paper.get("title") or "Kein Titel"
    abstract = paper.get("abstract") or "Kein Abstract verfügbar"
    prompt = (
        f"Suchanfrage: {query}\n\n"
        f"Titel: {title}\n\n"
        f"Abstract: {abstract}\n\n"
        f"Bewerte die Relevanz (0.0–1.0)."
    )
    return {
        "custom_id": custom_id,
        "params": {
            "model": model,
            "max_tokens": 64,
            "system": _SCORING_SYSTEM,
            "messages": [{"role": "user", "content": prompt}],
        },
    }


def submit_batch(
    papers: list[dict[str, Any]],
    query: str,
    model: str = "claude-haiku-4-5",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Submit papers for batch relevance scoring via Anthropic Batches API.

    Args:
        papers: List of paper dicts (title, abstract, doi).
        query: The original search query.
        model: Anthropic model to use (default: claude-haiku-4-5).
        api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var).

    Returns:
        dict with batch_id, n_papers, status, created_at, query.

    Raises:
        ValueError: if fewer than BATCH_THRESHOLD papers are provided.
    """
    if len(papers) < BATCH_THRESHOLD:
        raise ValueError(
            f"Batch mode requires at least {BATCH_THRESHOLD} papers, "
            f"got {len(papers)}. Use relevance-scorer directly for smaller sets."
        )

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)

    requests = [
        _build_request(paper, query, f"paper_{i}", model)
        for i, paper in enumerate(papers)
    ]

    response = client.beta.messages.batches.create(requests=requests)

    return {
        "batch_id": response.id,
        "n_papers": len(papers),
        "query": query,
        "model": model,
        "status": "submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_batch_job(session_dir: str, job_data: dict[str, Any]) -> None:
    """Save batch job metadata to <session_dir>/batch.json."""
    path = Path(session_dir) / _BATCH_JSON
    path.write_text(json.dumps(job_data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_batch_job(session_dir: str) -> dict[str, Any]:
    """Load batch job metadata from <session_dir>/batch.json."""
    path = Path(session_dir) / _BATCH_JSON
    return json.loads(path.read_text(encoding="utf-8"))


def get_batch_status(batch_id: str, api_key: str | None = None) -> str:
    """Return the processing status of a submitted batch.

    Polls the Anthropic Message Batches API. The batch is ready to be
    retrieved once the status is ``ended``.

    Args:
        batch_id: The ``msgbatch_...`` id returned by submit_batch().
        api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var).

    Returns:
        The processing status string (e.g. ``in_progress`` or ``ended``).
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)
    batch = client.beta.messages.batches.retrieve(batch_id)
    return batch.processing_status


def fetch_batch_results(batch_id: str, api_key: str | None = None) -> dict[str, float]:
    """Fetch and parse relevance scores for a finished batch.

    Should only be called once :func:`get_batch_status` reports ``ended``.
    Maps each ``paper_<i>`` custom_id back to its parsed relevance score.

    Args:
        batch_id: The ``msgbatch_...`` id of an ``ended`` batch.
        api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var).

    Returns:
        Mapping of custom_id (e.g. ``paper_0``) to relevance score (float).
        Entries that did not succeed or could not be parsed are skipped.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)

    scores: dict[str, float] = {}
    for entry in client.beta.messages.batches.results(batch_id):
        if getattr(entry.result, "type", None) != "succeeded":
            continue
        message = entry.result.message
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        try:
            parsed = json.loads(text)
            scores[entry.custom_id] = float(parsed["score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return scores
