"""Integration tests for deduplication inside run_pipeline."""

import pytest
from logslice.pipeline import run_pipeline


def _run(lines, **kwargs):
    return list(run_pipeline(lines, **kwargs))


LINES_WITH_DUPS = [
    "2024-01-01T00:00:01 ERROR disk full\n",
    "2024-01-01T00:00:02 INFO  started\n",
    "2024-01-01T00:00:03 ERROR disk full\n",
    "2024-01-01T00:00:04 ERROR disk full\n",
    "2024-01-01T00:00:05 INFO  stopped\n",
]


class TestPipelineDedup:
    def test_no_dedup_returns_all(self):
        result = _run(LINES_WITH_DUPS)
        assert result == LINES_WITH_DUPS

    def test_dedup_exact_removes_duplicates(self):
        lines = ["foo\n", "bar\n", "foo\n", "baz\n"]
        result = _run(lines, dedup=True)
        assert result == ["foo\n", "bar\n", "baz\n"]

    def test_dedup_ignore_timestamps(self):
        result = _run(LINES_WITH_DUPS, dedup=True, dedup_ignore_timestamps=True)
        # "ERROR disk full" appears 3 times; only first should survive
        error_lines = [l for l in result if "ERROR" in l]
        assert len(error_lines) == 1
        assert "INFO  started" in result[1]
        assert "INFO  stopped" in result[2]

    def test_dedup_max_seen(self):
        lines = ["x\n"] * 6
        result = _run(lines, dedup=True, dedup_max_seen=2)
        assert result == ["x\n", "x\n"]

    def test_dedup_combined_with_pattern(self):
        lines = [
            "ERROR something\n",
            "INFO  ok\n",
            "ERROR something\n",
            "ERROR different\n",
        ]
        result = _run(lines, pattern="ERROR", dedup=True)
        assert result == ["ERROR something\n", "ERROR different\n"]

    def test_dedup_empty_input(self):
        assert _run([], dedup=True) == []

    def test_dedup_all_unique_unchanged(self):
        lines = ["a\n", "b\n", "c\n"]
        assert _run(lines, dedup=True) == lines

    def test_dedup_with_context_lines(self):
        lines = [
            "before\n",
            "MATCH\n",
            "after\n",
            "before\n",
            "MATCH\n",
            "after\n",
        ]
        result = _run(
            lines,
            pattern="MATCH",
            before_context=1,
            after_context=1,
            dedup=True,
        )
        # context expansion yields before/MATCH/after twice; dedup collapses
        assert result.count("MATCH\n") == 1
        assert result.count("before\n") == 1
        assert result.count("after\n") == 1
