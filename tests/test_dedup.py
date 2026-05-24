"""Tests for logslice.dedup module."""

import pytest
from logslice.dedup import deduplicate, count_duplicates, _line_key


# ---------------------------------------------------------------------------
# _line_key
# ---------------------------------------------------------------------------

class TestLineKey:
    def test_no_ignore_timestamps_returns_stripped(self):
        assert _line_key("  hello world  ", False) == "hello world"

    def test_ignore_timestamps_strips_iso_prefix(self):
        key = _line_key("2024-01-15T10:22:33 ERROR something bad", True)
        assert key == "ERROR something bad"

    def test_ignore_timestamps_strips_syslog_prefix(self):
        key = _line_key("2024-01-15 10:22:33.456 INFO msg", True)
        assert key == "INFO msg"

    def test_no_timestamp_unchanged(self):
        key = _line_key("ERROR no timestamp here", True)
        assert key == "ERROR no timestamp here"


# ---------------------------------------------------------------------------
# deduplicate
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_empty_input(self):
        assert list(deduplicate([])) == []

    def test_all_unique(self):
        lines = ["a\n", "b\n", "c\n"]
        assert list(deduplicate(lines)) == lines

    def test_removes_exact_duplicates(self):
        lines = ["foo\n", "bar\n", "foo\n", "baz\n", "bar\n"]
        result = list(deduplicate(lines))
        assert result == ["foo\n", "bar\n", "baz\n"]

    def test_preserves_order(self):
        lines = ["c\n", "a\n", "b\n", "a\n", "c\n"]
        assert list(deduplicate(lines)) == ["c\n", "a\n", "b\n"]

    def test_max_seen_allows_n_occurrences(self):
        lines = ["x\n"] * 5
        result = list(deduplicate(lines, max_seen=3))
        assert result == ["x\n", "x\n", "x\n"]

    def test_max_seen_one_same_as_default(self):
        lines = ["x\n", "x\n", "x\n"]
        assert list(deduplicate(lines, max_seen=1)) == ["x\n"]

    def test_ignore_timestamps_deduplicates_same_message(self):
        lines = [
            "2024-01-01T00:00:01 ERROR disk full\n",
            "2024-01-01T00:00:02 ERROR disk full\n",
            "2024-01-01T00:00:03 INFO started\n",
        ]
        result = list(deduplicate(lines, ignore_timestamps=True))
        assert len(result) == 2
        assert result[0] == lines[0]
        assert result[1] == lines[2]

    def test_ignore_timestamps_false_keeps_all(self):
        lines = [
            "2024-01-01T00:00:01 ERROR disk full\n",
            "2024-01-01T00:00:02 ERROR disk full\n",
        ]
        result = list(deduplicate(lines, ignore_timestamps=False))
        assert result == lines


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

class TestCountDuplicates:
    def test_empty(self):
        assert count_duplicates([]) == {}

    def test_single_line(self):
        counts = count_duplicates(["hello\n"])
        assert counts == {"hello": 1}

    def test_multiple_duplicates(self):
        lines = ["a\n", "b\n", "a\n", "a\n"]
        counts = count_duplicates(lines)
        assert counts["a"] == 3
        assert counts["b"] == 1

    def test_ignore_timestamps_groups_same_message(self):
        lines = [
            "2024-01-01T00:00:01 ERROR disk full\n",
            "2024-01-01T00:00:02 ERROR disk full\n",
        ]
        counts = count_duplicates(lines, ignore_timestamps=True)
        assert list(counts.values()) == [2]
