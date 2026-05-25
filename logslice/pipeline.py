"""Pipeline: compose filter, dedup, rate-limit, tail, and sample steps."""

from __future__ import annotations

import re
from typing import Iterable, Iterator, List, Optional

from logslice.extractor import extract_timestamp
from logslice.time_range import within_range


def _is_match(
    line: str,
    pattern: Optional[re.Pattern],
    time_range=None,
) -> bool:
    if pattern is not None and not pattern.search(line):
        return False
    if time_range is not None:
        ts = extract_timestamp(line)
        if ts is not None and not within_range(ts, time_range):
            return False
    return True


def run_pipeline(
    lines: Iterable[str],
    pattern: Optional[re.Pattern] = None,
    time_range=None,
    dedup: bool = False,
    ignore_timestamps: bool = False,
    max_per_bucket: Optional[int] = None,
    bucket_seconds: int = 60,
    tail: Optional[int] = None,
    head: Optional[int] = None,
    sample_rate: Optional[float] = None,
    every_nth: Optional[int] = None,
    max_length: Optional[int] = None,
) -> Iterator[str]:
    """Run lines through the full processing pipeline."""
    from logslice.dedup import deduplicate
    from logslice.rate import rate_limit
    from logslice.tail import tail_lines, head_lines
    from logslice.sample import sample_by_rate, every_nth as every_nth_fn
    from logslice.truncate import truncate_lines

    matched: Iterable[str] = (
        line for line in lines if _is_match(line, pattern, time_range)
    )

    if dedup:
        matched = deduplicate(matched, ignore_timestamps=ignore_timestamps)

    if max_per_bucket is not None:
        matched = rate_limit(matched, max_per_bucket, bucket_seconds)

    result: List[str] = list(matched)

    if head is not None and (head > 0):
        result = head_lines(result, head)
    elif tail is not None and (tail > 0):
        result = tail_lines(result, tail)

    if sample_rate is not None:
        result = list(sample_by_rate(result, sample_rate))
    elif every_nth is not None:
        result = list(every_nth_fn(result, every_nth))

    if max_length is not None:
        result = list(truncate_lines(result, max_length))

    return iter(result)


def match_fn(
    pattern: Optional[re.Pattern] = None,
    time_range=None,
):
    """Return a predicate that tests a single line."""
    def _fn(line: str) -> bool:
        return _is_match(line, pattern, time_range)
    return _fn
