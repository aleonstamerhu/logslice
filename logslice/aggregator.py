"""Log aggregation: count occurrences grouped by regex capture groups or time buckets."""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from logslice.extractor import extract_timestamp


def aggregate_by_pattern(
    lines: Iterable[str],
    pattern: re.Pattern,
    group: int = 0,
) -> Counter:
    """Count lines grouped by a regex match (full match or capture group).

    Args:
        lines: Iterable of log lines.
        pattern: Compiled regex pattern.
        group: Capture group index (0 = full match).

    Returns:
        Counter mapping group value -> count.
    """
    counts: Counter = Counter()
    for line in lines:
        m = pattern.search(line)
        if m:
            try:
                key = m.group(group)
            except IndexError:
                key = m.group(0)
            counts[key] += 1
    return counts


def aggregate_by_time_bucket(
    lines: Iterable[str],
    bucket_seconds: int = 60,
    timestamp_formats: Optional[List[str]] = None,
) -> Dict[datetime, int]:
    """Count log lines grouped into fixed-size time buckets.

    Args:
        lines: Iterable of log lines.
        bucket_seconds: Size of each time bucket in seconds.
        timestamp_formats: Optional list of strptime format strings.

    Returns:
        Dict mapping bucket start datetime -> count, sorted by key.
    """
    counts: Dict[datetime, int] = defaultdict(int)
    delta = timedelta(seconds=bucket_seconds)

    for line in lines:
        ts = extract_timestamp(line, formats=timestamp_formats)
        if ts is None:
            continue
        # Floor to bucket boundary
        epoch = datetime(1970, 1, 1)
        total_seconds = int((ts - epoch).total_seconds())
        bucket_start_seconds = (total_seconds // bucket_seconds) * bucket_seconds
        bucket_dt = epoch + timedelta(seconds=bucket_start_seconds)
        counts[bucket_dt] += 1

    return dict(sorted(counts.items()))


def format_aggregation(counts: Counter, top_n: Optional[int] = None) -> List[str]:
    """Format aggregation results as human-readable lines.

    Args:
        counts: Counter of key -> count.
        top_n: If set, only return the top N entries.

    Returns:
        List of formatted strings "<count>\t<key>".
    """
    items = counts.most_common(top_n)
    return [f"{count}\t{key}" for key, count in items]
