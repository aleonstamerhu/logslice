"""Tests for logslice.burst."""

from datetime import datetime, timedelta

import pytest

from logslice.burst import BurstWindow, detect_bursts, format_burst


def _make_lines(base: datetime, count: int, gap_seconds: int = 5) -> list:
    lines = []
    for i in range(count):
        ts = base + timedelta(seconds=i * gap_seconds)
        lines.append(ts.strftime("%Y-%m-%d %H:%M:%S") + f" INFO message {i}")
    return lines


class TestDetectBursts:
    def test_empty_input_returns_empty(self):
        assert detect_bursts([]) == []

    def test_no_timestamps_returns_empty(self):
        lines = ["no timestamp here", "another plain line"]
        assert detect_bursts(lines, window_seconds=60, threshold=2) == []

    def test_single_burst_detected(self):
        base = datetime(2024, 1, 1, 12, 0, 0)
        lines = _make_lines(base, count=15, gap_seconds=3)
        bursts = detect_bursts(lines, window_seconds=60, threshold=10)
        assert len(bursts) >= 1
        assert bursts[0].count >= 10

    def test_no_burst_when_lines_spread_out(self):
        base = datetime(2024, 1, 1, 0, 0, 0)
        lines = _make_lines(base, count=5, gap_seconds=120)
        bursts = detect_bursts(lines, window_seconds=60, threshold=3)
        assert bursts == []

    def test_threshold_exactly_met(self):
        base = datetime(2024, 1, 1, 8, 0, 0)
        lines = _make_lines(base, count=5, gap_seconds=10)
        bursts = detect_bursts(lines, window_seconds=60, threshold=5)
        assert len(bursts) >= 1

    def test_threshold_not_met(self):
        base = datetime(2024, 1, 1, 8, 0, 0)
        lines = _make_lines(base, count=4, gap_seconds=10)
        bursts = detect_bursts(lines, window_seconds=60, threshold=5)
        assert bursts == []

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            detect_bursts([], window_seconds=0)

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            detect_bursts([], threshold=0)

    def test_burst_window_contains_lines(self):
        base = datetime(2024, 3, 15, 10, 0, 0)
        lines = _make_lines(base, count=12, gap_seconds=4)
        bursts = detect_bursts(lines, window_seconds=60, threshold=10)
        assert len(bursts) >= 1
        for burst in bursts:
            assert len(burst.lines) == burst.count

    def test_burst_start_before_end(self):
        base = datetime(2024, 3, 15, 10, 0, 0)
        lines = _make_lines(base, count=12, gap_seconds=4)
        bursts = detect_bursts(lines, window_seconds=60, threshold=10)
        for burst in bursts:
            assert burst.start <= burst.end


class TestFormatBurst:
    def test_format_output_contains_burst_label(self):
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 45)
        burst = BurstWindow(start=start, end=end, count=20, lines=[])
        result = format_burst(burst)
        assert "[BURST]" in result
        assert "20 lines" in result

    def test_format_includes_timestamps(self):
        start = datetime(2024, 6, 15, 9, 30, 0)
        end = datetime(2024, 6, 15, 9, 30, 55)
        burst = BurstWindow(start=start, end=end, count=11, lines=[])
        result = format_burst(burst)
        assert "2024-06-15 09:30:00" in result
        assert "2024-06-15 09:30:55" in result
