"""Tests for logslice.multiline."""

import pytest
from logslice.multiline import (
    join_multiline,
    split_record,
    count_multiline_records,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect(lines, **kwargs):
    return list(join_multiline(lines, **kwargs))


ISO_A = "2024-01-15 10:00:00 INFO  starting up"
ISO_B = "2024-01-15 10:00:01 ERROR boom"
SYSLOG_A = "Jan 15 10:00:00 host app: ok"
STACK_1 = "    at com.example.Foo.bar(Foo.java:42)"
STACK_2 = "    at com.example.Main.main(Main.java:10)"


# ---------------------------------------------------------------------------
# join_multiline
# ---------------------------------------------------------------------------

class TestJoinMultiline:
    def test_single_line_record(self):
        assert _collect([ISO_A]) == [ISO_A]

    def test_two_independent_records(self):
        records = _collect([ISO_A, ISO_B])
        assert records == [ISO_A, ISO_B]

    def test_continuation_lines_joined(self):
        lines = [ISO_B, STACK_1, STACK_2]
        records = _collect(lines)
        assert len(records) == 1
        assert STACK_1 in records[0]
        assert STACK_2 in records[0]

    def test_two_records_with_continuations(self):
        lines = [ISO_A, STACK_1, ISO_B, STACK_2]
        records = _collect(lines)
        assert len(records) == 2
        assert STACK_1 in records[0]
        assert STACK_2 in records[1]

    def test_syslog_timestamp_starts_new_record(self):
        lines = [SYSLOG_A, "    continuation", ISO_A]
        records = _collect(lines)
        assert len(records) == 2

    def test_blank_line_flushes_buffer(self):
        lines = [ISO_A, STACK_1, "", ISO_B]
        records = _collect(lines)
        assert len(records) == 2

    def test_custom_separator(self):
        lines = [ISO_B, STACK_1]
        records = _collect(lines, separator=" | ")
        assert " | " in records[0]

    def test_continuation_pattern_prevents_new_record(self):
        # Even though ISO_B starts with a timestamp, the continuation
        # pattern matches it so it should be folded into the previous record.
        lines = [ISO_A, ISO_B]
        records = _collect(lines, continuation=r"ERROR")
        assert len(records) == 1

    def test_max_lines_forces_flush(self):
        lines = [ISO_A] + [STACK_1] * 10
        records = _collect(lines, max_lines=5)
        # The buffer must have been flushed at least once mid-continuation
        assert len(records) >= 2

    def test_empty_input(self):
        assert _collect([]) == []

    def test_lines_with_trailing_newlines(self):
        lines = [ISO_A + "\n", STACK_1 + "\n", ISO_B + "\n"]
        records = _collect(lines)
        assert len(records) == 2
        assert "\n" not in records[0].split("\n")[0]  # stripped


# ---------------------------------------------------------------------------
# split_record
# ---------------------------------------------------------------------------

def test_split_record_single_line():
    assert split_record(ISO_A) == [ISO_A]


def test_split_record_multi_line():
    record = "\n".join([ISO_B, STACK_1, STACK_2])
    parts = split_record(record)
    assert parts == [ISO_B, STACK_1, STACK_2]


def test_split_record_custom_separator():
    record = ISO_B + " | " + STACK_1
    parts = split_record(record, separator=" | ")
    assert parts == [ISO_B, STACK_1]


# ---------------------------------------------------------------------------
# count_multiline_records
# ---------------------------------------------------------------------------

def test_count_multiline_records_none():
    records = [ISO_A, ISO_B]
    assert count_multiline_records(records) == 0


def test_count_multiline_records_some():
    records = ["\n".join([ISO_B, STACK_1]), ISO_A]
    assert count_multiline_records(records) == 1
