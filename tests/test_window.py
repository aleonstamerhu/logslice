"""Tests for logslice.window."""

import pytest

from logslice.window import (
    SlidingWindow,
    flatten_windows,
    window_lines,
)


# ---------------------------------------------------------------------------
# SlidingWindow unit tests
# ---------------------------------------------------------------------------

class TestSlidingWindow:
    def test_invalid_size_raises(self):
        with pytest.raises(ValueError):
            SlidingWindow(0)

    def test_negative_size_raises(self):
        with pytest.raises(ValueError):
            SlidingWindow(-3)

    def test_push_within_capacity(self):
        w = SlidingWindow(3)
        w.push("a")
        w.push("b")
        assert len(w) == 2

    def test_push_evicts_oldest_when_full(self):
        w = SlidingWindow(2)
        w.push("a")
        w.push("b")
        w.push("c")
        assert w.snapshot() == ["b", "c"]

    def test_snapshot_returns_copy(self):
        w = SlidingWindow(3)
        w.push("x")
        snap = w.snapshot()
        snap.append("extra")
        assert len(w) == 1

    def test_clear_empties_buffer(self):
        w = SlidingWindow(4)
        for ch in "abcd":
            w.push(ch)
        w.clear()
        assert len(w) == 0
        assert w.snapshot() == []

    def test_iter_yields_all_contents(self):
        w = SlidingWindow(3)
        for ch in "abc":
            w.push(ch)
        assert list(w) == ["a", "b", "c"]

    def test_size_property(self):
        w = SlidingWindow(5)
        assert w.size == 5


# ---------------------------------------------------------------------------
# window_lines tests
# ---------------------------------------------------------------------------

def _is_error(line: str) -> bool:
    return "ERROR" in line


def test_window_lines_no_matches_yields_nothing():
    lines = ["info a", "info b", "info c"]
    result = list(window_lines(lines, size=3, predicate=_is_error))
    assert result == []


def test_window_lines_match_at_start():
    lines = ["ERROR x", "info a", "info b"]
    result = list(window_lines(lines, size=3, predicate=_is_error))
    assert len(result) == 1
    assert "ERROR x" in result[0]


def test_window_lines_include_preceding_lines():
    lines = ["info a", "info b", "ERROR x"]
    result = list(window_lines(lines, size=3, predicate=_is_error))
    assert result == [["info a", "info b", "ERROR x"]]


def test_window_lines_include_window_false_returns_single():
    lines = ["info a", "info b", "ERROR x"]
    result = list(window_lines(lines, size=3, predicate=_is_error, include_window=False))
    assert result == [["ERROR x"]]


def test_window_lines_multiple_matches():
    lines = ["ERROR 1", "info", "ERROR 2"]
    result = list(window_lines(lines, size=2, predicate=_is_error))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# flatten_windows tests
# ---------------------------------------------------------------------------

def test_flatten_windows_no_matches_empty():
    lines = ["ok", "ok", "ok"]
    assert list(flatten_windows(lines, size=2, predicate=_is_error)) == []


def test_flatten_windows_single_match():
    lines = ["a", "b", "ERROR c", "d"]
    result = list(flatten_windows(lines, size=2, predicate=_is_error))
    assert "b" in result
    assert "ERROR c" in result


def test_flatten_windows_no_duplicate_lines():
    lines = ["a", "ERROR 1", "ERROR 2", "b"]
    result = list(flatten_windows(lines, size=3, predicate=_is_error))
    # overlapping windows — each line should appear at most once
    assert len(result) == len(set(result))
