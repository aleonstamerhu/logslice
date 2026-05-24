"""Integration tests: fold_lines applied to pipeline output."""

from __future__ import annotations

from typing import List

from logslice.fold import fold_lines
from logslice.pipeline import run_pipeline


def _run(lines: List[str], pattern: str | None = None) -> List[str]:
    """Run pipeline then fold the results."""
    matched = list(run_pipeline(lines, pattern=pattern))
    return list(fold_lines(matched))


LOG_LINES = [
    "2024-01-10T08:00:01 INFO  service started\n",
    "2024-01-10T08:00:02 ERROR disk full on /dev/sda1\n",
    "2024-01-10T08:00:03 ERROR disk full on /dev/sda1\n",
    "2024-01-10T08:00:04 ERROR disk full on /dev/sda1\n",
    "2024-01-10T08:00:05 WARN  retrying connection attempt 1\n",
    "2024-01-10T08:00:06 WARN  retrying connection attempt 2\n",
    "2024-01-10T08:00:07 WARN  retrying connection attempt 3\n",
    "2024-01-10T08:00:08 INFO  service stopped\n",
]


class TestFoldAfterFilter:
    def test_no_filter_folds_repeated_errors(self):
        result = _run(LOG_LINES)
        # The three identical ERROR lines should be folded
        error_lines = [l for l in result if "ERROR" in l]
        assert len(error_lines) == 1
        annotations = [l for l in result if "repeated 3" in l]
        assert len(annotations) == 1

    def test_filter_then_fold_warn_lines(self):
        result = _run(LOG_LINES, pattern="WARN")
        # All three WARN lines have different numeric suffixes → same fold key
        # so they should be folded into one
        warn_lines = [l for l in result if "WARN" in l]
        assert len(warn_lines) == 1
        assert any("repeated 3" in l for l in result)

    def test_no_repeats_passes_through_unchanged(self):
        result = _run(LOG_LINES, pattern="INFO")
        # Two INFO lines with different text → no folding
        info_lines = [l for l in result if "INFO" in l]
        assert len(info_lines) == 2
        assert not any("repeated" in l for l in result)

    def test_empty_pipeline_output(self):
        result = _run(LOG_LINES, pattern="CRITICAL")
        assert result == []

    def test_single_match_no_annotation(self):
        result = _run(LOG_LINES, pattern="service started")
        assert len(result) == 1
        assert not any("repeated" in l for l in result)
