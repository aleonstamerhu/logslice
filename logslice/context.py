"""Context lines support: capture N lines before/after each match."""

from collections import deque
from typing import Iterable, Iterator, List, Optional


def lines_with_context(
    lines: Iterable[str],
    before: int = 0,
    after: int = 0,
    match_fn=None,
) -> Iterator[dict]:
    """Yield dicts with 'line', 'lineno', and 'match' flag, including context.

    Each yielded dict:
        {
            'line': str,
            'lineno': int,
            'match': bool,   # True if this line itself matched
        }

    Duplicate lines (appearing as both before- and after-context) are
    deduplicated; the line is emitted only once, in order.
    """
    if match_fn is None:
        match_fn = lambda line: True  # noqa: E731

    before = max(0, before)
    after = max(0, after)

    # Buffer of (lineno, line) for look-behind
    pre_buf: deque = deque(maxlen=before)
    # Countdown of remaining after-context lines to emit
    after_countdown: int = 0
    # Track which line numbers have already been emitted
    emitted: set = set()

    # We need to look ahead for after-context, so buffer everything.
    indexed: List[tuple] = list(enumerate(lines, start=1))

    for idx, (lineno, line) in enumerate(indexed):
        is_match = match_fn(line)

        if is_match:
            # Emit before-context lines not yet emitted
            for prev_lineno, prev_line in pre_buf:
                if prev_lineno not in emitted:
                    emitted.add(prev_lineno)
                    yield {"line": prev_line, "lineno": prev_lineno, "match": False}

            # Emit the matching line
            if lineno not in emitted:
                emitted.add(lineno)
                yield {"line": line, "lineno": lineno, "match": True}

            # Schedule after-context
            after_countdown = after

        elif after_countdown > 0:
            if lineno not in emitted:
                emitted.add(lineno)
                yield {"line": line, "lineno": lineno, "match": False}
            after_countdown -= 1

        # Always update the pre-buffer
        pre_buf.append((lineno, line))


def extract_lines(context_entries: Iterable[dict]) -> Iterator[str]:
    """Extract just the line strings from context entries."""
    for entry in context_entries:
        yield entry["line"]
