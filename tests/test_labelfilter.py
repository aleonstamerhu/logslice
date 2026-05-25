"""Tests for logslice.labelfilter."""

import pytest
from logslice.labelfilter import (
    parse_labels,
    label_matches,
    parse_label_expr,
    filter_by_labels,
)


class TestParseLabels:
    def test_single_kv(self):
        assert parse_labels("level=error") == {"level": "error"}

    def test_multiple_kv(self):
        result = parse_labels("level=warn host=web01 env=prod")
        assert result == {"level": "warn", "host": "web01", "env": "prod"}

    def test_quoted_value(self):
        result = parse_labels('msg="disk full" level=error')
        assert result["msg"] == "disk full"
        assert result["level"] == "error"

    def test_single_quoted_value(self):
        result = parse_labels("msg='hello world' level=info")
        assert result["msg"] == "hello world"

    def test_no_labels(self):
        assert parse_labels("plain log line with no kv") == {}

    def test_dotted_key(self):
        result = parse_labels("http.status=200")
        assert result["http.status"] == "200"


class TestLabelMatches:
    def test_key_present_no_value_check(self):
        assert label_matches({"level": "error"}, "level") is True

    def test_key_absent(self):
        assert label_matches({}, "level") is False

    def test_value_match(self):
        assert label_matches({"level": "error"}, "level", "error") is True

    def test_value_mismatch(self):
        assert label_matches({"level": "warn"}, "level", "error") is False

    def test_negate_absent_key(self):
        assert label_matches({}, "level", negate=True) is True

    def test_negate_present_key(self):
        assert label_matches({"level": "error"}, "level", negate=True) is False

    def test_negate_value_mismatch(self):
        assert label_matches({"level": "warn"}, "level", "error", negate=True) is True


class TestParseLabelExpr:
    def test_key_only(self):
        assert parse_label_expr("level") == (False, "level", None)

    def test_key_value(self):
        assert parse_label_expr("level=error") == (False, "level", "error")

    def test_negated_key(self):
        assert parse_label_expr("!level") == (True, "level", None)

    def test_negated_key_value(self):
        assert parse_label_expr("!env=prod") == (True, "env", "prod")


class TestFilterByLabels:
    LINES = [
        "2024-01-01 level=error host=web01 msg=timeout",
        "2024-01-01 level=warn  host=web02 msg=slow",
        "2024-01-01 level=error host=db01  msg=conn_refused",
        "2024-01-01 level=info  host=web01 msg=ok",
    ]

    def test_filter_by_level(self):
        result = list(filter_by_labels(self.LINES, ["level=error"]))
        assert len(result) == 2
        assert all("level=error" in l for l in result)

    def test_filter_by_host(self):
        result = list(filter_by_labels(self.LINES, ["host=web01"]))
        assert len(result) == 2

    def test_multiple_expressions_and(self):
        result = list(filter_by_labels(self.LINES, ["level=error", "host=web01"]))
        assert len(result) == 1
        assert "timeout" in result[0]

    def test_negated_expression(self):
        result = list(filter_by_labels(self.LINES, ["!level=info"]))
        assert len(result) == 3

    def test_key_presence(self):
        result = list(filter_by_labels(self.LINES, ["host"]))
        assert len(result) == 4

    def test_no_expressions_returns_all(self):
        result = list(filter_by_labels(self.LINES, []))
        assert result == self.LINES

    def test_empty_input(self):
        assert list(filter_by_labels([], ["level=error"])) == []
