"""Exhaustive tests for each built-in grok pattern."""

import pytest
from logslice.grok import compile_grok, parse_line, BUILTIN_PATTERNS


@pytest.mark.parametrize("value", ["42", "-7", "+100", "0"])
def test_int_pattern(value):
    pat = compile_grok("%{INT:n}")
    result = parse_line(value, pat)
    assert result is not None and result["n"] == value


@pytest.mark.parametrize("value", ["3.14", "-0.5", "+1.0", "42"])
def test_float_pattern(value):
    pat = compile_grok("%{FLOAT:f}")
    result = parse_line(value, pat)
    assert result is not None


@pytest.mark.parametrize("ip", ["192.168.0.1", "10.0.0.255", "0.0.0.0"])
def test_ip_pattern(ip):
    pat = compile_grok("%{IP:addr}")
    result = parse_line(ip, pat)
    assert result is not None and result["addr"] == ip


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
def test_httpmethod_pattern(method):
    pat = compile_grok("%{HTTPMETHOD:m}")
    result = parse_line(method, pat)
    assert result is not None and result["m"] == method


@pytest.mark.parametrize("code", ["200", "301", "404", "500"])
def test_status_code_pattern(code):
    pat = compile_grok("%{STATUS_CODE:s}")
    result = parse_line(code, pat)
    assert result is not None and result["s"] == code


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL", "TRACE"])
def test_loglevel_pattern(level):
    pat = compile_grok("%{LOGLEVEL:lvl}")
    result = parse_line(level, pat)
    assert result is not None and result["lvl"] == level


def test_timestamp_iso_pattern():
    pat = compile_grok("%{TIMESTAMP_ISO:ts}")
    result = parse_line("2024-06-15T08:30:00", pat)
    assert result is not None and result["ts"] == "2024-06-15T08:30:00"


def test_uri_path_pattern():
    pat = compile_grok("%{URI_PATH:path}")
    result = parse_line("/api/v2/items", pat)
    assert result is not None and result["path"] == "/api/v2/items"


def test_greedydata_captures_rest():
    pat = compile_grok("%{LOGLEVEL:level} %{GREEDYDATA:msg}")
    result = parse_line("ERROR something went wrong here", pat)
    assert result["msg"] == "something went wrong here"


def test_all_builtin_names_compile():
    """Every built-in name should compile without error."""
    for name in BUILTIN_PATTERNS:
        compile_grok(f"%{{{name}:field}}")
