"""Tests for logslice.formatter."""

import pytest
from datetime import datetime

from logslice.formatter import (
    get_format_template,
    format_line,
    format_lines,
    DEFAULT_FORMAT,
    NUMBERED_FORMAT,
    TIMESTAMP_FORMAT,
    FULL_FORMAT,
)


class TestGetFormatTemplate:
    def test_default(self):
        assert get_format_template("default") == DEFAULT_FORMAT

    def test_numbered(self):
        assert get_format_template("numbered") == NUMBERED_FORMAT

    def test_timestamp(self):
        assert get_format_template("timestamp") == TIMESTAMP_FORMAT

    def test_full(self):
        assert get_format_template("full") == FULL_FORMAT

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown format"):
            get_format_template("nonexistent")


class TestFormatLine:
    def test_default_no_extras(self):
        result = format_line("hello world")
        assert result == "hello world"

    def test_numbered_template(self):
        result = format_line("an error", lineno=42, template=NUMBERED_FORMAT)
        assert result == "42: an error"

    def test_timestamp_template(self):
        ts = datetime(2024, 3, 15, 10, 30, 0)
        result = format_line("msg", timestamp=ts, template=TIMESTAMP_FORMAT)
        assert "2024-03-15 10:30:00" in result
        assert "msg" in result

    def test_full_template(self):
        ts = datetime(2024, 1, 1, 0, 0, 0)
        result = format_line("boot", lineno=1, timestamp=ts, template=FULL_FORMAT)
        assert result == "1: [2024-01-01 00:00:00] boot"

    def test_no_timestamp_gives_empty_placeholder(self):
        result = format_line("line", lineno=5, timestamp=None, template=FULL_FORMAT)
        assert result == "5: [] line"

    def test_timestamp_with_microseconds(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, 123456)
        result = format_line("x", timestamp=ts, template=TIMESTAMP_FORMAT)
        assert "123456" in result


class TestFormatLines:
    def test_yields_formatted_lines(self):
        ts = datetime(2024, 1, 1, 8, 0, 0)
        data = [
            (1, ts, "first line"),
            (2, None, "second line"),
        ]
        results = list(format_lines(data, template=NUMBERED_FORMAT))
        assert results[0] == "1: first line"
        assert results[1] == "2: second line"

    def test_empty_input(self):
        assert list(format_lines([], template=DEFAULT_FORMAT)) == []

    def test_default_template(self):
        data = [(1, None, "raw")]
        results = list(format_lines(data))
        assert results == ["raw"]
