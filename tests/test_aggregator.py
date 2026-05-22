"""Tests for logslice.aggregator module."""

import re
from collections import Counter
from datetime import datetime

import pytest

from logslice.aggregator import (
    aggregate_by_pattern,
    aggregate_by_time_bucket,
    format_aggregation,
)


SAMPLE_LINES = [
    "2024-01-15 10:00:05 ERROR disk full",
    "2024-01-15 10:00:30 WARN  high memory",
    "2024-01-15 10:01:10 ERROR connection refused",
    "2024-01-15 10:01:45 INFO  startup complete",
    "2024-01-15 10:02:05 ERROR timeout",
    "2024-01-15 10:02:50 WARN  retry",
]


class TestAggregateByPattern:
    def test_full_match_counts(self):
        pattern = re.compile(r"ERROR|WARN|INFO")
        counts = aggregate_by_pattern(SAMPLE_LINES, pattern, group=0)
        assert counts["ERROR"] == 3
        assert counts["WARN"] == 2
        assert counts["INFO"] == 1

    def test_capture_group(self):
        pattern = re.compile(r"(ERROR|WARN|INFO)\s+(\w+)")
        counts = aggregate_by_pattern(SAMPLE_LINES, pattern, group=2)
        assert counts["disk"] == 1
        assert counts["high"] == 1

    def test_no_matches(self):
        pattern = re.compile(r"CRITICAL")
        counts = aggregate_by_pattern(SAMPLE_LINES, pattern)
        assert len(counts) == 0

    def test_empty_lines(self):
        pattern = re.compile(r"ERROR")
        counts = aggregate_by_pattern([], pattern)
        assert isinstance(counts, Counter)
        assert len(counts) == 0

    def test_invalid_group_falls_back(self):
        pattern = re.compile(r"ERROR")
        # group=5 does not exist, should fall back to group 0
        counts = aggregate_by_pattern(SAMPLE_LINES, pattern, group=5)
        assert counts["ERROR"] == 3


class TestAggregateByTimeBucket:
    def test_60s_buckets(self):
        result = aggregate_by_time_bucket(SAMPLE_LINES, bucket_seconds=60)
        assert len(result) == 3  # 10:00, 10:01, 10:02
        values = list(result.values())
        assert values == [2, 2, 2]

    def test_120s_buckets(self):
        result = aggregate_by_time_bucket(SAMPLE_LINES, bucket_seconds=120)
        assert len(result) == 2

    def test_lines_without_timestamps_skipped(self):
        lines = ["no timestamp here", "also no timestamp"]
        result = aggregate_by_time_bucket(lines, bucket_seconds=60)
        assert result == {}

    def test_result_is_sorted(self):
        result = aggregate_by_time_bucket(SAMPLE_LINES, bucket_seconds=60)
        keys = list(result.keys())
        assert keys == sorted(keys)


class TestFormatAggregation:
    def test_format_output(self):
        counts = Counter({"ERROR": 5, "WARN": 3, "INFO": 1})
        lines = format_aggregation(counts)
        assert lines[0] == "5\tERROR"
        assert lines[1] == "3\tWARN"
        assert lines[2] == "1\tINFO"

    def test_top_n(self):
        counts = Counter({"ERROR": 5, "WARN": 3, "INFO": 1})
        lines = format_aggregation(counts, top_n=2)
        assert len(lines) == 2
        assert lines[0] == "5\tERROR"

    def test_empty_counter(self):
        lines = format_aggregation(Counter())
        assert lines == []
