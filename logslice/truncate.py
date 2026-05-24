"""Line truncation utilities for logslice output."""

from typing import Optional

DEFAULT_MAX_LENGTH = 200
ELLIPSIS = "..."


def truncate_line(line: str, max_length: Optional[int] = DEFAULT_MAX_LENGTH) -> str:
    """Truncate a single line to at most max_length characters.

    If max_length is None or <= 0, the line is returned unchanged.
    Appends an ellipsis marker when truncation occurs.

    Args:
        line: The input line (may include a trailing newline).
        max_length: Maximum number of characters to keep (excluding newline).

    Returns:
        The (possibly truncated) line, preserving a trailing newline if present.
    """
    if max_length is None or max_length <= 0:
        return line

    trailing_newline = line.endswith("\n")
    stripped = line.rstrip("\n")

    if len(stripped) <= max_length:
        return line

    truncated = stripped[:max_length] + ELLIPSIS
    return truncated + "\n" if trailing_newline else truncated


def truncate_lines(
    lines: list[str], max_length: Optional[int] = DEFAULT_MAX_LENGTH
) -> list[str]:
    """Apply truncation to every line in a list.

    Args:
        lines: Sequence of log lines.
        max_length: Maximum characters per line before truncation.

    Returns:
        New list with each line truncated as needed.
    """
    return [truncate_line(line, max_length) for line in lines]


def count_truncated(
    lines: list[str], max_length: Optional[int] = DEFAULT_MAX_LENGTH
) -> int:
    """Return the number of lines that would be truncated.

    Args:
        lines: Sequence of log lines.
        max_length: Threshold length.

    Returns:
        Count of lines whose stripped length exceeds max_length.
    """
    if max_length is None or max_length <= 0:
        return 0
    return sum(1 for line in lines if len(line.rstrip("\n")) > max_length)
