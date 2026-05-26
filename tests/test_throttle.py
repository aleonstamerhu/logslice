"""Tests for logslice.throttle."""

from __future__ import annotations

from datetime import datetime, timedelta
from itertools import count

import pytest

from logslice.throttle import throttle_lines


def _clock(start: datetime, step_seconds: float = 0.0):
    """Return a factory that advances by *step_seconds* on each call."""
    _counter = count()

    def _now() -> datetime:
        n = next(_counter)
        return start + timedelta(seconds=n * step_seconds)

    return _now


BASE = datetime(2024, 1, 1, 12, 0, 0)


def test_invalid_cooldown_raises():
    with pytest.raises(ValueError):
        list(throttle_lines(["a"], cooldown_seconds=0))


def test_negative_cooldown_raises():
    with pytest.raises(ValueError):
        list(throttle_lines(["a"], cooldown_seconds=-1))


def test_empty_input_returns_empty():
    result = list(throttle_lines([], cooldown_seconds=60))
    assert result == []


def test_single_line_passes_through():
    result = list(throttle_lines(["hello\n"], cooldown_seconds=60, now_fn=lambda: BASE))
    assert result == ["hello\n"]


def test_distinct_keys_all_pass():
    lines = ["error: disk full\n", "warn: low memory\n", "info: started\n"]
    now = _clock(BASE, step_seconds=0)
    result = list(throttle_lines(lines, cooldown_seconds=60, now_fn=now))
    assert result == lines


def test_duplicate_within_cooldown_suppressed():
    lines = ["error: disk full\n"] * 5
    # All calls return the same timestamp → all after the first are suppressed.
    result = list(throttle_lines(lines, cooldown_seconds=60, now_fn=lambda: BASE))
    assert result == ["error: disk full\n"]


def test_duplicate_after_cooldown_passes():
    # Each line arrives 30 s apart; cooldown is 25 s → every line passes.
    lines = ["error: disk full\n"] * 4
    now = _clock(BASE, step_seconds=30)
    result = list(throttle_lines(lines, cooldown_seconds=25, now_fn=now))
    assert result == lines


def test_duplicate_before_cooldown_suppressed_then_passes():
    # t=0 → pass, t=10 → suppress, t=20 → suppress, t=60 → pass
    times = [BASE + timedelta(seconds=s) for s in (0, 10, 20, 60)]
    _iter = iter(times)
    lines = ["repeated\n"] * 4
    result = list(throttle_lines(lines, cooldown_seconds=59, now_fn=lambda: next(_iter)))
    assert result == ["repeated\n", "repeated\n"]


def test_custom_key_fn_groups_by_prefix():
    lines = [
        "ERROR job=backup msg=failed\n",
        "ERROR job=backup msg=timeout\n",
        "WARN  job=backup msg=slow\n",
    ]
    # Key on first word only → both ERROR lines share a key.
    key_fn = lambda line: line.split()[0]
    result = list(throttle_lines(lines, cooldown_seconds=60, key_fn=key_fn, now_fn=lambda: BASE))
    assert len(result) == 2
    assert result[0].startswith("ERROR")
    assert result[1].startswith("WARN")


def test_mixed_lines_interleaved():
    lines = ["a\n", "b\n", "a\n", "c\n", "b\n"]
    result = list(throttle_lines(lines, cooldown_seconds=60, now_fn=lambda: BASE))
    assert result == ["a\n", "b\n", "c\n"]
