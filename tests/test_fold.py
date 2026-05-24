"""Tests for logslice.fold."""

import pytest

from logslice.fold import _fold_key, fold_lines, count_folded


# ---------------------------------------------------------------------------
# _fold_key
# ---------------------------------------------------------------------------

class TestFoldKey:
    def test_plain_text_unchanged(self):
        assert _fold_key("hello world") == "hello world"

    def test_integers_replaced(self):
        assert _fold_key("retry 3 of 10") == "retry <N> of <N>"

    def test_ipv4_replaced(self):
        assert _fold_key("connect 192.168.1.1 ok") == "connect <N>.<N>.<N>.<N> ok"

    def test_uuid_replaced(self):
        line = "id=550e8400-e29b-41d4-a716-446655440000 done"
        key = _fold_key(line)
        assert "550e8400" not in key
        assert "<N>" in key

    def test_trailing_newline_stripped(self):
        assert _fold_key("abc 1\n") == "abc <N>"


# ---------------------------------------------------------------------------
# fold_lines
# ---------------------------------------------------------------------------

def _collect(lines, **kw):
    return list(fold_lines(lines, **kw))


class TestFoldLines:
    def test_empty_input(self):
        assert _collect([]) == []

    def test_single_line_no_fold(self):
        result = _collect(["hello\n"])
        assert result == ["hello\n"]

    def test_two_identical_lines_folded(self):
        result = _collect(["error\n", "error\n"])
        assert result[0] == "error\n"
        assert "repeated 2 times" in result[1]

    def test_run_below_min_repeat_not_folded(self):
        result = _collect(["warn\n", "warn\n"], min_repeat=3)
        # both lines emitted, no annotation
        assert len(result) == 2
        assert all("repeated" not in l for l in result)

    def test_three_identical_lines_single_annotation(self):
        result = _collect(["x\n"] * 3)
        assert sum(1 for l in result if "repeated" in l) == 1
        assert "repeated 3 times" in result[1]

    def test_non_repeating_lines_pass_through(self):
        lines = ["a\n", "b\n", "c\n"]
        result = _collect(lines)
        assert result == lines

    def test_mixed_runs(self):
        lines = ["a\n", "a\n", "a\n", "b\n", "b\n"]
        result = _collect(lines)
        assert result[0] == "a\n"
        assert "repeated 3" in result[1]
        assert result[2] == "b\n"
        assert "repeated 2" in result[3]

    def test_lines_without_newline_get_newline(self):
        result = _collect(["no newline"])
        assert result[0].endswith("\n")

    def test_similar_numeric_lines_folded(self):
        lines = ["retry 1 of 5\n", "retry 2 of 5\n", "retry 3 of 5\n"]
        result = _collect(lines)
        assert "repeated 3" in result[1]

    def test_min_repeat_below_2_raises(self):
        with pytest.raises(ValueError):
            _collect(["x\n"], min_repeat=1)


# ---------------------------------------------------------------------------
# count_folded
# ---------------------------------------------------------------------------

class TestCountFolded:
    def test_no_repeats(self):
        out, away = count_folded(["a\n", "b\n", "c\n"])
        assert out == 3
        assert away == 0

    def test_all_same(self):
        out, away = count_folded(["x\n"] * 5)
        assert out == 1
        assert away == 4

    def test_partial_fold(self):
        lines = ["a\n", "a\n", "b\n"]
        out, away = count_folded(lines)
        assert out == 2   # "a" + "b"
        assert away == 1
