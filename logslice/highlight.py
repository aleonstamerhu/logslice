"""Terminal highlighting utilities for matched patterns in log lines."""

import re
from typing import Optional, Pattern

ANSI_RESET = "\033[0m"
ANSI_BOLD_RED = "\033[1;31m"
ANSI_BOLD_YELLOW = "\033[1;33m"
ANSI_BOLD_CYAN = "\033[1;36m"

COLOR_MAP = {
    "red": ANSI_BOLD_RED,
    "yellow": ANSI_BOLD_YELLOW,
    "cyan": ANSI_BOLD_CYAN,
}


def highlight_match(line: str, pattern: Pattern, color: str = "red") -> str:
    """Return line with all occurrences of pattern wrapped in ANSI color codes.

    Args:
        line: The raw log line.
        pattern: Compiled regex pattern to highlight.
        color: One of 'red', 'yellow', 'cyan'. Defaults to 'red'.

    Returns:
        Line with matched spans wrapped in ANSI escape sequences.
    """
    ansi_start = COLOR_MAP.get(color, ANSI_BOLD_RED)

    def _replace(m: re.Match) -> str:
        return f"{ansi_start}{m.group(0)}{ANSI_RESET}"

    return pattern.sub(_replace, line)


def highlight_lines(
    lines: list[str],
    pattern: Optional[Pattern],
    color: str = "red",
    enabled: bool = True,
) -> list[str]:
    """Apply highlight_match to each line if enabled and pattern is set.

    Args:
        lines: Sequence of log lines.
        pattern: Compiled regex or None.
        color: ANSI color name.
        enabled: When False, return lines unchanged (e.g. when stdout is not a tty).

    Returns:
        List of lines, highlighted where applicable.
    """
    if not enabled or pattern is None:
        return list(lines)
    return [highlight_match(line, pattern, color) for line in lines]


def supports_color(stream) -> bool:
    """Return True if *stream* appears to be a colour-capable terminal."""
    return hasattr(stream, "isatty") and stream.isatty()
