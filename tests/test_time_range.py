"""Tests for logslice.time_range and logslice.extractor."""

import pytest
from datetime import datetime

from logslice.time_range import parse_timestamp, parse_range, within_range
from logslice.extractor import extract_timestamp


# ---------------------------------------------------------------------------
# parse_timestamp
# ---------------------------------------------------------------------------

class TestParseTimestamp:
    def test_iso_basic(self):
        dt = parse_timestamp("2024-03-10T08:05:30")
        assert dt == datetime(2024, 3, 10, 8, 5, 30)

    def test_iso_with_space(self):
        dt = parse_timestamp("2024-03-10 08:05:30")
        assert dt == datetime(2024, 3, 10, 8, 5, 30)

    def test_iso_with_microseconds(self):
        dt = parse_timestamp("2024-03-10T08:05:30.123456")
        assert dt is not None
        assert dt.microsecond == 123456

    def test_syslog_format(self):
        dt = parse_timestamp("Mar 10 08:05:30")
        assert dt is not None
        assert dt.month == 3 and dt.day == 10

    def test_unknown_format_returns_none(self):
        assert parse_timestamp("not-a-timestamp") is None

    def test_strips_whitespace(self):
        dt = parse_timestamp("  2024-03-10T08:05:30  ")
        assert dt == datetime(2024, 3, 10, 8, 5, 30)


# ---------------------------------------------------------------------------
# parse_range
# ---------------------------------------------------------------------------

class TestParseRange:
    def test_both_valid(self):
        start, end = parse_range("2024-01-01T00:00:00", "2024-01-02T00:00:00")
        assert start < end

    def test_none_bounds(self):
        start, end = parse_range(None, None)
        assert start is None and end is None

    def test_invalid_start_raises(self):
        with pytest.raises(ValueError, match="start"):
            parse_range("bad-start", None)

    def test_invalid_end_raises(self):
        with pytest.raises(ValueError, match="end"):
            parse_range(None, "bad-end")

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="Start"):
            parse_range("2024-01-02T00:00:00", "2024-01-01T00:00:00")


# ---------------------------------------------------------------------------
# within_range
# ---------------------------------------------------------------------------

class TestWithinRange:
    def test_within_closed_range(self):
        ts = datetime(2024, 6, 15, 12, 0, 0)
        assert within_range(ts, datetime(2024, 6, 1), datetime(2024, 6, 30))

    def test_before_start(self):
        ts = datetime(2024, 5, 31)
        assert not within_range(ts, datetime(2024, 6, 1), None)

    def test_after_end(self):
        ts = datetime(2024, 7, 1)
        assert not within_range(ts, None, datetime(2024, 6, 30))

    def test_no_bounds(self):
        assert within_range(datetime(2000, 1, 1), None, None)


# ---------------------------------------------------------------------------
# extract_timestamp
# ---------------------------------------------------------------------------

class TestExtractTimestamp:
    def test_iso_in_log_line(self):
        line = "2024-03-10T08:05:30 ERROR Something went wrong"
        dt = extract_timestamp(line)
        assert dt == datetime(2024, 3, 10, 8, 5, 30)

    def test_apache_log_line(self):
        line = '127.0.0.1 - - [10/Mar/2024:08:05:30 +0000] "GET / HTTP/1.1" 200 612'
        dt = extract_timestamp(line)
        assert dt is not None
        assert dt.day == 10 and dt.month == 3

    def test_no_timestamp_returns_none(self):
        assert extract_timestamp("no timestamp here at all") is None

    def test_custom_pattern(self):
        line = "ts=2024-03-10T08:05:30 level=info msg=hello"
        dt = extract_timestamp(line, custom_pattern=r"ts=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")
        assert dt == datetime(2024, 3, 10, 8, 5, 30)

    def test_invalid_custom_pattern_raises(self):
        with pytest.raises(ValueError, match="Invalid custom"):
            extract_timestamp("some line", custom_pattern="[invalid(")
