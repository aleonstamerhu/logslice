"""Tests for the pipeline module."""

import re
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from logslice.pipeline import run_pipeline, _is_match


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(*texts):
    """Return a list of plain log line strings."""
    return list(texts)


# ---------------------------------------------------------------------------
# _is_match
# ---------------------------------------------------------------------------

class TestIsMatch:
    def test_no_pattern_always_true(self):
        assert _is_match("anything", None) is True

    def test_pattern_matches(self):
        pat = re.compile(r"ERROR")
        assert _is_match("2024-01-01 ERROR something", pat) is True

    def test_pattern_no_match(self):
        pat = re.compile(r"ERROR")
        assert _is_match("2024-01-01 INFO something", pat) is False

    def test_case_insensitive_flag(self):
        pat = re.compile(r"error", re.IGNORECASE)
        assert _is_match("2024-01-01 ERROR something", pat) is True


# ---------------------------------------------------------------------------
# run_pipeline — basic filtering
# ---------------------------------------------------------------------------

class TestRunPipelineBasic:
    LINES = [
        "2024-01-01 10:00:00 INFO  service started",
        "2024-01-01 10:01:00 ERROR disk full",
        "2024-01-01 10:02:00 WARN  high memory",
        "2024-01-01 10:03:00 ERROR connection refused",
        "2024-01-01 10:04:00 INFO  service stopped",
    ]

    def test_no_filters_returns_all(self):
        result = run_pipeline(self.LINES)
        assert result == self.LINES

    def test_pattern_filter(self):
        result = run_pipeline(self.LINES, pattern=re.compile(r"ERROR"))
        assert len(result) == 2
        assert all("ERROR" in line for line in result)

    def test_exclude_pattern(self):
        result = run_pipeline(self.LINES, exclude=re.compile(r"INFO"))
        assert len(result) == 3
        assert all("INFO" not in line for line in result)

    def test_pattern_and_exclude_combined(self):
        # Keep lines with ERROR but not 'disk'
        result = run_pipeline(
            self.LINES,
            pattern=re.compile(r"ERROR"),
            exclude=re.compile(r"disk"),
        )
        assert result == ["2024-01-01 10:03:00 ERROR connection refused"]

    def test_empty_input(self):
        assert run_pipeline([]) == []


# ---------------------------------------------------------------------------
# run_pipeline — time-range filtering
# ---------------------------------------------------------------------------

class TestRunPipelineTimeRange:
    LINES = [
        "2024-01-01 09:59:00 INFO  before range",
        "2024-01-01 10:00:00 INFO  start of range",
        "2024-01-01 10:30:00 WARN  middle of range",
        "2024-01-01 11:00:00 INFO  end of range",
        "2024-01-01 11:01:00 INFO  after range",
    ]

    def test_time_range_filters_correctly(self):
        time_range = (
            datetime(2024, 1, 1, 10, 0, 0),
            datetime(2024, 1, 1, 11, 0, 0),
        )
        result = run_pipeline(self.LINES, time_range=time_range)
        assert len(result) == 3
        assert "before range" not in "".join(result)
        assert "after range" not in "".join(result)

    def test_no_time_range_keeps_all(self):
        result = run_pipeline(self.LINES, time_range=None)
        assert result == self.LINES

    def test_time_range_no_matches(self):
        time_range = (
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 2, 1, 0, 0),
        )
        result = run_pipeline(self.LINES, time_range=time_range)
        assert result == []


# ---------------------------------------------------------------------------
# run_pipeline — line limit
# ---------------------------------------------------------------------------

class TestRunPipelineLimit:
    LINES = [f"2024-01-01 10:0{i}:00 INFO line {i}" for i in range(8)]

    def test_limit_truncates_output(self):
        result = run_pipeline(self.LINES, limit=3)
        assert len(result) == 3

    def test_limit_larger_than_input(self):
        result = run_pipeline(self.LINES, limit=100)
        assert result == self.LINES

    def test_limit_zero_returns_empty(self):
        result = run_pipeline(self.LINES, limit=0)
        assert result == []
