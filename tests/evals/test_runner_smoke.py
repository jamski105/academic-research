"""Smoke-Test fuer eval_runner.check_expected."""
import pytest

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


def test_json_field_schema_format_dollar_prefix():
    """Schema dokumentiert $.a.b[0].c - muss genauso funktionieren wie .a.b[0].c."""
    payload = '{"quotes": [{"text": "Zitat"}]}'
    assert check_expected(
        payload,
        {"type": "json_field", "path": "$.quotes[0].text", "check": "non_empty"},
    )


def test_json_field_invalid_path_raises():
    """Path ohne fuehrendes . oder $ ist Syntaxfehler, nicht stilles False-Positive."""
    with pytest.raises(ValueError, match="Ungueltiger JSONPath"):
        check_expected(
            '{"a": "x"}',
            {"type": "json_field", "path": "a", "check": "exists"},
        )
