"""Unit tests for logslice.rate."""

import pytest

from logslice.rate import rate_limit, count_suppressed


BASE = "2024-01-15T10:00:{:02d} ERROR something"


def _lines(seconds_range):
    return [BASE.format(s) for s in seconds_range]


def test_invalid_max_per_bucket_zero():
    with pytest.raises(ValueError, match="max_per_bucket"):
        list(rate_limit([], 0))


def test_invalid_max_per_bucket_negative():
    with pytest.raises(ValueError, match="max_per_bucket"):
        list(rate_limit([], -1))


def test_invalid_bucket_seconds_zero():
    with pytest.raises(ValueError, match="bucket_seconds"):
        list(rate_limit([], 1, bucket_seconds=0))


def test_empty_input():
    assert list(rate_limit([], 5)) == []


def test_lines_without_timestamp_always_pass():
    lines = ["no timestamp here", "also no timestamp"]
    assert list(rate_limit(lines, 1)) == lines


def test_all_lines_in_one_bucket_within_limit():
    lines = _lines(range(3))
    result = list(rate_limit(lines, 5, bucket_seconds=60))
    assert result == lines


def test_all_lines_in_one_bucket_over_limit():
    lines = _lines(range(5))
    result = list(rate_limit(lines, 3, bucket_seconds=60))
    assert result == lines[:3]


def test_new_bucket_resets_counter():
    # 00:00 bucket (0-59s) and 01:00 bucket (60-119s)
    early = ["2024-01-15T10:00:{:02d} INFO msg".format(s) for s in range(4)]
    late = ["2024-01-15T10:01:{:02d} INFO msg".format(s) for s in range(4)]
    lines = early + late
    result = list(rate_limit(lines, 2, bucket_seconds=60))
    assert result == early[:2] + late[:2]


def test_max_one_per_bucket():
    lines = _lines(range(10))
    result = list(rate_limit(lines, 1, bucket_seconds=60))
    assert result == [lines[0]]


def test_count_suppressed_none():
    lines = _lines(range(2))
    assert count_suppressed(lines, 5, bucket_seconds=60) == 0


def test_count_suppressed_some():
    lines = _lines(range(5))
    assert count_suppressed(lines, 3, bucket_seconds=60) == 2
