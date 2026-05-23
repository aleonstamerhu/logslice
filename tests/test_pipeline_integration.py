"""Integration tests for the full logslice pipeline.

These tests exercise run_pipeline end-to-end with realistic log lines,
verifying that filtering, time-range, context, and stats all interact
correctly without mocking internal components.
"""

import io
from datetime import datetime, timezone

import pytest

from logslice.pipeline import run_pipeline


SAMPLE_LOGS = [
    "2024-01-15 08:00:01 INFO  service started",
    "2024-01-15 08:00:02 DEBUG checking config",
    "2024-01-15 08:00:03 INFO  config loaded",
    "2024-01-15 08:00:04 ERROR failed to connect to db",
    "2024-01-15 08:00:05 INFO  retrying connection",
    "2024-01-15 08:00:06 ERROR connection timeout",
    "2024-01-15 08:00:07 WARN  falling back to cache",
    "2024-01-15 08:00:08 INFO  cache hit",
    "2024-01-15 08:00:09 DEBUG request processed",
    "2024-01-15 08:00:10 INFO  service healthy",
]


def _run(lines, **kwargs):
    """Helper: run pipeline over an iterable of lines and return (output_lines, stats)."""
    out = io.StringIO()
    stats = run_pipeline(iter(lines), output=out, **kwargs)
    out.seek(0)
    result = [l.rstrip("\n") for l in out.readlines()]
    return result, stats


class TestPipelineNoFilters:
    def test_all_lines_pass_through(self):
        result, stats = _run(SAMPLE_LOGS)
        assert len(result) == len(SAMPLE_LOGS)
        assert stats.total_lines == len(SAMPLE_LOGS)
        assert stats.matched_lines == len(SAMPLE_LOGS)

    def test_empty_input(self):
        result, stats = _run([])
        assert result == []
        assert stats.total_lines == 0
        assert stats.matched_lines == 0


class TestPipelinePatternFilter:
    def test_filter_errors_only(self):
        result, stats = _run(SAMPLE_LOGS, pattern="ERROR")
        assert all("ERROR" in line for line in result)
        assert len(result) == 2
        assert stats.matched_lines == 2
        assert stats.total_lines == len(SAMPLE_LOGS)

    def test_filter_info_lines(self):
        result, stats = _run(SAMPLE_LOGS, pattern=r"\bINFO\b")
        assert all("INFO" in line for line in result)
        assert stats.matched_lines == 5

    def test_case_insensitive_pattern(self):
        result, stats = _run(SAMPLE_LOGS, pattern="error", ignore_case=True)
        assert len(result) == 2

    def test_invert_match(self):
        result, stats = _run(SAMPLE_LOGS, pattern="ERROR", invert=True)
        assert all("ERROR" not in line for line in result)
        assert stats.matched_lines == len(SAMPLE_LOGS) - 2

    def test_no_matches_returns_empty(self):
        result, stats = _run(SAMPLE_LOGS, pattern="CRITICAL")
        assert result == []
        assert stats.matched_lines == 0


class TestPipelineTimeRange:
    def test_time_range_subset(self):
        """Only lines between 08:00:04 and 08:00:07 should appear."""
        result, stats = _run(
            SAMPLE_LOGS,
            time_start="2024-01-15 08:00:04",
            time_end="2024-01-15 08:00:07",
        )
        assert stats.matched_lines == 4
        assert all(
            "08:00:04" in l
            or "08:00:05" in l
            or "08:00:06" in l
            or "08:00:07" in l
            for l in result
        )

    def test_time_range_with_pattern(self):
        """Combine time range and pattern filter."""
        result, stats = _run(
            SAMPLE_LOGS,
            pattern="ERROR",
            time_start="2024-01-15 08:00:00",
            time_end="2024-01-15 08:00:05",
        )
        # Only the first ERROR (08:00:04) falls in range
        assert stats.matched_lines == 1
        assert "failed to connect" in result[0]


class TestPipelineContext:
    def test_before_context(self):
        result, stats = _run(SAMPLE_LOGS, pattern="ERROR", before_context=1)
        # Each ERROR line should be preceded by one context line
        assert len(result) > 2  # more than just the two ERROR lines

    def test_after_context(self):
        result, stats = _run(SAMPLE_LOGS, pattern="ERROR", after_context=1)
        assert len(result) > 2

    def test_context_does_not_inflate_stats(self):
        """Context lines should not count as matched lines in stats."""
        _, stats_no_ctx = _run(SAMPLE_LOGS, pattern="ERROR")
        _, stats_with_ctx = _run(SAMPLE_LOGS, pattern="ERROR", after_context=2)
        assert stats_no_ctx.matched_lines == stats_with_ctx.matched_lines


class TestPipelineStats:
    def test_stats_total_equals_input_length(self):
        _, stats = _run(SAMPLE_LOGS, pattern="INFO")
        assert stats.total_lines == len(SAMPLE_LOGS)

    def test_stats_match_rate(self):
        from logslice.stats import match_rate
        _, stats = _run(SAMPLE_LOGS, pattern="ERROR")
        rate = match_rate(stats)
        assert abs(rate - 2 / len(SAMPLE_LOGS)) < 1e-9
