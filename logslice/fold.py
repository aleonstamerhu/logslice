"""Line folding: collapse repeated/similar consecutive lines into a summary."""

from __future__ import annotations

import re
from typing import Iterator, List, Tuple


_VARIABLE_PARTS = re.compile(
    r"(\b(?:\d{1,3}\.){3}\d{1,3}\b"  # IPv4
    r"|\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"  # UUID
    r"|\b\d+\b)"  # plain integers
)


def _fold_key(line: str) -> str:
    """Return a normalised key used to decide whether two lines are 'the same'."""
    return _VARIABLE_PARTS.sub("<N>", line.rstrip())


def fold_lines(
    lines: List[str],
    min_repeat: int = 2,
) -> Iterator[str]:
    """Yield lines, collapsing runs of similar lines into a single summary.

    A run of *min_repeat* or more consecutive lines that share the same
    fold-key is replaced by the first line of the run followed by a
    ``  [... repeated N times]`` annotation.

    Args:
        lines:       Input lines (may or may not end with ``\\n``).
        min_repeat:  Minimum run length before folding kicks in (default 2).

    Yields:
        Processed lines, each ending with ``\\n``.
    """
    if min_repeat < 2:
        raise ValueError("min_repeat must be >= 2")

    if not lines:
        return

    current_key: str = _fold_key(lines[0])
    current_first: str = lines[0]
    run: int = 1

    def _flush(first: str, count: int) -> Iterator[str]:
        yield first if first.endswith("\n") else first + "\n"
        if count >= min_repeat:
            yield f"  [... repeated {count} times]\n"

    for line in lines[1:]:
        key = _fold_key(line)
        if key == current_key:
            run += 1
        else:
            yield from _flush(current_first, run)
            current_key = key
            current_first = line
            run = 1

    yield from _flush(current_first, run)


def count_folded(lines: List[str], min_repeat: int = 2) -> Tuple[int, int]:
    """Return ``(output_lines, lines_folded_away)`` for *lines*."""
    output = list(fold_lines(lines, min_repeat=min_repeat))
    # summary annotation lines start with two spaces + '['
    annotation_count = sum(1 for l in output if l.startswith("  [... repeated"))
    out_data = len(output) - annotation_count
    folded_away = len(lines) - out_data
    return out_data, folded_away
