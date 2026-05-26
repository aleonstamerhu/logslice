"""Tests for logslice.grok — grok-style named pattern matching."""

import re
import pytest
from logslice.grok import (
    compile_grok,
    parse_line,
    parse_lines,
    available_builtins,
    _expand_pattern,
    BUILTIN_PATTERNS,
)


class TestExpandPattern:
    def test_no_tokens_unchanged(self):
        assert _expand_pattern("hello world") == "hello world"

    def test_named_token_no_field(self):
        result = _expand_pattern("%{IP}")
        assert result == f"(?:{BUILTIN_PATTERNS['IP']})"

    def test_named_token_with_field(self):
        result = _expand_pattern("%{IP:src_ip}")
        assert result == f"(?P<src_ip>{BUILTIN_PATTERNS['IP']})"

    def test_multiple_tokens(self):
        result = _expand_pattern("%{IP:host} %{INT:port}")
        assert "(?P<host>" in result
        assert "(?P<port>" in result

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown grok pattern name"):
            _expand_pattern("%{UNKNOWN_THING}")

    def test_custom_pattern_used(self):
        result = _expand_pattern("%{MYTOKEN:field}", custom={"MYTOKEN": r"[XYZ]+"})
        assert "(?P<field>[XYZ]+)" in result


class TestCompileGrok:
    def test_returns_compiled_pattern(self):
        pat = compile_grok("%{IP:src}")
        assert hasattr(pat, "search")

    def test_compiled_matches_ip(self):
        pat = compile_grok("%{IP:src}")
        assert pat.search("client 192.168.1.1 connected")

    def test_compiled_with_custom(self):
        pat = compile_grok("%{MYVAL:v}", custom={"MYVAL": r"foo|bar"})
        assert pat.search("got foo here")


class TestParseLine:
    def test_match_returns_fields(self):
        pat = compile_grok("%{IP:src_ip} - %{LOGLEVEL:level}")
        result = parse_line("10.0.0.1 - ERROR something happened", pat)
        assert result == {"src_ip": "10.0.0.1", "level": "ERROR"}

    def test_no_match_returns_none(self):
        pat = compile_grok("%{IP:src_ip}")
        result = parse_line("no ip address here", pat)
        assert result is None

    def test_partial_match_returns_matched_fields(self):
        pat = compile_grok("%{HTTPMETHOD:method} %{URI_PATH:path}")
        result = parse_line("GET /api/v1/users HTTP/1.1", pat)
        assert result["method"] == "GET"
        assert result["path"] == "/api/v1/users"

    def test_no_named_groups_returns_empty_dict(self):
        pat = compile_grok("%{IP}")
        result = parse_line("1.2.3.4", pat)
        assert result == {}


class TestParseLines:
    def test_mixed_matches(self):
        pat = compile_grok("%{LOGLEVEL:level}")
        lines = ["INFO startup", "no level here", "ERROR crash"]
        results = parse_lines(lines, pat)
        assert results[0] == {"level": "INFO"}
        assert results[1] is None
        assert results[2] == {"level": "ERROR"}

    def test_empty_input(self):
        pat = compile_grok("%{INT:n}")
        assert parse_lines([], pat) == []


def test_available_builtins_returns_sorted_list():
    names = available_builtins()
    assert isinstance(names, list)
    assert names == sorted(names)
    assert "IP" in names
    assert "LOGLEVEL" in names
    assert "HTTPMETHOD" in names
