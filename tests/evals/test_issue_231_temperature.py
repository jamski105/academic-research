"""Regression-Test fuer Issue #231.

`call_claude()` / `call_claude_with_tokens()` muessen `temperature=0` an die
Claude-API uebergeben, damit Trigger-Evals deterministisch sind und nicht durch
nicht-deterministisches Sampling intermittierend in der CI fehlschlagen.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.evals import eval_runner


class _CaptureClient:
    """Anthropic-Client-Stub, der die kwargs von messages.create festhaelt."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - Stub
        self.captured: dict | None = None
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.captured = kwargs
        # Minimal-Response mit .content und .usage wie die echte SDK-Antwort.
        return SimpleNamespace(
            content=[SimpleNamespace(text="ok")],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )


@pytest.fixture
def captured_kwargs(monkeypatch):
    """Patcht das anthropic-Modul, sodass kein echter API-Call passiert.

    Liefert eine Liste, in die der einzige _CaptureClient nach Konstruktion
    seine create-kwargs schreibt.
    """
    holder: dict[str, dict] = {}

    def _client_factory(*args, **kwargs):
        client = _CaptureClient(*args, **kwargs)
        holder["client"] = client
        return client

    fake_anthropic = SimpleNamespace(Anthropic=_client_factory)
    monkeypatch.setattr(eval_runner, "anthropic", fake_anthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return holder


def test_call_claude_uses_temperature_zero(captured_kwargs):
    eval_runner.call_claude("sys", "user")
    kwargs = captured_kwargs["client"].captured
    assert kwargs is not None, "messages.create wurde nicht aufgerufen"
    assert "temperature" in kwargs, "temperature fehlt -> nicht-deterministisch"
    assert kwargs["temperature"] == 0


def test_call_claude_with_tokens_uses_temperature_zero(captured_kwargs):
    eval_runner.call_claude_with_tokens("sys", "user")
    kwargs = captured_kwargs["client"].captured
    assert kwargs is not None, "messages.create wurde nicht aufgerufen"
    assert "temperature" in kwargs, "temperature fehlt -> nicht-deterministisch"
    assert kwargs["temperature"] == 0
