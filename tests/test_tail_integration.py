"""Integration tests: tail/head combined with the filter pipeline."""

from __future__ import annotations

from typing import List, Optional

from logslice.filter import compile_pattern, filter_lines
from logslice.tail import head_lines, tail_lines


def _run(
    raw_lines: List[str],
    pattern: Optional[str] = None,
    tail: Optional[int] = None,
    head: Optional[int] = None,
) -> List[str]:
    """Filter then slice — mirrors typical pipeline order."""
    regex = compile_pattern(pattern)
    filtered = list(filter_lines(raw_lines, pattern=regex))
    if tail is not None:
        filtered = tail_lines(filtered, tail)
    if head is not None:
        filtered = head_lines(filtered, head)
    return filtered


LOGS = [
    "2024-01-01 INFO  server started\n",
    "2024-01-01 ERROR disk full\n",
    "2024-01-01 INFO  request ok\n",
    "2024-01-01 ERROR timeout\n",
    "2024-01-01 INFO  shutdown\n",
    "2024-01-01 ERROR connection refused\n",
]


class TestTailAfterFilter:
    def test_tail_errors_last_two(self):
        result = _run(LOGS, pattern="ERROR", tail=2)
        assert len(result) == 2
        assert "timeout" in result[0]
        assert "connection refused" in result[1]

    def test_tail_larger_than_matches_returns_all(self):
        result = _run(LOGS, pattern="ERROR", tail=100)
        assert len(result) == 3

    def test_tail_one_returns_last_match(self):
        result = _run(LOGS, pattern="ERROR", tail=1)
        assert len(result) == 1
        assert "connection refused" in result[0]

    def test_tail_no_pattern_last_n_lines(self):
        result = _run(LOGS, tail=3)
        assert result == LOGS[-3:]


class TestHeadAfterFilter:
    def test_head_errors_first_two(self):
        result = _run(LOGS, pattern="ERROR", head=2)
        assert len(result) == 2
        assert "disk full" in result[0]
        assert "timeout" in result[1]

    def test_head_one_returns_first_match(self):
        result = _run(LOGS, pattern="ERROR", head=1)
        assert len(result) == 1
        assert "disk full" in result[0]

    def test_head_no_pattern_first_n_lines(self):
        result = _run(LOGS, head=2)
        assert result == LOGS[:2]


class TestHeadAndTailCombined:
    def test_tail_then_head_gives_middle_slice(self):
        # tail=4 of all 6 → lines 2-5; head=2 → lines 2-3
        result = _run(LOGS, tail=4, head=2)
        assert result == LOGS[2:4]

    def test_empty_after_filter_tail_returns_empty(self):
        result = _run(LOGS, pattern="CRITICAL", tail=3)
        assert result == []

    def test_empty_after_filter_head_returns_empty(self):
        result = _run(LOGS, pattern="CRITICAL", head=3)
        assert result == []
