"""Tests for logslice.normalize."""

import pytest
from logslice.normalize import (
    strip_ansi,
    normalize_whitespace,
    normalize_endings,
    normalize_line,
    normalize_lines,
)


class TestStripAnsi:
    def test_no_codes_unchanged(self):
        assert strip_ansi('hello world') == 'hello world'

    def test_bold_reset(self):
        assert strip_ansi('\x1b[1mhello\x1b[0m') == 'hello'

    def test_color_code(self):
        assert strip_ansi('\x1b[31mERROR\x1b[0m: bad') == 'ERROR: bad'

    def test_multiple_codes(self):
        line = '\x1b[1m\x1b[33mWARN\x1b[0m message'
        assert strip_ansi(line) == 'WARN message'

    def test_empty_string(self):
        assert strip_ansi('') == ''


class TestNormalizeWhitespace:
    def test_single_spaces_unchanged(self):
        assert normalize_whitespace('a b c\n') == 'a b c\n'

    def test_multiple_spaces_collapsed(self):
        assert normalize_whitespace('a  b   c\n') == 'a b c\n'

    def test_tabs_collapsed(self):
        assert normalize_whitespace('a\t\tb\n') == 'a b\n'

    def test_leading_trailing_stripped(self):
        assert normalize_whitespace('  hello  \n') == 'hello\n'

    def test_preserve_newline_false(self):
        result = normalize_whitespace('  hi  \n', preserve_newline=False)
        assert result == 'hi'

    def test_no_trailing_newline(self):
        assert normalize_whitespace('  hi  ') == 'hi'


class TestNormalizeEndings:
    def test_lf_unchanged(self):
        assert normalize_endings('line\n') == 'line\n'

    def test_crlf_converted(self):
        assert normalize_endings('line\r\n') == 'line\n'

    def test_bare_cr_converted(self):
        assert normalize_endings('line\r') == 'line\n'

    def test_no_newline_unchanged(self):
        assert normalize_endings('line') == 'line'


class TestNormalizeLine:
    def test_defaults_strip_ansi_and_endings(self):
        line = '\x1b[31mERROR\x1b[0m: crash\r\n'
        assert normalize_line(line) == 'ERROR: crash\n'

    def test_whitespace_opt_in(self):
        line = 'a  b\n'
        assert normalize_line(line, whitespace=True) == 'a b\n'

    def test_ansi_opt_out(self):
        line = '\x1b[31mred\x1b[0m\n'
        result = normalize_line(line, ansi=False)
        assert '\x1b' in result

    def test_endings_opt_out(self):
        line = 'line\r\n'
        result = normalize_line(line, endings=False)
        assert result == 'line\r\n'


class TestNormalizeLines:
    def test_yields_all_lines(self):
        lines = ['\x1b[1mA\x1b[0m\r\n', '\x1b[32mB\x1b[0m\n']
        result = list(normalize_lines(lines))
        assert result == ['A\n', 'B\n']

    def test_empty_input(self):
        assert list(normalize_lines([])) == []

    def test_whitespace_flag_propagated(self):
        lines = ['a  b\n', 'c   d\n']
        result = list(normalize_lines(lines, whitespace=True))
        assert result == ['a b\n', 'c d\n']
