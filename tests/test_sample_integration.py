"""Integration tests: sampling applied after pipeline filtering."""

from logslice.pipeline import run_pipeline
from logslice.sample import every_nth, reservoir_sample, sample_by_rate


def _lines(*items):
    return list(items)


ERROR_LINES = [
    "2024-01-01 00:00:01 INFO  startup complete",
    "2024-01-01 00:00:02 ERROR disk full",
    "2024-01-01 00:00:03 INFO  heartbeat",
    "2024-01-01 00:00:04 ERROR network timeout",
    "2024-01-01 00:00:05 INFO  heartbeat",
    "2024-01-01 00:00:06 ERROR auth failure",
    "2024-01-01 00:00:07 INFO  heartbeat",
    "2024-01-01 00:00:08 ERROR disk full",
]


class TestSampleAfterFilter:
    """Sample from lines that have already been filtered by the pipeline."""

    def _error_lines(self):
        """Run pipeline keeping only ERROR lines."""
        return list(run_pipeline(ERROR_LINES, pattern="ERROR"))

    def test_filter_then_rate_one_keeps_all(self):
        errors = self._error_lines()
        result = list(sample_by_rate(errors, 1.0, seed=0))
        assert result == errors

    def test_filter_then_every_nth_two(self):
        errors = self._error_lines()  # 4 ERROR lines
        result = list(every_nth(errors, 2))
        assert len(result) == 2
        assert all("ERROR" in line for line in result)

    def test_filter_then_reservoir_returns_subset(self):
        errors = self._error_lines()  # 4 ERROR lines
        result = reservoir_sample(errors, 2, seed=42)
        assert len(result) == 2
        assert all("ERROR" in line for line in result)

    def test_reservoir_count_exceeds_filtered_set(self):
        errors = self._error_lines()  # 4 ERROR lines
        result = reservoir_sample(errors, 100, seed=0)
        assert sorted(result) == sorted(errors)


class TestSampleOnUnfilteredInput:
    """Sampling applied directly to raw log lines (no pattern filter)."""

    def test_every_nth_three_on_all_lines(self):
        result = list(every_nth(ERROR_LINES, 3))
        assert result == [ERROR_LINES[0], ERROR_LINES[3], ERROR_LINES[6]]

    def test_sample_rate_reproducible_across_runs(self):
        r1 = list(sample_by_rate(ERROR_LINES, 0.5, seed=21))
        r2 = list(sample_by_rate(ERROR_LINES, 0.5, seed=21))
        assert r1 == r2

    def test_reservoir_preserves_original_content(self):
        result = reservoir_sample(ERROR_LINES, 3, seed=7)
        for line in result:
            assert line in ERROR_LINES

    def test_every_nth_one_is_identity(self):
        result = list(every_nth(ERROR_LINES, 1))
        assert result == ERROR_LINES
