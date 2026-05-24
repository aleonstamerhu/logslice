"""Tests for logslice.truncate module."""

import pytest
from logslice.truncate import (
    truncate_line,
    truncate_lines,
    count_truncated,
    DEFAULT_MAX_LENGTH,
    ELLIPSIS,
)


class TestTruncateLine:
    def test_short_line_unchanged(self):
        line = "hello world"
        assert truncate_line(line, max_length=50) == line

    def test_exact_length_unchanged(self):
        line = "a" * 10
        assert truncate_line(line, max_length=10) == line

    def test_long_line_truncated(self):
        line = "a" * 20
        result = truncate_line(line, max_length=10)
        assert result == "a" * 10 + ELLIPSIS

    def test_trailing_newline_preserved_when_short(self):
        line = "hello\n"
        result = truncate_line(line, max_length=50)
        assert result == "hello\n"

    def test_trailing_newline_preserved_when_truncated(self):
        line = "a" * 20 + "\n"
        result = truncate_line(line, max_length=10)
        assert result.endswith("\n")
        assert result == "a" * 10 + ELLIPSIS + "\n"

    def test_no_newline_not_added_on_truncation(self):
        line = "b" * 30
        result = truncate_line(line, max_length=5)
        assert not result.endswith("\n")

    def test_max_length_none_returns_unchanged(self):
        line = "x" * 500
        assert truncate_line(line, max_length=None) == line

    def test_max_length_zero_returns_unchanged(self):
        line = "x" * 500
        assert truncate_line(line, max_length=0) == line

    def test_max_length_negative_returns_unchanged(self):
        line = "x" * 500
        assert truncate_line(line, max_length=-1) == line

    def test_default_max_length_used(self):
        long_line = "z" * (DEFAULT_MAX_LENGTH + 50)
        result = truncate_line(long_line)
        assert len(result) == DEFAULT_MAX_LENGTH + len(ELLIPSIS)
        assert result.endswith(ELLIPSIS)

    def test_empty_string_unchanged(self):
        assert truncate_line("", max_length=10) == ""


class TestTruncateLines:
    def test_empty_list(self):
        assert truncate_lines([], max_length=10) == []

    def test_all_short_lines_unchanged(self):
        lines = ["foo\n", "bar\n", "baz\n"]
        assert truncate_lines(lines, max_length=50) == lines

    def test_mixed_lines(self):
        lines = ["short\n", "a" * 20 + "\n"]
        result = truncate_lines(lines, max_length=10)
        assert result[0] == "short\n"
        assert result[1] == "a" * 10 + ELLIPSIS + "\n"

    def test_returns_new_list(self):
        lines = ["hello\n"]
        result = truncate_lines(lines, max_length=50)
        assert result is not lines


class TestCountTruncated:
    def test_none_truncated(self):
        lines = ["short\n", "also short\n"]
        assert count_truncated(lines, max_length=50) == 0

    def test_all_truncated(self):
        lines = ["a" * 20 + "\n", "b" * 20 + "\n"]
        assert count_truncated(lines, max_length=10) == 2

    def test_partial_truncated(self):
        lines = ["hi\n", "a" * 20 + "\n", "bye\n"]
        assert count_truncated(lines, max_length=10) == 1

    def test_max_length_none_returns_zero(self):
        lines = ["a" * 500 + "\n"]
        assert count_truncated(lines, max_length=None) == 0

    def test_empty_lines(self):
        assert count_truncated([], max_length=10) == 0
