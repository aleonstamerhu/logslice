"""Burst detection: identify time windows with unusually high log volume."""

from datetime import datetime, timedelta
from typing import Iterable, List, NamedTuple, Optional

from logslice.extractor import extract_timestamp


class BurstWindow(NamedTuple):
    start: datetime
    end: datetime
    count: int
    lines: List[str]


def detect_bursts(
    lines: Iterable[str],
    window_seconds: int = 60,
    threshold: int = 10,
) -> List[BurstWindow]:
    """Return windows where line count exceeds *threshold* within *window_seconds*."""
    if window_seconds <= 0:
        raise ValueError("window_seconds must be positive")
    if threshold <= 0:
        raise ValueError("threshold must be positive")

    timestamped: List[tuple] = []
    for line in lines:
        ts = extract_timestamp(line)
        if ts is not None:
            timestamped.append((ts, line))

    if not timestamped:
        return []

    delta = timedelta(seconds=window_seconds)
    bursts: List[BurstWindow] = []
    n = len(timestamped)
    left = 0

    for right in range(n):
        while timestamped[right][0] - timestamped[left][0] > delta:
            left += 1
        count = right - left + 1
        if count >= threshold:
            window_lines = [t[1] for t in timestamped[left : right + 1]]
            start_ts = timestamped[left][0]
            end_ts = timestamped[right][0]
            # Avoid duplicating windows that are strict subsets of the previous
            if bursts and bursts[-1].start == start_ts and bursts[-1].end <= end_ts:
                bursts[-1] = BurstWindow(start_ts, end_ts, count, window_lines)
            else:
                bursts.append(BurstWindow(start_ts, end_ts, count, window_lines))

    return bursts


def format_burst(burst: BurstWindow) -> str:
    """Return a human-readable summary line for a burst window."""
    fmt = "%Y-%m-%d %H:%M:%S"
    return (
        f"[BURST] {burst.start.strftime(fmt)} -> {burst.end.strftime(fmt)} "
        f"| {burst.count} lines"
    )
