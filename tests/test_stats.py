"""Tests for logslice.stats module."""

import pytest
from logslice.stats import FilterStats, collect_stats, format_stats


class TestFilterStats:
    def test_defaults(self):
        s = FilterStats()
        assert s.total_lines == 0
        assert s.matched_lines == 0
        assert s.match_rate == 0.0
        assert s.match_percent == 0.0

    def test_match_rate_no_lines(self):
        s = FilterStats(total_lines=0, matched_lines=0)
        assert s.match_rate == 0.0

    def test_match_rate_all_match(self):
        s = FilterStats(total_lines=10, matched_lines=10)
        assert s.match_rate == 1.0
        assert s.match_percent == pytest.approx(100.0)

    def test_match_rate_partial(self):
        s = FilterStats(total_lines=200, matched_lines=50)
        assert s.match_rate == pytest.approx(0.25)
        assert s.match_percent == pytest.approx(25.0)


class TestCollectStats:
    def _lines(self, n):
        return [f"line {i}" for i in range(n)]

    def test_all_matched(self):
        lines = self._lines(5)
        stats = collect_stats(lines, lines)
        assert stats.total_lines == 5
        assert stats.matched_lines == 5
        assert stats.skipped_lines == 0

    def test_none_matched(self):
        lines = self._lines(4)
        stats = collect_stats(lines, [])
        assert stats.matched_lines == 0
        assert stats.skipped_lines == 4

    def test_with_filtered_counts(self):
        lines = self._lines(10)
        matched = self._lines(3)
        stats = collect_stats(lines, matched, time_filtered=4, pattern_filtered=2)
        assert stats.time_filtered_lines == 4
        assert stats.pattern_filtered_lines == 2
        assert stats.skipped_lines == 1  # 10 - 3 - 4 - 2

    def test_skipped_never_negative(self):
        lines = self._lines(5)
        matched = self._lines(5)
        stats = collect_stats(lines, matched, time_filtered=3, pattern_filtered=3)
        assert stats.skipped_lines == 0

    def test_sources_default(self):
        stats = collect_stats([], [])
        assert stats.sources_processed == 1

    def test_sources_custom(self):
        stats = collect_stats([], [], sources=4)
        assert stats.sources_processed == 4

    def test_parse_errors(self):
        stats = collect_stats([], [], parse_errors=7)
        assert stats.parse_errors == 7


class TestFormatStats:
    def _make_stats(self):
        return FilterStats(
            total_lines=100,
            matched_lines=42,
            time_filtered_lines=10,
            pattern_filtered_lines=5,
            parse_errors=2,
            sources_processed=3,
        )

    def test_basic_output_contains_key_info(self):
        out = format_stats(self._make_stats())
        assert "100" in out
        assert "42" in out
        assert "42.0%" in out
        assert "Sources processed" in out

    def test_verbose_includes_extra_fields(self):
        out = format_stats(self._make_stats(), verbose=True)
        assert "Time-filtered" in out
        assert "Pattern-filtered" in out
        assert "Parse errors" in out

    def test_non_verbose_omits_extra_fields(self):
        out = format_stats(self._make_stats(), verbose=False)
        assert "Time-filtered" not in out
        assert "Parse errors" not in out
