"""Integration tests: grok parsing combined with filter and field extraction."""

from typing import List, Optional, Dict
from logslice.grok import compile_grok, parse_line
from logslice.filter import filter_lines, compile_pattern


APACHE_LOG = [
    '192.168.1.10 - - [01/Jan/2024:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 512',
    '10.0.0.5 - - [01/Jan/2024:10:00:02 +0000] "POST /api/login HTTP/1.1" 401 89',
    '172.16.0.1 - - [01/Jan/2024:10:00:03 +0000] "GET /static/app.js HTTP/1.1" 200 4096',
    '10.0.0.5 - - [01/Jan/2024:10:00:04 +0000] "DELETE /api/user/42 HTTP/1.1" 403 120',
]

GROK_APACHE = "%{IP:client} - - \\[%{DATA:timestamp}\\] \"%{HTTPMETHOD:method} %{URI_PATH:path} %{NOTSPACE:proto}\" %{STATUS_CODE:status} %{INT:bytes}"


def _parse_all(lines: List[str]) -> List[Optional[Dict[str, str]]]:
    pat = compile_grok(GROK_APACHE)
    return [parse_line(line, pat) for line in lines]


def test_all_apache_lines_parse():
    results = _parse_all(APACHE_LOG)
    assert all(r is not None for r in results)


def test_client_ips_extracted():
    results = _parse_all(APACHE_LOG)
    clients = [r["client"] for r in results]
    assert clients[0] == "192.168.1.10"
    assert clients[1] == "10.0.0.5"


def test_status_codes_extracted():
    results = _parse_all(APACHE_LOG)
    statuses = [r["status"] for r in results]
    assert statuses == ["200", "401", "200", "403"]


def test_filter_then_grok_only_errors():
    """Filter lines to non-200 statuses, then parse with grok."""
    pattern = compile_pattern(r" [45]\d{2} ")
    filtered = list(filter_lines(APACHE_LOG, pattern=pattern))
    assert len(filtered) == 2
    results = _parse_all(filtered)
    statuses = {r["status"] for r in results if r}
    assert statuses == {"401", "403"}


def test_grok_then_filter_by_method():
    """Parse all lines, then keep only POST/DELETE by re-filtering."""
    pattern = compile_pattern(r'"(?:POST|DELETE) ')
    filtered = list(filter_lines(APACHE_LOG, pattern=pattern))
    results = _parse_all(filtered)
    methods = [r["method"] for r in results if r]
    assert set(methods) == {"POST", "DELETE"}


def test_bytes_field_is_numeric_string():
    results = _parse_all(APACHE_LOG)
    for r in results:
        assert r["bytes"].isdigit()
