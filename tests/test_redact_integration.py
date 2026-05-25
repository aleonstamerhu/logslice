"""Integration tests: redaction applied inside the pipeline."""

from typing import List
from logslice.redact import compile_redaction, redact_lines
from logslice.filter import filter_lines, compile_pattern
from logslice.pipeline import run_pipeline


def _run(
    lines: List[str],
    pattern: str = None,
    builtins=None,
    custom=None,
) -> List[str]:
    """Filter then redact."""
    pat = compile_pattern(pattern) if pattern else None
    filtered = list(filter_lines(lines, pattern=pat))
    return list(redact_lines(filtered, builtins=builtins, custom=custom))


LOG_LINES = [
    '2024-01-10 INFO user admin@corp.com logged in from 10.0.0.1',
    '2024-01-10 ERROR password=TopSecret1 rejected for admin@corp.com',
    '2024-01-10 WARN token=eyJhbGciOiJIUzI1NiJ9 expired',
    '2024-01-10 DEBUG routine health check passed',
    '2024-01-10 ERROR api_key=sk-abc123 invalid for 172.16.0.5',
]


def test_filter_errors_then_redact_all():
    results = _run(LOG_LINES, pattern='ERROR', builtins=None)
    assert len(results) == 2
    for line in results:
        assert 'TopSecret1' not in line
        assert 'admin@corp.com' not in line
        assert 'sk-abc123' not in line


def test_redact_ip_only_from_all_lines():
    results = _run(LOG_LINES, builtins=['ipv4'])
    assert len(results) == 5
    assert '10.0.0.1' not in results[0]
    assert '[IPv4]' in results[0]
    assert '172.16.0.5' not in results[4]
    assert '[IPv4]' in results[4]
    # emails should still be present
    assert 'admin@corp.com' in results[0]


def test_filter_warn_redact_token():
    results = _run(LOG_LINES, pattern='WARN', builtins=['token'])
    assert len(results) == 1
    assert 'eyJhbGciOiJIUzI1NiJ9' not in results[0]
    assert '[REDACTED]' in results[0]


def test_custom_pattern_redacts_log_level():
    pat, repl = compile_redaction(r'\b(INFO|DEBUG|WARN|ERROR)\b', '[LEVEL]')
    results = _run(LOG_LINES, builtins=[], custom=[(pat, repl)])
    for line in results:
        assert '[LEVEL]' in line


def test_no_redaction_passes_through_unchanged():
    results = _run(LOG_LINES, pattern='DEBUG', builtins=[])
    assert results == [LOG_LINES[3]]


def test_empty_log_returns_empty():
    results = _run([], builtins=None)
    assert results == []
