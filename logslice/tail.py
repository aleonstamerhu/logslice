"""Tail support: read the last N lines from a stream or list."""

from __future__ import annotations

from collections import deque
from typing import Iterable, Iterator, List, Optional


def tail_lines(
    lines: Iterable[str],
    count: Optional[int],
) -> List[str]:
    """Return the last *count* lines from *lines*.

    If *count* is None or non-positive, all lines are returned.

    Parameters
    ----------
    lines:
        Any iterable of log line strings.
    count:
        Maximum number of trailing lines to keep.

    Returns
    -------
    list[str]
        The (up to) *count* last lines, preserving original order.
    """
    if count is None or count <= 0:
        return list(lines)
    buf: deque[str] = deque(maxlen=count)
    for line in lines:
        buf.append(line)
    return list(buf)


def head_lines(
    lines: Iterable[str],
    count: Optional[int],
) -> List[str]:
    """Return the first *count* lines from *lines*.

    If *count* is None or non-positive, all lines are returned.

    Parameters
    ----------
    lines:
        Any iterable of log line strings.
    count:
        Maximum number of leading lines to keep.

    Returns
    -------
    list[str]
        The (up to) *count* first lines.
    """
    if count is None or count <= 0:
        return list(lines)
    result: List[str] = []
    for line in lines:
        result.append(line)
        if len(result) >= count:
            break
    return result


def iter_tail(lines: Iterable[str], count: Optional[int]) -> Iterator[str]:
    """Yield the last *count* lines; convenience iterator wrapper."""
    yield from tail_lines(lines, count)
