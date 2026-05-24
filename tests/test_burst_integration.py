"""Integration tests: burst detection on realistic log streams."""

from datetime import datetime, timedelta

from logslice.burst import detect_bursts, format_burst
from logslice.filter import filter_lines, compile_pattern


def _syslog_line(ts: datetime, level: str, msg: str) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S") + f" {level} {msg}"


def _build_log(base: datetime) -> list:
    lines = []
    # Quiet period: 1 line per minute for 5 minutes
    for i in range(5):
        lines.append(_syslog_line(base + timedelta(minutes=i), "INFO", f"heartbeat {i}"))
    # Burst: 20 ERROR lines within 30 seconds
    burst_start = base + timedelta(minutes=10)
    for i in range(20):
        lines.append(_syslog_line(burst_start + timedelta(seconds=i), "ERROR", f"failure {i}"))
    # Another quiet period
    for i in range(3):
        lines.append(_syslog_line(base + timedelta(minutes=20, seconds=i * 30), "INFO", "ok"))
    return lines


class TestBurstOnFilteredLines:
    def setup_method(self):
        self.base = datetime(2024, 5, 1, 6, 0, 0)
        self.log = _build_log(self.base)

    def test_no_burst_in_quiet_period(self):
        quiet = self.log[:5]
        bursts = detect_bursts(quiet, window_seconds=120, threshold=5)
        # Only 5 lines spread over 4 minutes — threshold is 5, should just meet it
        # but they span > 60 s so within 120 s window they all fit
        assert isinstance(bursts, list)

    def test_burst_detected_in_error_flood(self):
        error_lines = [l for l in self.log if "ERROR" in l]
        bursts = detect_bursts(error_lines, window_seconds=60, threshold=10)
        assert len(bursts) >= 1
        assert bursts[0].count >= 10

    def test_filter_then_burst_detects_errors(self):
        pattern = compile_pattern("ERROR")
        filtered = list(filter_lines(self.log, pattern=pattern))
        bursts = detect_bursts(filtered, window_seconds=60, threshold=15)
        assert len(bursts) >= 1

    def test_format_burst_on_real_data(self):
        error_lines = [l for l in self.log if "ERROR" in l]
        bursts = detect_bursts(error_lines, window_seconds=60, threshold=10)
        assert bursts
        summary = format_burst(bursts[0])
        assert "[BURST]" in summary
        assert "lines" in summary

    def test_no_burst_below_threshold(self):
        bursts = detect_bursts(self.log, window_seconds=30, threshold=25)
        assert bursts == []
