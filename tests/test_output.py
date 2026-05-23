"""Tests for logslice.output module."""

import io
import pytest
from logslice.output import write_lines, write_summary, write_separator


class TestWriteLines:
    """Tests for write_lines function."""

    def test_write_empty_list(self):
        buf = io.StringIO()
        write_lines([], buf)
        assert buf.getvalue() == ""

    def test_write_single_line(self):
        buf = io.StringIO()
        write_lines(["hello world"], buf)
        assert buf.getvalue() == "hello world\n"

    def test_write_multiple_lines(self):
        buf = io.StringIO()
        lines = ["line one", "line two", "line three"]
        write_lines(lines, buf)
        assert buf.getvalue() == "line one\nline two\nline three\n"

    def test_write_lines_already_have_newline(self):
        """Lines that already end with newline should not get a double newline."""
        buf = io.StringIO()
        write_lines(["already\n"], buf)
        # Should not produce double newline
        assert buf.getvalue() == "already\n"

    def test_write_lines_mixed_newlines(self):
        buf = io.StringIO()
        lines = ["no newline", "has newline\n", "also no newline"]
        write_lines(lines, buf)
        result = buf.getvalue()
        assert "no newline\n" in result
        assert "has newline\n" in result
        assert "also no newline\n" in result
        # Ensure no double newlines
        assert "\n\n" not in result

    def test_write_lines_default_stdout(self, capsys):
        write_lines(["stdout line"])
        captured = capsys.readouterr()
        assert captured.out == "stdout line\n"


class TestWriteSummary:
    """Tests for write_summary function."""

    def test_write_summary_basic(self):
        buf = io.StringIO()
        write_summary({"total": 100, "matched": 42}, buf)
        result = buf.getvalue()
        assert "total" in result
        assert "100" in result
        assert "matched" in result
        assert "42" in result

    def test_write_summary_empty_dict(self):
        buf = io.StringIO()
        write_summary({}, buf)
        # Should write something (even if just a newline or empty block)
        assert isinstance(buf.getvalue(), str)

    def test_write_summary_single_entry(self):
        buf = io.StringIO()
        write_summary({"lines": 7}, buf)
        result = buf.getvalue()
        assert "lines" in result
        assert "7" in result

    def test_write_summary_default_stdout(self, capsys):
        write_summary({"count": 5})
        captured = capsys.readouterr()
        assert "count" in captured.out
        assert "5" in captured.out


class TestWriteSeparator:
    """Tests for write_separator function."""

    def test_write_separator_default(self):
        buf = io.StringIO()
        write_separator(buf)
        result = buf.getvalue()
        assert len(result.strip()) > 0

    def test_write_separator_is_string(self):
        buf = io.StringIO()
        write_separator(buf)
        assert isinstance(buf.getvalue(), str)

    def test_write_separator_ends_with_newline(self):
        buf = io.StringIO()
        write_separator(buf)
        assert buf.getvalue().endswith("\n")

    def test_write_separator_custom_char(self):
        buf = io.StringIO()
        write_separator(buf, char="=", width=20)
        result = buf.getvalue().strip()
        assert result == "=" * 20

    def test_write_separator_default_stdout(self, capsys):
        write_separator()
        captured = capsys.readouterr()
        assert len(captured.out.strip()) > 0
