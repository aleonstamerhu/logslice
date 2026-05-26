"""Unit tests for logslice.severity."""

import pytest

from logslice.severity import (
    parse_level,
    level_rank,
    extract_level,
    filter_by_severity,
)


class TestParseLevel:
    def test_lowercase(self):
        assert parse_level("error") == "error"

    def test_alias_warning(self):
        assert parse_level("warning") == "warn"

    def test_alias_err(self):
        assert parse_level("err") == "error"

    def test_uppercase(self):
        assert parse_level("ERROR") == "error"

    def test_mixed_case(self):
        assert parse_level("Warning") == "warn"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown severity level"):
            parse_level("verbose")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_level("")


class TestLevelRank:
    def test_debug_lowest(self):
        assert level_rank("debug") == 0

    def test_fatal_highest(self):
        assert level_rank("fatal") == 6

    def test_ordering(self):
        assert level_rank("debug") < level_rank("info") < level_rank("warn")
        assert level_rank("warn") < level_rank("error") < level_rank("crit")

    def test_alias_same_rank(self):
        assert level_rank("warning") == level_rank("warn")
        assert level_rank("err") == level_rank("error")


class TestExtractLevel:
    def test_error_in_brackets(self):
        assert extract_level("2024-01-01 [ERROR] something broke") == "error"

    def test_warn_in_line(self):
        assert extract_level("WARN: disk usage high") == "warn"

    def test_warning_alias(self):
        assert extract_level("WARNING disk full") == "warn"

    def test_debug_lowercase(self):
        assert extract_level("debug mode enabled") == "debug"

    def test_no_level_returns_none(self):
        assert extract_level("some random log line without level") is None

    def test_first_level_returned(self):
        # 'info' appears before 'error'
        assert extract_level("info: see error below") == "info"


class TestFilterBySeverity:
    LINES = [
        "[debug] starting up",
        "[info] server ready",
        "[warn] low memory",
        "[error] connection refused",
        "[fatal] out of memory",
        "no level here",
    ]

    def test_min_error_returns_error_and_above(self):
        result = list(filter_by_severity(self.LINES, "error"))
        assert result == ["[error] connection refused", "[fatal] out of memory"]

    def test_min_warn_max_error(self):
        result = list(filter_by_severity(self.LINES, "warn", "error"))
        assert result == ["[warn] low memory", "[error] connection refused"]

    def test_min_debug_returns_all_with_level(self):
        result = list(filter_by_severity(self.LINES, "debug"))
        assert len(result) == 5  # excludes "no level here"

    def test_lines_without_level_excluded(self):
        result = list(filter_by_severity(self.LINES, "debug"))
        assert "no level here" not in result

    def test_empty_input(self):
        assert list(filter_by_severity([], "info")) == []

    def test_alias_min_level(self):
        result = list(filter_by_severity(self.LINES, "warning"))
        assert "[warn] low memory" in result
