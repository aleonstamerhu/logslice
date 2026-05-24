"""Tests for logslice.tail — tail_lines and head_lines helpers."""

import pytest

from logslice.tail import head_lines, iter_tail, tail_lines


# ---------------------------------------------------------------------------
# tail_lines
# ---------------------------------------------------------------------------

class TestTailLines:
    def test_none_count_returns_all(self):
        lines = ["a", "b", "c"]
        assert tail_lines(lines, None) == ["a", "b", "c"]

    def test_zero_count_returns_all(self):
        assert tail_lines(["a", "b"], 0) == ["a", "b"]

    def test_negative_count_returns_all(self):
        assert tail_lines(["a", "b"], -5) == ["a", "b"]

    def test_count_less_than_total(self):
        lines = ["a", "b", "c", "d", "e"]
        assert tail_lines(lines, 3) == ["c", "d", "e"]

    def test_count_equals_total(self):
        lines = ["x", "y", "z"]
        assert tail_lines(lines, 3) == ["x", "y", "z"]

    def test_count_greater_than_total(self):
        lines = ["x", "y"]
        assert tail_lines(lines, 10) == ["x", "y"]

    def test_empty_input(self):
        assert tail_lines([], 5) == []

    def test_count_one(self):
        assert tail_lines(["a", "b", "c"], 1) == ["c"]

    def test_preserves_newlines(self):
        lines = ["line1\n", "line2\n", "line3\n"]
        assert tail_lines(lines, 2) == ["line2\n", "line3\n"]

    def test_accepts_generator(self):
        gen = (str(i) for i in range(10))
        result = tail_lines(gen, 3)
        assert result == ["7", "8", "9"]


# ---------------------------------------------------------------------------
# head_lines
# ---------------------------------------------------------------------------

class TestHeadLines:
    def test_none_count_returns_all(self):
        assert head_lines(["a", "b", "c"], None) == ["a", "b", "c"]

    def test_zero_count_returns_all(self):
        assert head_lines(["a", "b"], 0) == ["a", "b"]

    def test_negative_count_returns_all(self):
        assert head_lines(["a", "b"], -1) == ["a", "b"]

    def test_count_less_than_total(self):
        lines = ["a", "b", "c", "d"]
        assert head_lines(lines, 2) == ["a", "b"]

    def test_count_equals_total(self):
        assert head_lines(["a", "b"], 2) == ["a", "b"]

    def test_count_greater_than_total(self):
        assert head_lines(["a"], 100) == ["a"]

    def test_empty_input(self):
        assert head_lines([], 3) == []

    def test_count_one(self):
        assert head_lines(["a", "b", "c"], 1) == ["a"]

    def test_accepts_generator(self):
        gen = (str(i) for i in range(100))
        result = head_lines(gen, 4)
        assert result == ["0", "1", "2", "3"]


# ---------------------------------------------------------------------------
# iter_tail
# ---------------------------------------------------------------------------

def test_iter_tail_yields_correct_lines():
    result = list(iter_tail(["a", "b", "c", "d"], 2))
    assert result == ["c", "d"]


def test_iter_tail_none_yields_all():
    result = list(iter_tail(["a", "b"], None))
    assert result == ["a", "b"]
