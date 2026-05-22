"""Timestamp extraction from raw log lines."""

import re
from datetime import datetime
from typing import List, Optional

# Default timestamp formats tried in order
DEFAULT_FORMATS: List[str] = [
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%b %d %H:%M:%S",   # syslog: Jan  5 10:00:01
    "%b  %d %H:%M:%S",  # syslog with double space
]

# Regex to find candidate timestamp substrings quickly
_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
    r"|(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
)


def extract_timestamp(
    line: str,
    formats: Optional[List[str]] = None,
) -> Optional[datetime]:
    """Extract the first recognisable timestamp from *line*.

    Args:
        line: A single log line.
        formats: strptime format strings to try.  Defaults to DEFAULT_FORMATS.

    Returns:
        A :class:`datetime` object or ``None`` if no timestamp was found.
    """
    fmts = formats if formats is not None else DEFAULT_FORMATS
    m = _TS_RE.search(line)
    if not m:
        return None
    candidate = m.group(0).strip()
    for fmt in fmts:
        try:
            return datetime.strptime(candidate, fmt)
        except ValueError:
            continue
    return None
