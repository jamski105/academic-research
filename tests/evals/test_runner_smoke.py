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


def test_write_and_read_token_baseline(tmp_path):
    """write_token_baseline schreibt, read_token_baseline liest korrekt."""
    from tests.evals.eval_runner import read_token_baseline, write_token_baseline

    baseline_file = tmp_path / "tokens.json"
    write_token_baseline("my-suite", "case-01", 1000, 200, baseline_file=baseline_file)
    data = read_token_baseline(baseline_file=baseline_file)
    assert data["my-suite"]["case-01"] == {"tokens_in": 1000, "tokens_out": 200}


def test_write_token_baseline_merges(tmp_path):
    """Zweiter write_token_baseline ueberschreibt nur den eigenen Eintrag."""
    from tests.evals.eval_runner import read_token_baseline, write_token_baseline

    baseline_file = tmp_path / "tokens.json"
    write_token_baseline("suite-a", "c1", 100, 20, baseline_file=baseline_file)
    write_token_baseline("suite-b", "c2", 200, 40, baseline_file=baseline_file)
    data = read_token_baseline(baseline_file=baseline_file)
    assert "suite-a" in data and "suite-b" in data
