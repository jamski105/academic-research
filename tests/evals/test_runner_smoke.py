"""Smoke-Test fuer eval_runner.check_expected."""
from tests.evals.eval_runner import check_expected


def test_substring_match():
    assert check_expected("hello world", {"type": "substring", "value": "world"})


def test_substring_miss():
    assert not check_expected("hello", {"type": "substring", "value": "xyz"})


def test_regex_match():
    assert check_expected("abc123", {"type": "regex", "value": r"\d+"})


def test_json_field_exists():
    assert check_expected(
        '{"a": {"b": "x"}}',
        {"type": "json_field", "path": ".a.b", "check": "exists"},
    )


def test_json_field_non_empty_empty():
    assert not check_expected(
        '{"a": ""}',
        {"type": "json_field", "path": ".a", "check": "non_empty"},
    )
