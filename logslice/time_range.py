"""Time range parsing and filtering for log entries."""

from datetime import datetime
from typing import Optional, Tuple

# Common log timestamp formats to try when parsing
TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%d/%b/%Y:%H:%M:%S",
    "%b %d %H:%M:%S",
]


def parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Attempt to parse a timestamp string using known formats.

    Args:
        ts_str: Raw timestamp string extracted from a log line.

    Returns:
        A datetime object if parsing succeeds, otherwise None.
    """
    ts_str = ts_str.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def parse_range(start: Optional[str], end: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse start and end boundary strings into datetime objects.

    Args:
        start: Optional lower-bound timestamp string.
        end:   Optional upper-bound timestamp string.

    Returns:
        A tuple (start_dt, end_dt) where either element may be None.

    Raises:
        ValueError: If a provided string cannot be parsed.
    """
    start_dt = None
    end_dt = None

    if start:
        start_dt = parse_timestamp(start)
        if start_dt is None:
            raise ValueError(f"Cannot parse start timestamp: {start!r}")

    if end:
        end_dt = parse_timestamp(end)
        if end_dt is None:
            raise ValueError(f"Cannot parse end timestamp: {end!r}")

    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("Start timestamp must not be later than end timestamp.")

    return start_dt, end_dt


def within_range(
    ts: datetime,
    start: Optional[datetime],
    end: Optional[datetime],
) -> bool:
    """Check whether a datetime falls within [start, end] (inclusive).

    Args:
        ts:    The timestamp to test.
        start: Lower bound (or None for no lower bound).
        end:   Upper bound (or None for no upper bound).

    Returns:
        True if ts is within the specified range.
    """
    if start and ts < start:
        return False
    if end and ts > end:
        return False
    return True
