"""Output writing utilities for logslice."""

import sys
from typing import Iterable, Optional, TextIO

from logslice.formatter import format_lines, get_format_template, DEFAULT_FORMAT


def write_lines(
    lines: Iterable[tuple],
    dest: TextIO = sys.stdout,
    format_name: str = "default",
    max_lines: Optional[int] = None,
) -> int:
    """Write formatted log lines to a destination stream.

    Args:
        lines: Iterable of (lineno, timestamp, line) tuples.
        dest: Output stream (default: stdout).
        format_name: Named format template to apply.
        max_lines: If set, stop after this many lines are written.

    Returns:
        Total number of lines written.
    """
    template = get_format_template(format_name)
    written = 0
    for formatted in format_lines(lines, template=template):
        dest.write(formatted + "\n")
        written += 1
        if max_lines is not None and written >= max_lines:
            break
    return written


def write_summary(count: int, dest: TextIO = sys.stdout) -> None:
    """Write a match-count summary line to a destination stream.

    Args:
        count: Number of matched lines.
        dest: Output stream (default: stdout).
    """
    dest.write(f"-- {count} line(s) matched --\n")


def write_separator(dest: TextIO = sys.stdout, char: str = "-", width: int = 40) -> None:
    """Write a visual separator line.

    Args:
        dest: Output stream.
        char: Character to repeat.
        width: Total width of the separator.
    """
    dest.write(char * width + "\n")
