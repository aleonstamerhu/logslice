"""Output formatting utilities for logslice."""

from datetime import datetime
from typing import Iterable, Optional

DEFAULT_FORMAT = "{line}"
TIMESTAMP_FORMAT = "{timestamp} {line}"
NUMBERED_FORMAT = "{lineno}: {line}"
FULL_FORMAT = "{lineno}: [{timestamp}] {line}"

_FORMATS = {
    "default": DEFAULT_FORMAT,
    "timestamp": TIMESTAMP_FORMAT,
    "numbered": NUMBERED_FORMAT,
    "full": FULL_FORMAT,
}


def get_format_template(name: str) -> str:
    """Return a named format template string.

    Args:
        name: One of 'default', 'timestamp', 'numbered', 'full'.

    Returns:
        Format template string.

    Raises:
        ValueError: If the format name is unknown.
    """
    if name not in _FORMATS:
        raise ValueError(
            f"Unknown format '{name}'. Choose from: {', '.join(_FORMATS)}"
        )
    return _FORMATS[name]


def format_line(
    line: str,
    lineno: int = 0,
    timestamp: Optional[datetime] = None,
    template: str = DEFAULT_FORMAT,
) -> str:
    """Format a single log line using the given template.

    Args:
        line: The raw log line (stripped of trailing newline).
        lineno: 1-based line number within the source.
        timestamp: Parsed datetime for the line, or None.
        template: A format string with optional placeholders.

    Returns:
        Formatted string ready for output.
    """
    ts_str = timestamp.isoformat(sep=" ") if timestamp is not None else ""
    return template.format(line=line, lineno=lineno, timestamp=ts_str)


def format_lines(
    lines: Iterable[tuple],
    template: str = DEFAULT_FORMAT,
) -> Iterable[str]:
    """Format an iterable of (lineno, timestamp, line) tuples.

    Args:
        lines: Iterable of (lineno, timestamp, line) tuples.
        template: Format template string.

    Yields:
        Formatted log line strings.
    """
    for lineno, timestamp, line in lines:
        yield format_line(line, lineno=lineno, timestamp=timestamp, template=template)
