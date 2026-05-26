"""Sliding window line buffer for logslice.

Provides a fixed-size rolling buffer that retains the last N lines,
useful for look-back analysis and context-window aggregation.
"""

from collections import deque
from typing import Iterable, Iterator, List, Optional


class SlidingWindow:
    """A fixed-capacity deque-backed sliding window of lines."""

    def __init__(self, size: int) -> None:
        if size < 1:
            raise ValueError(f"Window size must be >= 1, got {size}")
        self._size = size
        self._buf: deque = deque(maxlen=size)

    @property
    def size(self) -> int:
        return self._size

    def push(self, line: str) -> None:
        """Add a line to the window, evicting the oldest if full."""
        self._buf.append(line)

    def snapshot(self) -> List[str]:
        """Return a copy of the current window contents (oldest first)."""
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)

    def __iter__(self) -> Iterator[str]:
        return iter(self._buf)


def window_lines(
    lines: Iterable[str],
    size: int,
    predicate,
    include_window: bool = True,
) -> Iterator[List[str]]:
    """Yield windows of *size* lines centred on lines matching *predicate*.

    For each matching line the function yields a list containing the
    window snapshot at the moment of the match.  When *include_window*
    is False only the matching line itself is yielded (as a one-element
    list).
    """
    win = SlidingWindow(size)
    for line in lines:
        win.push(line)
        if predicate(line):
            yield win.snapshot() if include_window else [line]


def flatten_windows(
    lines: Iterable[str],
    size: int,
    predicate,
) -> Iterator[str]:
    """Yield individual lines from all windows that contain a match.

    Duplicate lines that appear in overlapping windows are emitted only
    once (de-duplication is position-based using object identity of the
    original strings is not reliable, so we track by content+index).
    """
    seen_indices: set = set()
    buf: List[str] = []
    win = SlidingWindow(size)
    idx = 0
    for line in lines:
        win.push(line)
        buf.append(line)
        if predicate(line):
            start = max(0, idx - size + 1)
            for offset, wline in enumerate(win.snapshot()):
                abs_idx = start + offset
                if abs_idx not in seen_indices:
                    seen_indices.add(abs_idx)
                    yield wline
        idx += 1
