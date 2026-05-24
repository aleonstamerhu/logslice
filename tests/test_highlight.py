"""Tests for logslice.highlight module."""

import re
import io
import pytest

from logslice.highlight import (
    highlight_match,
    highlight_lines,
    supports_color,
    ANSI_RESET,
    ANSI_BOLD_RED,
    ANSI_BOLD_YELLOW,
    ANSI_BOLD_CYAN,
)


PAT_ERROR = re.compile(r"ERROR")
PAT_WORD = re.compile(r"\d+")


class TestHighlightMatch:
    def test_single_match(self):
        result = highlight_match("ERROR occurred", PAT_ERROR)
        assert f"{ANSI_BOLD_RED}ERROR{ANSI_RESET}" in result
        assert "occurred" in result

    def test_no_match_returns_original(self):
        result = highlight_match("INFO all good", PAT_ERROR)
        assert result == "INFO all good"

    def test_multiple_matches(self):
        result = highlight_match("port 80 and 443", PAT_WORD)
        assert f"{ANSI_BOLD_RED}80{ANSI_RESET}" in result
        assert f"{ANSI_BOLD_RED}443{ANSI_RESET}" in result

    def test_yellow_color(self):
        result = highlight_match("ERROR here", PAT_ERROR, color="yellow")
        assert f"{ANSI_BOLD_YELLOW}ERROR{ANSI_RESET}" in result

    def test_cyan_color(self):
        result = highlight_match("ERROR here", PAT_ERROR, color="cyan")
        assert f"{ANSI_BOLD_CYAN}ERROR{ANSI_RESET}" in result

    def test_unknown_color_falls_back_to_red(self):
        result = highlight_match("ERROR here", PAT_ERROR, color="purple")
        assert f"{ANSI_BOLD_RED}ERROR{ANSI_RESET}" in result

    def test_empty_line(self):
        assert highlight_match("", PAT_ERROR) == ""


class TestHighlightLines:
    def test_highlights_all_lines(self):
        lines = ["ERROR foo", "INFO bar", "ERROR baz"]
        result = highlight_lines(lines, PAT_ERROR)
        assert f"{ANSI_BOLD_RED}ERROR{ANSI_RESET}" in result[0]
        assert result[1] == "INFO bar"
        assert f"{ANSI_BOLD_RED}ERROR{ANSI_RESET}" in result[2]

    def test_disabled_returns_unchanged(self):
        lines = ["ERROR foo", "ERROR bar"]
        result = highlight_lines(lines, PAT_ERROR, enabled=False)
        assert result == lines

    def test_none_pattern_returns_unchanged(self):
        lines = ["ERROR foo"]
        result = highlight_lines(lines, None)
        assert result == lines

    def test_empty_list(self):
        assert highlight_lines([], PAT_ERROR) == []

    def test_preserves_order(self):
        lines = ["a", "ERROR b", "c"]
        result = highlight_lines(lines, PAT_ERROR)
        assert len(result) == 3
        assert result[0] == "a"
        assert result[2] == "c"


class TestSupportsColor:
    def test_tty_stream_returns_true(self):
        class FakeTTY:
            def isatty(self):
                return True

        assert supports_color(FakeTTY()) is True

    def test_non_tty_stream_returns_false(self):
        assert supports_color(io.StringIO()) is False

    def test_stream_without_isatty_returns_false(self):
        assert supports_color(object()) is False
