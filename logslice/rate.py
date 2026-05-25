"""Rate limiting: emit at most N lines per time bucket."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.extractor import extract_timestamp


def rate_limit(
    lines: Iterable[str],
    max_per_bucket: int,
    bucket_seconds: int = 60,
) -> Iterator[str]:
    """Yield at most *max_per_bucket* lines per time bucket of *bucket_seconds*.

    Lines without a parseable timestamp are always emitted.
    """
    if max_per_bucket <= 0:
        raise ValueError("max_per_bucket must be a positive integer")
    if bucket_seconds <= 0:
        raise ValueError("bucket_seconds must be a positive integer")

    bucket_start: Optional[datetime] = None
    bucket_count: int = 0
    delta = timedelta(seconds=bucket_seconds)

    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            yield line
            continue

        if bucket_start is None or ts >= bucket_start + delta:
            bucket_start = ts
            bucket_count = 0

        if bucket_count < max_per_bucket:
            bucket_count += 1
            yield line


def count_suppressed(
    lines: Iterable[str],
    max_per_bucket: int,
    bucket_seconds: int = 60,
) -> int:
    """Return the number of lines suppressed by rate limiting."""
    original = list(lines)
    kept = list(rate_limit(iter(original), max_per_bucket, bucket_seconds))
    return len(original) - len(kept)
