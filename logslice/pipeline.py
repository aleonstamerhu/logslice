"""Core pipeline: wire together filter, time-range, context, and dedup."""

from typing import Iterable, Iterator, List, Optional

from logslice.extractor import extract_timestamp
from logslice.filter import compile_pattern, filter_lines
from logslice.time_range import parse_range, within_range
from logslice.context import lines_with_context
from logslice.dedup import deduplicate


def _is_match(
    line: str,
    pattern=None,
    time_range=None,
) -> bool:
    """Return True when *line* satisfies all active filters."""
    if pattern is not None and not pattern.search(line):
        return False
    if time_range is not None:
        ts = extract_timestamp(line)
        if ts is None or not within_range(ts, time_range):
            return False
    return True


def run_pipeline(
    lines: Iterable[str],
    pattern: Optional[str] = None,
    time_range_str: Optional[str] = None,
    before_context: int = 0,
    after_context: int = 0,
    dedup: bool = False,
    dedup_ignore_timestamps: bool = False,
    dedup_max_seen: Optional[int] = None,
) -> Iterator[str]:
    """Run the full log-processing pipeline.

    Steps (in order):
      1. Compile regex pattern (if provided).
      2. Parse time range (if provided).
      3. Filter lines using pattern + time range.
      4. Expand with before/after context lines.
      5. Optionally deduplicate output.

    Args:
        lines: Raw input lines.
        pattern: Optional regex string.
        time_range_str: Optional time range like ``start,end``.
        before_context: Number of lines to include before each match.
        after_context: Number of lines to include after each match.
        dedup: If True, deduplicate output lines.
        dedup_ignore_timestamps: Passed to :func:`deduplicate`.
        dedup_max_seen: Passed to :func:`deduplicate`.

    Yields:
        Processed log lines.
    """
    compiled = compile_pattern(pattern) if pattern else None
    tr = parse_range(time_range_str) if time_range_str else None

    def match_fn(line: str) -> bool:
        return _is_match(line, pattern=compiled, time_range=tr)

    buffered: List[str] = list(lines)

    result: Iterable[str]
    if before_context > 0 or after_context > 0:
        result = lines_with_context(
            buffered,
            match_fn,
            before=before_context,
            after=after_context,
        )
    else:
        result = (line for line in buffered if match_fn(line))

    if dedup:
        result = deduplicate(
            result,
            ignore_timestamps=dedup_ignore_timestamps,
            max_seen=dedup_max_seen,
        )

    yield from result
