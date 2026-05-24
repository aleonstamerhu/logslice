"""Deduplication utilities for log lines."""

import hashlib
from typing import Iterable, Iterator, Optional


def _line_key(line: str, ignore_timestamps: bool) -> str:
    """Return a hashable key for a log line."""
    if ignore_timestamps:
        # Strip leading timestamp-like prefix (up to first ]: or ] )
        import re
        stripped = re.sub(
            r'^[\[\(]?[\d\-T:.Z /]+[\]\)]?\s*',
            '',
            line.strip()
        )
        return stripped
    return line.strip()


def deduplicate(
    lines: Iterable[str],
    ignore_timestamps: bool = False,
    max_seen: Optional[int] = None,
) -> Iterator[str]:
    """Yield unique log lines, optionally ignoring timestamp differences.

    Args:
        lines: Input log lines.
        ignore_timestamps: If True, lines differing only in timestamp are
            considered duplicates.
        max_seen: If set, only suppress a duplicate after it has appeared
            this many times (e.g. max_seen=2 keeps first two occurrences).

    Yields:
        Deduplicated lines.
    """
    seen: dict[str, int] = {}
    for line in lines:
        key = _line_key(line, ignore_timestamps)
        count = seen.get(key, 0)
        threshold = max_seen if max_seen is not None else 1
        if count < threshold:
            seen[key] = count + 1
            yield line
        else:
            seen[key] = count + 1


def count_duplicates(
    lines: Iterable[str],
    ignore_timestamps: bool = False,
) -> dict[str, int]:
    """Return a mapping of line key -> occurrence count."""
    counts: dict[str, int] = {}
    for line in lines:
        key = _line_key(line, ignore_timestamps)
        counts[key] = counts.get(key, 0) + 1
    return counts
