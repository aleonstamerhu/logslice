"""Integration tests for deduplication within the full pipeline."""

import pytest
from logslice.pipeline import run_pipeline


def _run(lines, **kwargs):
    """Helper to run pipeline and collect results as a list."""
    return list(run_pipeline(iter(lines), **kwargs))


SAMPLE_LINES = [
    "2024-01-15T10:00:01 ERROR connection refused",
    "2024-01-15T10:00:02 ERROR connection refused",
    "2024-01-15T10:00:03 INFO  service started",
    "2024-01-15T10:00:04 ERROR connection refused",
    "2024-01-15T10:00:05 INFO  service started",
    "2024-01-15T10:00:06 WARN  disk usage high",
    "2024-01-15T10:00:07 WARN  disk usage high",
    "2024-01-15T10:00:08 ERROR connection refused",
]


class TestDedupWithPatternFilter:
    """Deduplication combined with pattern filtering."""

    def test_dedup_after_pattern_filter(self):
        """Dedup should apply after pattern filtering reduces the set."""
        results = _run(
            SAMPLE_LINES,
            pattern="ERROR",
            dedup=True,
            ignore_timestamps=True,
        )
        # All ERROR lines have the same message after stripping timestamp
        assert len(results) == 1
        assert "ERROR" in results[0]

    def test_dedup_warn_lines(self):
        """WARN lines should be deduped to a single entry."""
        results = _run(
            SAMPLE_LINES,
            pattern="WARN",
            dedup=True,
            ignore_timestamps=True,
        )
        assert len(results) == 1
        assert "WARN" in results[0]

    def test_no_dedup_returns_all_matches(self):
        """Without dedup, all matching lines are returned."""
        results = _run(
            SAMPLE_LINES,
            pattern="ERROR",
            dedup=False,
        )
        assert len(results) == 4

    def test_dedup_exact_with_pattern(self):
        """Exact dedup (timestamps not ignored) keeps lines with different timestamps."""
        results = _run(
            SAMPLE_LINES,
            pattern="ERROR",
            dedup=True,
            ignore_timestamps=False,
        )
        # Each ERROR line has a unique timestamp, so none are deduped
        assert len(results) == 4


class TestDedupAllLines:
    """Deduplication applied to the full unfiltered log."""

    def test_dedup_reduces_total_lines(self):
        """Total unique lines (ignoring timestamps) should be fewer than input."""
        results = _run(
            SAMPLE_LINES,
            dedup=True,
            ignore_timestamps=True,
        )
        # Unique messages: ERROR connection refused, INFO service started,
        # WARN disk usage high => 3 unique
        assert len(results) == 3

    def test_dedup_preserves_first_occurrence(self):
        """The first occurrence of each unique line should be kept."""
        results = _run(
            SAMPLE_LINES,
            dedup=True,
            ignore_timestamps=True,
        )
        messages = [line.split(None, 2)[-1].strip() for line in results]
        assert "connection refused" in messages
        assert "service started" in messages
        assert "disk usage high" in messages

    def test_no_dedup_passthrough(self):
        """Without dedup, all lines pass through unchanged."""
        results = _run(SAMPLE_LINES, dedup=False)
        assert results == SAMPLE_LINES


class TestDedupEdgeCases:
    """Edge cases for deduplication integration."""

    def test_empty_input(self):
        """Empty input should produce empty output."""
        results = _run([], dedup=True, ignore_timestamps=True)
        assert results == []

    def test_single_line(self):
        """A single line should pass through dedup unchanged."""
        results = _run(
            ["2024-01-15T10:00:01 INFO only one line"],
            dedup=True,
            ignore_timestamps=True,
        )
        assert len(results) == 1

    def test_all_unique_lines(self):
        """All unique lines should all pass through dedup."""
        lines = [
            "2024-01-15T10:00:01 INFO  alpha",
            "2024-01-15T10:00:02 INFO  beta",
            "2024-01-15T10:00:03 INFO  gamma",
        ]
        results = _run(lines, dedup=True, ignore_timestamps=True)
        assert len(results) == 3

    def test_all_duplicate_lines(self):
        """All identical lines should collapse to one."""
        lines = ["2024-01-15T10:00:0{} INFO  same message".format(i) for i in range(5)]
        results = _run(lines, dedup=True, ignore_timestamps=True)
        assert len(results) == 1
        assert "same message" in results[0]
