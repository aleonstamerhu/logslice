"""Extract timestamps from raw log lines using configurable regex patterns."""

import re
from datetime import datetime
from typing import Optional

from logslice.time_range import parse_timestamp

# Ordered list of (pattern, group_name_or_index) tuples.
# Each pattern should capture the timestamp portion of a log line.
_TIMESTAMP_PATTERNS = [
    # ISO-8601 / RFC-3339 style: 2024-01-15T12:34:56 or with microseconds
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"),
    # Apache / nginx combined log: [15/Jan/2024:12:34:56
    re.compile(r"\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})"),
    # Syslog style: Jan 15 12:34:56
    re.compile(r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"),
]


def extract_timestamp(line: str, custom_pattern: Optional[str] = None) -> Optional[datetime]:
    """Extract and parse the first timestamp found in a log line.

    Args:
        line:           A single log line string.
        custom_pattern: An optional regex string with one capture group for
                        the timestamp.  Takes priority over built-in patterns.

    Returns:
        A datetime object if a timestamp is found and parsed, else None.
    """
    patterns = []
    if custom_pattern:
        try:
            patterns.append(re.compile(custom_pattern))
        except re.error as exc:
            raise ValueError(f"Invalid custom timestamp pattern: {exc}") from exc
    patterns.extend(_TIMESTAMP_PATTERNS)

    for pattern in patterns:
        match = pattern.search(line)
        if match:
            raw = match.group(1)
            dt = parse_timestamp(raw)
            if dt is not None:
                return dt
    return None
