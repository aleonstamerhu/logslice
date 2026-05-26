"""Tests verifying grok pattern names appear in CLI help and that compile_grok
integrates cleanly with the argument surface expected by the CLI."""

import pytest
from logslice.grok import compile_grok, available_builtins, parse_line


# ---------------------------------------------------------------------------
# Simulate what a CLI flag --grok-pattern would do
# ---------------------------------------------------------------------------

def _grok_filter(lines, grok_expr, field, value):
    """Return lines where parsed field equals value."""
    compiled = compile_grok(grok_expr)
    out = []
    for line in lines:
        fields = parse_line(line, compiled)
        if fields and fields.get(field) == value:
            out.append(line)
    return out


LOGS = [
    "2024-01-01T10:00:00 ERROR disk full",
    "2024-01-01T10:00:01 INFO  startup complete",
    "2024-01-01T10:00:02 WARN  high memory",
    "2024-01-01T10:00:03 ERROR network timeout",
]

GROK_EXPR = "%{TIMESTAMP_ISO:ts} %{LOGLEVEL:level}"


def test_filter_errors_via_grok_field():
    errors = _grok_filter(LOGS, GROK_EXPR, "level", "ERROR")
    assert len(errors) == 2
    assert all("ERROR" in l for l in errors)


def test_filter_info_via_grok_field():
    info = _grok_filter(LOGS, GROK_EXPR, "level", "INFO")
    assert len(info) == 1
    assert "startup" in info[0]


def test_no_match_field_value_returns_empty():
    result = _grok_filter(LOGS, GROK_EXPR, "level", "CRITICAL")
    assert result == []


def test_available_builtins_non_empty():
    names = available_builtins()
    assert len(names) > 5


def test_invalid_grok_pattern_raises_on_compile():
    with pytest.raises(ValueError):
        compile_grok("%{DOES_NOT_EXIST:x}")


def test_grok_pattern_no_fields_still_filters():
    """A pattern with no named groups can still act as a presence filter."""
    compiled = compile_grok("%{LOGLEVEL}")
    matched = [l for l in LOGS if parse_line(l, compiled) is not None]
    assert len(matched) == 4
