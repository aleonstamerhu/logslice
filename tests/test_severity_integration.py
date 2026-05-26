"""Integration tests: severity filtering inside the pipeline."""

from typing import List

from logslice.severity import filter_by_severity
from logslice.filter import filter_lines, compile_pattern
from logslice.pipeline import run_pipeline


LOG_LINES = [
    "2024-03-01 10:00:00 [debug] cache miss for key=abc",
    "2024-03-01 10:00:01 [info] request received method=GET",
    "2024-03-01 10:00:02 [warn] response time high latency=800ms",
    "2024-03-01 10:00:03 [error] db connection failed host=db1",
    "2024-03-01 10:00:04 [error] db connection failed host=db2",
    "2024-03-01 10:00:05 [fatal] process killed OOM",
    "2024-03-01 10:00:06 [info] health check ok",
]


def _sev(lines: List[str], min_level: str, max_level=None) -> List[str]:
    return list(filter_by_severity(lines, min_level, max_level))


def test_warn_and_above_from_full_log():
    result = _sev(LOG_LINES, "warn")
    levels = ["warn", "error", "error", "fatal"]
    assert len(result) == 4
    for line, expected in zip(result, levels):
        assert f"[{expected}]" in line


def test_error_only_range():
    result = _sev(LOG_LINES, "error", "error")
    assert len(result) == 2
    assert all("[error]" in l for l in result)


def test_pattern_then_severity():
    """Filter by pattern first, then apply severity threshold."""
    pattern = compile_pattern("db")
    matched = list(filter_lines(LOG_LINES, pattern=pattern))
    result = _sev(matched, "error")
    assert len(result) == 2
    assert all("db" in l for l in result)


def test_severity_then_pattern():
    """Apply severity filter first, then narrow by pattern."""
    errors_and_above = _sev(LOG_LINES, "error")
    pattern = compile_pattern("db")
    result = list(filter_lines(errors_and_above, pattern=pattern))
    assert len(result) == 2


def test_no_matches_above_fatal():
    """fatal is highest; filtering above it returns nothing extra."""
    result = _sev(LOG_LINES, "fatal")
    assert len(result) == 1
    assert "[fatal]" in result[0]


def test_debug_captures_everything_with_level():
    result = _sev(LOG_LINES, "debug")
    # All 7 lines have a level tag
    assert len(result) == 7
