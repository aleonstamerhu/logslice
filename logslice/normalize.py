"""Line normalization utilities: strip ANSI codes, collapse whitespace, normalize line endings."""

import re

_ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[mGKHF]')
_MULTI_SPACE = re.compile(r'[ \t]+')


def strip_ansi(line: str) -> str:
    """Remove ANSI escape sequences from a line."""
    return _ANSI_ESCAPE.sub('', line)


def normalize_whitespace(line: str, preserve_newline: bool = True) -> str:
    """Collapse runs of spaces/tabs to a single space.

    If *preserve_newline* is True, a trailing newline is kept.
    """
    trailing_nl = ''
    if preserve_newline and line.endswith('\n'):
        trailing_nl = '\n'
        line = line[:-1]
    line = _MULTI_SPACE.sub(' ', line).strip()
    return line + trailing_nl


def normalize_endings(line: str) -> str:
    """Replace Windows-style CRLF with LF."""
    return line.replace('\r\n', '\n').replace('\r', '\n')


def normalize_line(
    line: str,
    *,
    ansi: bool = True,
    whitespace: bool = False,
    endings: bool = True,
) -> str:
    """Apply selected normalizations to *line*.

    Parameters
    ----------
    line:       Input line.
    ansi:       Strip ANSI escape codes (default True).
    whitespace: Collapse whitespace runs (default False).
    endings:    Normalise CRLF to LF (default True).
    """
    if endings:
        line = normalize_endings(line)
    if ansi:
        line = strip_ansi(line)
    if whitespace:
        line = normalize_whitespace(line)
    return line


def normalize_lines(
    lines,
    *,
    ansi: bool = True,
    whitespace: bool = False,
    endings: bool = True,
):
    """Yield normalized versions of each line in *lines*."""
    for line in lines:
        yield normalize_line(line, ansi=ansi, whitespace=whitespace, endings=endings)
