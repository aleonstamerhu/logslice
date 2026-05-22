"""Tests for logslice.extractor module."""

from datetime import datetime

import pytest

from logslice.extractor import extract_timestamp


class TestExtractTimestamp:
    def test_iso_datetime_space_separator(self):
        line = "2024-03-10 14:22:05 INFO service started"
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 14, 22, 5)

    def test_iso_datetime_t_separator(self):
        line = "2024-03-10T14:22:05 INFO service started"
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 14, 22, 5)

    def test_iso_datetime_with_microseconds(self):
        line = "2024-03-10 14:22:05.123456 DEBUG tick"
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 14, 22, 5, 123456)

    def test_syslog_format(self):
        line = "Jan  5 10:00:01 myhost sshd: connection"
        ts = extract_timestamp(line)
        assert ts is not None
        assert ts.month == 1
        assert ts.day == 5
        assert ts.hour == 10

    def test_no_timestamp_returns_none(self):
        line = "no timestamp information here at all"
        ts = extract_timestamp(line)
        assert ts is None

    def test_empty_line_returns_none(self):
        assert extract_timestamp("") is None

    def test_custom_formats(self):
        line = "10/Mar/2024:14:22:05 GET /index.html"
        ts = extract_timestamp(line, formats=["%d/%b/%Y:%H:%M:%S"])
        # No match from _TS_RE — should return None gracefully
        assert ts is None

    def test_timestamp_not_at_start(self):
        line = "host myapp 2024-06-01 09:15:00 WARN something"
        ts = extract_timestamp(line)
        assert ts == datetime(2024, 6, 1, 9, 15, 0)
