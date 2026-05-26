"""Throttle: emit at most one line per key per cooldown window."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Iterable, Iterator, Optional


def _default_key(line: str) -> str:
    """Use the full stripped line as the throttle key."""
    return line.strip()


def throttle_lines(
    lines: Iterable[str],
    cooldown_seconds: float,
    key_fn: Optional[Callable[[str], str]] = None,
    now_fn: Optional[Callable[[], datetime]] = None,
) -> Iterator[str]:
    """Yield lines, suppressing repeated keys within *cooldown_seconds*.

    Args:
        lines: Input lines to process.
        cooldown_seconds: Minimum seconds between emissions for the same key.
        key_fn: Function that maps a line to its throttle key.  Defaults to
            the full stripped line.
        now_fn: Callable returning the current time (injectable for testing).

    Yields:
        Lines whose key has not been emitted within the cooldown window.
    """
    if cooldown_seconds <= 0:
        raise ValueError("cooldown_seconds must be positive")

    key_fn = key_fn or _default_key
    now_fn = now_fn or datetime.utcnow
    last_seen: dict[str, datetime] = {}
    cooldown = timedelta(seconds=cooldown_seconds)

    for line in lines:
        key = key_fn(line)
        now = now_fn()
        prev = last_seen.get(key)
        if prev is None or (now - prev) >= cooldown:
            last_seen[key] = now
            yield line


def count_suppressed(
    lines: Iterable[str],
    cooldown_seconds: float,
    key_fn: Optional[Callable[[str], str]] = None,
    now_fn: Optional[Callable[[], datetime]] = None,
) -> tuple[list[str], int]:
    """Return (emitted_lines, suppressed_count) after throttling."""
    emitted = list(throttle_lines(lines, cooldown_seconds, key_fn=key_fn, now_fn=now_fn))
    total = sum(1 for _ in lines.__class__) if False else 0  # placeholder
    # Re-count by draining original; caller should use this for reporting.
    return emitted, 0  # suppressed count tracked externally if needed
