"""Log line filtering with regex and time-range support."""

import re
from typing import Iterator, Optional, Tuple

from logslice.extractor import extract_timestamp
from logslice.time_range import within_range


def compile_pattern(pattern: Optional[str]) -> Optional[re.Pattern]:
    """Compile a regex pattern string, returning None if pattern is None."""
    if pattern is None:
        return None
    return re.compile(pattern)


def filter_lines(
    lines: Iterator[str],
    pattern: Optional[re.Pattern] = None,
    time_range: Optional[Tuple] = None,
    invert: bool = False,
) -> Iterator[str]:
    """
    Filter log lines by regex pattern and/or time range.

    Args:
        lines: Iterable of log line strings.
        pattern: Compiled regex pattern to match against each line.
        time_range: Tuple of (start, end) datetime objects from parse_range.
        invert: If True, yield lines that do NOT match the pattern.

    Yields:
        Lines that pass all active filters.
    """
    for line in lines:
        stripped = line.rstrip("\n")

        if pattern is not None:
            matched = bool(pattern.search(stripped))
            if invert and matched:
                continue
            if not invert and not matched:
                continue

        if time_range is not None:
            ts = extract_timestamp(stripped)
            if ts is not None and not within_range(ts, time_range):
                continue

        yield stripped


def count_matches(
    lines: Iterator[str],
    pattern: Optional[re.Pattern] = None,
    time_range: Optional[Tuple] = None,
) -> int:
    """Return the number of lines matching the given filters."""
    return sum(1 for _ in filter_lines(lines, pattern=pattern, time_range=time_range))
