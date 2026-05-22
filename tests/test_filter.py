"""Tests for logslice.filter module."""

import re
from datetime import datetime, timezone

import pytest

from logslice.filter import compile_pattern, count_matches, filter_lines


SAMPLE_LINES = [
    "2024-01-15T10:00:00Z INFO  Service started",
    "2024-01-15T10:01:00Z DEBUG Connecting to database",
    "2024-01-15T10:02:00Z ERROR Failed to connect",
    "2024-01-15T10:03:00Z INFO  Retrying connection",
    "2024-01-15T10:04:00Z INFO  Connection established",
]


def test_compile_pattern_none():
    assert compile_pattern(None) is None


def test_compile_pattern_valid():
    p = compile_pattern(r"ERROR|WARN")
    assert p is not None
    assert p.search("ERROR something")


def test_compile_pattern_invalid():
    with pytest.raises(re.error):
        compile_pattern(r"[invalid")


def test_filter_no_filters():
    result = list(filter_lines(iter(SAMPLE_LINES)))
    assert result == SAMPLE_LINES


def test_filter_by_pattern():
    pattern = compile_pattern(r"INFO")
    result = list(filter_lines(iter(SAMPLE_LINES), pattern=pattern))
    assert len(result) == 3
    assert all("INFO" in line for line in result)


def test_filter_invert_pattern():
    pattern = compile_pattern(r"INFO")
    result = list(filter_lines(iter(SAMPLE_LINES), pattern=pattern, invert=True))
    assert len(result) == 2
    assert all("INFO" not in line for line in result)


def test_filter_by_time_range():
    start = datetime(2024, 1, 15, 10, 1, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 3, 0, tzinfo=timezone.utc)
    time_range = (start, end)
    result = list(filter_lines(iter(SAMPLE_LINES), time_range=time_range))
    assert len(result) == 3


def test_filter_pattern_and_time_range():
    pattern = compile_pattern(r"INFO")
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, 10, 2, 0, tzinfo=timezone.utc)
    result = list(filter_lines(iter(SAMPLE_LINES), pattern=pattern, time_range=(start, end)))
    assert len(result) == 1
    assert "Service started" in result[0]


def test_filter_no_timestamp_lines_pass_time_filter():
    lines = ["no timestamp here", "also no timestamp"]
    start = datetime(2024, 1, 15, tzinfo=timezone.utc)
    end = datetime(2024, 1, 16, tzinfo=timezone.utc)
    result = list(filter_lines(iter(lines), time_range=(start, end)))
    assert result == lines


def test_count_matches():
    pattern = compile_pattern(r"INFO")
    assert count_matches(iter(SAMPLE_LINES), pattern=pattern) == 3


def test_count_matches_no_filter():
    assert count_matches(iter(SAMPLE_LINES)) == len(SAMPLE_LINES)
