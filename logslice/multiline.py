"""Multi-line log record joining.

Some log formats (e.g. Java stack traces, Python tracebacks) span multiple
lines.  This module groups raw lines into logical records by treating any line
that does *not* start with a timestamp (or matches a user-supplied continuation
pattern) as a continuation of the previous record.
"""

import re
from typing import Iterable, Iterator, List, Optional

# Matches the leading timestamp patterns recognised by extractor.py
_TIMESTAMP_RE = re.compile(
    r"(?:"
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"  # ISO-8601
    r"|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"     # syslog
    r")"
)


def _starts_record(line: str, continuation: Optional[re.Pattern]) -> bool:
    """Return True when *line* begins a new logical record."""
    if continuation is not None and continuation.search(line):
        return False
    return bool(_TIMESTAMP_RE.match(line.lstrip()))


def join_multiline(
    lines: Iterable[str],
    continuation: Optional[str] = None,
    separator: str = "\n",
    max_lines: int = 500,
) -> Iterator[str]:
    """Yield logical log records by joining continuation lines.

    Parameters
    ----------
    lines:
        Raw input lines (with or without trailing newline).
    continuation:
        Optional regex; lines matching it are treated as continuations even
        when they carry a timestamp.
    separator:
        String used to join continuation lines into a single record.
    max_lines:
        Safety cap — flush the current record after this many raw lines even
        if no new record has started.
    """
    cont_re: Optional[re.Pattern] = (
        re.compile(continuation) if continuation else None
    )

    buffer: List[str] = []

    for raw in lines:
        line = raw.rstrip("\n")
        if not line:
            # Blank line always flushes
            if buffer:
                yield separator.join(buffer)
                buffer = []
            continue

        if buffer and (_starts_record(line, cont_re) or len(buffer) >= max_lines):
            yield separator.join(buffer)
            buffer = [line]
        else:
            buffer.append(line)

    if buffer:
        yield separator.join(buffer)


def split_record(record: str, separator: str = "\n") -> List[str]:
    """Reverse of joining — split a record back into individual lines."""
    return record.split(separator)


def count_multiline_records(records: Iterable[str], separator: str = "\n") -> int:
    """Return the number of records that contain more than one raw line."""
    return sum(1 for r in records if separator in r)
