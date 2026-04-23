"""Shared Fixtures fuer Evals-Suites."""
from __future__ import annotations

import pytest

from tests.evals.eval_runner import (
    load_agent_content,
    load_eval_file,
    load_skill_content,
)


@pytest.fixture
def skill_loader():
    return load_skill_content


@pytest.fixture
def agent_loader():
    return load_agent_content


@pytest.fixture
def eval_loader():
    return load_eval_file
