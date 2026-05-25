"""Tests for logslice.fieldextract."""

import pytest
from logslice.fieldextract import (
    extract_fields,
    get_field,
    filter_by_field,
    field_values,
)


class TestExtractFields:
    def test_single_kv(self):
        assert extract_fields('level=info msg="hello world"') == {
            "level": "info",
            "msg": "hello world",
        }

    def test_multiple_kv_no_quotes(self):
        result = extract_fields("status=200 method=GET path=/health")
        assert result == {"status": "200", "method": "GET", "path": "/health"}

    def test_kv_with_quoted_value(self):
        result = extract_fields('error="connection refused" retries=3')
        assert result["error"] == "connection refused"
        assert result["retries"] == "3"

    def test_json_fields_fallback(self):
        line = '{"level": "warn", "code": 404}'
        result = extract_fields(line)
        assert result["level"] == "warn"
        assert result["code"] == "404"

    def test_empty_line_returns_empty_dict(self):
        assert extract_fields("") == {}

    def test_no_fields_returns_empty_dict(self):
        assert extract_fields("plain log line with no structure") == {}

    def test_dotted_key(self):
        result = extract_fields("http.status=500")
        assert result["http.status"] == "500"


class TestGetField:
    def test_existing_field(self):
        assert get_field("level=error msg=oops", "level") == "error"

    def test_missing_field_returns_none(self):
        assert get_field("level=error", "msg") is None

    def test_empty_line_returns_none(self):
        assert get_field("", "level") is None


class TestFilterByField:
    def _lines(self):
        return [
            "level=info msg=started",
            "level=error msg=failed",
            "level=info msg=finished",
            "level=warn msg=slow",
        ]

    def test_filter_keeps_matching_lines(self):
        result = list(filter_by_field(self._lines(), "level", "info"))
        assert result == ["level=info msg=started", "level=info msg=finished"]

    def test_filter_no_matches_returns_empty(self):
        result = list(filter_by_field(self._lines(), "level", "debug"))
        assert result == []

    def test_filter_on_missing_field_returns_empty(self):
        result = list(filter_by_field(self._lines(), "nonexistent", "x"))
        assert result == []


class TestFieldValues:
    def test_yields_present_values(self):
        lines = ["status=200", "status=404", "no-field-here", "status=500"]
        result = list(field_values(lines, "status"))
        assert result == ["200", "404", "500"]

    def test_empty_input(self):
        assert list(field_values([], "level")) == []

    def test_field_absent_in_all_lines(self):
        lines = ["a=1", "b=2"]
        assert list(field_values(lines, "z")) == []
